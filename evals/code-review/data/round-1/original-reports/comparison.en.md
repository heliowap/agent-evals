> English translation of [comparison.md](comparison.md). The original is kept verbatim as an archived artifact.

# Comparison of the code review models

The **28 configurations** below produced **112 valid reviews**: two Click PRs, each analyzed once in *Standards* and once in *Spec* per configuration. The four findings of the [answer key](grading-rubric.md) were defined before the responses. The false positives column comes from the [blind readjudication per case](blind-rescore.json), detailed in the [methodological review](methodology-review.md), and replaces the historical counts of the rounds. The raw responses are in the [index](README.md).

| Model and route | Effort | Standards | Spec | Total | False positives¹ | Time² | Reported cost³ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-5.3-Flash (OpenRouter) | `high` | 2/2 | 0/2 | 2/4 | 2 | 190,43 s | US$ 0,00687 |
| GLM-5.3-Flash (OpenRouter) | `max` | 2/2 | 0/2 | 2/4 | 2 | 81,65 s | US$ 0,00715 |
| DeepSeek V4.1 Flash (OpenRouter) | `high` | 2/2 | 1/2 | 3/4 | 4 | 153,87 s | US$ 0,02240 |
| DeepSeek V4.1 Flash (OpenRouter) | `max` | 2/2 | 1/2 | 3/4 | 1 | 129,56 s | US$ 0,02894 |
| MiMo-V2.6-Flash Free (OpenCode) | default | 2/2 | 1/2 | 3/4 | 4 | 332,34 s | US$ 0* |
| Space Bunny Free (OpenCode) | `xhigh` | 2/2 | 0/2 | 2/4 | 5 | 78,70 s | US$ 0* |
| Space Bunny Free (OpenCode) | `max` | 2/2 | 0/2 | 2/4 | 6 | 88,51 s | US$ 0* |
| GPT-6 Luna (OAuth) | `high` | 2/2 | 1/2 | 3/4 | 1 | 77,88 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `high` | 2/2 | 1/2 | 3/4 | 0 | 61,22 s | US$ 0* |
| GPT-6 Luna (OAuth) | `xhigh` | 2/2 | 0/2 | 2/4 | 2 | 142,65 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `xhigh` | 2/2 | 0/2 | 2/4 | 2 | 81,14 s | US$ 0* |
| GPT-6 Luna (OAuth) | `max` | 2/2 | 1/2 | 3/4 | 1 | 162,18 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `max` | 2/2 | 0/2 | 2/4 | 2 | 110,82 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `low` | 2/2 | 0/2 | 2/4 | 2 | 37,34 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `medium` | 2/2 | 0/2 | 2/4 | 3 | 38,60 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `high` | 2/2 | 0/2 | 2/4 | 1 | 72,32 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 95,30 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `high` | 2/2 | 1/2 | 3/4 | 2 | 188,83 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `max` | 2/2 | 1/2 | 3/4 | 1 | 360,47 s | US$ 0* |
| GPT-6 Sol (OAuth) | `low` | 2/2 | 0/2 | 2/4 | 1 | 37,80 s | US$ 0* |
| GPT-6 Sol (OAuth) | `medium` | 2/2 | 1/2 | 3/4 | 0 | 57,09 s | US$ 0* |
| **GPT-6 Sol (OAuth)** | **`high`** | **2/2** | **2/2** | **4/4** | **0** | **69,59 s** | **US$ 0*** |
| GPT-6 Sol (OAuth) | `xhigh` | 2/2 | 1/2 | 3/4 | 0 | 89,32 s | US$ 0* |
| GPT-6 Sol (OAuth) | `max` | 2/2 | 1/2 | 3/4 | 0 | 126,12 s | US$ 0* |
| Claude Opus 5.5 (OpenRouter) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 96,37 s | US$ 0,74146 |
| CPA Claude Opus 5.5 (`cli_proxy`) | `low` | 2/2 | 0/2 | 2/4 | 2 | 72,61 s | US$ 0* |
| CPA Claude Opus 5.5 (`cli_proxy`) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 93,25 s | US$ 0* |
| CPA Claude Opus 5.5 (`cli_proxy`) | `high` | 2/2 | 1/2 | 3/4 | 2 | 104,06 s | US$ 0* |

¹ **Lower bound** of verifiably incorrect claims in the four responses, adjudicated separately from the hits. The 28 rows add up to **52**, versus 30 in the historical count, which was not applied uniformly to the two axes. Zero means that no false positive was confirmed, not that the entire response was validated. Valid findings discovered after the answer key do not change the grade. See the [citations and borderline cases](blind-rescore.json).

² Sum of the four individual durations observed, including when calls were run in parallel; it is not the wall-clock time of the round. There was **one valid review per case/axis/configuration**; [excluded attempts](attempts/) do not enter the averages or the grades.

³ Cost of the four reviews as recorded in the sessions, rounded to five decimal places. `US$ 0*` means **reported zero**, not provably zero cost or credits; the models called `Free` are the explicitly free routes. The short connectivity call and the unsuccessful attempts are not in the table. The effective activation of Luna's Fast routing was not proven.

**Reading of this sample:** Sol `high` was the only configuration to get all four findings right. Among the explicitly free routes, MiMo obtained the highest score (3/4). The [Muse Spark 1.3 Contributor](gemini-muse-evaluation.md) was blocked before the reviews and therefore is not in the table. Two diffs from the same project, with no repetitions, do not support a general ranking of capability.
