# Researcher evaluation: execution complete, comparison not yet valid

## Outcome

The counted DeepSeek access case succeeded through OpenCode Go. All 72 scheduled cases were attempted once, with no candidate reruns or provider substitutions. However, the common request envelope was not compatible with most observed GLM Go upstream requests. **This run does not establish a GLM-versus-DeepSeek quality or speed winner.**

| Configuration | Operationally completed | Provider errors | Of which rejected `thinking` |
|---|---:|---:|---:|
| DeepSeek LOW | 12/12 | 0 | 0 |
| DeepSeek HIGH | 12/12 | 0 | 0 |
| DeepSeek MAX | 12/12 | 0 | 0 |
| GLM LOW | 0/12 | 12 | 11 |
| GLM HIGH | 1/12 | 11 | 10 |
| GLM MAX | 2/12 | 10 | 10 |

Operational completion is not a source-checked quality score. Blind semantic grading has not yet occurred; no factual accuracy or qualified-latency ranking is claimed.

## Verified execution evidence

- 72 planned and attempted cases; 39 operational completions and 33 provider errors.
- 178 logged client inference POSTs and 216 documentation-fetch attempts.
- Approximately 21.62 minutes from first worker launch through last worker exit.
- Same frozen prompts, source archive, tool schema, limits and counterbalanced schedule throughout execution.
- DeepSeek used the Go route, not OpenRouter. No Gemini calls, alternate candidate routes, policy changes or caller retries were made.
- Parent exact-key scanning found zero selected Go credential matches in owned artifacts/runtime; no credential store was copied.

These measurements come from `execution/index.json`, the 72 linked `record.json` files, `execution/post-starts.jsonl`, native response files and `execution/parent-provisioning.json`. Raw request/response evidence and failed rows are preserved.

## Compatibility failure

31 native HTTP 400 errors state:

> Upstream request failed: [unknown_parameter] invalid request body: json: unknown field "thinking"

Two further GLM HTTP 400 errors state:

> Upstream request failed: [unsupported_parameter] The request contains an unsupported parameter. See the API reference.

The harness explicitly sent `thinking: {type: "enabled"}` along with literal `reasoning_effort`. The former was documented in the native vendor contracts but was not accepted by the observed GLM Go upstream path in these cases. This is an integration/route compatibility problem, not evidence that GLM produces worse research answers. Fast rejections must not be counted as successful research latency.

## Audit status and immutable evidence

The independent pre-run review passed; the real frozen-stage audit passed before inference. All original frozen inputs remain unchanged.

Post-run collection exposed a separate false positive in the generic credential regex: the public Cloudflare D1 documentation contains the literal field `"Authorization":`. All 36 reported matches are this field and appear in the retained public source archive; they are not the selected Go key. A narrowly scoped supplemental verifier is being reviewed under `postrun/`, preserving the original verifier, source bodies, raw execution records and grading/statistical rules. **No final comparison audit is claimed as passed.**

## Proposed next step, not authorized or executed

For a fully paired comparison, prepare a new immutable study that omits the optional `thinking` envelope from every configuration, retaining the literal effort request and otherwise identical controls. Treat the first real scheduled case for each configuration as a counted compatibility gate, stopping on unsupported request parameters rather than spending the remaining cases. This proposal requires renewed authorization because the original 72 cases have already been consumed; no corrected candidate calls have been made.

Alternatively, source-grade only the 36 existing DeepSeek answers and explicitly leave the GLM comparison unresolved. Neither choice should reinterpret rejected requests as model-quality failures or silently merge an unpaired rerun into a contemporaneous ranking.

## Inspectable files

- `plan.md`, `contracts.md`, `protocol.json`, `schedule.json`, `freeze.json`: predeclared design and sealed inputs.
- `dataset/`, `research/`, `api-evidence/`: tasks, gold, whole primary sources and API-contract evidence.
- `execution/`: all attempts, native responses, full sources, timings, usage, errors and cleanup.
- `blind/`: opaque source/answer exports; `private/` keeps identity mapping separate.
- `postrun/`: supplemental audit correction and its review, when completed.
- `analysis/compatibility-report.json`: saved operational counts, not a quality ranking.
