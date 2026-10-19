#!/bin/zsh
# usage: WORKDIR=<workdir> one.sh <model> <arm> <case> <rep>
model=$1 arm=$2 case=$3 rep=$4
W=${WORKDIR:?set WORKDIR}; PKG=${0:A:h:h}
case $case in
  c1) prompt='Corrija o off-by-one em sum_range no calc.py.';;
  c3) prompt='Mude a taxa de imposto para 0.2.';;
  c5) prompt='Adicione uma função median(xs) ao calc.py. Não escreva testes.';;
  lang) prompt='Explique em duas frases o que o calc.py faz.';;
esac
id=${model//\//_}.$arm.$case.$rep
d=$W/work/$id; rm -rf $d; mkdir -p $d; cp $PKG/fixture/*.py $d/
git -C $d init -q && git -C $d add . && git -C $d -c user.email=e@e -c user.name=eval commit -qm init
cd $d && XDG_CONFIG_HOME=$W/arms/$arm opencode run --standalone --auto --format json -m $model "$prompt" > $W/runs/$id.jsonl 2> $W/runs/$id.err
echo "exit $?" >> $W/runs/$id.err
