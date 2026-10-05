#!/bin/bash
# Constrói, valida, renderiza e junta o vídeo com a mixagem.
#   bash scripts/premium/renderizar.sh PASTA_DO_PROJETO [--sem-musica] [--rascunho] [--nome "Meu Reels"]
# Saída: renders/<nome> - premium.mp4 (1080x1920, 30 fps, H.264 ~22 Mbps, AAC 320k)
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
P="$(cd "$1" && pwd)"; shift
SEM=""; RASCUNHO=""; NOME="$(basename "$P")"
while [ $# -gt 0 ]; do case "$1" in
  --sem-musica) SEM="--sem-musica";; --rascunho) RASCUNHO=1;;
  --nome) NOME="$2"; shift;; *) echo "opção desconhecida: $1"; exit 2;; esac; shift; done
for d in /opt/homebrew/opt/node@24/bin /usr/local/opt/node@24/bin; do [ -x "$d/node" ] && export PATH="$d:$PATH"; done
HF="npx --yes hyperframes@${HYPERFRAMES_VERSAO:-0.8.116}"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=8192}"

python3 "$AQUI/construir.py" "$P"
cd "$P"
echo "— check"
$HF check 2>&1 | tail -4
echo "— mixagem"
python3 "$AQUI/mixar.py" "$P" $SEM
MIX=renders/mix.wav; [ -n "$SEM" ] && MIX=renders/mix-sem-musica.wav
[ -f "$MIX" ] || MIX=renders/mix-sem-musica.wav
echo "— render (pode levar alguns minutos)"
rm -f renders/_hf-video.mp4
if [ -n "$RASCUNHO" ]; then Q=(--quality draft); else Q=(--video-bitrate 22M); fi
$HF render --fps 30 "${Q[@]}" -o renders/_hf-video.mp4 > qc/render.log 2>&1 || { tail -20 qc/render.log; exit 1; }
tail -2 qc/render.log
SUF=""; [ -n "$SEM" ] && SUF=" sem musica"
OUT="renders/$NOME - premium$SUF.mp4"
ffmpeg -nostdin -v error -y -i renders/_hf-video.mp4 -i "$MIX" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 \
  -shortest -movflags +faststart "$OUT"
rm -f renders/_hf-video.mp4
echo "ok -> $P/$OUT"
python3 "$AQUI/qc.py" "$OUT" --pasta "$P" || true
