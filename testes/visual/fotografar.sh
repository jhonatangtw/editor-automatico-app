#!/bin/bash
# Fotografa as telas com a ponte falsa (mock.js) no Chrome headless.
# Uso: testes/visual/fotografar.sh [pasta-de-saida]
# Perfil próprio e porta HTTP própria: não encosta no Chrome nem no app de ninguém.
set -e
cd "$(dirname "$0")/../.."
OUT="${1:-testes/visual/fotos}"
mkdir -p "$OUT"
rm -f "$OUT"/*.png
PORTA=8765
python3 -m http.server $PORTA --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 0.8
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
foto() { # nome largura altura query
  # perfil novo por foto e prazo de 30 s: o Chrome headless às vezes não sai
  # sozinho depois de gravar o PNG, e um perfil travado segura a próxima foto
  local P; P=$(mktemp -d)
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$P" \
    --no-first-run --no-default-browser-check \
    --window-size="$2,$3" --virtual-time-budget=4000 --force-device-scale-factor=1 \
    --screenshot="$OUT/$1.png" "http://127.0.0.1:$PORTA/testes/visual/tela.html?$4" >/dev/null 2>&1 &
  local C=$!
  for _ in $(seq 60); do
    [ -s "$OUT/$1.png" ] && sleep 1 && break
    sleep 0.5
  done
  kill $C 2>/dev/null; wait $C 2>/dev/null || true
  rm -rf "$P"
  echo "$OUT/$1.png"
}
foto inicio-cheio 1240 820 "cenario=cheio"
foto inicio-vazio 1240 820 "cenario=vazio"
foto contas-cheio 1240 820 "cenario=cheio&aba=contas"
foto contas-vazio 1240 820 "cenario=vazio&aba=contas"
foto contas-menu 1240 820 "cenario=cheio&aba=contas&menu=elevenlabs"
foto ambiente-vazio 1240 820 "cenario=vazio&aba=ambiente"
foto historico-cheio 1240 820 "cenario=cheio&aba=projetos"
foto conversa 1240 820 "cenario=cheio&aba=chat"
foto guia 1240 820 "cenario=cheio&aba=guia"
foto guia-minimo 1020 680 "cenario=cheio&aba=guia"
foto guia-webinario 1240 820 "cenario=cheio&aba=guia&grupo=webinario"
foto ambiente-cheio 1240 820 "cenario=cheio&aba=ambiente"
foto inicio-minimo 1020 680 "cenario=vazio"
foto contas-minimo 1020 680 "cenario=cheio&aba=contas"
foto inicio-pequeno 820 640 "cenario=vazio"
