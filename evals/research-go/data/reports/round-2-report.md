# Corrected Go researcher evaluation

## Outcome

**No configuration met the predeclared eligibility threshold; there is no decisive winner.**

Decision code: `no_eligible_configuration`. Price and historical cases did not enter the decision.

## Quality and qualified speed

| Configuration | Completed | Graded | Task-equal score /6 | Qualified | Required contradictions | Critical errors | Qualified median | Qualified p90 | Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| DeepSeek LOW | 12/12 | 12 | 5.58 | 5/12 | 0 | 0 | 15.19 s (n=5) | 22.90 s | no |
| DeepSeek HIGH | 12/12 | 12 | 5.58 | 3/12 | 0 | 0 | 43.52 s (n=3) | 56.28 s | no |
| DeepSeek MAX | 12/12 | 12 | 5.58 | 3/12 | 0 | 0 | 39.80 s (n=3) | 43.47 s | no |
| GLM LOW | 12/12 | 12 | 5.25 | 0/12 | 0 | 1 | — s (n=0) | — s | no |
| GLM HIGH | 12/12 | 12 | 5.71 | 0/12 | 0 | 1 | — s (n=0) | — s | no |
| GLM MAX | 8/12 | 9 | 5.12 | 0/12 | 0 | 0 | — s (n=0) | — s | no |

The score averages the six task means equally and includes the frozen unsupported-extra penalty. It is not a percentage of perfect answers. Empty responses have no fabricated semantic grade; grading denominators and per-task exclusions are retained in the analysis.

A qualified answer must complete within budget, satisfy all six facts with entailing fetched-source citations, address the uncertainty check, follow all instructions, use two distinct official pages and have no critical error or unsupported substantive extra. Failed and incomplete answers never enter qualified-success speed.

Eligibility requires at least 10/12 qualified answers, at least one on every task, zero required contradictions and zero critical errors. The quality tier is selected before the frozen 10% practical-speed, paired coverage, p90 and leave-one-task-out conditions. A descriptive frontier is not an eligible winner.

## Why the qualification rate is low

| Configuration | Graded answers | Not all six facts supported | Not all six checks grounded | Uncertainty not passed | Word cap failed | Full URL/anchor compliance failed |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek LOW | 12 | 3 | 3 | 1 | 0 | 3 |
| DeepSeek HIGH | 12 | 2 | 3 | 1 | 0 | 3 |
| DeepSeek MAX | 12 | 4 | 4 | 4 | 0 | 1 |
| GLM LOW | 12 | 6 | 10 | 5 | 8 | 6 |
| GLM HIGH | 12 | 2 | 4 | 5 | 9 | 5 |
| GLM MAX | 9 | 2 | 3 | 2 | 3 | 3 |

These counts overlap and do not sum to a unique failure count. Zero qualified responses is not zero factual accuracy. The frozen cap counts visible content across all assistant turns, not only the final answer. The literal-anchor policy conservatively rejects a text-fragment directive that does not match a stored literal anchor; this is a disclosed scoring limitation, not proof that every such link is unusable in a browser.

## Operational reliability (not a quality ranking)

| Configuration | Completed | Timeouts | Completed median | Completed p90 | Latency n |
|---|---:|---:|---:|---:|---:|
| DeepSeek LOW | 12/12 | 0 | 18.40 s | 23.43 s | 12 |
| DeepSeek HIGH | 12/12 | 0 | 29.03 s | 43.52 s | 12 |
| DeepSeek MAX | 12/12 | 0 | 44.74 s | 62.99 s | 12 |
| GLM LOW | 12/12 | 0 | 26.53 s | 48.99 s | 12 |
| GLM HIGH | 12/12 | 0 | 44.82 s | 88.06 s | 12 |
| GLM MAX | 8/12 | 4 | 105.57 s | 176.51 s | 8 |

All 72 scheduled cases were attempted once. The run logged 228 client inference POSTs and 296 documentation-fetch attempts over 63.68 minutes. Research cases are not HTTP-request counts; hidden upstream retries remain unknown.

The optional `thinking` field was omitted uniformly. All completed responses used the Go route and the frozen literal effort; no parameter rejection, model substitution, caller retry or privacy-setting change occurred. The initial GLM MAX compatibility case timed out and therefore has an incomplete gate, not a passed gate or native parameter rejection. The unchanged rule allowed later cases after that ordinary non-first timeout.

## Method and evidence

- Six engineering-documentation tasks: GitHub webhooks, fixed-version Node permissions, PostgreSQL isolation, Cloudflare D1 consistency, Docker Compose dependencies and Go toolchains.
- Two repetitions per task/configuration, twelve paired blocks, seeded order and each configuration occupying each position twice. One worker at a time.
- Same frozen tasks/gold as the authorized preceding study, with 22 freshly archived first-party bodies. Previous answers and timings were excluded.
- Identical webfetch-only tool, 400 visible-word cap, eight inference steps and 180-second supervisory wall deadline. Whole-page extraction and exact candidate-visible previews are retained.
- Two independent blind AI grading shards, then disclosed blind AI adjudication. Review receipts: `adjudication/reviews/shard-a.json`, `adjudication/reviews/shard-b.json`.
- Initial grades, overrides and review receipts sealed before unblinding. Source/citation truth remains AI judgment; saved-evidence integrity checks do not prove semantics.
- Ordinary medians and nearest-rank p90 with explicit denominators. Paired latency uses jointly qualified cases only, with exclusions retained.
- 10,000 shared whole-task bootstrap draws, six clusters retaining both repetitions and all configurations. Intervals are exploratory, not evidence for twelve independent tasks.

## Limits

This is a six-task first-party engineering-documentation suite, not a universal researcher leaderboard. Backend load, routing and prompt/source caches were not controlled; native cache/usage fields are retained, with unavailable values marked unknown. Client effort selection is verified on the wire, but backend honoring and GLM server-side reasoning retention are UNVERIFIED. The direct API harness is not comparable to the earlier CLI proof of concept. No pricing tie-breaker was used.

## Reproduce the saved-evidence audit

```sh
python3 -B "~/VSCode/Lab/evals/researcher-eval-20261007T093207Z/verify.py"
```

This command is offline: no candidate calls, credential inspection or source re-fetch. A passing final audit also requires the independent final-review seal; the command cannot legitimately pass while that review is pending.

Key files: `freeze.json`, `execution/index.json`, `analysis/results.json`, `analysis/failure-breakdown.json`, `analysis/tasks.csv`, `analysis/paired.csv`, `analysis/paired-exclusions.csv`, `analysis/leave-one-task-out.csv`, `grades-seal.json`, `final-review/index.json` and `audit.json`.
