"""
Reconstruir o PATH — sem isto o app não acha NENHUM CLI.

Um `.app` aberto pelo Finder não herda o PATH do shell. Ele recebe o mínimo
(`/usr/bin:/bin:/usr/sbin:/sbin`), e é só. Todo CLI que o app precisa mora fora
disso:

    claude, heygen   ~/.local/bin
    higgsfield       ~/.npm-global/bin
    ffmpeg           /opt/homebrew/bin
    whisper          ~/Library/Python/3.x/bin

O sintoma é cruel porque mente: a tela de Contas diz "não está instalado" para
programas que estão instalados e funcionando. E some em qualquer teste feito por
terminal — de onde o PATH vem completo. Foi assim que passou batido.

Duas fontes, nesta ordem:
  1. O shell de login do usuário, que sabe o PATH REAL dele (inclui coisas que
     eu não teria como adivinhar: asdf, pyenv, volta, nix...).
  2. Uma lista de lugares conhecidos, para quando o shell não responder.
"""

import os
import subprocess
import sys

CONHECIDOS = [
    "/opt/homebrew/bin", "/opt/homebrew/sbin",     # Apple Silicon
    "/usr/local/bin", "/usr/local/sbin",           # Intel
    "~/.local/bin",                                # claude, heygen
    "~/.npm-global/bin", "~/.nvm/versions/node",   # higgsfield
    "~/.bun/bin", "~/.cargo/bin", "~/go/bin",
    "~/Library/Python/3.9/bin", "~/Library/Python/3.11/bin",
    "~/Library/Python/3.12/bin", "~/Library/Python/3.13/bin",
    "/usr/bin", "/bin", "/usr/sbin", "/sbin",
]

_pronto = False


def _windows():
    """No Windows não existe o problema que este módulo resolve: processo aberto
    pelo Explorer HERDA o PATH do usuário. Só garantimos os cantos onde o npm e
    o pip põem executável de usuário, que nem sempre estão no PATH da sessão."""
    ap = os.environ.get("APPDATA") or ""
    la = os.environ.get("LOCALAPPDATA") or ""
    extras = [os.path.join(ap, "npm"),
              # é aqui que o winget deixa o ffmpeg — sem esta pasta o app
              # instala e continua dizendo que não achou
              os.path.join(la, "Microsoft", "WinGet", "Links"),
              os.path.join(la, "Microsoft", "WindowsApps"),
              os.path.expanduser(r"~\.local\bin")]
    # o Python de usuário muda de pasta a cada versão; varre as que existirem
    base = os.path.join(la, "Programs", "Python")
    try:
        for n in sorted(os.listdir(base), reverse=True):
            extras.append(os.path.join(base, n, "Scripts"))
    except Exception:
        pass
    atual = [x for x in (os.environ.get("PATH") or "").split(os.pathsep) if x]
    for d in extras:
        if os.path.isdir(d) and d not in atual:
            atual.append(d)
    os.environ["PATH"] = os.pathsep.join(atual)
    return os.environ["PATH"]


def _do_shell():
    """Pergunta ao shell de login qual é o PATH de verdade.

    `-l` carrega o perfil (é lá que o usuário põe as coisas). Silenciamos a
    saída de erro porque perfil de gente real imprime banner, e banner no meio
    da resposta estragaria o PATH."""
    shell = os.environ.get("SHELL") or "/bin/zsh"
    try:
        r = subprocess.run([shell, "-lc", "printf %s \"$PATH\""],
                           capture_output=True, text=True, timeout=12)
        p = (r.stdout or "").strip()
        # o perfil pode ter imprimido coisa antes; fica só com a última linha
        p = p.splitlines()[-1] if p else ""
        return [x for x in p.split(":") if x.startswith("/")]
    except Exception:
        return []


def ajustar():
    """Chame UMA vez, o mais cedo possível — antes de qualquer `which`."""
    global _pronto
    if _pronto:
        return os.environ["PATH"]
    if sys.platform.startswith("win"):
        _pronto = True
        return _windows()

    atual = [x for x in (os.environ.get("PATH") or "").split(":") if x]
    partes = []
    for lista in (_do_shell(), [os.path.expanduser(x) for x in CONHECIDOS], atual):
        for d in lista:
            if d and d not in partes and os.path.isdir(d):
                partes.append(d)

    os.environ["PATH"] = ":".join(partes)
    _pronto = True
    return os.environ["PATH"]


def diagnostico():
    """O que a tela de Ambiente mostra quando algo não é encontrado."""
    from shutil import which
    return {"path": os.environ.get("PATH", ""),
            "achados": {b: which(b) for b in
                        ("claude", "heygen", "higgsfield", "ffmpeg", "ffprobe",
                         "whisper", "ant", "brew", "npm")}}
