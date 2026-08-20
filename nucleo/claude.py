"""
Conta Claude (Anthropic) — quem toma as decisões de edição.

É a conexão mais importante do app: o Higgsfield gera pixel, o HeyGen fala, mas
quem decide ONDE entra o insert, qual fala justifica o corte e o que vira
lettering é o Claude. Sem esta conta o app vira um player de ffmpeg.

Duas portas de entrada, e a ordem importa:

  1. CONTA (OAuth)  — `ant auth login` abre o navegador, a pessoa entra com a
     conta Anthropic dela e o CLI guarda um perfil em ~/.config/anthropic/.
     É o mesmo formato do login do Higgsfield: ninguém copia e cola segredo.
  2. CHAVE DE API   — sk-ant-… do console.anthropic.com, para quem prefere
     pagar por uso avulso ou não quer instalar o CLI.

⚠️ A armadilha que vale ouro: **uma ANTHROPIC_API_KEY exportada no shell
silencia o perfil OAuth inteiro.** A ordem de resolução é ANTHROPIC_API_KEY →
ANTHROPIC_AUTH_TOKEN → perfil ativo, primeiro que casar vence. Então alguém
pode "entrar" com a conta certa, seguir usando a chave velha de outra conta e
não entender por que a cobrança cai no lugar errado. Por isso `fonte()` abaixo
não pergunta o que a pessoa quis — ele reporta quem de fato venceu, e a tela
mostra isso.
"""

import json
import os
import subprocess
import urllib.error
import urllib.request

from . import chaves, so

API = "https://api.anthropic.com/v1/models"
VERSAO = "2023-06-01"

# OAuth vai no Authorization: Bearer + este beta; chave de API vai no x-api-key.
# Trocar um pelo outro é erro de cabeçalho, não de credencial.
BETA_OAUTH = "oauth-2025-04-20"


# ---------------------------------------------------------------- método
#
# O usuário ESCOLHE como entrar, e o app respeita a escolha sem inventar
# alternativa. Cair sozinho de "sessão do Claude" para "chave de API" foi o que
# gerou o erro mais confuso do app: a pessoa tinha assinatura válida e via
# "credit balance is too low" de uma conta que nem sabia que existia.

ESCOLHA = os.path.expanduser("~/.editorblackbelt/claude-metodo.json")

# ⚠️ A DESCOBERTA que conserta tudo:
#
# Um perfil OAuth do `ant` em ~/.config/anthropic ENCOBRE a sessão do Claude
# Code. A ordem de resolução é perfil antes do login próprio do CLI — então
# quem faz `ant auth login` numa org de Console sem crédito passa a receber
# "Credit balance is too low" mesmo tendo assinatura Max ativa. O `claude -p`
# falha igual, o que faz parecer problema da assinatura.
#
# Apontar ANTHROPIC_CONFIG_DIR para uma pasta vazia esconde o perfil SÓ para o
# processo que o app dispara. Não mexe na configuração do usuário, não desloga
# nada — e a sessão da assinatura volta a valer. Verificado nesta máquina.
VAZIO = os.path.expanduser("~/.editorblackbelt/sem-perfil")


def metodo():
    """Como o usuário escolheu entrar: 'sessao' (CLI) ou 'chave'."""
    try:
        with open(ESCOLHA, encoding="utf-8") as f:
            m = json.load(f).get("metodo")
        if m in ("sessao", "chave"):
            return m
    except Exception:
        pass
    return "sessao" if tem_claude_cli() else ("chave" if chaves.ler("claude") else None)


def definir_metodo(m):
    if m not in ("sessao", "chave"):
        raise ValueError("método inválido")
    os.makedirs(os.path.dirname(ESCOLHA), exist_ok=True)
    tmp = ESCOLHA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"metodo": m}, f)
    os.replace(tmp, ESCOLHA)
    return m


def tem_claude_cli():
    from shutil import which
    return which("claude") is not None


def ambiente_isolado():
    """Ambiente para rodar o CLI sem o perfil do `ant` no caminho."""
    os.makedirs(VAZIO, exist_ok=True)
    env = dict(os.environ)
    env["ANTHROPIC_CONFIG_DIR"] = VAZIO
    # uma chave exportada no shell também encobriria a sessão
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    env.pop("ANTHROPIC_PROFILE", None)
    return env


def sessao_cli():
    """Estado da sessão do Claude Code — sem falar de crédito."""
    if not tem_claude_cli():
        return {"ok": False, "instalar": True,
                "msg": "O Claude Code não está instalado nesta máquina. Instale "
                       "pela aba Ambiente e volte aqui."}
    try:
        bruto = subprocess.run(
            ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
            capture_output=True, text=True, timeout=15)
        if bruto.returncode != 0:
            # "rode no Terminal" é o conselho que o app existe para não dar.
            # Quem trata isso agora é o botão Entrar, que abre o Terminal sozinho.
            return {"ok": False, "entrar": True,
                    "msg": "O Claude Code está instalado, mas ninguém entrou numa "
                           "conta ainda. Clique em Entrar — abro o Terminal com o "
                           "login e o navegador abre a partir dele."}
        d = json.loads(bruto.stdout).get("claudeAiOauth") or {}
        return {"ok": True, "assinatura": d.get("subscriptionType") or "conta",
                "escopos": d.get("scopes") or []}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def _cli(*args, timeout=40):
    try:
        r = so.run(("ant",) + args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return None, "sem_cli"
    except Exception as e:
        return None, str(e)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout or "").strip()
    return r.stdout.strip(), None


def tem_cli():
    return _cli("--version", timeout=10)[1] != "sem_cli"


def fonte():
    """Qual credencial VENCE agora — não qual a pessoa configurou.

    Devolve: ('ambiente', ...) | ('perfil', ...) | ('chave', ...) | (None, ...)
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "ambiente", "ANTHROPIC_API_KEY exportada no shell"
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "ambiente", "ANTHROPIC_AUTH_TOKEN exportada no shell"

    saida, erro = _cli("auth", "status")
    if not erro and saida and "profile" in saida.lower():
        return "perfil", saida.splitlines()[0][:120]

    if chaves.ler("claude"):
        return "chave", "chave de API guardada no cofre"
    return None, ""


def _token_oauth():
    """Token curto do perfil ativo. Sem --access-token o CLI imprime o JSON
    inteiro, e um JSON no cabeçalho Authorization vira erro de protocolo."""
    saida, erro = _cli("auth", "print-credentials", "--access-token")
    return None if erro else (saida or "").strip()


def _cabecalhos():
    origem, _ = fonte()
    base = {"anthropic-version": VERSAO, "Accept": "application/json"}

    if origem == "chave":
        base["x-api-key"] = chaves.ler("claude")
        return base, "chave de API"

    if origem == "ambiente":
        k = os.environ.get("ANTHROPIC_API_KEY")
        if k:
            base["x-api-key"] = k
            return base, "variável de ambiente"
        base["Authorization"] = "Bearer " + os.environ["ANTHROPIC_AUTH_TOKEN"]
        base["anthropic-beta"] = BETA_OAUTH
        return base, "variável de ambiente"

    if origem == "perfil":
        t = _token_oauth()
        if t:
            base["Authorization"] = "Bearer " + t
            base["anthropic-beta"] = BETA_OAUTH
            return base, "conta conectada"

    return None, ""


def entrar_sessao():
    """Login do Claude Code num terminal DE VERDADE.

    ⚠️ O `claude` abre um fluxo interativo e precisa de TTY — disparado por
    Popen mudo ele morre na hora, e o app reportaria sucesso sobre um processo
    morto (já aconteceu com os quatro outros logins de CLI)."""
    if not tem_claude_cli():
        return {"ok": False,
                "msg": "O Claude Code não está instalado. Instale pela aba Ambiente."}
    from . import so
    r = so.terminal(["claude"], "Claude")
    if r.get("ok"):
        r["msg"] = ("Abri o Terminal com o Claude. Escolha entrar com a sua conta, "
                    "autorize no navegador e volte aqui para clicar em Reconectar.")
    return r


def entrar():
    """Abre o navegador pro OAuth. Não trava a janela esperando."""
    if not tem_cli():
        return {"ok": False, "precisa_cli": True,
                "msg": "Para entrar com a conta é preciso o CLI da Anthropic. "
                       "No Terminal: brew tap anthropics/tap && brew install ant"}
    try:
        so.popen(["ant", "auth", "login"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "msg": "Abri o navegador. Autorize e volte aqui."}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def sair():
    _cli("auth", "logout")
    chaves.apagar("claude")
    return {"ok": True}


def testar():
    """Lista os modelos. É o teste mais barato que existe: prova a credencial,
    não gasta token nenhum, e de quebra mostra a que modelos a conta chega."""
    cab, como = _cabecalhos()
    if not cab:
        return {"ok": False, "msg": "Sem conta conectada e sem chave guardada."}

    req = urllib.request.Request(API, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {"ok": False,
                    "msg": "A credencial foi recusada. Se você entrou com a conta "
                           "mas exportou uma ANTHROPIC_API_KEY antiga no terminal, "
                           "é ela que está valendo — apague a variável."}
        return {"ok": False, "msg": "Resposta inesperada (HTTP %d)." % e.code}
    except Exception:
        return {"ok": False, "msg": "Sem resposta. Verifique sua internet."}

    modelos = [m.get("id", "") for m in (dados.get("data") or [])]
    return {"ok": True, "msg": "Conectado.", "conta": como,
            "saldo": "%d modelos disponíveis" % len(modelos),
            "modelos": modelos[:8]}


def estado_conta():
    """O que a aba Contas mostra: método ativo, conta, status. Sem crédito —
    consultar saldo aqui só criava ruído e uma chamada de rede a mais."""
    m = metodo()
    if m == "sessao":
        s = sessao_cli()
        return {"metodo": "sessao",
                "rotulo": "Sessão do Claude Code",
                "conta": ("assinatura " + s["assinatura"]) if s["ok"] else "",
                "conectado": s["ok"],
                "msg": s.get("msg", ""),
                "entrar": bool(s.get("entrar")),
                "instalar": bool(s.get("instalar")),
                "pode_trocar": bool(chaves.ler("claude")) or True}
    if m == "chave":
        k = chaves.ler("claude")
        return {"metodo": "chave", "rotulo": "Chave de API",
                "conta": ("chave …" + k[-4:]) if k else "",
                "conectado": bool(k), "msg": "" if k else "Sem chave guardada.",
                "pode_trocar": True}
    return {"metodo": None, "rotulo": "Não conectado", "conta": "",
            "conectado": False,
            "msg": "Escolha como entrar: sessão do Claude Code ou chave de API.",
            "pode_trocar": True}


def testar_conta():
    """Uma chamada mínima pelo método ATIVO. Não tenta o outro por conta própria."""
    m = metodo()
    if m == "sessao":
        if not tem_claude_cli():
            return {"ok": False, "msg": "O Claude Code não está instalado."}
        try:
            r = so.run(["claude", "-p", "--output-format", "json", "responda: ok"],
                               capture_output=True, text=True, timeout=90,
                               env=ambiente_isolado())
            d = json.loads(r.stdout or "{}")
            if d.get("is_error"):
                return {"ok": False, "msg": _humano(str(d.get("result") or ""))}
            return {"ok": True, "msg": "Sessão respondendo."}
        except Exception as e:
            return {"ok": False, "msg": _humano(str(e))}
    if m == "chave":
        return testar()
    return {"ok": False, "msg": "Escolha um método de conexão."}


def _humano(bruto):
    """Traduz o erro cru em algo que ensina o que fazer."""
    b = (bruto or "").lower()
    if "credit balance" in b or "too low" in b:
        return ("A conta que está valendo não tem crédito de API. Se você usa "
                "assinatura, troque o método para “Sessão do Claude Code”.")
    if "not logged in" in b or "unauthorized" in b or "401" in b:
        return "A sessão expirou. Reconecte."
    if "no conversation found" in b:
        return "A conversa anterior não foi encontrada. Mande a mensagem de novo — "\
               "eu começo uma sessão nova."
    if "not found" in b or "no such file" in b:
        return "O Claude Code não está instalado nesta máquina."
    if "already in use" in b or "in use by another" in b or "is running" in b:
        return ("Esta conversa já está sendo respondida. Espere a resposta atual "
                "terminar antes de mandar outra — uma sessão de cada vez.")
    if "rate limit" in b or "usage limit" in b or "429" in b:
        return "Você bateu o limite de uso da assinatura. Tente daqui a pouco."
    # ⚠️ O que sobra vai COM O MOTIVO. Antes esta linha devolvia só "a conexão
    # não está disponível" e jogava o erro fora — e aí ninguém, nem eu, tinha
    # como saber o que aconteceu na máquina do usuário.
    limpo = " ".join((bruto or "").split())[:220]
    return ("A conexão com o Claude falhou." + (" Motivo: " + limpo if limpo else ""))


def estado():
    origem, detalhe = fonte()
    return {
        "pronto": origem is not None,
        "origem": origem,
        "detalhe": detalhe,
        "tem_cli": tem_cli(),
        # o aviso que evita o chamado de suporte mais chato deste app
        "alerta": ("Uma chave exportada no terminal está na frente da sua conta."
                   if origem == "ambiente" else ""),
    }
