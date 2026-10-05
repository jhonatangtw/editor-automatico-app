#!/bin/bash
# Confere o que o Editor de Reels precisa. Não instala nada sozinho:
# o Editor Automático (aba Ambiente) instala ffmpeg, Whisper e Node.
#   bash scripts/requisitos.sh
ok=0
linha(){ printf "  %-22s %s\n" "$1" "$2"; }

# Node 24: no Mac com Homebrew ele pode estar "keg-only" fora do PATH
for d in /opt/homebrew/opt/node@24/bin /usr/local/opt/node@24/bin; do
  [ -x "$d/node" ] && case ":$PATH:" in *":$d:"*) ;; *) export PATH="$d:$PATH";; esac
done

echo "Editor de Reels — requisitos"
if command -v node >/dev/null; then
  v=$(node -v); maj=${v#v}; maj=${maj%%.*}
  if [ "$maj" -ge 22 ]; then linha "Node.js" "ok ($v)"; else linha "Node.js" "VERSÃO VELHA ($v) — precisa 24"; ok=1; fi
else linha "Node.js" "FALTA (instale o Node 24)"; ok=1; fi

if command -v npx >/dev/null; then
  hv=$(npx --yes hyperframes@${HYPERFRAMES_VERSAO:-0.8.116} --version 2>/dev/null | tail -1)
  [ -n "$hv" ] && linha "HyperFrames (npx)" "ok ($hv)" || { linha "HyperFrames (npx)" "não respondeu (sem internet na 1ª vez?)"; ok=1; }
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
