# Global rules

Global documentation (this file, agent files, skills) is written in English.
The user's instructions take precedence over a skill's or an agent file's
instructions.

## Done

Before acting, identify the observable condition that proves the requested
scope is complete. Derive it from the request and the applicable contract;
ask only when neither defines it.

Account for every requested item against that condition. Finish when all
items are verified; otherwise report the remaining items and the blocker.

When the condition holds, stop and report. Propose additional work instead
of performing it.

## Verification

An unverified claim does not become a statement. Evidence by kind, gathered
in this session:
- File, config or API response contents: read them.
- A tool's name, flag, default, precedence or limit: run `-h`, a version
  command or a minimal invocation; this outranks any doc on the web.
- Runtime behavior: execute the relevant path or test. Reading code shows
  intent, not behavior.
- Facts that change over time (versions, prices, releases, rules): fetch a
  source and cite it by URL.

A passing command proves only the scope it exercises. Reasoning and design
are labeled as such rather than verified.

Couldn't confirm it? Mark it `UNVERIFIED`. An `UNVERIFIED` fact that bears
on the requested scope is a blocker under Done; any other stays out of the
completion evidence. A declared assumption is acceptable; an assumption
presented as fact is not.

## Code changes

- YAGNI: implement only behavior required by the current task.
- Single source of truth: keep each rule or piece of knowledge authoritative
  in one place; derive other representations from it.

For every code change, record `git rev-parse HEAD` at task start as the
review fixed point, then:
1. Follow the `codebase-design` skill's discipline from design through review.
2. Load the `tdd` skill before the first test or implementation edit.
3. Before declaring the work complete, run the `code-review` skill against
   the fixed point (the `/code-review` command is only its wrapper). For
   uncommitted work, review `git diff <fixed-point>` instead of
   `<fixed-point>...HEAD`.

Before drafting, editing, opening or updating a PR body, load the `pr` skill.

## Repositories

`~/VSCode/<name>` is the main checkout. Worktrees live in
`~/VSCode/worktrees/<name>`; Codex-managed ones stay in
`~/.codex/worktrees/*`.

Commits and PRs carry the user as sole author: commit messages and PR bodies
end with their own content, with no `Co-Authored-By` trailer and no
"Generated with …" agent attribution.

## Subagents

Define each package before dispatch:
- **Purpose:** why this work is needed and which decision it supports.
- **Scope:** the question or responsibility it owns, with relevant dependencies.
- **Done:** the observable result that completes the package.

Use a short, outcome-oriented description; put Purpose, Scope and Done
in the prompt.

When a dispatch sets `model` explicitly, take the `providerID/modelID#variant`
from `tools.opencode.models({ provider | query })` via `execute`.

Budget each package for the model's effective context window (the smart
zone), reserving room for exploration and verification. Split oversized
packages by coherent responsibility. The parent reconciles returned
coverage against the requested scope before concluding.

Work spanning more than one independent question or file set follows
research → plan → implementation → review:
- Research: `researcher` agents, each with `background: true`.
- Plan: `planner`.
- Implementation: one `implementer` per package. Parallel packages own
  disjoint files; shared-file packages run sequentially or in separate worktrees.
- Review: the `code-review` skill (see Code changes), which dispatches its
  own Standards and Spec reviewers.

Provider failures: redispatch failed research or exploration so the plugin
can select a fallback. Stop when available routes are exhausted; report the
blocker. Task failures require diagnosis rather than redispatch.

## pstack

Before following a Cursor-oriented pstack skill, read
`~/.config/opencode/pstack-opencode.md` for OpenCode adaptations.
