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
import sys
import urllib.request

from . import codigo, rede, so

TEMPO = 20
UA = {"User-Agent": "EditorAutomatico"}


def _raiz():
    """Onde mora o version.json DO CÓDIGO QUE ESTÁ RODANDO.

    ⚠️ A ordem aqui é o bug mais escorregadio que a atualização leve produziu.
    `sys._MEIPASS` aponta para o PACOTE INSTALADO; depois de uma atualização
    leve, o app roda o código novo mas o pacote continua com o `version.json`
    velho. Lendo o pacote primeiro, o app rodava a 0.19 e se declarava 0.18 —
    então a versão nova NUNCA parecia instalada: o aviso de atualizar voltava a
    cada abertura, e atualizar de novo não resolvia nada.

    `aqui` é a pasta do código em execução (a externa, quando há uma). É essa a
    versão verdadeira."""
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in (aqui, getattr(sys, "_MEIPASS", None),
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
    ctx = rede.contexto()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def _base(repo):
    return "https://github.com/%s/releases" % repo


def _qual_asset():
    """Qual instalador serve ESTA máquina, e o nome de reserva se o
    version.json publicado for antigo e não trouxer a chave."""
    if so.WIN:
        return "asset_win", "EditorAutomatico-Instalador.exe"
    import platform
    if platform.machine() in ("x86_64", "AMD64", "i386"):
        return "asset_mac_intel", "EditorAutomatico-Intel.dmg"
    return "asset_mac", "EditorAutomatico.dmg"


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
        saida["erro"] = "Não consegui falar com o GitHub: %s" % rede.explicar(e)[:220]
        return saida
    saida["ultima"] = d.get("version")
    saida["notas"] = d.get("notes")
    # cada máquina baixa o SEU instalador. Não é só Mac × Windows: o .dmg do
    # Apple Silicon NÃO abre num Mac Intel (o Rosetta traduz Intel→ARM, nunca o
    # contrário), então o processador também escolhe.
    chave, padrao = _qual_asset()
    saida["asset"] = (d.get(chave) or eu.get(chave) or d.get("asset")
                      or eu.get("asset") or padrao)
    saida["para"] = chave

    # ATUALIZAÇÃO LEVE: quase toda correção é código, e código o app troca
    # sozinho. Só cai no instalador quando a versão declara que precisa — isto
    # é, quando mexeu em dependência binária.
    # `precisa_instalador` é só para versão que muda DEPENDÊNCIA BINÁRIA. Arquivo
    # novo em app.py/nucleo/web/regra viaja no pacote de código — marcar por
    # cautela faria toda versão virar reinstalação, que é o problema original.
    pesado = bool(d.get("precisa_instalador"))
    tem_codigo = bool(d.get("codigo"))
    saida["modo"] = "instalador" if (pesado or not tem_codigo) else "codigo"
    saida["porque_instalador"] = ("esta versão mexeu no que vem dentro do "
                                  "pacote, então precisa reinstalar") if pesado else ""
    saida["codigo"] = d.get("codigo")
    saida["codigo_sha256"] = d.get("codigo_sha256")
    saida["url_codigo"] = ("%s/latest/download/%s" % (_base(repo), d["codigo"])
                           if tem_codigo else None)
    saida["rodando_codigo"] = codigo.ativo()
    saida["tem_nova"] = maior(saida["ultima"], saida["versao"])
    saida["url"] = "%s/latest/download/%s" % (_base(repo), saida["asset"])
    return saida


def atualizar_codigo(ao_vivo=None):
    """Baixa só o código e aponta o app para ele. ~1 MB, sem instalador.

    Não substitui nada em uso: grava ao lado e troca o ponteiro. O código antigo
    continua no disco até a próxima limpeza, então voltar é trocar um arquivo."""
    diz = ao_vivo or (lambda _: None)
    info = conferir()
    if info.get("erro"):
        raise RuntimeError(info["erro"])
    if not info["tem_nova"]:
        return {"ok": True, "nada": True,
                "msg": "Você já está na versão mais nova (%s)." % info["versao"]}
    if info["modo"] != "codigo":
        raise RuntimeError(info.get("porque_instalador") or
                           "Esta versão precisa do instalador completo.")

    diz("baixando a versão %s…" % info["ultima"])
    dados = _pegar(info["url_codigo"], timeout=120)
    diz("conferindo e instalando…")
    r = codigo.instalar(dados, info["ultima"], info.get("codigo_sha256"))
    r["msg"] = ("Atualizado para a versão %s. Feche e abra o app para usar — "
                "não precisa reinstalar nada." % info["ultima"])
    r["reabrir"] = True
    return r


def reabrir():
    """Fecha e abre o app de novo, para a versão nova valer."""
    import subprocess
    import threading
    alvo = sys.executable
    if so.MAC and ".app/Contents/MacOS/" in alvo:
        cmd = ["open", "-n", alvo.split(".app/Contents/MacOS/")[0] + ".app"]
    elif getattr(sys, "frozen", False):
        cmd = [alvo]
    else:
        # em desenvolvimento `sys.executable` é o Python: sem o script junto,
        # "reabrir" abriria um interpretador vazio
        cmd = [alvo, os.path.join(_raiz(), "app.py")]

    def sair():
        import time
        time.sleep(0.8)
        try:
            subprocess.Popen(cmd, close_fds=True)
        except Exception:
            pass
        time.sleep(0.6)
        os._exit(0)

    threading.Thread(target=sair, daemon=True).start()
    return {"ok": True, "msg": "Reabrindo o app…"}


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
    ext = os.path.splitext(info["asset"])[1] or (".exe" if so.WIN else ".dmg")
    alvo = os.path.join(destino_dir, "EditorAutomatico-%s%s" % (info["ultima"], ext))

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

    aberto = so.abrir(alvo)
    comofaz = ("O instalador FECHA o app sozinho para trocar os arquivos — no "
               "Windows um programa aberto não pode ser sobrescrito. Siga as telas "
               "e abra de novo pelo atalho." if so.WIN else
               "Arraste o Editor Automático para a pasta Aplicativos e reabra o app.")
    return {"ok": True, "arquivo": alvo, "aberto": aberto, "versao": info["ultima"],
            "msg": "Baixei a versão %s e abri o instalador. %s"
                   % (info["ultima"], comofaz)}
