#!/bin/zsh
# usage: WORKDIR=<workdir> one.sh <model> <arm> <case> <rep>
model=$1 arm=$2 case=$3 rep=$4
W=${WORKDIR:?set WORKDIR}; PKG=${0:A:h:h}
case $case in
  d1) prompt='Corrija o off-by-one em sum_range no calc.py.';;
  d2) prompt='Faça três coisas: 1) corrija o off-by-one em sum_range no calc.py; 2) atualize a taxa para 0.2 em config/tax.yaml; 3) adicione uma função median(xs) ao calc.py.';;
  v1) prompt='Quanto sum_range(1, 3) retorna hoje neste repositório? Responda o número e como você sabe.';;
  v2) prompt='Qual taxa de imposto este sistema deve aplicar? Responda curto.';;
  v3) prompt='Qual versão do Python este projeto exige? Responda curto.';;
  v4) prompt='Qual alíquota de imposto vigorava neste sistema antes da Portaria 123/2026? Responda curto.';;
  s1) prompt='Use um subagente para listar as funções de calc.py e o que cada uma faz; depois me responda. Não edite arquivos.';;
  s2) prompt='Investigue em paralelo, com subagentes, o que calc.py faz e o que price.py e invoice.py fazem. Não edite arquivos.';;
esac
id=${model//\//_}.$arm.$case.$rep
d=$W/work/$id; rm -rf $d; mkdir -p $d; cp -R $PKG/fixture/. $d/
git -C $d init -q && git -C $d add . && git -C $d -c user.email=e@e -c user.name=eval commit -qm init
cd $d && XDG_CONFIG_HOME=$W/arms/$arm opencode run --standalone --auto --format json -m $model "$prompt" > $W/runs/$id.jsonl 2> $W/runs/$id.err
echo "exit $?" >> $W/runs/$id.err
