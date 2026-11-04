#!/usr/bin/env python3
"""Confere cada áudio de TTS contra o texto esperado (Whisper medium). Mostra WER e as diferenças.
    python3 qc_tts.py <blocos.json> <pasta_audios> ["Produto"]
Diferença de pontuação/número por extenso é falso positivo. Trecho suspeito: retranscreva ISOLADO antes de refazer
(o Whisper em passada única erra palavra curta). "-ed" que some antes de "t" é pronúncia natural, não refazer.
"""
import json, sys, os, re, difflib
from faster_whisper import WhisperModel

blocos, D = json.load(open(sys.argv[1])), sys.argv[2]
prod = sys.argv[3] if len(sys.argv) > 3 else ""
m = WhisperModel("medium", compute_type="int8")
norm = lambda s: re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("’", "'")).split()
for b in blocos:
    f = os.path.join(D, b["id"] + ".mp3")
    if not os.path.exists(f): print(b["id"], "FALTA"); continue
    seg, _ = m.transcribe(f, language="en", initial_prompt=prod)
    a, o = norm(b["txt"]), norm(" ".join(s.text for s in seg))
    ops = [x for x in difflib.SequenceMatcher(None, a, o).get_opcodes() if x[0] != "equal"]
    wer = sum(max(i2 - i1, j2 - j1) for _, i1, i2, j1, j2 in ops) / max(1, len(a))
    print(f'{b["id"]:9s} WER={wer:5.1%}', [(" ".join(a[i1:i2]), " ".join(o[j1:j2])) for _, i1, i2, j1, j2 in ops][:6], flush=True)
