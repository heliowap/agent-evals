# Recovery preflight review: PASS within limited scope

Approved controller SHA-256: `fb9c86b655eaed985142a1e45e040ad82a99b1b8d95ff85613edb2147a35ac66`.

Approval covers only the explicitly authorized 599 never-reserved slots, 50–648, after reconciling 48 indexed terminals to 49 durable terminals. It does **not** certify historical cleanup or authorize replay, extra probes, configuration changes or installations.

## Verified offline

- `python3 -B /tmp/folders/T/opencode/resume-research-eval.py --verify` exited 0: five fixture tests and the real audit passed, with 49 terminal trials, 347 client starts, valid native history, and zero candidate calls.
- All 9,076 frozen files remain unchanged. Trial 49 is completed, with its terminal hash matching its original record. Ledger, index and terminal records were unchanged by review.
- Thirteen additional in-memory rejection tests refused duplicate/nonprefix/unclosed reservations, duplicate terminals, missing/nonterminal records, prior mandatory stops, unrun records and inconsistent index counters. The existing terminal timeout is retained, never replayed.
- Eight tests executed the actual loop AST with only in-memory fake inference, credentials, receipts and writes. With only the historical limitation, all 599 new slots dispatch and final status remains incomplete. Each mandatory native fault or new cleanup/receipt failure stops further dispatch immediately: one simulated call, 598 `not_run_stop` records, no retries.
- Frozen finalizer normalization preserves the historical stop; frozen analysis returns no qualified or preferred winner. Counters match the original first-attempt-before-supervision policy.

## Historical integrity limitation

Trial 49's **original supervisor receipt is missing**. Historical wait/drain and the original interruption cause remain **UNVERIFIED**. No receipt, historical drain or historical wait is manufactured.

The matching-process absence check at `2026-10-08T12:58:08.672601+00:00` establishes only present-time absence, not historical cleanup or arbitrary unnamed descendant absence. The execution path repeats its audit under a controller lock; the original locked ledger independently prohibits duplicate reservations and starts.

The controller keeps `recovery_integrity_limit` separate from the local new-dispatch stop. It therefore permits safe, explicitly authorized new slots while leaving the final index `incomplete` with a `supervisor_cleanup_failure` stop even if all 648 slots are attempted. No qualified winner may be reported. Scores and speed remain descriptive. The final narrative must disclose the pause/gap, missing receipt and historical unknowns, including if a later mandatory stop becomes the immediate final stop reason.

## Operational scope and boundaries

The candidate path still uses the original frozen supervisor, public tasks, nine configurations, tools, 240-second budgets, native-history preservation, nonempty Gemini user tail and once-only client. Only orchestration outside the freeze changes.

The launcher creates a separate process session, detaches stdin, persists output in `execution/recovery/runner.log` and waits. It installs no daemon/service and changes no configuration. Before new candidates, the parent performs two authenticated metadata GETs against the frozen service base/version and Exa registration; no search or inference probe is added. Live metadata/auth availability was not tested in this review.

The reviewer did not call credential loading, service validation, execution or launching; inspect credential values, private account/quota data or private logs; make network/inference calls; spawn subagents; or modify the controller, frozen preflight or historical execution evidence. Only these two review files are created.
