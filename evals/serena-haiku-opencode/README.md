# Does adding Serena help Claude Haiku 5.5 explore and implement code in OpenCode? A 120-trial descriptive pilot

**Run dates:** harness preparation and four aborted attempts on 2026-10-12/13; the complete pilot (`full-5`) ran on 2026-10-13, 04:18–07:34 UTC. **Versions:** OpenCode 2.0.26; model `claude-haiku-5-5` at effort `medium` and `high` through a local OpenAI-compatible proxy (route `cli_proxy/cpa-claude-haiku-5-5#medium|#high`, Anthropic Messages wire protocol); [Serena](https://github.com/oraios/serena) at commit `8e1a255e979746597f6cc05a94022ec2d3d3a3ca` (`serena-agent 2.0.0.dev0`) with the Pyright 1.1.403 language server on Node v22.23.2; Docker sandbox image `sha256:5a3fe047f254…`.

## Abstract

We asked whether giving Claude Haiku 5.5 the Serena MCP server (symbol-level code navigation and editing through a language server), on top of OpenCode's native tools, improves quality or speed on small code-exploration and code-implementation tasks. The pilot crossed two effort levels (medium, high) with two tool conditions (native, native + Serena) over six synthetic Python cases (three exploration, three implementation) and five repetitions: 120 trials, all attempted. **Serena did not improve pass rates.** In implementation, all four configurations passed exactly the same 9/15 trials (one case was solved 5/5 everywhere, one 4/5 everywhere, one 0/5 everywhere). In exploration, Serena was neutral at medium effort (9/15 vs 9/15) and lower at high effort (7/15 vs 12/15 native). Serena was rarely used for real work: a useful Serena call happened in 12/30 exploration and 3/30 implementation trials of the Serena arm. The Serena tool definitions raised the median cached input of each trial by about 25k tokens, and median wall time was 2–5 s longer in exploration. Nine trials (7.5%) were lost to HTTP 429 rate limits from the proxy, in whole case-repetition blocks that hit both arms equally. The study was designed as descriptive, with no automatic winner, and these counts are small.

## 1. Introduction

Serena is an MCP server that gives coding agents language-server operations: symbol overviews, symbol lookup, reference search, diagnostics, and symbol-level edits. The usual pitch is that a semantic code tool helps an agent find the right code faster and edit it more precisely than text search and file reads. Small, inexpensive models are the ones that might gain most from such help, and also the ones most likely to lose from extra tool descriptions and choices in their context.

This study measures the net effect of adding Serena (its tools plus its instructions) to Claude Haiku 5.5 in OpenCode, keeping everything else fixed: model, effort, prompt, fixture, grader, code-execution sandbox and limits. It reuses exploration and implementation cases from two earlier studies in this repository ([code-exploration-haiku-5-5](../code-exploration-haiku-5-5/) and [code-implementation-opencode](../code-implementation-opencode/)), so the cases and graders had already been validated.

## 2. Hypotheses

No numeric hypotheses or decision thresholds were written down before the run. The design document states the question ("decide whether adding Serena improves Haiku's quality or time to explore and implement code in OpenCode") and a rule for interpretation: no winner is chosen when a gain falls within run-to-run variation or when the integration is not proven to work. The harness hard-codes the verdict `descriptive_pilot_no_automatic_winner`. The hypotheses below are reconstructed from that design:

- **H1 (quality).** Within each role and effort, native + Serena passes more trials than native alone.
- **H2 (time).** In pairs where both arms pass the same case and repetition, Serena reduces wall time, measured with Serena's startup and indexing included.
- **H3 (use).** When Serena is available, the model uses it for real work (more than reading its manual).

## 3. Methodology

### 3.1 Design

| Factor | Levels |
|---|---|
| Effort | `medium`, `high` |
| Tool condition | `native`; `serena` = native + Serena |
| Role and case | exploration: `route`, `config`, `feature`; implementation: `py-money-contract`, `py-document-scope`, `py-atomic-import` |
| Repetitions | 5 per case and configuration |

That gives 4 configurations × 6 cases × 5 repetitions = 120 trials, 30 per configuration (15 exploration, 15 implementation). The schedule has 30 blocks (case × repetition). Each block runs the four configurations back to back with rotated positions to spread order effects and drift. The schedule was frozen with seed 20261012 ([`data/results/full-5/freeze.json.gz`](data/results/full-5/)). Trials ran sequentially. There was no resume, overwrite, effort change or inference retry by the harness. An optional 8-trial smoke phase existed but was not run, and its results would not have gated the pilot.

### 3.2 Model and route

All trials request `claude-haiku-5-5` with adaptive thinking, a 272,000-token context and a 128,000-token output cap, through a local OpenAI-compatible proxy addressed by OpenCode as provider `cli_proxy`. A passive observer plugin recorded every request and checked the model identity, effort, route and output cap that were sent. This verifies the parameters sent, not which backend the provider actually served.

### 3.3 Tools and isolation

| Role | Native tools | Serena tools added (prefix `serena_`) |
|---|---|---|
| Exploration | `read`, `glob`, `grep` | `initial_instructions`, `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`, `search_for_pattern`, `get_diagnostics_for_file` |
| Implementation | `terminal` (commands run in a Docker container without network) | the six above plus `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol` |

- Every other tool is denied by permission rules. OpenCode's built-in `opencode.browser` and skill plugins are disabled in the private configuration.
- Each trial has its own session, `HOME`, XDG directories, OpenCode configuration, Serena configuration, metadata and a cold language-server index. The operator's plugins, instructions, skills, memories and MCP servers are excluded.
- Serena runs on the host over stdio in the trial's project, behind a bridge ([`harness/mcp_bridge.py`](harness/mcp_bridge.py)) that validates paths, fixes the tool list per role, and advertises only the MCP `tools` capability. Serena memories, onboarding, shell, REPL and project switching are unavailable. This is confinement by configuration and path checks, not OS-level isolation.
- OpenCode exposes the Serena tools directly (`codemode: false`); the `execute` wrapper is blocked.
- Before the first prompt of each Serena trial, the harness waits for the Serena catalog to be connected and exact. That wait counts toward the trial's time.

### 3.4 Prompts

All prompts were written and run in English and are reproduced verbatim.

**System prompt, exploration:**

> You explore source code and return only the requested JSON evidence. Do not modify files.

**System prompt, implementation:**

> Implement the exact request in this isolated project. Use the supplied terminal to inspect and run checks. Change only permitted source and check files. Finish with a concise description of your implementation and verification.

**Serena context and mode prompts** (delivered by Serena in the Serena arm only, as part of the treatment):

> You work on the single project supplied at startup. Use your allowed native tools and Serena tools when useful. Read initial_instructions before using Serena. Follow the task contract, including one-based evidence lines. Do not seek external files, memory, network or a different project.

> Complete the requested task autonomously. The task determines read-only exploration or source implementation. Return the exact requested output.

**Exploration task prompts.** Each starts with "Inspect this Python service in read-only mode. Do not modify files. The active HTTP entry point is service.routes.dispatch." and ends with a shared output contract (below).

- **route:** "Trace the active POST /orders request from its registered handler through the application method that invokes the external database transport. Include only application functions or methods on this database path, in order, starting at the handler and ending at the method that invokes the transport. Use fully qualified names. Identify the active registration module. Ignore imported modules that are never used by this route." Answer fields: `{"chain": "ordered list of fully qualified function or method names", "registration": "relative path to active route registration"}`.
- **config:** "Explain load_config precedence. Resolve its result for environment={"APP_ENDPOINT": ""}, tenant={"endpoint": "https://tenant.local", "timeout": 7}, file_config={"endpoint": "https://file.local", "timeout": 15}. Report endpoint, timeout, and the source precedence from strongest to weakest. Preserve empty values exactly." Answer fields: `{"endpoint": "string", "timeout": "integer", "precedence": "ordered list using environment, tenant, file, default"}`.
- **feature:** "For active GET /exports, context has tenant_flags={"stream_exports":false}, global_flags={"stream_exports":true}, environment={"EXPORT_STREAMING":"1"}. Which renderer is used? Report the flag name, the effective flag value, its winning source, and whether EXPORT_STREAMING affects this active route. Trace the active route rather than the old export module." Answer fields: `{"renderer": "fully qualified function", "flag": "string", "effective_value": "boolean", "winning_source": "tenant or global", "environment_affects_route": "boolean"}`.

Shared output contract:

> Return one JSON object, with no Markdown fences or prose outside it. Use {"answer": ..., "evidence": [{"path": ..., "symbol": ..., "line": ..., "quote": ...}]}. The answer object must have exactly these fields, whose descriptions follow.
> {…fields…}
> Provide at most eight evidence entries. Each path must be relative to this directory. Use the local function name, Class.method, or top-level assignment name for symbol. Use a one-based line number and copy the entire source line exactly, including indentation. Cite the specific statements supporting every answer field. For absence of a route, cite the active registration table and missing-route branch.

**Implementation task prompts:**

- **py-money-contract:** "Replace float-based parsing in src/money.py. parse_amount accepts Decimal, integers excluding bool, and plain decimal strings without whitespace or exponents, optionally signed. Reject floats, other types, non-finite numbers, zero, negatives, values over 1000000.00, and values not exactly representable in cents with ValueError. Extra trailing zeros are fine; never round a nonzero fractional cent. Return a Decimal with exponent -2. Preserve format_amount and make src/api.py.make_invoice apply the same rules. The API accepts a list of amounts and returns {'total': a two-decimal string, 'count': N}; its total must also be at most 1000000.00 and an empty list totals 0.00. Do not mutate the global decimal context or the caller's input. Start in src/money.py and src/api.py."
- **py-document-scope:** "Secure get_document(connection, tenant, owner, document_id) and list_documents in src/service.py. Only documents matching both tenant and owner and having deleted_at IS NULL are accessible. get_document returns None for any unavailable ID without distinguishing cross-tenant, cross-owner or deleted records. Lists return dictionaries ordered by id, and no deletion metadata. All queries use bound parameters, including names containing quotes. Keep result fields id, title and body unchanged. Start in src/service.py and src/repository.py."
- **py-atomic-import:** "Add import_contacts(connection, rows) in src/service.py and expose it through src/api.py.handle_import. Each row has exactly email and name strings. Trim both; email must contain exactly one @, with nonempty sides and no whitespace. Normalize email to lowercase; name must remain nonempty. Reject non-object rows, unknown or missing fields and duplicate normalized emails within a batch using ValueError. Validate the complete batch before writing. Insert new contacts and update names for existing emails, returning {'inserted': N, 'updated': N}; count an existing email as updated even when its name is unchanged. Empty batches return zero counts. Any validation or database failure must leave all contacts unchanged. The API receives {'contacts': [...]}, rejects malformed envelopes with ValueError and returns the summary. Preserve add_contact, list_contacts and the existing API. Start in src/service.py, src/repository.py and src/api.py. Connections are idle at entry."

Prompts are identical in both arms; the case definitions live in [`harness/vendor/exploration.py`](harness/vendor/exploration.py) and [`harness/vendor/tasks_python.py`](harness/vendor/tasks_python.py).

### 3.5 Limits

| Role | Wall-clock limit | Step / call limit |
|---|---|---|
| Exploration | 300 s | 25 steps |
| Implementation | 1,200 s | 60 calls |

Limits are identical across arms. The global admission budget was 172,800 s (48 h).

### 3.6 Scoring

- **Exploration** passes when the answer is strict JSON with the exact fields and correct values (`answer_correct`), and the evidence is valid (paths exist, lines and quotes match, one-based lines) and includes every required anchor (`evidence_correct`). The workspace must stay unchanged. Serena reports zero-based positions; the prompt asks for one-based lines in both arms.
- **Implementation** passes when the session finishes, the patch stays in scope, compiles, passes the original public regression checks, and passes a private acceptance script. The grader re-applies the patch to a clean copy in a separate Docker container; the private tests are never in the agent's project.
- **Serena use.** A Serena call is "useful" when it is anything other than `initial_instructions`. Trials without useful use stay in the Serena arm's denominator.
- **Time.** The primary time (`wall_s`) runs from before the OpenCode server starts to task exit, so it includes cold MCP and language-server startup. No indexing cost is subtracted. Preparation, export and grading are recorded separately.
- **Statistics.** Descriptive only: pass counts k/n per role × configuration, medians and ranges, and paired comparisons by role, effort, case and repetition. Paired time ratios use only pairs where both arms passed.

### 3.7 Preflight

Before any model call, the preflight ([`data/results/full-5/preflight.json`](data/results/full-5/preflight.json)) checked: local case contracts (reference answers pass, baselines fail); a real Serena stdio server with the Python language server for both roles; the Docker image; namespace isolation; the native terminal; case contracts inside Docker; and OpenCode's native tool discovery with the exact expected catalog. `full-5` passed every stage with zero inference calls.

## 4. Results

### 4.1 Execution history

The harness needed four aborted attempts before the complete run. Each attempt used a fresh output directory; none of their trials are included in the analysis.

| Attempt | Trials attempted | Stop reason |
|---|---|---|
| `full-1` | 0 | preflight blocked: native OpenCode tool surface differed from the contract (catalog, built-in browser plugin order, MCP representation) |
| `full-2` | 0 | preflight blocked: MCP server entry in the configuration used a legacy position; the exact response was not saved |
| `full-3` | 2 | trial 1 (medium, native) passed; trial 2 (medium, Serena) finished the task but was marked `infra_error` because the harness judged a tool-surface observation written 154 ms after the session's last activity, during server teardown |
| `full-4` | 2 | trial 1 passed; trial 2 stopped because the bridge forwarded Serena's `prompts`/`resources` capabilities, so OpenCode sent `prompts/list`, which the fixed protocol rejected |
| `full-5` | 120 | schedule exhausted (exit code 0) |

The fixes, with red/green test evidence, are in [`data/validation/`](data/validation/) and the decision log [`data/decisions.tsv`](data/decisions.tsv) (both in the original Portuguese). After the last fix, 51 Python and 7 Node harness tests passed.

**Correction to the earlier index.** The local index of studies described this package as "pilot prepared for 120 trials; full preflight needs Docker", which implied that no trials had run. The archived data show that `full-5` completed all 120 trials. No analysis of `full-5` was written at the time; the results below are computed from its `summary.json` and per-trial `result.json` files, and the automatic [`report.md`](data/results/full-5/report.md) agrees with them.

### 4.2 Trial outcomes in `full-5`

| Status | Trials |
|---|---|
| completed | 110 |
| `task_error` | 9 |
| `budget_exceeded` (300 s limit) | 1 |

All nine `task_error` trials are trials 0024–0032, run consecutively between 04:40 and 06:21 UTC. In each, the first model request got HTTP 429 from the proxy, the session made no progress, and the trial ran into its time limit with no task in the session. They cover two complete blocks (`config` repetition 2 and `py-atomic-import` repetition 3, all four configurations) and one trial of a third block (`feature` repetition 1, medium native). The next trial (0033) also got a 429 first, then recovered after about 14 minutes and passed (865.7 s). From 0034 on, no request failed. The one `budget_exceeded` trial (0023, high Serena, `feature`) had only HTTP 200 responses and timed out on its own.

### 4.3 Pass rates (primary)

All 120 trials are in the denominators, including the rate-limited ones.

| Role | Effort | Native | Serena |
|---|---|---|---|
| Exploration | medium | 9/15 | 9/15 |
| Exploration | high | 12/15 | 7/15 |
| Implementation | medium | 9/15 | 9/15 |
| Implementation | high | 9/15 | 9/15 |

Excluding the nine rate-limited trials (a post hoc sensitivity check) changes only the denominators: exploration medium 9/13 native vs 9/14 Serena, exploration high 12/14 vs 7/14, and implementation 9/14 in every configuration.

**By case** (passes out of 5):

| Case | medium native | medium Serena | high native | high Serena |
|---|---|---|---|---|
| route | 4 | 4 | 4 | 4 |
| config | 3 | 2 | 4 | 2 |
| feature | 2 | 3 | 4 | 1 |
| py-money-contract | 0 | 0 | 0 | 0 |
| py-document-scope | 5 | 5 | 5 | 5 |
| py-atomic-import | 4 | 4 | 4 | 4 |

The four `py-atomic-import` failures are the rate-limited block. Implementation outcomes are identical across all four configurations.

**Exploration grading components** (completed trials meeting each criterion; from `summary.json`):

| Configuration | Completed | Answer correct | Evidence valid | Anchors present | Evidence correct | Passed |
|---|---|---|---|---|---|---|
| medium native | 13 | 10 | 12 | 10 | 10 | 9 |
| medium Serena | 14 | 13 | 11 | 11 | 9 | 9 |
| high native | 14 | 13 | 13 | 12 | 12 | 12 |
| high Serena | 13 | 11 | 11 | 8 | 8 | 7 |

In the Serena arm, the typical failure was a correct answer with incomplete or invalid citations: 8 of the 11 failed completed Serena exploration trials had `answer_correct` true and `evidence_correct` false, against 2 of 6 failed completed native trials.

**Paired outcomes** (same effort, case and repetition; counts of pairs):

| Role | Effort | Both pass | Native only | Serena only | Neither |
|---|---|---|---|---|---|
| Exploration | medium | 5 | 4 | 4 | 2 |
| Exploration | high | 6 | 6 | 1 | 2 |
| Implementation | medium | 9 | 0 | 0 | 6 |
| Implementation | high | 9 | 0 | 0 | 6 |

### 4.4 Serena use

| Role | Effort | Serena-arm trials with a useful Serena call | Useful calls |
|---|---|---|---|
| Exploration | medium | 5/15 | 5 |
| Exploration | high | 7/15 | 9 |
| Implementation | medium | 1/15 | 12 |
| Implementation | high | 2/15 | 10 |

Useful calls were `find_symbol` (12), `get_symbols_overview` (12) and `replace_symbol_body` (12). `initial_instructions` was read in 56/60 Serena-arm trials; the four exceptions are rate-limited trials that never reached a tool call. The three implementation trials that used Serena were all `py-document-scope` and all passed, as did every other trial of that case. No Serena call returned an error. Median Serena catalog readiness was 0.60–0.66 s per configuration (maximum 1.90 s).

### 4.5 Time and tokens (completed trials, medians)

| Role | Configuration | n | Wall s (median, range) | Requests | Tool calls | Output tok | Reasoning tok | Cached input tok |
|---|---|---|---|---|---|---|---|---|
| Exploration | medium native | 13 | 19.31 (13.06–31.94) | 4 | 7 | 1,195 | 1,220 | 11,100 |
| Exploration | medium Serena | 14 | 21.95 (14.91–38.46) | 5 | 8 | 1,233 | 1,320 | 39,718 |
| Exploration | high native | 14 | 21.81 (15.88–41.65) | 4.5 | 9 | 1,456 | 1,970 | 15,739 |
| Exploration | high Serena | 13 | 26.31 (16.80–54.02) | 5 | 9 | 1,377 | 2,353 | 39,720 |
| Implementation | medium native | 14 | 37.83 (15.18–865.69) | 4.5 | 4 | 4,164 | 2,933 | 8,268 |
| Implementation | medium Serena | 14 | 34.97 (15.96–88.63) | 5 | 5 | 3,769 | 3,012 | 42,284 |
| Implementation | high native | 14 | 62.54 (14.96–94.57) | 7 | 6 | 5,211 | 6,267 | 38,794 |
| Implementation | high Serena | 14 | 55.90 (22.56–92.28) | 5 | 6 | 4,334 | 6,995 | 42,181 |

The 865.69 s maximum for implementation medium native is trial 0033, which spent about 14 minutes recovering from a 429.

**Paired time, both arms passed** (Serena / native wall-time ratio, from `summary.json`):

| Role | Effort | Pairs | Median ratio (range) | Serena faster | Native faster |
|---|---|---|---|---|---|
| Exploration | medium | 5 | 1.10 (0.81–1.66) | 1 | 4 |
| Exploration | high | 6 | 1.13 (0.74–1.56) | 2 | 4 |
| Implementation | medium | 9 | 1.14 (0.02–1.76) | 2 | 7 |
| Implementation | high | 9 | 1.06 (0.67–1.79) | 3 | 6 |

The 0.02 minimum is the 429-affected pair (trial 0033 vs 0034). OpenCode reported costs for the subscription route, but they do not measure the marginal price and are not analyzed.

### 4.6 Exploratory observation (post hoc)

In Serena-arm exploration trials, those that made a useful Serena call passed 3/12, and those that did not passed 13/18 (13/16 among completed trials). This is an association, not an effect of using Serena: the model may reach for Serena on runs where it is already struggling, and the counts are tiny.

## 5. Discussion

**H1 (quality) was not supported.** Implementation results did not depend on the configuration at all: every configuration solved `py-document-scope` 5/5, `py-atomic-import` 4/5 (the missing repetition was lost to rate limiting in all four), and `py-money-contract` 0/5. In exploration, Serena tied native at medium effort and trailed it at high effort (7/15 vs 12/15; 1 Serena-only pair against 6 native-only pairs). With 15 trials per cell and three distinct problems per role, the high-effort gap is suggestive, not established. Its pattern is consistent: Serena-arm failures were mostly correct answers with defective citations, which fits the zero-based positions Serena returns against the one-based lines the contract requires, even though both the prompt and the Serena context restated that rule.

**H2 (time) was not supported.** Serena was slower in most both-pass pairs (median ratio 1.06–1.14). Its startup is cheap (catalog ready in about 0.6 s), so the extra time comes from the model's work, not from Serena itself.

**H3 (use) was weakly supported at best.** The model read Serena's manual in almost every trial but used a real Serena operation in 12/30 exploration trials and only 3/30 implementation trials. For tasks this small, `grep`, `read` and the terminal were enough, and the model mostly chose them.

**Context cost.** Adding Serena raised median cached input from 8–16k to about 40k tokens per trial for medium effort and for exploration (implementation at high effort was already near 39k without Serena). The tool definitions and instructions are a fixed tax on every request, paid whether or not Serena is used.

**Practical reading.** For Haiku 5.5 in OpenCode on small, single-service Python tasks, Serena added context and time without improving outcomes, and may have hurt exploration accuracy at high effort. No configuration change was recorded in the archived material as a result of this pilot.

### Limitations and threats to validity

- **Small and narrow.** Three problems per role, five repetitions each; repetitions measure run-to-run variation, not new problems. The fixtures are small synthetic Python services where text search is already sufficient. Serena's advantages are claimed for large, unfamiliar codebases, which this pilot did not test.
- **Floor and ceiling cases.** `py-money-contract` failed in 20/20 trials and `py-document-scope` passed in 20/20, so two of three implementation cases cannot separate the arms. In `py-money-contract`, the private acceptance script rejected 12 trials because they accepted `".1"` and 8 because `make_invoice(None)` raised `TypeError` instead of `ValueError`. The prompt says "plain decimal strings" and "The API accepts a list", so both requirements are arguably underspecified. The reference solution does pass the script (verified in preflight). This case was inherited from the `money-contract-v2` round of [code-implementation-opencode](../code-implementation-opencode/).
- **Rate limiting.** Nine trials (7.5%) were lost to HTTP 429 from the proxy. Because of the block schedule, the losses fell on whole blocks or single trials and are nearly balanced between arms (5 native, 4 Serena), but they reduce power and remain in the denominators as specified.
- **Treatment is a bundle.** The Serena arm adds tools, Serena's instructions and the extra context and prompts in §3.4. The design measures the bundle, not any single component.
- **Model identity.** The observer verifies the requested model, effort and route, not the backend actually served by the provider.
- **Host-side Serena.** Serena and the language server ran on the host, confined by configuration and path validation, not by an OS namespace. The terminal and grader ran in Docker without network.
- **Time drift and load.** The run took about 3.3 hours on a shared machine (`machine.json` records load averages of 25–43 on 14 cores), which adds noise to wall times. Rotating positions within blocks spreads drift over arms.
- **Harness maturity.** The harness needed four aborted attempts and three fixes to how the tool surface is judged. `full-5` ran on the final, frozen version, but the fixes were made after seeing trials from `full-3` and `full-4` (infrastructure only; no outcome data drove them).
- **No pre-registered thresholds.** Hypotheses are reconstructed from the design (§2), and every comparison here is descriptive.

## 6. Reproduction

Requirements: OpenCode 2.0.26; a local proxy exposing `claude-haiku-5-5` as `cli_proxy/cpa-claude-haiku-5-5` with `medium` and `high` variants; Docker; Python 3.14; Node 22; a local Serena checkout at commit `8e1a255e979746597f6cc05a94022ec2d3d3a3ca`; and the Pyright 1.1.403 distribution placed in `harness/dependencies/pyright-1.1.403` (`harness/installation.py` copies it from a local `uvx` cache; prepare it with `uvx --from pyright==1.1.403 pyright --version`). The harness also expects a snapshot of OpenCode's model catalog at `harness/models.json` (a [models.dev](https://models.dev/) provider catalog, not redistributed here; pass another path with `--cache`). Agent runs are not deterministic.

The original commands ran from the parent folder of the package; from this folder the equivalent is:

```sh
python3 -B harness/bench.py plan --out /tmp/serena-plan            # frozen schedule, no inference
python3 -B harness/bench.py validate --out /tmp/serena-check       # contracts and offline tests, no inference
python3 -B harness/bench.py preflight --out /tmp/serena-preflight  # infrastructure gates, no inference
python3 -B harness/bench.py run --phase full --out /tmp/serena-full
python3 -B harness/bench.py report --out data/results/full-5       # rebuilds report.md and summary.json from an existing run
```

Each run needs a fresh output directory. Harness tests: `python3 -m pytest harness/test_bench.py` and `node harness/test_surface.mjs`. The report strings in `bench.py` were translated to English for this repository; this changes the source hashes recorded by `freeze`, but not behavior.

| Path | Contents |
|---|---|
| `harness/bench.py` | CLI: plan, validate, preflight, run, report; schedule and summary |
| `harness/runtime.py` | per-trial OpenCode and Serena configuration, discovery, capture, identity checks |
| `harness/cases.py`, `harness/domain.py` | case union and configurations |
| `harness/mcp_bridge.py` | stdio bridge that confines Serena and fixes its catalog |
| `harness/installation.py` | freezes the Serena installation, Pyright distribution and executables |
| `harness/observer.js`, `harness/surface.js` | OpenCode plugins: request observer and tool-surface recorder |
| `harness/vendor/` | frozen copies of the case definitions, graders and capture code from the two source studies (see `harness/provenance.json`) |
| `harness/test_bench.py`, `harness/test_surface.mjs`, `harness/native-catalog-fixture.json` | harness tests and a frozen regression fixture |

## 7. Data

| Path | Contents |
|---|---|
| `data/results/full-5/` | the complete pilot: `summary.json`, `report.md`, `preflight.json`, `freeze.json.gz` (frozen schedule, settings and installation hashes), `frozen-source/` (harness source as run), `discovery/`, MCP and terminal proofs, `grader-proof/`, `machine.json` |
| `data/results/full-5/trial-NNNN/` | one directory per trial: `prompt.txt`, `config.json`, `session.json` and `export.json` (OpenCode session), `events.jsonl`, `requests.json` (observed provider requests), `tool-events.json`, `mcp-status.jsonl`, `surface*.jsonl` and `discovery-*` (tool-surface observations; gzipped when over 1 MB), `mcp.jsonl` (Serena bridge log, Serena arm), `answer.txt` (final answer), `patch.json` and `grading/` (implementation only), `result.json` (status, grade, timing, usage, Serena use) |
| `data/results/full-1` … `full-4/` | aborted attempts (§4.1), kept for the record |
| `data/validation/` | design documents, reviews, red/green test logs and proofs from harness preparation and the fixes (Portuguese) |
| `data/decisions.tsv` | decision log with timestamps (Portuguese) |

**Anonymization.** Every file was copied through `tools/anonymize.py`. Session IDs are salted hashes; home paths are replaced by `~`.

**Not redistributed.** The Pyright 1.1.403 distribution (`dependencies/`, from the [pyright](https://www.npmjs.com/package/pyright) npm package); the Serena source and installation (cited by commit above); the 5 MB models.dev catalog snapshot (`models.json`, one copy per run and validation directory); the duplicated `freeze.json` and `frozen-source/` copies inside `validation/` (identical in kind to those kept in `results/`); and three validation files that inventory the operator's own files and configuration (`history-before.json`, `history-after.json`, `operator-config-before.json`).
