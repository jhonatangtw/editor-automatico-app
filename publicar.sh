#!/bin/bash
# Publica uma versão: marca a tag e deixa o CI construir os DOIS instaladores.
#
# Por que não construir aqui: o PyInstaller não faz build cruzado. O .exe do
# Windows só nasce numa máquina Windows, e o runner do GitHub é a máquina
# Windows que não precisa existir na mesa de ninguém.
#
# O contrato do auto-update são TRÊS arquivos na Release "latest":
#   EditorAutomatico.dmg              — Mac  (nome FIXO: a URL não pode mudar)
#   EditorAutomatico-Instalador.exe   — Windows
#   version.json                      — o mesmo que viaja dentro do app
set -e
cd "$(dirname "$0")"

VER=$(python3 -c "import json;print(json.load(open('version.json'))['version'])")
REPO=$(python3 -c "import json;print(json.load(open('version.json'))['repo'])")
TAG="v$VER"

echo "▸ versão $VER  ->  $REPO"

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "x a Release $TAG ja existe. Suba a versao no version.json antes." >&2
  exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  echo "x ha mudanca nao commitada. Commite antes de publicar." >&2
  exit 1
fi

echo "▸ empurrando main e a tag"
git push -q origin main
git tag -f "$TAG" >/dev/null
git push -q origin "$TAG" --force

echo "▸ o CI esta construindo Mac e Windows (leva ~10 min)"
sleep 8
ID=$(gh run list --repo "$REPO" --workflow publicar.yml --limit 1 --json databaseId \
     --jq '.[0].databaseId')
gh run watch "$ID" --repo "$REPO" --exit-status

echo "▸ conferindo o que o app vai enxergar"
for A in EditorAutomatico.dmg EditorAutomatico-Instalador.exe version.json; do
  CODE=$(curl -sIL -o /dev/null -w '%{http_code}' \
        "https://github.com/$REPO/releases/latest/download/$A")
  echo "   $A -> $CODE"
  [ "$CODE" = "200" ] || { echo "x $A nao respondeu" >&2; exit 1; }
done
PUB=$(curl -sL "https://github.com/$REPO/releases/latest/download/version.json" \
      | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])")
[ "$PUB" = "$VER" ] && echo "v publicado: latest responde $PUB" \
  || { echo "x latest responde $PUB, nao $VER" >&2; exit 1; }
