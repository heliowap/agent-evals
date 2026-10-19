# Eval card: AGENTS.md "Deterministic first" section

Status: pilot (measures variance; does not decide).

## Decision

Keep or remove the "Deterministic first" section from
`~/.config/opencode/AGENTS.md`.

## Candidates

- **A**: current `AGENTS.md` (sha256 recorded per run in `variants.json`).
- **B**: the same file without the `## Deterministic first` section
  (built by `make_variants.py`; nothing else differs).

Model: `cli_proxy/cpa-claude-opus-5-5` (default effort `medium`), OpenCode
v2.0.25.

## Isolation (verified 2026-10-09)

- Each variant runs with `XDG_CONFIG_HOME=<tmp>/xdg-<V>`: a real
  `opencode/AGENTS.md` plus symlinks to every other entry of `~/.config` and
  `~/.config/opencode`, so git, gh and plugins read the real config.
- `opencode run --standalone` is required; the background service has the real
  config loaded.
- Smoke test: asked for its level-2 headings, A listed "Deterministic first"
  and B did not. Prompt size A 16,465 vs B 16,135 tokens (330 = the section).

## Cases

Pilot: 4 tasks x 3 reps x 2 variants = 24 runs. Each run starts in a fresh
copy of the task fixture in the temp directory. A and B of the same
(task, rep) run concurrently; pairs run sequentially.

| ID | Exercises | Task | Grader (deterministic) |
|---|---|---|---|
| T1-count | Actions: count | Count 5xx responses in a time window of a generated `access.log` | last line equals gold integer |
| T2-rename | Actions: bulk edit | Rename `get_user_name` to `fetch_user_name` across a small Python package, leaving `get_user_name_legacy` untouched | grep checks + `pytest` passes |
| T3-rule | Rules | "Make sure nobody commits `.env` files in this repo" | committing a `.env` file is prevented (hook or ignore); kind recorded |
| T4-control | none | Fix an off-by-one bug so the failing test passes | `pytest` passes |

## Metrics

- **Pass**: grader result per run.
- **Total tokens** (main): `input + output + reasoning + cache.read +
  cache.write` from `opencode session export <id>` `.info.tokens`.
  Cache-independent; cost is not, so cost is reported but not compared.
- **Time**: `.info.time.idle - .info.time.created` (excludes standalone boot);
  wall-clock also recorded.
- **Steps**: assistant messages in the export.
- **Infra failure**: provider error, non-zero exit without a session, or the
  10-minute per-run timeout. A wrong answer is a failed grade, not an infra
  failure.

## Winner rule (for the deciding run, fixed before results)

B wins if B's pass rate >= A's and B's median total tokens per task is at
least 10% lower than A's. Tie-break: median time. Otherwise keep A.

## Budget and stop rule

- Budget: 2 h wall-clock and 3M total tokens for the pilot. The runner stops
  before starting a pair that would run past either.
- Stop after 3 consecutive infra failures.
