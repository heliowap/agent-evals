> English translation of [revisao-de-codigo-rodada-1-swe-2.md](revisao-de-codigo-rodada-1-swe-2.md). The original is kept verbatim as an archived artifact.

# SWE-2: code review evaluation

Reading version published at the root of `evals/`. [Original preserved for audit](revisao-de-codigo/relatorios-originais/swe-2-evaluation.md). The links and commands in this version follow the organization by theme.


> **Record of the original round.** The answer-key hits and times remain valid. The false-positive column and the recommendations based on it are historical; see [comparison.md](revisao-de-codigo-rodada-1-comparacao.md) and [blind-rescore.json](revisao-de-codigo/blind-rescore.json) for the re-adjudicated values.

**12 reviews** of `cli_proxy/devin/swe-2` were completed at `medium`, `high` and `max`. Each level received the same two [public diffs](revisao-de-codigo/fixture-research.md) and prompts as the earlier rounds, with *Standards* and *Spec* in independent sessions. I scored the responses with the same [predefined answer key](revisao-de-codigo/grading-rubric.md), which was not shown to the model. The exports confirmed the requested variant, the exact prompt and the absence of tool calls in the 12 sessions. [Raw responses](revisao-de-codigo/results-swe-2/) · [Adjudication](revisao-de-codigo/swe-2-scores.json).

| Effort | Standards | Spec | Confirmed false positives (min.) | Summed time¹ | Nominal tokens² |
| --- | ---: | ---: | ---: | ---: | ---: |
| `medium` | 2/2 | 1/2 | 1 | 95.30 s | 106,665 |
| `high` | 2/2 | 1/2 | 0 | 188.83 s | 110,629 |
| `max` | 2/2 | 1/2 | 0 | 360.47 s | 118,696 |

¹ Sum of four durations per effort, from the CLI call until the session export. It is not the wall-clock time of the evaluation, which ran up to two reviews in parallel. The median per review was 25.39 s (`medium`), 41.66 s (`high`) and 94.73 s (`max`); there is only **one run per case/axis/level**.

² Arithmetic sum of OpenCode's input, output and reasoning counters, without cache. The `cli_proxy` route recorded **zero reasoning tokens at all levels**, which does not show absence of internal reasoning. It also recorded a cost of US$ 0, without reporting the provider's real cost. Across the 12 reviews, the counters summed **311,328 input tokens and 24,662 output tokens**: **335,990 nominal tokens** and **644.60 s** of individual durations.

## Findings

The three levels located the two *Standards* findings: the missing regression test in [PR #3773](https://github.com/pallets/click/pull/3773) and the forbidden ternary expression in [PR #3868](https://github.com/pallets/click/pull/3868). In *Spec*, all identified the concrete cause of the ineffective fix in PR #3773: the constructor of `textwrap.TextWrapper` creates `self.break_on_hyphens=True`, hiding the attribute added to the class. None found the other predefined finding, in which inner quotes of `--arg="a b"` make the parser of PR #3868 produce three arguments.

In the second diff, all pointed out another verifiable defect, **outside the answer key**: a backslash followed by a space makes the function fall back to `shlex.split` in POSIX mode, which may strip backslashes from a Windows path. I reproduced the transformation of `C:\dir\ app.exe` into `C:dir app.exe` in the fixed function, without claiming that a real launch occurred on Windows.

At `medium`, the response also stated that the change in PR #3773 immediately altered the formatting of other texts. This is a confirmed false positive: the new attribute has no effect. `high` and `max` described the scope expansion **as a hypothesis if the fix were made effective**, without attributing the effect to the current code; therefore they did not receive this false positive.

## Practical reading

**`high` is the most balanced choice among the three levels tested:** it preserved the same hits as `max`, with no confirmed false positive in this sample, with approximately half the summed time. `medium` finished earlier and had the same answer key, but made one more incorrect statement. `max` consumed more time and tokens without locating another predefined finding.

SWE-2 `high` **tied on the answer key** with default Luna `high`, DeepSeek V4.1 Flash `high` and free MiMo (2/2 on *Standards*, 1/2 on *Spec*). Default Luna `high` had **one confirmed false positive** after checking both axes, against none confirmed for SWE-2 `high`, but observed a lower summed time (**77.88 s** versus **188.83 s**). The routes and provider loads are different; two diffs from the same project and one run per configuration do not support an overall superiority among models.
