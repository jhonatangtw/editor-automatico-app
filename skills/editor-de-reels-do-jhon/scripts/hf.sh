# Acha um Node >= 22 e o HyperFrames pelo MESMO critério do Editor Automático.
#   . "$(dirname "$0")/hf.sh"     (requisitos.sh, premium/renderizar.sh)
# Depois de carregado:
#   NODE_OK   caminho do Node 22+ (vazio se não há) — já vai na frente do PATH
#   HF        comando do HyperFrames, como array:  "${HF[@]}" check
#   HF_ORIGEM "atalho do Editor Automático" ou "npx"
#
# Preferência: o atalho que o app instala (~/.editorblackbelt/bin/hyperframes,
# .cmd no Windows) — versão fixa, testada com render, Node certo por dentro.
# Sem ele: npx na versão abaixo (baixa na 1ª vez, precisa de internet).
HYPERFRAMES_VERSAO="${HYPERFRAMES_VERSAO:-0.8.134}"

_hf_maior() { "$1" -v 2>/dev/null | sed -nE 's/^v([0-9]+)\..*/\1/p'; }

# keg-only do Homebrew primeiro (Apple Silicon e Intel): o `node` do PATH pode
# ser velho e vir na frente. Depois todo `node` do PATH. No Windows (Git Bash),
# a pasta de instalação padrão do Node.
_hf_cands=()
for _b in /opt/homebrew /usr/local; do
  for _f in node@24 node@22 node; do _hf_cands+=("$_b/opt/$_f/bin/node"); done
done
while IFS= read -r _p; do [ -n "$_p" ] && _hf_cands+=("$_p"); done < <(type -ap node 2>/dev/null)
[ -n "${PROGRAMFILES:-}" ] && _hf_cands+=("$PROGRAMFILES/nodejs/node.exe")
[ -n "${LOCALAPPDATA:-}" ] && _hf_cands+=("$LOCALAPPDATA/Programs/nodejs/node.exe")

NODE_OK=""
for _n in "${_hf_cands[@]}"; do
  [ -x "$_n" ] || continue
  _m=$(_hf_maior "$_n")
  if [ -n "$_m" ] && [ "$_m" -ge 22 ]; then NODE_OK="$_n"; break; fi
done
# sempre na frente: o npx e o npm têm `#!/usr/bin/env node`
[ -n "$NODE_OK" ] && export PATH="$(dirname "$NODE_OK"):$PATH"

_hf_bin="${EDITOR_HF_BIN:-$HOME/.editorblackbelt/bin}"
HF=(); HF_ORIGEM=""
for _a in "$_hf_bin/hyperframes" "$_hf_bin/hyperframes.cmd"; do
  if [ -x "$_a" ] || [ -f "$_a" -a "${_a##*.}" = "cmd" ]; then HF=("$_a"); HF_ORIGEM="atalho do Editor Automático"; break; fi
done
if [ ${#HF[@]} -eq 0 ]; then
  HF=(npx --yes "hyperframes@$HYPERFRAMES_VERSAO"); HF_ORIGEM="npx"
fi

HF_FALTA_MSG="abra o Editor Automático › Ambiente › Preparar este computador (instala o Node e o HyperFrames)"
unset _b _f _p _n _m _a _hf_bin _hf_cands
