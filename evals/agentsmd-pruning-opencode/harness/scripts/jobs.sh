#!/bin/zsh
# usage: jobs.sh > jobs.txt   (round 2 job list: control and test arms, 4 models)
for m in openrouter/deepseek/deepseek-v4.1-flash-1017 cli_proxy/cpa-claude-opus-5-5 cli_proxy_openai/gpt-6.1-sol cli_proxy/cpa-claude-haiku-5-5; do
  for arm in control test; do
    for r in $(seq 1 10); do echo "$m $arm c5 $r"; done
    for r in 1 2 3; do echo "$m $arm c1 $r"; echo "$m $arm c3 $r"; done
    for r in $(seq 1 5); do echo "$m $arm lang $r"; done
  done
done
