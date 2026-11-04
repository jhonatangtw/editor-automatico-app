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
import platform
import plistlib
import shutil
import subprocess
import tempfile
import urllib.request

from . import rede, so

NOME_APP = "BlackBeltEdit.app"

# Release própria, FORA da "latest": a atualização do Editor Automático lê a
# latest, e um instalador de outro app ali quebraria o auto-update de todos.
URL_DMG = ("https://github.com/jhonatangtw/editor-automatico-app/releases/download/"
           "blackbeltedit-beta/BlackBeltEdit.dmg")
# O .dmg tem ~35 MB; menos que isso é página de erro, não instalador.
TAMANHO_MINIMO = 5 * 1024 * 1024


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


MSG_SO_APPLE = "Por enquanto só para Mac com chip Apple."


def chip_apple():
    """O app é só arm64. `platform.machine()` como no `atualizacao._qual_asset`;
    sob Rosetta ele diz x86_64 num Mac com chip Apple, então o sysctl confirma."""
    if not so.MAC:
        return False
    if platform.machine() == "arm64":
        return True
    try:
        r = subprocess.run(["sysctl", "-n", "hw.optional.arm64"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() == "1"
    except (OSError, subprocess.TimeoutExpired):
        return False


def estado():
    app = localizar()
    ok = chip_apple()
    return {
        "suportado": ok,
        "msg": "" if ok else MSG_SO_APPLE,
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


def _rodando():
    r = subprocess.run(["pgrep", "-f", NOME_APP + "/Contents/MacOS/"], capture_output=True, text=True)
    return r.returncode == 0


def _rodar(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError("%s: %s" % (cmd[0], (r.stderr or r.stdout).strip()[-300:]))
    return r.stdout


def instalar(url=URL_DMG, destino=None):
    """Baixa o instalador e põe o app em Aplicativos.

    Baixado pelo Python, o .dmg não ganha a marca de quarentena — é isso que
    evita o "não é possível abrir" do macOS num app sem notarização, que pelo
    navegador travaria o aluno. Devolve {ok, msg}; nunca levanta."""
    if not chip_apple():
        return {"ok": False, "msg": MSG_SO_APPLE}
    if destino is None and _rodando():
        return {"ok": False, "msg": "Feche o BlackBeltEdit antes de instalar a versão nova."}
    tmp = tempfile.mkdtemp(prefix="blackbeltedit-")
    dmg = os.path.join(tmp, "BlackBeltEdit.dmg")
    ponto = os.path.join(tmp, "montado")
    os.makedirs(ponto)
    dest = destino or os.path.join("/Applications", NOME_APP)
    if destino is None and not os.access("/Applications", os.W_OK):
        dest = os.path.join(os.path.expanduser("~/Applications"), NOME_APP)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
    novo = os.path.join(os.path.dirname(dest), ".BlackBeltEdit-novo.app")
    montado = False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EditorAutomatico"})
        with urllib.request.urlopen(req, timeout=120, context=rede.contexto()) as r, open(dmg, "wb") as f:
            shutil.copyfileobj(r, f)
        if os.path.getsize(dmg) < TAMANHO_MINIMO:
            return {"ok": False, "msg": "O download veio incompleto. Tente de novo."}
        _rodar(["hdiutil", "attach", "-nobrowse", "-readonly", "-noverify", "-mountpoint", ponto, dmg])
        montado = True
        apps = [n for n in os.listdir(ponto) if n.endswith(".app")]
        if not apps:
            return {"ok": False, "msg": "O instalador não tem o app dentro."}
        shutil.rmtree(novo, ignore_errors=True)
        _rodar(["ditto", os.path.join(ponto, apps[0]), novo])
        # quarentena e os atributos que o macOS cola na cópia ("detritus"): sem
        # limpar, a conferência estrita da assinatura recusa o app inteiro
        subprocess.run(["xattr", "-cr", novo], capture_output=True)
        _rodar(["codesign", "--verify", "--deep", "--strict", novo], timeout=180)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.rename(novo, dest)
        return {"ok": True, "msg": "BlackBeltEdit instalado (versão %s)." % (_versao(dest) or "?"), "caminho": dest}
    except Exception as e:     # rede, disco, assinatura: a tela mostra
        shutil.rmtree(novo, ignore_errors=True)
        return {"ok": False, "msg": "Não consegui instalar o BlackBeltEdit: %s" % e}
    finally:
        if montado:
            subprocess.run(["hdiutil", "detach", ponto, "-quiet", "-force"], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
