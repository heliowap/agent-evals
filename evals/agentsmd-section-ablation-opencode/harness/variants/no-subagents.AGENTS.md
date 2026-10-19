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

## Verification

An unverified claim does not become a statement. Evidence by kind, gathered
in this session:
- File, config or API response contents: read them.
- What an installed tool does (name, flag, default, precedence, limit): run
  `-h`, a version command or a minimal invocation.
- Runtime behavior: execute the relevant path or test. Reading code shows
  intent, not behavior.
- What a rule or contract requires: read the official source and cite it by
  URL.
- Other facts that change over time (versions, prices, releases): fetch a
  source and cite it by URL.

On what is required, authority runs: Constitution > laws > decrees >
ordinances, normative instructions and resolutions (as published in the DOU)
> official technical documentation > upstream repositories > the code. Within
one rank, the more specific and then the later act prevails. Code that
disagrees with a higher source is a finding.

A passing command proves only the scope it exercises.

Couldn't confirm it? Mark it `UNVERIFIED`. An `UNVERIFIED` fact that bears
on the requested scope is a blocker under Done; any other stays out of the
completion evidence.

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

## pstack

Before following a Cursor-oriented pstack skill, read
`~/.config/opencode/pstack-opencode.md` for OpenCode adaptations.
