"""
Etapa 11 — a montagem no Premiere.

O app não desenha o vídeo: ele escreve na timeline que o editor já tem aberto.
Isso é decisão de produto. O aluno quer o job montado NO PROJETO dele, com as
trilhas dele, para ajustar à mão depois — não um mp4 fechado que ele não
consegue mexer.

O caminho é o mesmo do `adobe.py`: porta de debug do painel CEP → ExtendScript.
Aqui só mora o que ESCREVE.

Regras que valem para tudo neste arquivo, e o porquê:

  * **Escreve em passos separados.** Preparar, importar, posicionar, punch e
    marcadores são cinco chamadas. Uma chamada só ficaria minutos sem dar sinal
    de vida e, se falhasse no meio, ninguém saberia até onde tinha ido.

  * **Nada é dado como feito sem LER DE VOLTA.** O Premiere tem falha silenciosa
    demais para acreditar em retorno de função: `addVideoEffect` não adiciona e
    não reclama, `deleteSequence` do projectItem não apaga, transform pelo nome
    em inglês num Premiere PT-BR devolve sucesso sem mudar nada. Todo passo aqui
    relê o que escreveu e o relatório mostra o LIDO, não o pedido.

  * **Efeito por `matchName`, nunca por nome de menu.** `AE.ADBE Motion` é igual
    em qualquer idioma; "Motion" só existe no Premiere em inglês. Foi assim que
    quatro punch-ins "com sucesso" não mudaram nada num job real.

  * **B-roll entra só na trilha de VÍDEO.** `overwriteClip` numa videoTrack leva
    a imagem e deixa o áudio do b-roll de fora — que é exatamente o que se quer:
    áudio de IA por cima da voz do avatar não tem como ser separado depois.
"""

import json
import os
import time

from . import adobe, pipeline, projetos, skill

TRILHA_APOIO = 2      # V2. V1 é o body; o apoio entra por cima.
BIN = "Editor Automático"
SELO = "EA:"          # marca o que foi escrito por aqui — só isso é apagado


class Falhou(RuntimeError):
    pass


# ---------------------------------------------------------------- ExtendScript

# Biblioteca comum. Vai na frente de todo passo — o painel CEP não guarda
# estado entre chamadas, cada `evalScript` começa do zero.
LIB = r"""
function eaJson(o){ return JSON.stringify(o); }
function eaSeg(t){ return Math.round((t)*1000)/1000; }

function eaSeq(){
  if (typeof app === 'undefined' || !app.project) throw new Error('sem Premiere');
  var s = app.project.activeSequence;
  if (!s) throw new Error('nenhuma sequência ativa');
  return s;
}

function eaTempo(seg){ var t = new Time(); t.seconds = seg; return t; }

function eaBin(nome){
  var root = app.project.rootItem;
  var TIPO_BIN = (typeof ProjectItemType !== 'undefined') ? ProjectItemType.BIN : 2;
  for (var i = 0; i < root.children.numItems; i++){
    var it = root.children[i];
    if (it.name === nome && it.type === TIPO_BIN) return it;
  }
  return root.createBin(nome);
}

function eaCaminho(item){
  try { return item.getMediaPath(); } catch(e){ return ''; }
}

function eaAcharNoBin(bin, caminho){
  for (var i = 0; i < bin.children.numItems; i++){
    var it = bin.children[i];
    if (eaCaminho(it) === caminho) return it;
  }
  return null;
}

// O componente Movimento pelo matchName — imune a idioma da interface.
function eaMotion(clip){
  try {
    for (var i = 0; i < clip.components.numItems; i++){
      var c = clip.components[i];
      if (String(c.matchName) === 'AE.ADBE Motion') return c;
    }
  } catch(e){}
  return null;
}

// Propriedade por nome aceitando PT e EN; se nenhum casar, cai no índice
// conhecido — e DIZ que caiu, para o relatório não afirmar o que não sabe.
function eaProp(comp, nomes, indice){
  var achou = null, vistos = [];
  try {
    for (var i = 0; i < comp.properties.numItems; i++){
      var p = comp.properties[i];
      var n = String(p.displayName).toLowerCase();
      vistos.push(String(p.displayName));
      for (var k = 0; k < nomes.length; k++){
        if (n === nomes[k]) { achou = p; break; }
      }
      if (achou) return {prop: achou, por: 'nome', vistos: vistos};
    }
    if (indice !== undefined && indice < comp.properties.numItems)
      return {prop: comp.properties[indice], por: 'indice', vistos: vistos};
  } catch(e){}
  return {prop: null, por: 'nada', vistos: vistos};
}
"""

PREPARAR = LIB + r"""
(function(){
  try {
    var cfg = JSON.parse(%s);
    var seq = eaSeq();
    var precisa = cfg.trilhas_video;
    var criadas = 0;
    if (seq.videoTracks.numTracks < precisa){
      app.enableQE();
      var q = qe.project.getActiveSequence();
      var faltam = precisa - seq.videoTracks.numTracks;
      try { q.addTracks(faltam, seq.videoTracks.numTracks, 0); criadas = faltam; }
      catch(e){ criadas = -1; }
      seq = eaSeq();
    }

    var v1 = [];
    if (seq.videoTracks.numTracks > 0){
      var tr = seq.videoTracks[0];
      for (var j = 0; j < tr.clips.numItems; j++){
        var c = tr.clips[j];
        v1.push({nome: c.name, entra: eaSeg(c.start.seconds), sai: eaSeg(c.end.seconds),
                 fonte: eaSeg(c.inPoint.seconds)});
      }
    }
    return eaJson({
      ok: true,
      sequencia: seq.name,
      projeto: app.project.name,
      timebase: String(seq.timebase),
      trilhas_video: seq.videoTracks.numTracks,
      trilhas_audio: seq.audioTracks.numTracks,
      trilhas_criadas: criadas,
      duracao: eaSeg(seq.end / 254016000000),
      v1: v1
    });
  } catch(e){ return eaJson({ok:false, erro:String(e)}); }
})()
"""

IMPORTAR = LIB + r"""
(function(){
  try {
    var cfg = JSON.parse(%s);
    var bin = eaBin(cfg.bin);
    var faltam = [];
    for (var i = 0; i < cfg.arquivos.length; i++){
      if (!eaAcharNoBin(bin, cfg.arquivos[i])) faltam.push(cfg.arquivos[i]);
    }
    if (faltam.length) app.project.importFiles(faltam, true, bin, false);

    var saida = [];
    for (var k = 0; k < cfg.arquivos.length; k++){
      var it = eaAcharNoBin(bin, cfg.arquivos[k]);
      saida.push({arquivo: cfg.arquivos[k], entrou: !!it,
                  nome: it ? it.name : null});
    }
    return eaJson({ok:true, bin: bin.name, pedidos: cfg.arquivos.length,
                   novos: faltam.length, itens: saida});
  } catch(e){ return eaJson({ok:false, erro:String(e)}); }
})()
"""

POSICIONAR = LIB + r"""
(function(){
  try {
    var cfg = JSON.parse(%s);
    var seq = eaSeq();
    var idx = cfg.trilha - 1;
    if (idx < 0 || idx >= seq.videoTracks.numTracks)
      return eaJson({ok:false, erro:'a trilha V' + cfg.trilha + ' não existe'});
    var tr = seq.videoTracks[idx];
    var bin = eaBin(cfg.bin);

    // limpa só a trilha do apoio, e só quando pedido. Rodar a montagem duas
    // vezes sem isso empilharia b-roll por cima de b-roll.
    var limpos = 0;
    if (cfg.limpar){
      app.enableQE();
      var q = qe.project.getActiveSequence().getVideoTrackAt(idx);
      for (var i = q.numItems - 1; i >= 0; i--){
        var it = q.getItemAt(i);
        if (it && String(it.type) !== 'Empty'){ try { it.remove(false, false); limpos++; } catch(e){} }
      }
      seq = eaSeq(); tr = seq.videoTracks[idx];
    }

    var postos = [];
    for (var n = 0; n < cfg.itens.length; n++){
      var b = cfg.itens[n];
      var item = eaAcharNoBin(bin, b.arquivo);
      if (!item){ postos.push({id: b.id, ok:false, motivo:'não importado'}); continue; }
      try { tr.overwriteClip(item, b.inicio); }
      catch(e){ postos.push({id: b.id, ok:false, motivo:String(e)}); continue; }

      // acha o clipe recém-posto e apara no fim do beat
      var achado = null;
      for (var j = 0; j < tr.clips.numItems; j++){
        var c = tr.clips[j];
        if (Math.abs(c.start.seconds - b.inicio) < 0.05) { achado = c; break; }
      }
      if (!achado){ postos.push({id: b.id, ok:false, motivo:'sumiu depois de posto'}); continue; }

      var alvo = b.fim - b.inicio;
      var antes = eaSeg(achado.end.seconds - achado.start.seconds);
      if (achado.end.seconds > b.fim + 0.02){
        try { achado.end = eaTempo(b.fim); } catch(e){}
      }
      // LÊ DE VOLTA: é isto, e não o retorno das funções, que prova a montagem
      var dur = eaSeg(achado.end.seconds - achado.start.seconds);
      postos.push({id: b.id, ok:true, nome: achado.name,
                   entra: eaSeg(achado.start.seconds), sai: eaSeg(achado.end.seconds),
                   pedido: eaSeg(alvo), durou: dur, bruto: antes,
                   curto: dur < alvo - 0.06});
    }
    return eaJson({ok:true, trilha:'V' + cfg.trilha, limpos: limpos, itens: postos,
                   clipes_na_trilha: tr.clips.numItems});
  } catch(e){ return eaJson({ok:false, erro:String(e)}); }
})()
"""

PUNCH = LIB + r"""
(function(){
  try {
    var cfg = JSON.parse(%s);
    var seq = eaSeq();
    var tr = seq.videoTracks[cfg.trilha - 1];
    if (!tr) return eaJson({ok:false, erro:'trilha do body não existe'});
    var passo = 1.0 / (cfg.fps || 30);

    var feitos = [], vistos = [];
    for (var j = 0; j < tr.clips.numItems; j++){
      var c = tr.clips[j];
      var mot = eaMotion(c);
      if (!mot){ feitos.push({clipe: c.name, ok:false, motivo:'sem componente Movimento'}); continue; }
      var r = eaProp(mot, ['escala','scale'], 1);
      vistos = r.vistos;
      var p = r.prop;
      if (!p){ feitos.push({clipe: c.name, ok:false, motivo:'sem propriedade de escala'}); continue; }

      // keyframe de clipe é medido no tempo da FONTE, não da sequência
      function fonte(tSeq){ return c.inPoint.seconds + (tSeq - c.start.seconds); }

      var postos = 0, erro = null;
      try {
        p.setTimeVarying(true);
        for (var s = 0; s < cfg.segmentos.length; s++){
          var seg = cfg.segmentos[s];
          var ini = seg[0], fim = seg[1], esc = seg[2] * 100;
          if (fim <= c.start.seconds + 0.001 || ini >= c.end.seconds - 0.001) continue;
          var dentro = Math.max(ini, c.start.seconds);
          // um quadro antes segura o valor anterior: a virada vira SNAP, sem
          // rampa. É o punch em corte seco, sem precisar razorar o clipe.
          if (s > 0 && dentro - passo > c.start.seconds){
            var ant = cfg.segmentos[s-1][2] * 100;
            var ta = fonte(dentro - passo);
            p.addKey(ta); p.setValueAtKey(ta, ant, true);
          }
          var t = fonte(dentro);
          p.addKey(t); p.setValueAtKey(t, esc, true);
          postos++;
        }
      } catch(e){ erro = String(e); }

      var variando = false, amostra = null;
      try { variando = p.isTimeVarying(); } catch(e){}
      try { amostra = p.getValueAtTime(fonte(Math.max(c.start.seconds + 0.05, cfg.amostra))); } catch(e){}
      feitos.push({clipe: c.name, ok: (postos > 0 && !erro), chaves: postos,
                   variando: variando, amostra: amostra, achou_por: r.por,
                   motivo: erro});
    }
    return eaJson({ok:true, clipes: feitos, propriedades_vistas: vistos});
  } catch(e){ return eaJson({ok:false, erro:String(e)}); }
})()
"""

MARCADORES = LIB + r"""
(function(){
  try {
    var cfg = JSON.parse(%s);
    var seq = eaSeq();
    var m = seq.markers;

    // apaga só o que este app criou. Marcador do editor não se toca.
    var apagados = 0;
    var mk = m.getFirstMarker();
    while (mk){
      var prox = m.getNextMarker(mk);
      if (String(mk.comments).indexOf(cfg.selo) === 0){
        try { m.deleteMarker(mk); apagados++; } catch(e){}
      }
      mk = prox;
    }

    var criados = 0, falhas = [];
    for (var i = 0; i < cfg.itens.length; i++){
      var it = cfg.itens[i];
      try {
        var novo = m.createMarker(it.inicio);
        novo.name = it.nome;
        novo.comments = cfg.selo + (it.comentario || '');
        if (it.duracao > 0.04){
          try { novo.end = eaTempo(it.inicio + it.duracao); } catch(e){}
        }
        try { if (novo.setColorByIndex) novo.setColorByIndex(it.cor); } catch(e){}
        criados++;
      } catch(e){ falhas.push({nome: it.nome, motivo: String(e)}); }
    }

    // relê: quantos marcadores com o selo existem de fato agora
    var conferidos = 0;
    var q = m.getFirstMarker();
    while (q){
      if (String(q.comments).indexOf(cfg.selo) === 0) conferidos++;
      q = m.getNextMarker(q);
    }
    return eaJson({ok:true, apagados: apagados, criados: criados,
                   conferidos: conferidos, falhas: falhas});
  } catch(e){ return eaJson({ok:false, erro:String(e)}); }
})()
"""


def _rodar(script, carga, timeout=90):
    """Manda um passo e devolve o JSON dele. Erro do ExtendScript vira exceção
    aqui — passo que falhou não pode seguir como se tivesse dado certo."""
    bruto = adobe.extendscript(script % json.dumps(json.dumps(carga)), timeout=timeout)
    try:
        d = json.loads(bruto) if bruto else {}
    except Exception:
        raise Falhou("O Premiere respondeu algo que não é JSON: %s" % str(bruto)[:200])
    if not d.get("ok"):
        raise Falhou(d.get("erro") or "O Premiere recusou o passo sem explicar.")
    return d


# ---------------------------------------------------------------- preparo

def casar_midia(pid, aprovados):
    """Escreve no plano o arquivo de b-roll de cada beat.

    Sem isso o plano fica mentindo: o vídeo existe no disco, o beat continua
    "sem mídia", e a régua da skill barra a montagem por falta de arquivo.
    O caminho gravado é RELATIVO à pasta do projeto — plano com caminho absoluto
    quebra assim que o job vai para outra máquina."""
    p = projetos.ler(pid)
    raiz = projetos.dir_projeto(pid)
    por_id = {it["id"]: it for it in aprovados if it.get("arquivo")}
    casados, orfaos = [], []

    for b in p["plano"].get("beats", []):
        it = por_id.get(b.get("id"))
        if not it:
            continue
        arq = it["arquivo"]
        if not os.path.isfile(arq):
            orfaos.append(b.get("id"))
            continue
        rel = os.path.relpath(arq, raiz)
        b["midia"] = rel
        casados.append({"id": b.get("id"), "midia": rel})

    projetos.gravar_plano(pid, p["plano"])
    sobrando = [i for i in por_id if i not in {c["id"] for c in casados}]
    return {"casados": casados, "sem_arquivo": orfaos, "sem_beat": sobrando}


def _aprovados(pid):
    """Os b-rolls que passaram na etapa 9. Se a 9 não julgou nada, a montagem
    não inventa: quem decide o que entra no vídeo é o humano."""
    est = projetos.estado_pipeline(pid)
    itens = pipeline.aprovados(est, "vid_ok")
    if not itens:
        dados = pipeline.situacao(est, "animacao")["dados"].get("itens", [])
        if dados:
            raise Falhou(
                "Os b-rolls foram gerados mas nenhum está aprovado na etapa 9. "
                "Aprove os que vão entrar — montar sem esse aval é montar com "
                "material que você ainda não viu.")
        raise Falhou("Não há b-roll aprovado para montar. Rode as etapas 8 e 9 antes.")
    return itens


def plano_de_montagem(pid, corpo=None):
    """O que SERIA escrito na timeline. Não toca no Premiere — serve para o chat
    responder "o que você vai fazer?" antes de fazer."""
    corpo = corpo or {}
    aprovados = _aprovados(pid)
    casamento = casar_midia(pid, aprovados)

    p = projetos.ler(pid)
    saida = skill.compilar(p["plano"], caminho_plano=projetos.caminho(pid, "plano.json"))
    ed, marc = saida["edicao"], saida["marcadores"]

    raiz = projetos.dir_projeto(pid)
    inserts = []
    for b in ed["inserts"]:
        arq = b["arquivo"]
        arq = arq if os.path.isabs(arq) else os.path.join(raiz, arq)
        inserts.append({"id": os.path.splitext(os.path.basename(arq))[0],
                        "arquivo": arq, "inicio": b["inicio"], "fim": b["fim"],
                        "existe": os.path.isfile(arq)})

    return {
        "sequencia_alvo": "a sequência ATIVA do Premiere",
        "trilha_apoio": "V%d" % (corpo.get("trilha") or TRILHA_APOIO),
        "inserts": inserts,
        "punch": ed["punch"],
        "marcadores": marc,
        "casamento": casamento,
        "avisos": saida["avisos"],
        "fps": (p["plano"]["fonte"].get("fps") or 30),
    }


# ---------------------------------------------------------------- etapa 11

def montar(pid, corpo=None, log=None):
    """Escreve a montagem na sequência ativa e devolve o que LEU de volta."""
    corpo = corpo or {}
    diz = log or (lambda _: None)
    trilha = int(corpo.get("trilha") or TRILHA_APOIO)

    diz("conferindo a ponte com o Premiere…")
    v = adobe.verificar()
    if not v["leu_timeline"]:
        raise Falhou(v.get("detalhe") or
                     "Não consegui ler a timeline. Abra o Premiere, o projeto e o "
                     "painel do Tools PRO (Janela > Extensões) antes de montar.")

    pm = plano_de_montagem(pid, corpo)
    faltando = [i["id"] for i in pm["inserts"] if not i["existe"]]
    if faltando:
        raise Falhou("Estes b-rolls não estão no disco: %s. Gere de novo antes de montar."
                     % ", ".join(faltando))
    if not pm["inserts"]:
        raise Falhou("Nenhum b-roll aprovado com arquivo no disco.")

    alertas = list(pm["avisos"])

    diz("preparando a sequência…")
    prep = _rodar(PREPARAR, {"trilhas_video": trilha}, 60)
    if prep["trilhas_criadas"] == -1:
        alertas.append("Não consegui criar a trilha V%d — usando as que existem." % trilha)
    if not prep["v1"]:
        # Sequência vazia é caso normal: o editor abre uma nova e manda montar.
        # Sem isto o app parava e mandava ele fazer à mão a parte mais boba.
        corpo_body = projetos.ler(pid)["plano"]["fonte"]
        arq = corpo_body["body"]
        if os.path.isfile(arq):
            diz("a V1 está vazia — pondo o body nela…")
            _rodar(IMPORTAR, {"arquivos": [arq], "bin": BIN}, 180)
            _rodar(POSICIONAR, {"trilha": 1, "bin": BIN, "limpar": False,
                                "itens": [{"id": "BODY", "arquivo": arq, "inicio": 0.0,
                                           "fim": corpo_body.get("duracao") or 0}]}, 180)
            prep = _rodar(PREPARAR, {"trilhas_video": trilha}, 60)
        if not prep["v1"]:
            alertas.append("A V1 continua vazia: o punch não tem em que clipe pegar. "
                           "Ponha o body na V1 e rode esta etapa de novo.")

    arquivos = [i["arquivo"] for i in pm["inserts"]]
    diz("importando %d b-roll(s)…" % len(arquivos))
    imp = _rodar(IMPORTAR, {"arquivos": arquivos, "bin": BIN}, 180)
    nao_entrou = [i["arquivo"] for i in imp["itens"] if not i["entrou"]]
    if nao_entrou:
        raise Falhou("O Premiere não importou %d arquivo(s). O primeiro foi: %s"
                     % (len(nao_entrou), nao_entrou[0]))

    diz("posicionando na V%d…" % trilha)
    pos = _rodar(POSICIONAR, {
        "trilha": trilha, "bin": BIN, "limpar": corpo.get("limpar", True),
        "itens": [{"id": i["id"], "arquivo": i["arquivo"],
                   "inicio": i["inicio"], "fim": i["fim"]} for i in pm["inserts"]],
    }, 240)

    curtos = [i for i in pos["itens"] if i.get("curto")]
    for c in curtos:
        alertas.append("%s cobre %.2fs mas o beat pede %.2fs — o b-roll gerado é "
                       "mais curto que o trecho de fala." % (c["id"], c["durou"], c["pedido"]))
    ruins = [i for i in pos["itens"] if not i.get("ok")]
    for r in ruins:
        alertas.append("%s não entrou: %s" % (r["id"], r.get("motivo")))

    punch = {"pulado": True}
    if prep["v1"] and corpo.get("punch", True):
        segs = [s for s in pm["punch"] if abs(s[2] - 1.0) > 1e-6]
        if segs:
            diz("aplicando punch em %d janela(s)…" % len(segs))
            amostra = segs[0][0] + 0.1
            punch = _rodar(PUNCH, {"trilha": 1, "fps": pm["fps"],
                                   "segmentos": pm["punch"], "amostra": amostra}, 180)
            sem = [c for c in punch.get("clipes", []) if not c.get("ok")]
            for c in sem:
                alertas.append("punch não pegou em “%s”: %s"
                               % (c.get("clipe"), c.get("motivo") or "motivo não informado"))
            if punch.get("clipes") and all(c.get("achou_por") == "indice"
                                           for c in punch["clipes"] if c.get("ok")):
                alertas.append("A escala foi achada por posição, não por nome. Confira o "
                               "punch no Monitor de Programa antes de aprovar — as "
                               "propriedades vistas foram: %s"
                               % ", ".join(punch.get("propriedades_vistas") or []))
        else:
            punch = {"pulado": True, "motivo": "o estilo não pediu nenhuma janela de punch"}

    diz("escrevendo os marcadores…")
    marc = _rodar(MARCADORES, {"selo": SELO, "itens": pm["marcadores"]}, 180)
    if marc["criados"] != marc["conferidos"]:
        alertas.append("Criei %d marcadores mas reli %d. Confira a janela de marcadores."
                       % (marc["criados"], marc["conferidos"]))

    diz("relendo a timeline para conferir…")
    time.sleep(0.6)
    try:
        tl = adobe.timeline()
        conferido = tl.get("resumo")
        conferido["sequencia"] = tl.get("sequencia")
    except Exception as e:
        conferido = None
        alertas.append("Montei, mas não consegui reler a timeline para conferir: %s" % e)

    postos = [i for i in pos["itens"] if i.get("ok")]
    return {
        "projeto": prep["projeto"],
        "sequencia": prep["sequencia"],
        "trilha_apoio": "V%d" % trilha,
        "trilhas_criadas": prep["trilhas_criadas"],
        "importados": imp["novos"],
        "body_na_v1": len(prep["v1"]),
        "inserts_pedidos": len(pm["inserts"]),
        "inserts_postos": len(postos),
        "itens": pos["itens"],
        "punch": punch,
        "marcadores": marc,
        "cobertura": round(sum(i["durou"] for i in postos) /
                           (p_dur(pid) or 1) * 100, 1),
        "conferido": conferido,
        "alertas": alertas,
        "audio_do_broll": "fora — o b-roll entrou só na trilha de vídeo",
    }


def p_dur(pid):
    try:
        return projetos.ler(pid)["plano"]["fonte"].get("duracao") or 0
    except Exception:
        return 0
