#!/bin/bash
# Confere o que o Editor de Reels precisa. Não instala nada sozinho:
# o Editor Automático (aba Ambiente) instala ffmpeg, Whisper e Node.
#   bash scripts/requisitos.sh
ok=0
linha(){ printf "  %-22s %s\n" "$1" "$2"; }

# Node 22+ e HyperFrames: mesmo critério do Editor Automático (hf.sh)
. "$(dirname "$0")/hf.sh"

echo "Editor de Reels — requisitos"
if [ -n "$NODE_OK" ]; then linha "Node.js" "ok ($("$NODE_OK" -v))"
else
  v=$(command -v node >/dev/null && node -v)
  linha "Node.js" "FALTA o 22 ou mais novo${v:+ (achei só $v)} — $HF_FALTA_MSG"; ok=1
fi

if [ -n "$NODE_OK" ] || [ "$HF_ORIGEM" != "npx" ]; then
  hv=$("${HF[@]}" --version 2>/dev/null | tail -1)
  if [ -n "$hv" ]; then linha "HyperFrames" "ok ($hv, $HF_ORIGEM)"
  elif [ "$HF_ORIGEM" = "npx" ]; then linha "HyperFrames" "não respondeu (sem internet na 1ª vez?) — $HF_FALTA_MSG"; ok=1
  else linha "HyperFrames" "o atalho não respondeu — no Editor Automático: Ambiente › HyperFrames › Reparar"; ok=1; fi
else
  linha "HyperFrames" "precisa do Node 22+ — $HF_FALTA_MSG"; ok=1
fi

for b in ffmpeg ffprobe; do
  command -v $b >/dev/null && linha "$b" "ok" || { linha "$b" "FALTA"; ok=1; }
done
if command -v ffmpeg >/dev/null; then
  f=$(ffmpeg -hide_banner -filters 2>/dev/null)
  for flt in loudnorm ebur128 sidechaincompress freezedetect atempo; do
    echo "$f" | grep -q " $flt " || { linha "ffmpeg: $flt" "FALTA (ffmpeg incompleto)"; ok=1; }
  done
fi

PY=${PYTHON:-python3}
if $PY -c "import whisper" 2>/dev/null; then linha "Whisper (python)" "ok"; else linha "Whisper (python)" "FALTA: pip3 install --user openai-whisper"; ok=1; fi
$PY -c "import numpy" 2>/dev/null && linha "numpy" "ok" || { linha "numpy" "FALTA"; ok=1; }

# Tools PRO (só nas fases 2 e 3 — Premiere)
if [ -f "$HOME/.editor-black-belt/mcp-ppro.json" ]; then linha "Tools PRO (Premiere)" "conectado pelo menos uma vez"; else linha "Tools PRO (Premiere)" "não achei a conexão (fases 2–3 precisam: painel › Conectar IA)"; fi

[ $ok -eq 0 ] && echo "Tudo pronto." || echo "Falta algo acima. As fases 1, 5, 6 e 7 não rodam sem ffmpeg/Whisper/Node."
exit $ok
