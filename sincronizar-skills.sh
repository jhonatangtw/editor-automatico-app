#!/bin/bash
# Copia as skills que viajam DENTRO do app.
#
# Elas continuam sendo autoradas em ~/.claude/skills — aqui vive um retrato,
# para o app funcionar na máquina do editor, que não tem nenhuma delas. Rodar
# isto antes de publicar mantém os dois em dia.
#
# ⚠️ Só entram as skills de PRODUÇÃO DE CRIATIVO. As outras 39 da máquina do
# autor não têm o que fazer no computador de um editor — e instalador que leva
# tudo é instalador que ninguém baixa.
set -e
cd "$(dirname "$0")"
ORIGEM="$HOME/.claude/skills"
SKILLS="photorealism-prompts video-prompt-builder pixar3d storyboard-viral-3d editor-automatico-de-broll"

[ -d "$ORIGEM" ] || { echo "x nao achei $ORIGEM" >&2; exit 1; }
rm -rf skills; mkdir -p skills

for s in $SKILLS; do
  [ -d "$ORIGEM/$s" ] || { echo "x a skill '$s' nao esta instalada" >&2; exit 1; }
  rsync -a --exclude '__pycache__' --exclude '.DS_Store' --exclude '*.pyc' \
        "$ORIGEM/$s" skills/
  printf "  %-30s %s\n" "$s" "$(du -sh skills/$s | cut -f1)"
done

python3 - <<'PY'
import hashlib, json, os, time
d = {}
for s in sorted(os.listdir("skills")):
    p = os.path.join("skills", s)
    if not os.path.isdir(p):
        continue
    h = hashlib.sha256()
    for raiz, _, arqs in sorted(os.walk(p)):
        for a in sorted(arqs):
            h.update(open(os.path.join(raiz, a), "rb").read())
    d[s] = h.hexdigest()[:16]
json.dump({"origem": "~/.claude/skills", "sincronizado": time.strftime("%Y-%m-%d"),
           "skills": d}, open("skills/FONTE.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("  ---")
print("  %d skills, %s no total" % (len(d), os.popen("du -sh skills | cut -f1").read().strip()))
PY
