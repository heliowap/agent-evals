# Independent restart preflight recheck

## Current final decision — 2026-10-07T10:06:26.859568+00:00

**PASSED. R1, R2 and R3 are resolved; no remaining preflight blocker.** The final recheck was restricted to the last two precise corrections: exact parent receipt provenance and the runner integration fixture's missing receipt. No unrelated redesign, candidate experiment or additional test requirement was introduced. Earlier decisions below are historical only. `preflight/review.json` contains `passed: true` and the current SHA-256 map of all 80 meaningful inputs.

- **Exact provenance restored:** `verify.py:631` requires `credential_source` exactly `parent read-only selected opencode-go integration credential`, matching unchanged `preflight/provision.py`. Audit fixtures retain that schema and carry separate explicit synthetic/fixture-only markers. Independently changing the source to the exact previously accepted `Different provider, no selected Go credential` now fails both collected and default audits, **with and without public-document matches**, even after resealing the synthetic final-review receipt. Missing receipts and positive secret-match counts also fail; restoring the valid synthetic receipt passes. No real key was read, supplied or scanned in these fixtures.
- **Integration fixture corrected:** `tests/runner/test_runner.py:710-722` now writes an existing-schema receipt, explicitly marked synthetic, before the collected audit. Both formerly failing access-blocked/completed subcases pass in the full runner suite. Production `runner.py` is byte-identical to the already-passing R1/R2 recheck.
- **Complete observable proof:** actual unmodified suites ran through the previously documented private-temporary-directory allocation wrapper: **12 dataset + 33 runner + 59 audit = 104 passed, zero failures/errors/skips**. `python3 -B dataset.py verify --require-finalized` exited **0** again: same six tasks/gold, 22 fresh source bodies/22 successful attempts, 53 quotes, 44 anchors, 11 discovery links and finalized shared extraction. Source/task/protocol/metadata hashes remain unchanged; prior reviewed requirements are reused on that byte proof.
- **Boundary:** all original A/P files were byte-identical before/after verification. Only these two review files are delivered; no actual workflow, freeze, execution directory or study runtime exists. Zero candidate POSTs, credential-store accesses, network/model tools, agents or actual-root seal/execute operations occurred.

Preparation review is complete. The parent may now create its truthful workflow and seal the actual reviewed inputs, then must run the actual-root frozen-stage audit before its authorized provisioning/execution. This receipt does **not** claim that workflow creation, actual sealing, actual frozen auditing, parent exact-key scanning, candidate execution or cleanup has already occurred. Their runtime evidence remains pending; backend effort honoring and semantic grading truth remain unverified as previously disclosed.

## Historical first recheck — 2026-10-07T10:02:31.893988+00:00

**NOT PASSED. R1 and R2 are resolved; R3 remains partial.** This recheck examined only those three original findings and reran the complete offline proof. No new design/review scope was added. The original review below is retained as historical evidence, not a statement that R1/R2 remain open. `review.json` contains the current decision and all 80 current meaningful-input hashes.

### Exact boundary rechecks

**R1 PASS.** Both original HTTP-400 forms (`reasoning_effort is not supported`, `Unrecognised request parameter: reasoning_effort`) now return true in both runner and auditor. Generic malformed-request/`invalid_request_error` and integer-type errors remain false. Four independent actual-`run_case`/`run_study` probes injected each form at **case 7, step 1 and step 7**. Every probe launched only cases 1–7, saved seven attempts and 65 `not_run_compatibility_block` rows, retained six passed counted gates and a case-7 linked stop. Synthetic POST starts were exactly 7 or 13 respectively; actual HTTP POSTs were zero. The corrected collected auditor accepted each honest prefix. These probes used fixture-only seals under approved private temporary directories, never the actual study root/runtime.

**R2 PASS.** The exact former failing three-case saved-audit boundary was independently reproduced using the actual runner with injected native bytes: HTTP 400 `unknown field thinking` and HTTP 403 `Forbidden`. Original bytes remained unchanged, native usage/completion totals remained unknown, collected audits passed, and default audits returned `honest_compatibility_block`/`honest_access_block` with `completed_comparison: false`. A successful inference response changed to non-JSON still failed as `invalid JSON native response`. `verify.py:232-248` supplies only an in-memory classification wrapper for unsuccessful non-JSON HTTP responses; no invented response or usage is persisted.

**R3 PARTIAL — exact selected-Go provenance was weakened.** Missing receipts and positive `secret_matches` fail collected and default audits, both with and without the public-document exception. An omitted final-review receipt hash also fails. However, `verify.py:631-636` now accepts **any nonempty `credential_source`**, instead of the existing producer's exact value `parent read-only selected opencode-go integration credential`. Changing that field to `Different provider, no selected Go credential` and resealing the synthetic final-review receipt still passed collected/default audits in both cases, including `completed_comparison: true` for a completed fixture. Thus the original R3 requirement for the existing exact-selected-Go-key receipt schema is not fully restored; this is an existing provenance requirement, not an extra hypothetical test request.

Required remaining correction: enforce the producer's existing exact `credential_source` value. Synthetic receipts can preserve that schema while being unmistakably marked synthetic in a separate fixture-only metadata field/comment; they must not weaken the production verifier's acceptance rule. Reuse the existing receipt-tampering regression for this specific source-field mismatch.

### Combined offline proof — not all passing

The complete actual, unmodified suites ran with the same private-temporary-directory allocation wrapper as the first review: **12 dataset + 33 runner + 59 audit = 104 tests**, no skips. Dataset and all 59 audit tests passed. The runner suite had **two errors**, the `access_blocked` and `completed` subcases of `tests/runner/test_runner.py:test_independent_saved_only_auditor_on_runner_gate_and_complete_fixtures` at line 711. Both failed with `missing collected stage artifact: execution/parent-provisioning.json`. This integration fixture must write the explicitly synthetic existing-schema parent receipt before its collected audit; the production requirement should not be relaxed. Therefore the requested passing 104-test preparation proof does not yet exist.

`python3 -B dataset.py verify --require-finalized` exited **0** again: unchanged six tasks/gold, 22 fresh bodies/22 successful attempts, 53 quotations, 44 anchors, 11 discovery links and finalized shared extraction. Its bytes and every other source/task/protocol/metadata input remain identical to the first review. Only the six owner-fixed files changed since the original hash map: runner, verifier, runner tests, audit README, audit fixtures and restart audit tests. All original A/P files were byte-identical before/after this recheck's commands; only the two review files are delivered. No actual workflow/freeze/execution/runtime exists; no credential access, model/network call, agent or actual seal/execute occurred.

The unchanged requirement evidence below is reused by verified byte hashes. Once the two precise R3-related corrections above are made and the offline proof passes, the parent still owns truthful workflow creation, actual sealing and actual-root `verify.py --stage frozen`; none was fabricated or performed by this reviewer.

## Historical initial review — superseded only as stated above

**Initial decision at 09:53 UTC: NOT PASSED.** At that time all 99 existing offline tests passed, and the fresh finalized dataset passed verification, but three independently reproduced boundary failures remained. The current recheck decision and resolved findings are above. This is a preparation review, not a frozen-stage approval or study result.

Reviewed on 2026-10-07; A is `researcher-eval-20261007T093207Z`, compared read-only with P, `researcher-eval-20261007T021014Z`. Ownership is only this file and `preflight/review.json`. The JSON receipt contains `REVIEWEDSHA256` for all 80 pre-existing inputs, including all archived bodies.

## Blocking spec findings

### R1 — A native unsupported field can launch the remaining study

Location: `runner.py:209-220`, `runner.py:315-320`, `runner.py:620-631`; independently contrasted with `verify.py:164-197`.

For HTTP 400 and `{"error":{"message":"reasoning_effort is not supported"}}`, the actual runner's `parameter_error` returns **false**, while the independent auditor's `saved_parameter_denial` returns **true**. `Unrecognised request parameter: reasoning_effort` has the same discrepancy. These are explicit parameter diagnostics, not generic HTTP-400 errors.

An offline integration used the actual `run_case` and `run_study`, injected transports, an empty key and a synthetic sealed root under `/private/tmp/opencode`. After six successful counted gates, case 7 received the first payload. The runner saved `provider_error`, launched cases **8 through 72**, and saved `study_status: completed`, `attempted_cases: 72`, `stop: null`. The independent collected audit rejected it with `collected: native block classification/status mismatch`. No real HTTP POST occurred.

Required correction: recognize these explicit native field diagnostics at the runner boundary without promoting generic `invalid_request_error`, malformed input or ordinary 400s into compatibility blocks. Add actual runner/controller regressions at a later case and step; require exactly the attempted prefix, linked stop, honest suffix and no later launches. Extend `tests/runner/test_runner.py:test_parameter_errors_require_native_explicit_http_diagnostic` and `test_native_rejection_any_case_any_step_stops_without_replay`; retain independent audit agreement tests in `tests/audit/test_restart_audit.py`.

### R2 — Truthfully retained non-JSON native blockers cannot pass saved auditing

Location: `runner.py:305-318` and `verify.py:219-225,719-727`.

The runner deliberately retains a non-JSON HTTP error body and classifies it using a local error-message wrapper. Its existing `tests/runner/test_runner.py:test_non_json_native_parameter_and_access_errors_keep_response` passes for HTTP 400 `unknown field thinking` and HTTP 403 `Forbidden`. However, the collected auditor unconditionally parses the linked response as JSON.

An otherwise valid synthetic three-case compatibility prefix, with native response bytes `unknown field thinking` retained unchanged at its linked response path, failed with `collected: invalid JSON schema: execution/cases/C003/requests/1-response.json`. Consequently analysis/default final auditing cannot accept this honest native block.

Required correction: audit retained native error bytes for unsuccessful HTTP responses, independently reproduce the runner's classification from those bytes, preserve null usage, and still require valid JSON for successful inference. Add end-to-end actual-runner collected/default-block regressions for the already supported non-JSON compatibility and access errors. Do not rewrite native bytes into invented JSON evidence.

### R3 — Parent exact-key proof is conditional, not a collected/default prerequisite

Location: `verify.py:600-610,903-910,1286-1288`; producer reviewed at `preflight/provision.py:49-61`.

The requested collected/default exact-selected-Go-key receipt is checked only when `public_document_paths` finds an exempt public-document file. With no exemption, `execution/parent-provisioning.json` can be absent and the collected audit still returns `ok: true`. A fully populated synthetic completed/graded/analysis/report/final-review fixture also passed the **default final audit** without that receipt, returning `completed_comparison: true`.

Required correction: validate the existing parent receipt schema for every collected/default study and seal its bytes in final review, independently of public-regex matches. The existing producer already writes the relevant fields (`credential_source`, false copy/store-access flags, true ephemeral-environment flag, zero `secret_matches`/`caller_retries`, positive `scanned_file_count`, ordered UTC timestamps). No new credential property, credential read by the verifier, or blanket safety claim is needed. Add absence/tampering regressions both with and without the public exception in `tests/audit/test_restart_audit.py`; update only synthetic fixture receipts as necessary.

## Requirement evidence

| Requirement | Observed evidence / verdict |
|---|---|
| Exact six tasks/gold, no old answers in ranking | **PASS.** Tasks SHA-256 `390c481be89a5cfa35506b8c5dee8b3aa405c5f96c8ca060bb39c49ad2e35d34`; gold `fc8e2facfb149ced80cfb526550169df20ac251f84b6ce5291cc23c22d3077d9`; both byte-identical to P and bootstrap proof. Scope/restart exclude previous cases. |
| Fresh whole-source archive | **PASS.** Actual saved-only verifier: 22 fresh bodies/22 successful attempts, 18 canonical pages/4 native Markdown aliases, 53 factual/U quotes, 44 HTML anchor references and 11 discovery links. Shared extraction finalized; mirror non-equivalence and Node contradiction/Compose full paragraph retained. |
| Minimal envelope, no `thinking`, literal efforts/native history | **PASS.** Actual six-configuration × eight-step runner test checks every saved/wire body; `max` remains literal, step 8 removes tools, native assistant reasoning/tool history remains unchanged. Protocol omits the key. Backend honoring/GLM server retention remain explicitly UNVERIFIED. |
| First six counted gates; no smoke/retries/fallback | **PASS for covered diagnostics; FAIL R1.** Gate identity/status and once-only leases/controller reservation are tested. Ordinary generic 400s remain distinct. |
| Any-case/step native stop, honest prefix/suffix/index | **FAIL R1/R2.** Covered native forms and late case/step stops pass existing tests, including truthful POST counts. Uncovered explicit forms continue; non-JSON honest blocks cannot audit. |
| Narrow public Authorization correction | **PASS for reviewed implementation and existing regressions.** Every regex match is hashed; only linked successful/error-free/untruncated D1-R canonical/index.md full/model `.txt` equal to this archive can qualify. Requests/responses/history/raw/tool-result paths are excluded; unlinked/header/unknown/truncated/modified/Bearer/sk examples are rejected. Actual D1-R and D1-R-MD each have three matches, all hash `81d54facb40f6897ee428462a51dbaa0fde638e5b023f15811d05d66923b4e19`; full text equals fresh shared extraction. No whole-old-document hash exception. Parent-proof default enforcement fails R3. |
| Parent provisioning / worker bounds | **CODE-REVIEWED; runtime proof pending.** Parent opens only selected Go integration through read-only SQLite, refuses ambiguous keys, supplies a minimal ephemeral environment, redacts output and scans exact key without persisting it. Worker has no store reader or filesystem tool; source hashes, not gold, enter specs. Writes target A/new runtime; P references are read-only bootstrap/provenance/tests. No provisioning invocation or credential inspection occurred. Parent must retain its explicit frozen-stage/auth approval boundary. |
| Only webfetch; pinned first-party redirects/drift | **PASS offline/code.** Exact task allowlist, public-address validation, pinned address with hostname TLS, every redirect validation, authenticated POST no-follow, actual whole-page extraction and required-source drift stop tested. No extraction-specific gold output. |
| Schedule/budgets/statistics unchanged | **PASS.** Schedule bytes equal P; seed `20261007021014`, statistics `20261007021015`, new blind seed `20261007093207`. 72 balanced cases, 12/configuration, each position twice, 400 words/8 steps/16384 tokens/180-second supervised serial wall limit. Six-whole-task/10000-draw bootstrap, 10-qualified eligibility, zero contradictions/critical errors, quality-first speed margins and no-price decision remain unchanged. Failed latencies are diagnostic only. |
| Blind grading integrity | **PASS offline/code.** Two opaque 36-case shards; identity/time/usage/path leak rejection; fetched versus frozen references and exact candidate preview provenance; full URL/anchors and canonical-or-identical-content deduplication; six checks/U/extras/critical errors separate; initial grades/adjudication/seal-before-unblind. Semantic truth is not claimed by tests or quote membership. |
| Final default completion | **PARTIAL; FAIL R2/R3.** Existing tests require all completed grades/report/reproduced analysis, or truthful native block with no winner/null qualified latency/`completed_comparison: false`; ordinary incompleteness fails. The two uncovered evidence paths prevent approval. |
| Freeze coverage | **CODE-REVIEWED; NOT SEALED.** Actual `frozen_files` includes runnable code, all datasets/archives/tests/API evidence/research/preflight bootstrap/provision/catalog/guide/review and required parent workflow/restart. Actual parent workflow and freeze are intentionally absent. Parent must create truthful workflow, seal only after a passing corrected review, then run the actual-root frozen audit. |

## Commands and observed results

Help was run first: `python3 -B -m unittest -h`, `python3 -B dataset.py --help`, `python3 -B dataset.py verify --help`, `python3 -B verify.py -h`.

The three **actual, unmodified** test suites were loaded and run through `unittest.defaultTestLoader.discover('tests/<package>', pattern='test_*.py')` and `unittest.TextTestRunner(verbosity=2)` in separate `python3 -B` subprocesses, with `TMPDIR=/private/tmp/opencode` and `PYTHONDONTWRITEBYTECODE=1`. Only `tempfile.TemporaryDirectory` allocation was redirected to `/private/tmp/opencode` (including tests with an explicit original-root `dir`), so no fixture was written into A/P. No production code/classifier/transport behavior was patched by the reviewer. Counts: dataset **12**, runner **33**, audit **54**; **99 passed, 0 failures, 0 errors, 0 skips**.

`python3 -B dataset.py verify --require-finalized` exited **0**, with the archive/quote/anchor/link/finalization proof above. Before/after SHA maps proved all 80 existing A files and all 2453 P files byte-identical across the suite and dataset command. P's complete sorted path/hash-map digest is `f5c1f0a28c899b89ff060d60e451c64b149d51c793935ca203722a5b81bbb513`.

Classifier reproduction (read-only, no network):

```sh
python3 -B - <<'PY'
import runner, verify
for message in ('reasoning_effort is not supported',
                'Unrecognised request parameter: reasoning_effort'):
    payload = {'error': {'message': message}}
    print(message, runner.parameter_error(400, payload),
          verify.saved_parameter_denial(400, payload))
PY
```

Observed both rows: `False True`. The full actual-runner/controller late-case probe additionally established the 65 improper later launches, not just a helper disagreement.

Saved-audit boundary reproductions (synthetic files only under approved temporary directories):

```sh
TMPDIR=/private/tmp/opencode python3 -B - <<'PY'
from pathlib import Path
import sys, tempfile
import analysis, verify
sys.path.insert(0, str(Path.cwd() / 'tests/audit'))
import fixtures as f
from test_restart_audit import save_failure
with tempfile.TemporaryDirectory(dir='/private/tmp/opencode') as directory:
    root = Path(directory)
    f.frozen(root); f.collected(root)
    name = save_failure(root, 3, 1, 'compatibility_blocked',
                        {'error': {'message': 'unknown field thinking'}})
    row = f.read(root, name)
    (root / row['requests'][0]['response_path']).write_bytes(b'unknown field thinking')
    try:
        verify.audit(root, 'collected')
    except verify.AuditError as error:
        print(error)
with tempfile.TemporaryDirectory(dir='/private/tmp/opencode') as directory:
    root = Path(directory)
    f.complete(root)
    print('receipt exists:', (root / 'execution/parent-provisioning.json').exists())
    print('collected:', verify.audit(root, 'collected'))
    f.write(root, 'analysis/results.json', analysis.analyze(root))
    f.final_review(root)
    print('final:', verify.audit(root))
PY
```

Observed: invalid native-response JSON; absent receipt; collected `ok: true`; then default final `ok: true`, `completed_comparison: true`. These are deliberately synthetic probe outputs, not A's study evidence.

## Standards / limitations / boundary

No additional documented-standard finding is asserted; the blockers above are behavior/spec failures. The directory is not a Git checkout: P's saved files, not a fabricated commit/issue, supplied the comparison. No agents were spawned and no unrelated smell/refactoring review was added.

At both suite boundary observations, actual A had **no execution directory, freeze.json, parent workflow or study runtime**. This reviewer made **zero actual candidate POSTs**, used no model/catalog/network tools, inspected no credential store, invoked no parent provisioning, and performed no actual-root seal/execute/blind export/analysis. Fixture-only seals, launches, grading and process-cleanup tests are not production approvals. Existing catalog-current.json is the parent's dated tool/official-Go-document observation; it was read but not independently re-fetched here. API-vendor excerpts accurately retain their original day-level retrieval date/reuse annotation. Account access, upstream retries, backend effort honoring and future runtime cleanup remain unverified.

Only the two review files are delivered. After R1–R3 are corrected, rerun the actual full suites and finalized dataset proof and obtain an updated independent review. Do not treat passing existing tests, this failed receipt, or absent production evidence as authorization to seal or send candidate requests.
