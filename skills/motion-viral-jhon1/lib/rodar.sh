#!/usr/bin/env bash
# Roda um roteiro .jsx dentro do After Effects aberto e DEVOLVE O LOG.
#
#   lib/rodar.sh <pasta-do-projeto> <cena.jsx> [nome-do-log]
#
# Por que existe: DoScriptFile devolve so um status, nunca o valor. Todo retorno
# tem que ser gravado em arquivo pelo proprio script. Este wrapper monta
# prelúdio + ae_lib.jsx + a cena num arquivo so (evita $.evalFile com caminho
# absoluto), fecha tudo num try/catch, chama flush() sozinho e imprime o log.
#
# Variaveis: MVJ_COMP (comp principal, padrao MAIN) · MVJ_FPS (24)
#            MVJ_OUT (padrao <projeto>/07_Exports/_ae) · MVJ_AE (nome do app)
#            MVJ_TIMEOUT (segundos de espera pelo log, padrao 600 — script com
#            centenas de camadas passa de 3 min; desistir cedo deixa o AE ocupado e o
#            PROXIMO DoScriptFile colide com ele)
set -euo pipefail
[ $# -ge 2 ] || { echo "uso: rodar.sh <pasta-do-projeto> <cena.jsx> [nome-do-log]" >&2; exit 64; }
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJETO="$(cd "$1" && pwd)"; CENA="$2"; LOGNAME="${3:-$(basename "$CENA" .jsx)}"
[ -f "$CENA" ] || { echo "cena nao existe: $CENA" >&2; exit 66; }
OUT="${MVJ_OUT:-$PROJETO/07_Exports/_ae}"; mkdir -p "$OUT/frames"
RUN="$OUT/_run_$LOGNAME.jsx"
esc(){ printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
{
  printf 'var DEMANDA = "%s";\n'   "$(esc "$PROJETO")"
  printf 'var SAIDA = "%s";\n'     "$(esc "$OUT")"
  printf 'var COMP_MAIN = "%s";\n' "$(esc "${MVJ_COMP:-MAIN}")"
  printf 'var FPS = %s;\n'         "${MVJ_FPS:-24}"
  printf 'var LOGNAME = "%s";\n'   "$(esc "$LOGNAME")"
  cat "$SKILL/lib/ae_lib.jsx"
  [ -f "$SKILL/lib/ae_podcast.jsx" ] && cat "$SKILL/lib/ae_podcast.jsx"
  printf '\ntry {\n'
  cat "$CENA"
  printf '\n} catch(e){ log("ERRO NAO TRATADO: "+e.message+" linha "+e.line); }\n'
  printf 'try{ app.endUndoGroup(); }catch(x){}\n'
  printf 'fim();\n'
} > "$RUN"
rm -f "$OUT/$LOGNAME.log"
osascript -e "tell application \"${MVJ_AE:-Adobe After Effects 2026}\" to DoScriptFile \"$RUN\"" >/dev/null 2>&1 || true
for _ in $(seq 1 "${MVJ_TIMEOUT:-600}"); do [ -f "$OUT/$LOGNAME.log" ] && break; sleep 1; done
if [ ! -f "$OUT/$LOGNAME.log" ]; then
  echo "SEM LOG apos ${MVJ_TIMEOUT:-600}s." >&2
  echo "Duas causas: (a) o script ainda esta rodando — NAO dispare outro DoScriptFile, teste com um" >&2
  echo "ping curto antes; (b) o motor de script do AE esta preso num painel CEP com evalScript pendente." >&2
  echo "Ver references/armadilhas-extendscript.md > 'DoScript pendurou'." >&2
  exit 2
fi
cat "$OUT/$LOGNAME.log"
# O AE grava os PNG DEPOIS de fechar o log: esperar cada frame prometido aparecer e
# parar de crescer, senao o passo seguinte le um arquivo pela metade.
# ({ … || true } porque com pipefail um grep sem resultado derrubaria o runner com exit 1 silencioso)
{ grep -o '\-> /.*\.png$' "$OUT/$LOGNAME.log" 2>/dev/null || true; } | sed 's/^-> //' | while read -r png; do
  for _ in $(seq 1 30); do [ -s "$png" ] && break; sleep 0.5; done
  a=0; for _ in $(seq 1 30); do b=$(stat -f %z "$png" 2>/dev/null || echo 0); [ "$b" = "$a" ] && [ "$b" != "0" ] && break; a=$b; sleep 0.5; done
  [ -s "$png" ] || echo "AVISO: frame prometido nunca apareceu: $png" >&2
done
grep -q "^ERRO" "$OUT/$LOGNAME.log" && exit 1 || exit 0
