# Code-suite gold and data audit

Verify from the evaluation root:

```sh
python3 -B -m tasks.code.verify
```

The command validates artifacts and runs only the verifier's own data-mutation
tests in `tests/codetasks`. It does not import, execute, compile, install, or run
tests from any snapshot. No candidate calls are made. Snapshots, manifests,
licenses and parent artifacts are unchanged.

## Frozen task allocation

| ID | Repository | Type | Bounded intent |
|---|---|---|---|
| C01 | click | flow/config | Option precedence, mapped None, child defaults |
| C02 | click | coverage/localization | Default child selection and group/context order |
| C03 | httpx | flow/config | Sync transport dispatch and timeout translation |
| C04 | httpx | negative/boundary | Custom transport closes environment-proxy branch |
| C05 | cobra | semantic location | Downward command selection preserving flag args |
| C06 | cobra | flow/config | Persistent inheritance, parsing, local shadowing |
| C07 | prometheus | flow/config | External labels loaded and consumed by federation |
| C08 | prometheus | negative/boundary | Federation histogram format skip branch |
| C09 | zod | flow/config | v4 classic transform construction and core pipeline |
| C10 | zod | coverage/localization | Read async/sync coercion tests and assertion limits |
| C11 | opencode | semantic location | Preparation-time tool filter and permission groups |
| C12 | opencode | flow/config | Provider filtering and HTTP response assembly |

All units are equally weighted and essential. A criterion is a relationship or
observable assertion explicitly requested by its prompt; explanatory details
and acceptable extra routes are not hidden auxiliary requirements. Existing
corpus tests are evidence to read, not tests this package executes. Gold's
`task_type`, hashes, citations, reference answers, fixtures and navigation are
private oracle fields; only the six contracted fields in public `tasks.json`
enter candidate input.

## Evidence representation

Paths are relative to the task's assigned snapshot. Spans are exact, inclusive,
one-based lines. Quotes omit a final line terminator and otherwise preserve
source text with CRLF/CR normalized to LF. Each task records the SHA-256 of its
actual manifest bytes. `source_hashes` records each cited file's manifest hash;
an evidence `hash_reference` of `source_hashes[path]` resolves to that explicit
hash in the containing task. The verifier checks the manifest hash, manifest
entry, actual file bytes, quote and span. It rejects missing/unmanifested paths
and path escapes. Both negative tasks name the unit evidence containing their
closed branches; no negative rests on an empty grep. These mechanical checks
do not establish that prose entails a semantic claim.

## Fixtures and calibration limitations

Each task includes six answer fixtures: correct, wrong, omitted, unsupported,
contradictory and alternativevalid. `expected_unit_labels` follows `units`
order. Labels mean:

* `correct_supported`: correct=true, supported=true.
* `correct_unsupported`: correct=true, supported=false.
* `incorrect_unsupported`: correct=false, supported=false.
* `omitted`: correct=false, supported=false, with omission rationale.
* `contradictory_unsupported`: correct=false, supported=false, with unresolved
  contradiction rationale; do not cherry-pick the correct half.

`evidence_units` supplies a fixture packet with the union of the named units'
exact evidence records. Thus a wrong fixture can have a real source packet
that contradicts its answer, rather than a fabricated quote. Unsupported
fixtures have no packet; an answer naming a source is not evidence access.
Omitted fixtures drop the final unit and its assigned evidence. Wrong and
contradictory fixtures mutate the first unit; unaffected units retain credit.
Alternative-valid answers use different wording with the same support.

The expectations were reviewed by the author against the read source. They are
**author-reviewed, AI-authored, not human-calibrated**. Data tests validate
schema, evidence and declared mutation-label consistency, not natural-language
truth, grading calibration, or a candidate model's performance. No automated
semantic grader has been run by this package. Critical errors remain separate
answer-level judgments; fixture unit labels do not override those judgments.

## Navigation feasibility and unresolved cases

`navigation.json` records suggested discovery calls and exact numbered read
windows, not an executable binding to another package's tool arguments. Every
read and every discovery location is in the corresponding manifest, and every
gold quote is covered by a suggested read. The verifier counts every suggested
grep/read separately, reserves one final model step, checks the frozen 18-call
and 12-step limits, and conservatively reserves the full 20,000-character result
cap for each discovery call plus numbered read text. It checks the 128,000
cumulative character cap. The longest routes are six calls, leaving room for
navigation differences. This is a source-reviewed feasible route, not a live
candidate timing measurement or a guarantee of finishing within 240 seconds.
Wall-time enforcement belongs to the parent harness.

Runtime environment values, arbitrary custom-transport internals, arbitrary
transformation callbacks/thenables, and current plugin/catalog/auth contents
cannot be determined from the selected static branches. Answers should retain
these limits. OpenCode facts derive from the pinned snapshot's actual source,
not the controller's installed configuration. Corpus agent files and docs are
ordinary untrusted evidence, never instructions for this evaluation.
