"""
O chat — quem conduz o pipeline em linguagem natural.

Princípio que não se negocia: **o chat não fura o portão.**

O modelo interpreta o que a pessoa quis e chama a ação; quem decide se a ação
pode acontecer continua sendo o `pipeline.py`. Se o Claude tentar gerar b-roll
antes da aprovação do planejamento, recebe o mesmo "não" que o botão receberia,
com a mesma mensagem. A conversa é uma porta nova para as mesmas travas — não
um atalho por fora delas.

E o contrário também vale: aprovar POR ESCRITO é aprovação de verdade. "pode
gerar" no chat vira registro em `aprovacoes` com o nome de quem falou, a hora e
a frase exata que autorizou. Sem isso o registro mentiria sobre como a decisão
foi tomada.

Segredo nunca entra aqui. As chaves vivem no cofre do sistema (`chaves.py`) e
não são passadas ao modelo em hipótese alguma — o histórico do chat fica em
disco, no projeto, e projeto vai para o Drive.
"""

import json
import os
import re
import subprocess
import sys
import time

from . import (adobe, chaves, claude as conta_claude, conversas, gerar,  # noqa: F401
               pipeline, projetos, so)

MODELO = "claude-opus-5"

SISTEMA = """Você conduz o Editor Automático, um app de edição de criativos de vídeo.

Fala português do Brasil, direto, sem enrolação. Você é o operador do app: o
usuário conversa com você e você opera as ferramentas.

ANTES de qualquer tarefa nova, chame `ver_adobe`. Você precisa saber se o Premiere
ou o After Effects está aberto, qual projeto está carregado, qual sequência está
ativa e se a ponte do Tools PRO responde. Mostre isso ao usuário e peça confirmação
antes de mexer em qualquer coisa.

Se nenhum programa da Adobe estiver aberto, diga isso e peça para ele abrir o
Premiere (ou o After Effects) com o projeto. Se houver várias sequências e nenhuma
ativa, liste as opções na conversa e pergunte qual usar. Nunca escolha por ele.

Tudo acontece nesta conversa. Não existe outra tela nem formulário: se faltar
informação — o caminho de um vídeo, a copy, o nome do job — pergunte aqui mesmo.

O trabalho é um pipeline de 12 etapas com aprovação obrigatória entre cada uma.
Você NUNCA pula etapa e NUNCA gera nada que gaste crédito sem o usuário ter
aprovado a etapa anterior. As ferramentas recusam sozinhas se você tentar — mas
não tente: explique ao usuário o que falta.

Antes de qualquer geração que gaste crédito, diga quanto vai custar e em qual
motor, e espere o "pode" do usuário. Se ele pedir para economizar, mostre os
motores mais baratos com o preço de cada um.

Quando uma etapa termina, resuma o que saiu em duas ou três linhas e diga o que
o usuário pode fazer: aprovar, pedir de novo, ou mudar alguma coisa.

Não invente resultado. Se uma ferramenta falhou, diga o que falhou e o que fazer.
Nunca peça chave de API nem senha pelo chat — isso se resolve na aba Contas."""

FERRAMENTAS = [
    {"name": "ver_adobe",
     "description": "Estado do Adobe AGORA: Premiere/After Effects aberto, qual projeto, "
                    "quais sequências, qual está ativa, e se a ponte do Tools PRO responde. "
                    "Chame isto antes de começar qualquer tarefa.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},

    {"name": "criar_projeto",
     "description": "Cria um projeto de trabalho a partir do caminho do vídeo do body "
                    "(o bruto do avatar falante). Use quando o usuário indicar o arquivo. "
                    "Se ele não disse o caminho, pergunte antes.",
     "input_schema": {"type": "object", "properties": {
         "video": {"type": "string", "description": "caminho do arquivo de vídeo"},
         "nome": {"type": "string", "description": "nome do job, opcional"},
     }, "required": ["video"]}},

    {"name": "ver_estado",
     "description": "Estado atual do projeto: as 12 etapas, status de cada uma, "
                    "o que está liberado e o que está travado e por quê. "
                    "Use antes de agir quando não tiver certeza de onde o projeto está.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},

    {"name": "rodar_etapa",
     "description": "Executa uma etapa. Recusa se a anterior não estiver aprovada. "
                    "Etapas que gastam crédito (avatar, imagens, animacao, acabamento) "
                    "só devem ser chamadas depois do usuário autorizar explicitamente.",
     "input_schema": {"type": "object", "properties": {
         "etapa": {"type": "string", "description":
                   "analise|copy|marcacao|plano|avatar|imagens|img_ok|animacao|vid_ok|acabamento"},
         "motor": {"type": "string", "description": "id do motor, quando a etapa gera mídia"},
         "texto": {"type": "string", "description": "a copy, na etapa 'copy'"},
         "descricao": {"type": "string", "description": "o personagem, na etapa 'avatar'"},
     }, "required": ["etapa"]}},

    {"name": "aprovar_etapa",
     "description": "Registra a aprovação do usuário e libera a etapa seguinte. "
                    "Só chame quando o usuário disser claramente que aprova. "
                    "Em 'frase' copie o que ele escreveu, palavra por palavra.",
     "input_schema": {"type": "object", "properties": {
         "etapa": {"type": "string"},
         "frase": {"type": "string", "description": "o que o usuário escreveu ao aprovar"},
     }, "required": ["etapa", "frase"]}},

    {"name": "rejeitar_etapa",
     "description": "Marca a etapa como rejeitada com o motivo dado pelo usuário.",
     "input_schema": {"type": "object", "properties": {
         "etapa": {"type": "string"}, "motivo": {"type": "string"},
     }, "required": ["etapa", "motivo"]}},

    {"name": "julgar_item",
     "description": "Aprova, rejeita ou manda regerar UMA imagem ou vídeo, nas etapas "
                    "de aprovação por item (img_ok e vid_ok). Só os aprovados seguem.",
     "input_schema": {"type": "object", "properties": {
         "etapa": {"type": "string"}, "item": {"type": "string"},
         "acao": {"type": "string", "description": "aprovou|rejeitou|regerar"},
         "motivo": {"type": "string"},
     }, "required": ["etapa", "item", "acao"]}},

    {"name": "ver_motores",
     "description": "Catálogo de motores do Higgsfield com o preço real de cada um e "
                    "quantos créditos o usuário tem. Use quando ele perguntar de custo "
                    "ou pedir para economizar.",
     "input_schema": {"type": "object", "properties": {
         "tipo": {"type": "string", "description": "imagem|video"},
     }, "required": ["tipo"]}},
]


# ---------------------------------------------------------------- execução

def _executar(pid, nome, entrada, quem):
    """Roda a ferramenta que o modelo pediu. TODA passa pelo pipeline —
    o modelo não tem caminho por fora."""

    if nome == "ver_adobe":
        return adobe.estado()

    if nome == "criar_projeto":
        caminho = os.path.expanduser((entrada.get("video") or "").strip())
        if not caminho:
            return {"erro": "Sem caminho de vídeo. Pergunte ao usuário qual arquivo usar."}
        if not os.path.isfile(caminho):
            return {"erro": "Esse arquivo não existe: " + caminho}
        p = projetos.criar(entrada.get("nome") or os.path.splitext(
            os.path.basename(caminho))[0], caminho)
        return {"criado": p["id"], "job": p["plano"]["job"],
                "fonte": p["plano"]["fonte"],
                "aviso": "Projeto criado. A conversa continua nele."}

    if pid is None:
        return {"erro": "Ainda não há projeto. Pergunte ao usuário qual vídeo usar "
                        "e chame criar_projeto antes."}

    est = projetos.estado_pipeline(pid)

    if nome == "ver_estado":
        pnl = pipeline.painel(est)
        return {"etapas": [{"n": e["n"], "id": e["id"], "nome": e["nome"],
                            "status": e["rotulo"], "gasta_credito": e["gasta"],
                            "liberada": e["pode"], "travada_porque": e["bloqueio"]}
                           for e in pnl["etapas"]],
                "etapa_atual": pnl["atual"],
                "concluidas": "%d de %d" % (pnl["concluidas"], pnl["total"])}

    if nome == "ver_motores":
        q = len([b for b in projetos.ler(pid)["plano"].get("beats", [])
                 if b.get("tipo") == "insert"]) or 1
        ops = (gerar.opcoes_imagem(q) if entrada.get("tipo") == "imagem"
               else gerar.opcoes_video({"inicio": 0, "fim": 5}, False, q))
        return {"opcoes": ops, "saldo_creditos": gerar.saldo(), "itens": q}

    if nome == "rodar_etapa":
        from app import rota_etapa_iniciar          # importa tarde: evita ciclo
        eid = entrada["etapa"]
        corpo = {k: v for k, v in entrada.items() if k != "etapa" and v is not None}
        try:
            r = rota_etapa_iniciar(pid, eid, corpo)
        except pipeline.Bloqueado as e:
            # a recusa volta pro modelo com a razão — ele explica ao usuário
            return {"recusado": True, "porque": str(e)}
        if r.get("longa"):
            return {"rodando": True, "tarefa": r["tarefa"],
                    "aviso": "Está gerando. Avise o usuário e não chame de novo."}
        d = pipeline.situacao(projetos.estado_pipeline(pid), eid)["dados"]
        return {"pronto": True, "aguardando_aprovacao": True,
                "resultado": _resumir(eid, d)}

    if nome == "aprovar_etapa":
        try:
            pipeline.aprovar(est, entrada["etapa"], quem,
                             "pelo chat: " + entrada.get("frase", ""))
        except pipeline.Bloqueado as e:
            return {"recusado": True, "porque": str(e)}
        projetos.gravar_pipeline(pid, est)
        return {"aprovada": entrada["etapa"], "proxima": pipeline.proxima(est)}

    if nome == "rejeitar_etapa":
        pipeline.rejeitar(est, entrada["etapa"], quem, entrada.get("motivo", ""))
        projetos.gravar_pipeline(pid, est)
        return {"rejeitada": entrada["etapa"]}

    if nome == "julgar_item":
        try:
            pipeline.julgar_item(est, entrada["etapa"], entrada["item"],
                                 entrada["acao"], quem, entrada.get("motivo", ""))
        except pipeline.Bloqueado as e:
            return {"recusado": True, "porque": str(e)}
        projetos.gravar_pipeline(pid, est)
        return {"saldo": pipeline.saldo_itens(est, entrada["etapa"])}

    return {"erro": "ferramenta desconhecida: " + nome}


def _resumir(eid, d):
    """O que volta pro modelo. Enxuto de propósito: mandar o dado inteiro
    enche o contexto de ruído e o modelo passa a resumir JSON em vez de falar
    com a pessoa."""
    if eid == "analise":
        return {k: d.get(k) for k in ("formato", "geometria", "duracao", "alertas")}
    if eid == "copy":
        return {"cobertura": d.get("cobertura"), "graves": d.get("graves"),
                "repeticoes": len(d.get("repeticoes") or []),
                "veredito": d.get("veredito"),
                "primeiras": (d.get("divergencias") or [])[:6]}
    if eid == "marcacao":
        return {"por_cor": d.get("por_cor"), "cobertura": d.get("cobertura"),
                "sem_fala": d.get("sem_fala")}
    if eid == "plano":
        return {"liberado_pela_regra": d.get("liberado_pela_regra"),
                "a_gerar": d.get("a_gerar"), "custo": d.get("custo_previsto"),
                "portao": (d.get("portao") or "")[-900:]}
    if "itens" in d:
        return {"gerados": len(d["itens"]), "motor": d.get("motor"),
                "custo_gasto": d.get("custo_gasto"),
                "ids": [i.get("id") for i in d["itens"]]}
    return d


# ---------------------------------------------------------------- histórico

def historico(cid=None):
    """As mensagens de UMA conversa. Sem id, a mais recente — é o que o app
    reabre quando você volta."""
    if not cid:
        lista = conversas.listar()
        cid = lista[0]["id"] if lista else None
    return conversas.mensagens(cid) if cid else []


def _gravar(cid, msgs):
    conversas.gravar_mensagens(cid, msgs)


# ---------------------------------------------------------------- cliente

class SemAcesso(RuntimeError):
    pass


def _cliente():
    """Só é chamado no método 'chave'. Nunca cai aqui por conta própria."""
    import anthropic
    k = chaves.ler("claude")
    if not k:
        raise SemAcesso("Sem chave de API guardada. Vá em Contas.")
    return anthropic.Anthropic(api_key=k)


# ---------------------------------------------------------------- sessão
#
# O caminho da assinatura NÃO é uma API paralela: é o próprio Claude Code.
#
# Antes eu amarrava o modelo a um contrato JSON com seis ações. Isso desligava
# tudo que ele sabe fazer — as skills que o usuário já tem instaladas, o Bash, o
# Read, o raciocínio. Agora ele roda como sessão de verdade e recebe as
# ferramentas DESTE app por MCP, ao lado das dele. Quem escolhe o que usar é ele.
#
# `--session-id` fixo por projeto guarda o contexto entre mensagens: fechar o app
# e voltar continua a mesma conversa, com memória do que já foi feito.

RAIZ_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sessao_id(cid):
    """Um id de sessão estável por CONVERSA — é o que dá memória a ela."""
    import uuid
    arq = conversas.caminho(cid, "sessao.txt")
    try:
        with open(arq, encoding="utf-8") as f:
            v = f.read().strip()
        if v:
            return v, True          # já existe: retomar
    except Exception:
        pass
    novo_id = str(uuid.uuid4())
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    with open(arq, "w", encoding="utf-8") as f:
        f.write(novo_id)
    return novo_id, False


def comando_mcp():
    """Como subir o servidor MCP deste app.

    Empacotado, `sys.executable` É o binário do app — ele se relança com --mcp.
    Em desenvolvimento é o Python do venv com o script. Errar isso significa
    Claude sem ferramenta nenhuma, com a tela dizendo que está tudo certo."""
    if getattr(sys, "frozen", False):
        return sys.executable, ["--mcp"]
    return sys.executable, [os.path.join(RAIZ_APP, "app.py"), "--mcp"]


def _mcp_config():
    cmd, args = comando_mcp()
    return json.dumps({"mcpServers": {"editor": {"command": cmd, "args": args}}})


_mcp_cache = {}


def mcp_vivo(forcar=False):
    """O servidor MCP sobe e responde? Sem isto o Claude fica SEM as ferramentas
    do app — que foi exatamente o que aconteceu no app empacotado, com a tela
    dizendo que estava tudo conectado."""
    # ⚠️ Isto SOBE UM PROCESSO. A tela do Adobe chamava a cada pesquisa, e o
    # laço do "Reconectar" pesquisa seis vezes seguidas — seis servidores MCP
    # subindo e morrendo por clique. O resultado não muda de minuto a minuto.
    import time as _t
    if not forcar and _mcp_cache.get("q") and _t.time() - _mcp_cache["q"][0] < 120:
        return _mcp_cache["q"][1]

    cmd, args = comando_mcp()
    try:
        p = so.run(
            [cmd] + args, input='{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n',
            capture_output=True, text=True, timeout=30,
            env=conta_claude.ambiente_isolado())
        for linha in (p.stdout or "").splitlines():
            try:
                d = json.loads(linha)
            except Exception:
                continue
            t = (d.get("result") or {}).get("tools")
            if t:
                r = {"ok": True, "ferramentas": len(t),
                     "nomes": [x["name"] for x in t]}
                _mcp_cache["q"] = (_t.time(), r)
                return r
        r = {"ok": False, "msg": "O servidor de ferramentas não respondeu."}
    except Exception as e:
        r = {"ok": False, "msg": str(e)[:140]}
    _mcp_cache["q"] = (_t.time(), r)
    return r


def _contexto_ambiente(pid):
    """O que o Claude recebe de graça a cada mensagem. Sem isto ele começaria
    cego e gastaria turno perguntando o que já dá para saber."""
    linhas = ["Você é o agente do Editor Automático, um app de edição de criativos "
              "de vídeo. Fale português do Brasil, direto.",
              "",
              "As ferramentas do MCP `editor` operam o app: estado do Adobe, "
              "ExtendScript no Premiere, o pipeline de 12 etapas e a geração de mídia. "
              "Use também suas próprias skills e ferramentas quando fizerem sentido — "
              "cortar silêncio, marcar VSL, conferir b-roll, o que o usuário pedir.",
              "",
              "REGRAS QUE NÃO SE NEGOCIAM:",
              "- Nada que gaste crédito sem o usuário autorizar explicitamente antes. "
              "As ferramentas recusam sozinhas, mas não tente: explique o que falta.",
              "- Antes de mexer no Adobe, confira `adobe_estado` e mostre ao usuário.",
              "- Se faltar informação, pergunte aqui na conversa.",
              "- Nunca peça chave de API nem senha — isso se resolve na aba Contas.",
              ""]

    try:
        a = adobe.estado()
        linhas.append("AMBIENTE AGORA:")
        linhas.append("- Premiere: %s | After Effects: %s"
                      % ("aberto" if a["apps"]["premiere"] else "fechado",
                         "aberto" if a["apps"]["aftereffects"] else "fechado"))
        linhas.append("- Ponte Tools PRO: %s" % (a.get("painel") or "sem painel aberto"))
        if a.get("projeto"):
            linhas.append("- Projeto Adobe: %s" % a["projeto"])
            linhas.append("- Sequência ativa: %s" % (a.get("ativa") or "nenhuma"))
            if a.get("sequencias"):
                linhas.append("- Sequências: %s"
                              % ", ".join(x["nome"] for x in a["sequencias"][:10]))
        if a.get("aviso"):
            linhas.append("- Atenção: %s" % a["aviso"])
        try:
            t = adobe.timeline()
            r = t["resumo"]
            linhas.append("- TIMELINE ATIVA já lida: %s, %ss, %d clipes em %dV/%dA, "
                          "%d marcadores. Use `timeline_ler` para o detalhe — NÃO peça "
                          "caminho de .prproj nem vídeo exportado."
                          % (t["sequencia"], t["duracao"], r["clipes"],
                             r["trilhas_video"], r["trilhas_audio"], r["marcadores"]))
        except Exception:
            pass
    except Exception:
        linhas.append("AMBIENTE: não consegui ler o Adobe agora.")

    if pid:
        try:
            p = projetos.ler(pid)
            est = projetos.estado_pipeline(pid)
            pnl = pipeline.painel(est)
            linhas += ["",
                       "PROJETO DE TRABALHO: %s (id `%s`)" % (p["plano"].get("job"), pid),
                       "- Body: %s" % p["plano"]["fonte"]["body"],
                       "- Pasta: %s" % projetos.dir_projeto(pid),
                       "- Pipeline: %d de %d etapas concluídas; agora em `%s`"
                       % (pnl["concluidas"], pnl["total"], pnl["atual"])]
            travadas = [e for e in pnl["etapas"] if not e["pode"] and e["bloqueio"]]
            if travadas:
                linhas.append("- Travado: %s — %s"
                              % (travadas[0]["nome"], travadas[0]["bloqueio"]))
            if pnl["aprovacoes"]:
                linhas.append("- Últimas aprovações: %s"
                              % "; ".join("%s %s" % (x["acao"], x["etapa"])
                                          for x in pnl["aprovacoes"][:4]))
            linhas.append("- Passe `projeto: \"%s\"` nas ferramentas do pipeline." % pid)
        except Exception:
            pass
    else:
        linhas += ["", "Ainda não há projeto de trabalho. Se o usuário quiser editar "
                       "um criativo, pergunte o caminho do vídeo e use `projeto_criar`."]
    return "\n".join(linhas)


def _casa(cid):
    """O diretório de trabalho da sessão.

    ⚠️ A sessão do Claude Code é PRESA AO DIRETÓRIO. Um `.app` aberto pelo Finder
    roda a partir de `/`, então uma sessão criada em outro lugar some no
    `--resume` ("No conversation found with session ID"). Fixar a casa aqui é o
    que dá continuidade real à conversa."""
    d = conversas.dir_conversa(cid)
    os.makedirs(d, exist_ok=True)
    return d


def _resumo_entrada(nome, entrada):
    """O que a tela mostra ao lado do nome da ferramenta. Enxuto: JSON inteiro
    na conversa vira ruído e esconde o que importa."""
    if not isinstance(entrada, dict) or not entrada:
        return ""
    for chave in ("query", "etapa", "codigo", "prompt", "texto", "video",
                  "descricao", "file_path", "command", "pattern", "path"):
        if entrada.get(chave):
            v = str(entrada[chave]).replace("\n", " ")
            return v[:88] + ("…" if len(v) > 88 else "")
    return json.dumps(entrada, ensure_ascii=False)[:88]


def _resumo_saida(bruto):
    """Uma linha do que a ferramenta devolveu."""
    t = bruto if isinstance(bruto, str) else json.dumps(bruto, ensure_ascii=False,
                                                        default=str)
    t = " ".join(t.split())
    return t[:110] + ("…" if len(t) > 110 else "")


def _sessao_claude(cid, pid, texto, ao_vivo, _tentou_de_novo=False):
    """Uma mensagem para a sessão do Claude Code.

    Cada passo sai por `ao_vivo` NA HORA em que acontece — pensamento, chamada de
    ferramenta, resultado, texto. Antes eu juntava tudo e só entregava no fim: o
    usuário ficava olhando "pensando…" por minutos sem saber se travou."""
    sid, retomar = _sessao_id(cid)
    cmd = ["claude", "-p", texto,
           "--output-format", "stream-json", "--verbose",
           "--mcp-config", _mcp_config(),
           "--append-system-prompt", _contexto_ambiente(pid),
           "--permission-mode", "bypassPermissions",
           "--add-dir", RAIZ_APP]
    if pid:
        cmd += ["--add-dir", projetos.dir_projeto(pid)]
    cmd += (["--resume", sid] if retomar else ["--session-id", sid])

    proc = so.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1, cwd=_casa(cid),
                            env=conta_claude.ambiente_isolado())

    passos, erro = [], None
    pendentes = {}                       # tool_use_id -> índice do passo

    def emitir(ev):
        passos.append(ev)
        ao_vivo and ao_vivo(ev)
        return len(passos) - 1

    for linha in proc.stdout:
        linha = linha.strip()
        if not linha:
            continue
        try:
            ev = json.loads(linha)
        except Exception:
            continue
        tipo = ev.get("type")

        if tipo == "assistant":
            for b in (ev.get("message") or {}).get("content") or []:
                k = b.get("type")
                if k == "text" and b.get("text", "").strip():
                    emitir({"tipo": "texto", "texto": b["text"]})
                elif k == "thinking":
                    emitir({"tipo": "pensando"})
                elif k == "tool_use":
                    i = emitir({"tipo": "ferramenta", "nome": b.get("name"),
                                "resumo": _resumo_entrada(b.get("name"), b.get("input")),
                                "estado": "rodando"})
                    pendentes[b.get("id")] = i

        elif tipo == "user":
            for b in (ev.get("message") or {}).get("content") or []:
                if b.get("type") != "tool_result":
                    continue
                i = pendentes.pop(b.get("tool_use_id"), None)
                saida = _resumo_saida(b.get("content"))
                if i is None:
                    continue
                passos[i]["estado"] = "erro" if b.get("is_error") else "ok"
                passos[i]["saida"] = saida
                ao_vivo and ao_vivo(dict(passos[i], indice=i, atualiza=True))

        elif tipo == "result" and ev.get("is_error"):
            erro = str(ev.get("result") or "")

    proc.wait()
    bruto_erro = (erro or "") + " " + ((proc.stderr.read() if proc.stderr else "") or "")

    if "no conversation found" in bruto_erro.lower() and not _tentou_de_novo:
        try:
            os.remove(conversas.caminho(cid, "sessao.txt"))
        except Exception:
            pass
        ao_vivo and ao_vivo({"tipo": "aviso", "texto": "retomando em sessão nova…"})
        return _sessao_claude(cid, pid, texto, ao_vivo, _tentou_de_novo=True)

    if erro:
        raise SemAcesso(conta_claude._humano(erro))
    if proc.returncode != 0 and not passos:
        raise SemAcesso(conta_claude._humano(bruto_erro or "falha ao falar com o Claude"))

    fala = "\n\n".join(p["texto"] for p in passos if p["tipo"] == "texto").strip()
    return fala, passos


def falar(cid, texto, anexos=None, quem="usuário", ao_vivo=None):
    """Uma rodada de conversa.

    No método 'sessao' isto é uma mensagem para a sessão do Claude Code — com
    contexto, memória, skills e ferramentas. O app não interpreta nem filtra
    nada: só entrega o ambiente junto e guarda o que voltou."""
    metodo = conta_claude.metodo()
    if metodo is None:
        raise SemAcesso("Escolha como entrar no Claude, na aba Contas.")

    if not cid:
        cid = conversas.criar()
    pid = conversas.meta(cid).get("projeto")
    msgs = conversas.mensagens(cid)
    conteudo = texto or ""
    if anexos:
        conteudo += "\n\nArquivos anexados:\n" + "\n".join("- " + a for a in anexos)
    msgs.append({"role": "user", "content": conteudo, "quando": time.time()})

    if metodo == "sessao":
        resposta, passos = _sessao_claude(cid, pid, conteudo, ao_vivo)
        msgs.append({"role": "assistant", "content": resposta or "(sem resposta)",
                     "passos": [p for p in passos if p["tipo"] != "texto"],
                     "quando": time.time()})
        # o projeto pode ter nascido durante a conversa: amarra os dois
        if not pid:
            recentes = projetos.listar()
            if recentes:
                pid = recentes[0]["id"]
                conversas.gravar_meta(cid, projeto=pid)
        _gravar(cid, msgs)
        return {"mensagens": msgs, "conversa": cid, "projeto": pid}

    return _laco_api(cid, pid, msgs, quem, ao_vivo)


def _laco_api(cid, pid, msgs, quem, ao_vivo):
    """Caminho da chave de API — tool use nativo do SDK."""
    cliente = _cliente()
    contexto = _contexto_ambiente(pid)
    api_msgs = [{"role": m["role"], "content": m["content"]}
                for m in msgs if m.get("role") in ("user", "assistant")]

    for _ in range(12):
        r = cliente.messages.create(model=MODELO, max_tokens=8000,
                                    system=SISTEMA + "\n\n" + contexto,
                                    tools=FERRAMENTAS, messages=api_msgs)
        api_msgs.append({"role": "assistant", "content": r.content})

        if r.stop_reason != "tool_use":
            msgs.append({"role": "assistant",
                         "content": "".join(b.text for b in r.content if b.type == "text"),
                         "quando": time.time()})
            break

        parcial = "".join(b.text for b in r.content if b.type == "text").strip()
        if parcial:
            msgs.append({"role": "assistant", "content": parcial, "quando": time.time()})

        resultados = []
        for b in r.content:
            if b.type != "tool_use":
                continue
            try:
                saida, erro = _executar(pid, b.name, b.input or {}, quem), False
                if saida.get("criado") and not pid:
                    pid = saida["criado"]
            except Exception as e:
                saida, erro = {"erro": str(e)}, True
            msgs.append({"role": "ferramenta", "nome": b.name, "entrada": b.input,
                         "saida": saida, "quando": time.time()})
            resultados.append({"type": "tool_result", "tool_use_id": b.id,
                               "content": json.dumps(saida, ensure_ascii=False,
                                                     default=str)[:6000],
                               "is_error": erro})
        api_msgs.append({"role": "user", "content": resultados})

    _gravar(cid, msgs)
    return {"mensagens": msgs, "conversa": cid, "projeto": pid}
