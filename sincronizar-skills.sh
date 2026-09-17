#!/bin/bash
# Copia as skills que viajam DENTRO do app.
#
# Elas continuam sendo autoradas em ~/.claude/skills — aqui vive um retrato,
# para o app funcionar na máquina do editor, que não tem nenhuma delas. Rodar
# isto antes de publicar mantém os dois em dia.
#
# ⚠️ Só entram as skills de PRODUÇÃO DE CRIATIVO. As outras da máquina do
# autor não têm o que fazer no computador de um editor — e instalador que leva
# tudo é instalador que ninguém baixa. Ficam de fora, de propósito:
#   * as internas da casa (painel-hw-edicao, replicador-hw) — não são do aluno;
#   * corte-viral — precisa de venv própria (3.10+), do modelo YuNet e de 8
#     subagentes em ~/.claude/agents, pasta que o instalador ainda não instala.
#     Levar assim entregaria uma skill que morre no primeiro comando;
#   * motion-vox — a própria fonte está sem os 16 PNGs de asset.
#
# ⚠️ `skills/` NÃO viaja na atualização leve (`codigo.PARTES` leva só app.py,
# nucleo, web e version.json). Versão que muda esta lista precisa chegar pelo
# INSTALADOR — marque `precisa_instalador` no version.json.
set -e
cd "$(dirname "$0")"
ORIGEM="$HOME/.claude/skills"
SKILLS="
  editor-automatico-de-broll
  photorealism-prompts video-prompt-builder pixar3d storyboard-viral-3d
  skill-black-belt avatar-vsl-video-prompts blackbelt-omni
  gemini-omni omni-flash-reverse video-to-flow
  motion-viral-jhon1 motion-omni-vsl
"

[ -d "$ORIGEM" ] || { echo "x nao achei $ORIGEM" >&2; exit 1; }
rm -rf skills; mkdir -p skills

for s in $SKILLS; do
  [ -d "$ORIGEM/$s" ] || { echo "x a skill '$s' nao esta instalada" >&2; exit 1; }
  # .venv/.git/node_modules: uma venv de skill sozinha passa de 400 MB e
  # entraria calada no .dmg. runs/ é trabalho de projeto, não é a skill.
  #
  # ⚠️ `motion-omni-vsl/assets/produto_*.png` são o RENDER DO PRODUTO DO CLIENTE
  # do job em que a skill nasceu. O repositório é público e o app vai para todo
  # aluno: material de cliente não viaja. E nem serviria — cada um tem o seu.
  rsync -a --exclude '__pycache__' --exclude '.DS_Store' --exclude '*.pyc' \
        --exclude '.venv' --exclude '.git' --exclude 'node_modules' \
        --exclude 'runs' --exclude 'assets/produto_*.png' \
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
