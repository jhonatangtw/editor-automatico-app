#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mixagem final: voz original (intocada) + SFX de sfx-cues.json [+ música com ducking].

    python3 scripts/premium/mixar.py PASTA_DO_PROJETO                 # usa roteiro.json › musica (se houver)
    python3 scripts/premium/mixar.py PASTA_DO_PROJETO --sem-musica     # versão só voz + SFX
    python3 scripts/premium/mixar.py PASTA_DO_PROJETO --musica assets/musica/x.mp3 --musica-db -16

Alvo de entrega Reels: -14 LUFS integrado, true peak <= -1 dBTP.
Saída: renders/mix.wav (ou renders/mix-sem-musica.wav), 48 kHz 24 bits.
"""
import argparse
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import duracao, ler_json, sair  # noqa: E402


def medir(arq):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", arq, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    resumo = e[e.rfind("Summary"):]
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", resumo)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", resumo)[-1])
    return i, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--sem-musica", action="store_true")
    ap.add_argument("--musica")
    ap.add_argument("--musica-db", type=float)
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    P = os.path.abspath(a.pasta)
    os.chdir(P)
    R = ler_json("roteiro.json") if os.path.exists("roteiro.json") else {}
    voz = "assets/audio/voz.wav"
    if not os.path.exists(voz):
        sair("falta %s" % voz)
    DUR = R.get("duracao") or duracao(voz)
    cues = ler_json("sfx-cues.json") if os.path.exists("sfx-cues.json") else []
    mus = None if a.sem_musica else (a.musica or (R.get("musica") or {}).get("arquivo"))
    mdb = a.musica_db if a.musica_db is not None else (R.get("musica") or {}).get("volume_db", -16)
    inp = ["-i", voz]
    fc = ["[0:a]aformat=sample_rates=48000:channel_layouts=stereo" + (",asplit=2[voz][sc]" if mus else "[voz]")]
    labels = ["[voz]"]
    k = 1
    if mus:
        if not os.path.exists(mus):
            sair("música não encontrada: %s" % mus)
        inp += ["-stream_loop", "-1", "-i", mus]
        fc.append("[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:%.3f,asetpts=PTS-STARTPTS,volume=%.1fdB,"
                  "afade=t=in:d=0.4,afade=t=out:st=%.3f:d=2.2[m0]" % (DUR, mdb, max(0, DUR - 2.2)))
        # ducking: a voz comprime a música (sidechain) — a música nunca briga com a fala
        fc.append("[m0][sc]sidechaincompress=threshold=0.03:ratio=5:attack=25:release=400:makeup=1[mus]")
        labels.append("[mus]")
        k = 2
    for n, (t, nome, v, cap) in enumerate(cues):
        f = "assets/sfx/%s.mp3" % nome
        if not os.path.exists(f):
            print("! sem arquivo para o SFX '%s' — pulei" % nome)
            continue
        inp += ["-i", f]
        tr = "atrim=0:%s," % cap if cap else ""
        ms = int(t * 1000)
        fc.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,%safade=t=out:st=%.3f:d=0.15,volume=%.3f,adelay=%d|%d[s%d]"
                  % (k, tr, max(0, (cap or 9) - 0.15), v * 0.8, ms, ms, n))
        labels.append("[s%d]" % n)
        k += 1
    fc.append("".join(labels) + "amix=inputs=%d:normalize=0:duration=first,atrim=0:%.3f[mix]" % (len(labels), DUR))
    saida = "renders/mix-sem-musica.wav" if not mus else "renders/mix.wav"
    os.makedirs("renders", exist_ok=True)

    def rodar(cadeia, out):
        g = ";".join(fc + ["[mix]%s[o]" % cadeia])
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y"] + inp + ["-filter_complex", g, "-map", "[o]"] + out,
                           capture_output=True, text=True)
        if r.returncode:
            sair("ffmpeg falhou na mixagem:\n" + r.stderr[-800:])
        return r.stderr
    e = rodar("ebur128=peak=true", ["-f", "null", "-"])
    bruto = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e[e.rfind("Summary"):])[-1])
    ganho = a.lufs - bruto
    lim = 0.79
    for _ in range(3):
        rodar("volume=%.2fdB,alimiter=limit=%.3f:attack=3:release=60:level=false,aresample=48000" % (ganho, lim),
              ["-c:a", "pcm_s24le", saida])
        i, tp = medir(saida)
        if tp <= -1.0 and abs(i - a.lufs) <= 0.6:
            break
        if tp > -1.0:
            lim *= 0.9
        ganho += a.lufs - i
    print("mix: %s  ·  %.1f LUFS  ·  true peak %.1f dBTP  ·  %s" % (saida, i, tp, "música %s (%.0f dB, ducking)" % (mus, mdb) if mus else "sem música"))
    if tp > -1.0:
        print("! true peak acima de -1 dBTP — baixe o volume de algum SFX em sfx-cues.json")


if __name__ == "__main__":
    main()
