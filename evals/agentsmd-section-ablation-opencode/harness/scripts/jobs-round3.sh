#!/bin/zsh
# usage: jobs-round3.sh [reps] > jobs.txt   (new vs done2 on d1, d2, v2; Opus, Sol, Haiku)
reps=${1:-5}
for m in cli_proxy/cpa-claude-opus-5-5 cli_proxy_openai/gpt-6.1-sol cli_proxy/cpa-claude-haiku-5-5; do
  for c in d1 d2 v2; do
    for r in $(seq 1 $reps); do echo "$m new $c $r"; echo "$m done2 $c $r"; done
  done
done
