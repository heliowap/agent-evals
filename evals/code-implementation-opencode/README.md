# Delegated code implementation in OpenCode: six-configuration screening, contract correction, and a Sol low / GLM Flash cohort

- **Run dates:** 10–11 October 2026 (gates and original screening on 10–11 Oct; monetary-contract rerun and Sol/GLM cohort on 11 Oct). Times in the raw data are machine-local or UTC as labelled.
- **Agent runtime:** OpenCode 2.0.26, one custom agent (`implementer`), native tools removed; the only tool is an isolated `terminal` plugin that runs commands in a network-less Linux container.
- **Container image:** `sha256:5a3fe047f25468655ba68c3175b75ed9d184469370f957c5727763fa6d9f45ed` (Node 24.9.0, TypeScript 5.9.3, Python 3.11.2), built from [`harness/Dockerfile`](harness/Dockerfile).
- **Models and routes:** Claude Sonnet 5.5 (medium, high) and Claude Opus 5.5 (medium) through a local OpenAI-compatible proxy (`cli_proxy/...`, Anthropic Messages protocol); GPT-6.1 Sol with Fast selected (low, medium, high) through OpenCode's native OpenAI OAuth route; DeepSeek V4.1 Flash (max) and GLM 5.3 Flash (high, max) through the OpenCode Go subscription (`opencode-go/...`).
- **Budget per trial:** 1,200 s and 60 model calls, enforced by an external controller (15 s grace).
- **Companion study:** the Haiku 5.5 five-effort round that reuses this harness is published separately in [../code-implementation-opencode-haiku-effort/](../code-implementation-opencode-haiku-effort/).

## Abstract

We asked whether different model/effort configurations, running as a *delegated implementer* inside OpenCode, can take a bounded change request on a small layered project and deliver a patch that passes hidden acceptance tests without breaking regression, compilation or scope. Twelve tasks (six TypeScript/Node, six Python) were run three times for each configuration. In the original six-configuration screening, 202/216 trials were fully approved; 13 of the 14 failures were on one task, `py-money-contract`, where only Sonnet high (3/3) and DeepSeek max (2/3) passed. Rewriting only that task's request to state the contract explicitly (same starting code, reference and private tests) produced 18/18 approvals, and the corrected screening reaches **215/216**: every configuration 36/36 except DeepSeek max 35/36, whose remaining failure sits on another under-specified contract point. A later cohort of Sol 6.1 low Fast, GLM 5.3 Flash high and GLM 5.3 Flash max on the same corrected 12-task set reached **100/108 full approvals and 104/108 test-approved patches** (Sol low 35/36 full and 36/36 patches). At this task size the configurations are not separated by functional pass rate; they differ mainly in session time and call count (median session among approved trials from 16.6 s for Sonnet medium to 194 s for GLM Flash max). The tasks were too easy and too few to rank implementers; the most important finding is that incomplete contracts, not model capability, explained almost all failures.

## Introduction

The study belongs to a series that selects which model and reasoning effort to assign to each agent role in an OpenCode setup (see the exploration-role study in [../code-exploration-sol-fast-vs-deepseek/](../code-exploration-sol-fast-vs-deepseek/)). For the *implementer* role the agent receives one delegated task with the desired behaviour, acceptance criteria, constraints, entry points and public check commands, and must return a working patch. There is no second corrective message, no reviewer, no web, MCP or subagents. The question is practical: which configuration delivers correct, in-scope patches reliably and at what cost in time and calls, and does extra reasoning effort help?

A second goal was methodological: build a harness that separates a *correct patch* from a *completed session*, and both from transport or observation failures, so that an interrupted session with a good patch is not counted as a capability failure, and a confident final message is not counted as success.

## Hypotheses

The hypotheses were not pre-registered as testable statements. The harness README (in Portuguese, [`harness/README.md`](harness/README.md)) states the comparison set as "comparison hypotheses, not a ranking". The following are reconstructed from that design:

- **H1 (feasibility):** an isolated-terminal-only OpenCode agent with an external budget controller can complete the matrix with real model calls, and the gates (interruption proof, smoke) can be made to pass for all configurations. *Confirmed* after four interruption-gate rounds (see Results).
- **H2 (effort helps):** a higher effort level of the same model (Sonnet high vs medium, Sol high vs medium) yields more full approvals. *Not supported:* after the contract correction both pairs were 36/36; higher effort only increased time.
- **H3 (capability spread):** the six configurations differ in full-approval rate on the screening tasks. *Not supported at this task size:* 215/216 after correction. The original 202/216 spread was almost entirely a single under-specified task.
- **H4 (contract hypothesis, formulated after the screening):** the `py-money-contract` failures were caused by an incomplete request rather than by the models. *Supported, with caveats:* 5/18 → 18/18 after rewriting only the request; three repetitions of one task, with no contemporaneous control of the old contract.
- **H5 (cohort extension, exploratory):** Sol low Fast and GLM 5.3 Flash (high, max) can match the first cohort on the corrected set. *Partly:* Sol low 35/36 full (36/36 patches), GLM high 34/36, GLM max 31/36.

## Methodology

### Harness

All code is in [`harness/`](harness/). Source files are byte-identical to the archived originals, so the SHA-256 values in each `freeze.json` still verify.

| File | Role |
|---|---|
| `domain.py` | Task, candidate and budget data types; the six original candidates |
| `tasks_python.py`, `tasks_typescript.py` | Each task: request, starting files, reference solution, private acceptance test, allowed paths, optional structural check |
| `tasks.py` | Task inventory, smoke task and interruption-proof task |
| `bench.py` | CLI: `plan`, `validate`, `preflight`, `run`, `report`; freezes sources, catalog hash, schedule and parameters; writes `summary.json` and `report.md` |
| `runtime.py` | Builds a private OpenCode config per trial, starts the server, verifies transport, identity and effort |
| `controller.py` | External budget controller: counts calls and time, calls `session.interrupt`, stops the container |
| `terminal.js` | The only agent tool: runs commands in a Docker container with the project mounted at `/workspace`, no network |
| `observer.js` | Passive plugin that records HTTP/WebSocket requests and responses with original error codes |
| `isolation.py` | Docker/namespace isolation and proofs (mounts, denied external access, no network, subprocess cleanup) |
| `grader.py` | Re-applies only the allowed patch in a clean container, restores the original public checks, runs compilation, regression, private acceptance and structural checks |
| `test_*.py`, `test_*.mjs`, `verify_native_terminal.mjs` | Harness self-tests (no model calls) |
| `decisions.tsv` | Design decision log (Portuguese) |
| `rounds/money-contract-v2/` | Rerun of the monetary Python task with the explicit contract (`request.txt`) |
| `rounds/money-sol-low-glm-flash/` | New cohort gates plus 9 corrected-monetary trials |
| `rounds/sol-low-glm-flash-rest/` | Continuation: the other 11 tasks (99 trials) for that cohort, reusing the passed gates |
| `analysis/summarize.py` | Added for this publication: recomputes the tables below from `result.json` files |

Documentation files inside `harness/` (`README.md`, `rounds/*/README.md`, `DESIGN.md`, `decisions.tsv`) are kept in Portuguese because their bytes are part of the frozen source hashes. This README is the English description.

### Agent configuration

Each trial gets a fresh private OpenCode state. Permissions deny everything except `terminal`; `external_directory` is denied; formatter, LSP, MCP, skills, instructions, title and summary agents are disabled; the only plugins are the observer and the terminal. Native step limits are disabled so that only the external controller ends sessions (OpenCode adds an extra assistant turn when a native limit triggers, which had broken an earlier exploration round). The agent system prompt, identical for all configurations, is (verbatim, English in the original):

```text
Implement the requested change in the project. Use the terminal tool to explore and edit files and run the public checks. The Linux project is at /workspace. Keep changes within the requested scope. Preserve existing behavior. You receive one task; complete it autonomously and summarize the resulting change and verification. Do not use external services.
```

The user message is the task request (Appendix A). All task requests are in English in the original; no translation is needed.

### Configurations

| ID | OpenCode selection | Wire model | Route |
|---|---|---|---|
| sonnet-medium | `cli_proxy/cpa-claude-sonnet-5-5#medium` | claude-sonnet-5-5 | local OpenAI-compatible proxy, Messages protocol |
| sonnet-high | `cli_proxy/cpa-claude-sonnet-5-5#high` | claude-sonnet-5-5 | same |
| opus-medium | `cli_proxy/cpa-claude-opus-5-5#medium` | claude-opus-5-5 | same |
| sol-fast-medium | `openai/gpt-6.1-sol-fast#medium` | gpt-6.1-sol | native OpenAI OAuth (ChatGPT Codex backend), Responses protocol, Fast selected |
| sol-fast-high | `openai/gpt-6.1-sol-fast#high` | gpt-6.1-sol | same |
| deepseek-max | `opencode-go/deepseek-v4.1-flash#max` | deepseek-v4.1-flash | OpenCode Go, chat protocol |
| sol-fast-low (cohort 2) | `openai/gpt-6.1-sol-fast#low` | gpt-6.1-sol | native OpenAI OAuth, Fast selected |
| glm-flash-high (cohort 2) | `opencode-go/glm-5.3-flash#high` | glm-5.3-flash | OpenCode Go |
| glm-flash-max (cohort 2) | `opencode-go/glm-5.3-flash#max` | glm-5.3-flash | OpenCode Go |

Identity verification: for every trial the runtime audited the native configuration (provider, alias, wire model, effort) and the observer checked that each outgoing request carried the requested model, effort, route and session (`request_settings_verified`). This verifies what was *sent*; it does not attest which backend answered behind the proxy or subscription.

Fast tier: for the Sol configurations, `service_tier=priority` was verified as forwarded in every trial, but the terminal response reported `default` in all Sol trials (`fast_served=not_confirmed` in 72/72 screening, 6/6 contract-rerun and 36/36 cohort-2 trials). A source reading of the proxy code (`data/validation/fast-tier-source-notes.md`, CLIProxyAPI commit `633250c58de154300668f6bd87689d542dee7ae7`) shows that the proxy forwards `priority` and does not rewrite the tier, but the Sol trials here used OpenCode's native OAuth route, not that proxy. Whether Fast was actually served is therefore unknown; times are reported "with Fast requested".

### Tasks

Twelve screening tasks, one per family and language. Each is a small project (12 to 34 initial lines in `src/`) with layers and explicit dependencies, pinned dependencies and clocks, and local deterministic stand-ins for external services.

| Family | TypeScript/Node | Python |
|---|---|---|
| Cross-layer feature | `ts-cursor-orders` (cursor pagination with stable order) | `py-atomic-import` (batch import with validation, summary, atomicity) |
| Correctness and side effects | `ts-idempotent-payment` (retry without duplicate debit) | `py-transfer-commit` (rollback, publish only after commit) |
| Authorization and scope | `ts-archive-document` (no cross-tenant access) | `py-document-scope` (tenant, owner, soft delete) |
| Validation and contracts | `ts-profile-patch` (absent / null / empty fields) | `py-money-contract` (money values without improper rounding) |
| Streaming and cleanup | `ts-event-stream` (async iterator cancellation releases once) | `py-generator-cleanup` (early generator close, cleanup on exceptions) |
| Refactoring with preservation | `ts-money-consolidation` (consolidate conversions, remove an internal API) | `py-exporter-consolidation` (unify exporters, keep interfaces) |

Eight further *confirmation* tasks are defined in the task files and were validated offline, but the confirmation phase was never run. Before admission, every task's baseline had to fail the new requirement and pass public regressions, and the reference had to pass all criteria (`data/validation/offline-screening/`, `data/validation/offline-confirmation/`). Hidden tests check only behaviours described in the request; patches are never compared with the reference.

`py-money-contract-v2` is `py-money-contract` with a rewritten request (Appendix A shows both). Starting code, reference, public tests, private acceptance and allowed scope are unchanged; only the request and its copy in the project README differ.

### Phases

| Phase | Composition | Sessions |
|---|---|---:|
| Interruption gate (`budget`) | 1 per configuration, 20 s / 2 calls; `budget_exceeded` with `proof_passed=true` is the expected outcome | 6 per round |
| Smoke | `clamp()` in a tiny Python project, 1 per configuration | 6 |
| Screening | 12 tasks × 6 configurations × 3 repetitions, block-balanced order (seed 20261010) | 216 |
| Contract rerun | `py-money-contract-v2` × 6 configurations × 3 repetitions | 18 |
| Cohort 2 gates | 3 interruption + 3 smoke | 6 |
| Cohort 2 screening | corrected 12-task set × 3 configurations × 3 repetitions (9 monetary + 99 others) | 108 |

Sessions run sequentially. Cache on the provider side may persist across trials.

### Scoring

A trial is a **full approval** (`accepted`) only if all hold: (1) the session ended normally within budget, with the requested identity and effort; (2) private acceptance tests pass; (3) the original regression suite and compilation/type checks pass in the grader's trusted environment; (4) the diff stays inside the allowed paths and does not touch the evaluation mechanism; (5) explicit structural requirements, if any, are met. `patch_correct` (criteria 2–5 only), `session_completed`, scope violations, budget exceeded and integration failures are recorded separately. Every started trial is in the denominator. Candidate-written tests are part of the delivery but do not decide the outcome.

Time is the agent session (`task_wall_s`): model calls plus the agent's own terminal commands; preparation and external grading are excluded. Medians are descriptive; no significance tests were run. Pairwise time comparisons use only (task, repetition) pairs where both configurations were approved. Repetitions are not independent tasks. A blind diff-quality review was planned as secondary but was not performed.

## Results

### Gates

| Round | Started | Outcome | Model calls |
|---|---:|---|---:|
| `budget` | 0/6 | Preflight blocked (Docker socket permission denied in the sandbox where it was launched); no inference | 0 |
| `budget-r2` | 1/6 | First trial (Sol high) `infra_error`: the terminal plugin returned `output` without an output schema, and the CLI called `session.export` instead of `experimental.session.export`. Both fixed | 2 |
| `budget-r3` | 6/6 | 5/6 proofs passed; DeepSeek proof failed because the observer tried to close an already-cancelled stream (false `ERR_INVALID_STATE`). Observer fixed | 12 |
| `budget-r4` | 6/6 | **6/6 proofs passed, gate passed** | 12 |
| `smoke` | 6/6 | **6/6 approved** | 21 |
| cohort 2 `budget` / `smoke` | 3/3, 3/3 | 3/3 proofs passed; 3/3 approved | 6 + 12 |

### Original screening (216 trials)

All 216 sessions completed normally (status `completed`); there were no budget exceedances, non-200 responses or integration errors. 1,065 model calls.

| Configuration | Full approval | Calls | Median s (approved) | Median s (all sessions) |
|---|---:|---:|---:|---:|
| sonnet-medium | 33/36 | 139 | 16.63 | 16.92 |
| sonnet-high | 36/36 | 140 | 22.29 | 22.29 |
| sol-fast-medium | 33/36 | 148 | 29.02 | 29.26 |
| opus-medium | 33/36 | 147 | 31.35 | 31.71 |
| sol-fast-high | 33/36 | 151 | 36.47 | 37.07 |
| deepseek-max | 34/36 | 340 | 86.32 | 89.47 |
| **Total** | **202/216** | 1,065 | | |

Every configuration passed 3/3 on 11 of the 12 tasks, with one exception (DeepSeek max 2/3 on `py-atomic-import`). On `py-money-contract` the results were sonnet-high 3/3, deepseek-max 2/3, and 0/3 for the other four (5/18). Of the 13 monetary failures, 11 accepted the string `'.1'` as a valid amount, and 2 (Sonnet medium) raised `TypeError` instead of `ValueError` when `make_invoice` received `None`. Neither behaviour was explicitly forbidden by the original request ("plain decimal strings without whitespace or exponents"; no error type stated for non-list API input). The private test stops at its first failing assertion, so these are first failures, not complete defect lists.

### Monetary contract rerun (18 trials)

Only the request changed (Appendix A). 18/18 completed and fully approved, 105 model calls (the original 18 monetary trials used 109).

| Configuration | Original contract | Explicit contract | Median s | Min s | Max s | Calls |
|---|---:|---:|---:|---:|---:|---:|
| sonnet-medium | 0/3 | 3/3 | 26.65 | 26.48 | 27.37 | 12 |
| sonnet-high | 3/3 | 3/3 | 39.56 | 39.30 | 40.04 | 16 |
| sol-fast-medium | 0/3 | 3/3 | 43.26 | 42.79 | 52.73 | 13 |
| opus-medium | 0/3 | 3/3 | 54.89 | 46.28 | 57.75 | 17 |
| sol-fast-high | 0/3 | 3/3 | 66.59 | 54.24 | 73.70 | 15 |
| deepseek-max | 2/3 | 3/3 | 193.86 | 139.64 | 279.19 | 32 |

The observer logged `stream_cancelled` events on already-finished DeepSeek responses; these are not execution failures.

### Corrected screening (post hoc, 216 trials)

Replacing the 18 original monetary trials with the 18 explicit-contract trials (both raw series are kept in `data/`). This combines runs from different times; it is not a simultaneous rerun.

| Configuration | Full approval | Median s | Min s | Max s | Calls |
|---|---:|---:|---:|---:|---:|
| sonnet-medium | 36/36 | 16.92 | 9.88 | 27.37 | 139 |
| sonnet-high | 36/36 | 22.29 | 11.55 | 40.04 | 141 |
| sol-fast-medium | 36/36 | 29.26 | 17.86 | 52.73 | 147 |
| opus-medium | 36/36 | 31.71 | 16.85 | 57.75 | 150 |
| sol-fast-high | 36/36 | 37.07 | 20.42 | 73.70 | 154 |
| deepseek-max | 35/36 | 89.47 | 15.93 | 327.34 | 330 |
| **Total** | **215/216** | | | | 1,061 |

Times here are over all sessions (all completed). The one remaining failure is DeepSeek max on `py-atomic-import` (trial-0185, repetition 2): the patch accepts an extra field in the API envelope, and the private test requires rejecting it. The request explicitly forbids unknown fields in contact *rows*, but describes the envelope only as an "expected format" with malformed envelopes rejected. This is a second ambiguity, so the failure cannot be attributed unambiguously to the model. As a sensitivity analysis, excluding `py-atomic-import` for all configurations gives 33/33 for every configuration.

### Cohort 2: Sol 6.1 low Fast and GLM 5.3 Flash (108 trials)

Corrected 12-task set (11 original tasks plus `py-money-contract-v2`), three repetitions. All 108 started; 762 comparative calls plus 18 in the six gate sessions (780 total).

| Configuration | Full approval | Test-approved patch | Status | Calls | Median s (approved) | Range s (approved) | Median s (closed sessions) |
|---|---:|---:|---|---:|---:|---:|---:|
| sol-fast-low | 35/36 | 36/36 | 35 completed, 1 integration_error | 140 | 28.34 | 14.06–39.07 | 28.34 |
| glm-flash-high | 34/36 | 35/36 | 35 completed, 1 integration_error | 270 | 47.92 | 6.37–234.41 | 47.92 |
| glm-flash-max | 31/36 | 33/36 | 33 completed, 2 integration_error, 1 budget_exceeded | 352 | 194.06 | 15.10–656.13 | 232.35 |
| **Total** | **100/108** | **104/108** | | 762 | | | |

The closed-session median for GLM max covers 35 sessions; the budget-exceeded trial (1,200.21 s) is excluded. The longest closed GLM max session was 1,087.83 s.

| Task | sol-fast-low | glm-flash-high | glm-flash-max |
|---|---:|---:|---:|
| py-atomic-import | 3/3 | 3/3 | 2/3 |
| py-document-scope | 3/3 | 3/3 | 3/3 |
| py-exporter-consolidation | 3/3 | 2/3 | 3/3 |
| py-generator-cleanup | 2/3 | 3/3 | 3/3 |
| py-money-contract-v2 | 3/3 | 3/3 | 2/3 |
| py-transfer-commit | 3/3 | 3/3 | 2/3 |
| ts-archive-document | 3/3 | 3/3 | 3/3 |
| ts-cursor-orders | 3/3 | 3/3 | 3/3 |
| ts-event-stream | 3/3 | 3/3 | 2/3 |
| ts-idempotent-payment | 3/3 | 3/3 | 3/3 |
| ts-money-consolidation | 3/3 | 3/3 | 3/3 |
| ts-profile-patch | 3/3 | 2/3 | 2/3 |

The eight rejections:

| Trial | Configuration | Task | Status | Patch correct | Cause |
|---|---|---|---|---|---|
| rest/trial-0023 | sol-fast-low | py-generator-cleanup | integration_error | yes | The observer kept a fifth WebSocket call with no HTTP status and no final event; patch, session and exit were normal. Not evidence of a provider failure |
| rest/trial-0004 | glm-flash-high | ts-profile-patch | completed | no | Deduplicated tags instead of rejecting duplicates. The request speaks of "distinct tags" and a uniqueness check without stating rejection explicitly: contract ambiguity |
| rest/trial-0011 | glm-flash-high | py-exporter-consolidation | integration_error | yes | ECONNRESET transport failure |
| money/trial-0005 | glm-flash-max | py-money-contract-v2 | completed | no | Empty patch; baseline failures remain |
| rest/trial-0082 | glm-flash-max | py-transfer-commit | completed | no | Empty patch |
| rest/trial-0046 | glm-flash-max | py-atomic-import | budget_exceeded | no | Hit the 1,200 s limit with the endpoint not yet implemented |
| rest/trial-0006 | glm-flash-max | ts-profile-patch | integration_error | yes | Upstream timeout |
| rest/trial-0037 | glm-flash-max | ts-event-stream | integration_error | yes | ECONNRESET |

(`money/` = `data/results/money-sol-low-glm-flash/screening/trials/`, `rest/` = `data/results/sol-low-glm-flash-rest/trials/`.)

Paired times (same task and repetition, both approved): Sol low was faster in 28/33 pairs against GLM high (median GLM/Sol time ratio 1.78) and in 29/30 against GLM max (ratio 6.49).

### Cross-cohort summary (descriptive)

On the corrected 12-task set, eight of the nine configurations had 35/36 or 36/36 test-approved patches; GLM Flash max had 33/36. Median session time among approved trials ranged from about 17 s (Sonnet medium) to 194 s (GLM Flash max). The two cohorts were measured at different times, so cross-cohort time comparisons are confounded by provider load.

## Discussion

**The tasks did not separate the models.** After fixing one under-specified request, six configurations from four model families all reached 35/36 or 36/36, and Sol low Fast reached 36/36 test-approved patches. At this size (12–34 initial source lines, one delegated task with explicit entry points and public checks), functional pass rate is saturated. The useful signals are time, call count and operational reliability: Sonnet medium had the lowest median session time in the first cohort, Sol low Fast in the second; DeepSeek max and GLM max used two to three times as many calls and were several times slower.

**Higher effort did not help here.** Sonnet high and Sol high matched their medium variants on approvals but took longer (Sonnet 22.3 s vs 16.9 s; Sol 37.1 s vs 29.3 s median). GLM max was worse than GLM high on both approvals and time, and three of its failures were empty patches.

**Contract quality dominated the failures.** 13 of 14 original failures and the one remaining DeepSeek failure, plus one GLM high failure, sit on points the request left implicit (`'.1'`, the error type for non-list input, unknown envelope fields, duplicate tags). Tightening the request turned 5/18 into 18/18. For agent configuration this means that what is written in the delegation matters more than the choice among these models for bounded tasks of this size. The Sonnet-high 3/3 on the original contract shows that some configurations infer the stricter reading, but that is not evidence of a general instruction-following advantage.

**Operational failures need their own denominator.** In cohort 2, four of eight rejections had correct patches lost to transport (ECONNRESET, upstream timeout) or to an incomplete observer record. Recording `patch_correct` separately from `accepted` kept these from being read as capability failures, while the strict full-approval rate still counts them.

**What changed in configuration.** No configuration was promoted automatically, and no winner was declared. The results support using a fast, low-effort configuration (Sonnet medium or Sol low Fast) for bounded implementation delegations and investing in explicit acceptance criteria in the delegation prompt. They do not support high or max effort for this role.

### Limitations and threats to validity

- Small, synthetic projects; repetitions are not independent tasks; three repetitions per task. Novelty with respect to training data was not audited. Passing tests does not show the absence of bugs or security issues.
- The agent had only the isolated terminal tool, not OpenCode's normal native tools. Results do not describe the usual tool set or real production repositories.
- The contract correction is a post hoc change with no contemporaneous control of the old contract; the corrected 216-trial table mixes runs from different times.
- Identity checks verify what was sent; the answering backend behind the local proxy and the subscriptions was not attested. Whether Fast was served on the Sol route is unknown (all terminal responses said `default`).
- Provider load was not controlled or profiled; times include tool execution; no statistical tests were performed.
- The blind diff-quality review and the confirmation phase (8 unseen tasks × finalists × 5 repetitions) were planned but never run.
- Independent reviews of the harness and analyses were done by a model of the same family as one candidate (GPT); no reviewer from another family was available.
- Some gate-proof reports copied into cohort 2 (`data/results/sol-low-glm-flash-rest/gate-proofs/`) contain a cosmetic label "six configurations" although the cohort has three; counts are correct.

## Reproduction

Requirements: Docker, OpenCode 2.0.26 with working credentials for the routes above, a local OpenAI-compatible proxy on `127.0.0.1:8317` for the Claude routes, and the OpenCode model catalog at `~/.cache/opencode/models.json`. The catalog snapshot used in all runs is not redistributed (it is the OpenCode / models.dev catalog cache, about 5 MB, sha256 `f6a22feaaf4916289ead67712a27b2ba7ccdb38f6dc23ddfae11158b28a1a761`); `bench.py` checks its hash, so a different catalog changes the frozen setup.

The scripts expect to live at `implementacao/opencode-implementador/` under a parent `evals` directory and must be run from that parent. Copy `harness/` there, then (every `--out` must be a new directory):

```sh
# no model calls
python3 -B -m unittest discover -v          # from inside the harness directory
node --test test_terminal.mjs test_observer.mjs
python3 -B implementacao/opencode-implementador/bench.py validate --out implementacao/opencode-implementador/results/validate-screening

# gates and screening (model calls)
python3 -B implementacao/opencode-implementador/bench.py run --phase budget --build-image --out implementacao/opencode-implementador/results/budget
python3 -B implementacao/opencode-implementador/bench.py run --phase smoke --budget-proof implementacao/opencode-implementador/results/budget --out implementacao/opencode-implementador/results/smoke
python3 -B implementacao/opencode-implementador/bench.py run --phase screening --budget-proof implementacao/opencode-implementador/results/budget --smoke-proof implementacao/opencode-implementador/results/smoke --out implementacao/opencode-implementador/results/screening

# contract rerun and cohort 2
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py run --out implementacao/opencode-implementador/results/money-contract-v2
python3 -B implementacao/opencode-implementador/rounds/money-sol-low-glm-flash/run.py run --out implementacao/opencode-implementador/results/money-sol-low-glm-flash
python3 -B implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest/run.py run --out implementacao/opencode-implementador/results/sol-low-glm-flash-rest
```

To recompute the tables from the archived data:

```sh
python3 -I harness/analysis/summarize.py data/results/screening
python3 -I harness/analysis/summarize.py data/results/money-contract-v2
python3 -I harness/analysis/summarize.py data/results/money-sol-low-glm-flash/screening data/results/sol-low-glm-flash-rest
```

## Data

All files were copied through the repository anonymizer: local paths, user and host names are replaced with placeholders and OpenCode session IDs with salted hashes (consistent within the dataset). Text files over 1 MB are gzipped (`*.gz`), mainly large `observations.jsonl` files.

| Path | Contents |
|---|---|
| `data/results/budget`, `budget-r2`, `budget-r3`, `budget-r4` | Interruption-gate rounds (see Gates) |
| `data/results/smoke` | Smoke gate, 6 trials |
| `data/results/screening` | Original screening, 216 trials |
| `data/results/money-contract-v2` | Explicit-contract rerun, 18 trials, plus copied gate proofs |
| `data/results/money-sol-low-glm-flash/{budget,smoke,screening}` | Cohort 2 gates and the 9 corrected-monetary trials |
| `data/results/sol-low-glm-flash-rest` | Cohort 2 continuation, 99 trials |
| `data/validation/` | Offline validation of all 20 tasks, plans, preflight attempts, harness test logs, decision and work logs, and the verified analyses `money-contract-v2-analysis.json`, `sol-low-glm-flash-final-analysis.json` and `sol-low-glm-flash-final-report.md` (Portuguese) |

Each phase directory has `freeze.json` (source hashes, candidates, schedule, budget, image), `preflight.json`, `gates.json`, `validation.json`, `summary.json` and `report.md` (generated, Portuguese). Each trial directory `trials/trial-NNNN/` has:

| File | Contents |
|---|---|
| `request.txt` | The user message sent to the agent |
| `result.json` | Outcome: status, `accepted`, `patch_correct`, `session_completed`, identity, usage, requests, tiers, timing, full grade with changed files and check outputs |
| `control.json` | Controller record: limit reason, interrupt, container stop, execution time, calls at exit |
| `session.json` | Exported OpenCode session (messages, tool calls, finish reasons) |
| `run.stdout.jsonl`, `run.stderr` | OpenCode CLI event stream |
| `observations.jsonl[.gz]` | Observer record of each HTTP/WebSocket exchange |
| `terminal.jsonl` | Terminal tool invocations |
| `discovery.json`, `effective-config.json` | Native config audit and the private OpenCode config |
| `grading/` | Grader artefacts |

**Excluded:** the 16 identical copies of the OpenCode model catalog snapshot (`models.json`, sha256 above), Python bytecode caches, and the root-level Portuguese result report (its content is reproduced and checked here). No upstream repository or third-party code is part of this study. The Fast-tier source reading refers to a local CLIProxyAPI checkout at commit `633250c58de154300668f6bd87689d542dee7ae7` (project: [router-for-me/CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)); its file links in `fast-tier-source-notes.md` point to that checkout and are not redistributed.

## Appendix A: task requests (verbatim)

All requests are in English in the original. The TypeScript requests end with the standard suffix shown; the Python requests carry their check command inside the project README. The smoke request is in `harness/tasks.py`.

**`py-atomic-import`** (`data/results/screening/trials/trial-0091/request.txt`)

```text
Add import_contacts(connection, rows) in src/service.py and expose it through src/api.py.handle_import. Each row has exactly email and name strings. Trim both; email must contain exactly one @, with nonempty sides and no whitespace. Normalize email to lowercase; name must remain nonempty. Reject non-object rows, unknown or missing fields and duplicate normalized emails within a batch using ValueError. Validate the complete batch before writing. Insert new contacts and update names for existing emails, returning {'inserted': N, 'updated': N}; count an existing email as updated even when its name is unchanged. Empty batches return zero counts. Any validation or database failure must leave all contacts unchanged. The API receives {'contacts': [...]}, rejects malformed envelopes with ValueError and returns the summary. Preserve add_contact, list_contacts and the existing API. Start in src/service.py, src/repository.py and src/api.py. Connections are idle at entry.
```

**`py-document-scope`** (`data/results/screening/trials/trial-0043/request.txt`)

```text
Secure get_document(connection, tenant, owner, document_id) and list_documents in src/service.py. Only documents matching both tenant and owner and having deleted_at IS NULL are accessible. get_document returns None for any unavailable ID without distinguishing cross-tenant, cross-owner or deleted records. Lists return dictionaries ordered by id, and no deletion metadata. All queries use bound parameters, including names containing quotes. Keep result fields id, title and body unchanged. Start in src/service.py and src/repository.py.
```

**`py-exporter-consolidation`** (`data/results/screening/trials/trial-0055/request.txt`)

```text
Unify the duplicated export pipeline without changing public behavior. Keep src/csv_exporter.py.export_csv(rows) and src/json_exporter.py.export_json(rows) returning the exact same strings, including header and final newline rules. Introduce src/exporter.py.export_rows(rows, format) supporting 'csv' and 'json', and ValueError for unsupported formats. Both public wrappers must call that shared entry point; remove their duplicated row normalization and serialization loops. Normalization chooses only id and name, uses '' for missing or None values, stringifies other values, preserves order and supports one-shot iterables without mutating inputs. JSON uses ensure_ascii=False and separators=(',', ':'). CSV uses LF line endings, standard CSV quoting and an id,name header even with no rows. The existing dispatcher must keep working. Start in src/dispatcher.py and the two exporter modules.
```

**`py-generator-cleanup`** (`data/results/screening/trials/trial-0013/request.txt`)

```text
Fix stream_rows(resource, transform) in src/service.py so each started iterator closes its resource exactly once on exhaustion, explicit generator.close(), iteration errors and transformation errors. A transform failure propagates and no further row is read. Keep processing lazy, preserving order and transformed values; constructing or closing an unstarted generator performs no read or close. If cleanup also raises while an iteration or transform error is active, preserve the original error; otherwise propagate the cleanup error. src/consumer.py.take must close the iterator after taking its requested positive number of rows or if consuming fails. A limit of zero returns [] without starting the stream. Start in src/service.py and src/consumer.py. Resource.read_next() returns None at EOF.
```

**`py-money-contract`** (`data/results/screening/trials/trial-0007/request.txt`)

```text
Replace float-based parsing in src/money.py. parse_amount accepts Decimal, integers excluding bool, and plain decimal strings without whitespace or exponents, optionally signed. Reject floats, other types, non-finite numbers, zero, negatives, values over 1000000.00, and values not exactly representable in cents with ValueError. Extra trailing zeros are fine; never round a nonzero fractional cent. Return a Decimal with exponent -2. Preserve format_amount and make src/api.py.make_invoice apply the same rules. The API accepts a list of amounts and returns {'total': a two-decimal string, 'count': N}; its total must also be at most 1000000.00 and an empty list totals 0.00. Do not mutate the global decimal context or the caller's input. Start in src/money.py and src/api.py.
```

**`py-money-contract-v2`** (`data/results/money-contract-v2/trials/trial-0001/request.txt`)

```text
Replace float-based parsing in src/money.py. parse_amount accepts Decimal objects, integers excluding bool, and strings that fully match the ASCII grammar [+-]?[0-9]+(?:\.[0-9]+)?. Strings require digits before the decimal point and, if a decimal point is present, digits after it. Leading zeros and an optional sign are allowed. Reject .1, 1., whitespace, exponents, underscores, and non-ASCII digits in strings with ValueError. Decimal objects may use exponent notation.

Reject floats, other types, non-finite numbers, zero, negatives, values over 1000000.00, and values not exactly representable in cents with ValueError. Extra trailing zeros are allowed; never round a nonzero fractional cent. Return a Decimal with exponent -2. Preserve format_amount.

Make src/api.py.make_invoice accept only a Python list of amounts and apply the same validation to every item. Reject non-list inputs, including strings and None, invalid items, and totals over 1000000.00 with ValueError. Sum the amounts exactly without rounding. Return {'total': a two-decimal string, 'count': N}. An empty list returns {'total': '0.00', 'count': 0}.

Parsing and summation must remain exact even when the caller's decimal precision is too low to represent an amount or total, including a precision of 3. Do not mutate the global decimal context or the caller's input. Start in src/money.py and src/api.py.
```

**`py-transfer-commit`** (`data/results/screening/trials/trial-0019/request.txt`)

```text
Fix transfer(connection, publisher, source, target, amount) in src/service.py. A successful transfer debits and credits exactly once, appends one ledger row, commits, then publishes {'source': source, 'target': target, 'amount': amount}. source and target must differ and exist; amount is a positive integer, excluding bool, and cannot exceed the source balance. Invalid transfers raise ValueError without writes or publication. Database failure at any statement or commit rolls back all changes and never publishes. Publication failure propagates after the committed transfer and must not undo it. Caller connections are idle at entry. Keep balance reads and account setup intact. Start in src/service.py and src/repository.py.
```

**`ts-archive-document`** (`data/results/screening/trials/trial-0115/request.txt`)

```text
Add authorization to DocumentService.archive in src/service.ts. Actors have tenant,
user and role: admin, editor or viewer. Only active documents in the actor's tenant
are visible. Missing, deleted and foreign-tenant documents all throw Error('not found'),
even for admin. An admin may archive any visible document; an editor only one they own;
a viewer never may. Unauthorized visible requests throw Error('forbidden'). On success
set archived true and append exactly {actor: actor.user, document: id} to audit.
Repeating archive on an already archived visible document is a no-op, but still enforce
permission first. Failures must leave every document and audit entry unchanged.

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

**`ts-cursor-orders`** (`data/results/screening/trials/trial-0031/request.txt`)

```text
Add cursor pagination to OrderHandler.list in src/handler.ts and src/repository.ts.
Orders must be sorted ascending by createdAt, then id using lexicographic string order.
Keep the tenant filter and limit behavior for requests without a cursor. A cursor is
the literal createdAt + '|' + id of the last returned order; IDs and dates never contain '|'.
Add nextCursor: string | null to the response: null if no further matching order exists.
A cursor resumes strictly after that pair, even if its row has since been deleted.
Never repeat or skip equal-date orders. An empty tenant or cursor without exactly two
nonempty parts, or a limit that is not an integer from 1 through 100, throws Error('invalid request').
Filtering must precede pagination, including when the cursor pair belongs to another tenant.
Do not mutate the repository's input array or rows.

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

**`ts-event-stream`** (`data/results/screening/trials/trial-0133/request.txt`)

```text
Fix EventService.stream in src/service.ts so each opened lease is closed exactly once
on normal exhaustion, consumer break/return, source read failure, mapper failure or a
consumer-injected throw. Preserve the original read, mapper or injected exception if close also fails;
otherwise propagate a close failure. Do not open a lease until first iteration and do
not read ahead: one read for each next(), except the read establishing exhaustion.
stream still yields mapped records in order. Returning an unopened generator must not
open or close anything. Add relevant checks with the source interface in src/source.ts.

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

**`ts-idempotent-payment`** (`data/results/screening/trials/trial-0001/request.txt`)

```text
Fix PaymentService.pay in src/service.ts and Ledger.apply in src/ledger.ts so retries
never duplicate a debit. Idempotency is scoped by tenant and key; a repeated equal
amount returns the original receipt, including during concurrent calls. Reusing that
tenant/key with another amount throws Error('key conflict') without another debit.
Acknowledgement is external and may throw Transient after the debit committed.
Retry only Transient, up to attempts total tries, forwarding the same receipt each time.
Preserve the final thrown exception if retries are exhausted; do not retry other errors.
Validate nonempty tenant/key, positive integer cents and attempts integer 1..5 before
any ledger or transport action; invalid input throws Error('invalid payment').

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

**`ts-money-consolidation`** (`data/results/screening/trials/trial-0067/request.txt`)

```text
Consolidate the duplicated cent conversions used by invoice.ts and report.ts into
src/money.ts exporting formatAmount(cents: number): string. Both existing renderers
must import and use this shared function. Remove the old exported API names
invoiceAmount and reportAmount from all src/ code, migrating all callers in one change;
the old modules may be deleted or left empty. Preserve renderInvoice and renderReport
interfaces and exact existing output for positive, zero and negative integer cents.
formatAmount returns sign plus absolute whole currency units and exactly two fraction
digits, with no currency symbol. Do not change rounding or report line order.

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

**`ts-profile-patch`** (`data/results/screening/trials/trial-0037/request.txt`)

```text
Implement the PATCH contract in src/parser.ts and src/service.ts. Input is an unknown
plain object with only displayName and tags keys, with Object.prototype or null as its
prototype. Arrays, null and nonobjects are invalid.
Absent fields retain the stored value. displayName null clears it; a string is trimmed
and must have length 1..40 after trimming. tags null or [] clears tags; otherwise tags
is an array of at most five distinct nonempty strings, trimmed before uniqueness checks.
Every tag may have at most 12 characters after trimming. Do not coerce numeric values.
Any invalid field or unknown key throws Error('invalid profile') and leaves storage unchanged.
An empty object is a valid no-op. Return the resulting profile without changing the input
object or reusing the caller's tags array for storage. Begin with ProfileService.patch.

You may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.
```

