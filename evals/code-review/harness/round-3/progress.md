# Progress

## Task 1 — isolated review environment (2026-09-27)

### Isolation mechanism (inside `sandbox.build_env`)
- `OPENCODE_TEST_HOME=<workdir>/../.<name>-ochome`: redirects `~`, so `~/.claude/skills` and `~/.agents/skills` are not scanned.
- `XDG_CONFIG_HOME=<fake home>/.config`: redirects the global config dir, so `~/.config/opencode/opencode.json` (plugins `superpowers` and `@slkiser/opencode-quota`) and `~/.config/opencode/skills` are not loaded. Neither variable alone is enough: TEST_HOME alone still loads ~/.config/opencode, and XDG alone still scans ~/.claude/skills.
- The fake global config `<fake home>/.config/opencode/opencode.json` holds only `provider` and `disabled_providers`, copied from `~/.config/opencode/opencode.jsonc` (cli_proxy, openrouter, …). Its location is outside the snapshot, so the reviewer never sees it in the repo.
- The data dir stays the real one (`~/.local/share/opencode`), so `auth.json` credentials and `opencode session export` still work. No copy of auth.json is needed.
- Every inherited `OPENCODE_*` variable is dropped. This session's shell exported `OPENCODE_CONFIG_CONTENT`, which reroutes opencode/opencode-go/cli_proxy through a local jev-gateway on :8791 and :8792, plus an `OPENCODE_API_KEY`.
- `PWD=<workdir>` is set because opencode takes the session location from `$PWD`, not from the process cwd. Without it, the first probe session recorded location `round-3/`.
- `OPENCODE_CONFIG_CONTENT = {"plugin":[],"default_agent":"reviewer","permission":{"edit":"deny"},"agent":{"reviewer":REVIEWER_AGENT minus "model"}}`.
- The skill goes in `<workdir>/.opencode/skills/code-review/SKILL.md`. `/.opencode/` and `/.bin/` are added to the snapshot's `.git/info/exclude`.

Note: `opencode debug config` / `debug agents` query the shared background service and ignore the caller's env, so they cannot verify isolation. `probe_static.py` starts a private `opencode serve` with the env and reads `/api/skill`, `/api/plugin`, `/api/agent`, `/api/config` instead.

### Static probe (`python3 probe_static.py`, no model call) — STATIC CLEAN
- skills: `opencode` (/builtin), `report` (/builtin), `code-review` (snapshot .opencode/skills)
- non-builtin plugins: none
- agents: reviewer, build, general, explore, compaction, title, summary, plan
- config documents: only the fake-home opencode.json and the inline OPENCODE_CONFIG_CONTENT
- Baseline without isolation: 56 skills (15 from superpowers, 17 from ~/.config/opencode/skills, 22 from ~/.claude/skills and ~/.claude/skills/synced) and plugins superpowers (active) plus opencode-quota (failed).

### Live probe (`probe_isolation.py`)
- Calls 1–4, all on `opencode-go/glm-5.3-flash`, failed with `provider.quota: Upstream request failed: Insufficient account funds (402)`, returned about 20 ms after step start. Call 4 was a control in the user's normal non-isolated env and got the same 402. The opencode-go account is out of funds; this is not an isolation fault.
- Call 5 used `PROBE_MODEL=openrouter/z-ai/glm-5.3-flash` and came back **PROBE CLEAN**:
  - session `ses_c1018bd5f5debca04cdc`, agent `reviewer`, location = snapshot dir, cost $0.00031, 5888 input tokens
  - model reply: `code-review\nopencode\nreport`
  - no user skill names in the output or export; no `superpowers` in the export
  - The export has no system-prompt parts (messages: agent-switched, user, assistant, idle). The "no superpowers in system prompt" check therefore rests on the static probe showing the plugin is not loaded.

## Task 1 — Fix round 1

### Findings fixed
1. `make_snapshot` left `.git/FETCH_HEAD`, which contains the source repo path. It is now deleted after gc.
2. `install_fake_gh` wrote the full case (grading data included) to `<dest>/.bin/case.json`, where the agent could read it. It now writes only `pr`, `diff`, `issues`, `repo`, `head` to `<dest>.gh/case.json`, a sibling of the snapshot outside it. The `.bin/gh` wrapper points there.
3. `fake_gh` refused ordinary calls. It now:
   - accepts `-R`/`--repo`/`--repo=` when the value equals `case["repo"]`, and refuses any other repo;
   - takes the PR as nothing, `7`, `#7`, or the PR URL;
   - on `pr view --json`, serves number, title, body, baseRefName, headRefName, headRefOid (from `case["head"]`), url (built from repo), author, files, additions, deletions and state. files/additions/deletions are derived from the diff when absent, and unknown fields come back as `null` (same on `issue view --json`);
   - prints a readable title/branches/stats/body block for `pr view` without `--json`.
   It still refuses `--comments`, other PR/issue numbers, other repos and other subcommands.

### Tests added (test_sandbox.py)
- `SnapshotTest.test_no_source_path_in_git_dir`: no FETCH_HEAD; the source path (raw and resolved) appears in no file under `.git` outside `objects/pack`.
- `FakeGhCompatTest`:
  - `test_grading_data_not_under_dest`: "SECRET-TARGET" is in no file under dest; case.json sits outside dest and has no `target`.
  - `test_repo_flag`, `test_pr_number_optional`, `test_json_fields`, `test_unknown_json_field_is_null`, `test_human_readable_view`, `test_still_refuses`

### Command / output
`python3 -m unittest test_sandbox -v`
```
Ran 11 tests in 4.785s

OK
```
(all 11 tests ok: 3 SnapshotTest, 1 FakeGhTest, 7 FakeGhCompatTest)

## Task 7 — Sentinel v2 (steps 1–4)
- `sentinel-v2/sentinel.py`, `sentinel-v2/jev.py`, `sentinel-v2/test_sentinel.py`.
- lizard via uv (not installed globally). Test command: `uv run --with lizard==1.24.0 python3 -m unittest discover -s sentinel-v2 -v` (23 tests, 1 skipped = live Jev test, opt-in via `SENTINEL_LIVE=1`).
- Jev over OpenRouter (`/api/alpha/decisions`, `typesafe/jev-1.13`); spend goes to `jev_spend.json`; a missing `usage.cost` raises `JevUnknownCost` (pause).
- Step 5 (precomputing hotspots) not done yet: cases do not exist.
