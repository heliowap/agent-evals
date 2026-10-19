# Read-only code exploration in OpenCode: eleven model, effort and route configurations

- **Run dates:** 2026-10-10 (smokes, 210-trial pilot, 120-trial second round)
- **Harness:** OpenCode 2.0.26, single `navigator` agent, Python 3 runner (`harness/bench.py`)
- **Models (as requested):** GPT-6.1 Sol (Fast mode selected), DeepSeek V4.1 Flash, Claude Sonnet 5.5, Claude Opus 5.5, Gemini 3.8 Flash

## Abstract

We compared configurations (model, reasoning effort and route) in a read-only code-exploration role. The agent had to answer a question about a synthetic 23-file Python service and return strict JSON with verbatim line citations. In the first pilot, 7 configurations ran 6 cases with 5 repetitions each, for 210 trials and no missing trials or transport errors. Sonnet 5.5 medium, Opus 5.5 low and Opus 5.5 medium tied at 27/30 full passes. Sonnet medium had the lowest median task time (9.84 s against 11.89 s for Opus low). Sol low with Fast selected got all 30/30 literal answers right but only 14/30 full passes, because its citations were invalid or incomplete. A second, separate round of 120 trials tested 4 more configurations: Sonnet xhigh scored 24/30 and Sol medium 17/30. Gemini 3.8 Flash medium scored 23/30 and high 12/30. All 17 task errors in that round were HTTP 400 responses on Gemini, and every one came at the 25-step limit. They are most likely an incompatibility in how the agent loop ends, not a capability result. The operational choice that came out of the study was Sonnet medium, with Opus low as the closest alternative. It is provisional and holds only for this narrow contract.

## 1. Introduction

The user's agent setup hands codebase questions to a dedicated explorer agent: "where is X handled, which function owns Y, does route Z exist". A good explorer must find the active code path, tell it apart from legacy look-alikes, and return evidence the caller can check. Explorers run often, so latency matters as much as accuracy. This study asks which model, effort and route combination available to the user (OAuth subscription, OpenCode Go subscription, or a local OpenAI-compatible proxy) best fits that role. The role is measured under a strict, machine-gradable contract.

## 2. Hypotheses

The hypotheses were not pre-registered. They are reconstructed from the design documents (`data/validation/matrix-design.md`, `data/validation/r2-design.md`) and from the harness defaults:

- **H1.** Higher reasoning effort within a model family raises the full-pass rate (Sonnet low < medium < high < xhigh; Opus low < medium).
- **H2.** Selecting Fast mode for Sol (`service_tier=priority`) gives a time advantage, and the provider confirms it in its terminal metadata.
- **H3.** Configurations differ more in evidence quality (exact citations) than in literal answer correctness. This is why the scorer records `answer_correct` and `evidence_correct` separately.
- **H4** (second round). Gemini 3.8 Flash on the local proxy's Chat Completions route is a viable, cheaper explorer.

## 3. Methodology

### 3.1 Harness and isolation

Each trial runs one `opencode run` session with one user message and at most 25 agent steps. Each session gets a private project copy, discovery home, XDG directories and session database. All configurations use the same agent (`navigator`), system prompt and limits. Permissions allow only `read`, `glob`, `grep` and `list`. Shell, edit, web, skills and subagents are denied. Ancestor config discovery is disabled. The only non-builtin plugin is `harness/observer.js`, a passive HTTP and WebSocket hook. It records the URL without the query string, the sent model, effort, Fast tier, usage, status and timings. It does not alter requests and does not record headers, prompts or tokens. This isolation is a discovery and permissions boundary, not an OS sandbox.

Per-task timeout was 300 s and the round budget was 21,600 s. The runner never retries an inference. Provider errors, wrong answers and timeouts are recorded, and the round moves on to the next trial.

System prompt of the `navigator` agent (verbatim, English):

> You explore source code and return evidence for the requested question. Read relevant files, follow the active call paths, and distinguish active code from unused code. Do not modify files. Return only the requested JSON object.

### 3.2 Configurations

| Round | Config ID | OpenCode selection | Effort | Route |
|---|---|---|---|---|
| Pilot | `sol-fast-low` | `openai/gpt-6.1-sol-fast#low` | low, Fast selected | Native OpenCode OAuth (ChatGPT backend), WebSocket. Wire model `gpt-6.1-sol` |
| Pilot | `deepseek-max` | `opencode-go/deepseek-v4.1-flash#max` | max | OpenCode Go subscription, Chat Completions |
| Pilot | `sonnet-low` / `-medium` / `-high` | `cli_proxy/cpa-claude-sonnet-5-5#<effort>` | low / medium / high | Local OpenAI-compatible proxy, Anthropic Messages protocol, adaptive thinking + `output_config.effort` |
| Pilot | `opus-low` / `-medium` | `cli_proxy/cpa-claude-opus-5-5#<effort>` | low / medium | Same proxy route as Sonnet |
| Round 2 | `sonnet-xhigh` | `cli_proxy/cpa-claude-sonnet-5-5#xhigh` | xhigh | Same proxy route as Sonnet |
| Round 2 | `sol-fast-medium` | `openai/gpt-6.1-sol-fast#medium` | medium, Fast selected | Native OAuth, WebSocket |
| Round 2 | `gemini-medium` / `-high` | `cli_proxy_google/gemini-3.8-flash#<effort>` | medium / high | Same local proxy, Chat Completions protocol, `reasoning_effort` |

Model verification: the runner's preflight checked the model and variant resolved by the OpenCode binary. The observer then confirmed the sent model, effort and endpoint on every call. This shows what was sent to each endpoint. It does not show which model the proxy or provider actually ran upstream. Gemini responses reported `gemini-3.8-flash-n` while the requests named `gemini-3.8-flash`, and this discrepancy was not resolved.

### 3.3 Cases

All six cases use the same synthetic Python service: 23 files, generated by `harness/cases.py`, with legacy modules and look-alike functions as plausible decoys. No third-party repository is involved. Each prompt names the active dispatcher to bound the task.

| Case | Required output |
|---|---|
| `route` | Call chain from the POST /orders handler to the method that invokes the DB transport, plus the active registration module |
| `config` | `load_config` precedence and resolved values, preserving an empty env var |
| `retry` | Owner of the retry loop, max attempts, retried exceptions, whether ValueError is retried, whether the event is published inside the loop |
| `permission` | IDs returned for a given principal and rows, plus the authorization and deleted-row filter functions |
| `feature` | Renderer chosen when a tenant flag is off but the global flag and the env var are on |
| `absence` | Whether DELETE /orders/bulk is registered and the dispatcher's response for it (it exists only in legacy code) |

The prompts were run in English and are reproduced verbatim. Every prompt starts with:

> Inspect this Python service in read-only mode. Do not modify files. The active HTTP entry point is service.routes.dispatch.

and ends with the shared output contract:

> Return one JSON object, with no Markdown fences or prose outside it. Use {"answer": ..., "evidence": [{"path": ..., "symbol": ..., "line": ..., "quote": ...}]}. The answer object must have exactly these fields, whose descriptions follow.
> *(case-specific field schema)*
> Provide at most eight evidence entries. Each path must be relative to this directory. Use the local function name, Class.method, or top-level assignment name for symbol. Use a one-based line number and copy the entire source line exactly, including indentation. Cite the specific statements supporting every answer field. For absence of a route, cite the active registration table and missing-route branch.

Case-specific question and answer schema:

- **route:** "Trace the active POST /orders request from its registered handler through the application method that invokes the external database transport. Include only application functions or methods on this database path, in order, starting at the handler and ending at the method that invokes the transport. Use fully qualified names. Identify the active registration module. Ignore imported modules that are never used by this route." Schema: `{"chain": "ordered list of fully qualified function or method names", "registration": "relative path to active route registration"}`
- **config:** "Explain load_config precedence. Resolve its result for environment={"APP_ENDPOINT": ""}, tenant={"endpoint": "https://tenant.local", "timeout": 7}, file_config={"endpoint": "https://file.local", "timeout": 15}. Report endpoint, timeout, and the source precedence from strongest to weakest. Preserve empty values exactly." Schema: `{"endpoint": "string", "timeout": "integer", "precedence": "ordered list using environment, tenant, file, default"}`
- **retry:** "For active POST /orders, identify the function owning retries, the maximum number of transport attempts, and the exception types it retries. Say whether ValueError is retried and whether publishing order.created happens inside that retry loop. Do not include retries from unrelated or legacy code." Schema: `{"owner": "fully qualified method name", "max_attempts": "integer", "retryable": "alphabetically sorted list of exception class names", "value_error_retried": "boolean", "event_inside_retry": "boolean"}`
- **permission:** "Which IDs does active GET /orders return in input order for principal={"id":"u1","tenant":"north","role":"member"} and repository rows=[{"id":"o1","tenant":"north","owner":"u1","status":"draft"},{"id":"o2","tenant":"north","owner":"u2","status":"draft"},{"id":"o3","tenant":"north","owner":"u2","status":"published"},{"id":"o4","tenant":"south","owner":"u1","status":"published"},{"id":"o5","tenant":"north","owner":"u1","status":"deleted"}]? Identify the authorization function and the function that excludes deleted rows." Schema: `{"ids": "ordered list of order IDs", "authorization": "fully qualified function", "deleted_filter": "fully qualified function"}`
- **feature:** "For active GET /exports, context has tenant_flags={"stream_exports":false}, global_flags={"stream_exports":true}, environment={"EXPORT_STREAMING":"1"}. Which renderer is used? Report the flag name, the effective flag value, its winning source, and whether EXPORT_STREAMING affects this active route. Trace the active route rather than the old export module." Schema: `{"renderer": "fully qualified function", "flag": "string", "effective_value": "boolean", "winning_source": "tenant or global", "environment_affects_route": "boolean"}`
- **absence:** "Does the active HTTP dispatcher expose DELETE /orders/bulk? Return whether it is registered and the dispatcher response when method="DELETE", path="/orders/bulk", request={}, context={}. There are functions and old route declarations with similar names. Base the answer on active registration and missing-route behavior." Schema: `{"registered": "boolean", "status": "integer", "body": "string", "registration": "relative path to active route registration"}`

Each trial's exact prompt is archived as `data/results/<round>/trial-NNNN/prompt.txt`.

### 3.4 Scoring

The scorer (`grade` in `harness/cases.py`) is deterministic. A trial gets a **full pass** only if all of the following hold:

1. strict JSON parse (Markdown fences or trailing prose fail);
2. exact shape;
3. the workspace is unchanged;
4. every citation is valid: the path exists, the line is inside the named symbol, and the quote matches the source line byte for byte;
5. the required anchor lines for every answer field are present;
6. the answer object matches the reference exactly.

`answer_correct` (literal answer only) and `evidence_correct` are recorded separately. Reference solutions and execution proofs of the fixture live in `harness/test_cases.py`, outside the project visible to the agent. When JSON parsing fails, every later check is reported as `false` by construction. `workspace_unchanged=false` in those rows is therefore not a real modification: the separate `fixture_unchanged` field is `true` in all 340 completed trials of both rounds.

### 3.5 Schedule and statistics

Each block contains one case and one repetition, with every configuration of the round in it. Seed `20261010` shuffles the blocks, and rotations balance positions: in the pilot each configuration held each position 4 or 5 times, in round 2 7 or 8 times. Sessions ran one at a time. Time is the wall time of the `opencode run` process, including boot, tools and internal recoveries. It excludes preparation, export and grading. Medians include completed but failing answers and exclude task errors. Paired comparisons use only (case, repetition) pairs in which both configurations fully passed. The reported A/B value is the median of per-pair ratios. All statistics are descriptive, and no significance tests were run. The two rounds do not share blocks, so comparisons across rounds are not paired.

## 4. Results

### 4.1 Pilot: 7 configurations, 210 trials (2026-10-10)

210/210 trials completed, with no timeouts, transport errors or missing trials. The observer verified the parameters of 949 model calls.

| Configuration | Full pass | Literal answer correct | Median task time | Range |
|---|---:|---:|---:|---:|
| Sonnet medium | 27/30 | 29/30 | 9.84 s | 8.19 to 19.46 s |
| Opus low | 27/30 | 30/30 | 11.89 s | 6.73 to 18.32 s |
| Opus medium | 27/30 | 30/30 | 14.02 s | 9.02 to 22.77 s |
| Sonnet low | 25/30 | 28/30 | 10.69 s | 6.53 to 17.03 s |
| DeepSeek max | 25/30 | 29/30 | 31.93 s | 16.86 to 67.98 s |
| Sonnet high | 22/30 | 27/30 | 11.08 s | 9.11 to 15.47 s |
| Sol low, Fast selected | 14/30 | 30/30 | 15.42 s | 6.16 to 25.80 s |

Full pass by case (k/5):

| Configuration | route | config | retry | permission | feature | absence |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet medium | 5 | 4 | 5 | 5 | 3 | 5 |
| Opus low | 5 | 2 | 5 | 5 | 5 | 5 |
| Opus medium | 5 | 2 | 5 | 5 | 5 | 5 |
| Sonnet low | 3 | 5 | 5 | 5 | 2 | 5 |
| DeepSeek max | 5 | 5 | 5 | 4 | 1 | 5 |
| Sonnet high | 5 | 4 | 2 | 5 | 1 | 5 |
| Sol low, Fast | 3 | 2 | 2 | 1 | 1 | 5 |

There were 43 failures in total:

- 36 had a correct literal answer and failed on evidence alone: invalid citations or missing anchors.
- 3 failed strict JSON parsing: one DeepSeek answer in a Markdown fence, one invalid JSON from Sonnet low, and trailing prose after the object from Sonnet medium.
- 3 were Sonnet high `retry` answers that gave `DatabaseClient.execute` without the required `service.client.` prefix.
- 1 was a Sonnet low `route` answer with an incomplete call chain, which also had incomplete evidence.

All 16 Sol failures were evidence failures.

Selected paired comparisons (both configurations fully passed in the same case and repetition):

| A | B | Pairs | Median A/B | A faster | B faster |
|---|---|---:|---:|---:|---:|
| Sol low, Fast | Sonnet medium | 13 | 1.427 | 3 | 10 |
| DeepSeek max | Sonnet medium | 24 | 3.015 | 0 | 24 |
| Sonnet low | Sonnet medium | 22 | 1.042 | 10 | 12 |
| Sonnet medium | Opus low | 24 | 0.838 | 14 | 10 |
| Sonnet medium | Opus medium | 25 | 0.758 | 23 | 2 |

Median model calls per trial: 4 for every Sonnet and Opus configuration, 5 for Sol and 7.5 for DeepSeek. Provider call time made up most of the task time: the median share was 74.7% for Sol and 97.7% for DeepSeek.

### 4.2 Round 2: 4 configurations, 120 trials (2026-10-10)

All 120 trials ended: 103 completed answers (27 of them failing) and 17 task errors, all on Gemini. No trial was missing. The observer recorded 1,365 model calls: 1,348 returned status 200 and 17 returned HTTP 400.

| Configuration | Full pass (of 30 attempts) | Literal answer correct (of completed) | Task errors | Median of completed | Range |
|---|---:|---:|---:|---:|---:|
| Sonnet xhigh | 24/30 | 28/30 | 0 | 15.82 s | 11.48 to 22.19 s |
| Sol medium, Fast selected | 17/30 | 30/30 | 0 | 17.23 s | 8.57 to 22.55 s |
| Gemini medium | 23/30 | 26/26 | 4 | 75.48 s | 39.14 to 120.18 s |
| Gemini high | 12/30 | 17/17 | 13 | 108.86 s | 75.59 to 158.86 s |

| Case | Sonnet xhigh | Sol medium | Gemini medium | Gemini high |
|---|---:|---:|---:|---:|
| route | 5/5 | 5/5 | 5/5 | 1/5 (4 errors) |
| config | 5/5 | 1/5 | 5/5 | 5/5 |
| retry | 3/5 | 2/5 | 3/5 (2 errors) | 0/5 (5 errors) |
| permission | 5/5 | 1/5 | 3/5 (2 errors) | 1/5 (4 errors) |
| feature | 1/5 | 3/5 | 5/5 | 5/5 |
| absence | 5/5 | 5/5 | 2/5 | 0/5 |

Failure breakdown:

- **Sol medium:** 13, all evidence failures (6 invalid citations, 7 missing anchors).
- **Sonnet xhigh:** 4 missing anchors in `feature`, plus 2 `retry` answers with the same missing `service.client.` prefix.
- **Gemini:** every failure among its completed answers was missing anchors in `absence` (3 on medium, 5 on high). Every completed Gemini answer had a correct literal answer, and no completed answer in the round failed JSON parsing.

**The 17 Gemini errors.** 4 medium and 13 high sessions completed 24 steps with HTTP 200 and got HTTP 400 on call 25 with `Requests ending with a model turn are not supported.` In OpenCode's session runner (`packages/core/src/session/runner/llm.ts`), reaching the step limit appends an assistant message (`MAX_STEPS_PROMPT`) and disables tools. That would produce a request ending in a model turn. The causal link is an inference from the code and from the fact that all 17 errors fell exactly at the limit. The observer does not capture request bodies. Even in completed trials Gemini used many more calls: the median was 13 for medium and 17 for high, against 4 for Sonnet and 5 for Sol.

The observer also flagged a generic stream error on 743 Gemini calls that returned HTTP 200 (311 medium, 432 high). These flags are separate from the 17 fatal errors. The frozen observer marks stream cancellation as an error, so expected cancellations cannot be told apart from real faults. These flags are not failed tasks.

Paired comparisons:

- Sonnet xhigh and Sol medium had 15 jointly passed pairs. Sol was faster in 10 of them, and the median Sonnet/Sol ratio was 1.100.
- Gemini medium was faster than Gemini high in all 11 joint pairs (median ratio 0.697).
- Sonnet was faster than Gemini medium in all 19 joint pairs (median ratio 0.226).

### 4.3 Fast mode (H2)

Every Sol call sent effort and `service_tier=priority` as requested: 136 calls in the pilot and 141 in round 2. Every terminal `response.completed` event reported tier `default`, so Fast service was confirmed in 0/30 trials in the pilot and 0/30 in round 2.

### 4.4 Smokes

- **Historical smoke** (`data/results/smoke`): 2 configurations, Sol via the proxy and DeepSeek, on `route`. Both passed.
- **Pilot smoke** (`data/results/smoke-oauth-matrix`): 7 configurations on `route`, 6/7 full passes. DeepSeek max had a correct answer but failed on evidence.

Neither smoke enters the tables above.

## 5. Discussion

- **H1 (effort helps): not supported.** Opus medium did not beat Opus low (27/30 each). Sonnet high (22/30) scored below Sonnet medium (27/30), and Sonnet xhigh scored 24/30 in a separate round. Most of these differences come from a few cases: Sonnet high's `retry` naming slip and its `feature` evidence. With 6 distinct tasks, the data cannot show that high effort hurts. They only show that it did not help here.
- **H2 (Fast): not testable.** The provider never confirmed Fast service, so the Sol rows measure "Fast selected", not Fast.
- **H3 (evidence dominates): supported.** 36 of the 43 pilot failures and 25 of the 27 completed-answer failures in round 2 had a correct literal answer. Sol is the extreme case: 60/60 literal answers right across both rounds, but only 31/60 full passes. Whether citation exactness matters depends on how the caller uses the explorer's output.
- **H4 (Gemini viable): inconclusive.** The step-limit incompatibility, the unverified `-n` model identifier and the stream-error flags all have to be resolved before Gemini's numbers can be read as capability. Even its successful runs were 5 to 7 times slower than Sonnet.

**Configuration outcome.** Sonnet 5.5 medium was adopted as the provisional explorer default for this contract, with Opus 5.5 low as the closest alternative. Opus low had 30/30 literal answers and the same 27/30 full passes. Round 2 gave no reason to replace this choice.

**Limitations.**

- There are only 6 synthetic tasks. The 5 repetitions measure run-to-run variation, not 30 independent problems.
- Model, effort and route vary together, so these results compare complete configurations.
- Upstream model identity behind the proxy is not verified.
- Remote prompt caching may persist across sessions.
- Reported session costs do not reflect subscription usage.
- Machine load was recorded only at the start (14 CPUs, load average 4.36 in the pilot and 4.77 in round 2).
- The two rounds are not paired.
- The strict JSON and citation contract penalizes formatting slips that a looser caller would accept.

## 6. Reproduction

Requirements: OpenCode 2.0.26 (upstream https://github.com/anomalyco/opencode; the binary is not redistributed, and the source commit used when reading the step-limit code was not recorded), Python 3.10+ and Node for the observer tests. Running the study also requires local credentials for the `openai` OAuth, `cli_proxy` and `opencode-go` providers, plus a local model catalog. None of these are included. The paths below assume the study files are laid out as in the original package (`harness/` as the package root and `data/results/` as `results/`).

Offline checks, with no model calls:

```sh
python3 -B -m unittest discover -s harness -v
node --test harness/test_observer.mjs
```

Freeze a plan, run preflight, then run:

```sh
python3 -B harness/bench.py plan --out harness/plans/new
python3 -B harness/bench.py run --cases route --reps 1 --out results/smoke-new
python3 -B harness/bench.py run --out results/pilot-new
python3 -B harness/bench.py run --candidates sonnet-xhigh,sol-fast-medium,gemini-medium,gemini-high --out results/r2-new
python3 -B harness/bench.py report --out results/pilot-new
```

Each run directory also archives `frozen-source/` (the exact runner sources hashed in `freeze.json`) and `verify_analysis.py`. That script re-grades every export against the reference fixture and rechecks the transport captures without calling models.

The harness README (`harness/README.md`) and report strings in `bench.py` are in Portuguese and are kept verbatim. The README is part of the protocol hash in `freeze.json`, and the report text is runner output. Sections 3 and 4 above translate their content.

## 7. Data

| Path | Contents |
|---|---|
| `harness/` | `bench.py` (CLI: plan, preflight, run, report), `runtime.py` (OpenCode isolation, configurations), `cases.py` (fixture generator, prompts, scorer), `observer.js` (passive transport hook), tests, `plans/` (frozen schedules) |
| `data/results/pilot-oauth-matrix/` | 210 trials. `freeze.json`, `preflight.json`, `machine.json`, `summary.json`, `report.md` (automatic, Portuguese), `analysis.md`/`analysis.json` (curated analysis with per-failure detail), `verify_analysis.py`, `frozen-source/` |
| `data/results/pilot-r2-xhigh-gemini/` | 120 trials, same layout |
| `data/results/smoke`, `smoke-oauth-matrix/` | Smokes (2 and 7 trials) |
| `data/results/*/trial-NNNN/` | `prompt.txt`, `answer.json.txt`, `result.json` (status, grade, timings, transport, usage), `requests.json` (observer capture), `events.jsonl`, `session.json` (OpenCode export), `tool-events.json`, configs, discovery audit, stderr |
| `data/partials/` | Progress snapshot taken during the pilot |
| `data/validation/` | Design notes (Portuguese), offline test logs, preflight attempts, verification records |

OpenCode session IDs are replaced by salted hashes. Local paths and identifiers are replaced by placeholders.
