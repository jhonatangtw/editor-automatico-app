#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acelera o vídeo PRONTO (ex.: 1,15x) sem perder sincronia.

    python3 scripts/premium/acelerar.py "renders/X - premium.mp4" --fator 1.15 [--audio renders/mix.wav]

A aceleração vem DEPOIS da composição: imagem (setpts) e som (atempo, mesmo
tom de voz) andam juntos, então legenda, lettering e SFX continuam no tempo.
Se --audio for dado (a mixagem .wav), usa ele em vez do AAC do vídeo (menos perda).
Saída: mesmo nome + " 1.15x" — o vídeo de entrada não é alterado.
"""
import argparse
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import duracao, sair  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--fator", type=float, default=1.15)
    ap.add_argument("--audio")
    ap.add_argument("--saida")
    a = ap.parse_args()
    if not 0.5 <= a.fator <= 2.0:
        sair("fator entre 0,5 e 2,0 (atempo)")
    base, ext = os.path.splitext(a.video)
    out = a.saida or "%s %sx%s" % (base, ("%.2f" % a.fator).rstrip("0").rstrip("."), ext)
    if os.path.abspath(out) == os.path.abspath(a.video):
        sair("a saída não pode sobrescrever a entrada")
    inp = ["-i", a.video] + (["-i", a.audio] if a.audio else [])
    au = "1:a" if a.audio else "0:a"
    fc = "[0:v]setpts=PTS/%s,fps=30[v];[%s]atempo=%s,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" % (a.fator, au, a.fator)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + inp + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "slow", "-b:v", "20M", "-maxrate", "24M", "-bufsize", "40M", "-profile:v", "high",
                        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    if r.returncode:
        sair(r.stderr[-600:])
    d0, d1 = duracao(a.video), duracao(out)
    print("ok -> %s  (%.2f s -> %.2f s; esperado %.2f s)" % (out, d0, d1, d0 / a.fator))


if __name__ == "__main__":
    main()
