"""
Atualização do app — GitHub Releases, igual ao plugin.

Como funciona: o `version.json` que viaja dentro do app diz a versão instalada
e de qual repositório ele se atualiza. A versão publicada é o MESMO arquivo
anexado na Release "latest". Comparou, achou maior, oferece.

Duas decisões que valem a pena registrar:

  * **O app não se substitui sozinho.** Baixa o .dmg e abre — o aluno arrasta
    para Aplicativos. Trocar por baixo um bundle que está rodando é onde mora o
    app que não abre mais, e o custo de errar isso é suporte, não conveniência.

  * **Falha de rede não pode quebrar a tela.** Toda função aqui devolve o erro
    como dado (`{"erro": ...}`), nunca levanta. Um aluno sem internet continua
    editando; ele só não vê o aviso de atualização.
"""

import json
import os
import ssl
import subprocess
import sys
import urllib.request

TEMPO = 20
UA = {"User-Agent": "EditorAutomatico"}


def _raiz():
    """Onde mora o version.json — no código ou dentro do .app empacotado."""
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in (getattr(sys, "_MEIPASS", None), aqui,
                 os.path.dirname(sys.executable)):
        if base and os.path.isfile(os.path.join(base, "version.json")):
            return base
    return aqui


def local():
    try:
        with open(os.path.join(_raiz(), "version.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "0.0.0"}


def _num(v):
    partes = []
    for p in str(v or "0").strip().lstrip("vV").split("."):
        d = "".join(c for c in p if c.isdigit())
        partes.append(int(d or 0))
    return tuple((partes + [0, 0, 0])[:3])


def maior(a, b):
    return _num(a) > _num(b)


def _pegar(url, timeout=TEMPO):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def _base(repo):
    return "https://github.com/%s/releases" % repo


def conferir():
    """A versão publicada bate na de dentro? Nunca levanta — devolve o erro."""
    eu = local()
    repo = eu.get("repo")
    saida = {"versao": eu.get("version"), "notas_locais": eu.get("notes"),
             "repo": repo, "tem_nova": False, "ultima": None, "notas": None,
             "pagina": _base(repo) if repo else None, "erro": None}
    if not repo:
        saida["erro"] = ("Este app ainda não sabe de onde se atualizar "
                         "(falta 'repo' no version.json).")
        return saida
    try:
        d = json.loads(_pegar(_base(repo) + "/latest/download/version.json"))
    except Exception as e:
        saida["erro"] = "Não consegui falar com o GitHub: %s" % str(e)[:120]
        return saida
    saida["ultima"] = d.get("version")
    saida["notas"] = d.get("notes")
    saida["asset"] = d.get("asset") or eu.get("asset") or "EditorAutomatico.dmg"
    saida["tem_nova"] = maior(saida["ultima"], saida["versao"])
    saida["url"] = "%s/latest/download/%s" % (_base(repo), saida["asset"])
    return saida


def baixar(destino_dir=None, ao_vivo=None):
    """Baixa o .dmg da versão nova e abre. Quem arrasta para Aplicativos é o
    usuário — de propósito."""
    info = conferir()
    if info.get("erro"):
        raise RuntimeError(info["erro"])
    if not info["tem_nova"]:
        return {"ok": True, "nada": True,
                "msg": "Você já está na versão mais nova (%s)." % info["versao"]}

    destino_dir = destino_dir or os.path.expanduser("~/Downloads")
    os.makedirs(destino_dir, exist_ok=True)
    alvo = os.path.join(destino_dir, "EditorAutomatico-%s.dmg" % info["ultima"])

    ao_vivo and ao_vivo("baixando a versão %s…" % info["ultima"])
    req = urllib.request.Request(info["url"], headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        lido = 0
        tmp = alvo + ".parcial"
        with open(tmp, "wb") as f:
            while True:
                pedaco = r.read(262144)
                if not pedaco:
                    break
                f.write(pedaco)
                lido += len(pedaco)
                if ao_vivo and total:
                    ao_vivo("baixando… %d%%" % int(lido * 100 / total))
    os.replace(tmp, alvo)

    aberto = False
    if sys.platform == "darwin":
        aberto = subprocess.run(["open", alvo], capture_output=True).returncode == 0
    return {"ok": True, "arquivo": alvo, "aberto": aberto, "versao": info["ultima"],
            "msg": ("Baixei a versão %s e abri o instalador. Arraste o Editor "
                    "Automático para a pasta Aplicativos e reabra o app."
                    % info["ultima"])}
