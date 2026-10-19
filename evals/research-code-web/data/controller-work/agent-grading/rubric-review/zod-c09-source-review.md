# C09 transform reference-attribution review

## Decision

**No criterion correction is required.** The frozen alternative, “Equivalent input/output-stage wording is valid,” permits a source-supported description of the classic transform body for the requested synchronous, non-Promise case. Preserve the frozen rubric, original raw judgments, and existing labels. The flagged judgment still requires its ordinary independent semantic review; this source review does not validate an unread candidate answer or assign a score.

Independent, source-only reviewer: `ses_6a78697b53ea5d347976`, requested `openai/gpt-6.1-sol-fast#high`. The reviewer did not inspect candidate answers, raw judgments, private identity mappings, model configurations, or latency. This is AI source review, not human calibration. The parent subsequently read the cited constructor, classic/core transform, and memoizer spans to verify the attribution caveat.

## Primary-source findings

All paths refer to the frozen `corpus/zod/packages/zod/src/v4/` snapshot, not current upstream Zod.

- `classic/schemas.ts:2252–2257,2278–2287`: the classic constructor calls `core.$ZodTransform.init(inst, def)` and then replaces `inst._zod.parse`. Its callback receives `(payload.value, payload)`; the synchronous result is assigned to `payload.value`, and the same payload is returned.
- `core/schemas.ts:3844–3864`: the frozen reference accurately quotes the core transform body, including `const _out = def.transform(payload.value, payload)`, `payload.value = _out`, and `return payload`. That earlier parse body is not the effective ordinary classic transform body.
- `core/core.ts:73–88,118–128`: construction finishes the initializer before running deferred callbacks. `core/schemas.ts:226–231` defers the unchecked `inst._zod.run = inst._zod.parse` assignment; a checked runner instead calls the current parse implementation (`core/schemas.ts:297–321`).
- `core/memoizer.ts:226–237`: the deferred memoizer captures the final `inst._zod.parse`, wraps it, and patches `run` when necessary. This preserves the classic transform body rather than resurrecting the replaced core body.
- `classic/schemas.ts:245–247,2291–2298,2559–2565`: classic `.transform(tx)` builds `pipe(this, transform(tx))`; the output schema stores the callback. `classic/schemas.ts:2546–2553` initializes the pipe through core without replacing that pipe parser.
- `core/schemas.ts:4441–4446,4451–4456`: the forward pipe runs input first and then output. Any issue code other than `unrecognized_keys` aborts the output stage; an `unrecognized_keys`-only list proceeds with the same issue array.
- `classic/schemas.ts:2262–2286` versus `core/schemas.ts:3849–3863`: the bodies differ outside the requested scope. Classic adds `payload.addIssue` and chains a returned Promise, whereas the core synchronous branch throws `$ZodAsyncError` for a Promise. They are not generally interchangeable.
- `core/parse.ts:22–35`: synchronous public parsing rejects a Promise, throws for remaining issues, and otherwise returns `result.value`. Carrying exceptional issues onward does not establish public parse success.

## Application of the frozen criterion

The frozen C09 packet asks for representation, forward ordering, issue gating, and carriage of the returned transformed value. C09.U4's quoted core code establishes the value/payload behavior but has an attribution caveat when read as the actual classic runner. The already-frozen acceptable alternative allows equivalent input/output-stage wording. A correct classic-runner description therefore need not use the local variable `_out` or incorrectly claim that the original core body executes.

C09.U1, U2, and U3 do not need changes. The frozen critical-error criteria concern transformation before validation, omission of the `unrecognized_keys` exception, and confusing v3 effects with v4; none mandates attribution of callback execution to the replaced core body.

The review used a filtered, read-only view of job 30's prompt, reference, units, alternatives, and critical-error criteria. It did not use reference evidence as candidate support. Candidate-specific correctness and support remain the responsibility of fresh blind grading/review using only each packet's eligible evidence.

## Limits and preservation

- The source-only reviewer did not affirm the original raw judgment. Its candidate-specific application remains independently reviewable.
- Arbitrary callback results cannot be inferred without their bodies.
- A global postprocessor can run after deferred initialization (`core/core.ts:130–132`); unspecified external customization is outside this ordinary builder/interpreter trace.
- No rubric, label, candidate trial, or original raw judgment is changed by this finding. An acceptance receipt may unblock only the exact reviewed alert and raw hash, while retaining its original `uncertain: true` review trigger.
