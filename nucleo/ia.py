"""
Qual IA conduz a conversa — e onde mora a chave dela.

O app nasceu só com o Claude, e de um jeito bem específico: a assinatura roda o
**Claude Code de verdade**, com as skills e as ferramentas do usuário, e o app
entrega as suas por MCP. Isso não tem equivalente na OpenAI, e fingir que tem
seria pior do que não ter. Então:

  * **Claude** continua exatamente como está — sessão do Claude Code (ou a chave
    de API, se o usuário escolheu esse método na aba Contas).
  * **ChatGPT** entra pela **API oficial**, com function calling ligado nas
    MESMAS ferramentas do app. Ele não tem as skills do Claude Code, e a tela
    diz isso em vez de deixar o usuário descobrir sozinho.

Por que API e não CLI: o CLI da OpenAI é um agente de código com autenticação e
formato de saída próprios — seria uma segunda superfície de integração para
manter, sem contrato estável. A API é versionada, documentada, faz streaming e
function calling, e não depende do site do ChatGPT (que é o que o pedido proíbe).
Está escrita em `urllib` de propósito: o app empacota com PyInstaller e cada SDK
a mais é uma chance a mais de quebrar no empacotamento.

**A chave nunca aparece no front-end nem no código.** A ordem de busca existe
porque nenhuma das fontes está garantida numa máquina de aluno:

  1. variável de ambiente do processo — o jeito canônico;
  2. `~/.editorblackbelt/.env` (permissão 0600) — porque um `.app` aberto pelo
     Finder **não herda** o ambiente do shell: `export` no `.zshrc` é invisível
     para ele, e sem este arquivo a variável de ambiente seria uma promessa que
     só funciona para quem abre pelo terminal;
  3. o shell de login, perguntado na hora (mesma técnica do PATH);
  4. o cofre do sistema, que é onde o app já guarda as outras chaves.
"""

import json
import os
import subprocess

from . import chaves

BASE = os.path.expanduser("~/.editorblackbelt")
ESCOLHA = os.path.join(BASE, "ia.json")
ENV = os.path.join(BASE, ".env")

PROVEDORES = {
    "claude": {
        "id": "claude", "nome": "Claude", "papel": "conduz o pipeline",
        "env": None, "servico": "claude",
    },
    "chatgpt": {
        "id": "chatgpt", "nome": "ChatGPT", "papel": "OpenAI, por API",
        "env": "OPENAI_API_KEY", "servico": "openai",
    },
}
PADRAO = "claude"


# ---------------------------------------------------------------- credencial

def _do_arquivo_env(nome):
    """Lê `CHAVE=valor` do .env do app. Aceita aspas e ignora comentário."""
    try:
        with open(ENV, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                k, _, v = linha.partition("=")
                if k.strip() == nome:
                    return v.strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


def _do_shell(nome):
    """Pergunta ao shell de login. É o mesmo motivo do PATH: app aberto pelo
    Finder não vê o que o usuário exportou no perfil dele."""
    if os.name == "nt":
        return None
    shell = os.environ.get("SHELL") or "/bin/zsh"
    try:
        r = subprocess.run([shell, "-lc", 'printf %s "$' + nome + '"'],
                           capture_output=True, text=True, timeout=10)
        v = (r.stdout or "").strip().splitlines()
        return (v[-1].strip() or None) if v else None
    except Exception:
        return None


def chave(pid_provedor):
    """A chave do provedor e DE ONDE ela veio — nunca o valor para a tela."""
    p = PROVEDORES.get(pid_provedor) or {}
    nome = p.get("env")
    if not nome:
        return None, None
    v = os.environ.get(nome)
    if v:
        return v.strip(), "ambiente"
    v = _do_arquivo_env(nome)
    if v:
        return v, "arquivo .env"
    v = _do_shell(nome)
    if v:
        return v, "shell de login"
    v = chaves.ler(p["servico"])
    if v:
        return v, "cofre do sistema"
    return None, None


def guardar_chave(pid_provedor, valor):
    """Grava no `.env` do app, com permissão de dono. Fica FORA do projeto e
    fora do repositório de propósito — chave em pasta de projeto viaja junto
    quando o job vai para o Drive."""
    p = PROVEDORES.get(pid_provedor)
    if not p or not p.get("env"):
        raise ValueError("Esse provedor não usa chave.")
    nome = p["env"]
    os.makedirs(BASE, exist_ok=True)
    linhas, achou = [], False
    try:
        with open(ENV, encoding="utf-8") as f:
            linhas = f.read().splitlines()
    except OSError:
        pass
    valor = (valor or "").strip()
    saida = []
    for l in linhas:
        if l.strip().startswith(nome + "="):
            achou = True
            if valor:
                saida.append("%s=%s" % (nome, valor))
        else:
            saida.append(l)
    if valor and not achou:
        saida.append("%s=%s" % (nome, valor))

    tmp = ENV + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(saida).strip() + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, ENV)
    return {"ok": True, "arquivo": ENV}


# ---------------------------------------------------------------- escolha

def escolhido():
    try:
        with open(ESCOLHA, encoding="utf-8") as f:
            p = json.load(f).get("provedor")
        return p if p in PROVEDORES else PADRAO
    except Exception:
        return PADRAO


def escolher(pid_provedor):
    if pid_provedor not in PROVEDORES:
        raise ValueError("IA desconhecida: " + str(pid_provedor))
    os.makedirs(BASE, exist_ok=True)
    tmp = ESCOLHA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"provedor": pid_provedor}, f)
    os.replace(tmp, ESCOLHA)
    return pid_provedor


def modelo_chatgpt():
    return (os.environ.get("OPENAI_MODEL") or _do_arquivo_env("OPENAI_MODEL")
            or "gpt-5.1")


# ---------------------------------------------------------------- estado

def estado():
    """O que a tela precisa para desenhar o seletor. Sem chave nenhuma aqui."""
    from . import claude as conta_claude
    saida = []
    for p in PROVEDORES.values():
        d = {"id": p["id"], "nome": p["nome"], "papel": p["papel"]}
        if p["id"] == "claude":
            e = conta_claude.estado_conta()
            d["pronto"] = bool(e.get("conectado"))
            d["origem"] = e.get("rotulo", "")
            d["msg"] = "" if d["pronto"] else (
                e.get("msg") or "Conecte o Claude na aba Contas.")
            d["ferramentas"] = "pipeline completo, skills e ferramentas do app"
        else:
            k, origem = chave(p["id"])
            d["pronto"] = bool(k)
            d["origem"] = origem or ""
            d["modelo"] = modelo_chatgpt()
            d["msg"] = "" if k else (
                "Sem a OPENAI_API_KEY. Ponha no ambiente ou em %s." % ENV)
            d["ferramentas"] = "ferramentas do app (sem as skills do Claude Code)"
        saida.append(d)
    return {"provedores": saida, "escolhido": escolhido(), "env": ENV}
