# Two research evaluations — approval proposal

Status: design only, 2026-10-07. Candidate calls authorized now: **zero**. No model, agent, provider, privacy or search configuration changes. Earlier evaluations are not included in the new ranking. Research findings are in `research/`; their source registers distinguish fetched evidence from design judgments.

## 1. Objective and basis

Compare useful, accurate, source-grounded research and speed in two distinct workflows: **live web discovery + fetching** and **read-only codebase exploration**. Publish separate recommendations, not one merged model leaderboard. Price does not determine the ranking. The unit under evaluation is the model **plus this disclosed scaffold and route**, not an isolated model.

The design follows task-specific criteria, repeated isolated trials, reference solutions, partial credit, full traces and blinded calibrated graders in the [OpenAI evaluation guide](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [Anthropic agent-evaluation guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). [BrowseComp-Plus](https://aclanthology.org/2026.acl-long.1023/) motivates common retrieval controls and disclosure of live drift. [DeepResearch Bench II](https://arxiv.org/html/2601.08536v3) motivates atomic content criteria, but this is not its long-report benchmark. [RepoQA](https://arxiv.org/html/2406.06025v1) inspires semantic function location, not supplied-context BLEU scoring. [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) motivates solvability/alternative-answer review; patch correctness is outside this read-only evaluation.

All numerical budgets, utility thresholds and task selections below are **design proposals**, not quantities established by those papers.

## 2. Model and effort matrix

| Route/model | Efforts | Configurations |
|---|---|---:|
| `cli_proxy_google/gemini-3.8-flash` | `low`, `medium`, `high` | 3 |
| `opencode-go/deepseek-v4.1-flash` | `low`, `high`, `max` | 3 |
| `opencode-go/glm-5.3-flash` | `low`, `high`, `max` | 3 |

**Approval assumption:** Gemini 3.8 means **Flash**, as in the preceding study. Do not substitute Pro or include the CPA alias as another candidate. Catalog observations and native contracts are cited in `research/model-contracts.md`: [Google](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode), [Z.AI](https://docs.z.ai/guides/vlm/glm-5.3-flash.md).

These are all documented **enabled effort levels** on the proposed routes. Gemini 3.8 Flash rejects `minimal`. DeepSeek's native thinking-off mode is not an advertised/verified Go variant and is excluded; compatibility synonyms are not additional efforts. Backend effort honoring, installed proxy equivalence, quota, cache forwarding and hidden retries remain **UNVERIFIED**. Equal labels do not imply equal reasoning budgets.

Controller and blind graders: `openai/gpt-6.1-sol-fast#high`, retaining the user's earlier controller choice. No candidate model grades this comparison.

## 3. Proposed scale

| Option | Tasks per suite | Repetitions | Trials per suite | Both suites | Gemini trials, both suites |
|---|---:|---:|---:|---:|---:|
| Recommended | 12 | 3 | 324 | **648** | **216** |
| Exploratory alternative | 12 | 1 | 108 | **216** | **72** |

One trial is an entire agent research invocation, not one HTTP request. Under the caps below, the recommended option permits at most **6,480 client generation requests**, or **2,160** for the alternative. Unobservable upstream retries are not counted as known client requests. Grading/curation uses additional controller work, disclosed separately; search-provider calls may also consume service quota. No warmups, live inference probes, failed-case retries, fallback routes or subsequent rounds are implicitly approved.

At 240 seconds per trial and one active candidate, the scheduled candidate wall-time ceiling is **43.2 hours** recommended or **14.4 hours** exploratory, excluding preparation, grading and any pauses. This is a ceiling, not a prediction. Account debit and sufficient headroom are unknown; do not equate catalog availability or published request estimates with quota.

## 4. Web suite: question-only live search and fetch

Candidates receive a date/version-scoped question **without answer URLs**. The proposed task cut-off is 2026-10-07; freeze a replacement cut-off before approval if execution is deferred. Twelve tasks span four strata, three each. The following themes are not frozen prompts or validated gold:

| Stratum | Task themes |
|---|---|
| Routine | Discover the supported Python floor for a specified Django release; identify Node release-maintenance/EOL facts; find a PostgreSQL release-support deadline. |
| Applied | Pydantic v1-to-v2 validator migration; Kubernetes client/server version-skew decision; Terraform S3 locking version and limitations. |
| Difficult | Advisory applicability/fixed version for a named public package; reconcile an announcement and newer changelog; uv versus pip-tools on two explicitly named engineering requirements. |
| Stress | A bounded feature claim that may be unestablished; recovery from a verified relocated/redirected page; distinguish deprecation and removal releases using the governing specification. |

During approved preparation, authors must verify every question against accessible evidence and record a feasible search/fetch path within the envelope. Select any still-unspecified package/feature/releases then. Record replacements **before** freezing; do not change difficulty or gold after candidate outputs.

Tools: a common, external `websearch` and read-only `webfetch`, not Gemini-native grounding or vendor-specific search. No browser/JavaScript execution, local files, shell, accounts, forms or writes. Use a **single fixed search provider**, no random mode or silent fallback. Search-provider identity/access are not yet confirmed; a focused global-config selector check found no match, which does not identify remembered settings. Preparation must name the engine, API/schema, result count/default, locale and canonical result rendering before final approval. Do not invent unsupported tool arguments or alter user configuration silently.

Archive actual SERPs with ranks/snippets/URLs, raw fetched pages, effective URLs/redirects, visible normalized text, timestamps, hashes and truncation. Do not promise byte-identical live results at different times. Identical payloads use identical rendering; different model queries can legitimately find different evidence. No cross-trial harness cache; log any within-trial page reuse. Engine-side caches remain unknown. Do not pool live research with frozen-context retrieval. A separate replay or candidate injection challenge is **not included**.

Web controls deny private/loopback/metadata destinations and unsafe redirects, enforce public read-only requests, and isolate fetched instructions as untrusted data. Offline harmless injection fixtures test the controls, not candidate robustness. A recovered exploratory 404 is not automatically a failed final answer. One adequate source can suffice for a simple task; independent corroboration is required only by a task that actually needs it.

## 5. Codebase suite: six public snapshots, two tasks each

| Repository | Proposed full commit | Two task themes |
|---|---|---|
| Click | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` | Default/parameter precedence; command/context flow and tests. |
| HTTPX | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Client-to-transport/error flow; bounded configuration or dependency behavior. |
| Cobra | `adbc8813901bba65827259daa8e22ff94ec1f30e` | Semantic implementation location; inherited flag/dispatch behavior. |
| Prometheus | `d4467eede8e6d171c7ee06c0307a34878339a237` | Configuration-to-consumer path; decisive negative/counterexample branch. |
| Zod | `0b216ef674e297ebe41d8bf902262e56f8755822` | Cross-package transformation; implementation/test limits. |
| OpenCode | `b1fe25ab5ecc9f9bc911a8a2e6a51565cc764322` | Tool/provider/config dispatch; responsibility across package boundaries. |

Public metadata and root-license bodies were fetched; snapshots have **not** been acquired or source-gold validated. Sources are in `research/corpus-candidates.md`. Root licensing is not a complete audit of third-party files. Before freezing, acquire these revisions under the evaluation artifact directory, preserve required licenses/NOTICE, review included-file eligibility, exclude private or vendored/ineligible assets as appropriate, and hash every eligible file. Record all exclusions and line-ending policy; derive citations from the resulting snapshot. No user's private or working-tree code is included. chi/Hono are not additional authorized runs.

Proposed mix: two semantic-location tasks, six multi-file flow/configuration tasks, two negatives/boundaries, two coverage/localization tasks; balance exact assignments after reading the source. Repository size and task difficulty are distinct and will be measured rather than guessed.

Tools: bounded directory listing/path glob, regex/literal grep and numbered file reading. Freeze regex/glob semantics, ordering, encodings, ignore/hidden policy, line/offset units, output caps and continuation behavior. Enforce a snapshot-only root, reject traversal/external symlinks, and serve tools through a worker with no arbitrary shell, writes, execution, network, delegation or memory. Gold and other trials are outside its accessible view. Global instructions/configuration/skills and corpus agent files are not auto-loaded as instructions. If agent files remain searchable ordinary data, document that consistently. Do not silently downgrade the promised isolation if an OS sandbox is unavailable: report the concrete tool-only boundary and obtain explicit acceptance before execution.

Gold contains required paths/symbols, flow edges, exact evidence spans/lines, counterexamples, acceptable alternative routes, explicit unresolved dynamic cases and critical errors. An empty grep does not establish universal absence; negative claims require a decisive closed branch/schema or a validated bounded scope. Existing tests may be read, **not run**. A proposed fix is not the measured outcome.

## 6. Fixed resource envelopes

| Per trial | Web | Codebase |
|---|---:|---:|
| Supervisory wall deadline | 240 seconds | 240 seconds |
| Model steps, including final | 8 | 12 |
| Tool calls dispatched | 4 searches + 8 fetches | 18 total |
| Maximum returned characters per tool result | 20,000 | 20,000 |
| Maximum cumulative returned evidence characters | 64,000 | 128,000 |
| Requested output-token cap per client request | 16,384 | 16,384 |

Budgets are identical across candidates **within each suite**, not between different workflows. The last allowed model step is reserved for synthesis with no tools; disclose this in the initial prompt. Failed/duplicate calls and individual calls in a parallel batch consume budget. Attempts above a cap are logged/rejected without dispatch. A continuation/read of cached page material consumes a fetch/read allowance and returned-character budget. Truncation is explicit; no silent summaries of unread evidence. A ~600-word answer is a nonbinding usability guideline, not a zero-score rule. Equal numeric token caps across tokenizers/native protocols do not prove equal compute; effective native caps/finish metadata must be recorded.

The wall clock begins immediately before dispatching the trial, includes provider/network/tool time, and stops on a completed final answer or terminal limit/error. Last-step/tool-only output or incomplete/truncated answer is an operational failure; no post-cap request. Save partial evidence for diagnostic grading without calling it a completed answer.

## 7. Execution and compatibility

Fresh conversation per trial; one active candidate; no prior answer history or hidden controller assistance. Use twelve task-by-three-repetition blocks per suite, all nine configurations per block. Seed `20261007`; for the recommended option generate an odd-nine Williams schedule: base `[0,1,8,2,7,3,6,4,5]`, nine cyclic shifts and their reversals, each row twice. Check four appearances per position and four of every ordered adjacent configuration pair. Assign rows by seeded shuffling, retain all repetitions, and interleave suites/phases. Twelve-block exploratory ordering cannot be perfectly position-balanced and must disclose that limitation. Save the exact generated schedule before execution.

The first real scheduled task for each configuration **in each suite** doubles as its counted compatibility gate, not an extra call. Check actual tool invocation/result/continuation with intact route history. Gate outcomes: `passed` for a clean operational tool cycle and complete final answer, regardless of factual grade; `incomplete` for an ordinary timeout after verified clean continuation, counted and allowed to continue; `not_exercised` when no tool cycle was established but no actual native contract rejection occurred, counted and allowed to continue with compatibility still unverified; `rejected` only for an observed native-parameter/protocol incompatibility, stopping dispatch for approval. A time-limited gate is never labelled passed. A complete answer choosing not to research is an operational completion but a construct/task-success failure, with gate `not_exercised`, not proof of API incompatibility. No additional gate probe is permitted; later already-scheduled traces may establish compatibility without rewriting the first gate outcome.

Use the verified Chat routes and literal `reasoning_effort`, omit common optional `thinking` fields, preserve complete native assistant/tool history including available reasoning/signature fields, and unit-test adapters with recorded fixtures. Acceptance is not proof that the backend honored effort. If the existing shim cannot preserve required native state, seek approval instead of switching routes. Own user agent and stable per-trial `x-opencode-session` on Go; [Go guidance](https://opencode.ai/v2/docs/console/go/) asks for typical coding-agent traffic. All web questions stay within developer engineering research; material uncertainty about provider-policy suitability needs first-party clarification or separately approved routes, not an assumed user-granted exemption.

No client retries. Ordinary timeouts, wrong answers and recoverable candidate fetch errors remain scored cases. Quota/authentication/native-parameter rejection, common search outage or suspected harness defect stops dispatch; report the scope and request approval before repairs, provider switching or further inference. This is a run stop, not use of a persistent-goal pause tool. Resume schedules never resubmit interrupted/uncertain trials. A once-only ledger rejects duplicate trial IDs and records every client attempt and terminal status; hidden upstream attempts stay unknown.

Retain sanitized request bodies/hashes, native response/SSE state, actual model/effort intent and available response version, usage/cache/reasoning metadata, finish reasons and timings. Native reasoning is not the scored answer. Never persist auth headers, keys or account data; scan/sanitize artifacts without erasing legitimate public source facts. Do not toggle balance fallback, privacy settings or quota configuration.

## 8. Grading and guardrails

Freeze question, atomic criteria, essential units, acceptable alternatives, source evidence and passing reference answer **before any candidate answer**. All scored requirements must be inferable from the prompt. Validate correct, subtly wrong, omitted, unsupported, contradictory and alternative-valid fixtures. These are deterministic/offline preparation, not candidate inference pilots. Automated schema/quote checks cannot certify semantic truth.

Primary score vector, reported separately:

- **Correctness/completeness:** required atomic facts and relationships correctly answered.
- **Grounded coverage:** required units correct and supported by actual retrieved/read evidence.
- **Practical task success:** all essential units correct **and supported**, at least 80% of remaining units correct **and supported**, no decisive unsupported claim or critical error, complete answer inside deadline, and actual research evidence used (search + fetch for web; file read for code).
- **Critical errors:** materially wrong conclusions/flow/precedence, fabricated decisive evidence, overconfident unsupported negatives or prohibited instruction following.
- **Operational completion/reliability:** completion, timeout, cap, protocol, quota, transport and service outcomes over all scheduled attempts.

If a task has no nonessential units, the nonessential threshold is vacuous, not a zero-denominator perfect-precision statistic. Publish citation entailment, citation coverage, source authority, unsupported extras, uncertainty, instructions/usability and tool navigation separately. An HTTP 200 or existing line number is not semantic support. Anchor/text-fragment usability is separate from ordinary-page validity; use archived HTML/text when normalization drops anchors. Alternate valid sources/navigation are accepted with recorded blinded adjudication.

Answer-level semantic scores use completed/evaluable answers with explicit n. Additionally publish **all-attempt effective grounded coverage**: completed supported credit macro-averaged by task with operational nonanswers set to zero outcome credit, not fabricated semantic grades. Partial/time-limited text is diagnostic only. Failures remain in success/completion denominators; no survivor-only leaderboard. Small citation-formatting defects or harmless exploratory fetch failures do not automatically zero knowledge credit.

Blind grading hides candidate/model/effort/timing and supplies frozen gold plus actual evidence. An independent fresh-session reviewer on the **same GPT backend** reviews all critical/uncertain results and a seeded 25% sample over **planned trial IDs**, balanced by configuration and suite: 9 IDs per configuration per suite (162 total) for recommended size or 3 (54 total) exploratory, before overlaps/additional reviews. Select IDs before seeing answers. Sampled nonanswers get operational-evidence review, not fabricated semantic grades; do not replace their IDs with successful answers. Unrun IDs are explicitly accounted for as unrun, not marked reviewed. Report the actual semantic/operational review counts and any missing obligations in a stopped study. Report disagreements and corrections, preserve original labels/keys, regrade every affected answer consistently, and seal grades before unblinding. This is **AI-graded, same backend, not human-calibrated** unless a human review is actually obtained. Grading calls are additional controller work, not candidate runs.

Enforce exact-once dispatch, budgets, schemas, gold isolation, safe URLs/paths, native-history preservation and trace/hash integrity with executable checks in the future harness rather than merely adding written agent rules. No harness guardrail has been built in this planning stage.

## 9. Statistical analysis and decision

Publish each suite's per-configuration vector and per-task/repository slices. Use paired differences and 10,000 whole-cluster bootstrap draws: web tasks merged where they share a project/evidence family; codebase resamples the six repositories with their two tasks, all repeats and configurations retained. Freeze cluster membership before execution. Report 95% descriptive intervals and the small number of independent clusters; 36 repetitions are not 36 independent questions. No statistical-power guarantee is claimed.

Predeclare nine within-family effort-pair contrasts; publish all 36 pairwise contrasts per suite descriptively, not as uncorrected significance discoveries. Do not select a best configuration and then call a post-selection unadjusted interval proof of equivalence or formal superiority.

Speed: end-to-end median/p90 for completed answers with n, separately latency for practical successes with n, and success/completion by deadline over all attempts. Report first action/first final-answer timing when observed, request/tool intervals and consumed resources. Overlapping tool durations are not subtracted as though sequential; request wall time is not pure internal inference time. Failures never win by being fast.

Proposed practical recommendation rule, explicitly a utility judgment: candidates must have at least 95% operational completion, at least 85% practical task success and zero **observed** critical errors. Among those within five percentage points of the best observed all-attempt effective grounded coverage, prefer the lowest practical-success median latency. Show uncertainty and tradeoffs. This yields a **provisional recommendation**, not a formal statistical winner; if uncertainty permits material quality loss, disclose it prominently. If none qualifies, report no qualified candidate rather than force a winner. No price adjustment, pooled web/code winner, earlier-study result or best-of-three answer selection.

## 10. Preparation, approval and observable completion

**Now:** present this proposal. No implementation or candidate calls are authorized by the existing request.

**Design approval authorizes preparation only:** select recommended/exploratory volume and confirm Flash; acquire/sanitize public snapshots; identify the fixed search engine without exposing credentials; create the local harness, task/oracle files, tests and schedule under this evaluation directory. Source curation may use controller read-only search/fetch and thus search-service quota; it does not use candidate generation. No global config edits, installs or account changes are implied.

**Final execution approval:** show the frozen 24 prompts, rubric/evidence hashes, engine/route contracts, budgets, schedule, offline test results and remaining unknowns. Request authorization for exactly the approved number of trials. A source/engine/route/budget change requires new approval; no silent extra pilot.

After preparation, implementation packages have disjoint ownership: `corpus/`; `tasks/web/` + `gold/web/`; `tasks/code/` + `gold/code/` after snapshots; `harness/core/`; `harness/tools/`; `grading/`; `analysis/`. Independent implementers may work in parallel after permission, followed by a read-only review and offline checks. The parent integrates `freeze/`, then executes only after final approval. These directories and tests are proposed, not already present.

Observable preparation acceptance: all snapshot/source/gold hashes match; reference/mutation and sandbox/protocol/cap/ledger fixtures pass; fixed-engine contract and all nine effort rows recorded; schedule/count balance verified; approved freeze hash saved. Observable eval completion: every approved trial has exactly one terminal record (including failures or explicitly stopped/unrun statuses), every evaluable answer has a sealed grade, review obligations are accounted for, and a report audit reproduces tables from saved evidence. Audits establish integrity and accounting, **not semantic truth**. A stopped or partial study is labelled incomplete rather than complete.

Still unresolved for final approval: actual engine/access and account headroom, installed route behavior/effort honoring, sanitized corpus eligibility, concrete question solvability within budgets, and deployed isolation. Research/citations are complete; the runnable evaluation package is not.
