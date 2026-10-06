#!/bin/bash
# Mídia de EXEMPLO para a banca visual da prévia de entregas (0.22.1).
# Tudo sintético (ffmpeg testsrc/sine) — nenhum rosto, nenhum produto, nada de
# cliente. Fica em testes/visual/amostras/ (fora do git: regenera em segundos).
# Uso: testes/visual/gerar-amostras.sh
set -e
cd "$(dirname "$0")"
OUT=amostras
mkdir -p "$OUT"
F="ffmpeg -v error -y"
# 9 imagens 9:16 (cada uma de um gerador/tom diferente)
i=1
for src in "testsrc2=s=540x960" "smptehdbars=s=540x960" "mandelbrot=s=540x960" \
           "rgbtestsrc=s=540x960" "testsrc=s=540x960" "cellauto=s=540x960:rule=110" \
           "life=s=540x960:mold=10:ratio=0.5:death_color=#2b2010:life_color=#f2b33d" \
           "gradients=s=540x960:c0=0x1d2128:c1=0xf2b33d" "yuvtestsrc=s=540x960"; do
  $F -f lavfi -i "$src" -frames:v 1 "$OUT/broll-$(printf %02d $i).png"
  i=$((i+1))
done
# folha de contato larga (QC): 6 quadros lado a lado
$F -f lavfi -i "testsrc2=s=320x568:r=6" -frames:v 1 -vf "tile=6x1:padding=8:color=0x0f1115" "$OUT/qc-folha-de-contato.jpg" 2>/dev/null || \
$F -f lavfi -i "testsrc2=s=1920x568" -frames:v 1 "$OUT/qc-folha-de-contato.jpg"
# vídeos curtos em 9:16, 16:9 e 1:1, com som
$F -f lavfi -i "testsrc2=s=360x640:r=30" -f lavfi -i "sine=f=330:r=44100" -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest -movflags +faststart "$OUT/avatar-hook-9x16.mp4"
$F -f lavfi -i "smptehdbars=s=640x360:r=30" -f lavfi -i "sine=f=440:r=44100" -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest -movflags +faststart "$OUT/broll-produto-16x9.mp4"
$F -f lavfi -i "mandelbrot=s=480x480:r=30" -f lavfi -i "sine=f=550:r=44100" -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest -movflags +faststart "$OUT/broll-detalhe-1x1.mp4"
# capa (1º quadro) de cada vídeo: o servidor da banca devolve isto em /api/midia/quadro
for v in "$OUT"/*.mp4; do $F -ss 0 -i "$v" -frames:v 1 -q:v 4 "$v.capa.jpg"; done
# locução de exemplo: seno com volume variando (a onda tem forma)
$F -f lavfi -i "aevalsrc='0.8*sin(2*PI*220*t)*abs(sin(2*PI*0.7*t))*(0.4+0.6*abs(sin(2*PI*0.13*t)))':s=44100:d=12" -c:a libmp3lame -b:a 96k "$OUT/locucao-hook-01.mp3"
# dimensões, duração e forma da onda, medidas pelo MESMO código do app
# (nucleo/midia.py): o mock da banca devolve isto nas rotas /api/midia/*
( cd ../.. && python3 - <<'PY'
import json, os, sys
sys.path.insert(0, ".")
from nucleo import midia
midia.CACHE = "testes/visual/amostras/.cache"
pasta = "testes/visual/amostras"
dados = {}
for n in sorted(os.listdir(pasta)):
    c = os.path.join(pasta, n)
    if not os.path.isfile(c) or not midia.tipo_de(c):
        continue
    d = midia.info(c)
    if d["tipo"] == "audio":
        d.update(picos110=midia.picos(c, 110)["picos"], picos64=midia.picos(c, 64)["picos"])
    dados[n] = d
json.dump(dados, open(os.path.join(pasta, "dados.json"), "w"), ensure_ascii=False)
print("dados.json:", len(dados), "arquivos")
PY
)
ls -la "$OUT"
