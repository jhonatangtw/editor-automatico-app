"""
Atualização do app — servidor da área do aluno PRIMEIRO, GitHub Releases de
reserva.

Servidor (desde a 0.21.0): `GET /api/atualizacao/editor-automatico?so=…` com o
token do app. Ele só entrega versão para quem tem acesso liberado, numa URL
assinada de 5 minutos, com o sha256 calculado no servidor. **O sha256 é
OBRIGATÓRIO nesse caminho** — sem ele, ou não batendo, nada é instalado. Build
`universal` é o pacote de código (atualização leve); `mac`, `mac-intel` e
`windows` são instaladores.

Qualquer coisa fora do caminho feliz — sem sessão, sem internet, servidor sem
build, versão do servidor não mais nova, resposta estranha, download que não
confere — cai no fluxo do GitHub abaixo, que continua EXATAMENTE como era. Quem
instalou antes da área do aluno não perde nada.

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

import hashlib
import json
import os
import re
import ssl
import sys
import urllib.parse
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


# ---------------------------------------------------------------- servidor

APP_SERVIDOR = "editor-automatico"
TEMPO_SERVIDOR = 10   # a consulta roda na abertura: servidor lento não segura a tela
_SHA = re.compile(r"^[0-9a-fA-F]{64}$")


def _so_servidor():
    """O nome de sistema que o servidor usa (versoes_app.so)."""
    if so.WIN:
        return "windows"
    import platform
    if platform.machine() in ("x86_64", "AMD64", "i386"):
        return "mac-intel"
    return "mac"


def _host_confiavel(url):
    """Só baixa de HTTPS do próprio domínio. A URL vem do servidor, mas é ela
    que decide o que vai rodar nesta máquina — não custa conferir."""
    try:
        u = urllib.parse.urlsplit(str(url or ""))
    except Exception:
        return False
    host = (u.hostname or "").lower()
    return u.scheme == "https" and (host == "editorblackbelt.com.br"
                                    or host.endswith(".editorblackbelt.com.br"))


def _consultar_servidor(versao_local):
    """A versão que o servidor oferece, se for MAIS NOVA e vier completa.

    Devolve o dict do servidor ou None — None significa "siga pelo GitHub".
    Nunca levanta."""
    try:
        from . import conta
        t = conta.token()
        if not t:
            return None
        r = conta._chamar("/api/atualizacao/%s?so=%s" % (APP_SERVIDOR, _so_servidor()),
                          metodo="GET", bearer=t, tempo=TEMPO_SERVIDOR)
        if not isinstance(r, dict) or not r.get("ok") or not r.get("version"):
            return None
        if not _SHA.match(str(r.get("sha256") or "")):
            return None        # sem hash não instala — nunca mais fraco que o GitHub
        if not _host_confiavel(r.get("url")):
            return None
        if r.get("so") not in (None, "", "universal", _so_servidor()):
            return None        # instalador de outro sistema não serve aqui
        if not maior(r.get("version"), versao_local):
            return None        # em dia pelo servidor: o GitHub ainda pode ter mais nova
        return r
    except Exception:
        return None


def _info_servidor(eu, r):
    chave, padrao = _qual_asset()
    codigo_leve = r.get("so") == "universal"
    ext = ".zip" if codigo_leve else os.path.splitext(padrao)[1]
    sha = str(r["sha256"]).lower()
    return {
        "versao": eu.get("version"), "notas_locais": eu.get("notes"),
        "repo": eu.get("repo"), "tem_nova": True,
        "ultima": str(r["version"]), "notas": r.get("notes"),
        "pagina": (_base(eu["repo"]) if eu.get("repo") else None), "erro": None,
        "fonte": "servidor",
        "asset": "EditorAutomatico-%s%s" % (r["version"], ext), "para": chave,
        "modo": "codigo" if codigo_leve else "instalador",
        "porque_instalador": "",
        "codigo": "codigo.zip" if codigo_leve else None,
        "codigo_sha256": sha if codigo_leve else None,
        "url_codigo": r["url"] if codigo_leve else None,
        "rodando_codigo": codigo.ativo(),
        "url": r["url"],
        "sha256": sha,
        "tamanho": r.get("size"),
        # `sig` é texto livre que o admin cola na central. O app de hoje não
        # confere assinatura nenhuma além do sha256 (que aqui é obrigatório);
        # fica guardado para quando houver chave pública embutida.
        "assinatura": r.get("sig"),
    }


def conferir():
    """Servidor da área do aluno primeiro; GitHub se ele não tiver nada mais
    novo para esta máquina. Nunca levanta — devolve o erro."""
    eu = local()
    r = _consultar_servidor(eu.get("version"))
    if r:
        return _info_servidor(eu, r)
    return conferir_github()


# ---------------------------------------------------------------- GitHub

def conferir_github():
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
    if info.get("fonte") == "servidor" and info.get("modo") == "codigo":
        try:
            return _codigo_do_servidor(info, diz)
        except Exception as e:
            diz("o servidor não entregou (%s) — tentando pelo GitHub…" % str(e)[:160])
            info = _reserva_github(e)
    elif info.get("fonte") == "servidor":
        info = conferir_github()   # o servidor só tem instalador: a leve segue pelo GitHub
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


def _baixar_conferido(url, sha256, destino=None, ao_vivo=None, timeout=120):
    """Baixa do servidor conferindo o sha256 no caminho. Sem hash, não baixa.

    Com `destino`, grava em disco (`.parcial` até conferir — arquivo que não
    bate é apagado, nunca fica com o nome final); sem, devolve os bytes."""
    if not _SHA.match(str(sha256 or "")):
        raise RuntimeError("O servidor não informou o sha256 do pacote.")
    if not _host_confiavel(url):
        raise RuntimeError("Endereço de download fora do domínio do Editor Black Belt.")
    req = urllib.request.Request(url, headers=UA)
    h = hashlib.sha256()
    pedacos = [] if destino is None else None
    tmp = (destino + ".parcial") if destino else None
    f = open(tmp, "wb") if tmp else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=rede.contexto()) as r:
            total = int(r.headers.get("Content-Length") or 0)
            lido = 0
            while True:
                p = r.read(262144)
                if not p:
                    break
                h.update(p)
                lido += len(p)
                if f:
                    f.write(p)
                else:
                    pedacos.append(p)
                if ao_vivo and total:
                    ao_vivo("baixando… %d%%" % int(lido * 100 / total))
    except Exception:
        if f:
            f.close()
            f = None
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise
    finally:
        if f:
            f.close()
    if h.hexdigest().lower() != str(sha256).lower():
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise RuntimeError("O arquivo baixado não confere com o publicado (sha256). "
                           "Não vou instalar.")
    if tmp:
        os.replace(tmp, destino)
        return destino
    return b"".join(pedacos)


def _reserva_github(erro_servidor):
    """Depois de o servidor falhar no download, o GitHub assume — mas só se
    ELE tiver versão nova. Se não tiver, a falha do servidor é o que a pessoa
    precisa ler, não um "você já está em dia" que esconde o problema."""
    g = conferir_github()
    if g.get("erro") or not g.get("tem_nova"):
        raise RuntimeError("Não consegui baixar a atualização: %s" % erro_servidor)
    return g


def _codigo_do_servidor(info, diz):
    import io
    import zipfile
    diz("baixando a versão %s…" % info["ultima"])
    dados = _baixar_conferido(info["url_codigo"], info["codigo_sha256"])
    # versão que mexe em dependência binária não pode entrar pela porta leve
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            vj = json.loads(z.read("version.json").decode("utf-8"))
        if vj.get("precisa_instalador"):
            raise RuntimeError("esta versão precisa do instalador completo")
    except KeyError:
        raise RuntimeError("o pacote de código veio sem version.json")
    except zipfile.BadZipFile:
        raise RuntimeError("o pacote de código não é um .zip válido")
    diz("conferindo e instalando…")
    r = codigo.instalar(dados, info["ultima"], info["codigo_sha256"])
    r["msg"] = ("Atualizado para a versão %s. Feche e abra o app para usar — "
                "não precisa reinstalar nada." % info["ultima"])
    r["reabrir"] = True
    r["fonte"] = "servidor"
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


def limpar_instaladores(pasta=None, executavel=None):
    """Ao abrir já atualizado, ejeta o disco do instalador (Mac) e apaga os
    instaladores baixados (.dmg / .exe) que não são mais novos que esta versão.
    Cada .dmg montado aparece no Spotlight — e cada .exe velho na busca do
    Windows — como mais um "Editor Automático": era a origem dos ícones
    repetidos depois de cada atualização."""
    import glob
    import subprocess
    if not (so.MAC or so.WIN):
        return {"ejetados": [], "apagados": []}
    executavel = executavel or sys.executable
    if executavel.startswith("/Volumes/"):
        return {"ejetados": [], "apagados": []}  # rodando de dentro do disco: não mexe
    pasta = os.path.realpath(pasta or os.path.expanduser("~/Downloads"))
    eu = (local() or {}).get("version")
    ejetados, apagados = [], []
    try:
        info = "" if so.WIN else subprocess.run(["hdiutil", "info"], capture_output=True, text=True,
                              timeout=15).stdout
    except Exception:
        info = ""
    imagem = None
    for linha in info.splitlines():
        if linha.startswith("image-path"):
            imagem = linha.split(":", 1)[1].strip()
        elif imagem and "/Volumes/" in linha:
            nome = os.path.basename(imagem)
            if nome.startswith("EditorAutomatico") and nome.endswith(".dmg"):
                vol = linha[linha.index("/Volumes/"):].strip()
                try:
                    subprocess.run(["hdiutil", "detach", vol, "-quiet"],
                                   capture_output=True, timeout=30)
                    ejetados.append(vol)
                except Exception:
                    pass
            imagem = None
    for arq in glob.glob(os.path.join(pasta, "EditorAutomatico*" +
                                      (".exe" if so.WIN else ".dmg"))):
        m = re.search(r"(\d+\.\d+\.\d+)", os.path.basename(arq))
        if not m or not eu or maior(m.group(1), eu):
            continue  # sem versão no nome, ou mais nova que esta: fica
        try:
            os.remove(arq)
            apagados.append(arq)
        except OSError:
            pass
    return {"ejetados": ejetados, "apagados": apagados}


def baixar(destino_dir=None, ao_vivo=None):
    """Baixa o .dmg da versão nova e abre. Quem arrasta para Aplicativos é o
    usuário — de propósito."""
    info = conferir()
    if info.get("fonte") == "servidor":
        destino_dir = destino_dir or os.path.expanduser("~/Downloads")
        try:
            return _instalador_do_servidor(info, destino_dir, ao_vivo)
        except Exception as e:
            ao_vivo and ao_vivo("o servidor não entregou (%s) — tentando pelo GitHub…"
                                % str(e)[:160])
            info = _reserva_github(e)
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


def _como_instalar():
    return ("O instalador FECHA o app sozinho para trocar os arquivos — no "
            "Windows um programa aberto não pode ser sobrescrito. Siga as telas "
            "e abra de novo pelo atalho." if so.WIN else
            "Arraste o Editor Automático para a pasta Aplicativos e reabra o app.")


def _instalador_do_servidor(info, destino_dir, ao_vivo=None):
    """Instalador vindo da área do aluno: baixa, confere o sha256 e só então
    abre. Pacote que não bate é apagado antes de ganhar o nome final."""
    if info.get("modo") == "codigo":
        # build universal (código) pedido pelo caminho do instalador: a leve resolve
        r = atualizar_codigo(ao_vivo)
        return r
    os.makedirs(destino_dir, exist_ok=True)
    alvo = os.path.join(destino_dir, info["asset"])
    ao_vivo and ao_vivo("baixando a versão %s…" % info["ultima"])
    _baixar_conferido(info["url"], info["sha256"], destino=alvo, ao_vivo=ao_vivo, timeout=60)
    aberto = so.abrir(alvo)
    return {"ok": True, "arquivo": alvo, "aberto": aberto, "versao": info["ultima"],
            "fonte": "servidor",
            "msg": "Baixei a versão %s e abri o instalador. %s"
                   % (info["ultima"], _como_instalar())}
