#!/bin/zsh
# usage: jobs-round2.sh [reps] > jobs.txt   (full vs new on s2, v3, v4; Opus, Sol, Haiku)
reps=${1:-5}
for m in cli_proxy/cpa-claude-opus-5-5 cli_proxy_openai/gpt-6.1-sol cli_proxy/cpa-claude-haiku-5-5; do
  for c in s2 v3 v4; do
    for r in $(seq 1 $reps); do echo "$m full $c $r"; echo "$m new $c $r"; done
  done
done
