#!/usr/bin/env python3
"""Prova de lip sync: quadro do SILÊNCIO × quadros de PICO da voz, recortados na boca.

    python3 qc_lipsync.py --video renders/clone.mp4 --voz voz/voz_clone.wav \
        --palavras voz/voz_clone.json --saida qc/lipsync_silencio_x_pico.jpg \
        --fase "selfie:0.3:12.5:540:1655" --fase "cozinha:12.7:24.6:540:975"

--fase  nome:inicio:fim:x_boca:y_boca   (pixels no vídeo final; um por cenário/enquadramento)
        sem --fase: o vídeo inteiro numa fase só, boca no centro a 40 % da altura.

Para cada fase sai uma linha: 1 quadro na maior pausa entre palavras + os 4
picos de volume mais espaçados (≥ 1 s entre si). Leitura: no silêncio a boca
está FECHADA; nos picos está ABERTA, com formas de vogal diferentes. Se for
assim, a sincronia está boa.

Por que não correlação automática "abertura da boca × volume": o sinal de boca
improvisado é dominado por sombra, barba e movimento de cabeça. Num lote real
ela reprovou 42 de 68 clipes que estavam bons. Correlação serve, no máximo,
para ORDENAR suspeitos — nunca para reprovar.
"""
import argparse
import io
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 16000


def fonte(tam):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
              "C:\\Windows\\Fonts\\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--voz", required=True, help="o áudio da fala (wav/mp3) na MESMA linha de tempo do vídeo")
    ap.add_argument("--palavras", required=True, help="JSON {words:[{text,start,end}]} na linha de tempo do vídeo")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--fase", action="append", default=[])
    ap.add_argument("--picos", type=int, default=4)
    a = ap.parse_args()

    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height:format=duration", "-of", "json", a.video],
                        capture_output=True, text=True, check=True)
    info = json.loads(pr.stdout)
    W, H = info["streams"][0]["width"], info["streams"][0]["height"]
    dur = float(info["format"]["duration"])

    aud = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", a.voz, "-ac", "1", "-ar", str(SR),
                                        "-f", "s16le", "-"], capture_output=True, check=True).stdout,
                        np.int16).astype(float)

    def rms(t):
        i = int(t * SR)
        x = aud[max(0, i - 800):i + 800]
        return float(np.sqrt((x ** 2).mean())) if len(x) else 0.0

    d = json.load(open(a.palavras, encoding="utf-8"))
    w = d["words"] if "words" in d else [x for s in d.get("segments", []) for x in s.get("words", [])]
    pausas = [((w[k]["end"] + w[k + 1]["start"]) / 2, w[k + 1]["start"] - w[k]["end"])
              for k in range(len(w) - 1) if w[k + 1]["start"] - w[k]["end"] > 0.2]
    if w and w[0]["start"] > 0.3:
        pausas.append((w[0]["start"] / 2, w[0]["start"]))

    fases = []
    for f in a.fase or ["video:0:%.2f:%d:%d" % (dur, W // 2, int(H * 0.4))]:
        nome, t0, t1, x, y = f.split(":")
        fases.append((nome, float(t0), float(t1), int(float(x)), int(float(y))))

    linhas = []
    for nome, t0, t1, x, y in fases:
        sil = [t for t, g in sorted(pausas, key=lambda p: -p[1]) if t0 < t < t1]
        ts = np.arange(t0, t1, 0.04)
        picos = []
        for t in sorted(ts, key=rms, reverse=True):
            if all(abs(t - p) > 1.0 for p in picos):
                picos.append(float(t))
            if len(picos) == a.picos:
                break
        cel = ([("silêncio", sil[0])] if sil else [("SEM PAUSA", t0)]) + [("pico", p) for p in sorted(picos)]
        linhas.append((nome, x, y, cel))

    cw, ch, topo = 300, 200, 24
    col = 1 + a.picos
    img = Image.new("RGB", (cw * col, (ch + topo) * len(linhas)), "white")
    dr = ImageDraw.Draw(img)
    fn = fonte(14)
    meia_w, meia_h = int(W * 0.28), int(W * 0.28 * 2 / 3)
    for r, (nome, x, y, cel) in enumerate(linhas):
        for c, (tipo, t) in enumerate(cel):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", a.video, "-frames:v", "1",
                                  "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
            if not raw:
                continue
            q = Image.open(io.BytesIO(raw)).convert("RGB")
            caixa = (max(0, x - meia_w), max(0, y - meia_h), min(W, x + meia_w), min(H, y + meia_h))
            img.paste(q.crop(caixa).resize((cw, ch)), (c * cw, r * (ch + topo) + topo))
            dr.text((c * cw + 4, r * (ch + topo) + 6), "%s · %s %.2fs" % (nome[:14], tipo, t),
                    fill="red" if tipo == "silêncio" else "black", font=fn)
    img.save(a.saida, quality=90)
    for nome, x, y, cel in linhas:
        print("%-14s %s" % (nome, "  ".join("%s %.2f" % (tp, t) for tp, t in cel)))
    print("folha:", a.saida, "— abra e OLHE: boca fechada no silêncio, aberta e variada nos picos.")
    print("Pausa curta (< 0,4 s) pode pegar a boca em transição; a prova mais forte é a pausa longa ou o silêncio inicial.")


if __name__ == "__main__":
    main()
