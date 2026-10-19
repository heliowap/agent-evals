# Read-only codebase exploration evaluation: primary-source findings

Research date: 2026-10-07. This is research input to the parent planner, not an execution plan or approval to run candidates.

## Answer

**DESIGN JUDGMENT:** Use a frozen-repository, tool-assisted question-answering suite: locating code is necessary, but the main outcome is a useful explanation whose symbols, relationships, boundaries, and citations are supported by the snapshot. Include retrieval as a diagnostic, not as the whole benchmark. RepoQA measures function search; RepoBench and CrossCodeEval center on completion; SWE-bench measures patch resolution, so none directly substitutes for this requested read-only workflow. [S1–S8, S11]

**DESIGN JUDGMENT:** Compare semantic accuracy/grounding first, then latency and reliability; score partial understanding separately from critical errors, formatting, and tool compliance. Agent-evaluation guidance explicitly supports task-specific graders, partial credit, alternative valid routes, clean trials, and human calibration. [S9–S10] The local request prioritizes accuracy/source grounding, latency, reliability, excludes price, and authorizes zero candidate calls. [L1]

## Verified benchmark facts and applicability

| Primary source | What it actually measures | Transferable idea; boundary for this suite |
| --- | --- | --- |
| RepoQA README and paper | Searching Needle Function: 500 tasks, 50 repositories, five languages; models receive a large supplied code context and a description and retrieve a function. The paper describes purpose/input/output/procedure descriptions, avoiding target function/variable names. [S1–S2] | **DESIGN JUDGMENT:** Useful semantic-search archetype and language/domain diversity; supplied concatenated context is not an interactive filesystem-navigation evaluation. Do not equate function identification with explaining a multi-file architecture. |
| RepoQA scoring source | `needle_evaluator` sanitizes an output, iterates the repository's `needles`, computes similarity, and selects the largest similarity. `metric.py` uses whitespace tokenization and smoothed sentence BLEU. Score aggregation requires the correct best match and similarity at least the chosen threshold. [S3–S4] | **DESIGN JUDGMENT:** Keep target-symbol checks, but do not adopt copied-function BLEU as the correctness oracle for explanatory answers. The inspected implementation compares against `needles`; do not silently describe that as exhaustively checking every repository function. |
| RepoBench paper | RepoBench-R retrieves relevant cross-file snippets; RepoBench-C predicts the next line; RepoBench-P combines retrieval and next-line prediction, for Python and Java. [S5] | **DESIGN JUDGMENT:** Separate retrieval from downstream understanding. Completion accuracy is not evidence that an agent can answer a repository question. |
| RepoBench v1.1 repository | README describes masked cross-file first-use, random-use, and in-file lines; evaluation uses Exact Match, Edit Similarity, and CodeBLEU. Data README says its primary focus is next-line prediction, describes October–December 2023 collection and Stack-v2 file-content deduplication. [S6] | **DESIGN JUDGMENT:** Pin benchmark version if reusing ideas. The authors' deduplication claim is not proof of clean training data for today's candidates. |
| CrossCodeEval paper and code | Four languages: Python, Java, TypeScript, C#; static analysis selects completion examples requiring cross-file context. The paper describes permissively licensed source repositories. Scoring code checks normalized predicted/target lines, edit similarity, and identifier matching/precision/recall/F1. [S7] | **DESIGN JUDGMENT:** Cross-file dependency selection and identifier-level diagnostics transfer; generated-line matching does not evaluate grounded architectural explanation. The paper's corpus description does not replace a license audit of newly selected snapshots. |
| CodeSearchNet | README describes two million comment/function pairs across Python, JavaScript, Ruby, Go, Java, PHP; repository-disjoint train/validation/test partitions; retrieval evaluation with NDCG and human relevance judgments for 99 general queries. Human judgments are graded 0–3. [S8] | **DESIGN JUDGMENT:** Use graded relevance/ranking where a task really asks for ranked search results. Repository-level splitting is preferable to merely splitting neighboring files. Function/docstring retrieval does not test complete call/configuration flow. |
| SWE-bench and Agentless | SWE-bench asks for a patch resolving a GitHub issue. Agentless separates hierarchical localization (files, classes/functions, edit locations), repair, and patch validation. [S11–S12] | **DESIGN JUDGMENT:** Localization is relevant to locating responsibility or explaining a suspected fault; repair and test-pass scores are out of scope. An explanation can be right without a patch, and unchanged tests do not establish explanation accuracy. |
| SWE-bench Verified authors | They document underspecified issues, overly specific tests rejecting valid solutions, and environment setup failures; they use professional developer screening and discuss likely public-GitHub training contamination as a limitation. [S13] | **DESIGN JUDGMENT:** Validate task solvability and alternative answers before running candidates. Treat public-code contamination as an unresolved risk, not as evidence that any named candidate memorized these tasks. |

No historical model leaderboard results are used to infer the requested candidates' ranking. Model/effort contracts belong to the other researcher. [L1]

## Licensing and corpus reuse: verified versus unknown

- RepoQA's fetched project `LICENSE` is Apache-2.0; the inspected scoring modules also have Apache-2.0 SPDX headers. This verifies those project artifacts, not all third-party source files in its benchmark corpus. [S3–S4, S14]
- RepoBench's fetched project `LICENSE` is Creative Commons Attribution 4.0 International. Do not assume its license matches another benchmark or automatically re-licenses scraped third-party repositories. [S15]
- CrossCodeEval's fetched project `LICENSE` is Apache-2.0; its README says Apache-2.0 and the paper describes permissively licensed source repositories. No per-repository license manifest was audited here. [S7, S16]
- CodeSearchNet's project code/documentation is MIT; its README explicitly says licenses of source code used as data are supplied separately in language-specific `_licenses.pkl` files. Those data-license files were not downloaded or audited. [S8, S17]
- **UNVERIFIED:** Proposed new corpus repositories, commit SHAs, source licensing, notices, redistributability, cleanliness, and model-training overlap. Next: inspect each selected snapshot's actual LICENSE/NOTICE and third-party file headers, record provenance and exclusions, and obtain approval before acquiring repositories or sending private code to vendors. This is a proposed audit, not legal advice or an assertion of permission. [S8, S13–S17]

## Task archetypes for consideration, not yet gold tasks

All rows are **DESIGN JUDGMENTS**, adapting semantic retrieval, cross-file dependence, localization, and task-specific agent grading. They are proposals, not claims about an inspected corpus. [S1–S12]

| # | Read-only task archetype | Useful required output and oracle units |
| --- | --- | --- |
| 1 | Semantic function location without the exact symbol name | Correct path + fully qualified symbol + a short explanation of why its behavior fits; reject plausible same-name distractors. |
| 2 | Disambiguate similar names across packages/languages | Identify which implementation serves the specified entry point; cite namespace/import/registration evidence and distinguish the other candidate. |
| 3 | Follow an end-to-end call/data flow | Trace entry point → adapter/validation → core operation → result/error, with each required edge supported in its actual file. Accept equivalent routes through wrappers. |
| 4 | Explain configuration/default precedence | Trace declaration, loader/merge order, override, and consumer; cite what wins under specified inputs and any early exit. Do not infer precedence from variable names alone. |
| 5 | Map plugin/provider/registry dispatch | Connect registration/export to lookup/selection and concrete implementation; explicitly qualify runtime-loaded targets not resolvable from visible source. |
| 6 | Explain schema/serialization transformation | Locate producer, shared type/schema, conversion, and consumer; identify required fields, defaults, and transformations with evidence. |
| 7 | Locate behavior coverage and boundaries | Find relevant existing test(s) and implementation; explain what the test asserts and what it does not prove. Read tests; do not execute or modify them. |
| 8 | Bounded negative/counterexample question | Answer whether a specified path supports a feature or rejects an input; provide searched scope and decisive branch/schema/call-site evidence. Admit unresolvable dynamic cases. |
| 9 | Snapshot/version/dependency-constrained behavior | Reconcile actual manifest/lockfile and implementation, distinguish a declared range from a locked version, and avoid claims about an unobserved installed environment. |
| 10 | Locate responsibility or analyze a supplied symptom | Identify where a behavior/change would belong or a likely cause, explain neighboring interfaces and counterevidence; no edits, proposed implementation, or fix-pass grading. Separate hypothesis from demonstrated flow. |

**DESIGN JUDGMENT:** Prefer realistic bounded engineering questions, with mostly multi-file reasoning and a minority of function needles; no tool-heavy riddles. Add happy-path and counterexample/unsupported-feature cases. Explicitly include cases where “not established from this snapshot” is correct. This follows guidance to build balanced positive/negative cases and task-specific reference solutions. [S9–S10]

**DESIGN JUDGMENT:** Twelve questions cannot give reliable per-archetype estimates for ten archetypes. They are an initial discriminating suite, not a comprehensive language/capability certification; expand only after approval if important slices remain underrepresented. [S9–S10]

## Repository selection and immutable task packages

Recommendations below are **DESIGN JUDGMENTS**; they do not certify any current repository. Topic/language diversity and repository-disjoint partitions have precedent in RepoQA and CodeSearchNet; clean isolated trials are recommended in agent-eval guidance. [S2, S8–S10]

1. Consider categories rather than selecting solely by popularity: a small cohesive library; mid-sized application/CLI with configuration and tests; large layered service/framework; multi-package/monorepo with shared contracts. Cover Python, Go, and TypeScript if representative of the user's work; use at least one multi-language or generated/interface boundary only if its visible dependencies suffice.
2. Record actual eligible file counts/bytes, language mix, package count, and oracle-required files/edges before labeling size/difficulty. Define size bins prospectively; this research does not claim universal thresholds. Distinguish repository size from the amount of evidence needed to answer.
3. Choose between **four repositories × three tasks** (more within-repository coverage) and **six repositories × two tasks** (more repository clusters). Both are twelve tasks; favor six clusters if generalizing across unfamiliar codebases matters most, four if realistic deeper flows matter most. Neither gives strong small-difference inference. [Arithmetic A1]
4. Fix a full COMMIT SHA, not a moving branch. Produce a sanitized snapshot file manifest with byte hashes and line-ending policy; preserve provenance, licenses/notices, and a record of every exclusion. Recompute citations after any sanitization. Reject gold if hashes change.
5. Candidate-visible content: approved ordinary source, tests, manifests/lockfiles, and relevant repository documentation. Exclude `.git`, history/logs, credentials, external symlinks, caches, prior trials, task answers, grading code, and hidden oracle metadata. Do not auto-load candidate-visible `AGENTS.md`, `CLAUDE.md`, editor/global instruction files, skills, memory, or global config as candidate instructions. If such files are kept as ordinary data, record that policy and use it identically for all routes.
6. Freeze the task and hidden oracle before seeing candidate answers: scope, assumptions, required facts/relationships, accepted alternative paths/symbols, distractors, decisive source quotes, computed line ranges, uncertainty conditions, and critical-error definitions. Do not require the author's exact discovery sequence. [S10, S13]
7. Fresh questions on public snapshots reduce literal reuse of published task text but **do not prove** absence of source-code memorization. Keep held-out repositories for any later validation; optional newly authored/private fixtures require explicit consent and a separate privacy decision. Do not send the user's working tree merely because it is accessible. [S8, S13]

## Read-only tooling and evidence capture

Everything in this section is a **DESIGN JUDGMENT** unless explicitly identified as a documented capability. The benchmark outcome concerns model + scaffold, not a naked model; Anthropic expressly makes that distinction. [S10]

- Offer the same minimal logical operations to every route: directory listing/path glob, literal/regex content search, and file/chunk reading. No candidate shell, code/test execution, writing, network/web search, delegation, memory lookup, or access to private gold. The orchestrator may communicate with the selected provider; the code-reading worker should not gain general network access from that requirement.
- Specify the actual tool contract: argument types, regex engine/version, glob semantics, hidden/ignored files, case sensitivity, encoding/binary handling, ordering, line numbering, offset units and base, maximum output, truncation markers, continuation cursor, errors/timeouts, and path-root rules. Distinguish a common logical interface from proven equivalence to native tools; no emulation should be advertised as identical without tests.
- Validate contracts offline against recorded local `-h`/API/schema/source and deterministic fixtures. Test Unicode, CRLF, empty/no-hit files, duplicate symbols, long files, malformed regex, sorted/truncated output, final partial chunks, and continuation at the exact boundary. Numeric offset is not synonymous with line number or byte offset.
- Bound returned bytes/chars and record actual provider-reported tokens separately; model tokenizers need not yield equal token counts for equal text. Include tool outputs, prompt history, and the final response in total context accounting. Reserve room for a complete last tool response and final answer rather than truncating evidence silently.
- Resolve paths against one approved root; reject absolute/traversal escapes and external symlinks; include allowed internal symlink handling in the contract. Prefer a real OS/filesystem boundary plus tool validation over a prompt-only read-only promise.
- **Documented capability, not locally verified deployment:** Docker documents read-only bind mounts and an isolated `none` network with only loopback. Docker also documents recursive read-only mount/kernel caveats. These docs do not establish that Docker is installed, correctly configured, or secure in this environment. [S18–S20]
- Save complete actual tool requests and returned chunks (with timestamps, truncation/continuation information, resolved snapshot-relative paths, and content hashes), provider responses, and final output. Never replace an unread final tool body with an inferred summary, or reconstruct “expected” tool output as if observed. Preserve the agent-visible text as well as the full underlying result. Full traces are a primary agent-eval recommendation. [S9–S10]
- Before approved candidate trials, test the future sandbox with attempted write/read-outside/network operations and unchanged-snapshot hashes; test the oracle with deliberately wrong file, wrong symbol, valid quote but unsupported conclusion, reversed flow, and an accepted alternative. These are deterministic harness tests, not extra model probes. No harness was built or sandbox exercised in this research.

## Metrics and grading suggestions

All proposed metrics/threshold policies below are **DESIGN JUDGMENTS**. Retrieval/identifier diagnostics are inspired by CodeSearchNet/CrossCodeEval; combined code/model/human graders and partial credit are recommended in official agent-eval guidance. [S7–S10]

| Dimension | Suggested observable measurement | Important restriction |
| --- | --- | --- |
| Semantic correctness | Fraction of required atomic facts and required relationships correctly explained; distinguish missing, contradicted, and expressly unresolved units. | Deduplicate repeated claims; preregister unit weights before answers. A call edge cannot be credited merely because both symbols exist. |
| Grounding | Supported factual assertions / all factual assertions, plus coverage of required facts with valid evidence. Check path, line range, source quote, and semantic support against the exact snapshot. | Citation existence is only a deterministic preliminary check; a real line number does not prove the attached claim. No-claim answers do not receive perfect usefulness scores. |
| Completeness/usefulness | Required outputs addressed, relevant boundaries/counterexamples included, and practical answer sufficient for the stated question. | Do not reward verbosity or demand one template/word count unless user utility actually requires it. |
| Retrieval diagnostics | For explicit relevant-file/symbol tasks: precision, recall, F1 against interpretable gold equivalence sets; graded ranked relevance/NDCG when a ranked output is requested. | Score the answer's selected evidence/results, not every exploratory read. Alternative correct implementation paths must be adjudicated, not automatically treated as false positives. Do not reward grep-hit spam. |
| Critical errors | Counts/rates of invented APIs/files/symbols, wrong implementation, reversed precedence/flow, confident unsupported negative claim, or material contradicted conclusion. | Keep errors visible even if partial fact credit is high. Classify severity beforehand and explain every flag with source evidence. |
| Task success | Preregister task-specific essential units and no-critical-error condition; report alongside continuous component scores. | Do not make all knowledge credit zero solely for citation formatting, optional detail, or a generic length cap. Report strict formatting/compliance as a separate diagnostic. |
| Tool/instruction compliance | Allowed operations only, valid root/arguments, no writes/escape attempts/delegation. | Deterministically prevent prohibited actions; separately log attempted violations. Different valid navigation sequences are not failures. |
| Navigation efficiency | Tool calls, read/search output bytes, distinct files, repeated reads, useful evidence reached, context/tokens, and tool time. | These are diagnostics, not correctness proxies. More reads can be justified; fewer reads can mean a missed counterexample. |
| Latency/reliability | End-to-end time to completed answer, provider/tool time where observable, completion/error/timeout rate, all-trial denominator. | Keep failed/time-limited cases; do not give fast failures a speed advantage or report success-only latency as unconditional performance. |

**DESIGN JUDGMENT:** Negative claims require a declared finite scope and an oracle-backed reason: a decisive branch/closed schema, exhaustive bounded registrations, or audited search coverage including aliases. A single empty grep cannot establish absence across dynamic imports, generated code, external dependencies, or alternate terminology; uncertain cases should be scoped rather than punished for responsible abstention. This is a grading policy, not a claim that static inspection proves runtime behavior. [S9–S10]

**DESIGN JUDGMENT:** Report class-level components (needle retrieval, multi-file flow/configuration, negatives/boundaries, localization/analysis) separately and macro-average by task/repository as specified beforehand. Do not let easy one-file tasks mask weak multi-file understanding. Retain accuracy and grounding side by side instead of hiding them inside one opaque score. [S9–S10]

## Trial protocol, failure accounting, and scale tradeoffs

Recommendations are **DESIGN JUDGMENTS**, grounded in documented output variability, repeat trials, clean environments, and trace logging. [S9–S10]

- Pair configurations on the same tasks/snapshots; use fresh isolated sessions with no candidate-visible earlier transcripts or answers. Randomize/balance configuration order within task/repetition blocks, interleave routes in a comparable time window, and preregister concurrency to avoid confounding queue/resource load with model effort.
- Use three independent repetitions as an initial variability check, not “best of three.” Report average first-attempt task success and empirical all-three consistency separately; do not confuse these with the chance of at least one success (`pass@k`). Anthropic distinguishes pass@k from all-trials consistency (`pass^k`). [S10]
- Let `C` be the **verified** model/effort configuration count from the separate contracts research. Twelve tasks × three repetitions = `36C` trials for this suite. If and only if `C=9`, either initial corpus option is **324 trials**; six repositories × four tasks × three repetitions would be **648**. These are tool-computed arithmetic scenarios, not approved runs or an assertion that nine settings exist. [A1]
- Same observable capability catalog and class-appropriate budgets across routes: wall deadline, turns/tool calls, bytes/context, final-answer budget. Freeze them before candidate trials. Reaching a genuine budget/deadline is a reliability outcome; irrelevant formatting caps are not semantic failure gates. Budget adequacy remains unmeasured until approved work.
- Save requested route/variant and actual request fields, response identifiers/backend metadata available from the route, finish reason, tool parsing errors, usage including cache/reasoning fields when supplied, and full statuses. Effective upstream effort support is **UNVERIFIED** here; a requested setting is not proof it was honored.
- Predeclare how transient transport errors/retries consume time and are counted. Do not silently discard failures, reset clocks, repeat only bad answers, or grant unreported extra attempts. Distinguish harness defects, infrastructure/provider failures, quota/auth blocks, and candidate reasoning failures in the audit ledger.
- Compatibility confirmation should use the first authorized real scored case for each configuration and count every attempt; no extra upstream smoke/probe outside approval. Validate schemas and ledger uniqueness offline first. A hard once-only ledger should reject duplicate trial IDs and prevent resume logic from silently spending additional calls.
- Fresh sessions remove local conversation carryover but do not establish upstream cold caches or no training contamination. Record any reported cache hits; keep repeated code-context exposures balanced, and state cold-cache status as unknown when not observable. Avoid comparing one route's first reads with another route's later warmed reads as if contemporaneous. [S10, S13]
- Analyze paired task differences with repository clustering acknowledged; repeated runs on the same repository are not new independent repositories. Report per-repository distributions and paired uncertainty; resampling by repository/task blocks is a candidate method, not a guaranteed precise interval with only four or six clusters. No power analysis has been performed.
- Rank only on a preregistered policy: accuracy/grounding and critical errors first; latency/reliability within comparable quality tiers; show uncertainty/ties. No price ranking and no merging previous experiment outcomes into this comparison. [L1]
- Optional deterministic grep/navigation playbook and expert-solved reference traces can audit whether evidence is reachable within budgets. They are diagnostics, not an additional candidate model. Additional fixtures, baselines, private data, or permanent harness/tool creation require approval; none is added here.

## Oracle validation and judge calibration

These are **DESIGN JUDGMENTS**, following task-specific expert reference labeling, clear rubrics, valid-answer tolerance, grader calibration, and transcript review. [S9–S10, S13]

1. Oracle author actually reads the matched snapshot and records quotes, symbols, required edges, exclusions, counterexamples, and uncertainty. A README summary or a remembered architecture cannot substitute for source-matched gold.
2. Separate deterministic checks (paths, lines, quoted bytes, schemas, budgets, tool legality) from semantic entailment/flow judgments. Deterministic string match cannot establish every explanatory claim; an LLM judge is not ground truth merely because it returns structured JSON.
3. If an AI judge is later approved, blind model/effort identity, randomize answer order where using comparisons, supply the frozen evidence/reference and explicit per-dimension rubric, allow “insufficient evidence,” and require concise source-linked rationales. Avoid judge preference for length or the author's prose.
4. Calibrate against expert labels with good/borderline/bad examples before scoring. Independently inspect critical/ambiguous failures and a sampled set of accepted answers; report agreement and disagreements/adjudication. Do not claim trustworthy judging from agreement on only easy positives.
5. Validate accepted alternate routes and line-range tolerance with adversarial/mutation examples. Freeze rubric changes before the comparison; if a grader defect is discovered later, version it, document the change, and regrade all comparable saved answers rather than only the preferred model.
6. Read complete transcripts for errors, suspicious successes, missing final evidence, and overbroad absence claims. Distinguish a real candidate failure from an unfair oracle or broken harness before drawing model-ranking conclusions. [S10, S13]

## Unknowns and boundary of this research

- **UNVERIFIED:** Exact native model/effort matrix, backend honoring, context/usage/timeout contracts. Next: separate model-contract researcher; no candidate/provider/model calls were made by this researcher. [L1]
- **UNVERIFIED:** Specific corpus suitability, immutable commit/manifest, licences of selected source files, gold task solvability, and complete source-flow answers. Next: user-approved selection/acquisition and snapshot/oracle inspection, not current-checkout editing.
- **UNVERIFIED:** Deployed sandbox, tool semantic equivalence, budget adequacy, latency, reliability, actual candidate quality, human/AI grader agreement, and statistical power. Next: approved offline harness tests and subsequently the approved recorded trials; no claims of measured superiority are justified now.
- No codebase clones, installations, credential reads, configuration changes, candidate executions, or code-fixing experiments were required for these findings. Scope forbids candidate execution until approval. [L1]

## Primary evidence register

All external sources below were fetched/read in this session. URLs using moving branches describe the fetched version, not an immutable future corpus; the future experiment must pin its own sources and snapshots.

- [S1] RepoQA official README: https://raw.githubusercontent.com/evalplus/repoqa/main/README.md
- [S2] RepoQA author paper, sections 3.1–3.2 and future work: https://arxiv.org/html/2406.06025v1
- [S3] RepoQA actual scorer: https://raw.githubusercontent.com/evalplus/repoqa/main/repoqa/compute_score.py
- [S4] RepoQA similarity implementation: https://raw.githubusercontent.com/evalplus/repoqa/main/repoqa/metric.py
- [S5] RepoBench author paper abstract: https://arxiv.org/abs/2306.03091v2
- [S6] RepoBench official README and data/version documentation: https://raw.githubusercontent.com/Leolty/repobench/main/README.md ; https://raw.githubusercontent.com/Leolty/repobench/main/data/README.md
- [S7] CrossCodeEval author paper and actual metric implementation: https://arxiv.org/abs/2310.11248v2 ; https://raw.githubusercontent.com/amazon-science/cceval/main/scripts/eval_metric.py
- [S8] CodeSearchNet official README, Data, Evaluation, Human Relevance Judgements, Licenses: https://raw.githubusercontent.com/github/CodeSearchNet/master/README.md
- [S9] OpenAI official evaluation best practices, tips/process/graders: https://platform.openai.com/docs/guides/evaluation-best-practices
- [S10] Anthropic official agent-evaluation guidance, structure/graders/non-determinism/steps 2–7: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- [S11] SWE-bench official README, Overview: https://raw.githubusercontent.com/SWE-bench/SWE-bench/main/README.md
- [S12] Agentless authors' implementation README, three phases/localization: https://raw.githubusercontent.com/OpenAutoCoder/Agentless/main/README.md
- [S13] SWE-bench Verified first-party report, adaptation, annotation, discussion/limitations: https://openai.com/index/introducing-swe-bench-verified/
- [S14] RepoQA project LICENSE: https://raw.githubusercontent.com/evalplus/repoqa/main/LICENSE
- [S15] RepoBench project LICENSE: https://raw.githubusercontent.com/Leolty/repobench/main/LICENSE
- [S16] CrossCodeEval project LICENSE and README: https://raw.githubusercontent.com/amazon-science/cceval/main/LICENSE ; https://raw.githubusercontent.com/amazon-science/cceval/main/README.md
- [S17] CodeSearchNet project LICENSE: https://raw.githubusercontent.com/github/CodeSearchNet/master/LICENSE
- [S18] Docker official bind-mount read-only and recursive-mount caveats: https://docs.docker.com/engine/storage/bind-mounts/
- [S19] Docker official isolated network documentation: https://docs.docker.com/engine/network/drivers/none/
- [S20] Docker official container isolation description: https://docs.docker.com/engine/containers/run/
- [L1] Read local scope: `~/VSCode/Lab/evals/research-eval-design-20261007T184125Z/scope.json:2-13`.
- [A1] Arithmetic-only `functions.execute`: `4*3*3*9 = 324; 6*2*3*9 = 324; 6*4*3*9 = 648`; no candidate invocation. The generic formula is `task_count * repetitions * verified_configuration_count`.
