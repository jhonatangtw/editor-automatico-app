"""
As diferenças entre Mac e Windows, num lugar só.

O app nasceu no Mac e cada pedaço aprendeu o Mac por conta: `pgrep` para achar
o Premiere, `osascript` para abrir Terminal, `brew` para instalar, `/Applications`
para procurar programa. Espalhado assim, portar viraria caça a `if` escondido —
e o pior tipo de bug de porte é o que só aparece na máquina do aluno.

Regras:

  * **`run`/`popen` resolvem o argv[0] antes de chamar.** No Windows, CLI de npm
    é um `.cmd` — `["higgsfield", ...]` levanta FileNotFoundError enquanto
    `higgsfield.cmd` na mão funciona. `shutil.which` acha o `.cmd` (PATHEXT), e
    passar o caminho resolvido é o que faz o mesmo código servir nos dois.

  * **Nada aqui levanta por sistema desconhecido.** Linux não é alvo, mas cair
    num `KeyError` seria pior do que degradar.
"""

import os
import platform
import shutil
import subprocess

SISTEMA = platform.system()
MAC = SISTEMA == "Darwin"
WIN = SISTEMA == "Windows"

# Onde o Adobe guarda as extensões CEP — é a casa do plugin do Premiere.
# ⚠️ `os.path.expandvars` NÃO expande `%VAR%` fora do Windows (o posixpath só
# entende `$VAR`), então um teste no Mac veria o literal `%APPDATA%` e passaria
# mentindo. `os.environ` funciona igual nos dois.
def _appdata():
    return (os.environ.get("APPDATA")
            or os.path.expanduser(r"~\AppData\Roaming"))


CEP = (os.path.join(_appdata(), "Adobe", "CEP", "extensions") if WIN
       else os.path.expanduser("~/Library/Application Support/Adobe/CEP/extensions"))

# O gerenciador de pacotes de cada casa. `winget` vem no Windows 10/11.
GERENCIADOR = "winget" if WIN else "brew"


def onde(binario):
    """`which` que enxerga `.cmd`/`.bat` no Windows."""
    return shutil.which(binario)


def resolver(cmd):
    """Troca o argv[0] pelo caminho real. Lista igual se não achar — a mensagem
    de erro do sistema é melhor do que uma minha inventada."""
    if not cmd or not isinstance(cmd, (list, tuple)):
        return cmd
    achado = onde(cmd[0])
    return [achado] + list(cmd[1:]) if achado else list(cmd)


def run(cmd, **kw):
    return subprocess.run(resolver(cmd), **kw)


def popen(cmd, **kw):
    return subprocess.Popen(resolver(cmd), **kw)


def abrir(caminho):
    """Abre arquivo ou pasta no programa padrão do sistema."""
    try:
        if WIN:
            os.startfile(caminho)          # noqa: S606 — é a API do Windows
            return True
        return subprocess.run(["open" if MAC else "xdg-open", caminho],
                              capture_output=True).returncode == 0
    except Exception:
        return False


def processos(padrao):
    """Existe processo cujo nome/linha casa com o padrão?

    Mac tem `pgrep -f`; Windows não. `tasklist` lista o executável, então o
    padrão do Windows é o NOME do .exe, não a linha de comando inteira."""
    try:
        if WIN:
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq %s" % padrao],
                               capture_output=True, text=True, timeout=10)
            return padrao.lower() in (r.stdout or "").lower()
        r = subprocess.run(["pgrep", "-f", padrao], capture_output=True,
                           text=True, timeout=8)
        return bool([l for l in r.stdout.split() if l])
    except Exception:
        return False


def terminal(comando, titulo=""):
    """Roda um comando num terminal DE VERDADE, com TTY.

    ⚠️ Login de CLI por OAuth precisa de terminal. Disparado por Popen mudo, o
    processo morre na hora e o app relata sucesso sobre um processo morto — foi
    exatamente isso que fez os quatro botões de login não funcionarem."""
    import shlex
    try:
        if WIN:
            linha = subprocess.list2cmdline(resolver(comando))
            r = subprocess.run(["cmd", "/c", "start", titulo or "Editor Automatico",
                                "cmd", "/k", linha], capture_output=True, timeout=25)
        else:
            linha = " ".join(shlex.quote(x) for x in comando)
            script = ('tell application "Terminal"\n  activate\n  do script "%s"\n'
                      'end tell' % linha.replace("\\", "\\\\").replace('"', '\\"'))
            r = subprocess.run(["osascript", "-e", script], capture_output=True,
                               text=True, timeout=25)
        if r.returncode != 0:
            return {"ok": False, "msg": (r.stderr or b"").decode("utf-8", "ignore")[:160]
                    if isinstance(r.stderr, bytes) else (r.stderr or "")[:160]}
        return {"ok": True,
                "msg": "Abri o Terminal com o login%s. Autorize no navegador e "
                       "volte aqui." % (" do " + titulo if titulo else "")}
    except Exception as e:
        return {"ok": False, "msg": str(e)[:160]}


def premiere():
    """A versão do Premiere instalada, ou None."""
    try:
        if WIN:
            for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                         os.environ.get("ProgramW6432", r"C:\Program Files")):
                pasta = os.path.join(base, "Adobe")
                if not os.path.isdir(pasta):
                    continue
                achados = sorted((n for n in os.listdir(pasta)
                                  if n.startswith("Adobe Premiere Pro")), reverse=True)
                if achados:
                    return achados[0]
            return None
        for nome in sorted(os.listdir("/Applications"), reverse=True):
            if nome.startswith("Adobe Premiere Pro"):
                return nome
    except Exception:
        pass
    return None
