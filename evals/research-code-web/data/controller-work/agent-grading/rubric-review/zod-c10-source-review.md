# C10.U4 source and rubric-scope review

## Decision

**A genuine essential-unit/reference mismatch requires an explicitly authorized uniform correction or exclusion.** Do not accept the alert as merely an existing acceptable alternative, silently alter labels, or seal the final comparison under that interpretation.

Independent source-only reviewer: `ses_8614e04a114b7e9b63be`, requested `openai/gpt-6.1-sol-fast#high`. The reviewer read the pinned source and a filtered view of the frozen C10 prompt/reference/criteria. No candidate answer, base grade, review, identity mapping, model configuration, or timing was inspected. The parent additionally read the complete object/JIT spans, public parse guard, and three test assertions. This is AI source review, not human calibration.

## Frozen question and criterion

The question asks what the classic object-transform tests assert, what core runtime check explains synchronous rejection, and whether the rejection test asserts an exact error class/message. Essential C10.U4 specifically requires core `$ZodTransform`'s `_out instanceof Promise` rejection and its `ctx.async` output handling, citing `core/schemas.ts:3849–3860`.

The frozen alternative permits describing rejection by the branch rather than naming an externally rendered error message. The independent review concludes that this relaxes message wording, not the required body's identity/reachability. The existing criterion therefore cannot be treated as uniformly corrected without an explicit policy decision.

## Primary-source evidence and static inference

Paths are relative to the evaluation root, not current upstream Zod.

1. `corpus/zod/packages/zod/src/v4/classic/tests/transform.test.ts:93–125`: the synchronous object test expects `{ id: "5" }`; the asynchronous object test awaits `parseAsync` and expects the same value. The synchronous parse of the asynchronous callback asserts only `).toThrow();`, with no class/message argument. These are read assertions, not executed results.
2. `corpus/zod/packages/zod/src/v4/classic/schemas.ts:245–247,2291–2297,2546–2565`; `core/schemas.ts:1333–1341,4441–4456`: the transform is an input-number/output-transform pipe. The forward pipe passes successful input to the output stage and does not itself reject the output Promise.
3. `corpus/zod/packages/zod/src/v4/classic/schemas.ts:2253–2287`: after core initialization, classic replaces `inst._zod.parse`. It returns `output.then(...)` for a Promise without checking `_ctx.async`.
4. `corpus/zod/packages/zod/src/v4/core/schemas.ts:226–231,3837–3864`; `core/core.ts:118–128`; `core/memoizer.ts:226–237,327–330`: deferred runner assignment and the memoizer capture the completed classic override. The original core transform body quoted by the frozen reference is not the effective callback body on the ordinary classic path.
5. `corpus/zod/packages/zod/src/v4/classic/schemas.ts:1674–1682,1731–1740`; `core/schemas.ts:2242–2248,2360–2392`: classic objects initialize `$ZodObjectJIT`. With JIT enabled, evaluation allowed, `ctx.async === false`, and no per-call `jitless: true`, the generated object parser is selected; otherwise the generic object parser is selected.
6. `corpus/zod/packages/zod/src/v4/core/schemas.ts:2259,2285–2295,2312–2333`: generated object code stores the child `.run(...)` result and reads `${id}.issues.length` without a Promise check for this nonoptional input. **Static inference:** the native Promise returned by classic chaining lacks the parse payload's `issues` property, so this branch would produce an incidental TypeError before the public parse guard. Neither this inferred class nor its message is asserted by the test.
7. `corpus/zod/packages/zod/src/v4/core/schemas.ts:2226–2235`; `core/memoizer.ts:85–92,126–129,144–163,252–259`: the generic object collects child Promises and returns `Promise.all(proms).then(() => payload)` when there is no catchall. The ordinary nonrecursive memoizer path adds no Promise rejection.
8. `corpus/zod/packages/zod/src/v4/classic/schemas.ts:297–302`; `classic/parse.ts:8–20`; `core/parse.ts:22–34,48–58`: public synchronous parse supplies `async: false` and rejects a returned Promise with `$ZodAsyncError`. This is reached after the generic object's Promise propagation, not after the inferred JIT failure. Asynchronous parse supplies `async: true`, selects the generic object route, and awaits a returned Promise.

Thus classic chaining plus the public core parse guard is a legitimate conditional/core-contract explanation, but not the exact cause on the source-defined JIT path. The core transform body named by essential U4 is overwritten in either ordinary classic path.

## Scope and next decision

- Minimal source defect: C10.U4 and its reference explanation. U1–U3's test assertions need no source correction.
- Candidate-specific correctness, support, and score implications remain **UNVERIFIED**: no answer or judgment was reviewed by the source reviewer.
- Actual test-runner configuration and observed exception remain **UNVERIFIED**. No tests/code were run. Global postprocessing can further change execution (`core/core.ts:130–132`).
- The three read assertions establish no universal behavior for arbitrary callbacks or non-Promise thenables.
- There are 27 scheduled C10 trials, nine attempted and eight completed answers. The other 118 completed answers are unaffected by C10 exclusion. Counts were computed from the saved blind packets without using identity mappings.
- A user-authorized versioned correction must be applied consistently to all C10 answers, with original artifacts retained. Alternatively, uniformly exclude the defective unit or question from quality comparison, explicitly documenting the post-hoc policy and preserving operational accounting.

No correction, exclusion, new grading call, raw-review submission, or final seal was performed by this source review. All 126 base grades, 34 accepted reviews, and the blocked review's exact original JSON remain preserved.
