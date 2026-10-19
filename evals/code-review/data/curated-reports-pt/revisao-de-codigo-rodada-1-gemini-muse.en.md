> English translation of [revisao-de-codigo-rodada-1-gemini-muse.md](revisao-de-codigo-rodada-1-gemini-muse.md). The original is kept verbatim as an archived artifact.

# Partial evaluation — Gemini 3.8 Flash and Muse Spark 1.3 Contributor

Reading version published at the root of `evals/`. [Original preserved for audit](revisao-de-codigo/relatorios-originais/gemini-muse-evaluation.md). The links and commands of this version follow the organization by topic.


> **Record of the original round.** The answer-key hits, times and Muse status remain valid. The false-positives column is historical; see [comparison.md](revisao-de-codigo-rodada-1-comparacao.md) and [blind-rescore.json](revisao-de-codigo/blind-rescore.json) for the re-adjudicated values.

Gemini 3.8 Flash completed **12 reviews** through the `cli_proxy` provider, at the `low`, `medium` and `high` levels. I used the [two public diffs](revisao-de-codigo/fixture-research.md), the prompts and the [answer key](revisao-de-codigo/grading-rubric.md) of the earlier rounds, with the *Standards* and *Spec* axes independent. The exports of the 12 sessions confirmed the requested IDs and efforts, the exact receipt of the prompts and **no tool call**. The complete responses are in [`revisao-de-codigo/results-gemini-muse`](revisao-de-codigo/results-gemini-muse/), and the manual adjudication in [`revisao-de-codigo/gemini-muse-scores.json`](revisao-de-codigo/gemini-muse-scores.json).

| Gemini via `cli_proxy` | Standards | Spec | Confirmed false positives (min.) | Summed time¹ | Nominal tokens² |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 2/2 | 0/2 | 2 | 37,34 s | 113.611 |
| `medium` | 2/2 | 0/2 | 2 | 38,60 s | 115.378 |
| `high` | 2/2 | 0/2 | 1 | 72,32 s | 127.354 |

¹ Sum of the four durations of each level, including the CLI call and the session export, not the wall-clock time of the round. There were up to two parallel runs and only one run per case/axis/level; the times do not characterize the model's stable speed.

² Arithmetic sum of `input + output + reasoning` reported by OpenCode; cache apart. The `cli_proxy` counters require caution: at the `high` level, **`output` was zero in the four sessions despite there being text responses**. Therefore, the total does not serve as an exact count of tokens produced nor as a cost estimate. The cost field of the sessions also came as US$ 0, without proving the route is free.

On the first diff, the three levels pointed out the lack of tests in *Standards*, but stated in *Spec* that the new class attribute changes the formatting of all texts. The reproduction shows the opposite: `textwrap.TextWrapper.__init__` sets `self.break_on_hyphens=True` in each instance and the change is ineffective. The `medium` level also incorrectly stated that it would not be possible to pass `break_on_hyphens=True` to the constructor; this was also tested. On the second diff, all pointed out the prohibited ternary expression in *Standards* and found a real additional failure in the preservation of backslashes in arguments after the executable. None described the *Spec* finding of the answer key — the splitting of `--arg="a b"` into three arguments. The `high` level mentioned internal quotes, but without identifying that concrete splitting; therefore the answer key does not give it the point.

A first Gemini attempt was **excluded**: the script that started the round leaked through the inherited `stdin` into the prompts and some sessions called tools. I preserved the nine responses in [`revisao-de-codigo/attempts/gemini-stdin-leak-20260926`](revisao-de-codigo/attempts/gemini-stdin-leak-20260926/) and repeated the round with `stdin` closed; only the 12 verified sessions make up the table. In the total used, OpenCode reported **335.782 input tokens, 4.503 output and 16.058 reasoning** — a nominal sum of **356.343 tokens** and **148,26 s** of individual durations.

## Muse Contributor: blocked before the evaluation

The requested ID was confirmed as `openrouter/meta/muse-spark-1.3-contributor`, with variants `high`, `xhigh` and `max`. The short call returned `provider.invalid-request` (HTTP 404): the only endpoint available was excluded by the account's privacy policy, which prevents training on data sent to paid models. **None of the 12 Muse reviews was run.** At the user's request, I kept the choice of OpenRouter; I did not use the free route nor change the account policy. The test can only continue if the user decides to consciously enable this option in [OpenRouter → Privacy](https://openrouter.ai/settings/privacy) and says they have completed the change.

Until then, the comparison between **Gemini and Muse** remains inconclusive. Against the answer key already used for Luna, DeepSeek and MiMo, the three Gemini levels were below the best results in *Spec* (0/2 versus 1/2), but two cases from the same project do not support a general ranking.
