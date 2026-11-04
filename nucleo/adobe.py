"""
Ler o estado do Adobe — projeto ativo, sequência, conexão do Tools PRO.

Como funciona, porque não é óbvio:

O Premiere não expõe API local. O que existe é o painel CEP do Tools PRO, que
roda num Chromium embutido com a porta de debug aberta. Falando o protocolo do
Chrome DevTools com essa porta dá para avaliar JavaScript DENTRO do painel — e
o painel tem `CSInterface.evalScript()`, que executa ExtendScript no Premiere.

    app (aqui) → WebSocket CDP → painel CEP → evalScript → Premiere

⚠️ **A porta só existe enquanto um painel está ABERTO.** Fechou o painel ou
reiniciou o Premiere, a porta some — e o app precisa dizer "abra o painel em
Janela > Extensões" em vez de "erro de conexão", que não ensina nada.

WebSocket na mão porque o app não carrega dependência para isso: uma biblioteca
a mais é um jeito a mais do PyInstaller falhar no empacotamento.
"""

import base64
import json
import os
import socket
import struct
import urllib.request

from . import so

# 8899/8898 são a porta PRÓPRIA do Tools PRO, criada por `ponte.preparar()`.
# Vem primeiro de propósito: numa máquina que também tenha blinkl ou Higgsfield,
# é o painel do Tools PRO que queremos, não o do vizinho.
PORTAS = [8899, 8898, 8901, 8900, 8862, 8860, 8863, 7842, 8088, 8090, 8092]
TEMPO = 12


# ---------------------------------------------------------------- descoberta

# Uma única chamada de `/api/adobe` chama `estado()` e `verificar()`, e o
# `verificar()` chama `estado()` de novo — três varreduras completas por clique,
# cada uma com `tasklist` e 11 portas. Um cache de 2 segundos não esconde nada
# (o estado real não muda nesse intervalo) e corta a repetição dentro do mesmo
# pedido, que era o que fazia a tela do Windows piscar sem parar.
_cache = {}


def _lembrar(chave, segundos, fn):
    import time as _t
    agora = _t.time()
    val = _cache.get(chave)
    if val and agora - val[0] < segundos:
        return val[1]
    novo = fn()
    _cache[chave] = (agora, novo)
    return novo


def esquecer():
    _cache.clear()


def rodando():
    """Quais apps Adobe estão abertos agora.

    O padrão muda de casa: no Mac é a linha de comando inteira (`pgrep -f`), no
    Windows é o NOME do executável, que é o que o `tasklist` sabe filtrar."""
    def olhar():
        saida = {}
        for chave, mac, win in (("premiere", "Adobe Premiere Pro", "Adobe Premiere Pro.exe"),
                                ("aftereffects", "Adobe After Effects",
                                 "AfterFX.exe")):
            saida[chave] = so.processos(win if so.WIN else mac)
        return saida
    return _lembrar("rodando", 2.0, olhar)


def _alvos(porta):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json" % porta, timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return []


def paineis():
    """Painéis CEP alcançáveis. Sem eles não há como falar com o Premiere."""
    def varrer():
        achados = []
        for p in PORTAS:
            for t in _alvos(p):
                if t.get("webSocketDebuggerUrl"):
                    achados.append({"porta": p, "titulo": t.get("title", ""),
                                    "ws": t["webSocketDebuggerUrl"]})
        return achados
    return _lembrar("paineis", 2.0, varrer)


def _ponte():
    """O painel que sabe falar com o Premiere. Prefere o do Higgsfield/Tools PRO."""
    ps = paineis()
    for p in ps:
        t = (p["titulo"] or "").lower()
        if "higgsfield" in t or "tools" in t or "bridge" in t:
            return p
    return ps[0] if ps else None


# ---------------------------------------------------------------- WebSocket

class SemPonte(RuntimeError):
    pass


def _ws_abrir(url, timeout=TEMPO):
    resto = url.split("://", 1)[1]
    hostporta, _, caminho = resto.partition("/")
    host, _, porta = hostporta.partition(":")
    s = socket.create_connection((host, int(porta or 80)), timeout=timeout)
    s.settimeout(timeout)
    chave = base64.b64encode(os.urandom(16)).decode()
    s.sendall(("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n"
               "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n"
               % (caminho, hostporta, chave)).encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        pedaco = s.recv(4096)
        if not pedaco:
            raise SemPonte("O painel fechou a conexão.")
        resp += pedaco
    if b"101" not in resp.split(b"\r\n")[0]:
        raise SemPonte("O painel recusou a conexão de depuração.")
    return s


def _ws_enviar(s, texto):
    dados = texto.encode("utf-8")
    n = len(dados)
    cab = bytearray([0x81])
    if n < 126:
        cab.append(0x80 | n)
    elif n < 65536:
        cab.append(0x80 | 126)
        cab += struct.pack(">H", n)
    else:
        cab.append(0x80 | 127)
        cab += struct.pack(">Q", n)
    mascara = os.urandom(4)
    cab += mascara
    s.sendall(bytes(cab) + bytes(b ^ mascara[i % 4] for i, b in enumerate(dados)))


def _ws_ler(s):
    def exato(n):
        buf = b""
        while len(buf) < n:
            pedaco = s.recv(n - len(buf))
            if not pedaco:
                raise SemPonte("Conexão caiu no meio da resposta.")
            buf += pedaco
        return buf

    cab = exato(2)
    tam = cab[1] & 0x7F
    if tam == 126:
        tam = struct.unpack(">H", exato(2))[0]
    elif tam == 127:
        tam = struct.unpack(">Q", exato(8))[0]
    return exato(tam).decode("utf-8", "replace")


def _avaliar(js, timeout=TEMPO):
    """Roda JavaScript dentro do painel CEP."""
    p = _ponte()
    if not p:
        raise SemPonte(
            "Não achei nenhum painel do Tools PRO aberto. Abra o Premiere e vá em "
            "Janela > Extensões > Tools PRO — a ponte só existe com o painel aberto.")
    # o timeout PRECISA chegar no socket: importar 10 b-rolls passa dos 12s
    # padrão, e antes daqui o parâmetro era decorativo — a espera longa morria
    # no socket sem nunca ter sido concedida.
    s = _ws_abrir(p["ws"], timeout)
    try:
        _ws_enviar(s, json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": js, "awaitPromise": True, "returnByValue": True}}))
        for _ in range(400):
            msg = json.loads(_ws_ler(s))
            if msg.get("id") == 1:
                r = msg.get("result") or {}
                if r.get("exceptionDetails"):
                    raise SemPonte("O painel recusou: " +
                                   str(r["exceptionDetails"].get("text", ""))[:160])
                return (r.get("result") or {}).get("value")
        raise SemPonte("O painel não respondeu a tempo.")
    finally:
        try:
            s.close()
        except Exception:
            pass


def extendscript(codigo, timeout=TEMPO):
    """Executa ExtendScript no Premiere através do painel.

    Usa `window.__adobe_cep__` — a API BRUTA do CEP, presente em todo painel.
    O `CSInterface` é só um embrulho por cima dela e nem todo painel o carrega:
    o Higgsfield Bridge Host, por exemplo, não tem. Ir na API bruta funciona em
    qualquer painel, o que importa porque o app não controla qual deles o
    usuário deixou aberto."""
    js = ("new Promise(function(ok){ window.__adobe_cep__.evalScript(%s, ok); })"
          % json.dumps(codigo))
    return _avaliar(js, timeout)


# ---------------------------------------------------------------- estado

LER_ESTADO = r"""
(function(){
  try {
    if (typeof app === 'undefined' || !app.project) return JSON.stringify({sem:'app'});
    var pr = app.project;
    var seqs = [], ativa = null;
    for (var i = 0; i < pr.sequences.numSequences; i++) {
      var s = pr.sequences[i];
      seqs.push({nome: s.name, id: s.sequenceID});
      if (pr.activeSequence && s.sequenceID === pr.activeSequence.sequenceID) ativa = s.name;
    }
    return JSON.stringify({
      projeto: pr.name,
      caminho: pr.path,
      sequencias: seqs,
      ativa: ativa,
      itens: pr.rootItem ? pr.rootItem.children.numItems : 0
    });
  } catch (e) { return JSON.stringify({erro: String(e)}); }
})()
"""


def estado():
    """O que o chat mostra antes de mexer em qualquer coisa."""
    apps = rodando()
    base = {"apps": apps, "painel": None, "projeto": None,
            "sequencias": [], "ativa": None, "aviso": None}

    if not apps["premiere"] and not apps["aftereffects"]:
        base["aviso"] = ("Nenhum programa da Adobe aberto. Abra o Premiere Pro "
                         "(ou o After Effects) e o projeto que você quer editar.")
        return base

    p = _ponte()
    if not p:
        base["aviso"] = ("O Premiere está aberto, mas não achei o painel do Tools PRO. "
                         "Vá em Janela > Extensões > Tools PRO — a ponte só existe "
                         "com o painel aberto.")
        return base
    base["painel"] = p["titulo"]

    try:
        bruto = extendscript(LER_ESTADO)
        d = json.loads(bruto) if bruto else {}
    except SemPonte as e:
        base["aviso"] = str(e)
        return base
    except Exception as e:
        base["aviso"] = "Não consegui ler o Premiere: %s" % e
        return base

    if d.get("erro") or d.get("sem"):
        base["aviso"] = ("O painel respondeu, mas não há projeto aberto no Premiere. "
                         "Abra o projeto que você quer editar.")
        return base

    base.update(projeto=d.get("projeto"), caminho=d.get("caminho"),
                sequencias=d.get("sequencias") or [], ativa=d.get("ativa"),
                itens=d.get("itens"))
    if len(base["sequencias"]) > 1 and not base["ativa"]:
        base["aviso"] = ("Há %d sequências no projeto e nenhuma ativa. "
                         "Me diga qual usar." % len(base["sequencias"]))
    return base


# ---------------------------------------------------------------- timeline

LER_TIMELINE = r"""
(function(){
  try {
    var pr = app.project;
    if (!pr) return JSON.stringify({erro:'sem projeto'});
    var seq = pr.activeSequence;
    if (!seq) return JSON.stringify({erro:'nenhuma sequência ativa'});

    function tick(t){ return Math.round((t/254016000000)*1000)/1000; }

    function trilhas(cols, tipo){
      var out = [];
      for (var i=0;i<cols.numTracks;i++){
        var tr = cols[i], clipes = [];
        for (var j=0;j<tr.clips.numItems;j++){
          var c = tr.clips[j];
          clipes.push({
            nome: c.name,
            entra: tick(c.start.ticks),
            sai:   tick(c.end.ticks),
            dur:   tick(c.duration.ticks),
            mudo:  tipo==='audio' ? undefined : undefined
          });
        }
        // isMuted é MÉTODO. Sem os parênteses volta a função — sempre verdadeira —
        // e TODA trilha vira "muda". O Claude decidiria em cima disso.
        var mudo = false;
        try { mudo = (typeof tr.isMuted === 'function') ? tr.isMuted() : !!tr.isMuted; } catch(e){}
        out.push({tipo: tipo, n: i+1, nome: tr.name, mudo: mudo, clipes: clipes});
      }
      return out;
    }

    var marc = [], m = seq.markers, mk = m.getFirstMarker();
    while (mk) {
      marc.push({nome: mk.name, comentario: mk.comments,
                 t: tick(mk.start.ticks), fim: tick(mk.end.ticks),
                 cor: mk.getColorByIndex ? mk.getColorByIndex() : null});
      mk = m.getNextMarker(mk);
    }

    return JSON.stringify({
      sequencia: seq.name,
      duracao: tick(seq.end),
      video: trilhas(seq.videoTracks, 'video'),
      audio: trilhas(seq.audioTracks, 'audio'),
      marcadores: marc
    });
  } catch(e){ return JSON.stringify({erro:String(e)}); }
})()
"""


def timeline():
    """A timeline da sequência ativa — trilhas, clipes e marcadores.

    É isto que faz "analise esta timeline" funcionar sem pedir caminho de
    .prproj nem vídeo exportado: o material já está aberto na frente do usuário."""
    bruto = extendscript(LER_TIMELINE, timeout=40)
    d = json.loads(bruto) if bruto else {}
    if d.get("erro"):
        raise SemPonte(d["erro"])
    v = d.get("video") or []
    a = d.get("audio") or []
    d["resumo"] = {
        "trilhas_video": len(v), "trilhas_audio": len(a),
        "clipes": sum(len(t["clipes"]) for t in v + a),
        "marcadores": len(d.get("marcadores") or []),
        "trilhas_mudas": [t["nome"] for t in v + a if t.get("mudo")],
    }
    return d


def verificar():
    """Teste REAL de ponta a ponta antes de dizer que está conectado.

    A tela dizia "Tools PRO conectada" só porque achou um painel na porta de
    debug. Isso não prova nada: o painel pode estar aberto e o Premiere sem
    projeto, ou o ExtendScript pode falhar. Aqui a gente LÊ de verdade — e só
    então reporta conectado."""
    r = {"ponte": False, "leu_projeto": False, "leu_timeline": False,
         "mcp": False, "detalhe": "", "projeto": None, "sequencia": None}

    p = _ponte()
    if not p:
        # ⚠️ Antes daqui a mensagem mandava abrir o painel — e o aluno JÁ estava
        # com ele aberto. Sem `.debug` na extensão não existe porta nenhuma, e
        # nenhuma quantidade de abrir painel cria uma.
        from . import ponte
        e = ponte.estado()
        if e["plugin_instalado"] and not e["tem_debug"]:
            r["detalhe"] = ("O painel do Tools PRO não abre porta de conexão nesta "
                            "máquina — falta preparar a ponte. É um clique, e depois "
                            "reiniciar o Premiere.")
            r["preparar_ponte"] = True
        elif not e["plugin_instalado"]:
            r["detalhe"] = ("O plugin Tools PRO não está instalado. Vá em Ambiente > "
                            "Instalar plugin no Premiere.")
            r["instalar_plugin"] = True
        else:
            r["detalhe"] = ("A ponte está preparada mas o painel não respondeu. No "
                            "Premiere: Janela > Extensões > Tools PRO. Se acabou de "
                            "preparar, reinicie o Premiere primeiro.")
        return r
    r["ponte"] = True

    try:
        e = estado()
        if e.get("aviso") and not e.get("projeto"):
            r["detalhe"] = e["aviso"]
            return r
        r["leu_projeto"] = bool(e.get("projeto"))
        r["projeto"] = e.get("projeto")
        r["sequencia"] = e.get("ativa")
    except Exception as ex:
        r["detalhe"] = "A ponte respondeu mas não consegui ler o projeto: %s" % ex
        return r

    try:
        t = timeline()
        r["leu_timeline"] = True
        r["resumo"] = t.get("resumo")
    except SemPonte as ex:
        r["detalhe"] = str(ex)
    except Exception as ex:
        r["detalhe"] = "Não consegui ler a timeline: %s" % ex

    return r
