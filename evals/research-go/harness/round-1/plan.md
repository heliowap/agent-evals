# Controlled researcher evaluation plan

## Scope and completion

72 once-only research cases: six fixed engineering-documentation tasks, two repetitions, two Go models and three efforts. Quality, qualified latency and reliability determine recommendations; price does not.

Artifacts live in this directory. Runtime workers live only in `/private/tmp/opencode/researcher-eval-20261007T021014Z`. Existing research notes, prior experiments, credentials and global configuration are read-only.

The final observable check is `python3 verify.py`, which audits saved evidence without network or inference. A successful complete comparison requires 72 truthful terminal records, blind source-based grades, reproducible analysis, cleanup evidence and `report.md`. An access-gate stop instead reports one attempt and 71 unrun cases; it is not a completed comparison. Other interruptions remain incomplete.

## Harness and controls

Use direct Go `/chat/completions` requests and one controlled `webfetch` function. Archive official API/effort contracts before freeze. Both model IDs use `low`, `high`, and `max` requests. Client-selected effort is measurable; backend honoring remains unverified. The new harness intentionally differs from the historical OpenCode CLI proof of concept.

Run one candidate at a time with fresh messages and a stable per-case session ID. Limits: eight inference requests, 400 visible words, 180-second supervisory deadline, identical `max_tokens=16384`, no sampler override, no caller retries/warmups/pilots/alternative routes. Expose tools on steps 1–7, final-answer-only step 8. Preserve interleaved reasoning and tool messages where required by the native contract.

Documentation fetch limits: 32 attempts per case, 2 MiB raw body, 256 KiB extracted text, 20-second socket timeout clipped to the remaining case deadline. Validate each redirect against frozen HTTPS host/path rules; reject credentials, private-address destinations and nonstandard ports. Authenticated model requests do not follow redirects. Tool output is a generic whole-page extraction, not a gold excerpt.

Freeze protocol, tasks/gold, sources, tools/system, runnable code, metadata and schedule before the first model request. Required-source normalized-content drift stops further cases; raw navigation-only drift is recorded. Missing usage remains unknown, not zero. Price is diagnostic telemetry only.

## Schedule and gate

Seed: `20261007021014`. Use twelve task/repetition blocks, each containing six configurations. A cyclic Latin-square-based arrangement gives each configuration each position twice. Randomize row/task assignments with the first position constrained to a real DeepSeek LOW case. All first repetitions precede second repetitions.

The first scheduled case is the only access canary and counts toward 72. A region/auth/entitlement denial stops the entire study, without confirmation, privacy changes or OpenRouter fallback. A different first-case failure also stops pending a decision. At most 576 client inference POSTs are possible; 72 cases are not 72 HTTP requests.

## Grading and analysis

Adopt the exact tasks and six factual checks plus uncertainty key in `research/tasks.md`. Checks score supported +1, contradicted -1, missing/unverifiable 0. Unsupported extras incur 0.5 each, capped at 2. Critical errors, source grounding, full URL compliance, uncertainty and instructions are separate.

A qualified response operationally completes, has all six supported and grounded checks, passes uncertainty/citation/word/language/source/tool instructions, uses at least two distinct official pages, has no critical error and no unsupported asserted extras. Task-specific discovery-chain coverage is reported separately, not hidden answer points.

Grade shuffled opaque IDs without model, effort, order, timing or usage. Preserve initial grades and blind adjudication overrides, and seal effective grades before unblinding. Disclose AI adjudication; integrity checks do not prove semantic truth.

Eligibility: at least 10/12 qualified, at least one qualification on every task, zero required contradictions and zero critical errors across attempted cases. Prefer the highest qualified count among eligible configurations. A practical speed advantage additionally requires at least 10% lower qualified median, corroborating jointly-qualified paired medians, no more than 10% worse qualified p90, paired coverage of six blocks/four tasks and preserved direction under leave-one-task-out. Otherwise report a frontier, tie or no decisive winner.

Report task-equal quality, qualified rate, completion/errors/timeouts, ordinary medians, nearest-rank p90 with denominators, jointly-qualified paired comparisons, exclusions and taskwise outcomes. Bootstrap 10,000 whole-task cluster samples using a frozen seed; six tasks remain six clusters despite two repetitions. No prior result or price enters the ranking.

## Packages and sequencing

1. Dataset/source archive, minimal runner, and saved-evidence audit/statistics can be implemented in parallel under `contracts.md` with disjoint ownership.
2. Independently review offline tests, archive, requests, safety and schedule; seal before inference.
3. Execute the immutable schedule, stop honestly on the access gate or material drift, clean up owned workers and export blinded evidence.
4. Grade two disjoint blind shards, then independently adjudicate critical/ambiguous/citation failures and qualified responses; seal grades before joining identities.
5. Reproduce analysis/report, independently review consistency, and pass the final saved-evidence audit. No extra model runs or tuning.

Planner evidence and detailed protocol were returned by session `ses_86c67193dce33814b2b6`; research sources and current limitations are retained in `research/harness.md` and `research/tasks.md`.
