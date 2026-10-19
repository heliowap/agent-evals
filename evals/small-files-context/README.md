# Do small source files reduce a coding agent's context use? A controlled A/B pilot on bottle.py

**Run date:** 2026-10-18 (smoke 08:48, stage 1 08:50–11:28 UTC-3, with one interruption) · **Agent:** Claude Code 2.1.296, `claude-haiku-5-5`, effort `high` · **Python:** 3.14.6, pytest 9.1.1 · **Codebase:** [bottlepy/bottle](https://github.com/bottlepy/bottle) at `8ec5fe29420d14998c0d86885083983eaea8b839` · **Status:** pilot complete; the pre-specified stopping point was reached after stage 1.

This study was first published as a standalone repository, [small-files-agent-context](https://github.com/heliowap/small-files-agent-context), which also holds the PNG figures. This folder is an anonymized copy of the same harness and data, rearranged into this repository's layout (`harness/` and `data/`).

## Abstract

A common recommendation for codebases maintained by LLM coding agents is to keep every source file under about 5,000 tokens and to enforce the limit with a pre-commit hook. The assumption is that agents read whole files, so smaller files mean less context. We tested that assumption with a two-arm pilot. Arm A was the original single-file `bottle.py` (175,316 bytes, about 43.8k tokens). Arm B was the same module cut into 18 files of at most 20,000 bytes (about 5k tokens) that share one module namespace, checked against A by an automated equivalence gate. Four tasks (two injected bugs, two features), graded by hidden tests, were run 3 times per arm: 24 trials. **All 24 trials passed (12/12 per arm), and B used more peak context than A, not less: B/A ratio 1.152, 95% bootstrap interval 0.985–1.287.** B's median was higher on all four tasks, by 7% to 21%. Under the decision rule fixed before execution, the verdict was "reduction below 20%: stop", so neither stage 2 nor the hook arm (C) ran. Post hoc analysis suggests why. In A the agent never read `bottle.py` whole: it searched with `grep` and read slices. In B it printed whole part files 23 times across 5 of 12 trials. A ≤5k-token file limit is not justified by context efficiency in this setting. The pilot is small (N=3 per cell) and its interval includes no effect, so it is not evidence that small files are harmful.

## 1. Introduction

Coding agents work inside a finite context window, and everything they read stays in the transcript for the rest of the session. One response is to constrain the codebase: if no file exceeds a token budget, no single read can flood the context. The study began with a request to build such a constraint:

> Create a pre-commit hook that prevents files over 5,000 tokens. Tokens = bytes/4. Run only on staged files. Ignore files which are not authored by agents, like lockfiles or codegen. Provide explicit instructions on how to split files in the error message.

Before building and maintaining the hook, we asked whether its premise holds: **does the same code, split into files of at most 5,000 tokens, let an agent solve tasks equally well while using less context?**

The premise depends on agent behavior that is easy to assume and rarely measured. Current agents can search (`grep -n`) and read line ranges (`Read` with `offset`/`limit`, `sed -n`). If they navigate large files that way, file size may not matter, and small files could even invite more whole-file reads.

## 2. Hypotheses

The hypothesis, metrics and decision rule were written in a design document before any agent trial (see §5.5 on how verifiable that is).

**H1.** On the same tasks, the agent passes at an equal or higher rate and reaches a lower peak context when the code is split into files of at most 5,000 tokens (tokens = bytes/4).

The design also expected the broader tasks (t2, t4) to separate the arms most.

**Scope.** Arm B changes only file size, file names and file boundaries. Structure, imports and code are unchanged. A positive result would support "the same code in ≤5k-token files helps". It would not cover a refactor into a conventional package with imports. The agent's line-limited `Read` tool is part of the treatment on purpose, because that is how agents meet large files in practice. This is a directional pilot, meant to decide whether a larger study or adoption is worth it.

## 3. Methodology

### 3.1 Design

| Arm | Codebase | Hook active |
|---|---|---|
| A | original `bottle.py`, single file | no |
| B | same code in 18 files ≤ 20,000 bytes, one shared module namespace | no |
| C (conditional, not run) | B | yes; the task requires a commit, so the hook fires |

The comparison is between trials, crossed over 4 tasks × 2 arms × N repetitions. Arm C would measure the hook's increment over B and would run only if A/B supported H1.

### 3.2 Arm construction

**Codebase.** bottle at the commit above (2026-10-10). `bottle.py` is 175,316 bytes, 4,566 lines, about 43,800 tokens (roughly 9× the limit). The test suite has 364 cases.

**Arm B** is built deterministically by [`harness/fixture/build.py`](harness/fixture/build.py):

- **Loader.** `bottle/__init__.py` keeps the original header and docstring, then runs each part file in order in the package namespace (`exec(compile(source, path, 'exec'), globals())`). Every top-level name stays a global of `bottle`, and module-level mutation such as `bottle.DEBUG = True` still reaches all code. There are no imports between parts.
- **Cuts.** Cuts fall between top-level statements at bottle's own section banners. Within a section, statements are packed greedily up to 20,000 bytes. Files are named `NN_<section>[_<symbol>].py`. The result is 18 parts of 395 to 19,558 bytes (Appendix B).
- **The one code change.** The `Bottle` class alone is 21,468 bytes. Its `_cast` method (3,070 bytes) became a module-level function in `06_app_bottle_cast.py`, followed by `Bottle._cast = _cast; del _cast`.
- **Tests.** Test files over 20,000 bytes were split by class: `test_environ.py` into 3 files, `test_multipart.py` into 2 plus 2 sample-data modules.
- **Shared exclusions.** Both arms leave out upstream `AGENTS.md`, `docs/` and `.github/`. Both are git repositories with one commit and pinned dates.

**Equivalence gate** ([`harness/fixture/check_equivalence.py`](harness/fixture/check_equivalence.py), passed before any trial; output in [`data/results/preflight/equivalence.json`](data/results/preflight/equivalence.json)):

1. The parts, minus their header line and with `_cast` re-inserted, rebuild `bottle.py` byte for byte.
2. Both arms define the same 197 names with the same types, and all 403 functions and methods have identical ASTs.
3. Every function in B has the `bottle` module dict as its `__globals__`.
4. Both arms collect and pass the same 364 tests.
5. No file in B exceeds 20,000 bytes.

### 3.3 Tasks

Tasks are injected bugs and new features absent from bottle, never historical issues the model might remember. The same setup patch applies to both arms and is folded into the fixture's single commit, so `git log`/`git diff` do not reveal it. Each injected bug leaves all 364 visible tests passing. Prompts describe symptoms or requirements without naming files or functions (verbatim in Appendix A; they were written in English).

| ID | Type | Setup | Requirement |
|---|---|---|---|
| t1 | localized bugfix (control) | `parse_auth`: `split(':', 1)` → `split(':')` | passwords containing `:` must authenticate |
| t2 | subtle bugfix across components | `_mount_wsgi`: `path_shift(-path_depth)` → `path_shift(-1)` | parent `after_request` hooks see the correct path under multi-segment mount prefixes |
| t3 | small feature | none | `uuid` route filter: match, case-insensitivity, `uuid.UUID` to the callback, 404 otherwise, URL building |
| t4 | cross-cutting feature | none | opt-in request ID, echoed on normal responses, 404, uncaught 500, `abort()`, `redirect()` and raised `HTTPResponse` |

**Grading.** A trial passes when the hidden tests pass and the original suite still passes. Grading runs on a copy of the agent's final tree with `tasks/<id>/test_hidden.py` and `tasks/hidden_support.py` added; the agent never sees them. [`harness/harness/verify_tasks.py`](harness/harness/verify_tasks.py) confirmed for all 8 task-arm pairs that hidden tests fail after setup, pass with the reference solution, and that the visible suite passes in both states ([`data/results/preflight/verify.json`](data/results/preflight/verify.json)).

### 3.4 Agent and environment

Vanilla Claude Code 2.1.296 with `claude-haiku-5-5`, effort `high`, authenticated through a subscription login (OAuth), not an API key:

```sh
claude -p "$PROMPT" --safe-mode --tools "Bash,Read,Edit" \
  --setting-sources "" --strict-mcp-config --disable-slash-commands \
  --model claude-haiku-5-5 --effort high --max-turns 20 \
  --no-session-persistence --dangerously-skip-permissions \
  --output-format stream-json --verbose < /dev/null
```

- **Isolation.** `--bare` requires an API key, so `--safe-mode` was used instead. The `system/init` event of every trial was checked: tools exactly `Bash`, `Edit`, `Read`; no skills, slash commands or MCP servers; auto-memory off; only built-in plugins. A trial failing any check would have been excluded. None failed.
- **Tools.** No dedicated grep/glob tool and no subagent tool, so search goes through Bash and all context cost stays in one agent.
- **Workspace.** Each trial runs on a fresh clone in the system temp directory, so no parent directory contributes instructions. File mtimes are pinned to 2026-10-10 because an upstream test (`test_sendfile::test_ims`) fails when a file's mtime is the current second.
- **Prompt.** The task text plus one layout sentence per arm:
  - A: "The bottle source code is in `bottle.py` and the tests are in `test/`. Run the tests with `python -m pytest test`."
  - B: "The bottle source code is in the `bottle/` package: `bottle/__init__.py` executes the numbered files in `bottle/` in order, in one shared module namespace, so together they form the `bottle` module. The tests are in `test/`. Run the tests with `python -m pytest test`."
- **Limits.** 20 model calls (`--max-turns`) and a 15-minute wall-clock limit enforced by the runner. Both are the same in both arms.

### 3.5 Procedure

Trials ran one at a time. Within each task and repetition the two arms ran back to back, and the arm that went first alternated.

| Stage | Trials | Purpose / condition |
|---|---|---|
| Smoke | 3 | t1 in each arm, plus a turn-cap probe (t4, A, `--max-turns 2`). Not analyzed |
| 1 | 24 (N=3) | always |
| 2 | +16 (N=5 total) | only if stage 1 is inconclusive |

### 3.6 Outcomes

- **Primary: peak context.** The largest value of `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` over a trial's API calls, after deduplicating stream events by message ID.
- **Quality gate.** Pass rate per arm.
- **Secondary** (reported separately, never summed): fresh-input, cache-read, cache-creation and output tokens; API calls; wall time; estimated cost (`total_cost_usd`; the subscription was not billed per token); file exposure, meaning tokens returned by `Read` and by Bash commands that print files, plus the largest single exposure.
- **Flags** (review only, no exclusion): network use from Bash, reads outside the clone, turn-cap or timeout termination.

### 3.7 Pre-specified analysis and decision rule

- **Estimand.** Per task, median(B)/median(A) of peak context. The overall ratio is the geometric mean over the four tasks.
- **Interval.** 95% percentile bootstrap, 10,000 resamples, seed 20261018, resampling repetitions within each task × arm cell.
- **Population.** All valid trials. The passing-only ratio is a sensitivity check.

Rows are checked in order and the first match decides. PA and PB are passing trials in A and B.

| # | Condition | Verdict | Action |
|---|---|---|---|
| 1 | PB < PA − 1, or ratio > 1.00 with lower bound > 1.00 | refuted | stop |
| 2 | PB ≥ PA − 1, ratio ≤ 0.80, upper bound < 1.00 | supported | run arm C |
| 3 | PB ≥ PA + 2, ratio ≤ 1.00 | supported on quality | run arm C |
| 4 | PB ≥ PA − 1, lower bound > 0.80 | reduction below 20%: limit not worth keeping | stop |
| 5 | otherwise | inconclusive | stage 2, then report |

The 20% threshold is the operator's judgment that a smaller reduction would not justify maintaining a hook and splitting files.

### 3.8 Adversarial design review

Before execution, a model from another vendor (GPT-6-Astra, medium reasoning effort) reviewed the design adversarially ([prompt and output](data/reviews/2026-10-18-gpt-6-astra-medium.md)). It raised 15 findings and recommended a redesign. Most findings were accepted and the design was revised (Appendix C). The changes that matter most: B became the same module in one namespace instead of a refactored package; peak context replaced cumulative tokens as the primary metric; the decision rule and interval were fixed in advance; an invalid example task was replaced with mutation-tested setups.

## 4. Results

### 4.1 Execution

- 24 of 24 stage-1 trials completed with a valid session configuration. None were excluded and none timed out.
- One trial (t3/A, repetition 1) hit the 20-call cap and still passed. The smoke probe confirmed the cap is enforced.
- The run was interrupted once when the operator's session ended (§5.1).
- One trial (t4/B, repetition 3) was flagged for network use. It was `curl` against a server the agent had started on localhost to test its own change, a false positive of the flag's regex. It stays in the analysis, as specified.
- Stage 1 took 31.2 minutes of agent wall time at an estimated $0.39. The smoke stage took 68 s at $0.012.

### 4.2 Primary outcome: peak context (tokens)

Per-trial values were re-checked against each trial's `metrics.json` for this copy and match.

| Task | A: trials | B: trials | Median A | Median B | B/A |
|---|---|---|---|---|---|
| t1 | 10,098 · 10,659 · 15,089 | 10,648 · 11,444 · 11,530 | 10,659 | 11,444 | 1.074 |
| t2 | 19,155 · 21,056 · 27,457 | 23,868 · 24,090 · 26,551 | 21,056 | 24,090 | 1.144 |
| t3 | 24,465 · 30,578 · 32,736 | 35,070 · 36,224 · 42,463 | 30,578 | 36,224 | 1.185 |
| t4 | 57,164 · 59,851 · 68,882 | 65,372 · 72,531 · 82,379 | 59,851 | 72,531 | 1.212 |

**Overall B/A = 1.152, 95% bootstrap interval [0.985, 1.287]** ([`summary.json`](data/results/stage-1/report/summary.json)). The passing-only check is identical, since every trial passed.

### 4.3 Quality gate

| Arm | Passed |
|---|---|
| A | 12/12 |
| B | 12/12 |

Every task passed 3/3 in each arm.

### 4.4 Decision

PB = PA = 12, so rule 1's quality clause does not fire. The ratio is above 1 but the lower bound (0.985) is not, so the refutation clause does not fire either. Rules 2 and 3 need a ratio ≤ 0.80 and ≤ 1.00. Rule 4 holds (PB ≥ PA − 1 and 0.985 > 0.80). **Verdict: reduction below 20%; stop.** Stage 2 and arm C were not run. Only rule 4 matches these values, so the row order did not affect the verdict.

### 4.5 Secondary outcomes (medians per trial)

| Task | Arm | API calls | Output tok | File exposure tok | Largest exposure tok | Cost $ | Wall s |
|---|---|---|---|---|---|---|---|
| t1 | A | 8 | 2,759 | 984 | 282 | 0.003 | 25.0 |
| t1 | B | 8 | 2,705 | 1,187 | 340 | 0.003 | 21.9 |
| t2 | A | 12 | 8,027 | 4,664 | 1,167 | 0.009 | 48.9 |
| t2 | B | 12 | 8,223 | 5,842 | 1,423 | 0.010 | 47.5 |
| t3 | A | 19 | 11,906 | 7,220 | 2,248 | 0.015 | 73.2 |
| t3 | B | 18 | 15,084 | 9,543 | 2,219 | 0.018 | 83.0 |
| t4 | A | 17 | 32,637 | 13,407 | 3,181 | 0.033 | 160.2 |
| t4 | B | 16 | 28,281 | 24,417 | 4,889 | 0.035 | 148.8 |

Both arms used about the same number of API calls. B's extra context came from what the calls returned, most clearly on t4, where B's median file exposure was 1.8× A's. Full tables: [`data/results/stage-1/report/report.md`](data/results/stage-1/report/report.md).

### 4.6 Exploratory analyses (post hoc)

These were defined after seeing the stage-1 data ([`harness/analysis/exploratory.py`](harness/analysis/exploratory.py), output in [`data/results/stage-1/exploratory/`](data/results/stage-1/exploratory/exploratory.md)). They generate hypotheses only.

1. **Paired comparison.** Pairing A and B by task and repetition, B had the higher peak in 8/12 pairs (exact two-sided sign test p = 0.39). Mean log ratio 0.123 (SD 0.200).
2. **Peak equals final context** in 24/24 trials. With no compaction in these short sessions, peak context tracks how much the agent read and wrote overall, not the size of one read.
3. **Starting point.** Context at the first call was equal across arms: median 6,103 (A) and 6,155 (B). B's longer layout sentence accounts for about 50 tokens.
4. **Reading strategy in A.** The agent never read `bottle.py` whole: 0 whole-file `Read` or `cat` calls, 21 `Read` calls with `offset`/`limit`, plus `grep -n` and `sed -n` slices. The largest single exposure in any A trial was 3,529 tokens.
5. **Reading strategy in B.** The agent printed whole part files with `cat` 21 times and used whole-file `Read` twice. These 23 whole-file reads happened in 5 of 12 trials (all three t4 trials and two t3 trials). On t4, B touched 10–11 of the 18 parts per trial, and tool-result tokens were 20.3k–28.8k in B against 12.7k–17.8k in A.
6. **Edits to tests.** Agents added tests in both arms (median 2 files changed in A, 2.5 in B). No trial removed a non-blank line from an existing test file.

## 5. Discussion

**H1 was not supported.** Splitting the module into ≤5k-token files did not reduce peak context on any task. All four median ratios exceed 1, and the overall estimate is a 15% increase. The interval includes 1, so the data do not establish that small files cost more. They do rule out, at this sample size, the ≥20% reduction required to justify the hook.

**The premise behind the hook did not hold for this agent.** The hook assumes large files get read whole. Faced with a 44k-token file, the agent searched and read targeted slices. When files were small, reading them whole became affordable, and on the broadest task (t4) the agent did it repeatedly. Small files lowered the cost per read but raised the number of whole reads. This mechanism comes from post hoc analysis of 24 transcripts and should be tested directly.

**Task breadth.** The gap grew from t1 (1.07, localized fix) to t4 (1.21, change across request, response and error paths). That ordering matches the expectation that t2 and t4 would separate the arms most, but in the opposite direction.

**What changed in the configuration.** The file-size hook was not built, and a per-file token limit is not adopted for context efficiency. File-size limits may still help reviewability, merge conflicts or human navigation, which this study did not measure.

### Limitations, deviations and incidents

#### 5.1 Incidents

1. **Interrupted run.** Stage 1 stopped when the operator's interactive session ended. 12 trials had completed; the 13th (t3/A, repetition 2) had a 66 KB partial transcript and no result. It was moved to [`data/results/stage-1/interrupted/`](data/results/stage-1/interrupted/), kept but not analyzed, and the run resumed with the same configuration (the runner skips completed trials). The re-run is the only completed attempt for that cell, so no outcome was selected. The run log shows a gap of about two hours (09:02 to 11:09).
2. **Network flag false positive** (see §4.1). The regex cannot tell local from external traffic.
3. **Analysis-script bug, fixed before reporting.** The first exploratory script used a regex lookbehind that missed A's reads of `bottle.py` and reported zero sliced reads in A. It was found by checking a transcript by hand and fixed before any number was written. Pre-specified metrics were not affected.

#### 5.2 Deviations from the design

1. **Decision-rule order was added after the smoke run.** As first written, rows 1 and 4 overlapped. They were ordered (refuted first) after the smoke run and before stage 1, with knowledge that one smoke trial had B above A. Only one row matches the stage-1 data, so the order did not matter.
2. **"20 turns" means 20 model calls.** `--max-turns` counts API calls, while `num_turns` in the result event counts tool calls plus one; it reached 27 in trials that ended normally. The cap behaved the same in both arms.
3. **Verdict label.** "Reduction below 20%" is accurate but incomplete: the point estimate is an increase. The rule had no row for a non-significant increase.
4. **The reviewer's redesign verdict was overridden.** Finding 12 (conditional arm C is outcome-selected) was rejected because C estimates the hook's increment over B.

#### 5.3 Construct and internal validity

- Peak context is a proxy for context efficiency. It does not measure attention quality or reasoning degradation, and since peak equals final context here, it partly measures trajectory verbosity.
- "Tokens = bytes/4" is an approximation used for the limit and for exposure. Peak context uses the API's token counts.
- The B layout is artificial: one namespace assembled by `exec`, with numbered files. A conventional package might behave differently. This was deliberate, to avoid confounding size with architecture.
- Parts range from 395 to 19,558 bytes, not a uniform size. Long test files were also split in B.
- Bash exposure is heuristic: matched by command name and attributed to one exposure per tool result.
- The prompts differ by the layout sentence (about 50 tokens).
- `bottle.py` is in model training data. Familiarity may help A's grep-and-slice strategy; B's file names are new.
- Ceiling effect: every trial passed, so the quality gate gives no information about correctness.
- Trials ran over one day with a gap. Alternating arm order spreads serving drift over both arms.
- Trials inherited the operator's IDE-launched environment (`entrypoint: claude-vscode` in the init event), identically across arms.

#### 5.4 Statistical and external validity

- With 3 repetitions per cell, each cell has only 10 distinct bootstrap resamples. Percentile intervals are coarse and tend to be too narrow.
- The sign test and behavior measures were chosen post hoc and are not corrected for multiplicity.
- Results are specific to one model (Haiku 5.5) at one effort level, one harness version with one tool set and no subagents, one Python codebase the model likely knows, and four short tasks capped at 20 calls. The hook itself (arm C) was never tested.

#### 5.5 Process and disclosure

- The design, metrics and decision rule were written before execution in a local design document. The public repository was created after the study, so the timeline cannot be verified from git history.
- Most of the harness, fixture builder, analysis and the original report were written with Claude Opus 5.5 in Claude Code, from the same vendor as the model under test. The adversarial review used a model from another vendor.
- Bugs fixed before any agent trial, during task verification: comparing bytecode gave false differences (the gate switched to ASTs); a gap-only chunk broke the byte-for-byte rebuild; hidden tests did not expect bottle's header-name normalization (`X-Request-Id`); `redirect()` answers 302 or 303 depending on HTTP version; an upstream test depends on file mtimes.
- One proposed task (negative numbers in the `int` route filter) described intended behavior. The reviewer caught it and it was replaced.

## 7. Reproduction

Requirements: Claude Code 2.1.296 logged in, Python 3.14, git, and network access to clone bottle. Agent runs are not deterministic, and results will vary with model-serving changes.

The scripts locate tasks and fixtures relative to `harness/`, so run them from there:

```sh
cd harness
python3 -m venv .venv && .venv/bin/pip install pytest==9.1.1
python3 -B fixture/build.py --out build/fixture                # clones bottle at the pinned commit into .cache/
python3 -B fixture/check_equivalence.py build/fixture --python .venv/bin/python
python3 -B harness/verify_tasks.py --out /tmp/sfb-verify       # hidden tests fail before, pass with reference
python3 -B harness/run.py run --stage smoke --out ../data/results/smoke-2
python3 -B harness/run.py run --stage 1 --out ../data/results/stage-1-rerun
python3 -B harness/report.py ../data/results/stage-1 --out /tmp/sfb-report
python3 -B analysis/exploratory.py ../data/results/stage-1 --out /tmp/sfb-exploratory
```

`harness/run.py plan --stage N` lists a stage's trials without running them. Interrupted stages resume, skipping completed trials. The report and exploratory scripts read `stream.jsonl`; decompress the three gzipped t4/A transcripts first (from the study folder: `gunzip -k data/results/stage-1/trials/*/stream.jsonl.gz`).

| Path | Contents |
|---|---|
| `harness/fixture/build.py` | builds arms A and B at the pinned commit; writes `manifest.json` |
| `harness/fixture/check_equivalence.py` | equivalence gate (§3.2) |
| `harness/tasks/<id>/` | `task.json` (setup and reference replacements), `prompt.md`, `test_hidden.py` |
| `harness/tasks/hidden_support.py` | WSGI helper copied next to hidden tests at grading time |
| `harness/harness/common.py` | trial preparation, layout sentences, grading |
| `harness/harness/run.py` | schedule and execution |
| `harness/harness/metrics.py` | metrics from stream-json transcripts |
| `harness/harness/report.py` | pre-specified aggregation and decision rule |
| `harness/harness/verify_tasks.py` | task verification |
| `harness/analysis/exploratory.py` | post hoc analyses (§4.6) |
| `harness/analysis/redact_paths.py` | path redaction applied to the results before the first publication |

## 8. Data

| Path | Contents |
|---|---|
| `data/results/preflight/` | arm-B manifest, equivalence-gate output, task verification |
| `data/results/smoke-1/` | 3 smoke trials and run log (not analyzed) |
| `data/results/stage-1/trials/` | 24 analyzed trials |
| `data/results/stage-1/interrupted/` | partial transcript of the interrupted trial (not analyzed) |
| `data/results/stage-1/report/` | pre-specified report (`report.md`, `summary.json`) |
| `data/results/stage-1/exploratory/` | post hoc output |
| `data/results/stage-1/run.log` | run log |
| `data/reviews/` | adversarial design review (prompt and output) |
| `data/figures/` | HTML sources of the results figures (the PNG renders are in the original repository) |

Each trial directory holds `stream.jsonl` (full agent transcript; gzipped when over 1 MB), `stderr.txt`, `diff.patch` (the agent's final change), `grade.json` (hidden and visible test results), `metrics.json` and `trial.json` (prompt, configuration, timing).

**Anonymization.** Before the first publication, `analysis/redact_paths.py` replaced machine-specific absolute paths with relative paths or placeholders such as `<tmp>` and `<scratchpad>`. Per-trial `metrics.json` was computed before that redaction, so file-exposure values recomputed from the redacted transcripts come out about 1–4% lower; peak context and API usage are unchanged. For this repository every file was copied again through `tools/anonymize.py`.

**Not redistributed.** The bottle clone (`.cache/bottle-8ec5fe2`) and the built fixtures (`build/`) are regenerated by `fixture/build.py` from [bottlepy/bottle](https://github.com/bottlepy/bottle) at `8ec5fe29420d14998c0d86885083983eaea8b839`. The virtualenv is not included. bottle is © Marcel Hellkamp and contributors, MIT License; transcripts and diffs contain excerpts of its source.

---

## Appendix A. Task prompts (verbatim, English)

Each prompt is followed by the arm's layout sentence (§3.4).

**t1.** Users whose password contains a colon can't log in with HTTP Basic auth. For those users `request.auth` returns None, and routes protected with `auth_basic` reject them even with the right password. Users without a colon in their password are fine. Please fix it.

**t2.** We mount a plain WSGI sub-application under a multi-segment prefix, like `app.mount('/api/v1', legacy_wsgi_app)`. The sub-app itself works, but the parent app's `after_request` hooks see the wrong `request.path` and `request.script_name` for those requests, which breaks our access logging. With a single-segment prefix like `/api` everything is correct. Please fix it.

**t3.** Please add a `uuid` route wildcard filter, so we can write routes like `/item/<id:uuid>`. It should match canonical UUID strings (`8-4-4-4-12` hex digits with hyphens, upper or lower case), pass a `uuid.UUID` object to the callback, and give a 404 for anything that isn't a UUID. Building URLs with `app.get_url()` should accept a `uuid.UUID` for that parameter.

**t4.** Please add an opt-in request ID feature. When `app.config['request_id.header']` is set to a header name (for example `X-Request-ID`): `request.request_id` returns the value of that header from the incoming request, or, if the request doesn't have it, a newly generated ID made of 32 lowercase hex characters. It must return the same value every time it is read during one request. Every response from that app carries that header with the request ID: normal responses, 404s, 500s caused by uncaught exceptions, `abort()`, `redirect()`, and a raised `HTTPResponse`. When `request_id.header` is not set, nothing changes: no extra header is sent.

| Task | What the hidden tests check |
|---|---|
| t1 | passwords with one and several colons; empty password; malformed headers still return None |
| t2 | 1-, 2- and 3-segment prefixes; `request.path`, `script_name` and `url` in the parent hook; an exception inside the sub-app |
| t3 | match; case-insensitivity; callback type; 404 on invalid input; URL building |
| t4 | every listed response path; incoming vs. generated ID; stability within a request; no header when unset |

## Appendix B. Arm B parts

| Part | Bytes | | Part | Bytes |
|---|---|---|---|---|
| `01_cli.py` | 2,016 | | `10_utils_config_dict.py` | 17,327 |
| `02_helpers.py` | 4,795 | | `11_utils_resource_manager.py` | 6,623 |
| `03_exceptions.py` | 395 | | `12_app_helpers.py` | 5,874 |
| `04_routing.py` | 14,746 | | `13_http_utils.py` | 10,157 |
| `05_app_bottle.py` | 18,694 | | `14_multipart.py` | 8,805 |
| `06_app_bottle_cast.py` | 2,886 | | `15_servers.py` | 13,187 |
| `07_http_base_request.py` | 19,558 | | `16_app_control.py` | 7,549 |
| `08_http_base_response.py` | 14,774 | | `17_templates.py` | 19,347 |
| `09_plugins.py` | 4,009 | | `18_globals.py` | 4,769 |

## Appendix C. Review findings and dispositions

| Finding | Disposition |
|---|---|
| 1: A/B tests package architecture, not file size | Accepted: B is the same module in one namespace |
| 2: re-exports break mutable globals | Resolved by construction; the gate checks `__globals__` |
| 3: example task invalid (`int` filter accepts negatives by design) | Accepted: replaced by mutation-tested setups |
| 4: `--max-turns` undocumented; no timeout | Partly accepted: smoke verified the flag; the runner enforces a timeout |
| 5: Read-tool limits confound file size | Accepted as scope: part of the real treatment; chunked reads measured |
| 6, 7: N=3 underpowered; 20% rule undefined | Accepted: estimand, interval and rule defined; labeled a pilot; staged N |
| 8: cumulative tokens double-count cache | Accepted: peak context is primary |
| 9: file-read flag unobservable | Accepted: exposure measured across Read and Bash |
| 10: contamination; network via Bash | Accepted: limitation; network flagged |
| 11: split is an uncontrolled intervention | Resolved: deterministic builder plus equivalence gate |
| 12: conditional arm C is outcome-selected | Rejected: C estimates the hook increment over B |
| 13: hook may never run | Accepted: C tasks would require a commit |
| 14: hook semantics underspecified | Accepted: explicit contract and test cases |
| 15: test file count ambiguous | Accepted: counts stated |

## Appendix D. Planned but not executed: arm C

Arm C would have added the pre-commit hook to B and required each task to end in a commit. The hook would block a file whose staged blob exceeds 20,000 bytes, exempting lockfiles, files with generated-code markers (`@generated`, `DO NOT EDIT`) and generated-file patterns (`*.pb.go`, `*.min.js`). Its validation cases covered the exact boundary (20,000 bytes passes, 20,004 blocks), staged vs. working-tree versions, deletions, renames, names with spaces, binaries, symlinks, submodules, and an error message with path, token count and split instructions. The hook was not built, because the A/B result did not justify it.
