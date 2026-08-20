#!/bin/bash
# Publica uma versão: empacota, sobe na Release e deixa o auto-update ver.
#
# O contrato do auto-update são DOIS arquivos na Release "latest":
#   EditorAutomatico.dmg  — nome FIXO, senão a URL de download muda a cada versão
#   version.json          — o mesmo que viaja dentro do app
#
# ⚠️ O repositório é o do `version.json`. Se a conta ativa do `gh` não for a dona
# dele, o release falha aqui e não pela metade — que é o que se quer.
set -e
cd "$(dirname "$0")"

VER=$(python3 -c "import json;print(json.load(open('version.json'))['version'])")
REPO=$(python3 -c "import json;print(json.load(open('version.json'))['repo'])")
NOTAS=$(python3 -c "import json;print(json.load(open('version.json')).get('notes',''))")
TAG="v$VER"

echo "▸ versão $VER  →  $REPO"

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "✗ a Release $TAG já existe. Suba a versão no version.json antes." >&2
  exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  echo "✗ há mudança não commitada. Commite antes de publicar." >&2
  exit 1
fi

echo "▸ empacotando…"
./instalador/construir.sh

DMG=$(ls -t "instalador/saida/"*.dmg | head -1)
[ -f "$DMG" ] || { echo "✗ o build não gerou .dmg" >&2; exit 1; }

REL="instalador/release"
rm -rf "$REL"; mkdir -p "$REL"
cp "$DMG" "$REL/EditorAutomatico.dmg"
cp version.json "$REL/version.json"

echo "▸ criando a Release $TAG…"
git tag -f "$TAG" >/dev/null
git push -q origin "$TAG" --force
gh release create "$TAG" "$REL/EditorAutomatico.dmg" "$REL/version.json" \
  --repo "$REPO" --title "$TAG" --notes "$NOTAS" --latest

echo "▸ conferindo o que o app vai enxergar…"
sleep 3
PUB=$(curl -sL "https://github.com/$REPO/releases/latest/download/version.json" \
      | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])")
[ "$PUB" = "$VER" ] && echo "✓ publicado: latest responde $PUB" \
  || { echo "✗ latest responde $PUB, não $VER" >&2; exit 1; }
