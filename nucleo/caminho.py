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
