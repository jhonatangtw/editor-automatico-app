#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decupar.py — Decupagem de VSL / vídeo longo QUADRO A QUADRO, por plano.

Em vez de "N quadros espalhados", detecta cada CORTE de cena e tira um quadro em
alta de cada plano. Planos longos (talking head parado) ganham quadros de
cobertura a cada X segundos, para nada ficar sem amostra. Cada quadro sai com:
  - timecode e motivo (CORTE / COBERTURA / TEMPO pedido)
  - a FALA daquele trecho (legenda .vtt/.srt, transcrição [hh:mm:ss] ou Whisper)
  - o TEXTO NA TELA (OCR com tesseract — pega lettering, rótulos, preços)

USO
  python3 decupar.py <video.mp4 | URL do YouTube> [opções]

  --modo auto|cenas|intervalo|tempos   (padrão: auto = cortes + cobertura)
  --intervalo 5        segundos entre quadros no modo intervalo (padrão 5)
  --cobertura 12       no modo auto: no máximo X s sem quadro dentro de um plano
  --tempos "0:35,1:01,442"   timestamps extras (somam a qualquer modo)
  --sensibilidade 1.0  >1 pega mais cortes, <1 pega menos
  --max 900            teto de quadros
  --legenda arq        .vtt / .srt / .txt com [hh:mm:ss] (fala alinhada ao quadro)
  --transcrever        sem legenda: roda faster-whisper (--modelo small --idioma por|eng)
  --ocr                lê o texto na tela de cada quadro (tesseract; --ocr-idioma eng+por)
  --largura 1280       largura dos quadros salvos
  --por-folha 20       quadros por folha de contato (4 colunas)
  -o pasta             saída (padrão: <video>_DECUPAGEM ao lado do vídeo)
  --jobs 4             paralelismo da extração/OCR

SAÍDA (<saida>/)
  frames/0001_00m35s.jpg   quadros em alta
  folhas/folha_01.jpg      folhas de contato com timecode + motivo (para o Claude ler)
  decupagem.html           página navegável: quadro + fala + texto na tela
  decupagem.md             tabela enxuta (timecode | motivo | fala | tela)
  decupagem.json / .csv    dados completos
  legenda.vtt              (só quando veio de URL)

Requisitos: ffmpeg/ffprobe. Opcionais: pillow (folhas com rótulo), numpy (corte
mais rápido), tesseract (--ocr), yt-dlp (URL), faster-whisper (--transcrever).
"""
import argparse, csv, html, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor


# ---------------------------------------------------------------- util
def run(cmd, timeout=None, binary=False):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = p.stdout if binary else p.stdout.decode("utf-8", "replace")
    return p.returncode, out, p.stderr.decode("utf-8", "replace")


def tc(t, ms=False):
    t = max(0.0, float(t))
    h, r = divmod(int(t), 3600)
    m, s = divmod(r, 60)
    base = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    return base + (f".{int((t - int(t)) * 10)}" if ms else "")


def parse_tempo(s):
    s = s.strip()
    if not s:
        return None
    if ":" in s:
        parts = [float(x) for x in s.split(":")]
        v = 0.0
        for p in parts:
            v = v * 60 + p
        return v
    return float(s)


def need(binname):
    if not shutil.which(binname):
        sys.exit(f"ERRO: '{binname}' não encontrado no PATH. Instale antes (ver references/setup.md).")


# ---------------------------------------------------------------- entrada
def baixar_url(url, pasta):
    """Baixa o vídeo e, em separado, a legenda. Falha na legenda não derruba o vídeo
    (o YouTube devolve 429 nas legendas traduzidas automaticamente)."""
    need("yt-dlp")
    os.makedirs(pasta, exist_ok=True)
    print("→ Baixando vídeo (até 720p)...")
    rc, out, err = run(["yt-dlp", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b",
                        "--merge-output-format", "mp4", "--no-write-subs", "--no-playlist",
                        "--print", "after_move:filepath", "--no-simulate",
                        "-o", os.path.join(pasta, "video.%(ext)s"), url])
    linhas = [l for l in out.strip().splitlines() if l.strip()]
    caminho = linhas[-1] if linhas else ""
    if not os.path.isfile(caminho):
        sys.exit("ERRO no yt-dlp ao baixar o vídeo:\n" + err[-800:])
    print("→ Baixando legenda (original primeiro, sem traduções automáticas)...")
    run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--ignore-errors",
         "--no-playlist", "--sub-format", "vtt",
         "--sub-langs", "pt-BR,pt,pt-orig,en,en-orig,es,es-orig",
         "-o", os.path.join(pasta, "video.%(ext)s"), url])
    vtts = sorted(f for f in os.listdir(pasta) if f.endswith(".vtt"))
    escolha = None
    for pref in ("pt-BR.vtt", "pt.vtt", "en.vtt", "es.vtt", "pt-orig.vtt", "en-orig.vtt", "es-orig.vtt"):
        escolha = escolha or next((f for f in vtts if f.endswith("." + pref)), None)
    escolha = escolha or (vtts[0] if vtts else None)
    if not escolha:
        print("  ! Sem legenda disponível — rode com --transcrever para ter a fala.")
        return caminho, None
    leg = os.path.join(pasta, "legenda.vtt")
    shutil.copy(os.path.join(pasta, escolha), leg)
    print(f"  legenda: {escolha}")
    return caminho, leg


def probe(path):
    rc, out, _ = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                      "-show_streams", path])
    if rc != 0:
        sys.exit(f"ERRO: ffprobe não conseguiu ler {path}")
    j = json.loads(out)
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    dur = float(j.get("format", {}).get("duration") or v.get("duration") or 0)
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0
    return {"dur": dur, "w": v.get("width", 0), "h": v.get("height", 0), "fps": round(fps, 2),
            "codec": v.get("codec_name", "?")}


# ---------------------------------------------------------------- cortes
def diffs_do_video(path, fps_amostra=4, w=96, h=54):
    """Decodifica o vídeo inteiro em cinza pequeno e devolve [(t, diff 0-1)].
    Feito em Python (não usa o filtro scene do ffmpeg, que falha em alguns VP9)."""
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-an",
           "-vf", f"fps={fps_amostra},scale={w}:{h},format=gray", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tam = w * h
    try:
        import numpy as np
    except Exception:
        np = None
    prev, i, res = None, 0, []
    while True:
        buf = p.stdout.read(tam)
        if len(buf) < tam:
            break
        if np is not None:
            cur = np.frombuffer(buf, dtype=np.uint8).astype(np.int16)
            if prev is not None:
                res.append((i / fps_amostra, float(np.abs(cur - prev).mean()) / 255.0))
        else:
            cur = buf
            if prev is not None:
                res.append((i / fps_amostra, sum(abs(a - b) for a, b in zip(cur, prev)) / tam / 255.0))
        prev, i = cur, i + 1
    p.wait()
    return res


def detectar_cortes(diffs, sensibilidade=1.0, min_gap=0.8):
    """Corte = pico de diferença bem acima da vizinhança (limiar adaptativo)."""
    if not diffs:
        return []
    vals = [d for _, d in diffs]
    cortes, last = [], -1e9
    janela = 12  # ~3 s a 4 fps
    for k, (t, d) in enumerate(diffs):
        viz = sorted(vals[max(0, k - janela):k] + vals[k + 1:k + 1 + janela]) or [0]
        mediana = viz[len(viz) // 2]
        limiar = max(0.06, mediana * 3.0 + 0.04) / max(sensibilidade, 0.1)
        eh_pico = d >= max(vals[max(0, k - 1):k + 2])
        if d > limiar and eh_pico and t - last >= min_gap:
            cortes.append((t, d))
            last = t
    return cortes


def planejar(info, modo, cortes, intervalo, cobertura, extras, teto):
    dur = info["dur"]
    pts = []  # (t, motivo, score)
    if modo == "intervalo":
        t = 0.5
        while t < dur:
            pts.append((t, "INTERVALO", 0)); t += intervalo
    elif modo in ("auto", "cenas"):
        inicios = [0.0] + [c for c, _ in cortes]
        scores = [1.0] + [s for _, s in cortes]
        for j, ini in enumerate(inicios):
            fim = inicios[j + 1] if j + 1 < len(inicios) else dur
            plano = fim - ini
            # quadro do plano: já assentado depois do corte (evita a fusão da transição)
            t0 = ini + min(0.4, plano / 2)
            pts.append((t0, "CORTE" if j else "INICIO", round(scores[j], 3)))
            if modo == "auto" and plano > cobertura:
                n = int(plano // cobertura)
                passo = plano / (n + 1)
                for q in range(1, n + 1):
                    pts.append((ini + passo * q, "COBERTURA", 0))
    for t in extras:
        if 0 <= t < dur:
            pts.append((t, "TEMPO", 0))
    pts.sort()
    # junta quadros a menos de 0.5 s (fica o de motivo mais forte)
    prio = {"TEMPO": 3, "CORTE": 2, "INICIO": 2, "COBERTURA": 1, "INTERVALO": 1}
    limpo = []
    for p in pts:
        if limpo and p[0] - limpo[-1][0] < 0.5:
            if prio[p[1]] > prio[limpo[-1][1]]:
                limpo[-1] = p
            continue
        limpo.append(p)
    if len(limpo) > teto:  # corta coberturas primeiro, mantendo distribuição
        fixos = [p for p in limpo if p[1] != "COBERTURA"]
        cob = [p for p in limpo if p[1] == "COBERTURA"]
        sobra = max(0, teto - len(fixos))
        cob = cob[::max(1, len(cob) // sobra)][:sobra] if sobra else []
        limpo = sorted(fixos + cob)
        if len(limpo) > teto:
            passo = len(limpo) / teto
            limpo = [limpo[int(i * passo)] for i in range(teto)]
    return limpo


# ---------------------------------------------------------------- extração
def extrair(path, t, out_jpg, largura):
    rc, _, _ = run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", path,
                    "-frames:v", "1", "-vf", f"scale='min({largura},iw)':-2", "-q:v", "2",
                    out_jpg, "-y"], timeout=60)
    return rc == 0 and os.path.isfile(out_jpg)


def ocr(jpg, idioma, conf_min=70):
    """Texto na tela com filtro de confiança do tesseract (tira o ruído de textura)."""
    if not shutil.which("tesseract"):
        return ""
    rc, out, _ = run(["tesseract", jpg, "-", "-l", idioma, "--psm", "11", "tsv"], timeout=90)
    if rc != 0:
        rc, out, _ = run(["tesseract", jpg, "-", "--psm", "11", "tsv"], timeout=90)
    palavras = []
    for linha in out.splitlines()[1:]:
        c = linha.split("\t")
        if len(c) < 12:
            continue
        try:
            conf = float(c[10])
        except ValueError:
            continue
        tok = c[11].strip().strip("|·•—-_~=*.,;:'\"")
        if conf < conf_min or not tok:
            continue
        letras = sum(ch.isalpha() for ch in tok)
        numero = re.fullmatch(r"[$€]?\d[\d.,]*[%kKmMbB]?", tok)
        if numero or (letras >= 3 and letras / len(tok) >= 0.7):
            palavras.append(tok)
    return " ".join(palavras)[:300]


# ---------------------------------------------------------------- fala
def ler_legenda(path):
    """Devolve [(ini, fim, texto)] de .vtt, .srt ou .txt com [hh:mm:ss]."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    segs = []
    rx = re.compile(r"(\d+:)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(\d+:)?(\d{1,2}):(\d{2})[.,](\d{3})")
    if rx.search(txt):
        def sec(h, m, s, ms):
            return int((h or "0:")[:-1] or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        blocos = re.split(r"\n\s*\n", txt)
        vistos = set()
        for b in blocos:
            m = rx.search(b)
            if not m:
                continue
            ini = sec(*m.group(1, 2, 3, 4)); fim = sec(*m.group(5, 6, 7, 8))
            corpo = b[m.end():]
            linhas = [re.sub(r"<[^>]+>", "", l).strip() for l in corpo.splitlines()]
            for l in linhas:
                l = html.unescape(l).replace("&nbsp;", " ").strip()
                if not l or l in vistos or re.match(r"^(align|position):", l):
                    continue
                vistos.add(l)  # legenda automática repete a linha rolando
                segs.append((ini, fim, l))
    else:
        for l in txt.splitlines():
            m = re.match(r"\s*\[?(\d+:)?(\d{1,2}):(\d{2})(?:\.\d+)?\]?\s*(.*)", l)
            if m and m.group(4).strip():
                t = int((m.group(1) or "0:")[:-1] or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                segs.append((t, t, html.unescape(m.group(4).strip())))
        for k in range(len(segs) - 1):
            segs[k] = (segs[k][0], segs[k + 1][0], segs[k][2])
    segs.sort(key=lambda x: x[0])
    return [(a, segs[k + 1][0] if k + 1 < len(segs) else b, t) for k, (a, b, t) in enumerate(segs)]


def transcrever(path, modelo, idioma):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        print("  ! faster-whisper não instalado — sem fala. pip install faster-whisper")
        return []
    print(f"→ Transcrevendo com Whisper ({modelo}) — vídeo longo demora...")
    wav = tempfile.mktemp(suffix=".wav")
    run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav, "-y"])
    lang = {"por": "pt", "eng": "en", "spa": "es"}.get(idioma, idioma) or None
    model = WhisperModel(modelo, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(wav, language=lang, beam_size=1, vad_filter=True)
    res = [(s.start, s.end, s.text.strip()) for s in segs]
    os.remove(wav)
    return res


def fala_do_trecho(segs, ini, fim):
    """Trechos que começam dentro do plano; se nenhum, o que está sendo falado no início."""
    partes = [t for a, b, t in segs if ini <= a < fim]
    if not partes:
        partes = [t for a, b, t in segs if a < ini < b][:1]
    return re.sub(r"\s+", " ", " ".join(partes)).strip()


# ---------------------------------------------------------------- folhas
def montar_folhas(itens, pasta, por_folha, titulo):
    os.makedirs(pasta, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return montar_folhas_ffmpeg(itens, pasta, por_folha)
    cores = {"CORTE": (255, 196, 0), "INICIO": (255, 196, 0), "COBERTURA": (150, 160, 175),
             "INTERVALO": (150, 160, 175), "TEMPO": (90, 200, 255)}
    try:
        fonte = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
        fonte_p = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    except Exception:
        try:
            fonte = ImageFont.truetype("arialbd.ttf", 22); fonte_p = ImageFont.truetype("arial.ttf", 18)
        except Exception:
            fonte = fonte_p = ImageFont.load_default()
    cols, tw = 4, 400
    saidas = []
    for f0 in range(0, len(itens), por_folha):
        lote = itens[f0:f0 + por_folha]
        thumbs = []
        for it in lote:
            im = Image.open(it["arquivo_abs"]).convert("RGB")
            th = int(im.height * tw / im.width)
            thumbs.append(im.resize((tw, th)))
        th = max(t.height for t in thumbs)
        rows = (len(thumbs) + cols - 1) // cols
        pad, cab = 8, 46
        folha = Image.new("RGB", (cols * tw + pad * (cols + 1), cab + rows * (th + pad) + pad), (17, 19, 24))
        d = ImageDraw.Draw(folha)
        n_folha = f0 // por_folha + 1
        d.text((pad + 4, 12), f"{titulo}  ·  folha {n_folha}  ·  quadros {lote[0]['n']}–{lote[-1]['n']}  "
               f"({lote[0]['timecode']} → {lote[-1]['timecode']})", fill=(235, 235, 240), font=fonte)
        for i, (it, im) in enumerate(zip(lote, thumbs)):
            r, c = divmod(i, cols)
            x, y = pad + c * (tw + pad), cab + r * (th + pad)
            folha.paste(im, (x, y))
            rot = f"#{it['n']} {it['timecode']}"
            d.rectangle([x, y, x + 9 + int(d.textlength(rot, font=fonte)), y + 30], fill=(0, 0, 0))
            d.text((x + 5, y + 4), rot, fill=cores.get(it["motivo"], (255, 255, 255)), font=fonte)
            mot = it["motivo"]
            wm = int(d.textlength(mot, font=fonte_p))
            d.rectangle([x + tw - wm - 12, y, x + tw, y + 26], fill=(0, 0, 0))
            d.text((x + tw - wm - 6, y + 4), mot, fill=cores.get(mot, (255, 255, 255)), font=fonte_p)
        out = os.path.join(pasta, f"folha_{n_folha:02d}.jpg")
        folha.save(out, quality=84)
        saidas.append(out)
    return saidas


def montar_folhas_ffmpeg(itens, pasta, por_folha):
    saidas = []
    for f0 in range(0, len(itens), por_folha):
        lote = itens[f0:f0 + por_folha]
        tmp = tempfile.mkdtemp()
        for i, it in enumerate(lote):
            shutil.copy(it["arquivo_abs"], os.path.join(tmp, f"{i:03d}.jpg"))
        rows = (len(lote) + 3) // 4
        out = os.path.join(pasta, f"folha_{f0 // por_folha + 1:02d}.jpg")
        run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", os.path.join(tmp, "%03d.jpg"),
             "-vf", f"scale=400:-2,tile=4x{rows}:padding=8:margin=8:color=0x111318",
             "-frames:v", "1", "-q:v", "3", out, "-y"])
        shutil.rmtree(tmp, ignore_errors=True)
        saidas.append(out)
    return saidas


# ---------------------------------------------------------------- relatórios
def escrever_html(itens, info, titulo, saida, stats, video):
    """Página interativa: player + linha do tempo + quadros (modelo em pagina.html)."""
    modelo = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pagina.html"), encoding="utf-8").read()
    try:
        rel = os.path.relpath(video, os.path.dirname(saida)) if video else ""
    except ValueError:  # Windows: vídeo em outra unidade (D:\ x C:\)
        rel = "file:///" + os.path.abspath(video).replace(os.sep, "/")
    dados = {"titulo": titulo, "stats": stats, "video": rel.replace(os.sep, "/"),
             "info": info, "quadros": [{k: it[k] for k in ("n", "t", "timecode", "ate", "motivo",
                                                           "fala", "texto_tela", "arquivo")} for it in itens]}
    js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    doc = modelo.replace("__TITULO__", html.escape(titulo)).replace("__DADOS__", js)
    open(saida, "w", encoding="utf-8").write(doc)


def escrever_md(itens, info, titulo, saida, stats, folhas):
    L = [f"# Decupagem quadro a quadro — {titulo}", "",
         f"Duração {tc(info['dur'])} · {info['w']}×{info['h']} · {stats}", "",
         "Folhas de contato (ler em ordem): " + ", ".join(os.path.basename(f) for f in folhas), "",
         "| # | Timecode | Motivo | Fala do trecho | Texto na tela |", "|---|---|---|---|---|"]
    for it in itens:
        cel = lambda s: (s or "").replace("|", "/")[:220]
        L.append(f"| {it['n']} | {it['timecode']}–{it['ate']} | {it['motivo']} | {cel(it['fala'])} | {cel(it['texto_tela'])} |")
    open(saida, "w", encoding="utf-8").write("\n".join(L) + "\n")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Decupagem de VSL quadro a quadro, por plano.")
    ap.add_argument("entrada")
    ap.add_argument("-o", "--saida")
    ap.add_argument("--modo", default="auto", choices=["auto", "cenas", "intervalo", "tempos"])
    ap.add_argument("--intervalo", type=float, default=5.0)
    ap.add_argument("--cobertura", type=float, default=12.0)
    ap.add_argument("--tempos", default="")
    ap.add_argument("--sensibilidade", type=float, default=1.0)
    ap.add_argument("--max", type=int, default=900)
    ap.add_argument("--legenda")
    ap.add_argument("--transcrever", action="store_true")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--idioma", default="")
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--ocr-idioma", default="eng+por")
    ap.add_argument("--largura", type=int, default=1280)
    ap.add_argument("--por-folha", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    need("ffmpeg"); need("ffprobe")

    legenda = a.legenda
    if re.match(r"https?://", a.entrada):
        base = a.saida or os.path.abspath("DECUPAGEM")
        video, leg_url = baixar_url(a.entrada, os.path.join(base, "_fonte"))
        legenda = legenda or leg_url
        saida = base
    else:
        video = os.path.abspath(a.entrada)
        if not os.path.isfile(video):
            sys.exit(f"ERRO: arquivo não encontrado: {video}")
        saida = a.saida or os.path.splitext(video)[0] + "_DECUPAGEM"
    titulo = os.path.splitext(os.path.basename(video))[0]
    os.makedirs(os.path.join(saida, "frames"), exist_ok=True)

    info = probe(video)
    print(f"→ {titulo}: {tc(info['dur'])} · {info['w']}×{info['h']} · {info['codec']}")
    extras = [x for x in (parse_tempo(s) for s in a.tempos.split(",")) if x is not None]

    cortes = []
    if a.modo in ("auto", "cenas"):
        print("→ Detectando cortes de cena (lê o vídeo inteiro)...")
        cortes = detectar_cortes(diffs_do_video(video), a.sensibilidade)
        print(f"  {len(cortes)} cortes")
    modo = a.modo if a.modo != "tempos" else "tempos"
    pts = planejar(info, modo, cortes, a.intervalo, a.cobertura, extras, a.max)
    if not pts:
        sys.exit("Nenhum quadro planejado (no modo tempos, passe --tempos).")
    print(f"→ Extraindo {len(pts)} quadros...")

    itens = []
    for n, (t, motivo, score) in enumerate(pts, 1):
        nome = f"{n:04d}_{int(t // 60):02d}m{int(t % 60):02d}s.jpg"
        itens.append({"n": n, "t": round(t, 2), "timecode": tc(t), "motivo": motivo, "score": score,
                      "arquivo": f"frames/{nome}", "arquivo_abs": os.path.join(saida, "frames", nome)})
    for k, it in enumerate(itens):
        fim = itens[k + 1]["t"] if k + 1 < len(itens) else info["dur"]
        it["ate_s"] = round(fim, 2); it["ate"] = tc(fim)

    with ThreadPoolExecutor(a.jobs) as ex:
        ok = list(ex.map(lambda it: extrair(video, it["t"], it["arquivo_abs"], a.largura), itens))
    itens = [it for it, o in zip(itens, ok) if o]

    segs = []
    if legenda and os.path.isfile(legenda):
        segs = ler_legenda(legenda); print(f"→ Fala: {len(segs)} trechos de {os.path.basename(legenda)}")
    elif a.transcrever:
        segs = transcrever(video, a.modelo, a.idioma)
    for it in itens:
        # tempo pedido avulso: fala dos 15 s seguintes, não até o próximo pedido
        fim = min(it["ate_s"], it["t"] + 15) if it["motivo"] == "TEMPO" else it["ate_s"]
        it["fala"] = fala_do_trecho(segs, it["t"], fim) if segs else ""

    if a.ocr:
        if shutil.which("tesseract"):
            print("→ OCR do texto na tela...")
            with ThreadPoolExecutor(a.jobs) as ex:
                textos = list(ex.map(lambda it: ocr(it["arquivo_abs"], a.ocr_idioma), itens))
        else:
            print("  ! tesseract não instalado — pulando OCR."); textos = [""] * len(itens)
    else:
        textos = [""] * len(itens)
    for it, tx in zip(itens, textos):
        it["texto_tela"] = tx

    print("→ Montando folhas de contato e relatórios...")
    folhas = montar_folhas(itens, os.path.join(saida, "folhas"), a.por_folha, titulo)
    n_c = sum(1 for i in itens if i["motivo"] in ("CORTE", "INICIO"))
    stats = (f"{len(itens)} quadros · {n_c} planos (cortes detectados) · "
             f"{sum(1 for i in itens if i['motivo'] == 'COBERTURA')} de cobertura · "
             f"{sum(1 for i in itens if i['motivo'] == 'TEMPO')} pedidos")
    escrever_html(itens, info, titulo, os.path.join(saida, "decupagem.html"), stats, video)
    escrever_md(itens, info, titulo, os.path.join(saida, "decupagem.md"), stats, folhas)
    pub = [{k: v for k, v in it.items() if k != "arquivo_abs"} for it in itens]
    json.dump({"video": video, "info": info, "cortes": cortes, "quadros": pub},
              open(os.path.join(saida, "decupagem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(saida, "decupagem.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "t", "timecode", "ate", "motivo", "fala", "texto_tela", "arquivo"])
        for it in pub:
            w.writerow([it["n"], it["t"], it["timecode"], it["ate"], it["motivo"], it["fala"],
                        it["texto_tela"], it["arquivo"]])

    print("")
    print("=" * 60)
    print(f"  {stats}")
    print(f"  Página  : {os.path.join(saida, 'decupagem.html')}")
    print(f"  Tabela  : {os.path.join(saida, 'decupagem.md')}")
    print(f"  Folhas  : {os.path.join(saida, 'folhas')}  ({len(folhas)} folhas)")
    print("=" * 60)


if __name__ == "__main__":
    main()
