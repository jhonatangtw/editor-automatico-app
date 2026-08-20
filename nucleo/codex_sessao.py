"""
ChatGPT pela ASSINATURA — o Codex CLI conduzindo a conversa.

Por que isto existe, mesmo já tendo a API: no `~/.codex/auth.json` do usuário o
`auth_mode` é **chatgpt**. Ou seja, ele já paga uma assinatura que dá acesso ao
modelo — e a chave de API cobraria por fora, de novo, pelo que ele já tem. É a
mesma lição do HeyGen: login de conta gasta a ASSINATURA, chave gasta a carteira
de API, e mandar o aluno usar a chave é queimar o bolso errado.

É o espelho exato do que já fazemos com o Claude:

    Claude   →  `claude -p --session-id … --mcp-config …`
    ChatGPT  →  `codex exec [resume <thread>] --json -c mcp_servers.editor=…`

Nos dois casos o agente roda de verdade, com as ferramentas DESTE app entregues
por MCP — e passa pelos mesmos portões do pipeline.

⚠️ **Aprovação: só o bypass serve, e a razão é o `resume`.** Sem flag nenhum o
Codex recusa toda ferramenta ("requires approval, but approval policy is never").
No PRIMEIRO turno `--approve-for-me` resolveria mantendo o sandbox — mas o
`codex exec resume` **não aceita esse flag**, e a thread retomada não herda a
política: `-c approval_policy=...` também não vira. Medido nos dois casos. Como
uma conversa é feita de retomadas, usar o flag estreito só no primeiro turno
daria a um mesmo agente poderes diferentes conforme a mensagem — pior de
raciocinar do que assumir um nível de confiança só.

É o MESMO nível que este app já dá ao Claude Code (`--permission-mode
bypassPermissions`): agente do próprio usuário, na máquina dele, com as
ferramentas do app trancadas pelos portões do pipeline.

⚠️ **`resume` aceita menos flags que `exec`**: nada de `--approve-for-me`, `-s`
nem `-C`. Passar um deles faz o Codex sair com erro de uso — e a mensagem dele
contém "SESSION_ID", que casou com a minha regra de "sessão não encontrada" e
disparou um recomeço em thread nova. Resultado: a conversa respondia SEM memória
em vez de acusar o erro. O meu próprio contorno escondeu o defeito.

⚠️ **stdin fechado.** Com stdin de pipe o Codex imprime "Reading additional
input from stdin..." e espera — o app ficaria pendurado para sempre.
"""

import json
import os
import subprocess

from . import so

CODEX_HOME = os.path.expanduser("~/.codex")
AUTH = os.path.join(CODEX_HOME, "auth.json")


class SemCodex(RuntimeError):
    pass


def disponivel():
    return so.onde("codex") is not None


def conta():
    """Como o Codex está autenticado nesta máquina — sem tocar no token."""
    if not disponivel():
        return {"ok": False, "instalado": False,
                "msg": "O Codex CLI não está instalado. Instale pela aba Ambiente."}
    try:
        with open(AUTH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return {"ok": False, "instalado": True,
                "msg": "O Codex está instalado mas ninguém entrou numa conta. "
                       "Clique em Entrar — abro o Terminal com o login."}
    modo = d.get("auth_mode") or ""
    return {"ok": True, "instalado": True, "modo": modo,
            "rotulo": ("assinatura do ChatGPT" if modo == "chatgpt"
                       else "chave de API no Codex" if modo else "conectado"),
            "msg": ""}


def entrar():
    """Login interativo — precisa de TTY, como todos os outros."""
    if not disponivel():
        return {"ok": False, "msg": "O Codex CLI não está instalado. "
                                    "Instale pela aba Ambiente."}
    r = so.terminal(["codex", "login"], "ChatGPT")
    if r.get("ok"):
        r["msg"] = ("Abri o Terminal com o login do Codex. Escolha “Sign in with "
                    "ChatGPT”, autorize no navegador e volte aqui.")
    return r


# ---------------------------------------------------------------- a conversa

def _mcp_toml():
    """Injeta o servidor MCP do app como tabela TOML na linha de comando.

    O Codex lê servidores de MCP do config.toml; `-c` aceita TOML solto, então
    dá para entregar o nosso SEM escrever no arquivo de configuração do
    usuário — mexer no config.toml dele seria invadir uma casa que não é nossa."""
    from . import conversa
    cmd, args = conversa.comando_mcp()
    lista = ", ".join(json.dumps(a) for a in args)
    return "mcp_servers.editor={command=%s, args=[%s]}" % (json.dumps(cmd), lista)


def _thread(cid):
    from . import conversas
    return conversas.caminho(cid, "codex.txt")


def _ler_thread(cid):
    try:
        with open(_thread(cid), encoding="utf-8") as f:
            return (f.read() or "").strip() or None
    except OSError:
        return None


def _gravar_thread(cid, tid):
    try:
        with open(_thread(cid), "w", encoding="utf-8") as f:
            f.write(tid)
    except OSError:
        pass


def conversar(cid, pid, texto, ao_vivo, _tentou_de_novo=False):
    """Uma rodada. Devolve (resposta, passos, thread)."""
    from . import conversa

    if not disponivel():
        raise SemCodex("O Codex CLI não está instalado. Instale pela aba Ambiente.")
    c = conta()
    if not c["ok"]:
        raise SemCodex(c["msg"])

    casa = conversa._casa(cid)
    thread = _ler_thread(cid)

    # ⚠️ Os dois modos NÃO aceitam os mesmos flags. `-C` só existe no `exec`; a
    # casa da retomada vem do `cwd` do processo, que vale para os dois.
    cmd = [so.onde("codex"), "exec"]
    if thread:
        cmd += ["resume", thread]
    cmd += ["--json", "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox", "-c", _mcp_toml()]
    if not thread:
        cmd += ["-C", casa]

    # o Codex não tem "--append-system-prompt": o contexto do ambiente vai
    # colado na primeira mensagem da thread, e depois a própria thread lembra
    pergunta = texto
    if not thread:
        pergunta = (conversa.SISTEMA + "\n\n" + conversa._contexto_ambiente(pid)
                    + "\n\n---\n\n" + texto)
    cmd.append(pergunta)

    passos, erro = [], None
    pendentes = {}

    def emitir(ev):
        passos.append(ev)
        ao_vivo and ao_vivo(ev)
        return len(passos) - 1

    proc = so.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL, text=True, bufsize=1, cwd=casa)

    for linha in proc.stdout:
        linha = linha.strip()
        if not linha.startswith("{"):
            continue                      # ruído de log do Codex vai para stderr
        try:
            ev = json.loads(linha)
        except Exception:
            continue

        tipo = ev.get("type")
        if tipo == "thread.started" and ev.get("thread_id"):
            _gravar_thread(cid, ev["thread_id"])
            thread = ev["thread_id"]
            continue

        item = ev.get("item") or {}
        it = item.get("type")

        if tipo == "item.started" and it == "mcp_tool_call":
            pendentes[item.get("id")] = emitir({
                "tipo": "ferramenta", "nome": item.get("tool") or "?",
                "resumo": conversa._resumo_entrada(item.get("tool") or "",
                                                   item.get("arguments") or {}),
                "estado": "rodando"})
        elif tipo == "item.completed" and it == "mcp_tool_call":
            i = pendentes.pop(item.get("id"), None)
            ruim = bool(item.get("error")) or item.get("status") == "failed"
            saida = ((item.get("error") or {}).get("message") if ruim
                     else _texto_do_resultado(item.get("result")))
            ev2 = {"tipo": "ferramenta", "nome": item.get("tool") or "?",
                   "resumo": conversa._resumo_entrada(item.get("tool") or "",
                                                      item.get("arguments") or {}),
                   "estado": "erro" if ruim else "ok",
                   "saida": (saida or "")[:160]}
            if i is None:
                emitir(ev2)
            else:
                passos[i] = ev2
                ao_vivo and ao_vivo(dict(ev2, indice=i, atualiza=True))
        elif tipo == "item.completed" and it == "agent_message":
            emitir({"tipo": "texto", "texto": item.get("text") or ""})
        elif tipo == "item.completed" and it == "command_execution":
            emitir({"tipo": "ferramenta", "nome": "terminal",
                    "resumo": (item.get("command") or "")[:70],
                    "estado": "erro" if item.get("exit_code") else "ok"})
        elif tipo == "item.completed" and it == "error":
            # o Codex usa "error" também para recado de contexto; não derruba
            emitir({"tipo": "aviso", "texto": (item.get("message") or "")[:180]})
        elif tipo == "turn.failed":
            erro = ((ev.get("error") or {}).get("message")
                    or "O Codex encerrou a rodada com erro.")

    saida_erro = (proc.stderr.read() or "") if proc.stderr else ""
    proc.wait()

    # ⚠️ Erro de USO (flag que o subcomando não aceita) não pode virar recomeço
    # silencioso: foi assim que a conversa perdeu a memória sem ninguém ver.
    if "unexpected argument" in saida_erro.lower():
        raise SemCodex("Chamei o Codex com um argumento que esta versão não "
                       "aceita: " + saida_erro.strip().splitlines()[0][:120])

    # thread que não existe mais: recomeça uma, em vez de morrer
    perdida = any(m in saida_erro.lower() for m in
                  ("cannot resume thread", "error resuming thread",
                   "rollout path missing", "no such thread"))
    if proc.returncode != 0 and thread and not passos and not _tentou_de_novo and perdida:
        try:
            os.remove(_thread(cid))
        except OSError:
            pass
        ao_vivo and ao_vivo({"tipo": "aviso", "texto": "retomando em conversa nova…"})
        return conversar(cid, pid, texto, ao_vivo, _tentou_de_novo=True)

    if erro:
        raise SemCodex(erro)
    if proc.returncode != 0 and not passos:
        raise SemCodex(_explicar_saida(saida_erro))

    fala = "\n\n".join(p["texto"] for p in passos if p["tipo"] == "texto").strip()
    return fala, passos, thread


def _texto_do_resultado(resultado):
    if not isinstance(resultado, dict):
        return ""
    partes = [b.get("text", "") for b in (resultado.get("content") or [])
              if isinstance(b, dict)]
    return " ".join(p for p in partes if p).strip()


def _explicar_saida(txt):
    baixo = (txt or "").lower()
    if "not logged in" in baixo or "unauthorized" in baixo or "401" in baixo:
        return ("O Codex não está logado. Clique em Entrar para autorizar com a "
                "sua conta do ChatGPT.")
    if "rate limit" in baixo or "429" in baixo:
        return ("A OpenAI recusou por limite de uso da assinatura. Tente de novo "
                "daqui a pouco.")
    if "usage limit" in baixo or "quota" in baixo:
        return "A sua assinatura do ChatGPT bateu o limite de uso do período."
    linhas = [l for l in (txt or "").splitlines()
              if l.strip() and "ERROR rmcp" not in l]
    return ("O Codex falhou: " + (linhas[-1][:200] if linhas else "sem detalhe."))
