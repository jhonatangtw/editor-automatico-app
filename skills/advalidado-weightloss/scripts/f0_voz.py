#!/usr/bin/env python3
"""Mede a voz para escolher a candidata mais parecida com a do AD original.

Para cada arquivo de áudio: F0 mediana (altura da voz, por autocorrelação nos
trechos com voz), faixa do F0 (p10–p90) e, se houver um JSON de palavras ao
lado (mesmo nome, .json, formato do tts_elevenlabs.py ou do Whisper),
palavras por minuto.

Uso:
    python3 f0_voz.py original.wav cand_a.mp3 cand_b.mp3 cand_c.mp3

O PRIMEIRO arquivo é a referência (a voz do AD original). A tabela sai
ordenada pela distância de F0 até ela.

Limite honesto: F0 e ritmo separam grave × agudo e lento × rápido. Sotaque,
idade percebida e timbre NÃO saem de número — a escolha final é de ouvido,
do usuário, com as amostras lado a lado.
"""
import json
import os
import subprocess
import sys

import numpy as np

SR = 16000


def ler(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0


def f0s(a, fmin=70, fmax=400):
    n = int(0.04 * SR)             # janela de 40 ms
    passo = int(0.01 * SR)
    rms = np.array([np.sqrt((a[i:i + n] ** 2).mean()) for i in range(0, len(a) - n, passo)])
    if not len(rms):
        return np.array([])
    limiar = max(0.02, np.percentile(rms, 60) * 0.5)
    lmin, lmax = SR // fmax, SR // fmin
    saida = []
    for k, i in enumerate(range(0, len(a) - n, passo)):
        if rms[k] < limiar:
            continue
        x = a[i:i + n] - a[i:i + n].mean()
        c = np.correlate(x, x, "full")[n - 1:]
        if c[0] <= 0:
            continue
        c = c / c[0]
        seg = c[lmin:lmax]
        j = int(np.argmax(seg))
        if seg[j] > 0.45:          # só quadro claramente vozeado
            saida.append(SR / (lmin + j))
    return np.array(saida)


def palavras_por_min(p, dur):
    j = os.path.splitext(p)[0] + ".json"
    if not os.path.isfile(j):
        return None
    d = json.load(open(j, encoding="utf-8"))
    if "words" in d:
        w = d["words"]
    else:
        w = [x for s in d.get("segments", []) for x in s.get("words", [])]
    if not w:
        return None
    ini, fim = w[0]["start"], w[-1]["end"]
    return len(w) / max(0.1, (fim - ini)) * 60


def main(args):
    if len(args) < 2:
        sys.exit(__doc__)
    linhas = []
    for p in args:
        a = ler(p)
        f = f0s(a)
        dur = len(a) / SR
        if len(f) < 20:
            linhas.append((p, None, None, None, palavras_por_min(p, dur), dur))
            continue
        linhas.append((p, float(np.median(f)), float(np.percentile(f, 10)), float(np.percentile(f, 90)),
                       palavras_por_min(p, dur), dur))
    ref = linhas[0][1]
    print("%-34s %8s %13s %8s %6s %10s" % ("arquivo", "F0 med", "faixa p10-90", "pal/min", "dur", "dist. ref"))
    def chave(l):
        return (l[0] != args[0], abs(l[1] - ref) if (l[1] and ref) else 9e9)
    for p, med, lo, hi, ppm, dur in sorted(linhas, key=chave):
        dist = "(ref)" if p == args[0] else ("%+.0f Hz" % (med - ref) if med and ref else "-")
        print("%-34s %8s %13s %8s %6.1f %10s" % (
            os.path.basename(p)[:34], "%.0f Hz" % med if med else "-",
            "%.0f-%.0f" % (lo, hi) if lo else "-", "%.0f" % ppm if ppm else "-", dur, dist))
    print("\nReferência de faixa: voz feminina adulta ~165-255 Hz; masculina ~85-155 Hz.")
    print("Ritmo diferente se acerta depois (atempo até ~1,15x passa despercebido). Sotaque e idade: ouvido.")


if __name__ == "__main__":
    main(sys.argv[1:])
