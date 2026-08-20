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

import json
import os
import platform
import random
import string
import urllib.error
import urllib.request

SERVIDOR = "https://editor-black-belt-licenca.jhonatangtw.workers.dev"

PASTA = os.path.expanduser("~/.editorblackbelt")
ARQUIVO = os.path.join(PASTA, "sessao.json")

# as mesmas chaves que o painel CEP escreve — nomes diferentes quebrariam a divisão
CH_TOKEN = "bb_acesso_token"
CH_NOME = "bb_acesso_nome"
CH_ADM = "bb_acesso_adm"
CH_DIGITAL = "bb_digital"


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


def _chamar(rota, dados):
    corpo = json.dumps(dados or {}).encode("utf-8")
    req = urllib.request.Request(
        SERVIDOR + rota, data=corpo, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": _UA,
                 "Accept": "application/json"})
    try:
        from . import rede
        with urllib.request.urlopen(req, timeout=20, context=rede.contexto()) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # o Worker devolve JSON também nos 4xx — a mensagem dele é melhor que a minha
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "msg": "O servidor respondeu de forma inesperada."}
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

def estado():
    """Quem está logado agora. Não cria máquina — só revalida."""
    t = token()
    if not t:
        return {"entrou": False, "motivo": "sem_token"}

    r = _chamar("/api/sessao", {"token": t})

    # Internet caindo não pode virar reembolso: com token na mão, libera.
    # Só tranca quando o servidor responde explicitamente que não vale.
    if r.get("offline"):
        d = _ler()
        return {"entrou": True, "offline": True,
                "nome": d.get(CH_NOME, ""), "adm": d.get(CH_ADM) == "1"}

    if not r.get("ok"):
        if r.get("motivo") in ("sem_sessao", "expirou", "sem_conta"):
            _tirar(CH_TOKEN)
        return {"entrou": False, "motivo": r.get("motivo", "recusado"),
                "msg": r.get("msg", "")}

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
    if not r.get("ok"):
        return r
    _por(CH_TOKEN, r["token"])
    u = r.get("usuario") or {}
    _por(CH_NOME, u.get("nome", ""))
    _por(CH_ADM, "1" if u.get("admin") else "0")
    return {"ok": True, "nome": u.get("nome", ""), "email": u.get("email", "")}


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


def sair():
    t = token()
    if t:
        _chamar("/api/sair", {"token": t})
    _tirar(CH_TOKEN)
    _tirar(CH_NOME)
    _tirar(CH_ADM)
    return {"ok": True}
