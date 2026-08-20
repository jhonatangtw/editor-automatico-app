; Instalador do Editor Automático para Windows.
;
; RequestExecutionLevel user, e a instalação vai para %LOCALAPPDATA%: instalar
; sem pedir senha de administrador é a mesma decisão do Tools PRO — pedir admin
; num instalador não assinado faz metade da turma desistir na primeira tela.
;
; ⚠️ NÃO assinado (sem certificado Windows): o SmartScreen avisa na 1ª execução.
; O caminho é "Mais informações" → "Executar assim mesmo".

Unicode true
!include "MUI2.nsh"

!define NOME "Editor Automático"
!define BIN  "EditorAutomatico"
!ifndef VERSAO
  !define VERSAO "0.0.0"
!endif
!define CHAVE "Software\Microsoft\Windows\CurrentVersion\Uninstall\EditorAutomatico"

Name "${NOME}"
OutFile "..\saida\EditorAutomatico-Instalador.exe"
InstallDir "$LOCALAPPDATA\Programs\${BIN}"
InstallDirRegKey HKCU "Software\${BIN}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma

VIProductVersion "${VERSAO}.0"
VIAddVersionKey "ProductName"     "${NOME}"
VIAddVersionKey "FileDescription" "Editor Automático"
VIAddVersionKey "FileVersion"     "${VERSAO}"
VIAddVersionKey "LegalCopyright"  "Editor Black Belt"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${BIN}.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir o ${NOME} agora"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"
!insertmacro MUI_LANGUAGE "English"

Section "Editor Automático" SecApp
  SectionIn RO
  ; troca a árvore inteira: sobra de versão anterior é o que produz o app que
  ; roda com metade do código novo e metade do velho
  RMDir /r "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "..\saida\${BIN}\*.*"

  CreateDirectory "$SMPROGRAMS\${NOME}"
  CreateShortCut  "$SMPROGRAMS\${NOME}\${NOME}.lnk" "$INSTDIR\${BIN}.exe"
  CreateShortCut  "$DESKTOP\${NOME}.lnk"            "$INSTDIR\${BIN}.exe"

  WriteRegStr HKCU "Software\${BIN}" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "${CHAVE}" "DisplayName"     "${NOME}"
  WriteRegStr HKCU "${CHAVE}" "DisplayVersion"  "${VERSAO}"
  WriteRegStr HKCU "${CHAVE}" "Publisher"       "Editor Black Belt"
  WriteRegStr HKCU "${CHAVE}" "DisplayIcon"     "$INSTDIR\${BIN}.exe"
  WriteRegStr HKCU "${CHAVE}" "UninstallString" "$INSTDIR\Desinstalar.exe"
  WriteRegDWORD HKCU "${CHAVE}" "NoModify" 1
  WriteRegDWORD HKCU "${CHAVE}" "NoRepair" 1
  WriteUninstaller "$INSTDIR\Desinstalar.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\${NOME}\${NOME}.lnk"
  RMDir  "$SMPROGRAMS\${NOME}"
  Delete "$DESKTOP\${NOME}.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "${CHAVE}"
  DeleteRegKey HKCU "Software\${BIN}"
  ; os projetos e as chaves do usuário NÃO são apagados: desinstalar o app não
  ; é apagar o trabalho dele.
SectionEnd
