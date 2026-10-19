# Saved-only independent audit / analysis

## P4 B1–B4 regression proof

`test_review_regressions.py` reads all 53 actual factual/U quotations and the
finalized whole archive without editing them. A copied dataset is audited at the
frozen stage **only inside TemporaryDirectory**. Evidence membership removes
Markdown presentation (paired emphasis/backticks, link destinations, typographic
quotes and escapes) while preserving code, globs, operators, words and negation;
it never changes source/hash/model-text bytes and never proves semantic truth.

The same tests exercise actual `runner.run_case` / `blind_export` public interfaces
with an empty key and injected offline transports/fetchers. Synthetic clocks are
rebased only in test-owned records to keep unrelated mock cases sequential; no
production POST, auth, process-control, seal or output is created. Full fetched
sources and equal/truncated candidate previews are checked against corresponding
saved fetches. `candidate_visible_path` must be explicitly linked, opaque,
case-contained, sealed, leak-free and exactly the corresponding model text after
documented private redactions. No unlinked extra grader files are admitted.

Mechanical judgments now independently read the **literal frozen webfetch
ALLOWLIST using ast.literal_eval**, not a broad dataset pattern or an imported
network module. They reconstruct all native call names/types/argument schemas,
requested-call totals (including beyond-cap/terminal calls), and every attempted
requested/final/redirect URL, including rejected attempts. Legitimate false flags
remain auditable; changing them to true is detected. Canonical URL aliases **or
identical full extracted content** are unioned into one source group; previews and
nonfetched references do not inflate source counts. No qualification/ranking rule
changes are needed because graded mechanical compliance must reproduce this proof.

Gate classification independently matches saved native status/payload: every
401/403, or other >=400 errors explicitly mentioning region/privacy/entitlement/
authentication/invalid-key/subscription limitations. It still requires one POST,
one attempted case and 71 access-gate skips. Ordinary errors cannot be relabeled
as access blocks or completed comparisons. Stage/final interruption rules remain.

Fixtures are synthetic and all intentional writes stay in their caller-owned
`TemporaryDirectory`. No candidate code, credential store, network or process
control is imported or executed. Use `PYTHONDONTWRITEBYTECODE=1` to suppress
interpreter caches; the package proof is:

```sh
python3 -m unittest discover -s tests/audit -p 'test_*.py'
```

`verify.py` exposes frozen, collected, grades (optionally shard a/b), graded and
default final audits. `analysis.py` writes saved-input analysis and inspectable
task/paired/exclusion/leave-one-task-out CSVs only when explicitly invoked.
Ordinary interruptions can pass truthful collected evidence but never final
comparison completion. A counted access block is one client POST/one attempted
case and 71 honest skipped records, not a latency winner or a graded comparison.

## Read-only expectations agreed with parent / P2

These are saved proof expectations, not instructions for this package to edit
runner, protocol, dataset or parent files. No inferred true/zero defaults stand
in for evidence. The independent auditor never imports runner or webfetch.

* Freeze covers code, tests, protocol, tasks/gold/source archives, API evidence,
  schedule and **parent-owned `preflight/workflow.json`**. Workflow has `owner`,
  `created_utc`, zero `candidate_post_starts`, `credential_provisioning:
  parent_owned`, `external_secret_paths_imported: false`, `runtime_root`, and true
  `worker_bounds_verified`, `protocol_reviewed`, `api_evidence_reviewed`.
  The experiment's schedule seed is 20261007021014; analysis seed is 20261007021015.
* Protocol's semantic sections (grading, qualification, eligibility,
  recommendation, retries, source drift, access gate, security, bootstrap) are
  validated directly. `audit_rules` may document them but arbitrary label strings
  are not the source of truth. Models and literal `reasoning_effort`,
  `thinking: {type: enabled}`, nonstreaming and the current Go endpoint are checked.
* `visible_word_rule` freezes the runner's documented rule: all assistant content
  turns; replace Markdown links/images with labels, remove bare HTTPS URLs and
  marker characters `` `*_#>|~ ``, then whitespace count. Reasoning/tool text is
  excluded, not code or pre-fetch commentary. Unknown rules fail rather than
  silently change the word denominator.
* Actual client POST starts have durable `execution/post-starts.jsonl` intents
  `{case_id, step, request_path, started_utc}` and request fields `intent_logged`,
  `client_post_starts`, `client_post_started_utc`. Match the ledger to actual POST
  timestamps, not request preparation timestamps. A prepared but untransmitted
  request has zero starts/null POST time/no response/an explicit error; ambiguous
  transmitted requests still count once. Provider-internal attempts remain unknown.
* Request/response artifacts follow their record's `request_path`/`response_path`;
  `requests/1-body.json` is accepted. Hidden bodies are identified by outbound
  JSON schema, **not a filename prefix**. Steps/cases are not assumed to equal
  HTTP POST count. History contains unchanged native assistant messages, including
  `reasoning_content`/tool calls, and actual JSON tool envelopes. Outbound histories
  must preserve saved message prefixes. Step 8 omits tools (or uses an empty array);
  absent `tool_choice` is valid when no tools are exposed. A returned forbidden
  step-8 tool call can be truthfully retained as step_limit but never executed.
* Per-request `usage` is native JSON or null; the optional explicit summary shape
  is also supported when it declares `complete` and `raw_steps`. Case summaries
  preserve all raw steps and null unknown totals. Native completion is inclusive;
  `prompt_tokens_details.cached_tokens` and DeepSeek `prompt_cache_hit_tokens` are
  aliases, not additive. Cache writes use `cache_write_tokens` or
  `cache_creation_input_tokens`. Uncached input subtracts known read **and write**
  subsets, or uses native miss counts when prompt = hit + miss. Unknown writes
  remain null even when native misses resolve uncached input. Missing native cost
  is unknown, not zero; complete means all seven token totals, excluding cost.
* Fetch success is `ok` (legacy numeric 200 is also explicit), not a case status.
  Failed/rejected/interrupted attempts retain honest nullable fields. Redirects
  may be `{from,to,status}` objects preserving status/chain, or explicit URL arrays.
  Successful chains must stay in frozen official scope. Authenticated POSTs never
  follow redirects. `frozen_source_match` accepts the runner's `{raw,text}` proof
  or an explicit text-only boolean; required normalized drift halts later cases.
  Full raw/text/model-text hashes, bytes, truncation and JSON tool text are checked.
* `terminal_cases` counts all saved terminal rows, including skips (72); attempted
  cases are counted separately. Runner skip/gate statuses are supported. A killed
  final request/fetch may retain unknown end/elapsed/response with a saved timeout
  error, rather than fabricated timing. Monotonic launch-to-drained-exit wall time
  may exceed 180 seconds during truthful timeout cleanup. It is never qualified;
  completed cases over the frozen 180-second limit also cannot qualify.
* Cleanup includes real `owned_process_check_path`, `credential_scan_path` and
  `external_state_unchanged: true`, plus zero remaining processes or true native
  owned-group absence. Process proof uses `owned_only`, `runtime_root` and either
  `remaining: []` or actual positive `owned_pgid` with `owned_group_absent`,
  `worker_awaited`, `output_drained`. Secret proof has
  `redacted_before_persistence: true`, `secret_matches: 0`, nonempty `scanned_paths`
  and `external_secret_paths_read: false`. That last field describes **worker / runner
  behavior**, not the parent's separately approved one-time read-only selected-Go-key
  provisioning. Neither this auditor nor candidates inspect auth.

## Blind evidence and seal expectations

* Private mapping: `{mapping: {blind_id: case_id}, sealed_hashes: {path: sha256}}`;
  `unblinded_utc` is added only after grade seal. Public index `cases` accepts opaque
  IDs or their `blind/cases/<opaque>/case.json` paths; shards remain 36/36 disjoint
  IDs. Public data must have no identity/order/timing/token/backend/path leaks.
* Blind rubric can replace original archive paths with opaque `source_path` fields
  or preserve original archive paths. Removing path fields must leave **all rubric
  semantics identical**. No real answer can rewrite the frozen gold.
* Blind sources are `{url, source_path, status: fetched|frozen_reference, frozen}`.
  Fetched copies must match that candidate's actual saved full or model text;
  frozen references must match frozen primary bodies. Duplicate URLs are not
  collapsed into an arbitrary last copy. Mechanical scope/tool/word booleans are
  reconstructed; distinct sources are **canonical content pages**, not HTML plus
  native Markdown counted twice. Optional counts must also reproduce.
* Optional `private/redactions.json` maps IDs to answer operation arrays, or to
  `{answer: [...], source: [...]}`. Operations have `{original,replacement,reason:
  self_identification}`; source operations can also select `source_path`. They
  must exactly reproduce exports, stay private and cannot hide arbitrary edits.
* Grades have six checks per nonempty attempted answer, statuses and semantic
  rationales, answer quotes and primary evidence quote arrays. Missing checks have
  empty answer quotes with explicit absence rationale. Empty rows have no invented
  semantic grade files. Extras/critical entries have answer_quote/rationale/evidence.
* Citation records have answer_quote/url/support/anchor_compliance/rationale/evidence.
  Check citations link to those claims. Frozen-key quotes can support an expected
  fact comparison, but an **entailing citation requires an actually fetched canonical
  page and fetched evidence**, never a gold-only bibliography. Prefer the fetched
  path for grounding when frozen/live copies share a URL. Supplied anchors must
  actually exist in fetched full bodies or corresponding frozen canonical metadata.
  Quote membership and anchor integrity do not prove semantic entailment.
* Adjudication preserves `{blind_id,initial_grade_path,rationale,effective_grade}`.
  Grade seal has `{created_utc,files,effective_grades,blind_review_paths,mapping_sha256}`.
  It hashes initial grades, overrides and disclosed blind review records before
  unblinding. `mapping_sha256` hashes canonical JSON of `{mapping,sealed_hashes}`,
  using sorted keys and separators `(',', ':')`, excluding later unblinded_utc.
* Final comparison needs reproducible analysis/results.json, report.md and a
  parent-owned saved-only final-review/index.json hash seal including freeze,
  execution index, analysis, report and grades-seal. An honest access block instead
  has analysis/block-report.json (1 attempted, 71 not_run_access_gate, null qualified
  latency, no_decisive_winner) and no fabricated grade comparison.

## Statistical definitions

Scores are reconstructed from judgments; supplied qualified flags are ignored.
All six supported/entailing checks, uncertainty, complete citation/URL/instruction
compliance, two distinct fetched official pages, no critical errors/extras and
operational success inside the wall limit are required. Price never enters any
score, qualification, eligibility, bootstrap or recommendation.

Medians are ordinary; p90 is nearest-rank ceil(.9*n); empty qualified subsets give
null. Task-equal quality is null if any of six task means is missing; unknown scores
are not fabricated zero. Scheduled rate denominators are 12/configuration;
error/timeout denominators also explicitly identify attempts. Six tasks remain
six clusters; 432 check judgments are not independent tasks. The seeded 10,000-draw
bootstrap resamples six **whole tasks**, jointly retaining both repetitions and all
configurations. Intervals are exploratory. Speed decisions need the same quality
tier, 10% qualified and jointly-qualified median advantage, p90 no more than 10%
worse, six paired blocks/four tasks and favorable leave-one-task-out direction.
Exclusions, case/task IDs, taskwise outcomes and sensitivity remain inspectable.
