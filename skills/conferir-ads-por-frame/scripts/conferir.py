#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conferir.py — Ferramenta de terminal para QA (conferência) de criativos de vídeo / ADs.

Roda TODA a parte objetiva da conferência automaticamente e monta um dossiê visual:
  - lê metadados de cada vídeo (duração, resolução, formato, fps, áudio);
  - roda checks automáticos (arquivo quebrado, resolução baixa, formato errado 9:16,
    frame preto, imagem congelada, silêncio / sem áudio, duração fora do padrão);
  - gera um MOSAICO de frames com timecode de cada vídeo (pra bater o olho);
  - (opcional) faz OCR da faixa de legenda pra você comparar com a copy;
  - (opcional) transcreve o áudio e compara a fala com a copy (precisa faster-whisper);
  - entrega um RELATÓRIO HTML auto-contido + um resumo .md acionável.

A ideia é a mesma do fluxo "conferir por frame": em vez de assistir cada vídeo, você
audita um mosaico bem amostrado + os flags automáticos. O que é objetivo, a ferramenta
decide sozinha; o que é subjetivo (avatar, artefato, copy), ela deixa pronto pra revisão.

Uso:
    python3 conferir.py <pasta_ou_video> [opções]

Exemplos:
    python3 conferir.py ./ADs
    python3 conferir.py ./ADs --formato 9:16 --min-largura 720 --ocr
    python3 conferir.py ./ADs --copy copy.txt --transcrever --modelo small.en --idioma pt

Opções principais:
    -o, --out DIR       pasta de saída (default: <input>/_QA)
    --formato LISTA     formatos aceitos, ex "9:16" ou "9:16,1:1" ou "qualquer" (default 9:16)
    --min-largura N     largura mínima aceitável em px (default 720)
    --min-dur S         duração mínima em segundos (default 3)
    --max-dur S         duração máxima em segundos (default 120)
    --frames N          nº de frames no mosaico (default: auto 12-18)
    --ocr               extrai texto da faixa inferior (legenda) via tesseract
    --idioma COD        idioma p/ OCR e transcrição (por = português; eng = inglês) (default por)
    --copy ARQ          arquivo .txt com a copy oficial (compara com OCR/transcrição)
    --transcrever       transcreve o áudio (precisa: pip install faster-whisper)
    --modelo NOME       modelo whisper: tiny.en|base.en|small.en|small|medium (default small)
    --jobs N            processa N vídeos em paralelo (default 1; use 2-4 no computador)
    -h, --help          ajuda
"""

import argparse
import base64
import concurrent.futures as cf
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi")

# ---------------------------------------------------------------- utilidades

def run(cmd, timeout=None):
    """Roda um comando e devolve (returncode, stdout, stderr) como str."""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "ignore"), p.stderr.decode("utf-8", "ignore")


def which_or_die(bin_name):
    if not shutil.which(bin_name):
        sys.exit(f"ERRO: '{bin_name}' não encontrado no PATH. Instale antes de rodar.")


def label_from_path(path, root):
    """Deriva um rótulo AD_Hn a partir do caminho/nome (não da ordem)."""
    base = os.path.basename(path)
    parent = os.path.basename(os.path.dirname(path))
    ad = ""
    if re.match(r"(?i)^ad", parent):
        ad = parent
    else:
        m = re.search(r"(?i)AD ?\d{1,2}", base)
        ad = m.group(0).replace(" ", "").upper() if m else ""
    if not ad:
        ad = os.path.splitext(base)[0][:24]
    m = re.search(r"(?i)(?:HOOK ?|H)(\d{1,2})", base)
    hook = m.group(1) if m else ""
    return f"{ad}_H{hook}" if hook else ad


def fmt_dur(s):
    s = float(s)
    return f"{int(s // 60)}:{int(s % 60):02d}" if s >= 60 else f"{s:.1f}s"


# ---------------------------------------------------------------- probe

def probe(path):
    """Metadados via ffprobe. Devolve dict; ok=False se o arquivo estiver quebrado."""
    rc, out, _ = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path
    ])
    info = {"ok": False, "dur": 0.0, "w": 0, "h": 0, "fps": 0.0, "audio": False}
    if rc != 0 or not out.strip():
        return info
    try:
        data = json.loads(out)
    except Exception:
        return info
    dur = float(data.get("format", {}).get("duration", 0) or 0)
    vstream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    astream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not vstream:
        return info
    w = int(vstream.get("width", 0) or 0)
    h = int(vstream.get("height", 0) or 0)
    fps = 0.0
    r = vstream.get("avg_frame_rate") or vstream.get("r_frame_rate") or "0/1"
    try:
        num, den = r.split("/")
        fps = float(num) / float(den) if float(den) else 0.0
    except Exception:
        pass
    info.update({"ok": w > 0 and h > 0 and dur > 0, "dur": dur, "w": w, "h": h,
                 "fps": round(fps, 2), "audio": astream is not None})
    return info


def aspect_name(w, h):
    if not h:
        return "?"
    r = w / h
    known = {"9:16": 0.5625, "3:4": 0.75, "4:5": 0.8, "1:1": 1.0, "4:3": 1.333,
             "16:9": 1.7778, "2:1": 2.0}
    best = min(known.items(), key=lambda kv: abs(kv[1] - r))
    return best[0] if abs(best[1] - r) < 0.04 else f"{r:.2f}:1"


# ---------------------------------------------------------------- detecção

def detect_defects(path, dur):
    """Uma passada de ffmpeg com black/freeze/silence detect. Devolve listas de intervalos."""
    vf = "blackdetect=d=0.2:pix_th=0.10,freezedetect=n=0.003:d=1.0"
    af = "silencedetect=n=-35dB:d=1.5"
    rc, _, err = run([
        "ffmpeg", "-nostdin", "-i", path,
        "-vf", vf, "-af", af, "-map", "0", "-f", "null", "-"
    ], timeout=max(60, int(dur) + 30))
    black = re.findall(r"black_start:([\d.]+).*?black_end:([\d.]+)", err)
    freeze = re.findall(r"freeze_start:\s*([\d.]+)", err)
    sil = re.findall(r"silence_start:\s*([\-\d.]+)", err)
    sil_end = re.findall(r"silence_end:\s*([\d.]+)", err)
    total_black = sum(float(b) - float(a) for a, b in black)
    total_sil = 0.0
    for i, s in enumerate(sil):
        e = float(sil_end[i]) if i < len(sil_end) else dur
        total_sil += max(0.0, e - float(s))
    return {
        "black_intervals": [(float(a), float(b)) for a, b in black],
        "black_total": round(total_black, 1),
        "freeze_starts": [float(x) for x in freeze],
        "silence_total": round(total_sil, 1),
    }


# ---------------------------------------------------------------- frames / mosaico

def extract_frames(path, dur, n, tmpdir):
    """Extrai n frames amostrados. Devolve lista de (timestamp, arquivo_jpg)."""
    frames = []
    for j in range(1, n + 1):
        t = dur * (j - 0.5) / n
        fp = os.path.join(tmpdir, f"f{j:02d}.jpg")
        run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", f"{t:.2f}",
             "-i", path, "-frames:v", "1", "-vf", "scale=360:-1", "-q:v", "3", fp, "-y"],
            timeout=30)
        if os.path.exists(fp):
            frames.append((t, fp))
    return frames


def _mosaic_ffmpeg(frames, out_jpg):
    """Sem Pillow (máquina de aluno): grade 3-col só com ffmpeg, sem timecode no quadro."""
    if not frames:
        return False
    rows = (len(frames) + 2) // 3
    rc, _, _ = run(["ffmpeg", "-nostdin", "-loglevel", "error", "-start_number", "1",
                    "-i", os.path.join(os.path.dirname(frames[0][1]), "f%02d.jpg"),
                    "-vf", f"tile=3x{rows}:padding=8:margin=8:color=0x111318",
                    "-frames:v", "1", "-q:v", "3", out_jpg, "-y"], timeout=60)
    return rc == 0 and os.path.exists(out_jpg)


def build_mosaic(frames, out_jpg, title, badge_text):
    """Compõe um mosaico 3-col com timecode em cada frame + barra de título (via PIL)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return _mosaic_ffmpeg(frames, out_jpg)

    def font(sz):
        for fp in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                   "/Library/Fonts/Arial.ttf"):
            if os.path.exists(fp):
                return ImageFont.truetype(fp, sz)
        return ImageFont.load_default()

    if not frames:
        return False
    thumbs = [Image.open(fp).convert("RGB") for _, fp in frames]
    tw, th = thumbs[0].size
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    pad, top = 8, 46
    W = cols * tw + pad * (cols + 1)
    H = top + rows * (th + 22) + pad * (rows + 1)
    canvas = Image.new("RGB", (W, H), (17, 19, 24))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 12), title, fill=(255, 255, 255), font=font(22))
    if badge_text:
        d.text((W - pad - int(d.textlength(badge_text, font=font(16))), 15),
                badge_text, fill=(255, 180, 90), font=font(16))
    for i, ((t, _), im) in enumerate(zip(frames, thumbs)):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = top + pad + r * (th + 22 + pad)
        canvas.paste(im, (x, y))
        tc = f"{int(t // 60)}:{t % 60:04.1f}"
        d.rectangle([x, y + th, x + tw, y + th + 20], fill=(30, 33, 40))
        d.text((x + 5, y + th + 3), f"{tc}", fill=(180, 200, 220), font=font(14))
    canvas.save(out_jpg, quality=88)
    return True


def available_tess_langs():
    rc, out, _ = run(["tesseract", "--list-langs"])
    return set(l.strip() for l in out.splitlines()[1:] if l.strip())


def resolve_ocr_lang(idioma):
    """Mapeia o idioma pedido pro código do tesseract, com fallback pra eng."""
    want = {"por": "por", "pt": "por", "eng": "eng", "en": "eng"}.get(idioma, idioma)
    have = available_tess_langs()
    if want in have:
        return want, None
    if "eng" in have:
        return "eng", (f"idioma '{want}' do tesseract não instalado; usando 'eng'. "
                       f"Para PT: brew install tesseract-lang (Mac) / apt install tesseract-ocr-por.")
    fb = next(iter(have), "eng")
    return fb, f"idioma '{want}' indisponível; usando '{fb}'."


def ocr_caption_band(path, dur, lang):
    """OCR da faixa inferior (legenda queimada). Re-extrai frames em alta res do vídeo."""
    from PIL import Image
    texts = []
    times = [dur * f for f in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)]
    for k, t in enumerate(times):
        fp = os.path.join(tempfile.gettempdir(), f"ocr_{os.getpid()}_{k}.jpg")
        run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", path,
             "-frames:v", "1", "-vf", "scale=900:-1", "-q:v", "2", fp, "-y"], timeout=30)
        if not os.path.exists(fp):
            continue
        im = Image.open(fp).convert("L")  # tons de cinza ajuda o OCR
        w, h = im.size
        band = im.crop((0, int(h * 0.58), w, h))  # faixa inferior = onde a legenda mora
        tmp = fp + ".band.png"
        band.save(tmp)
        rc, out, _ = run(["tesseract", tmp, "stdout", "-l", lang, "--psm", "6"], timeout=30)
        txt = " ".join(out.split())
        for junk in (fp, tmp):
            try:
                os.remove(junk)
            except OSError:
                pass
        if txt and len(txt) > 2:
            texts.append(txt)
    # dedup preservando ordem
    seen, uniq = set(), []
    for t in texts:
        k = re.sub(r"\W+", "", t.lower())
        if k and k not in seen:
            seen.add(k)
            uniq.append(t)
    return uniq


# ---------------------------------------------------------------- avaliação

def evaluate(info, defects, cfg):
    """Gera flags com severidade a partir dos dados. Devolve lista de dicts."""
    flags = []

    def add(sev, code, msg):
        flags.append({"sev": sev, "code": code, "msg": msg})

    if not info["ok"]:
        add("crit", "QUEBRADO", "arquivo não abre / sem stream de vídeo válido")
        return flags
    if info["dur"] < 1:
        add("crit", "QUEBRADO", f"duração {info['dur']:.1f}s (arquivo provavelmente corrompido)")
        return flags
    if info["w"] < cfg["min_larg"]:
        add("crit", "RESOLUCAO", f"largura {info['w']}px < mínimo {cfg['min_larg']}px")
    asp = aspect_name(info["w"], info["h"])
    if cfg["formatos"] and asp not in cfg["formatos"]:
        add("crit", "FORMATO", f"formato {asp} (esperado: {', '.join(cfg['formatos'])})")
    if info["dur"] < cfg["min_dur"]:
        add("aten", "DURACAO", f"muito curto: {fmt_dur(info['dur'])} (< {cfg['min_dur']}s)")
    if info["dur"] > cfg["max_dur"]:
        add("aten", "DURACAO", f"muito longo: {fmt_dur(info['dur'])} (> {cfg['max_dur']}s)")
    if not info["audio"]:
        add("crit", "SEM_AUDIO", "não tem faixa de áudio")
    elif defects["silence_total"] >= info["dur"] * 0.9:
        add("crit", "SILENCIO", f"áudio quase todo em silêncio ({defects['silence_total']}s)")
    elif defects["silence_total"] > 2.5:
        add("aten", "SILENCIO", f"{defects['silence_total']}s de silêncio detectado")
    if defects["black_total"] > 0.5:
        ini = defects["black_intervals"][0][0] if defects["black_intervals"] else 0
        add("aten", "FRAME_PRETO", f"{defects['black_total']}s de frame preto (1º em {ini:.1f}s)")
    if defects["freeze_starts"]:
        add("aten", "CONGELADO", f"imagem congelada em {defects['freeze_starts'][0]:.1f}s")
    return flags


# ---------------------------------------------------------------- pipeline por vídeo

def process_video(path, root, out, cfg, framesdir):
    name = label_from_path(path, root)
    info = probe(path)
    rec = {"name": name, "file": path, "info": info, "flags": [], "mosaic": None,
           "caption": [], "transcript_hint": None}
    if not info["ok"] or info["dur"] < 1:
        rec["flags"] = evaluate(info, {}, cfg)
        return rec

    n = cfg["frames"] or max(12, min(18, round(info["dur"] / 12)))
    tmp = os.path.join(framesdir, name)
    os.makedirs(tmp, exist_ok=True)
    frames = extract_frames(path, info["dur"], n, tmp)
    defects = detect_defects(path, info["dur"])
    rec["flags"] = evaluate(info, defects, cfg)

    badge = " ".join(f["code"] for f in rec["flags"] if f["sev"] == "crit") or ""
    mos = os.path.join(out, "montage", f"{name}.jpg")
    if build_mosaic(frames, mos, name, badge):
        rec["mosaic"] = mos

    # áudio leve p/ transcrição posterior
    if info["audio"]:
        ap = os.path.join(out, "audio", f"{name}.mp3")
        run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path,
             "-ac", "1", "-ar", "16000", "-b:a", "48k", ap, "-y"], timeout=60)

    if cfg["ocr"] and frames:
        try:
            rec["caption"] = ocr_caption_band(path, info["dur"], cfg["ocr_lang"])
        except Exception as e:
            rec["caption"] = [f"(OCR falhou: {e})"]
    return rec


# ---------------------------------------------------------------- transcrição (opcional)

def _whisper_cli(ap, cfg, lang):
    """Fallback: CLI `whisper` (openai-whisper) — é o que o Editor Automático instala."""
    tmp = tempfile.mkdtemp(prefix="conferir_whisper_")
    cmd = ["whisper", ap, "--model", cfg["modelo"], "--output_format", "json",
           "--output_dir", tmp, "--fp16", "False"]
    if lang:
        cmd += ["--language", lang]
    rc, _, err = run(cmd)
    js = os.path.join(tmp, os.path.splitext(os.path.basename(ap))[0] + ".json")
    if rc != 0 or not os.path.exists(js):
        raise RuntimeError(err.strip()[-300:] or "whisper falhou")
    segs = json.load(open(js, encoding="utf-8")).get("segments", [])
    shutil.rmtree(tmp, ignore_errors=True)
    return [(s["start"], s["end"], s["text"]) for s in segs]


def transcribe_all(records, out, cfg):
    lang = None if not cfg["modelo"].endswith(".en") else "en"
    if cfg["idioma"] and cfg["idioma"] != "auto":
        lang = {"por": "pt", "eng": "en"}.get(cfg["idioma"], cfg["idioma"])
    try:
        from faster_whisper import WhisperModel
        print(f"  carregando modelo {cfg['modelo']} ...")
        model = WhisperModel(cfg["modelo"], device="cpu", compute_type="int8")
        def transcrever(ap):
            segs, _ = model.transcribe(ap, beam_size=1, language=lang)
            return [(s.start, s.end, s.text) for s in segs]
    except Exception:
        if not shutil.which("whisper"):
            print("  ! nem faster-whisper nem o comando 'whisper' instalados — pulando transcrição.")
            print("    Rode: pip install faster-whisper --break-system-packages")
            print("    (no Editor Automático: aba Ambiente > instalar Whisper)")
            return
        print(f"  usando o comando 'whisper' (modelo {cfg['modelo']}) ...")
        transcrever = lambda ap: _whisper_cli(ap, cfg, lang)
    os.makedirs(os.path.join(out, "transcripts"), exist_ok=True)
    for rec in records:
        ap = os.path.join(out, "audio", f"{rec['name']}.mp3")
        if not os.path.exists(ap):
            continue
        try:
            segs = transcrever(ap)
        except Exception as e:
            print(f"  ! transcrição falhou em {rec['name']}: {e}")
            continue
        lines, full = [], []
        for ini, fim, txt in segs:
            lines.append(f"[{ini:6.1f}-{fim:6.1f}] {txt.strip()}")
            full.append(txt.strip())
        text = " ".join(full)
        open(os.path.join(out, "transcripts", rec["name"] + ".txt"), "w").write("\n".join(lines))
        rec["transcript"] = text
        # heurística de bug de fala: repetição imediata de trecho
        words = text.split()
        rep = any(words[i:i + 4] == words[i + 4:i + 8] for i in range(len(words) - 8))
        rec["transcript_hint"] = "possível repetição/loop na fala" if rep else None
        print(f"  transcrito {rec['name']}")


# ---------------------------------------------------------------- relatórios

SEV_LABEL = {"crit": ("🔴", "Crítico"), "aten": ("🟠", "Atenção")}


def write_markdown(records, out, cfg, copy_text):
    crit = [(r, f) for r in records for f in r["flags"] if f["sev"] == "crit"]
    aten = [(r, f) for r in records for f in r["flags"] if f["sev"] == "aten"]
    ok = [r for r in records if not r["flags"]]
    lines = []
    lines.append(f"# Conferência de ADs — {datetime.now():%d/%m/%Y %H:%M}")
    lines.append("")
    lines.append(f"Escopo: {len(records)} vídeo(s). Método: checks automáticos + mosaico de "
                 f"frames{' + OCR da legenda' if cfg['ocr'] else ''}"
                 f"{' + transcrição' if cfg['transcrever'] else ''}.")
    lines.append("")
    lines.append("> Ressalva: sincronia labial fina e nuance de copy pedem revisão humana do "
                 "mosaico. A ferramenta cobre o objetivo (arquivo, resolução, formato, frame "
                 "preto/congelado, silêncio) e prepara o resto.")
    lines.append("")
    lines.append(f"## 🔴 Crítico — reexportar/corrigir ({len(crit)})")
    lines.append("")
    if crit:
        for r, f in crit:
            lines.append(f"- **{r['name']}** — {f['code']}: {f['msg']}")
    else:
        lines.append("Nada crítico. 🎉")
    lines.append("")
    lines.append(f"## 🟠 Atenção ({len(aten)})")
    lines.append("")
    if aten:
        for r, f in aten:
            lines.append(f"- **{r['name']}** — {f['code']}: {f['msg']}")
    else:
        lines.append("Nada.")
    lines.append("")
    lines.append(f"## ✅ Passaram sem flag ({len(ok)})")
    lines.append("")
    lines.append(", ".join(r["name"] for r in ok) if ok else "—")
    lines.append("")
    lines.append("## Resumo por AD")
    lines.append("")
    lines.append("| AD | Formato | Resolução | Duração | Áudio | Flags |")
    lines.append("|----|---------|-----------|---------|-------|-------|")
    for r in records:
        i = r["info"]
        asp = aspect_name(i["w"], i["h"]) if i["ok"] else "—"
        res = f"{i['w']}x{i['h']}" if i["ok"] else "quebrado"
        fl = ", ".join(f["code"] for f in r["flags"]) or "ok"
        lines.append(f"| {r['name']} | {asp} | {res} | {fmt_dur(i['dur'])} | "
                     f"{'sim' if i['audio'] else 'não'} | {fl} |")
    lines.append("")
    if cfg["ocr"]:
        lines.append("## Legenda detectada (OCR — revisar contra a copy)")
        lines.append("")
        for r in records:
            if r["caption"]:
                lines.append(f"**{r['name']}:** " + " / ".join(r["caption"][:8]))
        lines.append("")
    path = os.path.join(out, "relatorio.md")
    open(path, "w").write("\n".join(lines))
    return path


def b64_img(p):
    with open(p, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def write_html(records, out, cfg):
    crit = sum(1 for r in records for f in r["flags"] if f["sev"] == "crit")
    aten = sum(1 for r in records for f in r["flags"] if f["sev"] == "aten")
    okc = sum(1 for r in records if not r["flags"])
    cards = []
    for r in records:
        i = r["info"]
        badges = ""
        for f in r["flags"]:
            ico, _ = SEV_LABEL[f["sev"]]
            cls = "crit" if f["sev"] == "crit" else "aten"
            badges += f'<span class="badge {cls}">{ico} {f["code"]}: {html.escape(f["msg"])}</span>'
        if not r["flags"]:
            badges = '<span class="badge ok">✅ sem flag</span>'
        meta = (f'{aspect_name(i["w"], i["h"]) if i["ok"] else "—"} · '
                f'{i["w"]}x{i["h"]} · {fmt_dur(i["dur"])} · {i["fps"]}fps · '
                f'áudio {"sim" if i["audio"] else "não"}') if i["ok"] else "arquivo quebrado"
        img = f'<img loading="lazy" src="{b64_img(r["mosaic"])}">' if r.get("mosaic") else \
              '<div class="noimg">sem mosaico (arquivo quebrado)</div>'
        cap = ""
        if cfg["ocr"] and r["caption"]:
            items = "".join(f"<li>{html.escape(t)}</li>" for t in r["caption"][:10])
            cap = f'<details><summary>Legenda (OCR)</summary><ul>{items}</ul></details>'
        tr = ""
        if r.get("transcript"):
            hint = f' <span class="badge aten">⚠ {r["transcript_hint"]}</span>' if r.get("transcript_hint") else ""
            tr = (f'<details><summary>Transcrição da fala{hint}</summary>'
                  f'<p class="tr">{html.escape(r["transcript"])}</p></details>')
        cards.append(f"""
        <div class="card">
          <div class="head"><h3>{html.escape(r['name'])}</h3><span class="fpath">{html.escape(os.path.basename(r['file']))}</span></div>
          <div class="meta">{meta}</div>
          <div class="badges">{badges}</div>
          {img}
          {cap}{tr}
        </div>""")

    doc = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Conferência de ADs</title>
<style>
  :root{{color-scheme:dark}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:#0d0f14;color:#e8ecf2;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
  header{{position:sticky;top:0;background:#0d0f14ee;backdrop-filter:blur(8px);padding:20px 28px;border-bottom:1px solid #222836;z-index:5}}
  h1{{margin:0 0 4px;font-size:22px}}
  .sub{{color:#96a0b3;font-size:13px}}
  .kpis{{display:flex;gap:14px;margin-top:14px;flex-wrap:wrap}}
  .kpi{{background:#161a22;border:1px solid #232a38;border-radius:12px;padding:10px 16px;min-width:110px}}
  .kpi b{{display:block;font-size:26px;line-height:1}}
  .kpi span{{font-size:12px;color:#96a0b3}}
  .kpi.c b{{color:#ff6b6b}} .kpi.a b{{color:#ffb454}} .kpi.o b{{color:#4ade80}}
  main{{padding:24px 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;max-width:1500px;margin:0 auto}}
  .card{{background:#12151c;border:1px solid #222836;border-radius:14px;padding:14px;overflow:hidden}}
  .head{{display:flex;align-items:baseline;justify-content:space-between;gap:8px}}
  .head h3{{margin:0;font-size:17px}}
  .fpath{{font-size:11px;color:#6b7688;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:45%}}
  .meta{{color:#96a0b3;font-size:12.5px;margin:4px 0 10px}}
  .badges{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}}
  .badge{{font-size:11.5px;padding:3px 8px;border-radius:20px;background:#1b2130;border:1px solid #2a3346}}
  .badge.crit{{background:#3a1618;border-color:#5c2226;color:#ff9a9a}}
  .badge.aten{{background:#3a2c12;border-color:#5c471f;color:#ffcf8a}}
  .badge.ok{{background:#12301f;border-color:#1f5236;color:#8ef0b4}}
  img{{width:100%;border-radius:8px;display:block;border:1px solid #222836}}
  .noimg{{padding:40px;text-align:center;color:#6b7688;background:#161a22;border-radius:8px}}
  details{{margin-top:10px;background:#161a22;border-radius:8px;padding:8px 12px;font-size:13px}}
  summary{{cursor:pointer;color:#9db4ff}}
  details ul{{margin:8px 0 0;padding-left:18px}} details li{{margin:2px 0;color:#cdd6e4}}
  .tr{{color:#cdd6e4;font-size:13px}}
</style></head><body>
<header>
  <h1>Conferência de ADs</h1>
  <div class="sub">{len(records)} vídeo(s) · gerado em {datetime.now():%d/%m/%Y %H:%M} · método: checks automáticos + mosaico{' + OCR' if cfg['ocr'] else ''}{' + transcrição' if cfg['transcrever'] else ''}</div>
  <div class="kpis">
    <div class="kpi c"><b>{crit}</b><span>flags críticas</span></div>
    <div class="kpi a"><b>{aten}</b><span>atenção</span></div>
    <div class="kpi o"><b>{okc}</b><span>sem flag</span></div>
    <div class="kpi"><b>{len(records)}</b><span>vídeos</span></div>
  </div>
</header>
<main>{''.join(cards)}</main>
</body></html>"""
    path = os.path.join(out, "relatorio.html")
    open(path, "w").write(doc)
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="QA de criativos de vídeo por frame (terminal).")
    ap.add_argument("input", help="pasta com os vídeos ou um vídeo único")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--formato", default="9:16")
    ap.add_argument("--min-largura", type=int, default=720)
    ap.add_argument("--min-dur", type=float, default=3)
    ap.add_argument("--max-dur", type=float, default=120)
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--idioma", default="por")
    ap.add_argument("--copy", default=None)
    ap.add_argument("--transcrever", action="store_true")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args()

    which_or_die("ffmpeg")
    which_or_die("ffprobe")
    if args.ocr and not shutil.which("tesseract"):
        print("  ! 'tesseract' não encontrado — seguindo SEM ler a legenda na tela (OCR).")
        print("    Mac: brew install tesseract tesseract-lang · Windows: winget install UB-Mannheim.TesseractOCR")
        args.ocr = False

    inp = os.path.abspath(args.input)
    if not os.path.exists(inp):
        sys.exit(f"ERRO: não existe: {inp}")
    root = inp if os.path.isdir(inp) else os.path.dirname(inp)
    out = os.path.abspath(args.out) if args.out else os.path.join(root, "_QA")
    for sub in ("montage", "audio"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    framesdir = tempfile.mkdtemp(prefix="conferir_frames_")

    if os.path.isdir(inp):
        vids = sorted(os.path.join(dp, fn) for dp, _, fns in os.walk(inp)
                      for fn in fns if fn.lower().endswith(VIDEO_EXT)
                      and "_QA" not in dp)
    else:
        vids = [inp]
    if not vids:
        sys.exit("Nenhum vídeo encontrado (procurei .mp4/.mov/.m4v/.webm/.mkv/.avi).")

    formatos = [] if args.formato.strip().lower() in ("qualquer", "any", "") \
        else [x.strip() for x in args.formato.split(",")]
    cfg = {"formatos": formatos, "min_larg": args.min_largura, "min_dur": args.min_dur,
           "max_dur": args.max_dur, "frames": args.frames, "ocr": args.ocr,
           "idioma": args.idioma, "transcrever": args.transcrever, "modelo": args.modelo,
           "ocr_lang": "eng"}
    if args.ocr:
        cfg["ocr_lang"], warn = resolve_ocr_lang(args.idioma)
        if warn:
            print(f"  ! OCR: {warn}\n")

    print(f"Conferindo {len(vids)} vídeo(s) → saída em {out}\n")
    records = []
    if args.jobs > 1:
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(process_video, v, root, out, cfg, framesdir): v for v in vids}
            for fut in cf.as_completed(futs):
                r = fut.result()
                records.append(r)
                print(f"  ✓ {r['name']}  [{', '.join(f['code'] for f in r['flags']) or 'ok'}]")
    else:
        for v in vids:
            r = process_video(v, root, out, cfg, framesdir)
            records.append(r)
            print(f"  ✓ {r['name']}  [{', '.join(f['code'] for f in r['flags']) or 'ok'}]")
    records.sort(key=lambda r: r["name"])

    copy_text = ""
    if args.copy and os.path.exists(args.copy):
        copy_text = open(args.copy, encoding="utf-8", errors="ignore").read()

    if args.transcrever:
        print("\nTranscrevendo áudio...")
        transcribe_all(records, out, cfg)

    json.dump(records, open(os.path.join(out, "dados.json"), "w"),
              ensure_ascii=False, indent=2, default=str)
    md = write_markdown(records, out, cfg, copy_text)
    ht = write_html(records, out, cfg)

    crit = sum(1 for r in records for f in r["flags"] if f["sev"] == "crit")
    aten = sum(1 for r in records for f in r["flags"] if f["sev"] == "aten")
    print(f"\n{'='*54}")
    print(f"  Concluído: {len(records)} vídeos | 🔴 {crit} críticos | 🟠 {aten} atenção")
    print(f"  Relatório visual : {ht}")
    print(f"  Resumo markdown  : {md}")
    print(f"  Mosaicos         : {os.path.join(out, 'montage')}/")
    print(f"{'='*54}")
    try:
        shutil.rmtree(framesdir)
    except Exception:
        pass


if __name__ == "__main__":
    main()
