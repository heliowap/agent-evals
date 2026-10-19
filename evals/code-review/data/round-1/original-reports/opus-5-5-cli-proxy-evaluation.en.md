> English translation of [opus-5-5-cli-proxy-evaluation.md](opus-5-5-cli-proxy-evaluation.md). The original is kept verbatim as an archived artifact.

# CPA Claude Opus 5.5 via `cli_proxy`: code review evaluation

> **Record of the original round.** The answer-key hits and times remain valid. The false-positive column and the comparisons based on it are historical; see [comparison.md](comparison.md) and [blind-rescore.json](blind-rescore.json) for the re-adjudicated values.

**12 reviews** of `cli_proxy/cpa-claude-opus-5-5` were completed at `low`, `medium` and `high`: two [public diffs](fixture-research.md), each analyzed separately on the *Standards* and *Spec* axes. Each case/axis/level received the same prompt as the earlier rounds; the [predefined answer key](grading-rubric.md) was not sent to the model. The exports confirmed the CPA model, the requested variant, exact receipt of the prompts and the absence of tool calls in the 12 sessions. [Responses and metrics](results-opus-5-5-cli-proxy/) · [Adjudication](opus-5-5-cli-proxy-scores.json).

| Effort | Standards | Spec | Confirmed false positives (min.) | Summed time¹ | Output² | Reported cost³ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `low` | 2/2 | 0/2 | 2 | 72.61 s | 5,981 | US$ 0 |
| `medium` | 2/2 | 1/2 | 1 | 93.25 s | 8,340 | US$ 0 |
| `high` | 2/2 | 1/2 | 1 | 104.06 s | 9,543 | US$ 0 |

¹ Sum of the four individual durations per level, including CLI call and export; there were up to two reviews in parallel. The medians per review were 16.48 s (`low`), 21.59 s (`medium`) and 23.91 s (`high`). Each combination was run **once**.

² Output tokens reported by OpenCode, not total tokens. `cli_proxy` recorded **only 4 input tokens and zero reasoning in each call**, even though each prompt contains the diffs and the review protocol. It also recorded read and write cache in large volume. The counters do not offer a simple, comparable measure of total tokens nor prove absence of internal reasoning.

³ OpenCode recorded US$ 0 in the 12 sessions. Without an invoice or measurement of the service's credits, this **does not show it is free nor that the real cost is zero**.

## Quality of the reviews

- **Standards: 6/6.** All levels found the absence of the regression test in [PR #3773](https://github.com/pallets/click/pull/3773) and the forbidden ternary expression in [PR #3868](https://github.com/pallets/click/pull/3868).
- **Spec: 2/6.** `medium` and `high` explained why PR #3773 does not fix the breaking of the options: `textwrap.TextWrapper.__init__` sets `break_on_hyphens=True` on the instance, hiding the `False` added to the class. `low` did not identify this cause. No level pointed out the predefined finding of PR #3868: `--arg="a b"` splits into three tokens. `medium` and `high` mentioned inner quotes kept in the tokens, but did not describe the concrete split required by the answer key.
- **Additional finding, outside the scoreboard:** the three levels identified that backslashes in arguments after the executable may disappear when the first token does not contain a backslash. The failure was reproduced in the parsing function at the fixed revision with `WIN=True` on macOS; this does not prove real launch behavior on Windows.
- **Confirmed false positives:** the *Standards* response for PR #3773 stated, at the three levels, that the new attribute already changes the visible formatting. It does not: the instance attribute keeps the value `True`. The *Spec* response at `low` also stated this global effect, making two false positives at that level. `medium` and `high` described the possible expanded effect in *Spec* as conditional, without receiving another false positive for it. The counts are conservative lower bounds.

The **12 responses exceeded the 400-word limit** requested in the prompts (from 408 to 535 words). This did not change the score, but reduces suitability for a review that needs to be concise.

## Tokens, route and limits

| Effort | Reported input | Output | Reported reasoning | Cache read | Cache written |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 16 | 5,981 | 0 | 19,292 | 144,875 |
| `medium` | 16 | 8,340 | 0 | 51,244 | 112,923 |
| `high` | 16 | 9,543 | 0 | 51,244 | 112,927 |
| **12 calls** | **48** | **23,864** | **0** | **121,780** | **370,725** |

An earlier attempt to test this route was blocked by HTTP 400, with the error `Claude Code 2.1.251 does not support this model; version 2.1.280 or newer is required`. In this round, **the three short access tests answered and the 12 reviews finished**, with no change made by us to the local configuration. The causes of the earlier failure and of the recovery were not identified. The [earlier round of Opus 5.5 `medium` via OpenRouter](opus-5-5-evaluation.md) belongs to another provider: it also got 2/2 on *Standards* and 1/2 on *Spec*, with at least one false positive, but these two isolated results do not establish equivalence between routes.

**Choice among the CPA efforts tested: `medium`.** It tied with `high` on hits and confirmed false positives, with lower summed time and fewer output tokens in this round. Both stayed below Sol `high` on the answer key (3/4 versus 4/4). Two diffs from the same project, one run per combination and sources delivered directly in the prompts do not allow generalizing the hit rate or measuring the ability to navigate the repository and run `/code-review` in full.
