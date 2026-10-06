#!/usr/bin/env python3
"""Mede o deslocamento entre dois ÁUDIOS por correlação cruzada.

    python3 offset_audio.py lipsync/heygen_selfie.mp4 lipsync/aud_selfie.wav

Serve para saber quanto o vídeo do lip sync (HeyGen) está adiantado ou
atrasado em relação ao áudio que você mandou — e compensar no ponto de
entrada do clipe (data-media-start no HyperFrames, in-point no Premiere).

Correlação funciona aqui porque é SOM contra SOM (o mesmo sinal). Para
conferir BOCA contra SOM não use correlação: use qc_lipsync.py.
"""
import subprocess
import sys

import numpy as np

SR = 8000


def ler(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)


def main(a):
    if len(a) != 2:
        sys.exit(__doc__)
    x, y = ler(a[0]), ler(a[1])
    if not len(x) or not len(y):
        sys.exit("um dos arquivos não tem áudio")
    n = 1 << int(np.ceil(np.log2(len(x) + len(y))))
    c = np.fft.irfft(np.fft.rfft(x, n) * np.conj(np.fft.rfft(y, n)), n)
    k = int(np.argmax(c))
    k = k - n if k > n // 2 else k
    print("%s está %s %.3f s em relação a %s  (durações %.2f / %.2f s)" % (
        a[0], "ATRASADO" if k > 0 else "ADIANTADO", abs(k) / SR, a[1], len(x) / SR, len(y) / SR))
    print("deslocamento = %+.3f s  (some ao ponto de entrada do clipe)" % (k / SR))


if __name__ == "__main__":
    main(sys.argv[1:])
