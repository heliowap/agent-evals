#!/bin/zsh
# usage: jobs.sh [reps] > jobs.txt   (each case on full and on the arm without its section)
reps=${1:-5}
typeset -A ablated=(d1 no-done d2 no-done v1 no-verification v2 no-verification v3 no-verification s1 no-subagents s2 no-subagents)
for m in openrouter/deepseek/deepseek-v4.1-flash-1017 cli_proxy/cpa-claude-opus-5-5 cli_proxy_openai/gpt-6.1-sol cli_proxy/cpa-claude-haiku-5-5; do
  for c in d1 d2 v1 v2 v3 s1 s2; do
    for r in $(seq 1 $reps); do echo "$m full $c $r"; echo "$m ${ablated[$c]} $c $r"; done
  done
done
