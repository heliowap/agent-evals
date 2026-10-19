# Claude Haiku 5.5 as a read-only code explorer: five reasoning efforts

- **Run dates:** 2026-10-12 (5-trial smoke at 00:58 UTC; full 150-trial run frozen at 13:50 UTC, audited at 19:07 UTC)
- **Harness:** OpenCode 2.0.26, single `navigator` agent, Python 3 runner (`harness/bench.py`)
- **Model (as requested):** `cli_proxy/cpa-claude-haiku-5-5#<effort>`, wire model `claude-haiku-5-5`, efforts low, medium, high, xhigh and max
- **Related study:** [code-exploration-sol-fast-vs-deepseek](../code-exploration-sol-fast-vs-deepseek/) (same cases, prompts and scorer)

## Abstract

We ran Claude Haiku 5.5 at five reasoning efforts on the same six-case code-exploration suite as the [sibling study](../code-exploration-sol-fast-vs-deepseek/). The agent answers a question about a synthetic 23-file Python service and returns strict JSON with verbatim line citations. All 150/150 trials completed, with no errors, timeouts or output-limit stops, and the parameters of all 808 model calls were verified. High and xhigh tied at 28/30 full passes. High was faster: median 22.40 s against 39.30 s, and faster in 26 of the 27 pairs where both passed. Xhigh got all 30/30 literal answers right, while high got 28/30. Low and medium each reached 20/30 full passes. Max scored 24/30 at a median of 135.46 s. Accuracy rose from low and medium up to high and xhigh, then fell at max while time grew about 3.5× over xhigh. A separate earlier smoke of 5 trials passed 3/5 and is reported apart.

## 1. Introduction

Haiku is the cheapest and fastest Claude tier the user can reach through their local proxy. If it can carry the explorer role (find the active code path, avoid legacy decoys, return checkable evidence), it is the natural default for frequent, latency-sensitive delegation. This study asks two questions. Which Haiku 5.5 effort gives the best mix of accuracy and speed on the explorer contract? And how does that compare with the Sonnet and Opus configurations measured on the same contract?

## 2. Hypotheses

The hypotheses were not pre-registered. They are reconstructed from the design notes (`harness/DESIGN.md`, `data/validation/work.md`, `harness/decisions.tsv`):

- **H1.** The full-pass rate rises with effort.
- **H2.** Task time rises with effort.
- **H3.** With the output cap raised from 32,768 to 128,000 tokens, max effort no longer hits the output limit. An earlier implementation round had shown max exhausting a 32,768 cap on reasoning, which led to empty deliveries.
- **H4.** As in the sibling study, failures are mostly about evidence rather than the literal answer.

## 3. Methodology

### 3.1 Harness

The runner is a copy of the sibling study's frozen round-2 sources. `cases.py`, `test_cases.py` and `observer.js` are byte-identical, and `harness/provenance.json` records their hashes. `runtime.py` adapts the cohort, the output cap, the capture and diagnostics (it keeps `finish`/`rawFinish` and separates a recovered intermediate output limit from a terminal one). `haiku.py` adds the historical smoke gate and integrity envelopes.

Each trial runs one `opencode run` session with one user message and at most 25 agent steps. The session has a private project, home, XDG directories and session database. Only `read`, `glob`, `grep` and `list` are allowed. Shell, web, edit, skills, MCP, LSP, formatters and subagents are disabled. This is a discovery and permissions boundary, not an OS sandbox. Controls were the same for every effort:

- 300 s per task process;
- context 272,000 tokens and output cap 128,000 tokens;
- adaptive thinking, Fast off;
- seed 20261010, 5 repetitions;
- admission budget of 86,400 s for the run, checked between trials;
- no inference retries and no automatic effort fallback.

Route: the local OpenAI-compatible proxy's Anthropic Messages endpoint. Model verification: on every observed request, the observer checked the model identity, effort, adaptive thinking and an integer `max_tokens` of 128000. This proves what was sent. It does not prove which model the proxy ran upstream.

### 3.2 Cases, prompts and scoring

The cases (`route`, `config`, `retry`, `permission`, `feature`, `absence`), the fixture, the prompts and the scorer are identical to the sibling study. See its [Methodology section](../code-exploration-sol-fast-vs-deepseek/README.md#3-methodology), which reproduces all six prompts verbatim. The prompts are in English, and each trial's prompt is archived as `data/results/full-1/trial-NNNN/prompt.txt`. The agent system prompt (verbatim, English) is:

> You explore source code and return evidence for the requested question. Read relevant files, follow the active call paths, and distinguish active code from unused code. Do not modify files. Return only the requested JSON object.

A **full pass** requires all of the following: strict JSON, the exact shape, an unchanged workspace, valid citations (the path exists, the line is inside the named symbol, and the quote matches byte for byte), all required anchor lines, and an exactly correct answer object. `answer_correct` is recorded separately. When JSON parsing fails, every later check is `false` by construction, so `workspace_unchanged=false` in those rows does not mean a modification. `fixture_unchanged` is `true` in all 150 trials.

### 3.3 Schedule and statistics

Each block contains one case and one repetition, with all five efforts in it. Rotations give each effort each position 6 times. Sessions ran one at a time. Time is the wall time of the `opencode run` process (boot, tools and internal recoveries), excluding preparation, export and grading. Medians include failing answers. Paired comparisons use (case, repetition) pairs where both efforts fully passed, and report the median of per-pair time ratios. The analysis is descriptive only, with no significance tests.

## 4. Results

### 4.1 Full run, 150 trials

150/150 completed. There were 0 task errors, 0 timeouts and 0 terminal or intermediate output-limit events. The 808 model calls were re-verified by the post-run audit (`data/validation/full-1-audit-20261012T190742Z/snapshot.json`). Summed task time was 115.3 min, or 121.7 min including per-trial preparation and teardown.

| Effort | Full pass | Literal answer correct | Median time | Range | Median calls | Calls total | Median reasoning tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| low | 20/30 | 26/30 | 13.92 s | 6.90 to 23.73 s | 4 | 116 | 1,026 |
| medium | 20/30 | 27/30 | 18.03 s | 12.19 to 24.42 s | 4 | 135 | 1,390 |
| high | 28/30 | 28/30 | 22.40 s | 14.58 to 63.18 s | 4 | 135 | 2,228 |
| xhigh | 28/30 | 30/30 | 39.30 s | 23.50 to 63.13 s | 5.5 | 174 | 5,576 |
| max | 24/30 | 30/30 | 135.46 s | 84.95 to 202.75 s | 8 | 248 | 24,029 |

Full pass by case (k/5):

| Effort | route | config | retry | permission | feature | absence |
|---|---:|---:|---:|---:|---:|---:|
| low | 4 | 1 | 5 | 4 | 1 | 5 |
| medium | 4 | 5 | 2 | 3 | 1 | 5 |
| high | 4 | 5 | 5 | 5 | 4 | 5 |
| xhigh | 5 | 5 | 4 | 5 | 4 | 5 |
| max | 3 | 4 | 5 | 5 | 2 | 5 |

Failure breakdown (computed from `result.json` grades):

| Effort | Failures | Wrong literal answer | Strict JSON failure | Correct answer, evidence failed |
|---|---:|---:|---:|---:|
| low | 10 | 4 (3 `feature`, 1 `route`) | 0 | 6 |
| medium | 10 | 1 (`route`) | 2 (`retry`, answer wrapped in a Markdown fence) | 7 |
| high | 2 | 2 (1 `route` chain type, 1 `feature` renderer), evidence valid | 0 | 0 |
| xhigh | 2 | 0 | 0 | 2 (missing anchors) |
| max | 6 | 0 | 0 | 6 (3 invalid citations + missing anchors, 2 invalid citations, 1 missing anchors) |

Paired time comparisons, pooled over cases (both efforts fully passed in the same case and repetition):

| A | B | Pairs | Median A/B | A faster | B faster |
|---|---|---:|---:|---:|---:|
| low | medium | 14 | 0.803 | 12 | 2 |
| medium | high | 19 | 0.807 | 15 | 4 |
| high | xhigh | 27 | 0.591 | 26 | 1 |
| xhigh | max | 22 | 0.312 | 22 | 0 |
| high | max | 22 | 0.174 | 22 | 0 |

The automatic report (`data/results/full-1/report.md`) gives the same comparisons broken down by case for all 10 effort pairs. The pooled table above was recomputed from the trial data (exploratory).

### 4.2 Earlier smoke (`data/results/round-1`)

The historical wrapper (`haiku.py run`) ran 5 smokes, one per effort on `route`, behind a 5/5 gate. They passed 3/5. Medium returned `chain` as a string instead of a list, and high cited an import line under a symbol the scorer does not accept. The output cap, adaptive thinking and effort were verified on all 27 calls. Because the gate failed, the 150-trial pilot under that wrapper never started (`stop_reason: smoke_gate_failed`). The full run in 4.1 was then launched directly through `bench.py` with the same scorer and no gate. Quality failures were treated as outcomes to measure, not as reasons to stop. The smoke trials are excluded from 4.1.

## 5. Discussion

- **H1 (accuracy rises with effort): partly supported.** Low and medium (20/30) sit well below high and xhigh (28/30), but max falls back to 24/30. Max's 6 failures all had a correct literal answer and broken citations. Max read the most (median 20 tool calls against 9 for high) and still cited less precisely.
- **H2 (time rises with effort): supported.** The time ratios in the abstract and in 4.1 show it, and max costs about 3.5× xhigh in median time.
- **H3 (no output-limit stops at max): supported.** With the 128,000 cap there were no output-limit events, even at a median of 24k reasoning tokens.
- **H4 (evidence dominates): supported from medium upward.** The exception is high, whose two failures were wrong literal answers with valid evidence. Xhigh is the only effort that got every literal answer right and failed only on anchors.

**High vs xhigh.** The two efforts tie on full passes but fail in different ways. High is clearly faster (26/27 paired wins, median ratio 0.59). Xhigh is more reliable on the literal answer. For an explorer whose answers are consumed by a stronger orchestrator, high is the better trade-off on this suite. Xhigh is the safer pick when the answer itself must be right.

**Relation to the sibling study (not paired).** Haiku high and xhigh at 28/30 are numerically at or above the best Sonnet and Opus configurations of the 2026-10-10 pilot (27/30). Haiku's medians (22.4 s and 39.3 s) are about 2 to 4 times Sonnet medium's 9.84 s. The runs used different output caps (128,000 vs 32,768), different days and separate blocks, so no ranking claim follows. `data/validation/comparison-history-20261012T022728Z/comparison.json` holds a descriptive comparison of the `route` case only.

**Limitations.**

- There are only 6 synthetic tasks. The 5 repetitions are not independent problems.
- Upstream model identity behind the proxy is not verified.
- Remote prompt caching may persist.
- Reported cost of zero does not mean free usage.
- Machine load was not monitored continuously (14 CPUs, load average about 9.1 at start, higher than in the sibling runs).
- The output cap differs from the earlier rounds.
- Design reviews used only GPT-family models.

## 6. Reproduction

Requirements: OpenCode 2.0.26 (upstream https://github.com/anomalyco/opencode; the binary is not redistributed), Python 3.10+, Node for the observer test, and local credentials for the `cli_proxy` provider (not included). The frozen model catalog ships as `harness/models.json.gz`; run `gunzip` on it before use. Paths assume `harness/` as the package root and `data/results/` as `results/`.

```sh
python3 -B -m unittest discover -s harness -v      # offline: test_cases.py, test_haiku.py
node --test harness/test_observer.mjs
python3 -B harness/haiku.py validate-offline --out results/check-new
python3 -B harness/bench.py plan --cache harness/models.json --budget-seconds 86400 --out results/plan-new
python3 -B harness/bench.py run  --cache harness/models.json --budget-seconds 86400 --out results/full-new
python3 -B harness/bench.py report --out results/full-new
```

`harness/README.md`, `DESIGN.md`, `decisions.tsv` and the report strings in the scripts are in Portuguese and are kept verbatim. Their hashes are recorded in the frozen run (`freeze.json`, `provenance.json`). Sections 3 and 4 above translate the protocol.

## 7. Data

| Path | Contents |
|---|---|
| `harness/` | `bench.py` (scheduler and loop), `runtime.py` (isolation, cohort, capture), `cases.py` (fixture, prompts, scorer), `observer.js`, `haiku.py` (smoke gate wrapper), tests, `models.json.gz` (frozen catalog), `provenance.json`, `DESIGN.md`, `decisions.tsv` |
| `data/results/full-1/` | The 150-trial run: `freeze.json`, `preflight.json`, `phase.json`, `machine.json`, `summary.json`, `report.md` (automatic, Portuguese), `frozen-source/`, `models.json.gz` |
| `data/results/full-1/trial-NNNN/` | `prompt.txt`, `answer.json.txt`, `result.json` (status, grade, timings, transport, finishes, usage), `requests.json` (observer capture), `events.jsonl`, `session.json`, `export.json` (export receipt), tool events, configs, stderr |
| `data/results/round-1/` | Earlier smoke (5 trials), gate result and integrity envelopes |
| `data/validation/` | Design alternatives, reviews, offline checks, frozen plans, blocked native-run attempts (no inference) and post-run audit snapshots |

OpenCode session IDs are replaced by salted hashes. Local paths and identifiers are replaced by placeholders.
