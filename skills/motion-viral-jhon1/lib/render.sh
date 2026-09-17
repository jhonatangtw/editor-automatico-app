#!/usr/bin/env bash
# Render de revisão com trava contra instância dupla.
#   lib/render.sh <projeto.aep> <comp> <saida.mp4>
# Dois aerender gravando no mesmo caminho produzem um MP4 sem moov atom e um log vazio —
# aconteceu no AD04 (10/09/2026). Este wrapper recusa rodar se já houver aerender vivo,
# grava o log ao lado da saída e valida o arquivo com ffprobe antes de dizer "pronto".
set -euo pipefail
[ $# -eq 3 ] || { echo "uso: render.sh <projeto.aep> <comp> <saida.mp4>" >&2; exit 64; }
AEP="$1"; COMP="$2"; OUT="$3"; LOG="${OUT%.mp4}.aerender.log"
AER="${MVJ_AERENDER:-/Applications/Adobe After Effects 2026/aerender}"
if pgrep -f "aerender" >/dev/null 2>&1; then echo "já existe um aerender rodando — esperar ele terminar, não empilhar" >&2; exit 3; fi
rm -f "$OUT"
"$AER" -project "$AEP" -comp "$COMP" -output "$OUT" > "$LOG" 2>&1 || true
if ! ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" >/dev/null 2>&1; then
  echo "render inválido (ffprobe falhou). Fim do log:" >&2; tail -8 "$LOG" >&2; exit 1; fi
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames -of compact "$OUT" | head -3
ffmpeg -i "$OUT" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume" | sed 's/.*\] //'
