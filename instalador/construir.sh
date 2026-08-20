#!/bin/bash
# Empacota o Editor Automático em .app -> .pkg -> .dmg
#
# ⚠️ `pkgbuild --component App.app` grava um payload VAZIO (78 bytes) — o Bom
# lista os arquivos, o Payload não os contém, e o instalador roda "com sucesso"
# sem instalar nada. Só se descobre abrindo o pacote. Use --root com uma pasta
# de staging: o conteúdo dela é que vira o payload.
#
# Domínio de usuário (enable_currentUserHome): instala em ~/Applications SEM
# senha de administrador. Mesma decisão do Tools PRO — pedir senha de admin num
# instalador não assinado faz metade da turma desistir na primeira tela.
#
# NÃO assinado (sem Developer ID): Gatekeeper reclama na 1ª abertura.
set -euo pipefail
cd "$(dirname "$0")/.."

APP="Editor Automático"        # o que o usuário vê
BIN="EditorAutomatico"         # o nome do EXECUTÁVEL — precisa ser ASCII
#
# ⚠️ Acento no nome do executável QUEBRA a assinatura. O codesign responde
# "code has no resources but signature indicates they must be present" e o
# macOS recusa abrir pelo Finder — mas o binário roda pelo terminal, então o
# defeito passa em qualquer teste feito por linha de comando. Toda máquina de
# aluno bateria nisso. A pasta .app PODE ter acento; só o executável não.
ID="com.editorblackbelt.editorautomatico"
VER="$(python3 -c "import json;print(json.load(open('version.json'))['version'])")"
# CAMINHOS ABSOLUTOS. Com caminho relativo o pkgbuild responde
# "parent directory ./X.app does not exist" mesmo com a pasta ali na frente.
DIST="$PWD/instalador/saida"
STAGE="$PWD/instalador/stage"

echo "▸ limpando"
rm -rf build "$DIST" "$STAGE" ./*.spec

# No CI não existe .venv — lá o Python já vem preparado pelo runner.
PYI=".venv/bin/pyinstaller"
[ -x "$PYI" ] || PYI="pyinstaller"

echo "▸ empacotando com PyInstaller ($VER)"
"$PYI" \
  --name "$BIN" --windowed --noconfirm --clean \
  --distpath "$DIST" \
  --add-data "web:web" \
  --add-data "version.json:." \
  --add-data "regra:regra" \
  --hidden-import webview.platforms.cocoa \
  --osx-bundle-identifier "$ID" \
  app.py >/dev/null

[ -d "$DIST/$BIN.app" ] || { echo "ERRO: PyInstaller não gerou o .app"; exit 1; }

echo "▸ nome de exibição acentuado + assinatura"
mv "$DIST/$BIN.app" "$DIST/$APP.app"
/usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $APP" \
  "$DIST/$APP.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP" \
  "$DIST/$APP.app/Contents/Info.plist"

# O PyInstaller tenta assinar e falha (erro -10) — refazemos por fora.
codesign --force --deep --sign - --identifier "$ID" "$DIST/$APP.app" >/dev/null 2>&1

if ! codesign --verify --strict "$DIST/$APP.app" 2>/dev/null; then
  echo "ERRO: a assinatura ficou inválida — o macOS vai recusar abrir o app."
  codesign --verify --strict "$DIST/$APP.app" 2>&1 | head -3
  exit 1
fi
echo "  assinatura válida"

echo "▸ staging"
mkdir -p "$STAGE"
cp -R "$DIST/$APP.app" "$STAGE/"

echo "▸ .dmg (canal principal — arrastar para Aplicativos)"
hdiutil create -volname "$APP" -srcfolder "$DIST/$APP.app" \
  -ov -format UDZO "$DIST/$APP $VER.dmg" >/dev/null
echo "  $(du -h "$DIST/$APP $VER.dmg" | cut -f1)"

# O .pkg vem DEPOIS do dmg de propósito: se o pkgbuild falhar (ele precisa
# escrever em temporário do sistema e falha dentro de sandbox), o aluno ainda
# tem um instalador funcional em vez de nenhum.
echo "▸ .pkg (domínio do usuário — sem senha de admin)"
set +e
pkgbuild --root "$STAGE" --install-location "/Applications" \
  --identifier "$ID" --version "$VER" "$DIST/base.pkg" >/dev/null 2>&1
PKG_OK=$?
set -e
if [ $PKG_OK -ne 0 ] || [ ! -f "$DIST/base.pkg" ]; then
  echo "  ⚠ pkgbuild falhou (rode fora de sandbox). O .dmg acima está pronto."
  rm -rf "$STAGE"; exit 0
fi

cat > "$STAGE/dist.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
  <title>$APP</title>
  <domains enable_currentUserHome="true" enable_anywhere="false" enable_localSystem="false"/>
  <options customize="never" require-scripts="false" hostArchitectures="arm64,x86_64"/>
  <choices-outline><line choice="app"/></choices-outline>
  <choice id="app" title="$APP"><pkg-ref id="$ID"/></choice>
  <pkg-ref id="$ID" version="$VER">base.pkg</pkg-ref>
</installer-gui-script>
XML

productbuild --distribution "$STAGE/dist.xml" --package-path "$DIST" \
  "$DIST/$APP $VER.pkg" >/dev/null
rm -f "$DIST/base.pkg"

echo "▸ conferindo o payload (o erro que passa calado)"
BYTES=$(pkgutil --expand "$DIST/$APP $VER.pkg" "$STAGE/check" >/dev/null 2>&1 \
        && stat -f%z "$STAGE/check/base.pkg/Payload" 2>/dev/null || echo 0)
if [ "$BYTES" -lt 100000 ]; then
  echo "ERRO: payload de $BYTES bytes — o pacote está vazio."; exit 1
fi
echo "  payload: $(echo "$BYTES" | awk '{printf "%.1f MB", $1/1048576}')"

rm -rf "$STAGE"
echo
echo "pronto:"
ls -lh "$DIST" | awk 'NR>1 && ($9 ~ /pkg|dmg/) {print "   " $5 "  " $9}'
