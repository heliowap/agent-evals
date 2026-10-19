# Does a "Deterministic first" AGENTS.md block improve coding-agent outcomes? Three isolated pilots

**Run dates:** preliminary prototype on 2026-10-09; isolated pilots on 2026-10-10 (all times UTC).
**Tools and models:**
- Codex CLI 0.162.1 with `gpt-6.1-sol`, reasoning effort `xhigh`.
- OpenCode 2.0.25 with `openai/gpt-6.1-sol#xhigh`.
- OpenCode 2.0.25 with `cli_proxy/cpa-claude-opus-5-5#medium`, which is Claude Opus 5.5 at `medium` effort routed through a local OpenAI-compatible proxy.

The preliminary runs used OpenCode 2.0.25 with the same Opus route and with `openai/gpt-6.1-sol-fast#high`.

## Abstract

We tested a 992-byte AGENTS.md block called "Deterministic first". It asks a coding agent to enforce rules with executable guardrails, compute outputs with tools or scripts instead of generating them, script a step the second time it repeats, and run independent commands in parallel. Each of three agent configurations ran 12 synthetic tasks, 3 repetitions and 2 arms: an empty AGENTS.md versus an AGENTS.md containing only the block. That gives 72 runs per configuration and 216 in total. Every configuration delivered **36/36 correct tasks without the block and 36/36 with it**, so the block produced no measurable quality gain. However, the control arm was already at the ceiling. The block increased mean agent-invocation time by +17.1% (Codex/Sol), +23.5% (OpenCode/Sol) and +5.8% (OpenCode/Opus). The Opus difference is inconclusive (exploratory 95% CI −7.0% to +24.1%). The most consistent cost came from the second-repeat scripting rule. In the `repeat` task, all 3 treated runs were slower than all 3 control runs in every configuration, and the deliverable did not change. As a result, the block was kept out of the user's global AGENTS.md.

## 1. Introduction

Users often add process rules to the global instruction files that coding agents load at startup (`AGENTS.md`). The block tested here appeared to be good engineering hygiene, and it could plausibly reduce arithmetic and bulk-edit errors and prevent regressions. It also costs context on every request, and its imperative obligations (create a script, verify it, parallelize) can add work that does not pay off within one task. The question was whether keeping the block in a global configuration is justified by measured outcomes, not by how sensible it sounds.

The exact treatment text, identical in both runners (`harness/*/variants/deterministic/AGENTS.md`):

```markdown
Deterministic first

- **Rules.** When a rule can be enforced by a guardrail (a plugin, a
  permission or policy, a git hook, a linter, a test), build the guardrail
  instead of writing the rule into `AGENTS.md`, a skill or an agent file, and
  tell the user which guardrail you built and why. When building one falls
  outside the task, propose it at the end instead. Written rules are for
  judgment calls no guardrail can check.
- **Actions.** When a program can produce the output (a count, a
  calculation, a search, a bulk edit, a format or schema conversion), compute
  it with a tool or a script instead of generating it. Prefer the project's
  own tools, then a configuration of them, then a new script; run a new
  script on a sample or check its diff before trusting it. Script a step the
  second time it repeats. One-off scripts go in the temp directory; tell the
  user before adding a permanent script or tool to a repository or config.
  Run independent commands in parallel.
```

## 2. Hypotheses

The isolated runner's README stated these hypotheses before the pilots ran (`harness/codex/README.md`, in Portuguese). The hypotheses were not formally pre-registered with thresholds, and the pilots were declared non-deciding in advance.

- **H1 (primary):** the block increases the proportion of tasks delivered correctly.
- **H2:** for correct deliveries, the block reduces token use and duration.
- **H3:** the block increases tool and script reuse.
- **H4:** the block makes the agent create checks that detect when an error comes back.
- **Possible harms:** unnecessary scripts, out-of-scope edits, over-automation of judgment tasks, and running dependent steps concurrently.

The preliminary prototype had its own pre-stated winner rule. The arm without the section wins if its pass rate is at least as high and its median total tokens per task are at least 10% lower; otherwise the section is kept (`harness/preliminary/CARD.md`).

## 3. Methodology

### 3.1 Arms and isolation

- **Control (`empty`):** a private global `AGENTS.md` of 0 bytes.
- **Treatment (`deterministic`):** a private global `AGENTS.md` containing only the block (992 bytes).

The rest of the user's global instructions, skills and plugins was excluded from both arms. The study therefore measures the block on top of each product's base configuration, not its marginal effect inside the user's full instruction set. Each product's built-in system prompt and tools were present in both arms.

**Codex runner** (`harness/codex/`). Each run got a fresh working directory, Git repository, `CODEX_HOME` state and temp directory. The CLI ran with `--no-daemon`, sandbox `workspace-write` and approval `never`. Plugins, apps, hooks, memory and multi-agent were disabled, and every discovered skill was disabled by its `SKILL.md` path. Before any inference, `codex debug prompt-input` was used to check that the empty arm loaded no AGENTS.md text and the treatment arm loaded exactly the block. The run aborted otherwise (`data/codex/validation/`).

**OpenCode runner** (`harness/opencode/`). Each run got a fresh Git project, XDG directories, discovery home and session database. Inherited config, endpoints and keys were dropped, and project and ancestor instruction discovery was disabled. The built-in `opencode.skill` plugin was disabled, there were no external plugins, skills or MCP servers, and subagent, skill and web tools were denied. A preflight on a temporary local server, run before every trial, compared the effective configuration and the discovered plugins and skills across arms. OpenCode does not expose the full prompt in this flow, so equality of the complete HTTP request was **not** demonstrated. On the proxy route, the client-side model identity is checked in every exported assistant message. This does not prove which model the upstream service actually served.

The runners use the same `cases.py`, rubric (`REVIEW.md`) and variant files. The OpenCode runner checks this byte-for-byte before freezing a run. Each run writes `freeze.json` before the first inference, with hashes of sources, protocol, variants and schedule.

### 3.2 Cases

There are 12 synthetic tasks. Fixtures are generated deterministically by `cases.py`, and the gold answers stay in the controller process, outside the working directory. The prompts are in English and are reproduced verbatim:

| Case | Group | Prompt (verbatim) | Main criterion |
|---|---|---|---|
| `count` | actions | Count requests in access.log with status 500–599 and timestamp on 2026-10-09 from 10:00:00 inclusive to 11:00:00 exclusive. Write the integer to answer.txt. | Exact integer, with boundary traps |
| `money` | actions | In invoices.csv, total amount_cents for paid rows with currency BRL. Write only the integer total to answer.txt. | Exact total, with negatives and filters |
| `convert` | actions | Convert customers.csv to customers.json as an array in original row order. Keep id and note as strings, including leading zeros and embedded newlines. Convert active to a boolean and blank age to null, otherwise an integer. | Content, order and types preserved |
| `rename` | actions | Rename get_user_name to fetch_user_name throughout userlib, including definitions, imports and calls. Preserve get_user_name_legacy and all current behavior. | Correct uses changed, sibling untouched, tests pass |
| `project_tool` | actions | Produce report.json from orders.json using this project's order-report contract. The available interface is documented in README.md. | Respects the existing tool's contract |
| `repeat` | actions | Turn 1: For batch-a.csv, count rows whose state is ready by region. Save a JSON object to a-summary.json. Turn 2 (same session): Now do the same for batch-b.csv and batch-c.csv, saving b-summary.json and c-summary.json. | Three correct summaries; reuse observed |
| `guardrail` | rules | Prevent future uses of Python's eval builtin in src from passing this repository's standard check. The existing check is documented in README.md. Ordinary comments, strings and obj.eval method calls must remain valid. | Check rejects forbidden calls and accepts valid ones (grader mutates code) |
| `regression` | rules | clamp(value, low, high) should reject low > high with ValueError. Fix this recurring defect and make sure our standard unittest command catches it if someone reintroduces it. Preserve behavior for valid bounds. | Fix plus a test that fails when the defect is reintroduced |
| `out_of_scope` | controls | Review parser.py for a concrete defect in parse_enabled. Values other than the exact strings true and false should raise ValueError. Do not change any files. Explain the defect and recommend how to prevent recurrence. | Correct diagnosis, executable prevention proposed, no edits |
| `judgment` | controls | Rewrite only message.md to explain a delayed export in a calm, concise tone. Preserve every fact. This is a one-time wording change. | All facts kept, tone, only message.md changed |
| `independent` | actions | Run the three independent health checks in checks/ and write their actual returned values as a JSON object in health.json, keyed alpha, beta and gamma. | Real values; temporal overlap recorded separately |
| `dependent` | controls | Change settings.json mode to strict, regenerate manifest.json with python3 generate.py, then verify it with python3 verify.py. Both generated content and verification must correspond to the new setting. | Output consistent with the new setting; order kept |

### 3.3 Design and scoring

Each configuration ran 12 cases × 3 repetitions × 2 arms = 72 runs in 36 (case, repetition) pairs. Pair order was shuffled with seed 20261010, and the first arm was balanced (18 pairs started with each). One arm ran at a time. In `repeat`, each run continued only its own session. Limits were 600 s of agent time per run and a run-level budget checked between pairs. There were no retries and no model or provider fallback; the runners stop at the first infrastructure failure.

Outcome and obedience were scored separately. Using a script, running commands in parallel or writing a test earns no points unless the task itself asks for prevention. In that case the grader reintroduces the defect in a copy of the artifacts and checks that the guardrail catches it while still accepting valid inputs. Automatic checks for `out_of_scope` and `judgment` are partial. These 6 control runs per arm were accepted by a rubric review, written before the runs, of label-free artifacts (`blind/*/review.json`). Review hashes were sealed (`review-seal.json`) before the key was opened. The reviewer was the assistant that ran the study, which knew the design and some aggregate metrics. Some answers reveal their arm, and there was no independent human review.

**Measures.** Duration is the wall time of the agent invocation(s). It includes CLI boot and tool calls, and excludes setup, auditing, export and grading. Tokens use each product's native counters, which have different meanings:
- Codex counts cached input inside input and reasoning inside output.
- OpenCode reports input, cache read, cache write, output and reasoning separately.
- The proxy route reported 2–4 native input tokens per message and zero reasoning.

Counters are cumulative within a session, so only the last counter of each run is used. No monetary cost was estimated.

**Statistics.** All comparisons are paired within a configuration. Repetitions of the same 12 cases are not independent tasks. The runners report an exploratory pass-rate difference with a bootstrap clustered by case. For Opus, a case-clustered bootstrap of the mean duration difference (20,000 samples, seed 20261010) was chosen after the run and is labelled exploratory. The cross-product comparisons are also exploratory: runs were not interleaved across products, and the Codex and OpenCode/Sol runs partly overlapped in time.

### 3.4 Preliminary prototype and smoke runs

Before the isolated design, a prototype (`harness/preliminary/`, 2026-10-09) compared the user's **full** global OpenCode AGENTS.md (arm A, 4,211 bytes) with the same file minus the section (arm B, 3,215 bytes). Its AGENTS.md text is not archived; only the hashes are. It used 4 tasks:
- `T1-count`: count 5xx log lines in a time window.
- `T2-rename`: bulk rename that must leave a `_legacy` sibling untouched.
- `T3-rule`: "Make sure nobody can commit .env files in this repository."
- `T4-control`: "The tests in this repository fail. Fix the bug."

It made four runs:

| Run | Model | Runs | Pass A / B | Pre-stated rule outcome |
|---|---|---:|---|---|
| `20261009T213750Z-smoke` | Opus 5.5 via proxy | 2 | 1/1 / 0/1 (T4) | keep section |
| `20261009T213951Z-smoke2` | Opus 5.5 via proxy | 2 | 1/1 / 1/1 | keep section |
| `20261009T214013Z-pilot` | Opus 5.5 via proxy | 24 | 12/12 / 12/12 | keep section (median B/A token ratio 1.11) |
| `20261009T215927Z-pilot-sol-fast-high` | Sol 6.1 fast, high | 24 | 12/12 / 12/12 | remove section (median B/A token ratio 0.89) |

These runs changed the full instruction file rather than isolating the block, ran the two arms concurrently, and gave opposite rule outcomes across models. They are kept as history and do not enter the results below.

Several attempts with the isolated runners also produced no comparison:
- **Codex smoke and the first Codex pilot attempt** (`data/codex/results/smoke`, `pilot-20261010-r1`): each made 1 attempt that ended in an infrastructure error (`workspace routing discovery failed`) because network access was disabled in the assistant's sandbox. The remaining runs did not start.
- **First OpenCode attempt** (`data/opencode/results/pilot`): aborted in preflight before any task (`Expected only the built-in OpenCode plugins`). The cause was a plugin-activation race in the runner, which was fixed.
- **OpenCode/Sol smoke** (`smoke-r3`): 4/4 passes on `count` and `repeat`. This validated the runner.

All three full pilots were then run in the user's own terminal.

## 4. Results

### 4.1 Outcome

| Configuration | Run folder | Completed | Correct, empty | Correct, deterministic |
|---|---|---:|---:|---:|
| Codex 0.162.1 / Sol 6.1 xhigh | `data/codex/results/pilot` (15:09–16:02 UTC) | 72/72 | 36/36 | 36/36 |
| OpenCode 2.0.25 / Sol 6.1 xhigh | `data/opencode/results/pilot-r2` (15:43–16:31 UTC) | 72/72 | 36/36 | 36/36 |
| OpenCode 2.0.25 / Opus 5.5 medium | `data/opencode/results/opus-5-5-medium` (17:24–17:42 UTC) | 72/72 | 36/36 | 36/36 |

All 216 runs passed the automatic checks. In each configuration the 12 rubric-reviewed control runs (6 per arm) were accepted 12/12. File hashes confirmed that `out_of_scope` changed no files and `judgment` changed only `message.md`. There were no infrastructure failures. H1 is not supported, but the ceiling also made it nearly untestable.

### 4.2 Duration

| Configuration | Mean, empty | Mean, deterministic | Δ mean | Median, empty | Median, deterministic |
|---|---:|---:|---:|---:|---:|
| Codex / Sol | 40.46 s | 47.37 s | +17.1% | 39.02 s | 42.43 s |
| OpenCode / Sol | 34.14 s | 42.17 s | +23.5% | 27.13 s | 31.60 s |
| OpenCode / Opus | 12.70 s | 13.43 s | +5.8% | 12.23 s | 13.64 s |

For Opus, the treatment was faster in 18/36 pairs. The exploratory clustered-bootstrap 95% CI for the mean difference was [−7.0%, +24.1%], and excluding `repeat` changes the difference to −1.6%. H2 is not supported: the direction was unfavourable in all three configurations and clearly so in the two Sol runs.

The `repeat` case was where the block had the most consistent effect (per-run durations, s):

| Configuration | Empty | Deterministic | Median empty → deterministic |
|---|---|---|---|
| Codex / Sol | 48.41, 48.49, 61.54 | 83.27, 84.79, 91.70 | 48.5 → 84.8 |
| OpenCode / Sol | 40.28, 42.44, 42.59 | 75.68, 82.79, 87.88 | 42.4 → 82.8 |
| OpenCode / Opus | 11.97, 12.53, 14.88 | 22.48, 24.42, 25.43 | 12.5 → 24.4 |

Without the block, the agent already processed batches B and C with an inline Python loop. With it, the agent wrote a reusable temporary script, verified it, and then reused it. The result was the same.

Other per-case effects (medians, from the curated analyses):
- **Codex.** `convert` went from 32.2 to 65.2 s and `rename` from 61.2 to 76.8 s. The treatment switched from inline Python or a model-written patch to a script file with verification. `convert` and `repeat` together account for about 205 s of the 249 s added.
- **OpenCode/Sol.** `rename` went from 53.8 to 91.5 s and `repeat` from 42.4 to 82.8 s; in both, every treated run was slower than every control run. `convert` was faster with the block (75.5 → 51.7 s) when 2/3 treated runs wrote the JSON programmatically instead of by patch. The third treated run still used a patch and took 103.2 s.
- **Opus.** The control already generated `customers.json` with Python in 3/3 `convert` runs.

### 4.3 Tokens

| Configuration | Counter | Empty | Deterministic | Δ |
|---|---|---:|---:|---:|
| Codex / Sol | Output incl. reasoning | 35,800 | 43,232 | +20.8% |
| Codex / Sol | Input incl. cache | 2,153,921 | 2,205,259 | +2.4% |
| Codex / Sol | Uncached input | 450,113 | 363,467 | −19.2% |
| OpenCode / Sol | Output excl. reasoning | 27,092 | 27,892 | +3.0% |
| OpenCode / Sol | Reasoning | 4,206 | 12,436 | +195.7% |
| OpenCode / Sol | Output + reasoning | 31,298 | 40,328 | +28.9% |
| OpenCode / Sol | Total incl. cache and reasoning | 955,983 | 1,027,782 | +7.5% |
| OpenCode / Opus | Output as reported by proxy | 28,740 | 33,034 | +14.9% |

**Correction.** The Codex `result.json` files store a top-level `output_tokens` that sums the session-cumulative counters of both `repeat` turns. That double-counts turn 1 in the 6 `repeat` trials and gives 37,348 / 45,410 output tokens when summed directly. The curated analysis used only the last counter (`usage_raw[-1]`), reconciled against the rollout logs (`usage-audit.json`), which gives 35,800 / 43,232 (`corrected-metrics.tsv`). We re-summed the archived data and confirmed both figures. The original `result.json` files are preserved unmodified, and the runner was fixed afterwards. The OpenCode runner already used the last cumulative export.

### 4.4 Behaviour (H3, H4)

| Observation | Codex/Sol empty / det. | OpenCode/Sol empty / det. | OpenCode/Opus empty / det. |
|---|---|---|---|
| All three independent checks overlapped in time | 3/3 / 3/3 | 3/3 / 3/3 | 1/3 / 0/3 |
| Guardrail or test caught the reintroduced defect (`guardrail` + `regression`) | 6/6 / 6/6 | 6/6 / 6/6 | 6/6 / 6/6 |
| Tool calls (sum) | 218 / 250 | 326 / 330 | 159 / 165 |

The block did not increase parallelism, and on Opus the only run with overlap was in the control arm. Both arms built working guardrails, but those prompts ask for prevention explicitly. The study therefore does not measure whether the block makes an agent propose a guardrail unprompted. So 100% correct deliveries does not mean every sentence of the block was obeyed. Codex had 21 non-zero command exits (searches with no match, deliberately red tests before a fix, a diff, and one failed temporary assertion that was later fixed). OpenCode/Sol had 6, all deliberately red tests. Opus had two calls to a non-existent `tool_write` tool and two shell exit-1 commands (including `head -0` on macOS). All of these runs still ended correct, and no trial was excluded.

### 4.5 Exploratory cross-product comparison

These are the same 72 (case, repetition, arm) combinations in each configuration. With Sol xhigh in both, OpenCode used 55.3% fewer normalized total tokens than Codex (1,983,765 vs 4,438,212, including resent context, cache and reasoning) and 13.1% less time, and it was faster in 56/72 matches. OpenCode/Opus via the proxy took 62.8% (empty) and 68.1% (deterministic) less mean time than OpenCode/Sol. In each comparison the product or the model, effort, provider and time of day changed together, so these numbers describe the runs but do not identify a cause.

## 5. Discussion

The block did not improve measured delivery in any of the three configurations, and it made the agent slower overall in two of them. The clearest mechanism is the obligation "Script a step the second time it repeats". The agents already automated the repeated step inline, and turning that into a verified script file roughly doubled the time of `repeat` in every configuration without changing the output. The `Actions` guidance did produce one localized benefit (OpenCode/Sol `convert`), but the same kind of change made Codex `convert` slower. For these models, the behaviours the block asks for (compute with Python, run checks in parallel, write regression tests when asked) were largely present without it.

**Configuration change.** The block was kept out of the user's global AGENTS.md. This is a provisional decision about the whole block. It does not show that guardrails, tests or parallel commands are useless. A follow-up on removing other low-value text is in [../agentsmd-pruning-opencode/](../agentsmd-pruning-opencode/), and a section-by-section ablation is in [../agentsmd-section-ablation-opencode/](../agentsmd-section-ablation-opencode/).

**Limitations and threats to validity.**
- **Ceiling.** The control arm reached 36/36 everywhere, so the suite could not show a quality gain. A test of H1 needs tasks the control still fails.
- **Small, synthetic sample.** 12 cases with 3 repetitions each; repetitions are not independent tasks. Long-run benefits (reuse after many repetitions, fewer recurrences, less rework) were not measured.
- **Prompts that ask for prevention.** `guardrail` and `regression` request a safeguard explicitly, so spontaneous guardrail proposals were not tested.
- **Whole block only.** `Rules`, `Actions` and the second-repeat rule were not separated, and a shorter rewrite was not tested.
- **Isolation is partial.** Built-in product prompts were present in both arms, and full HTTP request equality was not captured. On the proxy route the upstream model identity is not attested, and the proxy's token accounting (near-zero native input, zero reasoning) does not support cost or reasoning conclusions.
- **Duration is noisy.** It includes remote service latency, and there was no profiling to separate inference, proxy, network, boot and tools.
- **Review.** Rubric reviews of the judgment controls were done by the assistant that ran the study, with partial blinding and no independent human reviewer.
- **Post hoc statistics.** The Opus bootstrap interval and the "without `repeat`" sensitivity analysis were chosen after the run.

## 6. Reproduction

Requirements: Python 3.10+, Git, and Codex CLI 0.162.1 or OpenCode 2.0.25 with access to the listed models. The OpenCode runner as archived targets the local-proxy Opus route and expects the proxy key in `CLIPROXY_API_KEY`. Re-running Sol requires a new frozen plan. No provider configuration or credentials are included.

```sh
# Offline unit tests of graders and runners (no model calls)
cd harness/codex && python3 -m unittest -v test_eval.py
cd harness/opencode && python3 -m unittest -v

# Live runs (consume quota). Output folders must be new.
cd harness/codex && python3 run.py preflight --out validation/isolated-context \
  && python3 run.py run --out results/pilot && python3 run.py report results/pilot && python3 run.py blind results/pilot
cd harness/opencode && python3 run.py preflight --out validation/preflight \
  && python3 run.py run --out results/new-run
```

Offline re-analysis scripts are archived next to each run: `data/codex/results/pilot/analyze.py`, `data/opencode/results/pilot-r2/analyze.py` and `data/opencode/results/opus-5-5-medium/analyze.py`.
- The OpenCode scripts load the evaluator from the run's `frozen-source/`.
- The Codex script expects the runner sources one level above `results/`. To run it, copy `harness/codex/*` into `data/codex/`.
- The scripts check source hashes against `freeze.json`. Python sources and variants are byte-identical to the originals, but the anonymizer rewrote paths in some Markdown and JSON files. Hash checks on those files, and steps that rebuild paths from exported sessions, may therefore fail on this copy.

The archived `analysis.json`, `metrics.tsv` and `corrected-metrics.tsv` are the outputs those scripts produced on the original data.

The runner scripts, their comments and their generated report strings are in Portuguese and were left untranslated: changing them would break the source hashes recorded in `freeze.json`. The prompts are in English (section 3.2).

## 7. Data

```
harness/
  preliminary/   prototype runner, task fixtures/graders, CARD.md (protocol and winner rule)
  codex/         isolated Codex runner, cases.py, REVIEW.md (rubric), variants/{empty,deterministic}/AGENTS.md, plans/
  opencode/      isolated OpenCode runner (same cases, rubric and variants), plans/{default,activation-fix,skills-isolated,opus-5-5-medium}/
data/
  preliminary/<run>/          args.json, variants.json (hashes only), results.jsonl, report.md
  codex/results/pilot/        72 trial-NNNN/ folders, blind/, blind-key.json, review-seal.json, freeze.json,
                              frozen-source/, analysis.{md,json}, corrected-metrics.tsv, usage-audit.json, analyze.py
  codex/results/{smoke,pilot-20261010-r1}/   aborted attempts (infra error, network disabled)
  codex/validation/           prompt-input context captures for both arms, model catalog, preflight
  opencode/results/pilot-r2/  OpenCode/Sol pilot (same layout as above, plus metrics.tsv and partial snapshots)
  opencode/results/opus-5-5-medium/   OpenCode/Opus pilot (same layout)
  opencode/results/{pilot,smoke-r3}/  aborted preflight attempt and 4-run smoke
  opencode/validation/        preflight, discovery and version probes
  reports/                    archived Portuguese reports with an English index (reports/README.md)
```

Each `trial-NNNN/` contains `result.json` (case, rep, arm, status, wall time, model and effort, token counters, `usage_raw`, tool-call count, `grade` with per-check results and observations), the CLI event stream (`turn-N.jsonl`, `.stderr`), OpenCode session exports (`turn-N-export.json`), `tool-events.json`, final answers, `isolation.json`, the initial file snapshot, and the final `work/` directory. Session IDs are replaced by salted hashes. Local paths, user names and the macOS per-user temp-directory ID are replaced by placeholders.
