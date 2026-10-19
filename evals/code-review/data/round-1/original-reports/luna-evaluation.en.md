> English translation of [luna-evaluation.md](luna-evaluation.md). The original is kept verbatim as an archived artifact.

# GPT-6 Luna: code review evaluation with and without Fast

> **Record of the original round.** The answer-key hits, times and costs remain valid. The false positives column and the comparisons based on it reflect the historical count; see [comparison.md](comparison.md) and [blind-rescore.json](blind-rescore.json) for the readjudicated values.

**24 reviews** were completed, without tool calls, via OpenAI OAuth: six model selections × two [public diffs](fixture-research.md) × two axes of the `/code-review` protocol. The prompts and the [answer key](grading-rubric.md) are the same as in the [previous round](evaluation.md), and the IDs actually used were checked in the sessions. The complete responses, prompts, tokens and times are in [`results-luna/`](results-luna/); the manual adjudication is in [`luna-scores.json`](luna-scores.json).

| Effort | OAuth selection | Standards | Spec | Confirmed false positives (min.) | CLI time¹ | Model turns¹ | Nominal tokens² |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high` | `openai/gpt-6-luna` | 2/2 | 1/2 | 1 | 77,88 s | 70,83 s | 106.296 |
| `high` | `openai/gpt-6-luna-fast` | 2/2 | 1/2 | 1 | 61,22 s | 54,94 s | 105.458 |
| `xhigh` | `openai/gpt-6-luna` | 2/2 | 0/2 | 2 | 142,65 s | 136,19 s | 106.049 |
| `xhigh` | `openai/gpt-6-luna-fast` | 2/2 | 0/2 | 2 | 81,14 s | 74,68 s | 108.715 |
| `max` | `openai/gpt-6-luna` | 2/2 | 1/2 | 1 | 162,18 s | 155,54 s | 107.318 |
| `max` | `openai/gpt-6-luna-fast` | 2/2 | 0/2 | 2 | 110,82 s | 104,05 s | 104.693 |

¹ Sum of four durations per selection, not the wall-clock time of the evaluation: there were up to two calls in parallel. "CLI time" measures from the call to OpenCode until the session export; "turns" measures, in the export, from the start to the end of the assistant message, excluding part of the preparation and of the export. Each case/axis/selection combination was run **once**; time and quality may vary between runs. The second Spec case concentrated the longest times (up to 85,87 s of CLI at `max` without Fast).

² Sum of the `input + output + reasoning` counters reported by OpenCode, not a deduplicated measure of billable tokens. The cache is kept separate in the table below.

## Quality of the reviews

- **Standards: 12/12.** The six selections pointed out the missing required test in [PR #3773](https://github.com/pallets/click/pull/3773) and the ternary expression forbidden by the [Click rules](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38) in [PR #3868](https://github.com/pallets/click/pull/3868).
- **Spec: 3/12 on the predefined answer key.** On the first diff, `high` with and without Fast and `max` without Fast noticed that the class attribute is overwritten by the constructor of `textwrap.TextWrapper`; `xhigh` and `max` with Fast missed it. On the second, **no** selection pointed out that the inner quotes of `--arg="a b"` are split into three arguments.
- **Additional findings, outside the scoreboard:** all six Spec responses on the second diff pointed out at least one distinct, well-founded flaw, such as loss of backslashes in arguments after the executable or resolution of `shutil.which` with a `PATH` different from `Editor.env`. The loss of backslashes and the deviation caused by the `"\\ "` condition were reproduced in the function at the pinned revision; this does **not** amount to proving a real launch failure of Notepad on Windows.
- **False positives (corrected adjudication):** at least four *Spec* responses and five *Standards* responses for the first diff claimed that the change already altered text formatting. It did not have that effect: the instance attribute preserves the value `True`. The *Spec* response at `high` without Fast described the risk conditionally, but its **separate Standards** response claimed that the behavior had already changed; it counts as one false positive. The earlier count omitted this and other *Standards* statements. The [case prompt](fixtures.json) carried an editorial sentence about scope capable of favoring this error. Each count remains a lower bound of refuted claims.

On the strict answer key, `high` **tied with the best results** of the previous round in Spec (1/2) and got both Standards cases right. `xhigh` did not improve the result; `max` without Fast tied with `high`, using more time and reasoning tokens. The `max` selected as Fast missed the finding on the first diff. The sample is too small to conclude that raising effort *causes* worsening or that one model is superior in general.

The test supplied the diff, specification and rules in the prompt. It did not measure the agent's ability to locate sources in the repository, run tests or carry out the skill's complete flow; the two cases also belong to the same project.

## Tokens and cost

| Effort / selection | Input | Output | Reasoning | Cache read | Cache written |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high` default | 103.293 | 817 | 2.186 | 0 | 0 |
| `high` Fast | 101.764 | 937 | 2.757 | 1.536 | 0 |
| `xhigh` default | 99.961 | 838 | 5.250 | 3.328 | 0 |
| `xhigh` Fast | 103.297 | 867 | 4.551 | 0 | 0 |
| `max` default | 98.680 | 1.588 | 7.050 | 4.608 | 0 |
| `max` Fast | 97.412 | 901 | 6.380 | 5.888 | 0 |
| **24 calls** | **604.407** | **5.948** | **28.174** | **15.360** | **0** |

**Nominal total:** 638.529 tokens and 635,89 s of summed individual durations. OpenCode reported **US$ 0** in all OAuth sessions, but that does **not** mean zero consumption of ChatGPT credits. The [OpenAI documentation](https://developers.openai.com/codex/speed) says that Fast for GPT-6 Luna consumes **2,5×** the credits of the standard mode where available. We did not obtain a credit statement to compute the real cost of these calls.

## What "Fast" means in this test

OAuth was active (`opencode auth list` identified `method: oauth`) and the sessions recorded `gpt-6-luna-fast` or `gpt-6-luna` with the requested effort. In **all three comparisons**, the `-fast` selection finished earlier in the sum of the four reviews; in **11 of the 12 case/axis pairs** it had a shorter turn. Since the generated texts, the reasoning tokens and the service conditions differed, this **does not prove** acceleration of the route. There is a [still-open report in OpenCode](https://github.com/anomalyco/opencode/issues/39864) of `-fast` OAuth selections that send `service_tier: priority` without obtaining effective acceleration; the [proposed fix](https://github.com/anomalyco/opencode/pull/39882) was closed without merge. That report tested another version/model and does not prove that the current installation suffers from the same problem, but it prevents the `-fast` suffix from being taken as independent verification of the route.

**Provisional choice for these cases:** default `high`, which found the defect in the first diff with less summed time than default `max`. Fast `high` gave the same grade and was faster in this round; before paying the possible credit multiplier, it would be necessary to confirm Fast routing with a controlled test on the account, preferably in the official Codex. None of the six selections replaces human review on the two cases.
