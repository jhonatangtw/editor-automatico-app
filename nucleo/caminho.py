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

⚠️ **O PATH não pode ser uma foto do arranque.** Ele era montado uma vez, com
uma trava (`_pronto`), e a montagem DESCARTA pasta que ainda não existe. Então
tudo que fosse instalado com o app aberto — o Homebrew, o Whisper em
`~/Library/Python/3.x/bin`, um CLI de npm — continuava invisível para o
`which` até o app ser fechado e aberto de novo. Era essa a razão real de
"instalei e a tela não mudou": não era a tela, era o processo procurando num
PATH velho. Por isso existe `recarregar()`, e por isso `conferir()` chama.
"""

import os
import subprocess
import sys
import threading

CONHECIDOS = [
    "~/.editorblackbelt/bin",                      # o que o próprio app instala
    "/opt/homebrew/bin", "/opt/homebrew/sbin",     # Apple Silicon
    "/usr/local/bin", "/usr/local/sbin",           # Intel
    "~/.local/bin",                                # claude, heygen
    "~/.npm-global/bin", "~/.nvm/versions/node",   # higgsfield
    "~/.bun/bin", "~/.cargo/bin", "~/go/bin",
    "/usr/bin", "/bin", "/usr/sbin", "/sbin",
]

# O Whisper vai para a pasta da VERSÃO do Python, e a versão muda de máquina em
# máquina — listar 3.9/3.11/3.12/3.13 na mão só adia o dia em que a 3.14 sai e
# o app diz "não instalado" para um Whisper que está lá.
def _pythons_do_usuario():
    base = os.path.expanduser("~/Library/Python")
    try:
        return sorted((os.path.join(base, n, "bin") for n in os.listdir(base)),
                      reverse=True)
    except OSError:
        return []


_pronto = False
# O servidor é multi-thread: duas telas podem reconferir ao mesmo tempo, e
# `os.environ["PATH"] = ...` é ler-alterar-gravar. Sem trava, uma escrita some
# no meio da outra e o PATH volta a ficar sem a pasta nova — o bug de origem
# reaparecendo de vez em quando, que é a versão pior dele.
_trava = threading.Lock()


def _extras_windows():
    """Os cantos onde o npm e o pip do Windows põem executável de usuário.

    Separado de `_windows()` porque o `recarregar()` barato precisa da MESMA
    lista: é aqui que o winget deixa o ffmpeg, e sem reconferir esta pasta o
    app instala e continua dizendo que não achou."""
    if not sys.platform.startswith("win"):
        return []
    ap = os.environ.get("APPDATA") or ""
    la = os.environ.get("LOCALAPPDATA") or ""
    extras = [os.path.expanduser(r"~\.editorblackbelt\bin"),
              os.path.join(ap, "npm"),
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
    return extras


def _windows():
    """No Windows não existe o problema que este módulo resolve: processo aberto
    pelo Explorer HERDA o PATH do usuário. Só garantimos os extras."""
    atual = [x for x in (os.environ.get("PATH") or "").split(os.pathsep) if x]
    for d in _extras_windows():
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


def _montar(com_shell):
    """Monta o PATH do zero. `com_shell` é o caro (abre um shell de login)."""
    if sys.platform.startswith("win"):
        return _windows()

    atual = [x for x in (os.environ.get("PATH") or "").split(":") if x]
    conhecidos = [os.path.expanduser(x) for x in CONHECIDOS] + _pythons_do_usuario()
    fontes = ([_do_shell()] if com_shell else []) + [conhecidos, atual]
    partes = []
    for lista in fontes:
        for d in lista:
            if d and d not in partes and os.path.isdir(d):
                partes.append(d)

    os.environ["PATH"] = ":".join(partes)
    return os.environ["PATH"]


def ajustar():
    """Chame o mais cedo possível — antes de qualquer `which`. Só na primeira
    vez ela paga o shell de login; depois use `recarregar()`."""
    global _pronto
    with _trava:
        if _pronto:
            return os.environ["PATH"]
        _pronto = True
        return _montar(com_shell=True)


def recarregar(com_shell=False):
    """Reconfere o PATH contra o disco de AGORA e diz se ele mudou.

    Chamada a cada `conferir()` da tela de Ambiente. O modo barato não abre
    processo nenhum — só relê a lista de lugares conhecidos, que é onde caem o
    Homebrew, o npm global e o Whisper, e ACRESCENTA o que passou a existir. É
    esse modo que faz uma dependência recém-instalada aparecer sem fechar o app.

    ⚠️ **Barato ACRESCENTA, não remonta.** Remontar reordenaria o PATH — o
    shell de login vinha na frente e passaria para trás dos lugares conhecidos —
    e mudar a ordem muda QUAL binário ganha quando existem dois. Um app que
    troca de `ffmpeg` sozinho no meio do expediente é pior que o bug original.

    `com_shell=True` volta a perguntar ao shell de login e remonta na ordem
    certa: custa ~1s e é para quando o usuário pede "Atualizar status" na mão,
    ou logo depois de uma instalação, quando o perfil do shell pode ter ganhado
    uma linha nova."""
    global _pronto
    with _trava:
        antes = _dirs()
        _pronto = True
        if com_shell:
            _montar(com_shell=True)
        else:
            atual = _dirs()
            for d in ([os.path.expanduser(x) for x in CONHECIDOS]
                      + _pythons_do_usuario() + _extras_windows()):
                if d and d not in atual and os.path.isdir(d):
                    atual.append(d)
            os.environ["PATH"] = os.pathsep.join(atual)
        depois = _dirs()
        mudou = set(antes) != set(depois)
        if mudou:
            _esquecer_which()
        return {"mudou": mudou, "path": os.environ.get("PATH", ""),
                "novos": [d for d in depois if d not in antes]}


def _dirs():
    return [x for x in (os.environ.get("PATH") or "").split(os.pathsep) if x]


def _esquecer_which():
    """O `which` pode ter memória, e memória de PATH velho é o bug de novo."""
    from shutil import which
    if hasattr(which, "cache_clear"):
        which.cache_clear()


def diagnostico():
    """O que a tela de Ambiente mostra quando algo não é encontrado."""
    from shutil import which
    return {"path": os.environ.get("PATH", ""),
            "achados": {b: which(b) for b in
                        ("claude", "heygen", "higgsfield", "ffmpeg", "ffprobe",
                         "whisper", "ant", "brew", "npm")}}
