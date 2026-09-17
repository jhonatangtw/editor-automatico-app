#!/usr/bin/env bash
# Troca a voz de arquivos de audio pela voz clonada do Jhon (ElevenLabs Voice Changer).
#
#   lib/voz_jhon.sh <pasta-com-wavs> <pasta-de-saida> [voice_id]
#
# Le a chave de ~/.config/hw-creative/.env (ELEVENLABS_API_KEY).
# NAO usar output_format=pcm_* — e exclusivo do plano Pro e devolve 403.
set -euo pipefail
[ $# -ge 2 ] || { echo "uso: voz_jhon.sh <pasta-wav> <pasta-saida> [voice_id]" >&2; exit 64; }
IN="$1"; OUT="$2"; VOICE="${3:-${MVJ_VOICE:-JM55dOm3pyMwSBeLoAJt}}"   # padrao: "Jhon 2"
set -a; . "${MVJ_ENV:-$HOME/.config/hw-creative/.env}"; set +a
: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY ausente}"
mkdir -p "$OUT"; falhas=0
for f in "$IN"/*.wav; do
  n="$(basename "$f" .wav)"
  code=$(curl -sS -m 300 -o "$OUT/$n.mp3" -w "%{http_code}" \
    -X POST "https://api.elevenlabs.io/v1/speech-to-speech/$VOICE?output_format=mp3_44100_128" \
    -H "xi-api-key: $ELEVENLABS_API_KEY" \
    -F "audio=@$f;type=audio/wav" \
    -F "model_id=${MVJ_STS_MODEL:-eleven_multilingual_sts_v2}" \
    -F "voice_settings=${MVJ_VOICE_SETTINGS:-{\"stability\":0.6,\"similarity_boost\":0.85,\"style\":0.15,\"use_speaker_boost\":true\}}" \
    -F "remove_background_noise=false")
  if [ "$code" != "200" ]; then echo "$n: HTTP $code -> $(head -c 240 "$OUT/$n.mp3")" >&2; falhas=$((falhas+1)); continue; fi
  ffmpeg -v error -y -i "$OUT/$n.mp3" -ac 1 -ar 44100 -c:a pcm_s16le "$OUT/${n}_jhon.wav"
  printf '%s  orig %.3fs  ->  jhon %.3fs\n' "$n" \
    "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")" \
    "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/${n}_jhon.wav")"
done
[ "$falhas" -eq 0 ] || { echo "$falhas arquivo(s) falharam" >&2; exit 1; }
echo
echo "AGORA CONFIRA A SINCRONIA antes de trocar o audio no AE:"
echo "  python3 $(dirname "${BASH_SOURCE[0]}")/conferir_voz.py <transcripts-originais> $OUT"
