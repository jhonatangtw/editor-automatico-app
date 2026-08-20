# Empacota o Editor Automático no Windows: .exe + instalador NSIS.
#
# Roda no CI (windows-latest) e numa máquina Windows igual. O PyInstaller NÃO
# faz build cruzado — .exe só sai de Windows, e é por isso que o instalador do
# Windows é construído por CI e não aqui no Mac.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$ver = (Get-Content version.json -Raw -Encoding UTF8 | ConvertFrom-Json).version
$bin = "EditorAutomatico"
$dist = "$PWD\instalador\saida"

Write-Host "> empacotando com PyInstaller ($ver)"
Remove-Item -Recurse -Force build, $dist -ErrorAction SilentlyContinue

# `edgechromium` é a plataforma do pywebview no Windows (WebView2, que já vem
# com o Edge). Sem o hidden-import a janela não abre no app empacotado.
pyinstaller --name $bin --windowed --noconfirm --clean `
  --distpath $dist `
  --add-data "web;web" `
  --add-data "version.json;." `
  --hidden-import webview.platforms.edgechromium `
  app.py
if (-not (Test-Path "$dist\$bin\$bin.exe")) { throw "PyInstaller não gerou o .exe" }

Write-Host "> conferindo se o binário responde (modo MCP, sem abrir janela)"
$saida = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' |
         & "$dist\$bin\$bin.exe" --mcp 2>$null
if ($saida -notmatch '"tools"') { throw "o .exe empacotado não respondeu como servidor MCP" }
Write-Host "  ok"

Write-Host "> instalador NSIS"
makensis /DVERSAO=$ver instalador\windows\EditorAutomatico.nsi
if (-not (Test-Path "$dist\EditorAutomatico-Instalador.exe")) { throw "o NSIS não gerou o instalador" }

$mb = [math]::Round((Get-Item "$dist\EditorAutomatico-Instalador.exe").Length / 1MB, 1)
Write-Host "  pronto: EditorAutomatico-Instalador.exe ($mb MB)"
