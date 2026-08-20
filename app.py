#!/usr/bin/env python3
"""
Editor Automático — janela + servidor local.

Servidor em 127.0.0.1 numa porta efêmera. Nunca 0.0.0.0: o app roda em rede de
estúdio e ninguém quer o projeto do cliente exposto na rede do prédio.

Só stdlib aqui de propósito. Cada dependência a mais é uma chance a mais do
PyInstaller falhar no empacotamento, e empacotar é o passo que decide se o app
existe pro aluno ou só pra quem tem terminal.
"""

import json
import mimetypes
import os
import secrets
import socket
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

# ANTES de qualquer import que faça `which`: um .app aberto pelo Finder não
# herda o PATH do shell, e sem isto NENHUM CLI é encontrado.
from nucleo import caminho  # noqa: E402
caminho.ajustar()

# Modo MCP: o Claude sobe ESTE MESMO binário com --mcp para ter as ferramentas
# do app. Antes eu apontava para `.venv/bin/python` + um .py solto — nada disso
# existe dentro do .app, então o servidor nunca subia e o Claude ficava sem
# ferramenta nenhuma enquanto a tela dizia "conectada".
if "--mcp" in sys.argv:
    from nucleo import mcp_servidor
    mcp_servidor.main()
    sys.exit(0)

from nucleo import (adobe, ambiente, atualizacao, chaves, claude, conta,  # noqa: E402
                    conversa, conversas,
                    decupar, etapas, gerar, montagem, pipeline, plugin,
                    ponte, projetos, qc, servicos, skill, voz)

WEB = os.path.join(RAIZ, "web")

# Token de sessão: qualquer página aberta no navegador da máquina consegue falar
# com 127.0.0.1. Sem isso, um site aberto numa aba poderia listar e apagar
# projetos por trás. O token vai na URL que a janela abre.
TOKEN = secrets.token_urlsafe(16)

TAREFAS = {}
_trava = threading.Lock()


def tarefa_nova(rotulo):
    tid = secrets.token_hex(6)
    with _trava:
        TAREFAS[tid] = {"id": tid, "rotulo": rotulo, "estado": "rodando",
                        "log": [], "passos": [], "resultado": None, "erro": None}
    return tid


def tarefa_log(tid, linha):
    """Aceita linha de texto OU passo estruturado.

    O passo estruturado é o que faz a tela mostrar cada etapa NA HORA — chamada
    de ferramenta, resultado, texto — em vez de só a última linha de um log."""
    with _trava:
        t = TAREFAS.get(tid)
        if not t:
            return
        if isinstance(linha, dict):
            if linha.get("atualiza"):
                i = linha.get("indice")
                if i is not None and 0 <= i < len(t["passos"]):
                    t["passos"][i] = {k: v for k, v in linha.items()
                                      if k not in ("indice", "atualiza")}
            else:
                t["passos"].append(linha)
        else:
            t["log"] = (t["log"] + [str(linha)])[-40:]


def tarefa_fim(tid, resultado=None, erro=None):
    with _trava:
        t = TAREFAS.get(tid)
        if t:
            t["estado"] = "erro" if erro else "pronto"
            t["resultado"], t["erro"] = resultado, erro


def em_fundo(rotulo, fn):
    tid = tarefa_nova(rotulo)

    def alvo():
        try:
            tarefa_fim(tid, resultado=fn(lambda l: tarefa_log(tid, l)))
        except Exception as e:
            tarefa_fim(tid, erro=str(e) or e.__class__.__name__)
    threading.Thread(target=alvo, daemon=True).start()
    return tid


# ------------------------------------------------------------------ rotas

def rota_estado(_):
    e = conta.estado()
    return {
        "conta": e,
        "servicos": servicos.estado(),
        "skill": {"instalada": skill.instalada(), "estilos": skill.estilos()},
        "ferramentas": {
            "whisper": decupar.disponivel(),
            "ffmpeg": _tem("ffmpeg"),
            "ffprobe": _tem("ffprobe"),
        },
    }


def _tem(b):
    from shutil import which
    return which(b) is not None


def rota_projetos(_):
    return {"projetos": projetos.listar()}


def rota_projeto_novo(corpo):
    caminho = (corpo.get("video") or "").strip()
    if not caminho:
        raise ValueError("Escolha o vídeo do body primeiro.")
    caminho = os.path.expanduser(caminho)
    if not os.path.isfile(caminho):
        raise ValueError("Esse arquivo não existe: " + caminho)
    nome = (corpo.get("nome") or os.path.splitext(os.path.basename(caminho))[0]).strip()
    return projetos.criar(nome, caminho)


def rota_projeto(pid):
    p = projetos.ler(pid)
    t = decupar.ler(pid)
    p["transcricao"] = {"tem": bool(t), "palavras": len(t["palavras"]) if t else 0,
                        "idioma": t.get("idioma") if t else None}
    return p


def rota_plano(pid, corpo):
    plano = corpo.get("plano")
    if not isinstance(plano, dict):
        raise ValueError("Plano inválido.")
    # a fala que justifica cada insert vem da transcrição, não da digitação
    for b in plano.get("beats", []):
        if b.get("tipo") == "insert" and not b.get("fala"):
            b["fala"] = decupar.frase_em(pid, b.get("inicio", 0), b.get("fim", 0))
    projetos.gravar_plano(pid, plano)
    return rota_projeto(pid)


def rota_revisao(pid):
    caminho = projetos.caminho(pid, "plano.json")
    p = projetos.ler(pid)
    r = skill.revisar(caminho, p["plano"].get("estilo"))
    if r["liberado"]:
        projetos.marcar_etapa(pid, "montar")
    return r


def rota_compilar(pid):
    p = projetos.ler(pid)
    saida = skill.compilar(p["plano"])
    d = projetos.caminho(pid, "saida")
    os.makedirs(d, exist_ok=True)
    for nome, dados in (("edicao.json", saida["edicao"]),
                        ("marcadores.json", saida["marcadores"])):
        tmp = os.path.join(d, nome + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp, os.path.join(d, nome))
    return {"avisos": saida["avisos"], "pasta": d,
            "inserts": len(saida["edicao"]["inserts"]),
            "punch": len(saida["edicao"]["punch"]),
            "marcadores": len(saida["marcadores"])}


# Cada entrada é o trabalho da etapa. Nenhuma conclui a si mesma — todas
# entregam em "aguardando aprovação". Quem conclui é o usuário, sempre.
EXECUTORES = {
    "analise":  lambda pid, c, log: etapas.analise(pid),
    "copy":     lambda pid, c, log: etapas.verificar_copy(pid, c.get("texto"), c.get("arquivo")),
    "marcacao": lambda pid, c, log: etapas.marcar_timeline(pid),
    "plano":    lambda pid, c, log: etapas.mapa_do_plano(pid),
    "avatar":   lambda pid, c, log: gerar.avatares(pid, c, log),
    "imagens":  lambda pid, c, log: gerar.imagens(pid, c, log),
    "img_ok":   lambda pid, c, log: _herdar(pid, "imagens"),
    "animacao": lambda pid, c, log: gerar.animar(
        pid, c, pipeline.aprovados(projetos.estado_pipeline(pid), "img_ok"), log),
    "vid_ok":   lambda pid, c, log: _herdar(pid, "animacao"),
    "acabamento": lambda pid, c, log: _acabamento(pid, c, log),
    "montagem": lambda pid, c, log: montagem.montar(pid, c, log),
    "qc":       lambda pid, c, log: qc.conferir(pid, c, log),
}


def _acabamento(pid, corpo, log):
    """Letterings, voz e legendas.

    A VOZ sai da ElevenLabs e de mais lugar nenhum — decisão do usuário
    (o gerador de voz do MiniMax não entra). O texto narrado é a copy VALIDADA
    na etapa 2; reescrever aqui invalidaria aquela validação."""
    est = projetos.estado_pipeline(pid)
    texto = (corpo.get("texto")
             or pipeline.situacao(est, "copy")["dados"].get("copy") or "").strip()
    if not texto:
        raise ValueError("Sem copy validada para narrar. Rode a etapa 2 antes.")

    log and log("conferindo a cota da ElevenLabs…")
    orc = voz.orcamento_voz(texto)
    if not orc["suficiente"]:
        raise ValueError("A cota da ElevenLabs não cobre %d caracteres (sobram %s)."
                         % (orc["caracteres"], orc["sobra"]))

    log and log("gerando a voz — %d caracteres" % orc["caracteres"])
    r = voz.falar(pid, texto, corpo.get("voz"), "narracao.mp3")

    p = projetos.ler(pid)
    letterings = [b for b in p["plano"].get("beats", []) if b.get("tipo") == "lettering"]
    return {"voz": r, "orcamento": orc,
            "letterings": [{"id": b.get("id"), "texto": b.get("texto") or b.get("intencao"),
                            "inicio": b.get("inicio"), "fim": b.get("fim")}
                           for b in letterings],
            "fonte_audio": "ElevenLabs (única fonte de voz do app)"}

# Etapas que chamam plataforma: demoram minutos e gastam. Rodam em segundo plano
# com log ao vivo, senão a janela congela e o usuário mata o app no meio de uma
# geração já paga.
# A montagem e o QC não gastam crédito, mas falam com o Premiere e decodificam
# vídeo — minutos de espera. Fora do segundo plano, a janela congela.
LONGAS = {"avatar", "imagens", "animacao", "acabamento", "montagem", "qc"}


def _herdar(pid, de):
    """As etapas de aprovação por item não geram nada: recebem o que a etapa
    anterior produziu para o usuário julgar item a item."""
    est = projetos.estado_pipeline(pid)
    itens = pipeline.situacao(est, de)["dados"].get("itens", [])
    if not itens:
        raise ValueError("A etapa anterior não produziu itens para julgar.")
    return {"itens": [dict(i) for i in itens], "origem": de}


def rota_pipeline(pid):
    est = projetos.estado_pipeline(pid)
    pnl = pipeline.painel(est)
    pnl["dados"] = {eid: pipeline.situacao(est, eid)["dados"] for eid in pipeline.ORDEM}
    return pnl


def rota_etapa_iniciar(pid, eid, corpo):
    """O ponto onde o portão vale dinheiro: `pipeline.iniciar` levanta Bloqueado
    ANTES de qualquer chamada paga. A ordem destas linhas é a regra inteira."""
    est = projetos.estado_pipeline(pid)
    pipeline.iniciar(est, eid)           # <- portão. Nada sai daqui sem passar.
    projetos.gravar_pipeline(pid, est)

    exec_ = EXECUTORES.get(eid)
    if not exec_:
        pipeline.marcar(est, eid, pipeline.PENDENTE)
        projetos.gravar_pipeline(pid, est)
        raise ValueError("A etapa “%s” ainda não tem executor ligado."
                         % pipeline.POR_ID[eid]["nome"])

    def trabalho(log):
        est2 = projetos.estado_pipeline(pid)
        try:
            dados = exec_(pid, corpo or {}, log)
        except Exception:
            # devolve para pendente: etapa travada em "gerando" é etapa morta
            pipeline.marcar(est2, eid, pipeline.PENDENTE)
            projetos.gravar_pipeline(pid, est2)
            raise
        pipeline.entregar(est2, eid, dados)
        projetos.gravar_pipeline(pid, est2)
        return {"etapa": eid}

    if eid in LONGAS:
        return {"tarefa": em_fundo(pipeline.POR_ID[eid]["nome"], trabalho),
                "longa": True}
    trabalho(lambda l: None)
    return rota_pipeline(pid)


def _quem():
    return conta.estado().get("nome") or "usuário"


def rota_etapa_julgar(pid, eid, acao, corpo):
    est = projetos.estado_pipeline(pid)
    nota = (corpo or {}).get("nota", "")
    if acao == "aprovar":
        pipeline.aprovar(est, eid, _quem(), nota)
    elif acao == "rejeitar":
        pipeline.rejeitar(est, eid, _quem(), nota)
    elif acao == "reabrir":
        pipeline.reabrir(est, eid, _quem(), nota)
    elif acao == "item":
        pipeline.julgar_item(est, eid, corpo["item"], corpo["acao"], _quem(), nota)
    else:
        raise ValueError("Ação desconhecida.")
    projetos.gravar_pipeline(pid, est)
    return rota_pipeline(pid)


def rota_motores(pid, tipo, quantos):
    """O catálogo com preço ao vivo — é o que deixa trocar o motor sabendo o custo."""
    if tipo == "imagem":
        return {"opcoes": gerar.opcoes_imagem(quantos), "saldo": gerar.saldo()}
    p = projetos.ler(pid)
    est = projetos.estado_pipeline(pid)
    ancora = pipeline.situacao(est, "avatar")["dados"].get("escolhida")
    beats = [b for b in p["plano"].get("beats", []) if b.get("tipo") == "insert"]
    exemplo = beats[0] if beats else {"inicio": 0, "fim": 5}
    return {"opcoes": gerar.opcoes_video(exemplo, bool(ancora), quantos),
            "saldo": gerar.saldo()}


ROTAS_GET = {
    "/api/estado": lambda h: rota_estado(None),
    "/api/projetos": lambda h: rota_projetos(None),
    "/api/estilos": lambda h: {"estilos": skill.estilos()},
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    # -------------------------------------------------------------- util
    def _json(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _autorizado(self):
        return self.headers.get("X-Token") == TOKEN

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def _estatico(self, caminho):
        rel = caminho.lstrip("/") or "index.html"
        alvo = os.path.normpath(os.path.join(WEB, rel))
        if not alvo.startswith(WEB) or not os.path.isfile(alvo):
            self.send_response(404), self.end_headers()
            return
        tipo = mimetypes.guess_type(alvo)[0] or "application/octet-stream"
        with open(alvo, "rb") as f:
            dados = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _arquivo_do_projeto(self):
        """Serve um arquivo gerado pelo app (mosaico do QC, por exemplo).

        Duas travas, e as duas são necessárias: o token vai na QUERY porque
        `<img>` não manda cabeçalho, e o caminho tem que estar DENTRO da pasta
        de projetos. Sem a segunda, esta rota viraria leitura de disco inteira
        para qualquer página aberta no navegador da máquina."""
        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(self.path).query)
        if (q.get("t") or [""])[0] != TOKEN:
            self.send_response(403), self.end_headers()
            return
        alvo = os.path.realpath(os.path.expanduser((q.get("p") or [""])[0]))
        raiz = os.path.realpath(projetos.RAIZ)
        if not alvo.startswith(raiz + os.sep) or not os.path.isfile(alvo):
            self.send_response(404), self.end_headers()
            return
        tipo = mimetypes.guess_type(alvo)[0] or "application/octet-stream"
        with open(alvo, "rb") as f:
            dados = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    # -------------------------------------------------------------- GET
    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho in ("/", "/index.html"):
            return self._estatico("index.html")
        if caminho == "/api/arquivo":
            return self._arquivo_do_projeto()
        if not caminho.startswith("/api/"):
            return self._estatico(caminho)
        if not self._autorizado():
            return self._json({"erro": "Sessão inválida."}, 403)

        try:
            if caminho in ROTAS_GET:
                return self._json(ROTAS_GET[caminho](self))
            partes = caminho.strip("/").split("/")
            if len(partes) == 3 and partes[1] == "projetos":
                return self._json(rota_projeto(partes[2]))
            if caminho == "/api/claude":
                return self._json(claude.estado_conta())
            if caminho == "/api/adobe":
                # Verificado de verdade: painel + ler projeto + ler timeline +
                # o servidor MCP subir. Dizer "conectada" só porque existe um
                # painel na porta era o que fazia a tela mentir para o usuário.
                e = adobe.estado()
                v = adobe.verificar()
                e["verificado"] = v
                e["mcp"] = conversa.mcp_vivo()
                e["utilizavel"] = bool(v["leu_timeline"] and e["mcp"]["ok"])
                return self._json(e)
            if caminho == "/api/conversas":
                return self._json({"conversas": conversas.listar()})
            if len(partes) == 3 and partes[1] == "conversas":
                cid = partes[2]
                m = conversas.meta(cid)
                return self._json({"mensagens": conversas.mensagens(cid),
                                   "meta": m})
            if caminho == "/api/conversa":
                lista = conversas.listar()
                cid = lista[0]["id"] if lista else None
                return self._json({"conversa": cid,
                                   "mensagens": conversas.mensagens(cid) if cid else []})
            if caminho == "/api/atualizacao":
                return self._json(atualizacao.conferir())
            if caminho == "/api/plugin":
                return self._json(plugin.estado())
            if caminho == "/api/ponte":
                return self._json(ponte.estado())
            if caminho == "/api/ambiente":
                d = ambiente.conferir()
                from nucleo import caminho as _cam
                d["diagnostico"] = _cam.diagnostico()
                return self._json(d)
            if len(partes) == 4 and partes[1] == "projetos" and partes[3] == "conversa":
                return self._json({"mensagens": conversa.historico(partes[2])})
            if caminho == "/api/vozes":
                return self._json({"vozes": voz.vozes(),
                                   "assinatura": voz.assinatura()})
            if len(partes) == 4 and partes[1] == "projetos" and partes[3] == "orcamento":
                return self._json(gerar.orcamento(partes[2]))
            if len(partes) == 5 and partes[1] == "projetos" and partes[3] == "motores":
                q = int((self.path.split("q=") + ["1"])[1].split("&")[0]) \
                    if "q=" in self.path else 1
                return self._json(rota_motores(partes[2], partes[4], q))
            if len(partes) == 4 and partes[1] == "projetos" and partes[3] == "pipeline":
                return self._json(rota_pipeline(partes[2]))
            if len(partes) == 4 and partes[1] == "projetos" and partes[3] == "revisao":
                return self._json(rota_revisao(partes[2]))
            if len(partes) == 4 and partes[1] == "projetos" and partes[3] == "transcricao":
                return self._json(decupar.ler(partes[2]) or {"palavras": []})
            if len(partes) == 3 and partes[1] == "tarefas":
                with _trava:
                    return self._json(TAREFAS.get(partes[2]) or {"erro": "sem tarefa"})
            return self._json({"erro": "rota não existe"}, 404)
        except Exception as e:
            traceback.print_exc()
            return self._json({"erro": str(e) or e.__class__.__name__}, 400)

    # -------------------------------------------------------------- POST
    def do_POST(self):
        caminho = self.path.split("?")[0]
        if not self._autorizado():
            return self._json({"erro": "Sessão inválida."}, 403)
        try:
            corpo = self._corpo()
            partes = caminho.strip("/").split("/")

            if caminho == "/api/conta/entrar":
                return self._json(conta.entrar(corpo.get("email", ""), corpo.get("senha", "")))
            if caminho == "/api/conta/cadastrar":
                return self._json(conta.cadastrar(corpo.get("nome", ""),
                                                  corpo.get("email", ""),
                                                  corpo.get("senha", "")))
            if caminho == "/api/conta/senha":
                return self._json(conta.trocar_senha(corpo.get("atual", ""),
                                                     corpo.get("nova", "")))
            if caminho == "/api/conta/sair":
                return self._json(conta.sair())

            if caminho == "/api/servicos/chave":
                chaves.gravar(corpo["servico"], corpo.get("valor", ""))
                return self._json({"ok": True})
            if caminho == "/api/servicos/testar":
                return self._json(servicos.testar(corpo["servico"]))
            if caminho == "/api/servicos/entrar":
                s = corpo["servico"]
                if s == "claude":
                    return self._json(claude.entrar())
                if s == "heygen":
                    return self._json(servicos.heygen_entrar())
                if s == "minimax":
                    return self._json(servicos.minimax_entrar(corpo.get("chave")))
                return self._json(servicos.higgs_entrar())
            if caminho == "/api/servicos/sair":
                s = corpo["servico"]
                if s == "claude":
                    return self._json(claude.sair())
                if s == "heygen":
                    return self._json(servicos.heygen_sair())
                if s == "minimax":
                    return self._json(servicos.minimax_sair())
                return self._json(servicos.higgs_sair())

            if caminho == "/api/claude/metodo":
                return self._json({"metodo": claude.definir_metodo(corpo["metodo"])})
            if caminho == "/api/claude/testar":
                return self._json(claude.testar_conta())

            if caminho == "/api/conversas/nova":
                return self._json({"conversa": conversas.criar()})
            if caminho == "/api/conversas/apagar":
                return self._json({"ok": conversas.apagar(corpo["conversa"])})

            if caminho == "/api/conversa":
                cid = corpo.get("conversa")
                tid = em_fundo("Conversando", lambda log: conversa.falar(
                    cid, corpo.get("texto", ""), corpo.get("anexos"),
                    conta.estado().get("nome") or "usuário", log))
                return self._json({"tarefa": tid})

            if caminho == "/api/atualizacao/baixar":
                tid = em_fundo("Baixando a atualização",
                               lambda log: atualizacao.baixar(ao_vivo=log))
                return self._json({"tarefa": tid})
            if caminho == "/api/ponte/preparar":
                return self._json(ponte.preparar())
            if caminho == "/api/plugin/instalar":
                tid = em_fundo("Instalando o plugin do Premiere",
                               lambda log: plugin.instalar(log))
                return self._json({"tarefa": tid})

            if caminho == "/api/ambiente/instalar":
                qual = corpo.get("qual")
                tid = em_fundo("Preparando o ambiente",
                               lambda log: (ambiente.instalar(qual, log) if qual
                                            else ambiente.instalar_tudo(log)))
                return self._json({"tarefa": tid})

            if caminho == "/api/projetos":
                return self._json(rota_projeto_novo(corpo))

            if len(partes) == 4 and partes[1] == "projetos":
                pid, acao = partes[2], partes[3]
                if acao == "plano":
                    return self._json(rota_plano(pid, corpo))
                if acao == "decupar":
                    tid = em_fundo("Decupando a fala", lambda log: decupar.rodar(
                        pid, corpo.get("modelo", "medium"), log))
                    return self._json({"tarefa": tid})
                if acao == "compilar":
                    return self._json(rota_compilar(pid))
                if acao == "apagar":
                    return self._json({"ok": projetos.apagar(pid)})
                if acao == "conversa":
                    # A conversa roda em segundo plano: uma rodada com ferramentas
                    # pode levar minutos, e travar a janela nisso mata o app.
                    tid = em_fundo("Conversando", lambda log: conversa.falar(
                        pid, corpo.get("texto", ""), corpo.get("anexos"),
                        conta.estado().get("nome") or "usuário", log))
                    return self._json({"tarefa": tid})

            # /api/projetos/{pid}/etapa/{eid}/{acao}
            if len(partes) == 6 and partes[1] == "projetos" and partes[3] == "etapa":
                pid, eid, acao = partes[2], partes[4], partes[5]
                if acao == "iniciar":
                    return self._json(rota_etapa_iniciar(pid, eid, corpo))
                return self._json(rota_etapa_julgar(pid, eid, acao, corpo))
            return self._json({"erro": "rota não existe"}, 404)
        except pipeline.Bloqueado as e:
            return self._json({"erro": str(e), "bloqueado": True}, 409)
        except Exception as e:
            traceback.print_exc()
            return self._json({"erro": str(e) or e.__class__.__name__}, 400)


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    porta = porta_livre()
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/?t=%s" % (porta, TOKEN)

    try:
        import webview
    except ImportError:
        # Sem pywebview ainda dá pra trabalhar — o app não trava por causa da moldura
        print("Janela nativa indisponível; abrindo no navegador.\n" + url)
        webbrowser.open(url)
        threading.Event().wait()
        return

    janela = webview.create_window(
        "Editor Automático", url,
        width=1240, height=820, min_size=(1020, 680),
        background_color="#0B0C0E")
    webview.start(gui="cocoa" if sys.platform == "darwin" else None)


if __name__ == "__main__":
    main()
