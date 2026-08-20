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

Write-Host "> conferindo se o binario responde (modo MCP, sem abrir janela)"
$saida = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' |
         & "$dist\$bin\$bin.exe" --mcp 2>$null
if ($saida -notmatch '"tools"') { throw "o .exe empacotado nao respondeu como servidor MCP" }
Write-Host "  ok"

Write-Host "> instalador NSIS"
# O choco instala o NSIS mas o PATH desta sessao nao enxerga o makensis — a
# variavel so e recarregada num shell novo. Procurar onde ele mora resolve aqui
# e na maquina de quem for construir a mao.
$nsis = (Get-Command makensis -ErrorAction SilentlyContinue).Source
if (-not $nsis) {
  foreach ($c in @("$env:ProgramFiles\NSIS\makensis.exe",
                   "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
                   "$env:ChocolateyInstall\bin\makensis.exe")) {
    if (Test-Path $c) { $nsis = $c; break }
  }
}
if (-not $nsis) { throw "makensis nao encontrado. Instale o NSIS (choco install nsis)." }
Write-Host "  usando $nsis"
& $nsis /DVERSAO=$ver instalador\windows\EditorAutomatico.nsi
if ($LASTEXITCODE -ne 0) { throw "o NSIS falhou (codigo $LASTEXITCODE)" }
if (-not (Test-Path "$dist\EditorAutomatico-Instalador.exe")) { throw "o NSIS nao gerou o instalador" }

$mb = [math]::Round((Get-Item "$dist\EditorAutomatico-Instalador.exe").Length / 1MB, 1)
Write-Host "  pronto: EditorAutomatico-Instalador.exe ($mb MB)"
