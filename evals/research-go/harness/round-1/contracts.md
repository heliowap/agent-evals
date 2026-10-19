# Package interfaces and ownership

All JSON is UTF-8. Paths in artifacts are relative to the artifact root unless explicitly marked runtime paths. Implementers may add documented fields, but must preserve the following keys and meanings. No candidate request occurs before the freeze review.

## Ownership

- Dataset package: `dataset.py`, `dataset/**`, `tests/dataset/**`.
- Runner package: `runner.py`, `webfetch.py`, `protocol.json`, `system.txt`, `tools.json`, `schedule.json`, `api-evidence/**`, `tests/runner/**`.
- Audit/statistics package: `verify.py`, `analysis.py`, `tests/audit/**`.
- Parent/coordinator: `scope.json`, `plan.md`, `contracts.md`; implementation packages read these and `research/**` without changes.
- Later phases: `freeze.json`, `preflight/**`, `execution/**`, `blind/**`, `private/**`, `grades/**`, `adjudication/**`, `grades-seal.json`, `analysis/**`, `report.md`, `final-review/**`, `audit.json`, and all owned runtime files. Pre-run modules may implement commands generating these destinations, but must not generate inference evidence during implementation.

## Dataset

`dataset/tasks.json`: array of six objects `{id, slug, title, prompt, starting_urls, allowed_url_patterns, required_source_urls, discovery_chain}`. IDs are `T1` to `T6`; `prompt` includes exact common instructions, exact decision prompt and starting URLs, with no checks. `discovery_chain` is descriptive/machine-readable evidence requirements, not an extra factual scoring bundle.

`dataset/gold.json`: object `{version, tasks}` where `tasks` maps task ID to `{checks, uncertainty, critical_errors, source_rules}`. Each `checks` array has six `{id, requirement, accepted, contradicted, source_evidence}` entries; evidence entries contain `{url, quote, archive_path}`. The uncertainty object gives pass/omit/fail criteria and evidence; critical errors remain checkable descriptions, not every omission. Keep scoring semantics in protocol.

`dataset/sources.json`: array `{id, url, final_url, status, content_type, raw_path, text_path, raw_sha256, text_sha256, anchors, links, retrieved_utc, canonical_url}`. Preserve raw bodies and generic normalized text. Native mirrors map to canonical URLs. Dataset archive preparation may use its own temporary extraction initially, then finalize `text_sha256` with the runner-owned shared extraction function before freeze.

`webfetch.extract_document(raw: bytes, content_type: str, url: str) -> str` is a deterministic, import-safe generic whole-page extractor retaining substantive text and useful links, not gold-specific sections. Dataset and runner use it for frozen/main-content hashes. `webfetch.normalize_text(text: str) -> str` normalizes whitespace/markup for quote checks without changing substantive words. No network action occurs merely on import.

## Frozen protocol and schedule

`protocol.json` contains explicit version, model endpoint and IDs, efforts, limits, retry/source-drift/access-gate rules, schedule/statistics seeds, grading semantics, qualification, eligibility and recommendation margins. `system.txt` and `tools.json` are identical for every case. The public API/source contracts are archived in `api-evidence/`.

`schedule.json`: object `{seed, algorithm, configurations, blocks, cases, position_counts}`. Configuration entries `{id, model, effort}` use IDs `deepseek-low`, `deepseek-high`, `deepseek-max`, `glm-low`, `glm-high`, `glm-max`. Block entries `{id, task_id, repetition, case_ids}` cover each task twice. Case entries `{id, index, block_id, position, task_id, repetition, configuration_id, model, effort}` use opaque IDs independent of identity. There are 72 cases; case 1 is DeepSeek LOW. Save algorithm/realized counterbalance.

`freeze.json`: object `{version, created_utc, files, schedule_sha256, no_candidate_calls_before_seal}`; `files` maps immutable relative paths to SHA-256, covering all runnable code, fixed tests, protocol, system/tools, dataset/gold/source archives, API evidence and schedule. Exclude generated execution/grading/report/audit files. Freeze hashing is saved-only.

## Execution evidence

`execution/index.json`: object `{study_status, gate_case_id, gate_status, planned_cases, attempted_cases, terminal_cases, cases, cleanup}`. `cases` is an array of record paths in schedule order; even unrun cases have records. `study_status` is `completed`, `access_blocked`, or `incomplete`; no interruption except the counted access gate qualifies as an honest blocked completion.

`execution/cases/<id>/record.json` contains `{case_id, schedule_index, block_id, task_id, repetition, configuration_id, model, effort, status, operational_complete, start_utc, end_utc, monotonic_start, monotonic_end, wall_s, assistant_span_s, inference_steps, requests, fetches, answer_path, visible_words, usage, errors, cleanup, source_drift}`. Unrun statuses have null times and zero requests, not invented latency. `requests` and `fetches` are arrays linking full artifacts; all request bodies omit credentials. Assistant/tool histories, native responses and full fetched bodies are retained.

Request records include `{step, started_utc, ended_utc, elapsed_s, request_path, response_path, http_status, error, usage}`; log intent before transmission, retain ambiguous failures and never replay. `inference_steps == len(requests) <= 8`. Save actual `reasoning_effort` and model on every body. Each case starts with fresh messages; terminal-step tool removal is explicit. Tools can involve several fetches per inference step.

Usage object `{complete, raw_steps, prompt_tokens, completion_tokens, reasoning_tokens, cache_read_tokens, cache_write_tokens, uncached_input_tokens, non_reasoning_output_tokens, reported_cost}` preserves null unknown totals and raw upstream fields. Native completion tokens are inclusive; do not add reasoning twice. No price formula is necessary for ranking.

Fetch records `{id, requested_url, final_url, status, redirects, started_utc, ended_utc, elapsed_s, raw_path, text_path, model_text_path, raw_sha256, text_sha256, model_text_sha256, raw_bytes, text_bytes, truncated, error, frozen_source_match}` distinguish raw, generic full extraction and actual limited text given to model. Do not assume controller re-fetch equals candidate content. Preserve denied/failed attempts with honest null fields.

Direct harness timing spans the supervised worker launch through exit, not CLI startup. `assistant_span_s` covers model request work as a secondary definition explicitly described in report. Errors, timeouts, incomplete answers and access rejections do not enter qualified-success speed distributions. All workers are sequential; cleanup includes saved owned-process checks and credential hygiene without secret output.

## Blind exports and grades

`private/unblind.json`: hidden mapping blind ID to execution case ID, and sealed hashes. Do not expose it to graders.

`blind/index.json`: `{shards: {a: [...], b: [...]}, cases: [...]}`. `blind/cases/<blind-id>/case.json`: `{blind_id, task_id, prompt, answer, sources, rubric, mechanical}`. Include answer/fetched source text and canonical URLs, but no model, effort, schedule index, times, tokens, raw response metadata, backend identity or identity-bearing paths. Mechanical fields may include visible-word and fetch/source compliance evidence; no latency. Keep source files inside the opaque case directory. Redact any explicit self-identification transparently and record the redaction separately from graders.

`grades/shard-<a|b>/<blind-id>.json`: `{blind_id, task_id, checks, uncertainty, citations, critical_errors, unsupported_extras, compliance, ambiguous, notes}`. Six checks `{id, status, answer_quote, evidence, rationale, citation_status}`; status is `supported`, `contradicted`, `missing`, or `unverifiable`; citation status is `entailing`, `missing`, or `non_entailing`. Evidence `{url, source_path, quote}` refers only to blind/frozen first-party sources. Missing checks use empty answer quotes with an explicit absence rationale. Uncertainty `{status, answer_quote, rationale, evidence}` uses pass/omit/fail.

Citation records identify claims/URLs/support/anchor compliance. Compliance has booleans `{full_urls, word_cap, english, fetched_two_sources, source_rules, tool_rules}` and a separate discovery-chain field. Critical errors and unsupported extras retain answer spans and source rationale. An empty unrun row receives no fabricated semantic grade.

`adjudication/<blind-id>.json` preserves any proposed effective override and rationale without editing initial grades. `grades-seal.json` hashes initial/effective grades and the blind review records before unblinding, with created UTC. Analysis reconstructs scores from judgments rather than trusting a supplied `qualified` flag.

## Analysis and offline audit

`analysis.py` consumes saved schedule/execution/blind mapping and sealed effective grades, writing `analysis/results.json` plus inspectable paired/task-cluster tables. Report code must not invoke network/model/auth operations. Implement medians/p90, eligibility, recommendation margins, taskwise/paired/leave-one-task-out and 10,000 whole-task bootstrap draws under the frozen protocol. Use null where no qualified observations or no sufficient paired coverage exist.

`verify.py --stage frozen|collected|grades|graded`, with `--shard a|b` for grades, performs stage-appropriate saved-only integrity checks. `python3 verify.py` audits final saved evidence and writes `audit.json`; expose whether the audit is a completed comparison or honest access block. Missing later-stage evidence must fail the final default audit. Unit tests run without models, credentials or external network.
