# Independent pre-execution review

**PASS — B1 and B2 resolved; parent freeze still required before candidate dispatch.** The narrow final recheck passes all eleven offline verification modules (122 discovered tests). Candidate dispatch is not approved by this unsealed review. This review made no network or inference requests and did not inspect credential stores, environment keys, or logs. Only this report and its JSON counterpart were authored.

## Narrow final recheck

- **B1 resolved:** `preparation/finalize.py:48-60` now attaches `study_incomplete` and `study_stop` to every normalized record. Record hashes bind that state into the grading seal and saved analysis inputs. `analysis/statistics.py:13-58,242-260` honors both fields and all seven mandatory statuses, even with 648 attempted trials; both suites then have empty qualified sets and no preference. `tests/analysis/test_analysis.py:149-243` exercises final-trial mandatory failures, completed-final-trial cleanup/hygiene stops, ordinary timeout/nonblocking outcomes, and saved-report/hash audit reproduction. All eleven analysis tests pass.
- **B2 resolved:** `gold/web/gold.json:167` now requires only exact-by-default synchronization and removal of extraneous packages. `tests/webtasks/test_verify.py:114-129` protects the visible-prompt/default-removal criterion and correct-fixture alignment. All sixteen web-task tests pass.
- `preparation/finalize.py:159-164` refuses a running execution index even with 648 terminals and requires `credential_hygiene.secret_matches == 0` before grading. Three additional in-memory guard checks rejected running, leaking and missing-hygiene fixture indexes before any broker call or credential read.
- `harness/core/runner.py:97-102` classifies the historical model-turn rejection and current assistant-prefill/user-tail rejection as protocol errors. The existing core regression exercises both without retries; all 27 core tests pass.
- `python3 -B -m preparation.freeze --verify`: **PASS, 11 modules, unsealed**. Verification outcomes independently counted 122 discovered tests: 14 web-tool, 17 code-tool, 27 core, 16 web-task, 18 code-task, 10 grading, 11 analysis and 9 integration. No broader task-semantic review or live source fetch was repeated. Generated sandbox proof uses the same policy; temporary absolute probe paths do not represent a policy change.

## Original findings — preserved history, both resolved

The following records describe the original blocked review and source line numbers at that time, not current unresolved defects. Its eleven-module run passed 117 tests.

### B1 — A mandatory stop on trial 648 can still publish a preference

- `preparation/run.py:86-89,102` records a mandatory fault or supervisor-cleanup fault as an incomplete study, even when it occurs on the final scheduled trial.
- `preparation/finalize.py:205` passes records to analysis without passing that study-stop state. `analysis/statistics.py:194` determines incompleteness only from unattempted trials or unresolved unrun review IDs. With all 648 attempted, neither condition necessarily holds.
- Offline reproduction used artificial grading fixtures only: set the last of 648 records to `auth_error`, `completed=False`, seal the remaining semantic grades and required reviews, and call `analyze(..., draws=10)`. Observed: `n_attempted=648`, `incomplete=False`, and a `gemini-low` preference in both suites. These are fixture outputs, not candidate results.

**Required correction:** propagate the execution-level mandatory-stop/cleanup/hygiene state into the sealed analysis inputs and suppress preferences for any incomplete study, including a final-trial fault. Add an offline regression covering that boundary and reproducible report auditing.

### B2 — W09 has an essential requirement absent from its question

- `tasks/web/tasks.json:10` asks for uv sync's default removal behavior, not its opt-out flag.
- `gold/web/gold.json:167` nevertheless includes `--inexact is the opt-out` in essential scored unit U3. Its attached quote establishes the default removal behavior, not the flag.
- The fully correct and alternative fixtures at `gold/web/gold.json:176,181`, and the reference answer at line 174, omit `--inexact` while claiming full coverage. A grader following the whole required-unit description can therefore reject an answer that satisfies the visible question and the package's own correct fixture.

**Required correction:** remove the flag from the required unit or explicitly request it in the prompt and align the reference evidence and fixtures. Do not leave this as discretionary hidden grader interpretation.

## Verification actually performed

- `python3 -B -m preparation.freeze --verify`: PASS, eleven modules, **unsealed**. Repeated verification after the integration/controller tests appeared also passed: 14 web-tool, 17 code-tool, 27 core, 15 web-task, 18 code-task, 10 grading, 7 analysis and 9 integration tests.
- Production sandboxed code `dispatch("read", ...)` exercised all 36 authored read windows: all 73 gold quote spans were visible without core truncation. No snapshot code or tests were executed.
- Production web extraction replayed the nineteen saved public source bodies offline: all 68 content quote checks matched after whitespace normalization. The remaining URL criterion is archived redirect metadata. This is extractor compatibility, not a fresh accessibility/search observation.
- Actual production-policy denial probes passed for outside-file reads, snapshot writes, shell execution and network connection; the proof discloses permitted unconnected socket allocation and runtime-read exceptions.
- In-memory `preparation.finalize.call_batch` → base seal → independent review → final seal exercised artificial 648-record fixtures: 647 semantic grades and 162 planned reviews; review payloads excluded original grades. Controller generation and saves were mocked; zero network requests/file writes. This verifies interface/hash compatibility, not live grading quality.
- Source inspection checked Gemini nonempty user tails, batched tool-result ordering, full native assistant history, literal effort values, tool-free final steps, once-only reservations/send starts, direct transport without client retries, 240-second owned-process-group supervision, visible evidence caps/pagination, fixed explicit Exa selection, question-only candidate inputs, blind support-eligible evidence, preselected review IDs, pre-unblinding seals, and separate 10,000-draw suite bootstraps.

## Boundaries

The public-source archive and root-license/source-manifest checks pass. Mutable historical source contents remain explicitly UNVERIFIED; post-cutoff UTC retrieval timestamps are not backdated. Existing saved Exa validation reports HTTP 200/eight results, service-normalized response scope and unknown locale; it was not repeated here. No credential material was read, and live credential availability is not independently certified by this reviewer. Controller usage/version/upstream attempts remain unknown as disclosed by its text-only broker contract.

Real candidate execution, compatibility gates, semantic grading and execution accounting audits are **not executed**. Passing offline integrity tests and authored fixture labels do not establish semantic truth or human calibration. B1/B2 corrections and their offline verification are complete. The parent must seal the final inputs before any candidate call; this review does not perform or certify that future seal.
