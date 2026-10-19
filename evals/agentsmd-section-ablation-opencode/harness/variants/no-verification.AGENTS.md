# Global rules

Global documentation (this file, agent files, skills) is written in English.

## Done

Before acting, identify the observable condition that proves the requested
scope is complete. Derive it from the request and the applicable contract;
ask only when neither defines it.

Account for every requested item against that condition. Finish when all
items are verified; otherwise report the remaining items and the blocker.

When the condition holds, stop and report. Propose additional work instead
of performing it.

## Code changes

Single source of truth: keep each rule or piece of knowledge authoritative
in one place; derive other representations from it.

For every code change, record `git rev-parse HEAD` at task start as the
review fixed point, then:
1. Follow the `codebase-design` skill's discipline from design through review.
2. Load the `tdd` skill before the first test or implementation edit.
3. Before declaring the work complete, run the `code-review` skill against
   the fixed point (the `/code-review` command is only its wrapper). For
   uncommitted work, review `git diff <fixed-point>` instead of
   `<fixed-point>...HEAD`.

Skipping tests skips only `tdd`; `code-review` still runs.

Before drafting, editing, opening or updating a PR body, load the `pr` skill.

## Repositories

`~/VSCode/<name>` is the main checkout. Worktrees live in
`~/VSCode/worktrees/<name>`; Codex-managed ones stay in
`~/.codex/worktrees/*`.

Commits and PRs carry the user as sole author: commit messages and PR bodies
end with their own content, with no `Co-Authored-By` trailer and no
"Generated with …" agent attribution.

## Subagents

Every dispatch, including a quick `explore` or `general` one, carries a
package in its prompt:
- **Purpose:** why this work is needed and which decision it supports.
- **Scope:** the question or responsibility it owns, with relevant dependencies.
- **Done:** the observable result that completes the package.

A subagent owns one package. Follow-ups to it stay within that package:
retrieval, clarification, re-checks. A change to Purpose, Scope or Done goes
to a fresh subagent with its own package.

Each agent file defines its report. Check returned claims against the files
before acting on them, and reconcile returned coverage against the requested
scope before concluding.

When a dispatch sets `model` explicitly, take the `providerID/modelID#variant`
from `tools.opencode.models({ provider | query })` via `execute`.

Work spanning more than one independent question or file set follows
research → plan → implementation → review, with at most 4 concurrent
subagents per stage:
- Research: one `researcher` per independent question, with `background: true`.
- Plan: `planner`.
- Implementation: one `implementer` per package, executing it as planned; a
  needed deviation returns to the planner. Parallel packages own disjoint
  files; shared-file packages run sequentially or in separate worktrees.
- Review: the `code-review` skill (see Code changes).

Failures:
- Provider failure: redispatch so the plugin can select a fallback; when
  routes are exhausted, report the blocker.
- Task failure: diagnose before any redispatch. If the diagnosis changes
  Scope or Done, re-plan only the affected packages; the rest proceed.

## pstack

Before following a Cursor-oriented pstack skill, read
`~/.config/opencode/pstack-opencode.md` for OpenCode adaptations.
