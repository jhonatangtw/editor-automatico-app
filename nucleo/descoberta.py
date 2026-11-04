"""
Arquivo de descoberta: é por ele que o painel do Tools PRO (dentro do Premiere
e do After) acha o Editor Automático aberto.

O servidor sobe numa porta EFÊMERA com um token novo a cada abertura — de
propósito, ver `app.py`. Quem está de fora não tem como adivinhar nenhum dos
dois, então o app deixa escrito, num lugar só do usuário:

    ~/.editorblackbelt/editor-automatico.json
    {"porta", "token", "pid", "versao", "iniciado_em", "app", "modo", "servico"}

Regras (cada uma tem motivo):
- permissão 0600: o token dá acesso às conversas e ao pipeline que gasta
  crédito; outro usuário da máquina não pode ler;
- gravação atômica (temporário + rename): o painel lê enquanto o app escreve, e
  arquivo pela metade viraria "app fechado" ou JSON quebrado;
- apagar ao fechar — mas SÓ se o arquivo ainda for deste processo. Duas
  aberturas seguidas: a segunda sobrescreve, e a primeira, ao fechar, não pode
  apagar o arquivo da que continua aberta;
- quem lê confere se o pid está vivo (`ler()` faz isso). Se o app morrer sem
  passar pelo fechamento (kill, queda), o arquivo fica para trás e o pid é o
  que denuncia.

Multiplataforma: `~` é a pasta do usuário nos dois sistemas (no Windows,
C:\\Users\\<nome>), a mesma `.editorblackbelt` onde já moram `sessao.json` e o
resto. No Windows o 0600 é só o que o `os.chmod` consegue (somente leitura ou
não); a proteção de verdade lá é a pasta do perfil, que já é só do usuário.
"""

import json
import os
import sys
import tempfile
import time

NOME = "editor-automatico.json"


def pasta():
    return os.path.join(os.path.expanduser("~"), ".editorblackbelt")


def caminho():
    return os.path.join(pasta(), NOME)


def caminho_do_app():
    """O que o painel deve abrir para trazer ESTE app de volta.

    Empacotado no Mac: o `.app` (sobe três níveis a partir de
    Contents/MacOS/EditorAutomatico). Empacotado no Windows: o próprio .exe.
    Rodando do código-fonte: o atalho `Abrir Editor Automático.command`, se
    existir — é assim que se testa uma versão que ainda não foi publicada."""
    exe = os.path.abspath(sys.executable)
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            p = exe
            for _ in range(3):
                p = os.path.dirname(p)
            if p.endswith(".app"):
                return p
        return exe
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    atalho = os.path.join(raiz, "Abrir Editor Automático.command")
    if sys.platform == "darwin" and os.path.isfile(atalho):
        return atalho
    return ""


def argv_servico():
    """Como subir ESTE app em modo serviço (sem janela). Vai no arquivo de
    descoberta: é por ele que o painel religa o serviço depois, inclusive
    quando o app roda do código-fonte (que não está em /Applications)."""
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--servico"]
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [os.path.abspath(sys.executable), os.path.join(raiz, "app.py"), "--servico"]


def desligar_servico_vivo(tempo=3):
    """O app abriu COM janela e já tem um serviço sem janela de pé (ligado
    pelo painel): pede para o serviço sair, para não ficarem dois cérebros
    disputando as mesmas conversas. O painel percebe o pid morto e passa a
    falar com a janela. Devolve True se pediu."""
    d = ler()
    if not d or d.get("modo") != "servico" or d.get("pid") == os.getpid():
        return False
    import urllib.request
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:%d/api/servico/desligar" % int(d["porta"]), data=b"{}",
            method="POST", headers={"X-Token": d["token"], "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=tempo).read()
    except Exception:
        return False
    for _ in range(30):                         # até 3 s para o arquivo dele sumir
        if not pid_vivo(d["pid"]):
            break
        time.sleep(0.1)
    return True


def pid_vivo(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            codigo = ctypes.c_ulong()
            if not k.GetExitCodeProcess(h, ctypes.byref(codigo)):
                return False
            return codigo.value == 259           # STILL_ACTIVE
        finally:
            k.CloseHandle(h)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                              # existe, só não é nosso
    except OSError:
        return False
    return True


def gravar(porta, token, versao, pid=None, app=None, modo="janela"):
    """Grava o arquivo de forma atômica, já com 0600. Devolve o caminho."""
    d = pasta()
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    dados = {
        "porta": int(porta),
        "token": token,
        "pid": int(pid if pid is not None else os.getpid()),
        "versao": versao or "",
        "iniciado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "app": caminho_do_app() if app is None else app,
        # "janela" = o app que a pessoa abriu; "servico" = sem janela, ligado
        # pelo painel (o painel só oferece "Desligar a IA" para este)
        "modo": modo,
        "servico": argv_servico(),
    }
    # mkstemp já cria com 0600 — o token nunca existe no disco com permissão
    # aberta, nem por um instante entre o write e o chmod
    fd, tmp = tempfile.mkstemp(prefix=".editor-automatico-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, caminho())               # atômico nos dois sistemas
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return caminho()


def ler():
    """O conteúdo, ou None se não existe, está quebrado ou o pid morreu."""
    try:
        with open(caminho(), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict) or not pid_vivo(d.get("pid")):
        return None
    return d


def apagar(pid=None):
    """Apaga só se o arquivo ainda for deste processo. Devolve True se apagou."""
    pid = int(pid if pid is not None else os.getpid())
    try:
        with open(caminho(), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(d, dict) or d.get("pid") != pid:
        return False
    try:
        os.unlink(caminho())
        return True
    except OSError:
        return False
