"""
Mac: a versão nova entra em Aplicativos SEM o aluno arrastar nada.

Antes o app baixava o .dmg, abria e pedia "arraste para Aplicativos". Metade da
turma arrastava para a área de trabalho, abria direto do .dmg ou deixava em
Downloads — e o macOS roda app fora de Aplicativos TRANSLOCADO (uma cópia
somente leitura em /private/var/.../AppTranslocation), onde ele se perde.

O cuidado que fazia a troca ser do usuário continua valendo: NUNCA mexer no
.app que está rodando. Por isso a troca é em duas metades:

  1. com o app aberto: monta o .dmg escondido, copia o .app novo para uma pasta
     oculta AO LADO do destino (mesmo disco = `mv` atômico), tira a quarentena
     e confere a assinatura. Qualquer falha aqui não tocou em nada;
  2. um script à parte espera ESTE processo sair, põe o antigo de lado, move o
     novo para o lugar, apaga o antigo e reabre. Se o `mv` falhar, devolve o
     antigo — o aluno nunca fica sem app.

O mesmo caminho serve para "mover para Aplicativos" um app aberto de outro lugar.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from . import so

NOME = "Editor Automático.app"
PASTAS = ("/Applications", os.path.expanduser("~/Applications"))


def bundle_atual():
    """O .app em execução, ou None em desenvolvimento (rodando pelo Python)."""
    exe = sys.executable
    if ".app/Contents/MacOS/" not in exe:
        return None
    return exe.split(".app/Contents/MacOS/")[0] + ".app"


def em_aplicativos(caminho):
    return (caminho is not None and "/AppTranslocation/" not in caminho
            and os.path.dirname(caminho) in PASTAS)


def local():
    """Onde o app está e se precisa ir para Aplicativos. Nunca levanta."""
    b = bundle_atual()
    if not so.MAC or not b:
        return {"mac": so.MAC, "fora": False}
    return {"mac": True, "caminho": b, "fora": not em_aplicativos(b),
            "translocado": "/AppTranslocation/" in b, "no_dmg": b.startswith("/Volumes/")}


def destino():
    """Onde a versão nova deve ficar: onde este app já está, se for Aplicativos;
    senão onde já existir uma cópia; senão /Applications (ou ~/Applications,
    quando /Applications não aceita escrita sem senha)."""
    b = bundle_atual()
    if em_aplicativos(b) and os.access(os.path.dirname(b), os.W_OK):
        return b
    for p in PASTAS:
        alvo = os.path.join(p, NOME)
        if os.path.exists(alvo) and os.access(p, os.W_OK):
            return alvo
    if os.access("/Applications", os.W_OK):
        return os.path.join("/Applications", NOME)
    os.makedirs(PASTAS[1], exist_ok=True)
    return os.path.join(PASTAS[1], NOME)


def _rodar(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError("%s: %s" % (cmd[0], (r.stderr or r.stdout).strip()[-300:]))
    return r.stdout


def preparar(origem_app, dest, diz=None):
    """Copia `origem_app` para uma pasta oculta ao lado de `dest`, pronto para
    a troca. Devolve o caminho preparado. Não toca no destino."""
    diz = diz or (lambda _: None)
    novo = os.path.join(os.path.dirname(dest), ".EditorAutomatico-novo.app")
    shutil.rmtree(novo, ignore_errors=True)
    diz("copiando para %s…" % os.path.dirname(dest))
    _rodar(["ditto", origem_app, novo])
    subprocess.run(["xattr", "-dr", "com.apple.quarantine", novo], capture_output=True)
    try:
        _rodar(["codesign", "--verify", "--strict", novo], timeout=120)
    except Exception:
        shutil.rmtree(novo, ignore_errors=True)
        raise RuntimeError("a cópia nova não passou na conferência de assinatura")
    if not os.path.isfile(os.path.join(novo, "Contents", "MacOS", "EditorAutomatico")):
        shutil.rmtree(novo, ignore_errors=True)
        raise RuntimeError("a cópia nova veio sem o executável")
    return novo


def preparar_do_dmg(dmg, diz=None):
    """Monta o .dmg sem aparecer no Finder, prepara o .app dele e desmonta."""
    diz = diz or (lambda _: None)
    dest = destino()
    ponto = tempfile.mkdtemp(prefix="editorautomatico-dmg-")
    diz("abrindo o instalador…")
    _rodar(["hdiutil", "attach", "-nobrowse", "-readonly", "-noverify",
            "-mountpoint", ponto, dmg])
    try:
        app = os.path.join(ponto, NOME)
        if not os.path.isdir(app):
            achados = [n for n in os.listdir(ponto) if n.endswith(".app")]
            if not achados:
                raise RuntimeError("o .dmg não tem o app dentro")
            app = os.path.join(ponto, achados[0])
        return preparar(app, dest, diz), dest
    finally:
        subprocess.run(["hdiutil", "detach", ponto, "-quiet", "-force"], capture_output=True)
        shutil.rmtree(ponto, ignore_errors=True)


# O script vive FORA do app: ele roda depois que este processo morre.
TROCA = r'''#!/bin/bash
PID="$1"; NOVO="$2"; DEST="$3"; APAGAR="$4"
for i in $(seq 1 100); do kill -0 "$PID" 2>/dev/null || break; sleep 0.3; done
VELHO="$DEST.velho-$$"
[ -e "$DEST" ] && mv "$DEST" "$VELHO"
if mv "$NOVO" "$DEST"; then
  rm -rf "$VELHO"
  [ -n "$APAGAR" ] && [ "$APAGAR" != "$DEST" ] && rm -rf "$APAGAR"
else
  [ -e "$VELHO" ] && mv "$VELHO" "$DEST"
fi
open "$DEST"
rm -f "$0"
'''


def trocar_e_reabrir(novo, dest, apagar_origem=None):
    """Dispara o script de troca e fecha o app em ~1,5 s (dá tempo de a tela
    receber a resposta)."""
    fd, script = tempfile.mkstemp(prefix="editorautomatico-troca-", suffix=".sh")
    with os.fdopen(fd, "w") as f:
        f.write(TROCA)
    os.chmod(script, 0o700)
    subprocess.Popen(["/bin/bash", script, str(os.getpid()), novo, dest, apagar_origem or ""],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)

    def sair():
        time.sleep(1.5)
        os._exit(0)

    threading.Thread(target=sair, daemon=True).start()


def mover_para_aplicativos(diz=None):
    """Leva o app que está aberto (Downloads, Mesa, .dmg) para Aplicativos e
    reabre de lá. A cópia de origem é apagada quando dá — translocada ou dentro
    do .dmg não é nossa para apagar."""
    info = local()
    if not info.get("fora"):
        return {"ok": True, "nada": True, "msg": "O app já está em Aplicativos."}
    dest = destino()
    novo = preparar(info["caminho"], dest, diz)
    apagar = None if (info["translocado"] or info["no_dmg"]) else info["caminho"]
    trocar_e_reabrir(novo, dest, apagar)
    return {"ok": True, "destino": dest,
            "msg": "Movido para %s. Reabrindo de lá…" % os.path.dirname(dest)}
