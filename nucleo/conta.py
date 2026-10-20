"""
Conta Tools PRO — a porta de entrada do app.

Fala com o mesmo Worker que o painel do Premiere já usa, e — isto é o ponto
importante — **divide a mesma sessão com ele**.

Por que dividir: o servidor conta máquinas por uma "impressão" que o painel
gera aleatória e guarda em ~/.editorblackbelt/sessao.json. O plano do aluno
permite 2 computadores. Se este app fizesse o próprio login, o mesmo
computador apareceria como uma segunda máquina e o aluno queimaria a vaga
sobrando sem sair da cadeira — e abriria chamado dizendo que o app quebrou a
licença dele.

A regra que evita isso: **nunca chamar /api/login quando já existe token
válido no arquivo.** /api/sessao só revalida, não cria dispositivo. Login novo
é o último recurso, e mesmo aí reusa a impressão que estiver no arquivo.
"""

import hashlib
import json
import os
import platform
import random
import string
import time
import urllib.error
import urllib.request

SERVIDOR = "https://licenca.editorblackbelt.com.br"  # Hostinger desde 03/10/2026; o workers.dev antigo só repassa

PASTA = os.path.expanduser("~/.editorblackbelt")
ARQUIVO = os.path.join(PASTA, "sessao.json")

# as mesmas chaves que o painel CEP escreve — nomes diferentes quebrariam a divisão
CH_TOKEN = "bb_acesso_token"
CH_NOME = "bb_acesso_nome"
CH_ADM = "bb_acesso_adm"
CH_DIGITAL = "bb_digital"
# só deste app (o painel ignora chaves que não conhece): quando e com qual
# token o servidor disse "vale" pela última vez — é o que segura o modo offline
CH_VALIDADO_EM = "ea_validado_em"
CH_VALIDADO_TOKEN = "ea_validado_token"

# Sem internet, o acesso continua por até 7 dias desde a última confirmação
# com o MESMO token. Antes era para sempre — e um token inventado bastava.
OFFLINE_DIAS = 7
MSG_OFFLINE = ("Não consegui confirmar seu acesso: o servidor não respondeu. "
               "Conecte-se à internet e abra o app de novo — sem conexão o app "
               "funciona por até 7 dias desde a última confirmação.")

# A mesma frase vale para e-mail com e sem conta — não dá para descobrir quem é
# aluno digitando e-mails aqui.
MSG_CODIGO = ("Se houver um acesso com este e-mail, enviamos um código de 6 "
              "dígitos. Ele vale por 10 minutos.")


# ---------------------------------------------------------------- arquivo

def _ler():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _gravar(dados):
    """Troca atômica: o painel lê este arquivo a qualquer momento, e um JSON
    pela metade derruba o login dele."""
    try:
        os.makedirs(PASTA, exist_ok=True)
        tmp = ARQUIVO + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False)
        os.replace(tmp, ARQUIVO)
    except Exception:
        pass


def _por(chave, valor):
    d = _ler()
    d[chave] = valor
    _gravar(d)


def _tirar(chave):
    d = _ler()
    d.pop(chave, None)
    _gravar(d)


def token():
    return _ler().get(CH_TOKEN) or ""


def digital():
    """A impressão desta máquina. Se o painel já criou uma, é ela que vale."""
    d = _ler().get(CH_DIGITAL)
    if d:
        return d
    novo = "m-" + "".join(random.choice(string.ascii_lowercase + string.digits)
                          for _ in range(12))
    _por(CH_DIGITAL, novo)
    return novo


def apelido():
    so = "Windows" if platform.system() == "Windows" else "Mac"
    return so + " · " + (platform.node() or platform.platform())


# ---------------------------------------------------------------- rede

# O Worker está atrás do Cloudflare, que RECUSA o User-Agent padrão do Python
# ("Python-urllib/3.x") com erro 1010 — a resposta nem é JSON, é uma página de
# bloqueio. O painel do Premiere nunca sofreu disso porque fetch() dentro do CEP
# já manda User-Agent de navegador. Sem esta linha, nenhum aluno consegue entrar.
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) EditorAutomatico/1.0")


def _chamar(rota, dados=None, metodo="POST", bearer=None, tempo=20):
    """Fala com o servidor e devolve SEMPRE um dict — nunca levanta.

    `bearer` vai no cabeçalho Authorization: as rotas novas da área do aluno
    (/api/passe, /api/atualizacao) leem a sessão dali, não do corpo. `_status`
    leva o código HTTP de volta para quem precisar distinguir 401 de 5xx."""
    corpo = json.dumps(dados or {}).encode("utf-8") if metodo == "POST" else None
    cab = {"User-Agent": _UA, "Accept": "application/json"}
    if corpo is not None:
        cab["Content-Type"] = "application/json"
    if bearer:
        cab["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(SERVIDOR + rota, data=corpo, method=metodo, headers=cab)
    try:
        from . import rede
        with urllib.request.urlopen(req, timeout=tempo, context=rede.contexto()) as r:
            d = json.loads(r.read().decode("utf-8"))
            if isinstance(d, dict):
                d.setdefault("_status", getattr(r, "status", 200))
                return d
            return {"ok": False, "msg": "O servidor respondeu de forma inesperada."}
    except urllib.error.HTTPError as e:
        # o Worker devolve JSON também nos 4xx — a mensagem dele é melhor que a minha
        try:
            d = json.loads(e.read().decode("utf-8"))
            if not isinstance(d, dict):
                raise ValueError
            d["_status"] = e.code
            return d
        except Exception:
            return {"ok": False, "_status": e.code,
                    "msg": "O servidor respondeu de forma inesperada."}
    except Exception as e:
        # ⚠️ Este `except` engolia TUDO e chutava "verifique sua internet" — e o
        # que estava acontecendo de verdade num Mac sem Homebrew era falta de
        # certificado. O aluno foi procurar problema na rede dele por causa
        # desta frase. Agora a causa vem junto.
        from . import rede
        porque = rede.explicar(e)
        return {"ok": False, "offline": True, "causa": str(e)[:200],
                "msg": "Não consegui falar com o servidor. %s" % porque}


# ---------------------------------------------------------------- uso

def _impressao_token(t):
    """Não guarda o token de novo: só um resumo para saber se é o mesmo."""
    return hashlib.sha256(("ea:" + (t or "")).encode("utf-8")).hexdigest()[:32]


def _marcar_validado(t):
    d = _ler()
    d[CH_VALIDADO_EM] = int(time.time())
    d[CH_VALIDADO_TOKEN] = _impressao_token(t)
    _gravar(d)


def _offline_vale(t, d):
    """Houve confirmação boa, com este token, nos últimos OFFLINE_DIAS?"""
    try:
        quando = float(d.get(CH_VALIDADO_EM) or 0)
    except (TypeError, ValueError):
        return False
    agora = time.time()
    if not quando or d.get(CH_VALIDADO_TOKEN) != _impressao_token(t):
        return False
    # relógio voltado para trás também não estica o prazo
    return -86400 <= agora - quando <= OFFLINE_DIAS * 86400


def estado():
    """Quem está logado agora. Não cria máquina — só revalida."""
    t = token()
    if not t:
        return {"entrou": False, "motivo": "sem_token"}

    r = _chamar("/api/sessao", {"token": t})

    # Internet caindo não pode virar reembolso: com token CONFIRMADO há pouco,
    # libera. Token nunca confirmado (ou confirmado há mais de 7 dias) pede
    # conexão — senão qualquer texto no sessao.json abria o app para sempre.
    if r.get("offline"):
        d = _ler()
        if not _offline_vale(t, d):
            return {"entrou": False, "offline": True, "motivo": "offline_sem_confirmacao",
                    "msg": MSG_OFFLINE}
        return {"entrou": True, "offline": True,
                "nome": d.get(CH_NOME, ""), "adm": d.get(CH_ADM) == "1"}

    if not r.get("ok"):
        if r.get("motivo") in ("sem_sessao", "expirou", "sem_conta"):
            _tirar(CH_TOKEN)
        return {"entrou": False, "motivo": r.get("motivo", "recusado"),
                "msg": r.get("msg", "")}

    _marcar_validado(t)
    u = r.get("usuario") or {}
    if u.get("nome"):
        _por(CH_NOME, u["nome"])
    return {"entrou": True, "nome": u.get("nome", ""),
            "email": u.get("email", ""), "adm": bool(u.get("admin"))}


def entrar(email, senha):
    """Login de verdade. Consome vaga de máquina — por isso só quando não há token."""
    r = _chamar("/api/login", {
        "email": email, "senha": senha,
        "impressao": digital(), "apelido": apelido(),
        "so": platform.system(),
    })
    return _guardar_sessao(r)


def _guardar_sessao(r):
    """Grava o token no MESMO arquivo do painel do Premiere. Senha e código
    devolvem o mesmo formato, então os dois caminhos passam por aqui."""
    if not r.get("ok"):
        return r
    if not r.get("token"):
        return {"ok": False, "msg": "O servidor respondeu de forma inesperada."}
    _por(CH_TOKEN, r["token"])
    _marcar_validado(r["token"])
    u = r.get("usuario") or {}
    _por(CH_NOME, u.get("nome", ""))
    _por(CH_ADM, "1" if u.get("admin") else "0")
    return {"ok": True, "nome": u.get("nome", ""), "email": u.get("email", "")}


# ---------------------------------------------------------------- código por e-mail

def _email_ok(email):
    e = (email or "").strip()
    return "@" in e and "." in e.split("@")[-1] and " " not in e


def pedir_codigo(email):
    """Pede o código de 6 dígitos. O servidor responde IGUAL para e-mail com e
    sem conta (anti-enumeração) — e a tela repete isso: nunca dizer "este
    e-mail não existe" nem "enviamos para a sua conta"."""
    email = (email or "").strip()
    if not _email_ok(email):
        return {"ok": False, "msg": "Digite um e-mail válido."}
    r = _chamar("/api/entrar/codigo", {"email": email})
    if r.get("offline") or not r.get("ok"):
        return {"ok": False, "offline": bool(r.get("offline")),
                "msg": r.get("msg") or "Não consegui pedir o código agora. Tente de novo."}
    return {"ok": True, "msg": MSG_CODIGO}


def entrar_com_codigo(email, codigo):
    """Troca o código pelo MESMO token do login com senha, na mesma impressão
    desta máquina — então não queima vaga a mais."""
    email = (email or "").strip()
    codigo = "".join(c for c in str(codigo or "") if c.isdigit())
    if not _email_ok(email):
        return {"ok": False, "msg": "Digite um e-mail válido."}
    if len(codigo) != 6:
        return {"ok": False, "msg": "Digite o código de 6 dígitos."}
    r = _chamar("/api/entrar/verificar", {
        "email": email, "codigo": codigo,
        "impressao": digital(), "apelido": apelido(),
        "so": platform.system(),
    })
    return _guardar_sessao(r)


# ---------------------------------------------------------------- área do aluno

def passe():
    """Link de uso único (60 s) que já entra logado na área do aluno do site.

    Devolve {ok, url} ou {ok: False, motivo, msg} com a causa certa: sem
    internet, sessão vencida, sem acesso. Quem abre o navegador é quem chama."""
    t = token()
    if not t:
        return {"ok": False, "motivo": "sem_sessao",
                "msg": "Sua sessão terminou. Saia e entre de novo para abrir as aulas."}
    r = _chamar("/api/passe", {}, bearer=t)
    if r.get("offline"):
        return {"ok": False, "motivo": "offline",
                "msg": "Sem conexão com o servidor agora. Confira a internet e tente de novo."}
    if r.get("ok") and str(r.get("url") or "").startswith("https://"):
        return {"ok": True, "url": r["url"]}
    if r.get("_status") == 401 or r.get("motivo") in ("sem_sessao", "expirou"):
        return {"ok": False, "motivo": "sem_sessao",
                "msg": "Sua sessão expirou. Saia e entre de novo para abrir as aulas."}
    if r.get("_status") == 404:
        return {"ok": False, "motivo": "indisponivel",
                "msg": "A área do aluno ainda não está disponível. Tente mais tarde."}
    return {"ok": False, "motivo": r.get("motivo") or "recusado",
            "msg": r.get("msg") or "Não consegui abrir a área do aluno agora. Tente de novo."}


def cadastrar(nome, email, senha):
    """Cria a conta como 'pendente'. Quem aprova é o Jhon, no painel de ADM.

    A resposta é deliberadamente igual para e-mail novo e e-mail já existente —
    é anti-enumeração do servidor, não bug. O texto abaixo cobre os dois casos
    sem afirmar qual aconteceu."""
    r = _chamar("/api/cadastro", {"nome": nome, "email": email, "senha": senha})
    return r


def trocar_senha(atual, nova):
    """Troca a senha da conta Tools PRO.

    ⚠️ O servidor DERRUBA as outras sessões e mantém só esta — é o certo (quem
    troca senha costuma desconfiar que alguém entrou), mas tem um efeito que
    precisa ser dito na tela: **o painel do Tools PRO dentro do Premiere vai
    pedir login de novo**, porque a sessão dele é outra. Quem não for avisado
    acha que quebrou alguma coisa."""
    t = token()
    if not t:
        return {"ok": False, "msg": "Entre na conta antes de trocar a senha."}
    if len(nova or "") < 8:
        return {"ok": False, "msg": "A senha precisa ter pelo menos 8 caracteres."}
    if nova == atual:
        return {"ok": False, "msg": "A nova senha precisa ser diferente da atual."}
    return _chamar("/api/senha", {"token": t, "atual": atual, "nova": nova})


class SemAcesso(PermissionError):
    """A sessão não vale (ou não deu para confirmar e o prazo offline passou)."""


# Confirmação recente vale por alguns minutos: as rotas que entregam valor
# conferem a sessão, mas não podem bater no servidor a cada clique.
_CACHE = {"quando": 0.0, "token": ""}
CACHE_SEG = 600


def exigir():
    """Para as rotas que entregam valor (etapas do pipeline, skills). Levanta
    SemAcesso com texto para o aluno; dentro do prazo offline, libera."""
    t = token()
    if t and _CACHE["token"] == t and time.time() - _CACHE["quando"] < CACHE_SEG:
        return True
    e = estado()
    if not e.get("entrou"):
        _CACHE["quando"], _CACHE["token"] = 0.0, ""
        raise SemAcesso(e.get("msg") or "Sua sessão do Tools PRO terminou. "
                        "Saia e entre de novo na conta para continuar.")
    _CACHE["quando"], _CACHE["token"] = time.time(), t
    return True


def sair():
    _CACHE["quando"], _CACHE["token"] = 0.0, ""
    t = token()
    if t:
        _chamar("/api/sair", {"token": t})
    _tirar(CH_TOKEN)
    _tirar(CH_NOME)
    _tirar(CH_ADM)
    _tirar(CH_VALIDADO_EM)
    _tirar(CH_VALIDADO_TOKEN)
    return {"ok": True}
