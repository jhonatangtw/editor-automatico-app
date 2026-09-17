#!/usr/bin/env python3
"""Confere um render contra a fonte, sem abrir o video no olho.

    conferir_render.py timbre <render.mp4> <voz_esperada.wav> <voz_antiga.wav>
        Espectro medio de longo prazo. Prova de QUAL voz saiu no render.
        Casar >0.95 com a esperada e ficar bem abaixo com a antiga.

    conferir_render.py frames <render.mp4> <pasta-saida> <nome>=<segundos> ...
        Grava um PNG por momento pedido, nomeado com o timecode.

    conferir_render.py sync <render.mp4> <pasta-saida> <palavra>=<segundos> ...
        Grava o quadro 4f ANTES e 6f DEPOIS de cada palavra-ancora: prova visual
        de que o elemento entra na palavra, e nao antes.
"""
import subprocess, sys
from pathlib import Path
import numpy as np

def _pcm(path, ss=0, t=None):
    cmd = ["ffmpeg", "-v", "error"]
    if ss: cmd += ["-ss", str(ss)]
    if t:  cmd += ["-t", str(t)]
    cmd += ["-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, dtype=np.float32)

def _ltas(a):
    n, hop = 1024, 512
    fr = np.array([a[i:i+n]*np.hanning(n) for i in range(0, len(a)-n, hop)])
    S = np.abs(np.fft.rfft(fr, axis=1))**2
    keep = S.mean(1) > np.percentile(S.mean(1), 30)      # so quadros com voz
    L = np.log(S[keep].mean(0)+1e-9)
    return L - L.mean()

def _sim(a, b): return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))

def _grab(mp4, t, dest):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(mp4),
                    "-frames:v", "1", "-update", "1", str(dest)], check=True)

def main():
    if len(sys.argv) < 4: print(__doc__); return 64
    modo, mp4 = sys.argv[1], sys.argv[2]
    if modo == "timbre":
        esperada, antiga = sys.argv[3], sys.argv[4]
        r, e, o = (_ltas(_pcm(x, 0, 6)) for x in (mp4, esperada, antiga))
        se, so = _sim(r, e), _sim(r, o)
        print(f"render x voz esperada : {se:.3f}")
        print(f"render x voz antiga   : {so:.3f}")
        ok = se > 0.95 and se > so + 0.05
        print("VEREDITO:", "a voz do render e a esperada" if ok else "NAO bate — o render saiu com a voz errada")
        return 0 if ok else 1
    dest = Path(sys.argv[3]); dest.mkdir(parents=True, exist_ok=True)
    pares = [(a.split("=")[0], float(a.split("=")[1])) for a in sys.argv[4:]]
    for nome, t in pares:
        if modo == "frames":
            _grab(mp4, t, dest/f"{nome}_{t:05.2f}s.png")
        elif modo == "sync":
            _grab(mp4, t-4/24, dest/f"{nome}_ANTES.png")
            _grab(mp4, t+6/24, dest/f"{nome}_DEPOIS.png")
        else:
            print(__doc__); return 64
    print(f"{len(pares)} momento(s) em {dest}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
