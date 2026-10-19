# Offline blind grading machinery

No inference, network calls, candidate grading, installs or provider configuration occur here. The parent orchestrates fresh GPT sessions using `prompt.md` and jobs from `pack_jobs`; only artificial tests construct grades automatically. All real semantic judgments must come from those graders.

## Public interfaces

- `export(records, tasks, gold, evidence_loader, schedule, review_per_group=9)` returns a hash-sealed bundle containing blind `packets`, **private** `private_mapping`, and the planned `review_plan`. `tasks` is the contract array or ID map; `gold` is the combined task-ID map from both suites. The loader is `callable(path) -> exact UTF-8 text`, or None when all candidate-visible text is inline and reference archives are already validated by task authors.
- `select_review_ids(schedule, per_group=9)` depends exclusively on the frozen schedule. Freeze its output before execution; nine per suite/configuration means 162 planned IDs. Do not replace unrun or failed IDs. Hash IDs are deterministic under the frozen seed; mapping stays outside grader jobs.
- `pack_jobs(bundle, batch_size=4, review=False, base_grades=None)` produces fresh-session jobs, no private mapping, at most four packets each. A nonanswer is an operational-review job only. Unrun IDs have no job and remain unresolved in accounting. Graders must not receive the entire export bundle or seal, which contain the private mapping.
- `validate_grade(grade, packet)` validates exact units, independent booleans, grader provenance and candidate-visible support quotes. It returns normalized auxiliaries: missing measures become null (unknown), never invented zeros. `derive_metrics(packet, grade)` exposes correctness, supported fraction, correct-and-supported grounded coverage and frozen practical success. Nonanswers require a null grade and get zero effective coverage, not semantic zero labels.
- `seal_base(bundle, grade_map)` seals every completed answer's original. `seal_final(bundle, base_seal, review_envelopes, adjudication_envelopes=())` requires all attempted sample/critical/uncertain reviews, preserves originals and disagreements, and seals final grades before unblinding. Sampled unrun IDs remain explicitly unresolved. `validate_sealed(document)` reproduces the seal. `grading.sealing.unblind(document)` refuses unsealed input.

## Engine adapter (parent integration seam)

The engine is being authored separately; normalize its terminal records to this schema rather than treating undocumented native fields as visible evidence:

```json
{"id":"planned-trial-id","status":"completed","completed":true,
 "final_answer":"exact final answer only","wall_seconds":42.0,
 "tool_evidence":[{"name":"webfetch","status":"ok",
                   "visible_text":"exact delimited/truncated candidate-visible result"}],
 "timings":{"first_action_seconds":1.0,"first_final_answer_seconds":41.0,
            "request_seconds":30.0,"tool_seconds":12.0},
 "resources":{"model_steps":3,"tool_calls":2}}
```

Identity aliases `trial_id` or `trial.id`, status alias `terminal_status`, and timing alias `timings.wall_seconds` are accepted. Optional suite/task/configuration/repetition fields are checked against schedule. Duplicate records or schedule IDs are rejected. Completion requires the engine's normal terminal completion inside the supervisory deadline plus a nonempty final answer; known wall times above 240 seconds are rejected. Engine-certified completion can lack a timing observation, but analysis reports missing latency, never fabricates it. Failures use their real terminal status and `completed:false`; their text is diagnostic only. Missing records, `unrun`, or `stopped_unrun` are not attempts. Mark those records `attempted:false` if supplied. All other records are attempts.

Each evidence entry requires `name`, `status`, and `visible_text` or `visible_path`. A raw original archive is **not** an acceptable fallback. Optional `visible_sha256` is the SHA-256 of the exact UTF-8 visible text. Inline text is preferred if the engine stores a richer archive format. Tools are `websearch`, `webfetch`, `list`, `glob`, `grep`, `read`; only nonempty `ok`/`success` results are support eligible. All results, including errors, remain visible in the packet. Packet evidence IDs are local `e-0001`, etc.; candidate metadata/native history is omitted by allowlist. Gold evidence is in the reference-only section with `support_eligible:false`. Optional gold `archive_path` loads a frozen source and checks `quote` and supplied `sha256`/`hash`; other source quotes/hashes remain the task author's frozen validation responsibility. Source paths/URLs, quotes and line spans are retained; gold fixtures are not exported. Candidate answer/source self-identification cannot be removed without changing the exact answer/evidence; blinding excludes engine metadata, not arbitrary source prose.

Grades use the schema in `prompt.md`. Support citations are exactly `{source_id, quote}` and must cite successful exact visible text, not reference evidence. Substring validity is an integrity check, **not a semantic entailment verdict**. Essential units all pass; at least 80% of other units pass (vacuous if none); decisive unsupported claims/critical errors block success; actual successful search and fetch (web) or file read (code) are required. Supported fraction and correct-and-supported fraction are reported separately.

Review envelopes require `blind_id`, `kind`, `grade`, `rationale`, `grader`, `independent_session:true`, `session_id`, and `base_grade_hash` (canonical JSON hash of normalized original, or null for nonanswers). A review session has at most four packets. Disagreements in labels, critical/unsupported/uncertain flags or auxiliary values require separate adjudication with `blind_id`, `grade`, `rationale`, `grader`, `base_grade_hash` and `review_hash`. Rationale-only differences are preserved but do not force adjudication. Fresh-session independence is an orchestrator assertion, not something a JSON hash proves. Same-backend AI review is not human calibration. If a rubric correction affects other answers, parent must review/adjudicate every affected case consistently before sealing; the module cannot infer the semantic scope of a correction.

## CLI lifecycle

Run from the evaluation root. Commands all use `python3 -B -m grading.cli`:

1. `plan-reviews --schedule schedule.json --output grading/artifacts/planned-reviews.json` **before execution**.
2. `export --records RECORDS.json --tasks TASKS.json --gold GOLD.json --schedule schedule.json --evidence-root ARCHIVE_ROOT --output grading/artifacts/bundle.json` after execution. The CLI loader denies paths outside its explicit archive root.
3. `jobs --bundle BUNDLE --output JOBS` (send only jobs and prompt to fresh graders).
4. `import-base --bundle BUNDLE --input GRADES_ARRAY --store PRIVATE_STORE`; imports validate every item and cannot overwrite originals.
5. `seal-base --bundle BUNDLE --store PRIVATE_STORE --output BASE_SEAL`.
6. `jobs --review --base-seal BASE_SEAL --bundle BUNDLE --output REVIEW_JOBS`; orchestrate fresh reviews, then `import-review`/`import-adjudication` with the same bundle/input/store options.
7. `seal-final --bundle BUNDLE --base-seal BASE_SEAL --store PRIVATE_STORE --output FINAL_SEAL`.
8. `unblind --sealed FINAL_SEAL --output JOINED_JSON` only after sealing.

Imports/seals/jobs use exclusive atomic publication; published originals cannot be overwritten through this CLI. Base and final seals preserve hashes and separate histories. Retain the published root hash outside the artifact tree if adversarial rewriting is a concern: ordinary SHA-256 integrity manifests are not authenticated signatures or protection against someone rewriting every file and hash.

Verify: `python3 -B -m grading.verify`. Audit real artifacts: `python3 -B -m grading.audit --sealed FINAL_SEAL`. Bare `--sealed` explicitly audits artificial fixtures only; it never claims the real study was graded. Audits verify schemas, support eligibility, accounting and integrity, not semantic truth.
