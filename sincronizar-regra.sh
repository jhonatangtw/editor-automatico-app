#!/bin/bash
# Copia a regra de edição da skill para dentro do app.
#
# A regra continua sendo AUTORADA na skill `editor-automatico-de-broll` — aqui
# vive um retrato dela, para o app funcionar em máquina que não tem a skill
# instalada (ou seja: a de todo editor). Rodar isto antes de publicar mantém os
# dois em dia; o app avisa na tela quando está usando o retrato.
set -e
cd "$(dirname "$0")"
SKILL="$HOME/.claude/skills/editor-automatico-de-broll"

[ -d "$SKILL" ] || { echo "x a skill nao esta instalada em $SKILL" >&2; exit 1; }

cp "$SKILL"/scripts/{compilar,revisar,montar}.py regra/scripts/
cp "$SKILL"/estilos/*.json regra/estilos/

python3 - <<'PY'
import hashlib, json, os, time
arqs = {}
for pasta in ("regra/scripts", "regra/estilos"):
    for n in sorted(os.listdir(pasta)):
        if n.startswith("."):
            continue
        p = os.path.join(pasta, n)
        arqs[p] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
json.dump({"origem": "skill editor-automatico-de-broll",
           "sincronizado": time.strftime("%Y-%m-%d"),
           "arquivos": arqs},
          open("regra/FONTE.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("regra sincronizada:", len(arqs), "arquivos")
PY
