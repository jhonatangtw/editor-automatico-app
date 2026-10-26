#!/usr/bin/env python3
"""Transcreve um vídeo/áudio com timestamp por palavra (faster-whisper medium, inglês).
    python3 transcrever.py <arquivo> <saida_sem_extensao> ["termos, do, produto"]
Gera <saida>.json (lista {w,s,e}) e <saida>.txt (segmentos com tempo).
Atenção: em passada longa o Whisper pula trechos/inventa — confira a legenda queimada da referência.
"""
import sys, json
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
prompt = sys.argv[3] if len(sys.argv) > 3 else "supplement, upsell, bottles, triple dose, money-back guarantee"
m = WhisperModel("medium", compute_type="int8")
seg, _ = m.transcribe(src, language="en", word_timestamps=True, initial_prompt=prompt)
ws, txt = [], []
for s in seg:
    txt.append(f"[{s.start:7.2f}] {s.text.strip()}")
    for w in s.words:
        ws.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})
json.dump(ws, open(out + ".json", "w"))
open(out + ".txt", "w").write("\n".join(txt))
print(len(ws), "palavras")
