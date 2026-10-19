# Haiku 5.5 as a delegated implementer in OpenCode across five effort levels (interrupted round)

- **Run date:** 11 October 2026 (gates and 100 screening trials in one afternoon session; the round stopped on an infrastructure error).
- **Status:** **incomplete.** 100 of 180 planned comparative trials ran (20 per effort level); 80 were never started. This README documents the protocol and reports the partial results as descriptive.
- **Agent runtime:** OpenCode 2.0.26 with the isolated-terminal-only harness of [../code-implementation-opencode/](../code-implementation-opencode/) (same controller, grader, observer, terminal, isolation, image and catalog).
- **Container image:** `sha256:5a3fe047f25468655ba68c3175b75ed9d184469370f957c5727763fa6d9f45ed` (Node 24.9.0, TypeScript 5.9.3, Python 3.11.2).
- **Model and route:** Claude Haiku 5.5 (`claude-haiku-5-5`) through a local OpenAI-compatible proxy, OpenCode selection `cli_proxy/cpa-claude-haiku-5-5#<effort>`, efforts `low`, `medium`, `high`, `xhigh`, `max`, adaptive thinking.
- **Budget per trial:** 1,200 s and 60 model calls (15 s grace); output limit 32,768 tokens per response; context 272,000 tokens.

## Abstract

We ran Claude Haiku 5.5 at five reasoning-effort levels on the corrected 12-task implementer benchmark from the companion study (small TypeScript/Python projects, hidden acceptance tests, isolated terminal only). Gates passed for all five efforts (5/5 interruption proofs, 5/5 smoke approvals). The round then stopped after 100 of 180 trials when a session export could not be parsed. On the 20 (task, repetition) pairs started for every effort, **low, medium, high and xhigh each reached 20/20 full approvals, while max reached 6/20.** All 13 max patch failures were empty patches: the final model call ended with `finish=length` after spending the entire 32,768-token output budget on reasoning and producing no output. Median session time among approved trials grew steadily with effort: 22.0 s (low), 36.1 s (medium), 64.7 s (high), 136.2 s (xhigh) and 325.5 s (max, 6 trials). In this setup, effort above low bought no extra approvals and cost time, and max failed under the per-response output limit.

## Introduction

The companion study ([../code-implementation-opencode/](../code-implementation-opencode/)) found that, after correcting an under-specified request, six configurations from four model families all passed 35/36 or 36/36 of the 12 bounded implementation tasks. This round asks whether a smaller, cheaper model, Haiku 5.5, holds up in the same delegated-implementer role, and how its reasoning effort setting changes outcome and time. Effort is a configuration choice for each agent role; if low effort is enough, higher settings only add latency.

## Hypotheses

The hypotheses were not written down before the runs; they are reconstructed from the design (`harness/DESIGN.md`, Portuguese):

- **H1 (feasibility):** the frozen harness, with only the cohort, task selection and a private variant declaration changed, can run all five Haiku efforts through the gates. *Confirmed:* 5/5 proofs and 5/5 smokes.
- **H2 (effort and approval):** higher effort yields more full approvals. *Not supported in the partial data:* low to xhigh were all 20/20; max was 6/20.
- **H3 (effort and time):** higher effort increases session time. *Supported (descriptive):* medians increase monotonically from low to max.

## Methodology

### Harness

[`harness/run.py`](harness/run.py) is a phase wrapper (budget → smoke → screening) around a frozen copy of the core harness in [`harness/harness/`](harness/harness/). Compared with the baseline core, only these differ, and the wrapper checks that the deltas are exactly these before importing the core:

- `domain.py`: the five Haiku candidates;
- `tasks.py`: selection of the 12 screening tasks, with `py-money-contract` replaced by the corrected `py-money-contract-v2`;
- `runtime.py`: inside `configuration()` only, an explicit declaration of the five Haiku variants (the frozen catalog did not yet contain Haiku 5.5), with the experiment's limits of 272,000 context and 32,768 output tokens;
- `contract.py` (new): the explicit monetary contract.

The core verifies hashes of its 19 harness files before every trial; the wrapper, README, tests, provenance, schedule and external budget are verified before and after every phase. Wrapper documentation (`README.md`, `DESIGN.md`) is in Portuguese and kept byte-identical because it is part of the frozen hashes. `harness/provenance.json` records the source hashes. `harness/analysis/summarize.py` was added for this publication to recompute the tables.

The agent system prompt, tools, permissions and scoring rules are identical to the companion study; see its Methodology section. The system prompt (verbatim, English in the original):

```text
Implement the requested change in the project. Use the terminal tool to explore and edit files and run the public checks. The Linux project is at /workspace. Keep changes within the requested scope. Preserve existing behavior. You receive one task; complete it autonomously and summarize the resulting change and verification. Do not use external services.
```

The 12 task requests are reproduced verbatim (English in the original) in Appendix A of the companion study, using `py-money-contract-v2` for the Python monetary task. Two known ambiguities (duplicate tags in `ts-profile-patch`, unknown envelope fields in `py-atomic-import`) were deliberately left unchanged.

### Design

| Phase | Composition | Sessions |
|---|---|---:|
| Interruption gate | 1 per effort, 20 s / 2 calls; `budget_exceeded` with `proof_passed=true` expected | 5 |
| Smoke | `clamp()` task, 1 per effort | 5 |
| Screening | 12 tasks × 5 efforts × 3 repetitions, block-balanced order (seed 20261010), 6 h global limit | 180 |

Efforts alternate within blocks of (task, repetition), so every started block covers all five efforts. Identity checks: the native audit had to find provider, alias, wire model and selected effort; every observed request had to carry model, effort, route, session and `thinking_type=adaptive`. This attests what was sent, not the backend behind the proxy.

Scoring: a trial is a full approval only if the session ended normally within budget with the requested identity and effort, private acceptance, regression, compilation, scope and structural checks pass. `patch_correct` and `session_completed` are recorded separately. Time is the agent session (`task_wall_s`), excluding preparation and grading.

### Why the round stopped

Infrastructure errors stop the sequence by design. Trial-0100 (max, `ts-archive-document`) ended with `infra_error`: the JSON export of the session could not be parsed (`Unterminated string starting at ... char 255468`). The agent had exited with code 0 after 335.03 s and 15 calls, and its changes to `checks/public.cjs` and `src/service.ts` were in scope, but the patch was never graded (`grade.not_executed=true`); the recorded `patch_correct=false` is a default of the error path, so that patch's correctness is unknown. The raw export stdout was not preserved. An offline check (`data/validation/haiku55-check-20261011T230212Z/stdout-capture-check.json`) showed the frozen helper captures a 1,000,016-byte JSON in full; a synthetic Bun reproduction showed truncation when a CLI writes to stdout and calls `process.exit` without draining. This supports, but does not prove, a truncation hypothesis in the OpenCode 2.0.26 binary. No trial was restarted and no source, result or budget was changed.

## Results

### Gates

| Effort | Interruption proof | Smoke | Smoke time (s) |
|---|---|---|---:|
| low | passed | approved | 7.58 |
| medium | passed | approved | 12.24 |
| high | passed | approved | 17.27 |
| xhigh | passed | approved | 53.45 |
| max | passed | approved | 154.71 |

Gate calls: 10 (interruption) + 32 (smoke) = 42.

### Screening, partial (100/180 trials)

The same 20 (task, repetition) pairs were started for each effort, covering 11 of the 12 tasks; `ts-event-stream` was never reached.

| Effort | Started | Full approval | Patch approved / graded | Calls | Median s (approved) | Range s (approved) | Median s (all closed sessions) |
|---|---:|---:|---:|---:|---:|---:|---:|
| low | 20/36 | 20/20 | 20/20 | 98 | 22.04 | 11.49–42.44 | 22.04 |
| medium | 20/36 | 20/20 | 20/20 | 125 | 36.13 | 12.51–78.35 | 36.13 |
| high | 20/36 | 20/20 | 20/20 | 167 | 64.65 | 20.99–143.08 | 64.65 |
| xhigh | 20/36 | 20/20 | 20/20 | 229 | 136.22 | 66.82–296.67 | 136.22 |
| max | 20/36 | 6/20 | 6/19 | 144 | 325.47 (n=6) | 256.92–421.25 | 167.43 (n=19) |
| **Total** | **100/180** | **86/100** | | **763** | | | |

Total model calls in the round: 805 (763 comparative + 42 gates). The generated `report.md` shows 167.43 s as the max median because it includes completed sessions with rejected patches.

Per task (approved / started):

| Task | low | medium | high | xhigh | max |
|---|---:|---:|---:|---:|---:|
| py-atomic-import | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| py-document-scope | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| py-exporter-consolidation | 2/2 | 2/2 | 2/2 | 2/2 | 1/2 |
| py-generator-cleanup | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| py-money-contract-v2 | 3/3 | 3/3 | 3/3 | 3/3 | 0/3 |
| py-transfer-commit | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| ts-archive-document | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| ts-cursor-orders | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| ts-idempotent-payment | 3/3 | 3/3 | 3/3 | 3/3 | 1/3 |
| ts-money-consolidation | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| ts-profile-patch | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |

### The max failures

All 13 graded max failures have empty patches (no changed files). Each session made exactly three HTTP 200 calls, exited with code 0 after 149.10 to 180.67 s, and was not interrupted by the controller. The last call ended with `finish=length` (`rawFinish=max_tokens`), 32,768 reasoning tokens and zero output tokens. The raw status is `completed` because the parser derives it from `idle.outcome=succeeded` and does not distinguish `finish=length`. The grader rejected 12 on acceptance and 1 (`py-exporter-consolidation`, trial-0050) on the structural check, where acceptance passed only because a refactoring's behaviour was already correct at baseline. Example: `data/results/haiku-5-5/screening/trials/trial-0008/`.

## Discussion

Within the 20 pairs that ran, Haiku 5.5 at low effort matched every higher effort on approvals (20/20) and was the fastest, with the fewest calls. Each step up in effort roughly doubled median session time without changing the outcome. For the delegated-implementer role on tasks of this size, the data favour `low` (or `medium`) for Haiku 5.5. Its 20/20 at low effort is in line with the companion study's saturation result.

The max result measures *this configuration under a 32,768-token per-response output limit*: the model spent the whole budget on reasoning before writing anything. It is not evidence of difficulty following instructions, and it does not show how max would behave with a larger output budget. Raising that limit would be a different experiment and would have to be labelled as such.

### Limitations

- Incomplete round: 100/180 trials, 11 of 12 tasks, one to three repetitions per task. Partial blocks were not chosen at random; they are the first blocks of the frozen schedule.
- One max patch (trial-0100) was never graded; its correctness is unknown.
- Small synthetic projects, isolated terminal only, no statistical tests, provider load not controlled; repetitions are not independent tasks.
- The answering backend behind the local proxy was not attested; identity checks cover only what was sent.
- The two known contract ambiguities remain in the task set (they did not cause any failure among the trials run).
- Independent reviews of the package and of the post-stop audit were done by a GPT-family model; no reviewer from another family was available.

## Reproduction

Requirements as in the companion study: Docker, OpenCode 2.0.26, a local OpenAI-compatible proxy on `127.0.0.1:8317` that serves `claude-haiku-5-5` with the five efforts, the container image above, and the OpenCode catalog snapshot (sha256 `f6a22feaaf4916289ead67712a27b2ba7ccdb38f6dc23ddfae11158b28a1a761`, not redistributed). The wrapper expects to live at `implementacao/opencode-implementador/rounds/haiku-5-5/` beside the core package under a parent `evals` directory, and must be run from that parent with a new output directory:

```sh
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py plan --out <new-dir>       # no model calls
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py validate --out <new-dir>   # no model calls
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py run --out <new-dir>        # 190 sessions
```

Completing the round requires fixing the session-export failure first and running into a fresh output directory with evidence preserved. To recompute the tables:

```sh
python3 -I harness/analysis/summarize.py data/results/haiku-5-5/screening
python3 -I harness/analysis/summarize.py data/results/haiku-5-5/budget data/results/haiku-5-5/smoke
```

## Data

Copied through the repository anonymizer (paths, user and host names replaced; OpenCode session IDs replaced with salted hashes). Text files over 1 MB are gzipped.

| Path | Contents |
|---|---|
| `data/results/haiku-5-5/round-freeze.json`, `round-summary.json` | Frozen sources, commands and schedules; per-phase status and call counts |
| `data/results/haiku-5-5/budget/`, `smoke/`, `screening/` | Phase outputs: `freeze.json`, `preflight.json`, `gates.json`, `validation.json`, `summary.json`, `report.md` (generated, Portuguese) and `trials/trial-NNNN/` |
| `data/validation/haiku55-plan/`, `haiku55-validate/` | Plan (5/5/180 schedules) and offline validation of the 12 tasks, no model calls |
| `data/validation/haiku55-preflight-attempt/` | Sandbox preflight blocked by Docker socket permissions, no inference |
| `data/validation/haiku55-tests.log`, `haiku55-root-check.json` | 20 wrapper tests; independent check of the package deltas and earlier hashes |
| `data/validation/haiku55-check-20261011T230212Z/` | Post-stop audit: report (Portuguese), snapshot with counts and hashes, stdout-capture check |
| `data/validation/haiku55-review.md`, `haiku55-work.md` | Review and work log (Portuguese) |

Trial directories contain `request.txt`, `result.json`, `control.json`, `session.json`, `run.stdout.jsonl`, `run.stderr`, `observations.jsonl[.gz]`, `terminal.jsonl`, `discovery.json`, `effective-config.json` and `grading/`; see the companion study's Data section for field descriptions.

**Excluded:** copies of the OpenCode model catalog snapshot (`models.json`, sha256 above) and Python bytecode caches.
