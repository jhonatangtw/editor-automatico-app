"""
Entregas de mídia na Conversa — achar, baixar, medir e servir com segurança.

A Conversa mostra a PRÉVIA do que a IA entregou (imagem, vídeo, áudio), como o
Claude faz. Este módulo é o lado de cá:

  detectar()   acha caminhos de mídia e URLs de entrega num texto (resultado de
               ferramenta ou resposta da IA). Do Higgsfield vale `result_url`,
               NUNCA `min_result_url` — a miniatura de 600 px já enganou em job
               real (memória higgsfield-cli-result-url-vs-min).
  baixar()     traz a entrega remota para a PASTA DO PROJETO, em
               `media/imagens|videos|audio`. Link de entrega expira; pasta
               temporária é limpa sem aviso; e mídia fora da pasta do projeto
               vira mídia offline no Premiere. Regra do Jhon: tudo o que é
               baixado ou gerado fica na pasta do projeto.
  info()       dimensões e duração (ffprobe), em cache.
  picos()      a forma da onda de um áudio (ffmpeg), em cache no disco.
  quadro()     miniatura de imagem ou primeiro quadro de vídeo (ffmpeg).
  permitido()  a trava: só se serve o que está dentro das pastas do app
               (projetos e conversas), da pasta do job ligada a um projeto ou
               da pasta de projeto que o usuário escolheu. Tudo resolvido com
               realpath antes de comparar — symlink e `..` não escapam.

Só stdlib, como o resto do app.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from array import array

from . import conversas, projetos, so

EXT_IMAGEM = ("png", "jpg", "jpeg", "webp", "gif")
EXT_VIDEO = ("mp4", "mov", "webm", "m4v")
EXT_AUDIO = ("mp3", "wav", "m4a", "aac", "ogg")
TIPO_EXT = {**{e: "imagem" for e in EXT_IMAGEM}, **{e: "video" for e in EXT_VIDEO},
            **{e: "audio" for e in EXT_AUDIO}}
PASTA_TIPO = {"imagem": "imagens", "video": "videos", "audio": "audio"}

# O `mimetypes` do sistema não conhece todos (m4a, m4v e webm faltam em alguns
# Mac e Windows) — e Content-Type errado faz o WebKit recusar tocar.
MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
        "gif": "image/gif", "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
        "m4v": "video/x-m4v", "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
        "aac": "audio/aac", "ogg": "audio/ogg"}
EXT_DO_MIME = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp",
               "image/gif": "gif", "video/mp4": "mp4", "video/quicktime": "mov",
               "video/webm": "webm", "video/x-m4v": "m4v", "audio/mpeg": "mp3",
               "audio/mp3": "mp3", "audio/wav": "wav", "audio/x-wav": "wav",
               "audio/wave": "wav", "audio/mp4": "m4a", "audio/x-m4a": "m4a",
               "audio/aac": "aac", "audio/ogg": "ogg"}

LIMITE_BAIXAR = 1024 ** 3          # 1 GB: maior que qualquer entrega de IA, menor que um disco cheio
MAX_POR_TEXTO = 60                 # um resultado com 200 caminhos não vira 200 prévias
CACHE = os.path.expanduser("~/.editorblackbelt/cache/midia")

# Chaves de JSON que NÃO são a entrega: miniatura, prévia e a mídia de ENTRADA
# (referência que o usuário mandou para o Higgsfield).
CHAVES_FORA = {"min_result_url", "min_url", "thumbnail_url", "thumbnail", "thumb_url",
               "thumb", "preview_url", "gif_url", "poster_url", "cover_url",
               "caption_url", "subtitle_url"}
SUBARVORES_FORA = {"params", "input", "inputs", "medias", "reference", "references",
                   "input_images", "image_references", "reference_images"}
# Chaves que SÃO entrega mesmo sem extensão na URL
CHAVES_ENTREGA = {"result_url": None, "video_url": "video", "audio_url": "audio",
                  "image_url": "imagem", "download_url": None, "output_url": None,
                  "url": None}


def ext_de(caminho):
    p = caminho
    if "://" in p:
        p = urllib.parse.urlparse(p).path
    return os.path.splitext(p)[1].lower().lstrip(".")


def tipo_de(caminho):
    return TIPO_EXT.get(ext_de(caminho))


def mime_de(caminho):
    return MIME.get(ext_de(caminho))


# ================================================================ detecção
_EXT_RE = r"png|jpe?g|webp|gif|mp4|mov|webm|m4v|mp3|wav|m4a|aac|ogg"
_FIM_EXT = re.compile(r"\.(?:%s)(?![\w])" % _EXT_RE, re.I)
_URL = re.compile(r"https?://[^\s\"'<>`\\)\]}|^]+", re.I)
_URL_CHAVE = re.compile(r'"([A-Za-z_]+)"\s*:\s*"(https?://[^"\s]+)"')
_FRONTEIRA = set(" \t\"'`([{<=,;:*")


def _limpar_url(u):
    return u.rstrip(".,;:!?*")


def _chave_url(u):
    p = urllib.parse.urlsplit(u)
    return "%s://%s%s" % (p.scheme.lower(), p.netloc.lower(), p.path)


def _inicio(linha, i):
    """Começa um caminho absoluto em `i`? (`/`, `~/` ou `C:\\`)"""
    if i > 0 and linha[i - 1] not in _FRONTEIRA:
        return False
    c = linha[i]
    if c == "/":
        return True
    if c == "~":
        return linha[i + 1:i + 2] in ("/", "\\")
    return (c.isalpha() and linha[i + 1:i + 2] == ":" and linha[i + 2:i + 3] in ("\\", "/"))


def _normal(cand):
    c = cand.strip()
    if c.lower().startswith("file://"):
        c = urllib.parse.unquote(urllib.parse.urlparse(c).path)
    return os.path.expanduser(c)


def _caminhos(texto, existe):
    """Caminhos absolutos de mídia que existem. Caminho com espaço é comum
    (`Editor Automático/Projetos/...`), então para cada fim de extensão tenta
    os começos possíveis da linha, do mais longo para o mais curto, e fica com
    o primeiro que EXISTE no disco — é a existência que decide, não a regex."""
    achados = []
    for linha in texto.splitlines():
        if "." not in linha:
            continue
        piso = 0
        for m in _FIM_EXT.finditer(linha):
            fim = m.end()
            for i in range(piso, m.start()):
                if not _inicio(linha, i):
                    continue
                cand = linha[i:fim]
                if len(cand) > 1024:
                    continue
                p = _normal(cand)
                try:
                    if existe(p):
                        achados.append(p)
                        piso = fim
                        break
                except (OSError, ValueError):
                    continue
    return achados


def _de_json(obj, urls, textos, fora=False, chave=None):
    """Anda no JSON: URLs das chaves de entrega e todos os textos (para os
    caminhos). Miniatura e mídia de entrada ficam de fora."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            _de_json(v, urls, textos, fora or kl in SUBARVORES_FORA, kl)
    elif isinstance(obj, list):
        for v in obj[:500]:
            _de_json(v, urls, textos, fora, chave)
    elif isinstance(obj, str):
        if fora or chave in CHAVES_FORA:
            return
        s = obj.strip()
        if s.lower().startswith(("http://", "https://")) and " " not in s:
            t = tipo_de(s)
            if t or (chave in CHAVES_ENTREGA and chave != "url"):
                urls.append((s, t or CHAVES_ENTREGA.get(chave)))
        else:
            textos.append(obj)


def detectar(texto, existe=os.path.isfile, permitido_=None, limite=MAX_POR_TEXTO):
    """Mídias num texto, na ordem em que aparecem, sem repetir.

    Devolve [{"tipo", "caminho", "nome"}] para arquivo local e
    [{"tipo", "url"}] para entrega remota (o `tipo` da remota pode ser None
    quando a URL não tem extensão: o download decide pelo Content-Type)."""
    if not texto or not isinstance(texto, str):
        return []
    urls, textos = [], []
    obj = None
    s = texto.strip()
    if s[:1] in "[{":
        try:
            obj = json.loads(s)
        except Exception:
            obj = None
    if obj is not None:
        _de_json(obj, urls, textos)
        corpo = "\n".join(textos)
    else:
        bloqueadas = {_chave_url(u) for k, u in _URL_CHAVE.findall(texto)
                      if k.lower() in CHAVES_FORA}
        for k, u in _URL_CHAVE.findall(texto):
            kl = k.lower()
            if kl in CHAVES_ENTREGA and kl != "url" and not tipo_de(u):
                urls.append((u, CHAVES_ENTREGA[kl]))
        for m in _URL.finditer(texto):
            u = _limpar_url(m.group(0))
            if _chave_url(u) in bloqueadas:
                continue
            t = tipo_de(u)
            if t:
                urls.append((u, t))
        corpo = texto
    # as URLs saem do texto antes de procurar caminho: "/a/b.png" dentro de
    # "https://x/a/b.png" não é arquivo desta máquina
    corpo = _URL.sub(lambda m: " " * len(m.group(0)), corpo)

    saida, vistos = [], set()
    for p in _caminhos(corpo, existe):
        t = tipo_de(p)
        if not t:
            continue
        try:
            k = os.path.realpath(p)
        except Exception:
            k = p
        if k in vistos:
            continue
        if permitido_ is not None and not permitido_(p):
            continue
        vistos.add(k)
        saida.append({"tipo": t, "caminho": p, "nome": os.path.basename(p)})
    for u, t in urls:
        u = _limpar_url(u)
        k = _chave_url(u)
        if k in vistos:
            continue
        vistos.add(k)
        saida.append({"tipo": t, "url": u})
    return saida[:limite]


def detectar_permitidas(texto):
    """A detecção que vale na Conversa: arquivo que existe E que o app pode
    servir. O que fica fora não vira prévia quebrada na tela."""
    return detectar(texto, permitido_=lambda p: permitido(p, so_midia=True))


def do_passo(p):
    """Mídias de um passo de ferramenta/texto já guardado (histórico)."""
    if not isinstance(p, dict):
        return []
    if p.get("tipo") == "texto":
        return detectar_permitidas(p.get("texto") or "")
    if p.get("tipo") != "ferramenta":
        return []
    achadas = detectar_permitidas(p.get("resultado") or p.get("saida") or "")
    # o Claude VIU uma imagem do job (folha de contato do QC, original × clone):
    # ela entra como prévia da ação, grande no lightbox
    ent = p.get("entrada") or {}
    nome = str(p.get("nome") or "")
    if nome == "Read" and isinstance(ent, dict):
        c = ent.get("file_path") or ""
        if c and tipo_de(c) == "imagem" and os.path.isfile(c) and permitido(c, so_midia=True):
            if not any(m.get("caminho") == c for m in achadas):
                achadas.append({"tipo": "imagem", "caminho": c, "nome": os.path.basename(c)})
    return achadas


def _ainda_valem(lista):
    saida = []
    for m in lista or []:
        if not isinstance(m, dict):
            continue
        if m.get("url"):
            saida.append(m)
        elif m.get("caminho") and os.path.isfile(m["caminho"]) and permitido(m["caminho"], so_midia=True):
            saida.append(m)
    return saida


def anotar(msgs):
    """Prévia também nas conversas ANTIGAS: passo sem `midias` (gravado antes
    da 0.22.1) ganha a detecção na hora de abrir; os que já têm são
    reconferidos — arquivo apagado não vira miniatura quebrada."""
    for m in msgs or []:
        if not isinstance(m, dict):
            continue
        if m.get("role") == "assistant":
            ps = m.get("passos") or []
            tem_texto = False
            for p in ps:
                if not isinstance(p, dict):
                    continue
                if p.get("tipo") == "texto":
                    tem_texto = True
                if p.get("tipo") not in ("texto", "ferramenta"):
                    continue
                p["midias"] = _ainda_valem(p["midias"]) if "midias" in p else do_passo(p)
                if not p["midias"]:
                    p.pop("midias", None)
            if not tem_texto and m.get("content"):
                mm = detectar_permitidas(str(m.get("content")))
                if mm:
                    m["midias"] = mm
        elif m.get("role") == "ferramenta":
            try:
                t = json.dumps(m.get("saida"), ensure_ascii=False, default=str)
            except Exception:
                t = ""
            mm = detectar_permitidas(t)
            if mm:
                m["midias"] = mm
    return msgs


# ================================================================ pastas permitidas
_raizes_cache = {"chave": None, "quando": 0.0, "valor": None}
_trava_raizes = threading.Lock()


def _largas():
    """Pastas que NUNCA viram raiz: a casa do usuário e as gavetas de cima.
    Se o body do projeto está solto em Downloads, servir Downloads inteiro
    seria abrir a gaveta toda."""
    casa = os.path.realpath(os.path.expanduser("~"))
    xs = {os.path.realpath(os.sep), casa}
    for d in ("Documents", "Desktop", "Downloads", "Movies", "Pictures", "Music",
              "Library", "Public", "Documentos", "Área de Trabalho", "Videos", "Vídeos"):
        xs.add(os.path.join(casa, d))
    p = casa
    while True:                      # os pais da casa (/Users, C:\Users)
        pai = os.path.dirname(p)
        if pai == p:
            break
        xs.add(pai)
        p = pai
    return xs


def _temporaria(p):
    rp = os.path.realpath(p)
    for t in {tempfile.gettempdir(), "/tmp", "/private/tmp", "/var/tmp", "/private/var/folders"}:
        try:
            rt = os.path.realpath(t)
        except Exception:
            continue
        if rp == rt or rp.startswith(rt + os.sep):
            return True
    return False


def larga_demais(p):
    rp = os.path.realpath(os.path.expanduser(p))
    if rp in _largas():
        return True
    partes = [x for x in rp.split(os.sep) if x]
    if sys.platform == "darwin" and len(partes) <= 2 and partes[:1] == ["Volumes"]:
        return True                  # raiz de um disco montado
    if os.name == "nt" and len(partes) <= 1:
        return True                  # C:\
    return False


def _destinos_escolhidos():
    try:
        with open(os.path.join(conversas.CASA, "pastas-de-projeto.json"), encoding="utf-8") as f:
            xs = json.load(f)
        return [x for x in xs if isinstance(x, str)]
    except Exception:
        return []


def lembrar_destino(pasta):
    xs = _destinos_escolhidos()
    if pasta not in xs:
        xs.append(pasta)
        destino = os.path.join(conversas.CASA, "pastas-de-projeto.json")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        tmp = destino + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(xs[-200:], f, ensure_ascii=False)
        os.replace(tmp, destino)
    esquecer_raizes()


def esquecer_raizes():
    with _trava_raizes:
        _raizes_cache["valor"] = None


def raizes():
    """(raízes do app, raízes de job). As do app servem qualquer arquivo
    (mosaico do QC, anexo); as de job só servem mídia."""
    chave = (projetos.RAIZ, conversas.RAIZ, getattr(conversas, "CASA", ""))
    with _trava_raizes:
        if (_raizes_cache["valor"] is not None and _raizes_cache["chave"] == chave
                and time.time() - _raizes_cache["quando"] < 5):
            return _raizes_cache["valor"]
    app_ = [os.path.realpath(projetos.RAIZ), os.path.realpath(conversas.RAIZ)]
    job = []
    try:
        pids = os.listdir(projetos.RAIZ) if os.path.isdir(projetos.RAIZ) else []
    except OSError:
        pids = []
    for pid in pids:
        try:
            with open(projetos.caminho(pid, "plano.json"), encoding="utf-8") as f:
                body = ((json.load(f).get("fonte") or {}).get("body")) or ""
        except Exception:
            continue
        if body:
            job.append(os.path.dirname(os.path.expanduser(body)))
    job += _destinos_escolhidos()
    finais = []
    for r in job:
        try:
            rr = os.path.realpath(r)
        except Exception:
            continue
        if rr and not larga_demais(rr) and not _temporaria(rr) and rr not in finais:
            finais.append(rr)
    valor = (app_, finais)
    with _trava_raizes:
        _raizes_cache.update(chave=chave, quando=time.time(), valor=valor)
    return valor


def _dentro(alvo, raiz):
    return alvo == raiz or alvo.startswith(raiz.rstrip(os.sep) + os.sep)


def permitido(caminho, so_midia=False):
    """O caminho pode ser servido? realpath ANTES de comparar (symlink e `..`
    não escapam); tem que ser arquivo; dentro das pastas do app vale qualquer
    arquivo (exceto com `so_midia`), na pasta de job só mídia."""
    if not caminho or not isinstance(caminho, str) or "\x00" in caminho:
        return False
    try:
        alvo = os.path.realpath(os.path.expanduser(caminho))
    except Exception:
        return False
    if not os.path.isfile(alvo):
        return False
    app_, job = raizes()
    eh_midia = bool(tipo_de(alvo))
    if any(_dentro(alvo, r) and alvo != r for r in app_):
        return eh_midia or not so_midia
    if eh_midia and any(_dentro(alvo, r) and alvo != r for r in job):
        return True
    return False


# ================================================================ destino do download
def destino_da_conversa(cid):
    """A pasta de projeto onde as entregas desta conversa são gravadas, ou
    None quando a conversa ainda não tem projeto (aí a tela PERGUNTA)."""
    if not cid:
        return None
    m = conversas.meta(cid)
    pid = m.get("projeto")
    if pid and os.path.isdir(projetos.dir_projeto(pid)):
        return {"pasta": projetos.dir_projeto(pid), "projeto": pid,
                "nome": _nome_projeto(pid)}
    pasta = m.get("pasta_projeto")
    if pasta and os.path.isdir(pasta) and not larga_demais(pasta) and not _temporaria(pasta):
        return {"pasta": pasta, "projeto": None, "nome": os.path.basename(pasta.rstrip(os.sep))}
    return None


def _nome_projeto(pid):
    try:
        return projetos.ler(pid)["plano"].get("job") or pid
    except Exception:
        return pid


def projetos_para_escolher():
    try:
        return [{"id": p["id"], "nome": p["nome"]} for p in projetos.listar()][:30]
    except Exception:
        return []


def pasta_valida_para_projeto(pasta):
    """Pasta escolhida pelo usuário para guardar as entregas. Recusa as que a
    regra proíbe: temporária, Downloads, Mesa, a casa inteira, pasta de conversa."""
    if not pasta:
        return "Nenhuma pasta escolhida."
    rp = os.path.realpath(os.path.expanduser(pasta))
    if not os.path.isdir(rp):
        return "Essa pasta não existe."
    if _temporaria(rp):
        return "Pasta temporária é limpa sem aviso — escolha a pasta do projeto."
    if larga_demais(rp):
        return "Escolha a pasta do PROJETO, não uma pasta geral como Downloads, Mesa ou Documentos."
    if _dentro(rp, os.path.realpath(conversas.RAIZ)):
        return "A pasta da conversa não é pasta de projeto — escolha a pasta do job."
    return None


# ================================================================ download
class ErroBaixar(Exception):
    pass


class _SoHttp(urllib.request.HTTPRedirectHandler):
    """Redireciona só para http(s) — o padrão do urllib aceitaria ftp."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).scheme.lower() not in ("http", "https"):
            raise ErroBaixar("Redirecionamento para fora de http(s) recusado.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _abrir(url, timeout):
    handlers = [_SoHttp()]
    try:
        from . import rede
        handlers.append(urllib.request.HTTPSHandler(context=rede.contexto()))
    except Exception:
        pass
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": "EditorAutomatico/1.0"})
    return opener.open(req, timeout=timeout)


def _farejar(inicio):
    """A extensão pelo conteúdo: a miniatura `.jpg` do Higgsfield era webp."""
    if inicio[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if inicio[:3] == b"\xff\xd8\xff":
        return "jpg"
    if inicio[:4] == b"RIFF" and inicio[8:12] == b"WEBP":
        return "webp"
    if inicio[:4] == b"RIFF" and inicio[8:12] == b"WAVE":
        return "wav"
    if inicio[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return None


def _nome_base(url):
    b = os.path.splitext(os.path.basename(urllib.parse.urlparse(url).path))[0]
    b = urllib.parse.unquote(b)
    b = "".join(c if (c.isalnum() or c in "-_") else "-" for c in b).strip("-")[:48]
    return b or "entrega"


_travas_url = {}
_trava_geral = threading.Lock()


def _registro(pasta):
    return os.path.join(pasta, "media", ".entregas.json")


def _ler_registro(pasta):
    try:
        with open(_registro(pasta), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _gravar_registro(pasta, d):
    destino = _registro(pasta)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, destino)


def baixar(url, pasta_projeto, tipo=None, limite=LIMITE_BAIXAR, timeout=60):
    """Baixa UMA entrega para `<pasta_projeto>/media/<tipo>/`.

    - só http(s), inclusive nos redirecionamentos;
    - nome estável (o mesmo link cai sempre no mesmo arquivo) e registro em
      `media/.entregas.json`: o segundo pedido devolve o que já está no disco;
    - teto de tamanho, conferido no Content-Length E durante a leitura;
    - grava em `.parte` DENTRO da pasta do projeto e só renomeia no fim:
      download interrompido não deixa arquivo pela metade com nome de pronto;
    - o destino final é conferido com realpath: nunca sai da pasta do projeto.
    Devolve {"caminho", "tipo", "ja_tinha"}."""
    u = (url or "").strip()
    pu = urllib.parse.urlparse(u)
    if pu.scheme.lower() not in ("http", "https") or not pu.netloc:
        raise ErroBaixar("Só baixo entrega por http ou https.")
    if not pasta_projeto or not os.path.isdir(pasta_projeto):
        raise ErroBaixar("A pasta do projeto não existe.")
    raiz = os.path.realpath(pasta_projeto)
    chave = hashlib.sha1(_chave_url(u).encode("utf-8")).hexdigest()[:12]

    with _trava_geral:
        trava = _travas_url.setdefault((raiz, chave), threading.Lock())
    with trava:
        reg = _ler_registro(raiz)
        if chave in reg:
            ja = os.path.join(raiz, reg[chave])
            if os.path.isfile(ja) and _dentro(os.path.realpath(ja), raiz):
                return {"caminho": ja, "tipo": tipo_de(ja), "ja_tinha": True}
        try:
            r = _abrir(u, timeout)
        except ErroBaixar:
            raise
        except Exception as e:
            raise ErroBaixar("Não consegui baixar a entrega: %s" % (str(e)[:160] or e.__class__.__name__))
        with r:
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype.startswith("text/html"):
                raise ErroBaixar("O link devolveu uma página, não a mídia (expirou?).")
            try:
                n = int(r.headers.get("Content-Length") or 0)
            except ValueError:
                n = 0
            if n and n > limite:
                raise ErroBaixar("A entrega tem %d MB — acima do limite de %d MB."
                                 % (n // 2 ** 20, limite // 2 ** 20))
            inicio = r.read(65536)
            ext = (_farejar(inicio) or (ext_de(u) if ext_de(u) in TIPO_EXT else None)
                   or EXT_DO_MIME.get(ctype))
            if ext == "jpeg":
                ext = "jpg"
            t = TIPO_EXT.get(ext or "")
            if not t:
                raise ErroBaixar("Isso não parece imagem, vídeo nem áudio (%s)." % (ctype or "sem tipo"))
            pasta = os.path.join(raiz, "media", PASTA_TIPO[t])
            os.makedirs(pasta, exist_ok=True)
            final = os.path.join(pasta, "%s-%s.%s" % (_nome_base(u), chave[:8], ext))
            if not _dentro(os.path.realpath(os.path.dirname(final)), raiz):
                raise ErroBaixar("Destino fora da pasta do projeto recusado.")
            parte = final + ".parte"
            total = 0
            try:
                with open(parte, "wb") as f:
                    bloco = inicio
                    while bloco:
                        total += len(bloco)
                        if total > limite:
                            raise ErroBaixar("A entrega passou do limite de %d MB." % (limite // 2 ** 20))
                        f.write(bloco)
                        bloco = r.read(1024 * 1024)
                if n and total < n:
                    raise ErroBaixar("O download foi interrompido (%d de %d bytes)." % (total, n))
                os.replace(parte, final)
            finally:
                if os.path.exists(parte):
                    try:
                        os.remove(parte)
                    except OSError:
                        pass
        reg = _ler_registro(raiz)
        reg[chave] = os.path.relpath(final, raiz)
        _gravar_registro(raiz, reg)
        return {"caminho": final, "tipo": t, "ja_tinha": False}


# ================================================================ ffprobe / ffmpeg
_info_cache = {}


def _assinatura(caminho):
    st = os.stat(caminho)
    return "%s|%d|%d" % (os.path.realpath(caminho), int(st.st_mtime), st.st_size)


def info(caminho):
    """Tipo, dimensões (já com a rotação do celular aplicada), duração e
    tamanho. Em cache pela assinatura do arquivo (caminho + data + tamanho)."""
    ass = _assinatura(caminho)
    if ass in _info_cache:
        return dict(_info_cache[ass])
    d = {"tipo": tipo_de(caminho), "nome": os.path.basename(caminho),
         "tamanho": os.path.getsize(caminho), "largura": None, "altura": None,
         "duracao": None}
    try:
        r = so.run(["ffprobe", "-v", "error", "-show_entries",
                    "stream=codec_type,width,height,duration:stream_tags=rotate:"
                    "stream_side_data=rotation:format=duration",
                    "-of", "json", caminho], capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout or "{}")
        sts = j.get("streams") or []
        v = next((s for s in sts if s.get("codec_type") == "video"), None)
        if v:
            w, h = v.get("width"), v.get("height")
            rot = 0
            try:
                rot = int(float((v.get("tags") or {}).get("rotate") or 0))
            except ValueError:
                rot = 0
            for sd in v.get("side_data_list") or []:
                if "rotation" in sd:
                    try:
                        rot = int(float(sd["rotation"]))
                    except (TypeError, ValueError):
                        pass
            if abs(rot) % 180 == 90:
                w, h = h, w
            d["largura"], d["altura"] = w, h
        dur = (j.get("format") or {}).get("duration")
        if dur not in (None, "N/A") and d["tipo"] != "imagem":
            d["duracao"] = round(float(dur), 3)
        d["tem_audio"] = any(s.get("codec_type") == "audio" for s in sts)
    except Exception as e:
        d["aviso"] = "ffprobe indisponível: %s" % (str(e)[:80])
    _info_cache[ass] = dict(d)
    return d


def _cache(sub, ass, ext):
    pasta = os.path.join(CACHE, sub)
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, hashlib.sha1(ass.encode("utf-8")).hexdigest()[:24] + ext)


TAXA_PICOS = 4000


def picos(caminho, n=96):
    """A forma da onda: `n` picos de 0 a 1. O ffmpeg decodifica para PCM mono
    em 4 kHz (sobra para desenhar; 10 min de áudio são 4,8 MB), o máximo
    absoluto de cada fatia vira uma barra. Em cache no disco."""
    n = max(16, min(int(n or 96), 400))
    ass = _assinatura(caminho) + "|%d" % n
    arq = _cache("picos", ass, ".json")
    try:
        with open(arq, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        pass
    r = so.run(["ffmpeg", "-v", "error", "-i", caminho, "-vn", "-ac", "1", "-ar", str(TAXA_PICOS),
                "-f", "s16le", "-"], capture_output=True, timeout=120)
    if r.returncode != 0 and not r.stdout:
        raise RuntimeError("Não consegui ler o áudio: %s"
                           % (r.stderr or b"").decode("utf-8", "replace")[-160:])
    amostras = array("h")
    dados = r.stdout[: len(r.stdout) // 2 * 2]
    amostras.frombytes(dados)
    if sys.byteorder != "little":
        amostras.byteswap()
    total = len(amostras)
    barras = []
    if total:
        passo = total / n
        for i in range(n):
            a, b = int(i * passo), max(int((i + 1) * passo), int(i * passo) + 1)
            fatia = amostras[a:b]
            barras.append(max((abs(x) for x in fatia), default=0))
    topo = max(barras) if barras and max(barras) else 1
    d = {"picos": [round(x / topo, 3) for x in barras] or [0] * n,
         "duracao": round(total / TAXA_PICOS, 3)}
    tmp = arq + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, arq)
    return d


def quadro(caminho, largura=480):
    """Miniatura JPEG: a imagem reduzida, ou o PRIMEIRO quadro do vídeo (a
    capa do player). O WebKit do app não mostra o 1º quadro com
    `preload="metadata"` — sem capa, o player fica preto. Em cache no disco.
    None quando o ffmpeg não consegue (a tela usa o arquivo original)."""
    largura = max(64, min(int(largura or 480), 1600))
    ass = _assinatura(caminho) + "|q%d" % largura
    arq = _cache("quadros", ass, ".jpg")
    if os.path.isfile(arq) and os.path.getsize(arq) > 0:
        return arq
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if tipo_de(caminho) == "video":
        cmd += ["-ss", "0"]
    cmd += ["-i", caminho, "-frames:v", "1", "-vf",
            "scale='min(%d,iw)':-2" % largura, "-q:v", "4", arq + ".tmp.jpg"]
    try:
        r = so.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and os.path.isfile(arq + ".tmp.jpg"):
            os.replace(arq + ".tmp.jpg", arq)
            return arq
    except Exception:
        pass
    try:
        os.remove(arq + ".tmp.jpg")
    except OSError:
        pass
    return None


# ================================================================ sistema
def mostrar(caminho):
    """"Mostrar no Finder" / "Mostrar na pasta" — só para caminho permitido."""
    if not permitido(caminho):
        raise PermissionError("Esse arquivo está fora das pastas do projeto.")
    alvo = os.path.realpath(caminho)
    if so.WIN:
        # explorer devolve 1 mesmo quando abre; não dá para usar o código de saída
        subprocess.Popen('explorer /select,"%s"' % alvo, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    if so.MAC:
        return subprocess.run(["open", "-R", alvo], capture_output=True, timeout=15).returncode == 0
    return subprocess.run(["xdg-open", os.path.dirname(alvo)], capture_output=True, timeout=15).returncode == 0


def escolher_pasta(titulo="Em qual pasta de projeto salvar as entregas?"):
    """Abre o seletor de pasta do sistema (o app pode estar sem janela, no
    modo serviço do painel, por isso não é o diálogo do pywebview).
    Devolve o caminho ou None se a pessoa cancelar."""
    if so.MAC:
        script = 'POSIX path of (choose folder with prompt "%s")' % titulo.replace('"', "'")
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
        p = (r.stdout or "").strip()
        if r.returncode == 0 and p:
            return p.rstrip("/") or "/"
        return None
    if so.WIN:
        ps = ("Add-Type -AssemblyName System.Windows.Forms;"
              "$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
              "$d.Description='%s';"
              "if($d.ShowDialog() -eq 'OK'){[Console]::Out.Write($d.SelectedPath)}" % titulo.replace("'", ""))
        r = so.run(["powershell", "-NoProfile", "-STA", "-Command", ps],
                   capture_output=True, text=True, timeout=600)
        return (r.stdout or "").strip() or None
    return None
