"""
Preparar o ambiente — o app instala o que falta.

Mandar o aluno abrir o Terminal e colar comando é onde a instalação morre.
Aqui o app confere cada dependência, diz em português o que ela faz, e instala
sozinho o que dá para instalar.

O que NÃO dá para automatizar está marcado `manual` com o motivo — Premiere e
Tools PRO precisam de instalador próprio, e prometer que o app resolve isso
seria mentira que só aparece na máquina do aluno.
"""

import os
import shutil
import subprocess

from . import so

MAC, WIN = so.MAC, so.WIN

CEP = os.path.join(so.CEP, "com.editorblackbelt.toolspro")

# quem instala pacote nesta máquina. `winget` vem de fábrica no Windows 10/11;
# o Homebrew, não — por isso ele é o único que o app manda instalar à mão.
GERENCIADOR = so.GERENCIADOR


def _tem(b):
    return so.onde(b) is not None


def _versao(cmd):
    try:
        r = so.run(cmd, capture_output=True, text=True, timeout=15)
        return (r.stdout or r.stderr).strip().splitlines()[0][:60]
    except Exception:
        return ""


def _premiere():
    return so.premiere()


def _skills():
    """Quantas das skills do app estão na pasta do Claude do usuário.

    Sem isto a tela dizia "tudo pronto" enquanto o Claude do editor respondia
    sem repertório nenhum — o mesmo app dando resultado diferente por máquina,
    e sem aviso."""
    from . import skills as sk
    try:
        e = sk.estado()
        return {"ok": not e["faltam"], "rotulo": "%d de %d na pasta do Claude"
                % (e["instaladas"], e["total"]), "faltam": e["faltam"]}
    except Exception as e:
        return {"ok": False, "rotulo": str(e)[:40], "faltam": []}


def _regra():
    """De onde sai a regra de edição. A tela dizia "tudo pronto" enquanto a peça
    que decide a edição não existia na máquina — agora ela aparece na lista."""
    from . import skill
    try:
        o = skill.origem()
        return {"ok": skill.instalada(), "rotulo": o["rotulo"]}
    except Exception as e:
        return {"ok": False, "rotulo": str(e)[:40]}


def _toolspro():
    if not os.path.isdir(CEP):
        return None
    try:
        import json
        with open(os.path.join(CEP, "version.json"), encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return "instalado"


def conferir():
    """O diagnóstico que a tela mostra. Cada item diz para que serve — sem isso
    o aluno vê uma lista de nomes técnicos e não sabe o que é opcional."""
    brew = _tem(GERENCIADOR)
    npm = _tem("npm")
    itens = [
        {"id": "ffmpeg", "nome": "FFmpeg", "tem": _tem("ffmpeg"),
         "para": "cortar, montar e exportar o vídeo",
         "essencial": True, "instalavel": brew, "versao": _versao(["ffmpeg", "-version"])},
        {"id": "ffprobe", "nome": "FFprobe", "tem": _tem("ffprobe"),
         "para": "ler duração, formato e fps do bruto",
         "essencial": True, "instalavel": brew, "versao": ""},
        {"id": "whisper", "nome": "Whisper", "tem": _tem("whisper"),
         "para": "transcrever a fala palavra por palavra, sem subir nada",
         "essencial": True,
         "instalavel": _tem("py") or _tem("python") if WIN
                       else (_tem("pip3") or _tem("python3"))},
        {"id": "node", "nome": "Node.js", "tem": _tem("npm"),
         "para": "é por ele que Claude, Higgsfield e MiniMax se instalam",
         "essencial": True, "instalavel": brew,
         "versao": _versao(["node", "--version"]) if _tem("node") else ""},
        {"id": "claude", "nome": "Claude Code", "tem": _tem("claude"),
         "para": "é quem lê a fala e decide a edição — sem ele o app não pensa",
         "essencial": True, "instalavel": npm,
         "versao": _versao(["claude", "--version"]) if _tem("claude") else ""},
        {"id": "codex", "nome": "Codex CLI (ChatGPT)", "tem": _tem("codex"),
         "para": "falar com o ChatGPT pela SUA assinatura, sem pagar API à parte",
         "essencial": False, "instalavel": npm,
         "versao": _versao(["codex", "--version"]) if _tem("codex") else ""},
        {"id": "higgsfield", "nome": "Higgsfield CLI", "tem": _tem("higgsfield"),
         "para": "gerar imagem e b-roll",
         "essencial": True, "instalavel": npm},
        {"id": "heygen", "nome": "HeyGen CLI", "tem": _tem("heygen"),
         "para": "avatar falante — o login por CLI gasta crédito de ASSINATURA, "
                 "não a carteira de API",
         "essencial": False, "instalavel": True},
        {"id": "mmx", "nome": "MiniMax CLI", "tem": _tem("mmx"),
         "para": "vídeo, imagem e música da MiniMax (voz não — é ElevenLabs)",
         "essencial": False, "instalavel": npm},
        {"id": "ant", "nome": "CLI da Anthropic", "tem": _tem("ant"),
         "para": "entrar na conta Claude sem colar chave (opcional — dá para usar chave)",
         "essencial": False, "instalavel": brew and not WIN,
         "manual": ("No Windows, use a chave de API na tela de Contas."
                    if WIN else None)},
        {"id": "regra", "nome": "Regra de edição", "tem": _regra()["ok"],
         "para": "onde entra o punch, a cadência e o marcador — vem dentro do app",
         "essencial": True, "instalavel": False,
         "manual": None if _regra()["ok"] else "Reinstale o app: ela vem junto.",
         "versao": _regra()["rotulo"]},
        {"id": "skills", "nome": "Skills do Claude", "tem": _skills()["ok"],
         "para": "o repertório que o Claude usa — fotorrealismo, Pixar 3D, "
                 "storyboard, prompts de vídeo e a edição de b-roll",
         "essencial": False, "instalavel": False,
         "manual": None if _skills()["ok"] else "Instale pelo botão no card acima.",
         "versao": _skills()["rotulo"]},
        {"id": "premiere", "nome": "Adobe Premiere Pro", "tem": bool(_premiere()),
         "para": "receber a timeline montada",
         "essencial": False, "manual": "Instale pelo Creative Cloud.",
         "versao": _premiere() or ""},
        {"id": "toolspro", "nome": "Tools PRO", "tem": bool(_toolspro()),
         "para": "montar a timeline por dentro do Premiere",
         "essencial": False,
         "manual": "Instale pelo instalador do Editor Black Belt.",
         "versao": _toolspro() or ""},
    ]
    faltam = [i for i in itens if not i["tem"] and i["essencial"]]
    return {
        "itens": [dict((k, v) for k, v in i.items() if v is not None) for i in itens],
        "brew": brew,
        "gerenciador": GERENCIADOR,
        "sistema": so.SISTEMA,
        "pronto": not faltam,
        "faltam": [i["nome"] for i in faltam],
        "so_manual": [i["nome"] for i in itens
                      if not i["tem"] and i.get("manual")],
    }


# ---------------------------------------------------------------- instalar

_WINGET = ["winget", "install", "-e", "--accept-package-agreements",
           "--accept-source-agreements", "--id"]

RECEITAS_MAC = {
    "node":       [["brew", "install", "node"]],
    "codex":      [["npm", "install", "-g", "@openai/codex"]],
    "claude":     [["npm", "install", "-g", "@anthropic-ai/claude-code"]],
    "ffmpeg":     [["brew", "install", "ffmpeg"]],
    "ffprobe":    [["brew", "install", "ffmpeg"]],   # vem no mesmo pacote
    # faster-whisper em vez do whisper oficial: mesma qualidade sem arrastar o
    # torch inteiro (~2GB), que é o que fazia a instalação desistir no meio.
    "whisper":    [["pip3", "install", "--user", "--upgrade", "openai-whisper"]],
    "higgsfield": [["npm", "install", "-g", "@higgsfield/cli"]],
    "mmx":        [["npm", "install", "-g", "mmx-cli"]],
    "ant":        [["brew", "tap", "anthropics/tap"],
                   ["brew", "install", "anthropics/tap/ant"]],
}

# ⚠️ No Windows os CLI de npm viram `.cmd`. Quem chama tem que passar pelo
# `so.run`, senão o Python levanta FileNotFoundError com o binário instalado.
RECEITAS_WIN = {
    "node":       [_WINGET + ["OpenJS.NodeJS.LTS"]],
    "codex":      [["npm", "install", "-g", "@openai/codex"]],
    "claude":     [["npm", "install", "-g", "@anthropic-ai/claude-code"]],
    "ffmpeg":     [_WINGET + ["Gyan.FFmpeg"]],
    "ffprobe":    [_WINGET + ["Gyan.FFmpeg"]],
    "whisper":    [["python", "-m", "pip", "install", "--upgrade", "openai-whisper"]],
    "higgsfield": [["npm", "install", "-g", "@higgsfield/cli"]],
    "mmx":        [["npm", "install", "-g", "mmx-cli"]],
}

RECEITAS = RECEITAS_WIN if WIN else RECEITAS_MAC


BIN = os.path.expanduser("~/.editorblackbelt/bin")
HEYGEN_REPO = "heygen-com/heygen-cli"


def _instalar_heygen(ao_vivo=None):
    """Baixa o binário oficial do HeyGen e põe em ~/.editorblackbelt/bin.

    ⚠️ A receita antiga era `brew install heygen` — e essa fórmula NÃO EXISTE.
    Nunca instalou nada em máquina nenhuma; na do aluno o app abriu um Terminal
    que respondeu "command not found". O CLI se distribui por GitHub Releases,
    um binário por plataforma, e é isso que dá para instalar sem depender de
    Homebrew, de Node ou de qualquer outra coisa que o editor não tem."""
    import json as _json
    import platform as _plat
    import tarfile
    import urllib.request
    import zipfile
    from . import rede

    diz = ao_vivo or (lambda _: None)
    maquina = _plat.machine().lower()
    arq = "arm64" if maquina in ("arm64", "aarch64") else "amd64"
    sis = "windows" if WIN else "darwin"

    diz("procurando a versão publicada do HeyGen…")
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/releases/latest" % HEYGEN_REPO,
        headers={"User-Agent": "EditorAutomatico", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30, context=rede.contexto()) as r:
        rel = _json.loads(r.read())

    alvo = None
    for a in rel.get("assets", []):
        n = a["name"]
        if sis in n and arq in n and n.endswith((".tar.gz", ".zip")):
            alvo = a
            break
    if not alvo:
        raise RuntimeError("Não achei o HeyGen para %s/%s na versão %s."
                           % (sis, arq, rel.get("tag_name")))

    diz("baixando %s…" % alvo["name"])
    req = urllib.request.Request(alvo["browser_download_url"],
                                 headers={"User-Agent": "EditorAutomatico"})
    with urllib.request.urlopen(req, timeout=180, context=rede.contexto()) as r:
        dados = r.read()

    os.makedirs(BIN, exist_ok=True)
    import io
    diz("instalando em %s…" % BIN)
    if alvo["name"].endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            for n in z.namelist():
                if os.path.basename(n).lower().startswith("heygen"):
                    with z.open(n) as f, open(os.path.join(BIN, os.path.basename(n)), "wb") as g:
                        g.write(f.read())
    else:
        with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as t:
            for m in t.getmembers():
                if m.isfile() and os.path.basename(m.name).lower().startswith("heygen"):
                    f = t.extractfile(m)
                    destino = os.path.join(BIN, os.path.basename(m.name))
                    with open(destino, "wb") as g:
                        g.write(f.read())
                    os.chmod(destino, 0o755)

    if BIN not in os.environ.get("PATH", ""):
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + BIN
    return {"ok": _tem("heygen"), "qual": "heygen", "versao": rel.get("tag_name")}


def instalar(qual, ao_vivo=None):
    if qual == "heygen":
        return _instalar_heygen(ao_vivo)
    receita = RECEITAS.get(qual)
    if not receita:
        raise RuntimeError("Não sei instalar “%s” automaticamente." % qual)
    if qual in ("ffmpeg", "ffprobe", "ant") and not _tem(GERENCIADOR):
        if WIN:
            raise RuntimeError(
                "O winget não respondeu. Ele vem no Windows 10 e 11 pela loja "
                "(App Installer) — abra a Microsoft Store, instale o "
                "“Instalador de Aplicativo” e tente de novo.")
        raise RuntimeError(
            "Precisa do Homebrew. Cole isto no Terminal uma vez:\n"
            '/bin/bash -c "$(curl -fsSL '
            'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

    for cmd in receita:
        ao_vivo and ao_vivo("$ " + " ".join(cmd))
        proc = so.popen(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
        for linha in proc.stdout:
            ao_vivo and ao_vivo(linha.rstrip()[:160])
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("Falhou em: " + " ".join(cmd))

    # o PATH do processo já rodando não vê o que acabou de ser instalado
    novos = ([os.path.join(os.environ.get("APPDATA") or "", "npm"),
              os.path.join(os.environ.get("LOCALAPPDATA") or "",
                           "Microsoft", "WinGet", "Links")] if WIN else
             ["/opt/homebrew/bin", "/usr/local/bin",
              os.path.expanduser("~/.npm-global/bin"),
              os.path.expanduser("~/Library/Python/3.9/bin")])
    os.environ["PATH"] = os.pathsep.join(
        [os.environ.get("PATH", "")] + novos)
    shutil.which.cache_clear() if hasattr(shutil.which, "cache_clear") else None
    return {"ok": _tem(qual), "qual": qual}


def instalar_gerenciador():
    """Instala o que instala o resto.

    Mandar o aluno "colar isto no Terminal" é onde a instalação morre — e no Mac
    sem Homebrew o app fica sem FFmpeg, que é a peça essencial. O instalador do
    Homebrew PRECISA de terminal de verdade: ele pede a senha de administrador,
    e um Popen mudo morreria esperando uma senha que ninguém vê para digitar."""
    if WIN:
        return {"ok": False, "loja": True,
                "msg": "No Windows o winget vem pela Microsoft Store: instale o "
                       "“Instalador de Aplicativo” e volte aqui."}
    if _tem("brew"):
        return {"ok": True, "ja_tinha": True, "msg": "O Homebrew já está instalado."}
    r = so.terminal(
        ["/bin/bash", "-c",
         '"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'],
        "Homebrew")
    if r.get("ok"):
        r["msg"] = ("Abri o Terminal com o instalador do Homebrew. Ele vai pedir a "
                    "SENHA DO SEU MAC — é o instalador oficial pedindo, não o app. "
                    "Quando terminar, volte aqui e clique em Instalar o que falta.")
    return r


def instalar_tudo(ao_vivo=None):
    d = conferir()
    feitos, erros = [], []
    for i in d["itens"]:
        if i["tem"] or not i["essencial"] or i.get("manual"):
            continue
        try:
            ao_vivo and ao_vivo("▸ instalando " + i["nome"])
            instalar(i["id"], ao_vivo)
            feitos.append(i["nome"])
        except Exception as e:
            erros.append("%s: %s" % (i["nome"], e))
    return {"instalados": feitos, "erros": erros, "estado": conferir()}
