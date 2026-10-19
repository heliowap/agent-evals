> English translation of [evaluation.md](evaluation.md). The original is kept verbatim as an archived artifact.

# Exploratory evaluation of models for code review

> **Record of the original round.** The answer-key hits, times and costs below remain valid. For the false positive count, which was readjudicated, see [comparison.md](comparison.md) and [blind-rescore.json](blind-rescore.json); the quality conclusions of this round prior to the readjudication are historical.

28 independent reviews were evaluated: two [public Click diffs](fixture-research.md), two axes of `/code-review` (*Standards* and *Spec*) and seven configurations. The diffs, commits, specification excerpts and repository rules were frozen in [`fixtures.json`](fixtures.json). All models received the same prompt in each combination of case and axis; no response used tools. The [answer key](grading-rubric.md) contains one verifiable finding per case and axis, defined in the research before the responses.

| Model / effort | Standards | Spec | Other confirmed bug¹ | Cost of the 4 calls | Summed time² |
| --- | ---: | ---: | :---: | ---: | ---: |
| GLM-5.3-Flash `high` | 2/2 | 0/2 | yes | US$ 0,00687 | 190 s |
| GLM-5.3-Flash `max` | 2/2 | 0/2 | no | US$ 0,00715 | 82 s |
| DeepSeek V4.1 Flash `high` | 2/2 | 1/2 | yes | US$ 0,02240 | 154 s |
| DeepSeek V4.1 Flash `max` | 2/2 | 1/2 | yes | US$ 0,02894 | 130 s |
| MiMo-V2.6-Flash Free, default | 2/2 | 1/2 | yes | US$ 0 | 332 s |
| Space Bunny Free `xhigh` | 2/2 | 0/2 | yes | US$ 0 | 79 s |
| Space Bunny Free `max` | 2/2 | 0/2 | no | US$ 0 | 89 s |

¹ Finding **after the answer key**: `code.cmd C:\src\a.txt` becomes `['code.cmd', 'C:srca.txt']` in the function changed by [PR #3868](https://github.com/pallets/click/pull/3868). Five configurations pointed out the loss of backslashes in arguments after the executable. It is a reproduced defect, but it was not added to the predefined score.

² Sum of the time observed in the four completed calls per configuration, subject to load and to provider limits. There was one GLM `high` attempt that returned HTTP 429; it was [archived](attempts/click-3868/) and repeated with the same prompt. The cost of the unsuccessful attempt, US$ 0,00037, is not in the table. The costs of the 28 results used add up to US$ 0,06536; initial connectivity calls were also left out of this total.

### Time and tokens

The times in the previous table are **sums of the individual durations**, not the wall-clock time of the complete evaluation: the Standards and Spec reviews were run in parallel. The median per review was 35,3 s / 20,3 s for GLM `high/max`, 19,3 s / 32,2 s for DeepSeek `high/max`, 35,1 s for MiMo and 14,5 s / 22,2 s for Space Bunny `xhigh/max`. One MiMo call took 234,1 s and one DeepSeek `high` call, 105,1 s; this sample does not allow attributing the time differences only to the model.

| Model / effort | Input | Output | Reasoning | Nominal sum³ | Cache read / written |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLM `high` | 96.292 | 2.634 | 6.330 | 105.256 | 0 / 9.828 |
| GLM `max` | 96.295 | 2.473 | 8.682 | 107.450 | 0 / 9.828 |
| DeepSeek `high` | 97.757 | 2.593 | 8.275 | 108.625 | 1.536 / 9.828 |
| DeepSeek `max` | 98.199 | 2.485 | 19.174 | 119.858 | 1.152 / 9.828 |
| MiMo default | 91.568 | 2.470 | 12.749 | 106.787 | 16.640 / 0 |
| Space Bunny `xhigh` | 105.208 | 2.713 | 4.400 | 112.321 | 1.806 / 0 |
| Space Bunny `max` | 99.586 | 2.525 | 6.954 | 109.065 | 7.430 / 0 |
| **28 calls** | **684.905** | **17.893** | **66.564** | **769.362** | **28.564 / 39.312** |

³ Arithmetic sum of the three counters reported by OpenCode (`input + output + reasoning`); the cache is shown separately to avoid summing it twice. Do not interpret this sum as a deduplicated count of billable tokens. The numbers include the agent and protocol context, not only the diffs.

## Standards

**All got the two predefined findings right.** In [PR #3773](https://github.com/pallets/click/pull/3773), the test required by the PR template was not added. In [PR #3868](https://github.com/pallets/click/pull/3868), the new ternary expression goes against [`docs/contributing.md`](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38). Several responses also pointed out the absence of an entry in `CHANGES.rst`, a requirement stated in the template; it was not part of the four predefined findings. The protocol's *code smells* were treated as judgments, not as automatic violations.

## Spec

In [PR #3773](https://github.com/pallets/click/pull/3773), DeepSeek (`high` and `max`) and MiMo identified the cause: the constructor of `textwrap.TextWrapper` sets `self.break_on_hyphens=True`, hiding the new class attribute. [We reproduced the example from issue #3362](https://github.com/pallets/click/issues/3362) at the pinned revision; the options are still split. GLM and Space Bunny did not identify this cause at any of the efforts tested.

In PR #3868, **no configuration** pointed out the predefined finding about inner quotes: `C:\tools\vim.exe --arg="a b"` produces three arguments, even though the PR promises to respect quotes. The later finding in note ¹, pointed out by five configurations, shows that some responses found a distinct and valid flaw; it remains separate from the initial score to avoid changing the criterion after seeing the results. The reproduction exercised only the parsing function with `WIN=True` on macOS: there was no real launch test on Windows.

### Confirmed false positives

**All seven Spec responses for PR #3773** also claimed that the change extended the behavior to all formatted text. Since the new attribute is ineffective, this global effect did not occur. Part of this error may have been favored by the scope sentence used in the case's editorial excerpt; the effect claim is still incorrect, but should not be generalized to other prompts. Space Bunny `max` also attributed to `textwrap` a nonexistent `__init_subclass__` contract and cited a test case with a trailing slash that is not in the diff of PR #3868. [`scores.json`](scores.json) records only a **conservative lower bound** of evident false positives, without automatically labeling other debatable findings as errors.

## Practical reading and limits

In this sample, **DeepSeek V4.1 Flash `high`** offers the best paid combination: it got the same answer key right as `max` at a lower cost. **MiMo-V2.6-Flash Free** tied on the answer key with no per-call cost, but took longer in the four rounds. `max` did not increase the predefined hits in GLM, DeepSeek or Space Bunny; in the case of Space Bunny, `xhigh` found the additional defect that `max` let pass. The stealth model is interesting as a free second opinion, not as the sole reviewer for important decisions.

The higher effort consumed more reasoning tokens without raising this score: GLM went from **6,3 mil** (`high`) to **8,7 mil** (`max`); DeepSeek, from **8,3 mil** to **19,2 mil**; Space Bunny, from **4,4 mil** (`xhigh`) to **7,0 mil** (`max`). These are totals of the four calls, not a controlled measurement of the models' intrinsic capacity or speed.

This is a small sample of **two unmerged commits from the same project**, with no repetitions per configuration. The test supplied the relevant materials and forbade tools; therefore, it measures analysis of a frozen context, **not** the ability to discover issues, navigate the repository or run the skill in full. GLM and DeepSeek were called through the [fixed OpenRouter IDs](provider-metadata.json) at `high/max`, because the OpenCode Go route returned HTTP 402. The free MiMo does not expose an effort variant; it does not allow the requested comparison between `max` and the immediately preceding level. Space Bunny Free was tested at `xhigh/max`, without presuming the permanent identity of the stealth model.

To audit: [`results`](results/) contains the prompt, response, ID actually used, tokens, duration and cost of each call; [`benchmark.py`](benchmark.py) runs the matrix; [`summarize_results.py`](summarize_results.py) checks the coverage of the 28 responses and summarizes the metrics.
