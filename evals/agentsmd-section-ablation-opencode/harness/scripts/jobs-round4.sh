#!/bin/zsh
# usage: jobs-round4.sh [reps] > jobs.txt   (done2 vs src on k1, k2, k3, v2; Opus, Sol, Haiku)
reps=${1:-5}
for m in cli_proxy/cpa-claude-opus-5-5 cli_proxy_openai/gpt-6.1-sol cli_proxy/cpa-claude-haiku-5-5; do
  for c in k1 k2 k3 v2; do
    for r in $(seq 1 $reps); do echo "$m done2 $c $r"; echo "$m src $c $r"; done
  done
done
