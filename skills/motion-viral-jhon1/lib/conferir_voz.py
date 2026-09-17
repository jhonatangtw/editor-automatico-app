#!/usr/bin/env python3
"""Prova que a voz trocada NAO andou no tempo — obrigatorio antes de trocar o audio
sob um motion ja sincronizado.

    conferir_voz.py <pasta-transcripts-json> <pasta-audio-convertido> [tolerancia_ms]

Retranscreve cada WAV convertido palavra a palavra e compara com o transcript do
original. Sai != 0 se alguma PALAVRA-ANCORA passar da tolerancia.
Desvio isolado grande no INICIO de palavra depois de pausa costuma ser jitter do
Whisper, nao deslocamento: confira o FIM da mesma palavra antes de condenar.
"""
import json, sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print(__doc__); return 64
    tdir, adir = Path(sys.argv[1]), Path(sys.argv[2])
    tol = float(sys.argv[3])/1000 if len(sys.argv) > 3 else 0.100
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    pior, ruins = 0.0, 0
    for wav in sorted(adir.glob("*_jhon.wav")):
        base = wav.name.replace("_jhon.wav", "")
        cand = [p for p in tdir.glob("*.json") if base.lower().replace(" ","_") in p.stem.lower().replace(" ","_")]
        if not cand:
            print(f"{base}: sem transcript original correspondente em {tdir}"); continue
        orig = json.load(open(cand[0]))
        segs, _ = m.transcribe(str(wav), language="pt", word_timestamps=True)
        conv = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
        json.dump([{"w": w, "t": round(a, 2), "e": round(b, 2)} for w, a, b in conv],
                  open(adir / f"{base}_jhon_palavras.json", "w"), ensure_ascii=False)
        n = min(len(orig), len(conv))
        if len(orig) != len(conv):
            print(f"{base}: ATENCAO contagem difere — orig {len(orig)} x conv {len(conv)}")
        di = [conv[k][1]-orig[k]["t"] for k in range(n)]
        de = [conv[k][2]-orig[k]["e"] for k in range(n)]
        mx = max(abs(d) for d in di) if di else 0
        pior = max(pior, mx)
        print(f"{base}: {n} palavras | inicio: medio {sum(di)/n*1000:+.0f} ms, pior {mx*1000:.0f} ms"
              f" | fim: pior {max(abs(d) for d in de)*1000:.0f} ms")
        for k in range(n):
            if abs(di[k]) > tol:
                ruins += 1
                print(f"    ! {orig[k]['w']:<14} inicio {di[k]*1000:+.0f} ms  fim {de[k]*1000:+.0f} ms"
                      f"   {'(so o inicio: provavel jitter apos pausa)' if abs(de[k])<=tol else '(DESLOCOU DE VERDADE)'}")
    print(f"\npior desvio de inicio: {pior*1000:.0f} ms ({pior*24:.1f} quadros a 24fps) | fora da tolerancia: {ruins}")
    return 0 if ruins == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
