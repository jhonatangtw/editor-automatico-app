#!/bin/zsh
# Renderiza A, B, C em sequência (1 worker), master -16 LUFS e limpa os quadros temporários entre um e outro.
export PATH=/opt/homebrew/opt/node@24/bin:$PATH
J="${JOB:-$PWD}"   # pasta do job
T=/var/folders/n1/b2xgttjx76745dsphq52z1h40000gn/T
for v in A B C; do
  cd $J && python3 edicao/build.py $v || exit 1
  cd $J/hyperframes/up1-MarcaE && npx hyperframes render --fps 25 --workers 1 --quiet -o renders/up1_$v.mp4 > $J/edicao/render_$v.log 2>&1
  [ -s renders/up1_$v.mp4 ] || { echo "RENDER $v FALHOU"; tail -5 $J/edicao/render_$v.log; exit 1; }
  cd $J && python3 edicao/master.py hyperframes/up1-MarcaE/renders/up1_$v.mp4 $v > edicao/master_$v.json && echo "OK $v $(grep -E 'saida_LUFS|TP_dBTP|duracao' edicao/master_$v.json | tr -d '\n ')"
  for d in $T/hf-render-*(N); do rm -rf "${d:?}"; done
done
echo FIM
