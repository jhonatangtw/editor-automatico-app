#!/usr/bin/env python3
"""
transcribe.py — transcreve os .mp3 de _QA/audio e gera transcrição com timestamps.

FUNCIONA quando há acesso de rede para baixar o modelo (ex.: rodando a tarefa NO
COMPUTADOR do usuário). No sandbox em nuvem o download do modelo costuma estar
BLOQUEADO (HuggingFace/OpenAI 403) — nesse caso, rode a tarefa no computador.

Uso:
    pip install faster-whisper
    python transcribe.py "<PASTA>/_QA/audio" "<PASTA>/_QA/transcripts" [modelo]

modelo: tiny.en | base.en | small.en | medium.en  (padrão: small.en)
        Use um modelo multilíngue (ex.: small) e language=None se o áudio não for inglês.

Saída por vídeo:
  <nome>.txt       -> linhas "[  ini-  fim] texto"  (bom pra achar fala corrida/loop/corte)
  <nome>.full.txt  -> texto corrido (bom pra comparar com a copy)
"""
import os, sys, glob
from faster_whisper import WhisperModel

src = sys.argv[1] if len(sys.argv) > 1 else "_QA/audio"
out = sys.argv[2] if len(sys.argv) > 2 else "_QA/transcripts"
model_name = sys.argv[3] if len(sys.argv) > 3 else "small.en"
lang = "en" if model_name.endswith(".en") else None

os.makedirs(out, exist_ok=True)
print(f"Carregando modelo {model_name} ...", flush=True)
model = WhisperModel(model_name, device="cpu", compute_type="int8")

for f in sorted(glob.glob(os.path.join(src, "*.mp3"))):
    name = os.path.splitext(os.path.basename(f))[0]
    dst = os.path.join(out, name + ".txt")
    if os.path.exists(dst):
        print("skip (já existe):", name, flush=True); continue
    segs, _ = model.transcribe(f, beam_size=1, language=lang)
    lines, full = [], []
    for s in segs:
        lines.append(f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}")
        full.append(s.text.strip())
    open(dst, "w").write("\n".join(lines))
    open(os.path.join(out, name + ".full.txt"), "w").write(" ".join(full))
    print("DONE", name, flush=True)

print("ALL DONE ->", out, flush=True)
