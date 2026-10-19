> English translation of [2026-09-26-code-review-eval-v2-design.md](2026-09-26-code-review-eval-v2-design.md). The original is kept verbatim as an archived artifact.

# Round 2 of the code review benchmark — design

Date: 09/26/2026
Status: collection and adjudication completed in `round-2/revision-2/`; the report is **exploratory**, since the later audit identified [validity limits](../../../round-2/revision-2/methodology-review.md) without changing the cases, prompts, answer key or blind decisions.

## Goal and limit of inference

Compare the quality and observed time of 25 model configurations facing **English** prompts, inspired by the two axes of `/code-review`. Each model receives the same fixed material for one case and one axis, without tools. This round measures analysis of the context provided, not the full execution of the skill. The causal effect of optimizing the prompts will **not** be measured: cases and prompts change relative to the previous round, and the old prompt will not be run on the new cases.

The 112 results of the first round, including archived failures and the re-adjudication, remain intact. Round 2 will have its own cases, prompts, answers, answer key and report in `round-2/`; the root `README.md` will point to it. The four-point scores of the Click round will not be compared numerically with the new scores.

## Matrix and routes

There are **25 configurations**, three cases, two axes and two independent runs per cell: `25 × 3 × 2 × 2 = 300` valid reviews as the planned maximum. The two runs use distinct sessions and receive identical prompts.

| Family and route | Variants | Total |
| --- | --- | ---: |
| GPT-6 Luna, OpenAI OAuth | default and Fast, each at `high/xhigh/max` | 6 |
| GPT-6 Sol, OpenAI OAuth | `low/medium/high/xhigh/max` | 5 |
| Gemini 3.8 Flash, `cli_proxy` | `low/medium/high` | 3 |
| SWE-2, `cli_proxy` | `medium/high/max` | 3 |
| CPA Claude Opus 5.5, `cli_proxy` | `low/medium/high` | 3 |
| GLM-5.3-Flash | `high/max` | 2 |
| DeepSeek V4.1 Flash | `high/max` | 2 |
| MiMo-V2.6-Flash, OpenRouter | default | 1 |

GLM and DeepSeek keep the OpenRouter IDs already used. The route initially planned for MiMo was `opencode/mimo-v2.6-flash-free`, but the preflight before the reviews received HTTP 403 (`OpenCode's free tier can only be used from within OpenCode`), with no response or tokens. The alternative **fixed before the first review** is `openrouter/xiaomi/mimo-v2.6-flash#none`, at the reported price of US$ 0.14 per million input tokens and US$ 0.28 per million output tokens; this configuration also counts toward the OpenRouter US$ 10 cap. The [preliminary manifests](../../../round-2/manifest-v1-preflight.json) and [of the second attempt](../../../round-2/manifest-v2-preflight.json) were archived, with no valid review. A failure in the decoder after the first response required preserving the [original run manifest](../../../round-2/manifest.json) and freezing another [manifest, of revision 1](../../../round-2/revision-1/manifest.json), without changing cases, prompts, answer key, matrix or tool policy. Three old sessions were revalidated: two fill distinct cells; the third is an excess attempt preserved, not an additional repetition. Do not mix routes between the two runs of the same configuration. Space Bunny and Opus via OpenRouter are left out; Muse remains blocked and does not enter the matrix. A route failure after freezing does not authorize silently swapping model or provider.

When `opencode run` returned without a session ID for a MiMo call, revision 1 preserved the excluded attempt with unknown cost and paused OpenRouter. The later export found **the session of the same call**, with prompt, agent and route fixed and a reported cost of US$ 0.00106231; it had no final response and does **not** count as a valid review. With the user's approval, [revision 2](../../../round-2/revision-2/manifest.json) froze the [cost record](../../../round-2/revision-2/cost-resolution.json) and the [original export](../../../round-2/revision-2/cost-evidence.json), revalidated and [copied the earlier results](../../../round-2/revision-2/migration.json) without altering the source files. The pause for unknown cost remains in force for any new attempt without proof; the US$ 10 limit remains based on the **reported** cost, and is not an account billing block.

## Selection and freezing of the three cases

- Select three public PRs from three distinct repositories, preferably with different languages, diff sizes and defect types. Do not reuse the two Click PRs.
- Require verifiable base/head commits, a reproducible diff, an issue or source specification accessible at the revision, a documented *Standards* rule in force at that revision and enough context to follow the affected paths. If a PR does not satisfy this, discard it **before** calling models.
- Separate in the material delivered to the model: original request, PR author claims, diff, unchanged context and repository rules. Use excerpts faithful to the sources, without an editorial interpretation that hints at the defect or the expected result. Do not include the answer key nor reproduction tests that reveal the target finding.
- Before any response, verify the target defects in the fixed code and record in the answer key: requirement/rule, line, mechanism, reproduction or proof, limits of the proof and acceptable equivalences. Seek targets of varied difficulty on both axes; do not depend only on the absence of tests or a changelog.
- Also fix, before execution, version and hash of the cases, the English instructions, the matrix, the scoring criteria and the planned random order. After the first response, do not modify these inputs; a necessary correction creates a distinct round version.

## English prompts

The common material will specify a review of **a single axis**, fixed commit and diff, sources, absence of tools and a conciseness limit. The *Standards* axis will require a rule in force and applicable, the changed location, mechanism and consequence; it will distinguish process rule, code convention and heuristic *code smell*. The *Spec* axis will treat the issue as the goal and the PR description as a claim about the solution; it will require requirement, location, mechanism and impact. In both:

- Report only supported findings; explicitly allow `No supported findings`.
- Examine missing requirements, wrong behavior and undue scope without requiring all categories to appear. An absence of a test is a lack of coverage/evidence, not proof that the fix failed.
- Distinguish confirmed current effect, conditional hypothesis and a result not verifiable with the available materials. Do not turn a platform hypothesis into a demonstrated failure.
- Avoid invented citations; each finding must point to its source and changed excerpt. When a *code smell* has no concrete cost, omit it.
- Use the same finding format, with location, basis of the claim, mechanism and consequence; limit the number of substantiated findings, without filling space with empty categories.

The full English texts and their hashes will be recorded in `round-2/` before the calls. The installed `/code-review` skill will not be changed.

## Execution, integrity and cost

The runner will have IDs per case/axis/configuration/repetition and resumable writing. It will close `stdin`, limit concurrency, record attempts and accept a response only if the exported session confirms **exact prompt, effective route/model/effort, non-empty response and absence of tools**. Exclude and preserve API errors, truncated responses, contaminated prompts or sessions without confirmation; up to two attempts per cell with the same prompt, without altering the answer key. The order of calls will be shuffled with a recorded seed, to reduce temporal bias between configurations.

The cost reported by OpenRouter, including preflight and billed unsuccessful attempts, will have a **US$ 10 cap**; the runner will pause upon reaching it or if it cannot safely compute the reported consumption. OAuth and `cli_proxy` may record US$ 0 without the real cost being zero: record this observability limit, without estimating a price or calling these routes free. Times per call, median and dispersion per configuration will be shown; sums of durations will not be treated as wall-clock time. The Fast selection will be annotated as requested, without presuming effective acceleration.

## Scoring and publication

The fixed answer key measures coverage of the known targets per axis. Every additional finding will be classified separately as **verified valid**, **refuted by evidence**, **not verifiable** or **opinion/style**, with a quotation from the response and a justification; the same claim repeated in one response counts once, and independent responses count separately. An omission is not a false positive. Later findings do not alter the predefined targets. The responses will be shuffled and de-identified per case for adjudication; borderline points will be exposed and the decisions tied to the original responses. Do not claim independent double evaluation if it does not occur.

Publish target coverage, verified false claims, additional valid findings, inconclusive ones, duration and reported cost in separate columns. Do not create a single quality/speed score with weights decided after the responses; present the trade-off frontier and indicate the small sample. If cases, routes, cost or integrity prevent the 300 valid reviews, publish the partial state and the missing combinations, without filling gaps by assumption.

## Acceptance criteria

1. Three cases from three repositories and the yardstick are archived and verified before the first review.
2. Manifest of the 25 configurations, hashes of the English prompts and 300 cell IDs are generated before executing; the runner's local tests validate coverage, resumption and rejection of a contaminated session.
3. Each response considered valid has an auditable session with prompt, model, effort, time and reported cost; failures and excluded attempts are kept separate.
4. Adjudication does not turn unproven claims into false ones and does not reclassify new bugs as predefined targets.
5. Report and `README.md` present round 2 separately from the Click round, without claiming an overall victory or real costs not measured.
