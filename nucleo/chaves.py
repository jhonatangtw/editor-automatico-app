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
import subprocess

SERVICO = "EditorAutomatico"

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
    if _keyring:
        return "keyring"
    if _MAC:
        return "chaveiro"
    if _WIN:
        return "credenciais"
    return "arquivo"


# ------------------------------------------------------------ Mac

def _mac_gravar(nome, valor):
    subprocess.run(["security", "delete-generic-password", "-s", SERVICO, "-a", nome],
                   capture_output=True)
    r = subprocess.run(
        ["security", "add-generic-password", "-s", SERVICO, "-a", nome,
         "-w", valor, "-U"], capture_output=True)
    return r.returncode == 0


def _mac_ler(nome):
    r = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICO, "-a", nome, "-w"],
        capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _mac_apagar(nome):
    subprocess.run(["security", "delete-generic-password", "-s", SERVICO, "-a", nome],
                   capture_output=True)


# ------------------------------------------------------------ Windows

def _ps(script):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
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
    if _keyring:
        try:
            _keyring.set_password(SERVICO, servico, valor)
            return True
        except Exception:
            pass
    if _MAC and _mac_gravar(servico, valor):
        return True
    if _WIN and _win_gravar(servico, valor):
        return True
    _reserva_gravar(servico, valor)
    return True


def ler(servico):
    if _keyring:
        try:
            v = _keyring.get_password(SERVICO, servico)
            if v:
                return v
        except Exception:
            pass
    if _MAC:
        v = _mac_ler(servico)
        if v:
            return v
    if _WIN:
        v = _win_ler(servico)
        if v:
            return v
    return _reserva_ler(servico)


def apagar(servico):
    if _keyring:
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
