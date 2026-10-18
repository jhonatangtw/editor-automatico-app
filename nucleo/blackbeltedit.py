"""
BlackBeltEdit — o editor de vídeo próprio da Editor Black Belt (beta).

O Editor Automático não edita: ele conduz o pipeline e manda o Premiere montar.
O BlackBeltEdit é a interface de edição nossa (timeline, monitores, Tools PRO
nativo, assistente de IA) e roda sem o Premiere. Aqui só se ACHA e se ABRE o
app — ele é um programa à parte, com instalador próprio.

Por enquanto só existe para Mac (Apple Silicon). No Windows a tela diz isso em
vez de oferecer um botão que não faz nada.
"""

import os
import plistlib
import subprocess

from . import so

NOME_APP = "BlackBeltEdit.app"


def _lugares():
    casa = os.path.expanduser("~")
    return [os.path.join("/Applications", NOME_APP),
            os.path.join(casa, "Applications", NOME_APP)]


def localizar():
    """O caminho do .app instalado, ou None."""
    if not so.MAC:
        return None
    for p in _lugares():
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, "Contents", "Info.plist")):
            return p
    return None


def _versao(app):
    try:
        with open(os.path.join(app, "Contents", "Info.plist"), "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString") or ""
    except (OSError, plistlib.InvalidFileException, ValueError):
        return ""


def estado():
    app = localizar()
    return {
        "suportado": so.MAC,
        "instalado": bool(app),
        "caminho": app or "",
        "versao": _versao(app) if app else "",
        "beta": True,
    }


def abrir(arquivo=None):
    """Abre o BlackBeltEdit (opcionalmente com um projeto .fcproj ou mídia).
    Devolve {ok, msg}. Nunca levanta: a tela mostra a mensagem."""
    if not so.MAC:
        return {"ok": False, "msg": "O BlackBeltEdit (beta) ainda é só para Mac."}
    app = localizar()
    if not app:
        return {"ok": False, "msg": "O BlackBeltEdit não está instalado neste Mac. "
                                    "Arraste o BlackBeltEdit para a pasta Aplicativos e tente de novo."}
    cmd = ["open", "-a", app]
    if arquivo:
        if not os.path.exists(arquivo):
            return {"ok": False, "msg": "Arquivo não encontrado: " + arquivo}
        cmd.append(arquivo)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "msg": "Não consegui abrir o BlackBeltEdit: %s" % e}
    if r.returncode != 0:
        return {"ok": False, "msg": "Não consegui abrir o BlackBeltEdit: %s" % (r.stderr.strip() or r.returncode)}
    return {"ok": True, "msg": "Abrindo o BlackBeltEdit…"}
