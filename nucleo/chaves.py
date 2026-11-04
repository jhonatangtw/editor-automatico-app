"""
Onde as chaves dos serviços ficam guardadas.

Decisão do produto: **cada pessoa usa a própria conta**. Nenhuma chave passa
pelo nosso servidor, nenhuma sai desta máquina. O app só guarda e usa.

Guardar em .env de texto puro seria o mais fácil e o mais errado: um arquivo
desses vai junto quando o aluno manda a pasta do projeto pro editor, e aí a
chave da ElevenLabs dele está no Drive de outra pessoa. Então vai no cofre do
sistema operacional — Chaveiro no Mac, Gerenciador de Credenciais no Windows.

A ordem de tentativa existe porque nenhuma das opções está garantida numa
máquina de aluno:
  1. keyring   — se estiver instalado, resolve nos dois sistemas
  2. security  — CLI nativa do Mac, sempre existe lá
  3. PowerShell + DPAPI — nativo do Windows, cifra por usuário
  4. arquivo 0600 — último recurso, e o app AVISA na tela que está aqui
"""

import base64
import json
import os
import platform


def _so():
    """import tardio: chaves.py é carregado muito cedo no arranque."""
    from . import so
    return so

import subprocess

SERVICO = "EditorAutomatico"

# No Mac as chaves vão pelo /usr/bin/security, num serviço PRÓPRIO dele.
# ⚠️ O app é assinado ad hoc: o Chaveiro amarra o "Permitir Sempre" à impressão
# exata do binário, que muda a cada versão — com o keyring (que chama o cofre de
# dentro do app) o Mac pedia a senha de novo a cada atualização, uma vez por
# chave. O `security` é da Apple, a assinatura dele não muda, e ele não pede nada
# para ler item que ele mesmo criou. O serviço é outro nome para não colidir com
# os itens antigos do keyring, que são migrados uma vez (ver ler()).
SERVICO_MAC = "EditorAutomatico.cofre"
_SECURITY = "/usr/bin/security"

# Leitura guardada em memória: a aba Contas reconfere a cada 15 s.
_cache = {}

SERVICOS = ["elevenlabs", "higgsfield", "heygen", "minimax"]

_RESERVA = os.path.expanduser("~/.editorblackbelt/chaves.json")

_MAC = platform.system() == "Darwin"
_WIN = platform.system() == "Windows"

try:
    import keyring as _keyring
except Exception:
    _keyring = None


def cofre():
    """Qual cofre está em uso — a UI mostra isso, porque o 'arquivo' merece aviso."""
    if _MAC:
        return "chaveiro"
    if _keyring:
        return "keyring"
    if _WIN:
        return "credenciais"
    return "arquivo"


# ------------------------------------------------------------ Mac

def _mac_gravar(nome, valor):
    subprocess.run([_SECURITY, "delete-generic-password", "-s", SERVICO_MAC, "-a", nome],
                   capture_output=True)
    r = subprocess.run(
        [_SECURITY, "add-generic-password", "-s", SERVICO_MAC, "-a", nome,
         "-w", valor, "-U"], capture_output=True)
    return r.returncode == 0


def _mac_ler(nome):
    r = subprocess.run(
        [_SECURITY, "find-generic-password", "-s", SERVICO_MAC, "-a", nome, "-w"],
        capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _mac_apagar(nome):
    subprocess.run([_SECURITY, "delete-generic-password", "-s", SERVICO_MAC, "-a", nome],
                   capture_output=True)


def _mac_antigo(nome):
    """Item gravado pelo keyring nas versões até a 0.24.1. Consultado UMA vez por
    chave (a marca fica em _MIGRADAS): ler esse item é o que dispara o aviso do
    Chaveiro, e quem não tem chave antiga levaria o aviso a cada abertura."""
    feitas = _reserva_todas().get("_migradas_mac", [])
    if nome in feitas:
        return ""
    v = ""
    if _keyring:
        try:
            v = _keyring.get_password(SERVICO, nome) or ""
        except Exception:
            v = ""
    if v and _mac_gravar(nome, v):
        try:
            _keyring.delete_password(SERVICO, nome)
        except Exception:
            pass
    if not v or _mac_ler(nome):
        _reserva_gravar("_migradas_mac", sorted(set(feitas) | {nome}))
    return v


# ------------------------------------------------------------ Windows

def _ps(script):
    r = _so().run(["powershell", "-NoProfile", "-Command", script],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _win_gravar(nome, valor):
    b64 = base64.b64encode(valor.encode("utf-8")).decode("ascii")
    saida = _ps(
        "Add-Type -AssemblyName System.Security;"
        "$b=[Convert]::FromBase64String('%s');"
        "$c=[Security.Cryptography.ProtectedData]::Protect($b,$null,'CurrentUser');"
        "[Convert]::ToBase64String($c)" % b64)
    if not saida:
        return False
    _reserva_gravar(nome, "dpapi:" + saida)
    return True


def _win_ler(nome):
    bruto = _reserva_ler(nome)
    if not bruto.startswith("dpapi:"):
        return bruto
    saida = _ps(
        "Add-Type -AssemblyName System.Security;"
        "$c=[Convert]::FromBase64String('%s');"
        "$b=[Security.Cryptography.ProtectedData]::Unprotect($c,$null,'CurrentUser');"
        "[Text.Encoding]::UTF8.GetString($b)" % bruto[6:])
    return saida


# ------------------------------------------------------------ reserva

def _reserva_todas():
    try:
        with open(_RESERVA, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _reserva_gravar(nome, valor):
    d = _reserva_todas()
    d[nome] = valor
    os.makedirs(os.path.dirname(_RESERVA), exist_ok=True)
    tmp = _RESERVA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.chmod(tmp, 0o600)          # antes do replace: nunca existe legível por outros
    os.replace(tmp, _RESERVA)


def _reserva_ler(nome):
    return _reserva_todas().get(nome, "")


def _reserva_apagar(nome):
    d = _reserva_todas()
    if d.pop(nome, None) is not None:
        tmp = _RESERVA + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, _RESERVA)


# ------------------------------------------------------------ API

def gravar(servico, valor):
    valor = (valor or "").strip()
    if not valor:
        apagar(servico)
        return True
    _cache.pop(servico, None)
    if _MAC and _mac_gravar(servico, valor):
        _cache[servico] = valor
        return True
    if _keyring and not _MAC:
        try:
            _keyring.set_password(SERVICO, servico, valor)
            return True
        except Exception:
            pass
    if _WIN and _win_gravar(servico, valor):
        return True
    _reserva_gravar(servico, valor)
    return True


def ler(servico):
    if servico in _cache:
        return _cache[servico]
    v = _ler(servico)
    _cache[servico] = v
    return v


def _ler(servico):
    if _MAC:
        v = _mac_ler(servico) or _mac_antigo(servico)
        if v:
            return v
        return _reserva_ler(servico)
    if _keyring:
        try:
            v = _keyring.get_password(SERVICO, servico)
            if v:
                return v
        except Exception:
            pass
    if _WIN:
        v = _win_ler(servico)
        if v:
            return v
    return _reserva_ler(servico)


def apagar(servico):
    _cache.pop(servico, None)
    if _keyring and not _MAC:
        try:
            _keyring.delete_password(SERVICO, servico)
        except Exception:
            pass
    if _MAC:
        _mac_apagar(servico)
    _reserva_apagar(servico)


def resumo():
    """O que a tela de Contas mostra. Nunca devolve a chave — só se existe e o
    fim dela, o bastante pra pessoa reconhecer qual conta está ali."""
    saida = {}
    for s in SERVICOS:
        v = ler(s)
        saida[s] = {"tem": bool(v), "fim": ("…" + v[-4:]) if len(v) >= 4 else ""}
    return saida
