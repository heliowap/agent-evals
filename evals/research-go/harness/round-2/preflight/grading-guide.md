# Blind semantic grading procedure

Two independent AI graders each receive one 36-case shard, the opaque case exports and this guide. They do not read execution records, private mapping, latency, token usage, model identity, prior answers or ranking results. They may use local parsing to organize evidence but must adjudicate each substantive judgment against the answer and primary source text; matching keywords is not semantic grading.

For each nonempty answer, preserve six check judgments, uncertainty, citations, critical errors, unsupported extras, instruction compliance and explicit ambiguity. Empty answers have no invented semantic grade. Initial grades remain immutable after review; adjudication overrides preserve the initial grade and a reason.

## Checks and source evidence

- `supported`: the answer satisfies the frozen atomic requirement and the primary source supports it.
- `contradicted`: an asserted answer claim conflicts with the frozen source-backed requirement.
- `missing`: required content is absent. Use an empty answer quote and an absence rationale.
- `unverifiable`: an asserted claim cannot be resolved by the allowed evidence. Explain the limit rather than presuming error.
- Citation status is separately `entailing`, `missing` or `non_entailing`. A fact can be correct but uncited.

Use exact answer spans and verbatim source spans, with their official URL and opaque source path. Frozen reference pages may establish the expected fact, but only pages actually fetched by that candidate can earn citation grounding. Inspect any `candidate_visible_path` if truncation matters. Do not give grounding credit for a plausible unfetched bibliography, nonexistent anchor or irrelevant citation.

An entailing check must have a claim-level citation record covering its exact answer quote and source URL. A citation may apply to a paragraph/list by clear placement; require actual semantic entailment, not merely a matching domain. Preserve exact Markdown in quotes where convenient; the verifier's presentation normalization is not permission to change words or negations.

## Uncertainty and extra assertions

Apply the task's frozen uncertainty key using `pass`, `omit` or `fail`. A correct refusal to infer an unsupported guarantee is useful evidence; vague caution that never addresses the specific requested limit does not automatically pass. Critical mistakes and unsupported substantive extras remain separate, each with answer/source evidence and rationale. Avoid double-counting paraphrases as several extra assertions. Ordinary omissions are not automatically critical errors.

## Citation and instruction compliance

Record complete usable HTTPS URLs, valid supplied anchors, English, the fixed visible-word cap, actual distinct-source fetching and source/tool rules. Mechanical booleans are evidence constraints, not automatic truth. Two HTML/Markdown aliases of one canonical page are one source; duplicated identical page content is also one. Report discovery-chain coverage separately from factual scores.

The exact grade schema and judgment proof requirements are in `contracts.md`. Graders may read its schema without reading identity-bearing files. No inferred qualified flag, model recommendation or timing should be written by graders; analysis reconstructs qualification only after the effective grades are sealed.

## Independent adjudication and seal

A separate blind AI review checks initially qualified-looking answers, all critical/contradicted/ambiguous judgments and citation failures against sources. It records reviewed IDs and any override under `adjudication/`, without modifying initial grades or changing the rubric. Ambiguity remains disclosed. Save a passed review receipt only when required review coverage is actually complete.

The parent seals initial grades, effective overrides and blind review receipts before unblinding. The saved-evidence audit verifies provenance and integrity; it does not prove semantic correctness or turn AI adjudication into human judgment.
