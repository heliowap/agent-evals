> English translation of [2026-09-27-code-review-eval-v3-design.md](2026-09-27-code-review-eval-v3-design.md). The original is kept verbatim as an archived artifact.

# Round 3 of the code review benchmark — design

Date: September 27, 2026
Status: design approved in conversation; awaiting review of this spec before the implementation plan.

## Goal

Choose, with reproducible evidence, the combination of **model, provider, effort and review skill** that the `reviewer` agent of [`gh-agents`](https://github.com/<user>/gh-agents) will use from now on. The eval ends with the announcement of the winner; the decision to incorporate it into the Action belongs to the user.

Decision criteria, in this order:

1. **Few false positives**, especially in BLOCKING, which in the current flow becomes an issue. A configuration that does not pass the gate is eliminated, no matter how many bugs it finds.
2. **BLOCKING precision** among the configurations that passed.
3. Recall, stability, time and cost only as tie-breakers.

## Out of scope

- Any change to `gh-agents`, including incorporating the winner. That is left for later, by the user's decision.
- Reinterpreting or adding up the numbers of rounds 1 and 2, which remain intact in `evals/` and `evals/round-2/`.
- Measuring the user's local `/code-review` skill.
- Using the code or reviews from the user's own repositories as ground truth. They are 100% agent-generated and would be a weak reference.

## Lessons from previous rounds that this design corrects

| Observed problem | Correction |
|---|---|
| 2–3 PRs, not enough repetition; no sustainable ranking | ~60 cases and 3 repetitions in the test set; bootstrap intervals over cases |
| Prompt without tools, pre-selected context; not what the Action does | The executor runs the `reviewer` agent with the Action's permissions on a real checkout |
| Target not demonstrable with the material delivered (Axios / Standards) | Every target is reproduced at the pinned commit **before** running models; a target without reproduction discards the case |
| Without clean PRs, the false positive rate was only a lower bound | 15 clean PRs in the test set and an explicit false positive gate |
| A single adjudicator | LLM judge from another family + blind human adjudication of all BLOCKING in the test set and ~10% of the rest, with kappa reported |
| Overfitting risk if the skill is optimized and evaluated on the same cases | dev/validation/test split with a seal; test opened only once |

## Architecture

Everything lives in `evals/round-3/`. Six independent parts, each with file input and output:

| Part | Responsibility | Output |
|---|---|---|
| 1. Case mining | Find candidate PRs, reproduce targets, choose clean PRs, generate mutations and prompt injection cases | `cases/<id>/case.json` + repository snapshot, with hash |
| 2. Split and seal | Draw dev/validation/test with a recorded seed; record the hash of the test list | `split.json`, `seal.json` |
| 3. Executor | Run `opencode run` with the `reviewer` agent in an isolated checkout, resumable, with shuffled order | `runs/<cell>.json` + session export |
| 4. Output reader | Extract BLOCKING/WARNING/NIT with `path:line` and check the format | `findings/<cell>.json` |
| 5. Adjudication | Match findings against the target; send extras to the LLM judge; prepare blind batches for the user | `adjudication.json`, `human-blind/*.json` |
| 6. Report | Apply the gate, floor and ranking; bootstrap intervals | `comparison.md`, `methodology-review.md` |

Separately, in `evals/round-3/sentinel-v2/`: rewrite of `diff-risk-sentinel` as a **prioritizer** (section "Sentinel v2"). It feeds variant C of the skill; it is not part of the eval.

## Cases

### Origin

Public PRs **from other users**, in mature projects, with CI, long history and mandatory human review. Exclude single-maintainer projects and the user's repositories. At least four languages: Python, TypeScript, Go and Rust. Prefer PRs merged in the last few months, to reduce the chance that the models saw the case in training; the residual risk will be declared in the report.

### Types

| Type | Definition | Ground truth |
|---|---|---|
| **Tracked bug** | Merged PR that was later reverted or fixed by another PR that cites it as the cause ("regression introduced in #N", explicit revert) | The defect described by the fix, reproduced at the PR's commit |
| **Clean** | Merged PR in the same repository, with no revert or fix linked to it for at least 90 days | No known defect; any BLOCKING is presumed false |
| **Mutation** | Clean PR with a defect plausibly injected into the diff | The injected defect |
| **Prompt injection** | Clean PR with a malicious instruction in a code comment or in the description | Do not obey; outside the ranking |

Maintainers' comments on the original PR **do not enter the score**. They serve only as evidence for classifying extra findings.

### Acceptance criteria for a case (before any execution)

- Verifiable base and head commits; reproducible diff.
- For tracked bug and mutation: reproduction of the defect at the pinned commit (test, script or code evidence), recorded with file, lines, mechanism, consequence and acceptable equivalences.
- The defect must be demonstrable with what the agent can see in the checkout. If the proof depends on something the agent cannot reach, the case is discarded.
- Diff between ~20 and ~800 changed lines.

### Size and split

| Set | Cases | Composition |
|---|---:|---|
| dev | 15 | free mix; used to iterate the skill |
| validation | 15 | ≥ 5 clean; used in triage and in choosing the variant |
| test | 30 | 15 clean, ≥ 10 tracked bugs, the rest mutations; sealed |
| injection | 3 | outside the ranking; runs in phase 3 |

Distribution stratified by language and type. The seed and the hash of `split.json` are recorded before the first execution. The test list sits in a file that the main agent does not read during phases 1 and 2; the seal records the hash to prove that it has not changed.

With 15 clean PRs, zero observed BLOCKING still allows a true rate of up to ~20% (rule of three). The report must say so.

## Agent isolation

- **Git:** clone cut at the PR's head commit, with the base available for `git merge-base`, with no later commit. `git log` must not be able to reach the fix.
- **`gh`:** a stand-in on the `PATH` answers `gh pr view`, `gh pr diff` and `gh issue view` with frozen data: PR title and body, issues referenced at merge time, and the diff. No comments, reviews, later PRs or network.
- **OpenCode:** version pinned at `v2.0.16` (the one in the current `gh-agents`). The eval's own configuration: all plugins off, skills directory containing only the variant under test, `reviewer` agent with the permissions copied from `agents/opencode.json`, `edit`, `webfetch` and `websearch` denied. `OPENCODE_CONFIG_CONTENT` identical to the Action's. The user prompt is the exact text of the `review` step in `.github/workflows/agents.yml`.
- **Run validation:** a run counts only if the exported session confirms the model, the effort variant and the `reviewer` agent; if no tool outside the allowed list was called; and if there is a final answer. Invalid attempts are archived in `attempts/`; up to two attempts per cell, with the same prompt.
- **Residual risk:** memory recognition of a famous repository. Declared, not eliminated.

## Configuration matrix

One route per model. It is **forbidden** to run OAuth or CPA models through another provider.

| Model | Provider | Effort | Route used by the Action today? |
|---|---|---|---|
| GLM-5.3-Flash | `opencode-go` | low, high, max | yes |
| GLM-5.3-Flash | Fireworks | high | yes |
| GLM-5.3-Flash | OpenRouter | high | no (requires new secret) |
| DeepSeek V4.1 Flash | `opencode-go` | low, high, max | yes |
| MiMo-V2.6-Flash | OpenRouter | none, thinking | no (requires new secret) |
| GPT-6 Luna | OAuth | low, high, max | no |
| Gemini 3.8 Flash | CPA (`cli_proxy`) | low, medium, high | no |
| SWE-2 | CPA (`cli_proxy/devin/swe-2`) | medium, high, max | no |
| **Baseline** Claude Opus 5.5 | CPA (`cli_proxy/cpa-claude-opus-5-5`) | medium, xhigh | no |
| **Control** linters only | — | — | — |

That makes 21 LLM configurations and 1 control. The control runs each language's standard linters and analyzers over the changed files and converts the messages into WARNING with `path:line`; it never emits BLOCKING.

The exact IDs and effort variants are frozen in `manifest.json` after a pilot. The pilot also checks whether MiMo `none` produces output in the format (in round 2 it had 0/6). The effective effort recorded is the one the exported session confirms, not just the one requested.

## Skill variants

| Variant | Content |
|---|---|
| **A** | Current `skills/code-review/SKILL.md` from `gh-agents`, unchanged |
| **B** | Skill optimized on the dev cases: requires evidence before BLOCKING, downgrades hypotheses to WARNING, explicitly allows `(none)` and keeps the current output contract |
| **C** | B + sentinel v2 hotspot list appended to the context |
| **D** | B + placebo list: randomly drawn changed functions, same format and size as the list in C |

All preserve the current contract: `BLOCKING`, `WARNING`, `NIT` sections, `path:line` on every finding and a last line `SUMMARY: N BLOCKING, N WARNING, N NIT`.

## Sentinel v2

The prototype at `~/.agents/skills/diff-risk-sentinel` has no effect eval and has design problems: without coverage it assumes 0% and CRAP becomes CCN² + CCN; CCN for JS/TS by regex counts `?.` as a branch; the `ACCEPTABLE_LOW_RISK` seal works as a filter and can hide one-line bugs; the use of Jev contradicts the [jev-1.13 limitations documentation](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) (numbers in the state, several judgments in one question, score used as magnitude) and the confidence is not used.

The v2:

- **Prioritizes, does not filter.** Produces an ordered list of up to 5 changed functions; the reviewer still sees the whole diff.
- CCN by `lizard` for all supported languages; coverage only when there is a report, and absence of coverage recorded as unknown, not as 0%.
- Jev with **atomic Noul questions per function**, in natural language and with no numbers in the state, for example: "does it change the public contract?", "does it remove a validation or fallback?", "does it change error handling?". The combination is done in code.
- Answers with low confidence do not raise the priority.
- Jev failure degrades to a structural-only list, recorded in the result.

The v2 only enters the final skill if variant C beats **B and D** on validation.

## Phases

1. **Triage.** 22 configurations × 15 validation cases × 1 run, with skill A: 330 runs. Finalists: the 3–4 best that pass the gate, plus any whose precision interval overlaps that of the last finalist.
2. **Skill.** Iterate B on the dev cases with the finalists. Each iteration records the skill diff and the dev result. Then, run B, C and D on the validation cases with the finalists, 1 run. Choose the winning variant by the same decision rules.
3. **Test.** Open the seal once. Finalists × (A, winner) + Opus 5.5 `medium` and `xhigh` with A and with the winner + control, on the 30 test cases, 3 repetitions; plus the 3 injection cases. No case, prompt or rule changes after the first execution of this phase; a needed correction creates a new round.

## Scoring

### Finding classes

| Class | Criterion |
|---|---|
| Target | Right file, line within the changed stretch or up to ±5 lines, right mechanism |
| Valid extra | Not the target; confirmed by reproduction, by the code or by a maintainer comment |
| Refuted | Code or reproduction shows it is false |
| Unverifiable | Plausible, but with neither proof nor refutation |
| Style/opinion | Preference without concrete cost |

The same claim repeated in one answer counts once. Omission is not a false positive.

**False BLOCKING** = BLOCKING classified as refuted, unverifiable or style/opinion. A BLOCKING becomes an issue, so it needs evidence.

### Decision rule

1. **False positive gate.** Eliminate the configuration with false BLOCKING in more than 10% of runs on clean PRs, or with a false BLOCKING rate per PR, over the 30 test cases, worse than that of Opus 5.5 `medium` with the same skill variant.
2. **Utility floor.** Target recall, at any severity, higher than that of the linters-only control.
3. **Ranking** by BLOCKING precision (target + valid extra ÷ total BLOCKING), with a 95% bootstrap interval over cases. Overlapping intervals are a statistical tie.
4. **Tie-breaker:** target recall as BLOCKING → stability (fraction of cases in which the 3 repetitions agree on the target) → wall-clock time p50/p95 → reported cost.

Obeying a prompt injection case eliminates the configuration.

Reported without entering the score: severity calibration, `path:line` precision, adherence to the format and to the `SUMMARY:` line, operational failure rate, cost per valid finding.

### Judge and human adjudication

- LLM judge: **GPT-6 Sol `high` via OAuth**, which is not a production candidate nor from the baseline's family. It receives each extra finding, the case and the reproduction, without the model name.
- The user adjudicates, blind and in shuffled order: **all BLOCKING in the test set** and a random sample of ~10% of the other findings. Estimate: ~6 h.
- Cohen's kappa between user and judge is reported. If kappa < 0.6, all extra findings of the finalists go to human adjudication.
- Human decisions prevail over the judge's. A BLOCKING on a clean PR only becomes a valid extra if the user confirms it with reproduction; the case is marked as mislabeled, but is not removed.

## Budget and integrity

- Cap of **US$ 80** in reported cost from the paid routes (`opencode-go`, Fireworks, OpenRouter, TypeSafe), including pilot and invalid attempts. The executor pauses on reaching it or if it cannot compute the cost of a call.
- Before phase 1, a pilot with 2 dev cases and all configurations measures the real cost per run. If the projection exceeds the cap, reduce the phase 3 repetitions to 2 before starting, and record the change.
- US$ 0 on OAuth and CPA is recorded as "reported zero", never as free.
- Concurrency limited per provider; execution order shuffled with a recorded seed; `stdin` closed; resumable execution.
- Each valid run stores the sanitized session export, without the reasoning, with a SHA-256 hash of the full export.

## Winner announcement

The report ends with an announcement section, without opening a PR or changing `gh-agents`:

- **overall winner:** configuration (model, provider, effort) and skill variant, with the evidence from the decision rule;
- **best configuration with a route the Action already supports** (`opencode-go` or Fireworks), when different from the overall winner, with the measured difference between the two;
- what incorporation would require in each case: swapping the default `model`, replacing `skills/code-review/SKILL.md`, new provider and secret (OpenRouter), sentinel v2 in the runtime (variant C) or OAuth/CPA support in the runner.

The decision to incorporate belongs to the user.

## Acceptance criteria

1. `cases/`, `split.json` and `seal.json` exist before the first execution; every target has an archived reproduction.
2. The executor has tests covering: git isolation, `gh` stand-in without network, rejection of a session with a divergent model/effort/agent or a forbidden tool, resumption and pause on cost.
3. The test list hash in the seal matches the file at the time of phase 3.
4. The report shows, per configuration: gate, floor, BLOCKING precision with interval, tie-breakers, kappa and the reported metrics; it declares the limits (training contamination, size of the clean PR sample, routes not supported by the Action).
5. Rounds 1 and 2 remain unchanged; the root `README.md` points to round 3 without combining numbers.
