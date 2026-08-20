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
        {"id": "higgsfield", "nome": "Higgsfield CLI", "tem": _tem("higgsfield"),
         "para": "gerar imagem e b-roll",
         "essencial": True, "instalavel": npm},
        {"id": "heygen", "nome": "HeyGen CLI", "tem": _tem("heygen"),
         "para": "avatar falante — o login por CLI gasta crédito de ASSINATURA, "
                 "não a carteira de API",
         "essencial": False, "instalavel": brew and not WIN,
         "manual": ("No Windows o HeyGen CLI se instala pelo site deles."
                    if WIN else None)},
        {"id": "mmx", "nome": "MiniMax CLI", "tem": _tem("mmx"),
         "para": "vídeo, imagem e música da MiniMax (voz não — é ElevenLabs)",
         "essencial": False, "instalavel": npm},
        {"id": "ant", "nome": "CLI da Anthropic", "tem": _tem("ant"),
         "para": "entrar na conta Claude sem colar chave (opcional — dá para usar chave)",
         "essencial": False, "instalavel": brew and not WIN,
         "manual": ("No Windows, use a chave de API na tela de Contas."
                    if WIN else None)},
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
    "ffmpeg":     [["brew", "install", "ffmpeg"]],
    "ffprobe":    [["brew", "install", "ffmpeg"]],   # vem no mesmo pacote
    # faster-whisper em vez do whisper oficial: mesma qualidade sem arrastar o
    # torch inteiro (~2GB), que é o que fazia a instalação desistir no meio.
    "whisper":    [["pip3", "install", "--user", "--upgrade", "openai-whisper"]],
    "higgsfield": [["npm", "install", "-g", "@higgsfield/cli"]],
    "heygen":     [["brew", "install", "heygen"]],
    "mmx":        [["npm", "install", "-g", "mmx-cli"]],
    "ant":        [["brew", "tap", "anthropics/tap"],
                   ["brew", "install", "anthropics/tap/ant"]],
}

# ⚠️ No Windows os CLI de npm viram `.cmd`. Quem chama tem que passar pelo
# `so.run`, senão o Python levanta FileNotFoundError com o binário instalado.
RECEITAS_WIN = {
    "ffmpeg":     [_WINGET + ["Gyan.FFmpeg"]],
    "ffprobe":    [_WINGET + ["Gyan.FFmpeg"]],
    "whisper":    [["python", "-m", "pip", "install", "--upgrade", "openai-whisper"]],
    "higgsfield": [["npm", "install", "-g", "@higgsfield/cli"]],
    "mmx":        [["npm", "install", "-g", "mmx-cli"]],
}

RECEITAS = RECEITAS_WIN if WIN else RECEITAS_MAC


def instalar(qual, ao_vivo=None):
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
    novos = ([os.path.expandvars(r"%APPDATA%\npm")] if WIN else
             ["/opt/homebrew/bin", "/usr/local/bin",
              os.path.expanduser("~/.npm-global/bin"),
              os.path.expanduser("~/Library/Python/3.9/bin")])
    os.environ["PATH"] = os.pathsep.join(
        [os.environ.get("PATH", "")] + novos)
    shutil.which.cache_clear() if hasattr(shutil.which, "cache_clear") else None
    return {"ok": _tem(qual), "qual": qual}


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
