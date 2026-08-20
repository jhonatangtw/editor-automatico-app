"""
Os quatro serviços de geração — conectar e conferir.

Dois jeitos diferentes de entrar, e a diferença não é escolha nossa:

  Higgsfield  entra de verdade. O CLI faz OAuth no navegador (`auth login`)
              e guarda o token dele mesmo. Não pedimos chave nenhuma.
  Os outros   não oferecem "Entrar com..." pra app de terceiro. O que existe
              é chave de API. Então a tela pede a chave, guarda no cofre do
              sistema (ver chaves.py) e prova que funciona chamando o serviço.

Sobre a tabela abaixo: cada serviço é DADO, não código. Quando um endpoint
mudar — e vai mudar — o conserto é uma linha aqui, não uma função nova.

VERIFICAÇÃO: o Higgsfield foi testado ao vivo nesta máquina. Os outros três
foram escritos a partir da documentação de cada um e **ainda não passaram por
um teste com chave real** — não tenho chave deles aqui. O primeiro "Testar
conexão" de cada um é que fecha essa conta; se algum responder 404, é o
caminho da tabela que está errado, não a sua chave.
"""

import json
import subprocess
import urllib.error
import urllib.request

from . import chaves, claude as _claude, so

# nome do cabeçalho, caminho do teste e onde ler o saldo na resposta
TABELA = {
    "claude": {
        "titulo": "Claude",
        "papel": "decide a edição",
        "modo": "anthropic",
        "verificado": True,
    },
    "elevenlabs": {
        "titulo": "ElevenLabs",
        "papel": "voz — única fonte de áudio do app",
        "modo": "chave",
        "url": "https://api.elevenlabs.io/v1/user",
        "cabecalho": "xi-api-key",
        "prefixo": "",
        "verificado": False,
    },
    "heygen": {
        "titulo": "HeyGen",
        "papel": "avatar falante",
        # CLI oficial com OAuth. A diferença NÃO é comodidade, é dinheiro:
        # `heygen auth login --oauth` gasta CRÉDITO DE ASSINATURA; chave de API
        # gasta a carteira de API, que costuma estar quase vazia. Nesta máquina
        # a carteira tinha US$ 0,15 e a assinatura, 11.647 créditos.
        "modo": "cli",
        "cli": "heygen",
        # v3. O /v2/user/remaining_quota ainda responde, mas a própria HeyGen
        # avisa no corpo que ele é legado e sai do ar em 31/10/2026 — sair
        # dele agora é mais barato que sair depois com alunos instalados.
        "url": "https://api.heygen.com/v3/users/me",
        "cabecalho": "X-Api-Key",
        "prefixo": "",
        "verificado": True,
    },
    "minimax": {
        "titulo": "MiniMax",
        "papel": "vídeo, imagem e música",
        # CLI oficial `mmx`. Tem OAuth (`--recommend`) além de chave — e o OAuth
        # é o caminho recomendado por eles, mesmo padrão do HeyGen.
        # ⚠️ O `mmx` também faz VOZ (`mmx speech`). O app NÃO usa: voz é
        # ElevenLabs e só — decisão do Jhon.
        "modo": "cli",
        "cli": "mmx",
        "verificado": True,
    },
    "higgsfield": {
        "titulo": "Higgsfield",
        "papel": "b-roll e imagem",
        "modo": "cli",
        "verificado": True,
    },
}


def _http(url, cabecalho, valor, metodo="GET"):
    req = urllib.request.Request(url, method=metodo, headers={
        cabecalho: valor, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            bruto = r.read().decode("utf-8", "replace")
        try:
            return True, json.loads(bruto)
        except Exception:
            return True, {}
    except urllib.error.HTTPError as e:
        detalhe = ""
        try:
            detalhe = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        return False, {"http": e.code, "detalhe": detalhe}
    except Exception as e:
        return False, {"rede": str(e)}


# ------------------------------------------------------------ Higgsfield

def abrir_no_terminal(comando, titulo=""):
    from . import so
    return so.terminal(comando, titulo)


def _abrir_no_terminal_mac(comando, titulo=""):
    """Roda um login interativo num Terminal de verdade.

    ⚠️ CLI de OAuth precisa de TTY. Disparado por Popen dentro do app, o `mmx`
    responde "--api-key is required in non-interactive mode" e morre na hora —
    e como eu descartava a saída, a tela dizia "abri o navegador" enquanto nada
    acontecia. Abrir o Terminal.app dá o TTY que falta e o navegador abre
    sozinho a partir dele."""
    import shlex
    linha = " ".join(shlex.quote(x) for x in comando)
    script = (
        'tell application "Terminal"\n'
        '  activate\n'
        '  do script "%s"\n'
        'end tell' % linha.replace("\\", "\\\\").replace('"', '\\"'))
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True,
                           text=True, timeout=25)
        if r.returncode != 0:
            return {"ok": False, "msg": (r.stderr or "").strip()[:160]}
        return {"ok": True,
                "msg": "Abri o Terminal com o login%s. Autorize no navegador e "
                       "volte aqui." % (" do " + titulo if titulo else "")}
    except Exception as e:
        return {"ok": False, "msg": str(e)[:160]}


def _minimax_status():
    try:
        r = so.run(["mmx", "auth", "status"], capture_output=True,
                           text=True, timeout=40)
    except FileNotFoundError:
        return {"conectado": False,
                "msg": "O CLI da MiniMax não está instalado. Instale na aba Ambiente."}
    except Exception as e:
        return {"conectado": False, "msg": str(e)}

    bruto = (r.stdout or "") + (r.stderr or "")
    try:
        # o CLI imprime um banner ASCII antes do JSON
        i = bruto.index("{")
        d = json.loads(bruto[i:])
    except Exception:
        return {"conectado": False, "msg": "Não está conectado. Clique em Entrar."}

    if d.get("error"):
        return {"conectado": False, "msg": "Não está conectado. Clique em Entrar."}

    conta = (d.get("email") or d.get("user") or d.get("account")
             or (d.get("auth") or {}).get("email") or "")
    quota = d.get("quota") or d.get("quotas") or {}
    saldo = ""
    if isinstance(quota, dict):
        for k in ("remaining", "balance", "tokens_remaining"):
            if quota.get(k) is not None:
                saldo = "%s restante" % quota[k]
                break
    tipo = "OAuth" if (d.get("type") or d.get("method")) == "oauth" else "chave"
    return {"conectado": True, "conta": conta,
            "saldo": saldo or ("conectado por %s" % tipo)}


def minimax_entrar(chave=None):
    """OAuth por padrão (o caminho que a própria MiniMax recomenda). Com chave,
    grava direto sem abrir navegador."""
    try:
        if chave:
            r = so.run(["mmx", "auth", "login", "--api-key", chave],
                               capture_output=True, text=True, timeout=90)
            ok = r.returncode == 0
            return {"ok": ok, "msg": "Chave guardada pelo CLI." if ok
                    else (r.stderr or r.stdout or "").strip()[:160]}
        from shutil import which
        if not which("mmx"):
            return {"ok": False, "msg": "O CLI da MiniMax não está instalado. "
                                        "Instale na aba Ambiente."}
        return abrir_no_terminal(["mmx", "auth", "login", "--recommend",
                                  "--region=global"], "MiniMax")
    except Exception as e:
        return {"ok": False, "msg": str(e)[:160]}


def minimax_sair():
    so.run(["mmx", "auth", "logout"], capture_output=True)
    return {"ok": True}


def _heygen_status():
    try:
        r = so.run(["heygen", "auth", "status"], capture_output=True,
                           text=True, timeout=40)
    except FileNotFoundError:
        return {"conectado": False,
                "msg": "O CLI do HeyGen não está instalado nesta máquina."}
    except Exception as e:
        return {"conectado": False, "msg": str(e)}
    if r.returncode != 0:
        return {"conectado": False, "msg": "Não está conectado. Clique em Entrar."}
    try:
        d = json.loads(r.stdout)
    except Exception:
        return {"conectado": False, "msg": "Resposta inesperada do CLI."}

    cred = d.get("credential") or {}
    dados = d.get("data") or {}
    assin = dados.get("subscription") or {}
    cred_rest = ((assin.get("credits") or {}).get("add_on_credits") or {}).get("remaining")
    tipo = "assinatura" if cred.get("type") == "oauth" else "chave de API"
    return {
        "conectado": True,
        "conta": (cred.get("user") or {}).get("email") or dados.get("email", ""),
        "saldo": ("%s créditos · plano %s (%s)"
                  % (cred_rest, assin.get("plan", "?"), tipo)) if cred_rest is not None
                 else "plano %s (%s)" % (assin.get("plan", "?"), tipo),
    }


def heygen_entrar():
    """OAuth no navegador — usa crédito de ASSINATURA, não a carteira de API."""
    from shutil import which
    if not which("heygen"):
        return {"ok": False, "msg": "O CLI do HeyGen não está instalado."}
    return abrir_no_terminal(["heygen", "auth", "login", "--oauth"], "HeyGen")


def heygen_sair():
    so.run(["heygen", "auth", "logout"], capture_output=True)
    return {"ok": True}


def _higgs_status():
    try:
        r = so.run(["higgsfield", "account", "status", "--json"],
                           capture_output=True, text=True, timeout=40)
    except FileNotFoundError:
        return {"conectado": False,
                "msg": "O CLI do Higgsfield não está instalado nesta máquina."}
    except Exception as e:
        return {"conectado": False, "msg": str(e)}

    if r.returncode != 0:
        return {"conectado": False, "msg": "Não está conectado. Clique em Entrar."}
    try:
        d = json.loads(r.stdout)
    except Exception:
        return {"conectado": False, "msg": "Resposta inesperada do CLI."}
    return {
        "conectado": True,
        "conta": d.get("email", ""),
        "saldo": "%s créditos · plano %s" % (
            format(int(d.get("credits", 0)), ",d").replace(",", "."),
            d.get("subscription_plan_type", "?")),
    }


def higgs_entrar():
    """OAuth do Higgsfield. Vai pelo Terminal pelo mesmo motivo dos outros:
    fluxo interativo precisa de TTY."""
    from shutil import which
    if not which("higgsfield"):
        return {"ok": False, "msg": "O CLI do Higgsfield não está instalado."}
    return abrir_no_terminal(["higgsfield", "auth", "login"], "Higgsfield")


def higgs_sair():
    so.run(["higgsfield", "auth", "logout"], capture_output=True)
    return {"ok": True}


# ------------------------------------------------------------ chave

def _conta_legivel(sid, dados):
    """Qual conta é essa. Quem tem duas assinaturas precisa enxergar a
    diferença antes de gastar crédito da errada."""
    try:
        d = (dados.get("data") or dados)
        return d.get("email", "") or ""
    except Exception:
        return ""


def _saldo_legivel(sid, dados):
    """Cada serviço conta o que sobra de um jeito. Sem isso a tela mostraria
    JSON cru pro aluno."""
    try:
        if sid == "elevenlabs":
            s = (dados.get("subscription") or {})
            usado = s.get("character_count")
            teto = s.get("character_limit")
            if usado is not None and teto:
                return "%s de %s caracteres usados" % (
                    format(usado, ",d").replace(",", "."),
                    format(teto, ",d").replace(",", "."))
        if sid == "heygen":
            d = (dados.get("data") or dados)
            w = d.get("wallet") or {}
            if "remaining_balance" in w:
                return "US$ %.2f na carteira" % float(w["remaining_balance"])
    except Exception:
        pass
    return ""


def testar(sid):
    cfg = TABELA.get(sid)
    if not cfg:
        return {"ok": False, "msg": "Serviço desconhecido."}

    if cfg["modo"] == "anthropic":
        return _claude.testar()

    if cfg["modo"] == "cli":
        e = ({"heygen": _heygen_status, "minimax": _minimax_status}
             .get(sid, _higgs_status))()
        return {"ok": e["conectado"], "msg": e.get("msg", ""),
                "conta": e.get("conta", ""), "saldo": e.get("saldo", "")}

    k = chaves.ler(sid)
    if not k:
        return {"ok": False, "msg": "Sem chave guardada."}

    ok, dados = _http(cfg["url"], cfg["cabecalho"], cfg["prefixo"] + k)
    if ok:
        return {"ok": True, "msg": "Conectado.",
                "conta": _conta_legivel(sid, dados),
                "saldo": _saldo_legivel(sid, dados)}

    if dados.get("http") in (401, 403):
        return {"ok": False, "msg": "A chave foi recusada. Confira se copiou inteira."}
    if dados.get("http") == 404:
        return {"ok": False,
                "msg": "O endereço de teste deste serviço mudou — é do app, não da sua chave."}
    if dados.get("rede"):
        return {"ok": False, "msg": "Sem resposta. Verifique sua internet."}
    return {"ok": False, "msg": "Resposta inesperada (HTTP %s)." % dados.get("http", "?")}


def estado():
    """O que a tela de Contas desenha. Não testa a rede — só diz o que existe.
    Testar é clique, porque bater em quatro serviços a cada abertura é lento e,
    em alguns planos, contado."""
    saida = []
    guardadas = chaves.resumo()
    for sid, cfg in TABELA.items():
        item = {"id": sid, "titulo": cfg["titulo"], "papel": cfg["papel"],
                "modo": cfg["modo"], "verificado": cfg["verificado"],
                "opcional": cfg.get("opcional", False)}
        if cfg["modo"] == "anthropic":
            e = _claude.estado()
            item.update(pronto=e["pronto"], conta=e.get("detalhe", ""),
                        alerta=e.get("alerta", ""), tem_cli=e.get("tem_cli", False))
        elif cfg["modo"] == "cli":
            e = ({"heygen": _heygen_status, "minimax": _minimax_status}
                 .get(sid, _higgs_status))()
            item.update(pronto=e["conectado"], conta=e.get("conta", ""),
                        saldo=e.get("saldo", ""), msg=e.get("msg", ""))
        else:
            g = guardadas.get(sid, {})
            item.update(pronto=g.get("tem", False), fim=g.get("fim", ""))
        saida.append(item)
    return {"servicos": saida, "cofre": chaves.cofre()}
