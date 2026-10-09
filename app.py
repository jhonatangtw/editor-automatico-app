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


def _codigo_externo():
    """Se existe código baixado mais novo, é ELE que roda.

    O pacote instalado passa a ser também um carregador: correção de código não
    exige mais reinstalar o app inteiro. Ver `nucleo/codigo.py` para as travas.

    ⚠️ Purgar `sys.modules` antes de entregar o controle não é zelo: sem isso o
    `nucleo` embutido já estaria carregado e o app novo importaria os módulos
    VELHOS — metade código novo, metade antigo, e nenhum sintoma óbvio."""
    try:
        from nucleo import codigo
    except Exception:
        return None
    d = codigo.ativo()
    if not d or os.path.realpath(d["pasta"]) == os.path.realpath(RAIZ):
        return None
    # ⚠️ A quarentena vale só para a JANELA. O modo --mcp é disparado pelo Claude
    # várias vezes por conversa e morre logo — ele nunca chega no ponto que
    # limpa a marca, então marcaria a cada chamada e a abertura seguinte
    # descartaria uma atualização que estava perfeita.
    janela = "--mcp" not in sys.argv
    if janela:
        if codigo.em_quarentena():
            codigo.descartar("o código baixado não abriu na tentativa anterior")
            return None
        codigo.marcar_tentativa(d["versao"])
    for m in [m for m in sys.modules if m == "nucleo" or m.startswith("nucleo.")]:
        del sys.modules[m]
    sys.path.insert(0, d["pasta"])
    return d["pasta"]


# ⚠️ SÓ quando este arquivo é EXECUTADO. O `mcp_servidor` faz `from app import
# ...`, e sem esta guarda um simples import entregaria o controle ao código
# externo com run_name="__main__" — abrindo uma janela e travando ali. Foi o que
# aconteceu na primeira varredura de rotas que rodei.
_EXTERNO = _codigo_externo() if __name__ == "__main__" else None
if _EXTERNO:
    import runpy
    runpy.run_path(os.path.join(_EXTERNO, "app.py"), run_name="__main__")
    sys.exit(0)

# ANTES de qualquer subprocesso: no Windows o `so` faz todo Popen nascer sem
# janela e ler a saída em UTF-8 — sem isto o terminal pisca e o acento quebra.
from nucleo import so  # noqa: E402,F401

# ANTES de qualquer import que faça `which`: um .app aberto pelo Finder não
# herda o PATH do shell, e sem isto NENHUM CLI é encontrado.
from nucleo import caminho  # noqa: E402
caminho.ajustar()

# ANTES de qualquer HTTPS: o Python empacotado procura os certificados no
# caminho da máquina onde foi COMPILADO, que não existe na máquina do aluno.
from nucleo import rede  # noqa: E402
rede.preparar()

# Modo MCP: o Claude sobe ESTE MESMO binário com --mcp para ter as ferramentas
# do app. Antes eu apontava para `.venv/bin/python` + um .py solto — nada disso
# existe dentro do .app, então o servidor nunca subia e o Claude ficava sem
# ferramenta nenhuma enquanto a tela dizia "conectada".
if "--mcp" in sys.argv:
    from nucleo import mcp_servidor
    mcp_servidor.main()
    sys.exit(0)

from nucleo import instalar_mac  # noqa: E402
from nucleo import (adobe, ambiente, atualizacao, cancelar, chaves, claude,  # noqa: E402
                    conta, conversa, conversas,
                    decupar, etapas, gerar, ia, midia, montagem, pipeline, plugin,
                    ponte, preparar, projetos, qc, servicos, skill, skills, voz)

WEB = os.path.join(RAIZ, "web")

# Token de sessão: qualquer página aberta no navegador da máquina consegue falar
# com 127.0.0.1. Sem isso, um site aberto numa aba poderia listar e apagar
# projetos por trás. O token vai na URL que a janela abre.
TOKEN = secrets.token_urlsafe(16)

TAREFAS = {}
CONTROLES = {}          # tid -> cancelar.Controle, só das tarefas que sabem parar
_trava = threading.Lock()


def tarefa_nova(rotulo):
    tid = secrets.token_hex(6)
    with _trava:
        TAREFAS[tid] = {"id": tid, "rotulo": rotulo, "estado": "rodando",
                        "log": [], "passos": [], "resultado": None, "erro": None,
                        "seq": 0, "versoes": []}
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
            # a ETAPA em curso ("abrindo o Claude", "conferindo o Adobe") não é
            # passo da conversa: é o que a tela mostra ao lado do "Pensando…"
            # enquanto nada mais chegou — antes a tela ficava muda nesse trecho
            if linha.get("tipo") == "etapa":
                t["etapa"] = linha.get("texto") or ""
                return
            # cada passo guarda a "versão" em que mudou pela última vez: a tela
            # pede só o que mudou desde a versão que já tem (`?v=`). Com o texto
            # chegando letra a letra e centenas de ações numa rodada longa,
            # mandar a lista inteira a cada pesquisa travava a janela.
            t["seq"] = t.get("seq", 0) + 1
            versoes = t.setdefault("versoes", [])
            if linha.get("atualiza"):
                i = linha.get("indice")
                if i is not None and 0 <= i < len(t["passos"]):
                    t["passos"][i] = {k: v for k, v in linha.items()
                                      if k not in ("indice", "atualiza")}
                    versoes[i] = t["seq"]
            else:
                t["passos"].append(linha)
                versoes.append(t["seq"])
        else:
            t["log"] = (t["log"] + [str(linha)])[-40:]


def tarefa_fim(tid, resultado=None, erro=None, estado=None):
    with _trava:
        t = TAREFAS.get(tid)
        if t:
            t["estado"] = estado or ("erro" if erro else "pronto")
            t["resultado"], t["erro"] = resultado, erro
        CONTROLES.pop(tid, None)


def tarefa_ver(tid, desde=None):
    """O retrato da tarefa para a tela — com `cancelavel` calculado na hora:
    só é verdade enquanto existe um processo de pé para encerrar.

    Com `desde` (a versão que a tela já tem), em vez da lista inteira vão só
    os passos que mudaram depois dela, em `novos` = [[índice, passo], …], e o
    `total` para a tela saber o tamanho da lista."""
    with _trava:
        t = TAREFAS.get(tid)
        if not t:
            return None
        versoes = list(t.get("versoes") or [])
        t = dict(t)
        t["passos"] = list(t["passos"])
        c = CONTROLES.get(tid)
    t.pop("versoes", None)
    t["cancelavel"] = bool(c and t["estado"] == "rodando" and c.cancelavel)
    if desde is not None:
        t["novos"] = [[i, p] for i, p in enumerate(t["passos"])
                      if i < len(versoes) and versoes[i] > desde]
        t["total"] = len(t["passos"])
        del t["passos"]
    return t


def tarefa_cancelar(tid):
    with _trava:
        c = CONTROLES.get(tid)
    if not c:
        return {"ok": False, "msg": "Esta tarefa não pode ser cancelada."}
    c.cancelar()
    return {"ok": True}


def em_fundo(rotulo, fn, controle=None):
    tid = tarefa_nova(rotulo)
    if controle is not None:
        with _trava:
            CONTROLES[tid] = controle

    def alvo():
        try:
            tarefa_fim(tid, resultado=fn(lambda l: tarefa_log(tid, l)))
        except cancelar.Cancelado:
            tarefa_fim(tid, estado="cancelado")
        except Exception as e:
            tarefa_fim(tid, erro=str(e) or e.__class__.__name__)
    threading.Thread(target=alvo, daemon=True).start()
    return tid


# ------------------------------------------------------------------ rotas

def rota_estado(_, forcar=False):
    """O retrato completo — inclui a licença, que é uma ida ao servidor.

    ⚠️ Não use isto para reconferir contas. É a rota mais CARA que existe (~3s,
    e uma delas é rede), e a tela de Contas passou a reconferir sozinha. Bater
    no servidor de licença a cada volta de aba seria transformar um conserto de
    interface num pequeno ataque ao nosso próprio servidor. Para isso existe
    `/api/servicos`."""
    if forcar:
        caminho.recarregar(com_shell=True)
    e = conta.estado()
    return {
        "conta": e,
        "servicos": servicos.estado(reler_path=not forcar),
        "skill": {"instalada": skill.instalada(), "estilos": skill.estilos()},
        "ferramentas": {
            "whisper": decupar.disponivel(),
            "ffmpeg": _tem("ffmpeg"),
            "ffprobe": _tem("ffprobe"),
        },
    }


def rota_servicos(forcar=False):
    """Só as contas, lidas do sistema AGORA — sem tocar no servidor de licença.

    É a rota que a tela de Contas chama toda vez que volta para a aba, depois de
    cada login e enquanto espera um login de navegador terminar. Por isso ela é
    barata de propósito: o que ela faz é perguntar aos CLIs e ao cofre."""
    if forcar:
        caminho.recarregar(com_shell=True)
    d = servicos.estado(reler_path=not forcar)
    d["ferramentas"] = {"whisper": decupar.disponivel(),
                        "ffmpeg": _tem("ffmpeg"), "ffprobe": _tem("ffprobe")}
    return d


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


# ------------------------------------------------------------- conversa nova
# A tela da Conversa (web/conversa-ui.js) usa estas rotas. Ela também é montada
# no painel do Tools PRO, dentro do Premiere — por isso nada aqui assume que a
# página foi servida por este app: tudo é JSON e o token vai no cabeçalho.

def rota_conversa_ver(cid):
    m = conversas.meta(cid)
    pid = m.get("projeto")
    if pid:
        try:
            m["projeto_nome"] = projetos.ler(pid)["plano"].get("job") or pid
        except Exception:
            m["projeto_nome"] = pid
    m["destino"] = midia.destino_da_conversa(cid)
    # prévia das entregas também nas conversas antigas (e reconferida: arquivo
    # apagado não vira miniatura quebrada)
    return {"conversa": cid, "mensagens": midia.anotar(conversas.mensagens(cid)), "meta": m}


# ------------------------------------------------------------- entregas de mídia
# A prévia das entregas na Conversa (web/conversa-ui.js). Toda rota aqui passa
# pela trava de `midia.permitido`: só o que está nas pastas do app, na pasta do
# job ligada a um projeto ou na pasta de projeto que o usuário escolheu.

def _caminho_da_query(h):
    from urllib.parse import parse_qs, urlparse
    return (parse_qs(urlparse(h.path).query).get("p") or [""])[0]


def rota_midia_destinos(cid):
    return {"destino": midia.destino_da_conversa(cid),
            "projetos": midia.projetos_para_escolher()}


def rota_midia_baixar(corpo):
    """Baixa a entrega remota para a pasta do PROJETO da conversa. Sem projeto
    NÃO baixa em lugar nenhum: devolve 409 com a lista para a tela perguntar."""
    cid = corpo.get("conversa")
    d = midia.destino_da_conversa(cid)
    if not d:
        return 409, {"erro": "Em qual projeto salvar?", "precisa_destino": True,
                     "projetos": midia.projetos_para_escolher()}
    try:
        r = midia.baixar(corpo.get("url") or "", d["pasta"], corpo.get("tipo"))
    except midia.ErroBaixar as e:
        return 400, {"erro": str(e)}
    r["destino"] = d
    return 200, r


def rota_destino(cid, corpo):
    """A conversa sem projeto escolhe onde guardar as entregas: um projeto do
    app (a conversa passa a ser dele) ou uma pasta de projeto do disco."""
    if not cid or "/" in cid or ".." in cid or not os.path.isdir(conversas.dir_conversa(cid)):
        raise ValueError("Conversa inválida.")
    if corpo.get("projeto"):
        pid = corpo["projeto"]
        if "/" in pid or ".." in pid or not os.path.isdir(projetos.dir_projeto(pid)):
            raise ValueError("Projeto não encontrado.")
        conversas.gravar_meta(cid, projeto=pid)
    else:
        pasta = corpo.get("pasta")
        if corpo.get("escolher"):
            pasta = midia.escolher_pasta()
            if not pasta:
                return {"ok": False, "cancelado": True, "destino": midia.destino_da_conversa(cid)}
        motivo = midia.pasta_valida_para_projeto(pasta)
        if motivo:
            raise ValueError(motivo)
        pasta = os.path.realpath(os.path.expanduser(pasta))
        midia.lembrar_destino(pasta)
        conversas.gravar_meta(cid, pasta_projeto=pasta)
    midia.esquecer_raizes()
    return {"ok": True, "destino": midia.destino_da_conversa(cid)}


def rota_aprovacao(cid):
    """O cartão de aprovação que aparece DENTRO da conversa.

    Só aparece quando aprovar a etapa que está esperando LIBERA uma etapa que
    gasta crédito. O cartão não aprova nada sozinho: os botões chamam a mesma
    rota do botão Aprovar do pipeline (`/api/projetos/{pid}/etapa/{eid}/aprovar`),
    que grava quem aprovou e quando. Nenhuma trava muda — é só outra porta
    para a MESMA decisão explícita."""
    pid = conversas.meta(cid).get("projeto") if cid else None
    if not pid:
        return {"cartao": None}
    try:
        est = projetos.estado_pipeline(pid)
    except Exception:
        return {"cartao": None}
    pnl = pipeline.painel(est)
    etapas = pnl["etapas"]
    for i, e in enumerate(etapas):
        if e["status"] != pipeline.AGUARDANDO or i + 1 >= len(etapas):
            continue
        prox = etapas[i + 1]
        if not prox["gasta"]:
            continue
        cartao = {"projeto": pid, "etapa": e["id"], "n": e["n"], "nome": e["nome"],
                  "libera": prox["id"], "libera_nome": prox["nome"],
                  "libera_resumo": prox["resumo"], "saldo_itens": e.get("saldo"),
                  "custo": None}
        if prox["id"] in ("imagens", "animacao"):
            try:
                o = gerar.orcamento(pid)
                unit = o["custo_imagem"] if prox["id"] == "imagens" else o["custo_video"]
                motor = o["motor_imagem"] if prox["id"] == "imagens" else o["motor_video"]
                qtd = o["inserts"]
                if prox["id"] == "animacao" and e.get("saldo"):
                    qtd = e["saldo"].get("aprovados") or qtd
                cartao["custo"] = {"itens": qtd, "unitario": unit, "motor": motor,
                                   "total": round(qtd * (unit or 0), 1),
                                   "saldo": o.get("saldo")}
            except Exception as ex:
                cartao["custo_erro"] = str(ex)[:160]
        return {"cartao": cartao}
    return {"cartao": None}


_PULAR = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache",
          "Adobe Premiere Pro Auto-Save", "Adobe Premiere Pro Video Previews",
          "Adobe Premiere Pro Audio Previews"}
_adobe_pasta = {"q": (0, None)}


def _sem_acento(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn").lower()


def _raizes_da_conversa(cid):
    """Onde o "@" procura: a pasta do projeto do app, a pasta do vídeo bruto
    e, sem projeto, a pasta do projeto aberto no Premiere."""
    raizes = []
    pid = conversas.meta(cid).get("projeto") if cid else None
    if pid:
        raizes.append(projetos.dir_projeto(pid))
        try:
            corpo = projetos.ler(pid)["plano"]["fonte"].get("body")
            if corpo:
                raizes.append(os.path.dirname(corpo))
        except Exception:
            pass
    else:
        import time as _t
        quando, pasta = _adobe_pasta["q"]
        if _t.time() - quando > 60:
            try:
                cam = adobe.estado().get("caminho")
                pasta = os.path.dirname(cam) if cam else None
            except Exception:
                pasta = None
            _adobe_pasta["q"] = (_t.time(), pasta)
        if pasta:
            raizes.append(pasta)
    if cid:
        raizes.append(os.path.join(conversas.dir_conversa(cid), "anexos"))
    vistas, saida = set(), []
    for r in raizes:
        r = os.path.realpath(os.path.expanduser(r))
        if r not in vistas and os.path.isdir(r):
            vistas.add(r)
            saida.append(r)
    return saida


def rota_arquivos(cid, q, limite=30, teto=6000):
    """Busca de arquivos para o "@" do campo de mensagem."""
    q = _sem_acento(q or "").strip()
    achados, vistos = [], 0
    raizes = _raizes_da_conversa(cid)
    for raiz in raizes:
        for pasta, dirs, arqs in os.walk(raiz):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _PULAR]
            for a in arqs:
                if a.startswith("."):
                    continue
                vistos += 1
                cam = os.path.join(pasta, a)
                rel = os.path.relpath(cam, raiz)
                alvo = _sem_acento(rel)
                if not q or q in alvo:
                    nome = _sem_acento(a)
                    nota = (0 if nome.startswith(q) else 1 if q in nome else 2, len(rel))
                    achados.append((nota, {"caminho": cam, "rel": rel,
                                           "raiz": os.path.basename(raiz)}))
                if vistos >= teto:
                    break
            if vistos >= teto:
                break
    achados.sort(key=lambda x: x[0])
    return {"raizes": raizes, "arquivos": [a for _, a in achados[:limite]]}


def rota_anexo(handler, cid):
    """Arquivo arrastado para a conversa: grava em <conversa>/anexos/ e devolve
    o caminho. O navegador (WebKit do pywebview, Chromium do painel) não expõe
    o caminho do arquivo arrastado — então o arquivo vem, e o caminho volta."""
    from urllib.parse import unquote
    if not cid or "/" in cid or ".." in cid:
        raise ValueError("Conversa inválida.")
    n = int(handler.headers.get("Content-Length") or 0)
    if n <= 0:
        raise ValueError("Arquivo vazio.")
    if n > 4 * 1024 ** 3:
        raise ValueError("Arquivo grande demais para anexar (máximo 4 GB).")
    nome = os.path.basename(unquote(handler.headers.get("X-Nome") or "")) or "anexo"
    nome = "".join(c for c in nome if c not in '\\:*?"<>|').strip() or "anexo"
    pasta = os.path.join(conversas.dir_conversa(cid), "anexos")
    os.makedirs(pasta, exist_ok=True)
    base, ext = os.path.splitext(nome)
    alvo, k = os.path.join(pasta, nome), 2
    while os.path.exists(alvo):
        alvo = os.path.join(pasta, "%s (%d)%s" % (base, k, ext))
        k += 1
    falta = n
    with open(alvo, "wb") as f:
        while falta > 0:
            bloco = handler.rfile.read(min(falta, 1024 * 1024))
            if not bloco:
                break
            f.write(bloco)
            falta -= len(bloco)
    if falta:
        os.remove(alvo)
        raise ValueError("O envio do arquivo foi interrompido.")
    return {"caminho": alvo, "nome": os.path.basename(alvo), "tamanho": n}


def rota_limpar(cid):
    """/limpar: apaga as mensagens desta conversa e começa sessão nova da IA
    (sem a memória do que foi dito). O projeto continua amarrado."""
    conversas.gravar_mensagens(cid, [])
    for arq in ("sessao.txt", "codex.txt"):
        try:
            os.remove(conversas.caminho(cid, arq))
        except Exception:
            pass
    conversas.gravar_meta(cid, titulo="Nova conversa")
    return {"ok": True, "conversa": cid}


def abrir_aulas():
    """"Minhas aulas": pede o passe de 60 s e abre no navegador padrão.

    Quem abre é o lado Python — `window.open` dentro da janela do pywebview
    abriria a área do aluno DENTRO do app, sem os cookies do navegador da
    pessoa. O link vale uma vez e por 60 s: não volta para a tela nem fica
    guardado."""
    r = conta.passe()
    if not r.get("ok"):
        return r
    aberto = False
    try:
        aberto = bool(webbrowser.open(r["url"]))
    except Exception:
        aberto = False
    if not aberto:
        from nucleo import so as _so
        aberto = _so.abrir(r["url"])
    if not aberto:
        return {"ok": False, "motivo": "navegador",
                "msg": "Não consegui abrir o navegador deste computador."}
    return {"ok": True, "msg": "Abrindo a área do aluno no navegador…"}


def _forcar(h):
    """`?forcar=1` = o usuário clicou em "Atualizar status". Aí vale pagar a
    releitura cara do PATH, que pergunta ao shell de login."""
    return "forcar=1" in h.path


ROTAS_GET = {
    "/api/estado": lambda h: rota_estado(None, _forcar(h)),
    "/api/servicos": lambda h: rota_servicos(_forcar(h)),
    "/api/projetos": lambda h: rota_projetos(None),
    "/api/estilos": lambda h: {"estilos": skill.estilos()},
}


# ------------------------------------------------------------------ painel do Tools PRO
#
# O painel do Tools PRO (CEP, dentro do Premiere e do After) mostra a Conversa
# do app. A página dele é um arquivo local, então o navegador do CEP manda
# `Origin: null` (ou `file://`). Liberar CORS para isso SÓ nas rotas da
# conversa e SÓ com o token certo: qualquer arquivo .html aberto do disco
# também tem origem "null", e sem o token ele não pode nem saber que o app
# existe. Nada de `*`, e o servidor continua só em 127.0.0.1.
ORIGENS_PAINEL = ("null", "file://")

# Modo serviço: o app sobe SEM janela, só o servidor, porque o painel do Tools
# PRO pediu o cérebro e o editor não pode sair do Premiere para conversar.
# Morre sozinho quando ninguém fala com ele por OCIOSO_SERVICO segundos (o
# painel manda sinal de vida a cada 20 s; fechar o painel ou o Premiere para
# o sinal) — mas nunca no meio de uma tarefa rodando.
MODO_SERVICO = "--servico" in sys.argv
OCIOSO_SERVICO = int(os.environ.get("EDITOR_AUTOMATICO_OCIOSO") or 120)   # a banca encurta
_ULTIMO_CONTATO = [0.0]


def _rota_da_conversa(caminho):
    if caminho in ("/api/saude", "/api/servico/desligar", "/api/conversa", "/api/conversas",
                   "/api/conversas/nova", "/api/ia", "/api/ia/escolher",
                   "/api/skills"):        # o menu "/" de skills do campo de mensagem
        return True
    partes = caminho.strip("/").split("/")
    if partes[:2] == ["api", "conversas"]:
        # /api/conversas/{id} e o que a tela da conversa faz dentro dela
        if len(partes) == 3:
            return True
        return len(partes) == 4 and partes[3] in ("aprovacao", "arquivos", "anexo", "limpar",
                                                   "destino", "renomear")
    # prévia das entregas (info, picos, quadro, baixar, mostrar). O
    # /api/arquivo fica FORA de propósito: <img>/<video>/<audio> não precisam
    # de CORS, e sem ele nenhuma página de origem "null" lê o conteúdo por fetch.
    if len(partes) == 3 and partes[:2] == ["api", "midia"]:
        return True
    # acompanhar e cancelar a rodada em andamento
    if len(partes) in (3, 4) and partes[:2] == ["api", "tarefas"]:
        return len(partes) == 3 or partes[3] == "cancelar"
    # o cartão de aprovação DENTRO da conversa usa a mesma rota do botão do
    # pipeline. Só aprovar/rejeitar — iniciar etapa fica na janela do app.
    if len(partes) == 6 and partes[:2] == ["api", "projetos"] and partes[3] == "etapa":
        return partes[5] in ("aprovar", "rejeitar")
    return False


def _versao_do_app():
    try:
        with open(os.path.join(RAIZ, "version.json"), encoding="utf-8") as f:
            return json.load(f).get("version", "")
    except Exception:
        return ""


def _mesmo_token(t):
    # compare_digest com str não-ASCII levanta TypeError: compara em bytes
    return secrets.compare_digest(str(t).encode("utf-8"), TOKEN.encode("utf-8"))


def _ler_range(cabecalho, tam):
    """`Range: bytes=a-b` → (a, b). False = cabeçalho de outra unidade (ignora
    e serve inteiro). None = faixa inválida ou fora do arquivo (416).
    Uma faixa só: é o que players pedem; várias faixas viram 416."""
    unidade, _, faixas = cabecalho.partition("=")
    if unidade.strip().lower() != "bytes":
        return False
    faixas = faixas.strip()
    if not faixas or "," in faixas or "-" not in faixas:
        return None
    a, _, b = faixas.partition("-")
    a, b = a.strip(), b.strip()
    try:
        if a == "":                     # bytes=-500: os últimos 500
            if not b.isdigit() or int(b) == 0 or tam == 0:
                return None
            n = int(b)
            return (max(0, tam - n), tam - 1)
        if not a.isdigit() or (b and not b.isdigit()):
            return None
        ini = int(a)
        fim = int(b) if b else tam - 1
    except ValueError:
        return None
    if ini >= tam or fim < ini:
        return None
    return (ini, min(fim, tam - 1))


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
        self._cors()
        self.end_headers()
        self.wfile.write(corpo)

    def _origem_do_painel(self):
        o = self.headers.get("Origin")
        return o if o in ORIGENS_PAINEL else None

    def _cors(self):
        """Cabeçalhos CORS na resposta de verdade: origem do painel + rota da
        conversa + token válido. Faltou qualquer um, a resposta sai sem eles e
        o navegador do painel não entrega nada à página."""
        o = self._origem_do_painel()
        if o and _rota_da_conversa(self.path.split("?")[0]) and self._autorizado():
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Vary", "Origin")

    def _token_na_query(self):
        """`<img>`, `<video>` e `<audio>` não mandam cabeçalho: nas rotas de
        arquivo e de mídia o token também vale na query (`t=`). Só nelas."""
        caminho = self.path.split("?")[0]
        if self.command not in ("GET", "HEAD"):
            return False
        if caminho != "/api/arquivo" and not caminho.startswith("/api/midia/"):
            return False
        from urllib.parse import parse_qs, urlparse
        return _mesmo_token((parse_qs(urlparse(self.path).query).get("t") or [""])[0])

    def _autorizado(self):
        ok = _mesmo_token(self.headers.get("X-Token") or "") or self._token_na_query()
        if ok:
            import time as _t
            _ULTIMO_CONTATO[0] = _t.time()     # sinal de vida (modo serviço)
        return ok

    def _desligar_servico(self):
        """"Desligar a IA" do painel. Só vale no modo serviço: o app que a
        pessoa abriu com janela não é do painel para fechar."""
        if not MODO_SERVICO:
            return self._json({"ok": False, "erro": "O Editor Automático está aberto com janela — feche pela janela."}, 409)
        self._json({"ok": True})
        threading.Thread(target=_encerrar_servico, args=(0.3,), daemon=True).start()

    def do_OPTIONS(self):
        """Pré-voo do CORS. Ele nunca traz o token (o navegador não manda
        cabeçalho próprio no pré-voo), então aqui só se libera o FORMATO do
        pedido; quem decide é o pedido de verdade, que exige o token."""
        caminho = self.path.split("?")[0]
        o = self._origem_do_painel()
        if not (o and _rota_da_conversa(caminho)):
            self.send_response(403)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", o)
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Token, X-Nome")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        # Chromium mais novo pede licença extra para página local falar com
        # 127.0.0.1 (Private Network Access); sem isto o pré-voo é recusado
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Length", "0")
        self.end_headers()

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

    def _arquivo_do_projeto(self, so_cabecalho=False):
        """Serve um arquivo para a tela: mosaico do QC, anexo, prévia de entrega.

        Travas, todas necessárias:
        - token (na query, porque `<img>`/`<video>` não mandam cabeçalho);
        - o caminho resolvido com realpath tem que estar DENTRO das pastas do
          app (projetos, conversas) ou — só mídia — da pasta do job ligada a um
          projeto ou da pasta de projeto escolhida. Sem isto a rota viraria
          leitura de disco inteira para qualquer página aberta na máquina.

        Aceita Range (206 Partial Content): vídeo e áudio tocam e pulam sem
        baixar o arquivo inteiro, e o WebKit do app EXIGE isso para tocar mp4."""
        if not self._autorizado():
            return self._vazio(403)
        alvo = _caminho_da_query(self)
        if not midia.permitido(alvo):
            return self._vazio(404)
        alvo = os.path.realpath(os.path.expanduser(alvo))
        tipo = midia.mime_de(alvo) or mimetypes.guess_type(alvo)[0] or "application/octet-stream"
        tam = os.path.getsize(alvo)
        ini, fim, parcial = 0, tam - 1, False
        faixa = (self.headers.get("Range") or "").strip()
        if faixa:
            r = _ler_range(faixa, tam)
            if r is None:
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % tam)
                self.send_header("Content-Length", "0")
                self._cors()
                self.end_headers()
                return
            if r is not False:
                ini, fim = r
                parcial = True
        n = max(0, fim - ini + 1)
        self.send_response(206 if parcial else 200)
        self.send_header("Content-Type", tipo)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(n))
        if parcial:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (ini, fim, tam))
        self.send_header("Cache-Control", "private, max-age=60")
        self._cors()
        self.end_headers()
        if so_cabecalho or not n:
            return
        try:
            with open(alvo, "rb") as f:
                f.seek(ini)
                falta = n
                while falta > 0:
                    bloco = f.read(min(falta, 256 * 1024))
                    if not bloco:
                        break
                    self.wfile.write(bloco)
                    falta -= len(bloco)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass        # o player pulou para outro ponto e largou este pedido

    def _vazio(self, codigo):
        self.send_response(codigo)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def _midia_get(self, caminho):
        """GET /api/midia/{info,picos,quadro,destinos}."""
        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(self.path).query)
        if caminho == "/api/midia/destinos":
            return self._json(rota_midia_destinos((q.get("conversa") or [""])[0]))
        alvo = (q.get("p") or [""])[0]
        if not midia.permitido(alvo):
            return self._json({"erro": "Arquivo fora das pastas do projeto."}, 404)
        if caminho == "/api/midia/info":
            return self._json(midia.info(alvo))
        if caminho == "/api/midia/picos":
            n = (q.get("n") or ["96"])[0]
            return self._json(midia.picos(alvo, int(n) if n.isdigit() else 96))
        if caminho == "/api/midia/quadro":
            w = (q.get("w") or ["480"])[0]
            arq = midia.quadro(alvo, int(w) if w.isdigit() else 480)
            if not arq:
                return self._arquivo_do_projeto()      # sem ffmpeg: o original
            with open(arq, "rb") as f:
                dados = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "private, max-age=600")
            self._cors()
            self.end_headers()
            self.wfile.write(dados)
            return None
        return self._json({"erro": "rota não existe"}, 404)

    def do_HEAD(self):
        if self.path.split("?")[0] == "/api/arquivo":
            return self._arquivo_do_projeto(so_cabecalho=True)
        self._vazio(405)

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
            if caminho.startswith("/api/midia/"):
                return self._midia_get(caminho)
            if caminho == "/api/saude":
                # barata de propósito: o painel do Tools PRO chama para provar
                # que a porta e o token do arquivo de descoberta são DESTE app
                # `conversa_ui` diz se a tela reutilizável da Conversa existe
                # nesta versão — o painel decide por isso entre montar o
                # componente ou cair no modo de reserva, sem pedir um arquivo
                # que daria 404 (e o 404 estático aqui não fecha a conexão)
                return self._json({
                    "ok": True, "app": "editor-automatico",
                    "versao": _versao_do_app(), "pid": os.getpid(),
                    "modo": "servico" if MODO_SERVICO else "janela",
                    "conversa_ui": os.path.isfile(os.path.join(WEB, "conversa-ui.js"))})
            if caminho in ROTAS_GET:
                return self._json(ROTAS_GET[caminho](self))
            partes = caminho.strip("/").split("/")
            if len(partes) == 3 and partes[1] == "projetos":
                return self._json(rota_projeto(partes[2]))
            if caminho == "/api/claude":
                return self._json(claude.estado_conta())
            if caminho == "/api/adobe":
                # o cache serve para não repetir a varredura DENTRO do mesmo
                # pedido; num clique explícito de Reconectar ele atrapalharia —
                # o usuário acabou de abrir o painel e receberia a foto velha
                forcar = "forcar=1" in self.path
                if forcar:
                    adobe.esquecer()
                # Verificado de verdade: painel + ler projeto + ler timeline +
                # o servidor MCP subir. Dizer "conectada" só porque existe um
                # painel na porta era o que fazia a tela mentir para o usuário.
                e = adobe.estado()
                v = adobe.verificar()
                e["verificado"] = v
                e["mcp"] = conversa.mcp_vivo(forcar=forcar)
                e["utilizavel"] = bool(v["leu_timeline"] and e["mcp"]["ok"])
                return self._json(e)
            if caminho == "/api/conversas":
                # o Histórico da Conversa: ?q= procura no título e no conteúdo
                from urllib.parse import parse_qs, urlparse
                q = (parse_qs(urlparse(self.path).query).get("q") or [""])[0]
                lista = conversas.buscar(q) if q.strip() else conversas.listar()
                nomes = {}
                for c in lista:
                    pid = c.get("projeto")
                    if pid and pid not in nomes:
                        try:
                            nomes[pid] = projetos.ler(pid)["plano"].get("job") or pid
                        except Exception:
                            nomes[pid] = None
                    c["projeto_nome"] = nomes.get(pid) if pid else None
                return self._json({"conversas": lista})
            if len(partes) == 3 and partes[1] == "conversas":
                return self._json(rota_conversa_ver(partes[2]))
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "aprovacao":
                return self._json(rota_aprovacao(partes[2]))
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "arquivos":
                from urllib.parse import parse_qs, urlparse
                q = (parse_qs(urlparse(self.path).query).get("q") or [""])[0]
                return self._json(rota_arquivos(partes[2], q))
            if caminho == "/api/conversa":
                lista = conversas.listar()
                cid = lista[0]["id"] if lista else None
                return self._json({"conversa": cid,
                                   "mensagens": midia.anotar(conversas.mensagens(cid)) if cid else []})
            if caminho == "/api/atualizacao":
                return self._json(atualizacao.conferir())
            if caminho == "/api/app/local":
                return self._json(instalar_mac.local())
            if caminho == "/api/ia":
                return self._json(ia.estado())
            if caminho == "/api/plugin":
                return self._json(plugin.estado())
            if caminho == "/api/ponte":
                return self._json(ponte.estado())
            if caminho == "/api/skills":
                return self._json(skills.estado())
            if caminho == "/api/ambiente/plano":
                return self._json(preparar.plano(
                    com_opcionais=self.path.find("opcionais=0") < 0))
            if caminho == "/api/ambiente":
                from nucleo import caminho as _cam
                if _forcar(self):
                    _cam.recarregar(com_shell=True)
                d = ambiente.conferir()
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
                from urllib.parse import parse_qs, urlparse
                v = (parse_qs(urlparse(self.path).query).get("v") or [None])[0]
                desde = int(v) if v not in (None, "") and v.lstrip("-").isdigit() else None
                return self._json(tarefa_ver(partes[2], desde) or {"erro": "sem tarefa"})
            if caminho == "/api/pasta":
                # chamado logo ao abrir: no Mac é aqui que o sistema pergunta
                # sobre a pasta Documentos — com a tela explicando o porquê —
                # e não no meio da primeira mensagem, com a conversa parada
                return self._json(conversas.garantir_acesso())
            return self._json({"erro": "rota não existe"}, 404)
        except Exception as e:
            traceback.print_exc()
            return self._json({"erro": str(e) or e.__class__.__name__}, 400)

    # -------------------------------------------------------------- POST
    def do_POST(self):
        caminho = self.path.split("?")[0]
        if not self._autorizado():
            return self._json({"erro": "Sessão inválida."}, 403)
        if caminho == "/api/servico/desligar":
            return self._desligar_servico()
        try:
            partes = caminho.strip("/").split("/")
            # arquivo arrastado para a conversa: o corpo é o arquivo, não JSON
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "anexo":
                return self._json(rota_anexo(self, partes[2]))
            corpo = self._corpo()

            if caminho == "/api/conta/entrar":
                return self._json(conta.entrar(corpo.get("email", ""), corpo.get("senha", "")))
            if caminho == "/api/conta/codigo":
                return self._json(conta.pedir_codigo(corpo.get("email", "")))
            if caminho == "/api/conta/codigo/entrar":
                return self._json(conta.entrar_com_codigo(corpo.get("email", ""),
                                                          corpo.get("codigo", "")))
            if caminho == "/api/conta/aulas":
                return self._json(abrir_aulas())
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
            if caminho == "/api/claude/entrar":
                return self._json(claude.entrar_sessao())
            if caminho == "/api/claude/testar":
                return self._json(claude.testar_conta())

            if caminho == "/api/midia/baixar":
                codigo, d = rota_midia_baixar(corpo)
                return self._json(d, codigo)
            if caminho == "/api/midia/mostrar":
                try:
                    return self._json({"ok": midia.mostrar(corpo.get("p") or "")})
                except PermissionError as e:
                    return self._json({"erro": str(e)}, 403)
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "renomear":
                cid = partes[2]
                if "/" in cid or ".." in cid:
                    raise ValueError("Conversa inválida.")
                return self._json({"ok": True, "meta": conversas.renomear(cid, corpo.get("titulo"))})
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "destino":
                return self._json(rota_destino(partes[2], corpo))
            if caminho == "/api/conversas/nova":
                return self._json({"conversa": conversas.criar()})
            if caminho == "/api/conversas/apagar":
                return self._json({"ok": conversas.apagar(corpo["conversa"])})
            if len(partes) == 4 and partes[1] == "conversas" and partes[3] == "limpar":
                return self._json(rota_limpar(partes[2]))

            if caminho == "/api/ia/escolher":
                return self._json({"escolhido": ia.escolher(corpo["provedor"]),
                                   "estado": ia.estado()})
            if caminho == "/api/ia/chave":
                # a chave entra por aqui e vai para o .env do app, com permissão
                # de dono. Nunca volta para a tela: as rotas de leitura só dizem
                # se existe e de onde veio.
                ia.guardar_chave(corpo["provedor"], corpo.get("valor", ""))
                return self._json({"ok": True, "estado": ia.estado()})
            if caminho == "/api/ia/entrar":
                from nucleo import codex_sessao
                return self._json(codex_sessao.entrar())
            if caminho == "/api/ia/metodo":
                return self._json({"metodo": ia.definir_metodo_chatgpt(corpo["metodo"]),
                                   "estado": ia.estado()})
            if caminho == "/api/ia/testar":
                if corpo.get("provedor") == "chatgpt":
                    from nucleo import openai_chat
                    return self._json(openai_chat.testar())
                return self._json(claude.testar_conta())

            if caminho == "/api/conversa":
                cid = corpo.get("conversa")
                prov = corpo.get("provedor")
                ctl = cancelar.Controle()
                tid = em_fundo("Conversando", lambda log: conversa.falar(
                    cid, corpo.get("texto", ""), corpo.get("anexos"),
                    conta.estado().get("nome") or "usuário", log, provedor=prov,
                    controle=ctl), controle=ctl)
                return self._json({"tarefa": tid})
            if len(partes) == 4 and partes[1] == "tarefas" and partes[3] == "cancelar":
                return self._json(tarefa_cancelar(partes[2]))

            if caminho == "/api/atualizacao/codigo":
                tid = em_fundo("Atualizando",
                               lambda log: atualizacao.atualizar_codigo(log))
                return self._json({"tarefa": tid})
            if caminho == "/api/atualizacao/reabrir":
                return self._json(atualizacao.reabrir())
            if caminho == "/api/app/mover":
                tid = em_fundo("Movendo para Aplicativos",
                               lambda log: instalar_mac.mover_para_aplicativos(log))
                return self._json({"tarefa": tid})
            if caminho == "/api/atualizacao/baixar":
                tid = em_fundo("Baixando a atualização",
                               lambda log: atualizacao.baixar(ao_vivo=log))
                return self._json({"tarefa": tid})
            if caminho == "/api/skills/instalar":
                tid = em_fundo("Instalando as skills",
                               lambda log: skills.instalar(
                                   bool(corpo.get("substituir")), log))
                return self._json({"tarefa": tid})
            if caminho == "/api/ponte/preparar":
                return self._json(ponte.preparar())
            if caminho == "/api/plugin/instalar":
                tid = em_fundo("Instalando o plugin do Premiere",
                               lambda log: plugin.instalar(log))
                return self._json({"tarefa": tid})

            if caminho == "/api/ambiente/preparar":
                # UM botão: gerenciador → programas → skills → plugin → ponte,
                # reconferindo entre um e outro. Roda em fundo porque o Homebrew
                # e o plugin terminam num Terminal de fora, e o app fica olhando.
                tid = em_fundo("Preparando esta máquina",
                               lambda log: preparar.rodar(
                                   com_opcionais=corpo.get("opcionais", True),
                                   com_plugin=corpo.get("plugin", True),
                                   ao_vivo=log))
                return self._json({"tarefa": tid})
            if caminho == "/api/ambiente/gerenciador":
                return self._json(ambiente.instalar_gerenciador())
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
                    prov = corpo.get("provedor")
                    tid = em_fundo("Conversando", lambda log: conversa.falar(
                        pid, corpo.get("texto", ""), corpo.get("anexos"),
                        conta.estado().get("nome") or "usuário", log,
                        provedor=prov))
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


def _tarefa_rodando():
    with _trava:
        return any(t.get("estado") == "rodando" for t in TAREFAS.values())


def _encerrar_servico(espera=0.0):
    """Sai de vez: cancela o que dá para cancelar, apaga a descoberta e mata o
    processo. os._exit porque o servidor e as tarefas são threads daemon e um
    sys.exit numa thread não derruba nada."""
    import time as _t
    if espera:
        _t.sleep(espera)
    with _trava:
        tids = [tid for tid, t in TAREFAS.items() if t.get("estado") == "rodando"]
    for tid in tids:
        try:
            tarefa_cancelar(tid)
        except Exception:
            pass
    from nucleo import descoberta
    descoberta.apagar()
    os._exit(0)


def _vigiar_ociosidade():
    import time as _t
    while True:
        _t.sleep(min(10, max(1, OCIOSO_SERVICO / 2)))
        if _t.time() - _ULTIMO_CONTATO[0] > OCIOSO_SERVICO and not _tarefa_rodando():
            _encerrar_servico()


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    if MODO_SERVICO:
        # já existe o app COM janela aberto: ele é o cérebro, o serviço não sobe
        # (sobrescrever a descoberta deixaria a janela inalcançável pelo painel)
        from nucleo import descoberta as _d
        viva = _d.ler()
        if viva and viva.get("modo") != "servico":
            return
    porta = porta_livre()
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    # subiu: se este código veio de uma atualização leve, tira a quarentena.
    # É este ponto — imports resolvidos e servidor no ar — que prova que o
    # código baixado presta.
    from nucleo import codigo as _cod
    _cod.deu_certo()
    # disco do instalador montado e .dmg velho no Downloads viram ícone repetido
    # no Spotlight a cada atualização: some com eles em segundo plano
    def _limpar():
        try:
            atualizacao.limpar_instaladores()
        except Exception:
            traceback.print_exc()
    threading.Thread(target=_limpar, daemon=True).start()
    url = "http://127.0.0.1:%d/?t=%s" % (porta, TOKEN)

    # Arquivo de descoberta: é por ele que o painel do Tools PRO acha este app
    # (porta e token mudam a cada abertura). Some ao fechar; se o app morrer
    # sem passar por aqui, o painel vê o pid morto e ignora o arquivo.
    from nucleo import descoberta
    if not MODO_SERVICO:
        # abriu com janela e o painel tinha ligado um serviço: ele sai, fica a janela
        try:
            descoberta.desligar_servico_vivo()
        except Exception:
            traceback.print_exc()
    try:
        descoberta.gravar(porta, TOKEN, _versao_do_app(),
                          modo="servico" if MODO_SERVICO else "janela")
    except Exception:
        traceback.print_exc()          # sem o arquivo o app segue; só o painel não acha
    import atexit
    atexit.register(descoberta.apagar)
    if os.name != "nt":
        import signal

        def _sair(*_):
            descoberta.apagar()
            os._exit(0)
        for sinal in (signal.SIGTERM, signal.SIGHUP):
            try:
                signal.signal(sinal, _sair)
            except (ValueError, OSError):
                pass

    if MODO_SERVICO:
        # sem janela, sem pywebview (é ele que acorda o AppKit e põe o ícone
        # no Dock): só o servidor, até o painel desligar ou parar de falar
        import time as _t
        _ULTIMO_CONTATO[0] = _t.time()
        threading.Thread(target=_vigiar_ociosidade, daemon=True).start()
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        descoberta.apagar()
        return

    try:
        import webview
    except ImportError:
        # Sem pywebview ainda dá pra trabalhar — o app não trava por causa da moldura
        print("Janela nativa indisponível; abrindo no navegador.\n" + url)
        webbrowser.open(url)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        descoberta.apagar()
        return

    janela = webview.create_window(
        "Editor Automático", url,
        width=1240, height=820, min_size=(1020, 680),
        background_color="#0B0C0E")
    try:
        webview.start(gui="cocoa" if sys.platform == "darwin" else None)
    finally:
        # janela fechada = app fechado para o painel, já, sem esperar o atexit
        descoberta.apagar()


if __name__ == "__main__":
    main()
