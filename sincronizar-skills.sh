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
#     subagentes em ~/.claude/agents, pasta que o instalador ainda não instala;
#   * motion-vox — a própria fonte continua sem os 16 PNGs de asset (o
#     verificar.py dela reprova); entra quando o kit estiver completo;
#   * motion-viral-jhon1 — é o motion dos Reels do PRÓPRIO autor (voz clonada
#     dele, identidade visual dele, acervo no disco dele). Não é genérica;
#   * gemini-omni — feita para os vídeos de uma pessoa específica;
#   * cortar-aula — chama scripts que só existem na máquina do autor.
#
# Depois de copiar, `limpar-skills.py` tira o que é do autor e do cliente
# (caminhos, Drive, marcas, o registro de job) e AUDITA: se sobrar qualquer
# coisa, este script para com erro e o retrato não é usado.
#
# `skills/` viaja na atualização leve: o CI põe a pasta no codigo.zip e o
# app procura as skills primeiro ao lado do código em execução.
set -e
cd "$(dirname "$0")"
ORIGEM="$HOME/.claude/skills"
SKILLS="
  skill-black-belt editor-automatico-de-broll hooks-meat-hook
  blackbelt-omni motion-omni-vsl vibe-motion motion-design
  photorealism-prompts video-prompt-builder avatar-vsl-video-prompts
  pixar3d storyboard-viral-3d omni-flash-reverse video-to-flow
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

echo "  --- limpando e auditando"
python3 limpar-skills.py skills

python3 - <<'PY'
import json, os, sys, time
sys.path.insert(0, ".")
from nucleo.skills import hash_pasta
d = {}
for s in sorted(os.listdir("skills")):
    p = os.path.join("skills", s)
    if not os.path.isdir(p):
        continue
    d[s] = hash_pasta(p)     # o MESMO hash que o instalador usa para saber o que é nosso
json.dump({"origem": "~/.claude/skills", "sincronizado": time.strftime("%Y-%m-%d"),
           "skills": d}, open("skills/FONTE.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("  ---")
print("  %d skills, %s no total" % (len(d), os.popen("du -sh skills | cut -f1").read().strip()))
PY
