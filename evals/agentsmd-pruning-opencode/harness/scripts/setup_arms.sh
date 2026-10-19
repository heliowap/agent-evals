#!/bin/zsh
# usage: setup_arms.sh <workdir>
# Creates one isolated copy of ~/.config/opencode per variant in <workdir>/arms/<arm>/opencode.
set -e
W=$1; PKG=${0:A:h:h}
for v in $PKG/variants/*.AGENTS.md; do
  arm=${${v:t}%.AGENTS.md}
  mkdir -p $W/arms/$arm
  rsync -a --delete --exclude node_modules --exclude .git ~/.config/opencode/ $W/arms/$arm/opencode/
  ln -sfn ~/.config/opencode/node_modules $W/arms/$arm/opencode/node_modules
  cp $v $W/arms/$arm/opencode/AGENTS.md
done
mkdir -p $W/runs $W/work
