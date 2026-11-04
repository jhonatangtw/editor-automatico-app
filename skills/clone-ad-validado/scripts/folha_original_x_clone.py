#!/usr/bin/env python3
"""Folhas de conferência do clone.

1) Original × clone lado a lado, no MESMO segundo:
    python3 folha_original_x_clone.py --original original/AD.mp4 --clone renders/clone.mp4 \
        --saida qc/original_x_clone.jpg [--tempos "0.8,2.6,4.6,8.8"] [--passo 2]

2) Varredura do clone inteiro (procura sobra da pessoa antiga, quadro errado, legenda dupla):
    python3 folha_original_x_clone.py --clone renders/clone.mp4 --varredura 4 \
        --saida qc/clone_varredura_4fps.jpg

Sem --tempos, pega um quadro a cada --passo segundos (padrão 2 s), começando
em 0,5 s. Escolha tempos DENTRO de cada cena e logo depois de cada troca.
Não há drawtext no ffmpeg de muitas máquinas: o timecode é desenhado com PIL.
"""
import argparse
import io
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont


def fonte(tam):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "C:\\Windows\\Fonts\\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def duracao(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", v],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def quadro(v, t, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", v, "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    if not raw:
        return Image.new("RGB", (w, h), "#400")
    return Image.open(io.BytesIO(raw)).convert("RGB").resize((w, h))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original")
    ap.add_argument("--clone", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--tempos")
    ap.add_argument("--passo", type=float, default=2.0)
    ap.add_argument("--varredura", type=float, help="quadros por segundo da varredura do clone")
    ap.add_argument("--colunas", type=int, default=7)
    a = ap.parse_args()
    f = fonte(22)

    if a.varredura:
        dur = duracao(a.clone)
        n = int(dur * a.varredura)
        w, h, cols = 135, 240, 16
        rows = (n + cols - 1) // cols
        img = Image.new("RGB", (cols * w, rows * (h + 18)), "#111")
        d = ImageDraw.Draw(img)
        # um único ffmpeg para todos os quadros (mais rápido que um por quadro)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.clone, "-vf",
                              "fps=%g,scale=%d:%d" % (a.varredura, w, h), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        tam = w * h * 3
        for i in range(min(n, len(raw) // tam)):
            q = Image.frombytes("RGB", (w, h), raw[i * tam:(i + 1) * tam])
            x, y = (i % cols) * w, (i // cols) * (h + 18)
            img.paste(q, (x, y + 18))
            d.text((x + 3, y + 2), "%.2f" % (i / a.varredura), fill="#F2B33D")
        img.save(a.saida, quality=85)
        print("varredura: %d quadros -> %s" % (n, a.saida))
        return

    if not a.original:
        ap.error("--original é obrigatório fora do modo --varredura")
    if a.tempos:
        T = [float(x) for x in a.tempos.split(",") if x.strip()]
    else:
        dur = min(duracao(a.original), duracao(a.clone))
        T, t = [], 0.5
        while t < dur - 0.1:
            T.append(round(t, 2))
            t += a.passo
    w, h, cols = 270, 480, a.colunas
    rows = (len(T) + cols - 1) // cols
    img = Image.new("RGB", (cols * (2 * w + 16), rows * (h + 40) + 50), "#111")
    d = ImageDraw.Draw(img)
    d.text((12, 12), "ORIGINAL (esq.)  x  CLONE (dir.)", font=f, fill="white")
    for i, t in enumerate(T):
        x, y = (i % cols) * (2 * w + 16), 50 + (i // cols) * (h + 40)
        img.paste(quadro(a.original, t, w, h), (x, y + 30))
        img.paste(quadro(a.clone, t, w, h), (x + w, y + 30))
        d.text((x + 6, y + 4), "%.1f s" % t, font=f, fill="#F2B33D")
    img.save(a.saida, quality=88)
    print("folha: %d tempos -> %s" % (len(T), a.saida))


if __name__ == "__main__":
    main()
