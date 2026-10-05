#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prévia leve do plano de corte (para o aluno ouvir ANTES de ir ao Premiere).

    python3 scripts/previa_corte.py --video BRUTO.MOV --plano decupagem/plano-corte.json \
        --saida decupagem/previa-corte.mp4 [--sem-opcionais]

608x1080, 30 fps, H.264 SDR. Se o bruto for HDR (HLG/PQ), aplica só uma
APROXIMAÇÃO de cor (eq) — a cor certa é feita no Premiere (fase 3).
Fade de 20/30 ms em cada emenda para não estalar. O bruto não é alterado.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import exigir, info_video, ler_json, sair  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--sem-opcionais", action="store_true")
    ap.add_argument("--alta", action="store_true", help="corte em 1080x1920 qualidade alta (caminho sem Premiere)")
    a = ap.parse_args()
    exigir("ffmpeg")
    if os.path.abspath(a.saida) == os.path.abspath(a.video):
        sair("a saída não pode ser o bruto")
    inf = info_video(a.video)
    pl = ler_json(a.plano)
    pecas = [p for p in pl["pedacos"] if not (a.sem_opcionais and p["opcional"])]
    w, h = (608, 1080) if inf["altura"] >= inf["largura"] else (1080, 608)
    if a.alta:
        w, h = (1080, 1920) if inf["altura"] >= inf["largura"] else (1920, 1080)
        print("! --alta: a cor HDR aqui é só aproximada (eq). Para cor certa, use o Premiere (fase 3)." if inf["hdr"] else "corte em alta")
    cor = ",eq=gamma=0.80:saturation=1.55:contrast=1.12" if inf["hdr"] else ""
    tmp = tempfile.mkdtemp(prefix="previa-")
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w") as L:
        for k, p in enumerate(pecas):
            out = os.path.join(tmp, "%03d.mp4" % k)
            d = p["saida"] - p["entrada"]
            vf = "scale=%d:%d,fps=30%s,format=yuv420p" % (w, h, cor)
            af = "afade=t=in:d=0.02,afade=t=out:st=%.3f:d=0.03" % max(0, d - 0.03)
            r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % p["entrada"], "-t", "%.3f" % d,
                                "-i", a.video, "-map", "0:v:0", "-map", "0:a:0", "-vf", vf, "-af", af,
                                "-c:v", "libx264", "-preset", "slow" if a.alta else "veryfast", "-crf", "14" if a.alta else "24",
                                "-c:a", "aac", "-b:a", "320k" if a.alta else "128k", "-ar", "48000", "-ac", "2" if a.alta else "1", "-colorspace", "bt709", "-color_primaries", "bt709",
                                "-color_trc", "bt709", out], capture_output=True, text=True)
            if r.returncode:
                sair("ffmpeg falhou na peça %s: %s" % (p["nome"], r.stderr[-400:]))
            L.write("file '%s'\n" % out)
            print("  %s %.2f-%.2f" % (p["nome"], p["entrada"], p["saida"]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy",
                    "-movflags", "+faststart", a.saida], check=True)
    print("ok ->", a.saida, "(%d peças)" % len(pecas))


if __name__ == "__main__":
    main()
