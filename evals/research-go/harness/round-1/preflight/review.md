# P4 independent pre-run review — PASS

**Passed: true. B1–B4 are resolved; no blocking issues remain in this scoped recheck.** This is pre-run review approval, not an actual freeze, account-access proof, execution result, semantic grading proof, or final-comparison completion.

## Current continuation evidence

P4 rechecked only the four previously reported blockers, reading the latest `verify.py`, `tests/audit/test_review_regressions.py`, and `tests/audit/README.md`. The current auditor SHA-256 is `85fcfb0bcaba169eacd25cee95aba41047dc249b20c8720d8318115a5f977a4a`; the previous blocked version was `bcb1b999e89fb0dbd451fd42a6f2d1947e2a6043a730158ad324d243631fcfca`. Full current reviewed-input hashes and requirement evidence are in `preflight/review.json`.

Hash comparisons confirm **all 14 other previously fingerprinted inputs are unchanged**: runner, webfetch, dataset generator, analysis/ranking, protocol, system, tools, schedule, tasks, gold, source manifest, archive state, and both API evidence files. Prior safety/control/statistical evidence for those unchanged inputs is reused, not falsely represented as a new live test. The saved-source verifier rechecked the retained archive itself.

| Issue / requirement | Current code evidence | Observed regression evidence |
| --- | --- | --- |
| B1: conservative evidence-only normalization, including U and grade quotes | `verify.py:56–77,411–417,946–958` | All 53 actual factual/U quotations pass; altered words/negation, globs/operators and escaping retain distinctions. Actual finalized dataset passes frozen validation **only in a temporary copied fixture** (`tests/audit/test_review_regressions.py:168–196`). No source/model/hash bytes are rewritten. |
| B2: linked opaque full/visible bodies and actual model-preview provenance | `verify.py:869–905,920–925` | Actual offline runner/export succeeds for equal and truncated previews; bad hash, missing seal hash, wrong preview even with updated hash, identity leak, outside-case path and unlinked extras fail (`tests/audit/test_review_regressions.py:198–241`). A preview must match a corresponding successful fetch's model text, not a controller re-fetch or frozen reference. |
| B3: real native calls, denied attempts, exact frozen URL scope and canonical/content deduplication | `verify.py:102–142,224–277,642–675,906–925` | Independent literal-AST scope reading without importing webfetch; shell, malformed/extra args, wrong type, rejected foreign/broad-scope URL/redirect, overflow, step-eight and excessive batch outcomes match actual offline runner; false-to-true mechanical tampering fails. Identical extracted bodies count once; requested-call count tampering fails (`tests/audit/test_review_regressions.py:243–295`). |
| B4: counted native auth/entitlement denial versus ordinary interruption | `verify.py:145–155,776–784` | 401 invalid key, generic 403, 400 subscription, 402 entitlement, 429 region/privacy and 500 authentication denials match runner classification. Malformed request, rate limit and ordinary internal error cannot pass as access blocks; truthful incomplete records remain non-final (`tests/audit/test_review_regressions.py:297–323`). One POST, one attempt, 71 access skips remain required. |

Help was rechecked with `python3 -B verify.py -h` and `python3 -B dataset.py verify -h`; earlier unchanged CLI/Python/unittest-help evidence remains applicable. Commands actually rerun from the artifact root:

| Command | Current result |
| --- | --- |
| `python3 dataset.py verify --require-finalized` | PASS: 6 tasks, 36 checks, 6 U keys, 22 raw whole bodies, 53 quotes, 44 anchor references, 11 discovery links, shared extraction finalized |
| `python3 -B -m unittest discover -s tests/dataset -p 'test_*.py'` | 9 tests, OK |
| `python3 -B -m unittest discover -s tests/runner -p 'test_*.py'` | 28 tests, OK |
| `python3 -B -m unittest discover -s tests/audit -p 'test_*.py'` | 39 tests, OK, including all six B1–B4 regression tests and their subcases |

Actual `freeze.json`, `execution/`, `preflight/workflow.json` and the owned runtime root remain absent. Only these two review files are edited by P4; no code/source finalization, real seal, credentials/config inspection, network, candidate/model calls, provisioning or delegation occurred. Synthetic temporary test seals, injected transport boundaries and rebased clocks are not real candidate/account/workflow evidence.

## Remaining parent-only actions

1. Create truthful `preflight/workflow.json`, referencing both passed review files and zero candidate POST starts.
2. Seal the actual archive once; run **`python3 verify.py --stage frozen` successfully before any credential provisioning or candidate request**. This real frozen-stage check has not been performed by P4.
3. Provision only the approved ephemeral `GO_API_KEY` and execute the immutable schedule once, one candidate at a time. The first real DeepSeek LOW case remains the sole counted access gate; stop without confirmation, fallback or privacy/route changes on denial.
4. Preserve truthful cleanup and execution evidence. If completed, do blinded semantic grading/adjudication, seal before unblinding, reproduce analysis/report and final review, and run the default saved-only final audit. An access block is still one attempted/71 unrun and an unresolved comparison, never a fast winner.

Prior nonblocking limitations remain: backend effort honoring/account access/upstream retries/cache behavior are UNVERIFIED; GLM default `clear_thinking` may ignore historical reasoning server-side despite preserved client wire messages; direct-harness times are not historical CLI times; six task clusters/small p90 subsets limit inference; Python/runtime/cache validity is trusted, while actual workers explicitly use `-I -B`. None is changed or hidden by this pass.

## Superseded initial review — historical record only

**Everything below records the initial blocked version, including its old line numbers, 33-test result, and proposed fixes. Its blocking statements and recommendations are superseded by the current pass and B1–B4 resolution evidence above.** Preserved to show exactly what the continuation resolved; do not treat the historical sections as current workflow attestation or outstanding blockers.

Artifact root: `~/VSCode/Lab/evals/researcher-eval-20261007T021014Z`.
Runtime root: `/private/tmp/opencode/researcher-eval-20261007T021014Z`.
Only `preflight/review.md` and `preflight/review.json` were authored by P4. No implementation/source edits, finalization, real seal, candidate calls, credentials/config inspection, network, installs, or follow-up agents. Existing offline tests used their own temporary fixtures; their synthetic seals/transports are not real workflow or access evidence.

## Observable checks

Help was inspected for dataset/verify/runner/analysis; Python help confirms `-B` suppresses import bytecode and `-I` implies ignoring Python environment variables. Unittest discovery help confirms the test selectors.

Commands run from the artifact root:

| Command | Observed result |
| --- | --- |
| `python3 dataset.py verify --require-finalized` | PASS: six exact tasks, 36 checks, six U keys, 18 canonical + four native bodies, 53 quotes, 44 anchor references, 11 discovery links, shared extraction finalized |
| `python3 -B -m unittest discover -s tests/dataset -p 'test_*.py'` | 9 tests, OK |
| `python3 -B -m unittest discover -s tests/runner -p 'test_*.py'` | 28 tests, OK |
| `python3 -B -m unittest discover -s tests/audit -p 'test_*.py'` | 33 tests, OK |

Read-only inspection also found: saved schedule equals `runner.make_schedule()`; actual `freeze.json`, `execution/`, `preflight/workflow.json`, and the declared runtime root are absent. These are observations before this review, not a parent workflow attestation. No frozen/final stage was represented as passed.

## Blocking issues — route to audit owner P3

### B1 — Actual finalized gold cannot pass the frozen audit

**Locations:** `verify.py:56–58,303–309,779–791`; correct dataset evidence contract at `dataset.py:149–176,480–488`.

The auditor uses HTML-unescaped whitespace-only membership for gold quotes, whereas the actual retained extraction contains link destinations and the research evidence quotes contain Markdown presentation. A read-only loop over all actual gold evidence found **23/53 failed memberships** using `verify.normalized(quote) in verify.normalized(saved_text)`. The first scored quote already fails:

`T1/C1`, `dataset/sources/GH-V.extracted.txt`: `GitHub recommends that you use the \`X-Hub-Signature-256\` header, which uses the HMAC-SHA256 algorithm.`

Other failures include linked prose, inline code, emphasis, and quotation-mark presentation. Dataset verification succeeds because its evidence-only normalizer handles these while leaving archived bytes/content hashes untouched. Consequently `verify.py --stage frozen` will fail on the actual dataset once a real seal exists; the synthetic fixtures did not exercise it.

**Required fix/test:** implement compatible conservative evidence-only presentation normalization independently in the auditor, including source-quote checks in grading. Keep raw/extracted/hash text unchanged and preserve literal globs/operators/escaped punctuation. Test all actual factual and U evidence plus negative altered-word/negation tests; exercise the actual finalized dataset through frozen-stage validation inside an owned test fixture, not by sealing the real archive during implementation.

### B2 — Linked truncated previews are forbidden and not independently validated

**Locations:** exporter `runner.py:795–809`; auditor `verify.py:724–738,755–758,779–791`.

When a fetched full body differs from its model preview, the runner writes `sources/sN-visible.txt`, links it as `candidate_visible_path`, and seals its hash. The auditor's allowed-artifact set contains only `source_path`, never `candidate_visible_path`. Any such honest export therefore fails `unreviewed extra grader input artifact`. The auditor also never independently checks that the linked preview equals that candidate's actual saved model text. Merely permitting arbitrary extra files would weaken blindness. None of the 22 current frozen bodies exceeds 256 KiB, but other allowed fetched pages can, and truncation is explicitly part of the frozen contract.

**Required fix/test:** accept only explicitly linked, opaque, case-contained previews; validate their sealed hash, leak constraints, and exact provenance against the corresponding successful fetch/model-text artifact. Support the equal-full/preview path too. Add runner-export-to-auditor integration tests with an actual truncated fetch, and negative wrong-preview/unlinked-extra/outside-case-path/hash tests. Preserve full versus candidate-visible evidence distinction; no re-fetch substitutes.

### B3 — Mechanical reconstruction ignores rejected calls, exact tool scope, and content deduplication

**Locations:** runner `runner.py:322–372,710–759`; URL contract `webfetch.py:16–26,135–153`; auditor `verify.py:83–98,167–170,552–556,739–753`.

Read-only in-memory reproductions using the actual T1 task and `runner.mechanical_compliance`:

| Saved behavior | Runner source/tool compliance | Auditor reconstruction |
| --- | --- | --- |
| Rejected `webfetch` of `https://evil.test/secret` | false / true | true / true |
| Rejected `shell` call, no URL | false / false | true / true |
| Two allowed URLs with identical extracted content | one distinct page | two distinct pages |

The auditor drops error-bearing fetches from source compliance and defines tool compliance only by fetch/step counts. It does not reconstruct actual names, function type, argument schema, over-cap call requests, or terminal returned calls for the mechanical flag. Thus it rejects truthful false flags as fabricated, while equivalent edited true flags evade these mechanical checks. Its URL validator also uses the broader dataset patterns without the narrower frozen webfetch allowlist: it accepts `https://docs.github.com/en/rest` for T1, while the actual tool rejects it. It does not reconstruct `requested_tool_calls`. The runner groups canonical aliases **and identical extracted content**; the auditor groups canonical URLs only.

**Required fix/test:** independently reconstruct the runner's complete mechanical contract from native assistant calls/history plus all attempted requested/final/redirect URLs, including denied attempts and beyond-cap calls. Enforce frozen HTTPS host/path scope, not just count bounds or the broad archive patterns. Match canonical/content equivalence without counting mirrors twice; validate optional counts. Rejected attempts must remain auditable and disqualifying as appropriate, not disappear or cause a truthful export to be ungradeable. Add end-to-end rejected-name, malformed/extra arguments, denied request/redirect, broad-but-out-of-tool-scope URL, step-eight/cap-overflow, and identical-content tests with negative tampered compliance cases.

### B4 — Auth/entitlement gate classifications do not agree

**Locations:** runner `runner.py:202–206,584–590`; auditor `verify.py:630–639`.

Actual classifier/regex evaluation demonstrated these JSON denials are access blocks in the runner but rejected as missing native denial evidence by the auditor: HTTP 401 `Invalid API key`; HTTP 403 `Forbidden`; HTTP 400 `A Go subscription is required`. The runner accepts every 401/403 plus explicit subscription/invalid-key/privacy/region/auth terms for other errors. The auditor only accepts 400/401/403 with a narrower text regex. Its status whitelist also differs from the runner's broader explicit-error status policy. A legitimate first-case auth failure can therefore stop safely at one attempt/71 unrun but fail the required honest-block audit.

**Required fix/test:** independently validate the same frozen gate classification against saved status/native payload, without requiring an extra confirmation call. Add invalid-key 401, generic forbidden 403, subscription/entitlement and region/privacy denials, plus non-access-error negatives. One client POST and 71 honest unrun rows must remain mandatory; do not convert ordinary failures into comparisons or change auth/privacy/routes.

## Requirement evidence and findings

| Requirement | Evidence / finding |
| --- | --- |
| Direct Go, six literal effort settings, thinking enabled, 16384, no sampler override | `protocol.json:4–11`; `runner.py:30–34,172–199`; six-request serialization test. Client selection implemented; backend honoring UNVERIFIED. |
| Native reasoning/tool history, fresh states, public inputs only | `runner.py:236,305–310,624–643`; history/request-prefix tests. Worker spec contains public task and URL/hash metadata, no gold/rubric. Model wire receives only system/prompt/tool schema. |
| Eight calls, final tools absent, 400 words, 180 seconds, sequential/once-only, no retries/warmups/fallback | `runner.py:229–230,260,312–325,404–435,555–611,642–650`; protocol and runner tests. Word overrun is a compliance failure, not evidence of qualification. |
| First real DeepSeek LOW gate; one attempt/71 skips; no settings or route changes | Seeded schedule equality and tests; `runner.py:584–598`; blocked by B4 for audit compatibility. No actual access proof exists yet. |
| Ephemeral auth; no external credential imports/debug logs; owned writes/process cleanup | `runner.py:162–169,183–199,438–498,614–686,878–890`; mocked auth-redirect/secret and owned-process tests. Minimal child env, key popped, auth POST has no redirects, runtime/execution scans contain no secret values. This is reviewed behavior, not live cleanup proof. |
| Token-free first-party webfetch, public DNS pinning/TLS, bounded validated redirects | `webfetch.py:135–233`; denial, DNS/TLS, redirect and bounds tests. Network enforcement implemented; independent mechanical reconstruction blocked by B3. |
| Whole archives/shared generic extraction, semantic asides/inline prose, real anchors/links, honest native mappings | Finalized verification; `webfetch.py:68–128`; `dataset.py:418–541`; callout/adjacency/mirror tests. Raw hashes and whole-body mirror hashes are not claimed equal. Auditor blocked by B1. |
| Retained raw/full/actual preview and required-source drift stops | `runner.py:349–377`; `webfetch.py:219–229`; source drift and preview tests; `protocol.json:13`. Required text mismatch stops current/further cases, raw-only mismatch is recorded. Blind preview audit blocked by B2. |
| Freeze code/data/system/tools/protocol/schedule/archive/API/tests/review/workflow | `runner.py:501–549`; `verify.py:187–340`; freeze tests. Runner includes all preflight files and parent workflow, excludes bytecode/generated outputs. Parent workflow/seal/frozen verification remain pending, not fabricated. |
| Blind semantic grades, fetched versus frozen sources, claim citations/anchors, seal before identity join | `runner.py:762–856`; `verify.py:642–898`; `tests/audit/README.md:87–126`. Semantic judgment is disclosed AI review, never keyword truth. Entailing citation requires actual fetched canonical page and fetched evidence, not an unfetched bibliography. B1–B3 must be fixed before this pipeline is credible. |
| Eligibility, qualified-only medians/p90, paired coverage/task bootstrap/LOTO/speed margin; no price/prior ranking | `analysis.py:32–242`; `protocol.json:35–41`; statistics tests. 10/12, each task, zero required contradictions/critical errors; six supported/cited facts + U/instructions/two canonical sources/no extras. Ordinary median, nearest-rank p90 with n, six-block/four-task joint coverage, 10000 whole-task draws, 10% speed margin and sensitivity. Fast failures excluded. |
| Saved-only verification; stage results are not final completion; honest blocked comparison unresolved | `verify.py:901–965`; `analysis.py:245–251`; interruption/missing-stage/gate tests. Auditor imports no API/auth/process-control modules or candidate runner. Default final requires saved later-stage evidence and report/final review. No final outcome is asserted here. |

## Nonblocking limitations / remaining parent obligations

- Public API contract excerpts and model metadata in `api-evidence/` establish documented fields/IDs only; P4 did not independently re-fetch them. Account entitlement, effective upstream effort, server-side retries/backend changes and caches remain UNVERIFIED. Mocks do not establish these facts.
- GLM default `clear_thinking` can ignore historical reasoning server-side. This is explicitly acknowledged in `api-evidence/contracts.md:32–36`; exact native messages are preserved on the client wire, but equal server retention is not proven. Acceptable without an undocumented common field or extra probe. Carry this limitation into the report.
- The direct nonstreaming supervised harness differs from the historical OpenCode CLI (`protocol.json:41–43`, `plan.md:13`); rank only these new times. Six tasks and small qualified subsets limit generalization/p90 precision; bootstrap intervals are exploratory.
- Python `-I` ignores `PYTHONDONTWRITEBYTECODE`, but the actual worker command also has **`-B`** (`runner.py:642`) and the runner sets `sys.dont_write_bytecode` before importing webfetch (`runner.py:24–26`). No newly required artifact-bytecode write was found. Bytecode is excluded from freeze; Python/runtime/cached-module validity remains a trusted runtime assumption, not a frozen interpreter snapshot.
- After fixes and a passing review, the parent must create truthful workflow evidence, seal once, pass `verify.py --stage frozen`, then provision only the approved ephemeral Go key and perform the immutable schedule. Later blind grading/adjudication seals, unblinding, report/final review, actual cleanup, and default audit are still future work. This review supplies no permission to bypass the blocking issues.
