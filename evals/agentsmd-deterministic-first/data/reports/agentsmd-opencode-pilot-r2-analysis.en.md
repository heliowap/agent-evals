> English translation of [agentsmd-opencode-pilot-r2-analysis.md](agentsmd-opencode-pilot-r2-analysis.md). The original is kept verbatim as an archived artifact.

# Final OpenCode result

Reading version published at the root of `evals/`. [Original preserved for audit](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/analysis.md). The links and commands in this version follow the organization by topic.


The Deterministic first snippet did not demonstrate a quality gain. Both conditions delivered 36/36 correct tasks. With the snippet, OpenCode used more time and tokens in this sample. The pilot remains inconclusive for general adoption.

OpenCode 2.0.25, openai/gpt-6.1-sol#xhigh. Twelve synthetic tasks, three repetitions per condition, 36 pairs and 72 completed runs on 10/10/2026. This report replaces the partial cuts for interpreting the round.

| Metric | Empty AGENTS | With the snippet | Observed difference |
|---|---:|---:|---:|
| Correct deliveries | 36/36 | 36/36 | 0 percentage points |
| Mean time per task, s | 34.1 | 42.2 | +23.5% |
| Median time per task, s | 27.1 | 31.6 | +16.5% |
| Uncached input | 303,245 | 351,422 | +15.9% |
| Cached input | 621,440 | 636,032 | +2.3% |
| Output excluding reasoning | 27,092 | 27,892 | +3.0% |
| Reasoning | 4,206 | 12,436 | +195.7% |
| Output including reasoning | 31,298 | 40,328 | +28.9% |
| Total tokens, including cache and reasoning | 955,983 | 1,027,782 | +7.5% |
| Tool calls | 326 | 330 | +1.2% |

The mean duration difference was 8.0 s per task, about 4 min 49 s additional across the 36 runs with the snippet. The number of tool calls changed little; the difference also appears in the volume of reasoning and in the content of the operations. There was no profile that separates the causal contribution of each component to the duration.

## Quality, isolation and audit

All 72 runs passed the graders. The 78 exports confirm model, effort, session and completion of each turn, including continuity of the six repeat cases. The counters in the results match the last cumulative export, without duplicating the first turn. There are no recorded infrastructure errors or assistant errors. The six commands with a non-zero return were regression tests deliberately red before the fix; all final artifacts passed.

The 12 subjective controls also passed the frozen rubric. The hash comparison confirmed that out_of_scope did not alter files and judgment altered only message.md. The decisions are in blind/*/review.json and were sealed in [review-seal.json](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/review-seal.json) before consulting the key for this round. The reviewer was the assistant and already knew the metrics and the study design. Labels were hidden, but there is no guarantee of blinding nor independent human review.

The configuration and the discovery of plugins/skills match the preflight in all trials. There are no additional skills. OpenCode does not expose the full prompt in this flow; equality of the entire HTTP prompt was not demonstrated. Original sources and protocol are in [frozen-source/](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/frozen-source/), with hashes equal to freeze.json. Cases, rubric, treatment and raw results were not altered.

## Duration per case

Median and minimum-to-maximum range, in seconds, with three correct runs in each cell.

| Case | Empty: median; min to max | Snippet: median; min to max |
|---|---:|---:|
| count | 23.3; 16.0 to 24.8 | 31.1; 20.3 to 32.1 |
| money | 21.9; 19.9 to 22.3 | 19.0; 16.0 to 28.9 |
| convert | 75.5; 67.9 to 91.6 | 51.7; 49.4 to 103.2 |
| rename | 53.8; 51.1 to 56.7 | 91.5; 87.3 to 92.7 |
| project_tool | 15.9; 14.7 to 16.9 | 19.3; 17.7 to 26.0 |
| repeat | 42.4; 40.3 to 42.6 | 82.8; 75.7 to 87.9 |
| guardrail | 39.7; 33.2 to 43.4 | 38.7; 36.0 to 49.0 |
| regression | 40.6; 34.4 to 49.1 | 50.7; 47.2 to 51.8 |
| out_of_scope | 25.5; 22.0 to 29.4 | 33.6; 29.2 to 36.6 |
| judgment | 24.1; 20.0 to 24.9 | 22.5; 16.6 to 24.5 |
| independent | 27.3; 22.9 to 29.0 | 23.5; 21.2 to 27.9 |
| dependent | 19.6; 19.1 to 26.9 | 24.7; 22.5 to 29.2 |

The largest total increases are in rename and repeat. In both, all runs with the snippet were slower than all runs without the snippet. In repeat, the control computes the summaries with inline Python and writes them by patch. The treatment creates a reusable temporary file and adds checks. The final delivery remained correct in all repetitions. Evidence: tool-events.json of trial-0019, 0020, 0035, 0036, 0051 and 0052.

There is a favorable signal in convert: median from 75.5 s to 51.7 s. The three controls write the JSON by patch; two of the three treatments write it by program. The third treatment still uses patch and takes 103.2 s. This suggests that writing the computed transformation directly can avoid work, but three repetitions and this variability do not support a promise of speed. Evidence: tool-events.json of trial-0015, 0016, 0067, 0068, 0069 and 0070.

The three independent checks overlapped in 3/3 runs of each condition. The guardrail and regression cases detected recurrence in 6/6 of each condition. The snippet brought no quality advantage in these behaviors, which already appeared in the control.

## Exploratory comparison with Codex

The same 72 combinations of case, repetition and condition in each product. Both had 72/72 deliveries accepted by the scale, including the reviewed controls. The tokens were normalized: Codex includes cache in the input and reasoning in the output; in OpenCode these portions are separate. The transformation was checked in the compiled code of the OpenCode 2.0.25 executable; the hash and excerpts are in analysis.json.

| Condition | Codex mean time, s | OpenCode mean time, s | Time difference | Total token difference |
|---|---:|---:|---:|---:|
| empty | 40.5 | 34.1 | -15.6% | -56.3% |
| deterministic | 47.4 | 42.2 | -11.0% | -54.3% |

Across the complete set, OpenCode consumed 55.3% fewer total tokens and took 13.1% less time than Codex. That was 1,983,765 versus 4,438,212 tokens, including resent context, cache and reasoning. It was faster in 56/72 matches. The largest reduction is in the input.

This cross-product comparison is exploratory. The rounds were not randomized/interleaved across products, their execution periods partly overlapped, and internal instructions, tools, permissions and integrations differ. The design isolated the effect of AGENTS within each product; it does not identify which component explains the difference between them. The duration covers agent invocations with initialization and tools, but excludes preparation, audit, export and grading of the eval. It does not represent the total time of the evaluation process nor the model's throughput. Monetary cost was not estimated.

## Interpretation

The evidence from the two rounds favors reviewing the block's obligations before keeping it as global policy. No accuracy gain appeared; the control reached the ceiling of the scale and the snippet increased the aggregate duration in both products. This does not prove that each sentence is useless or harmful. The convert case in OpenCode suggests a localized advantage of producing the file by program, while the rule of creating a script on the second occurrence added work in repeat.

There are only three repetitions of the same 12 synthetic cases. The bootstrap interval [0,0] of the automatic report results from the ceiling of hits and does not demonstrate equivalence outside the sample. A confirmation should use new real tasks, minimum-gain criteria and tolerable cost defined beforehand, more repetitions and measurement of rework/recurrence. Separating Rules from Actions would help locate benefits; this study evaluated the whole block.

Offline reproduction: `python3 instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/analyze.py`. Full data: [analysis.json](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/analysis.json) and [metrics.tsv](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/metrics.tsv). The analysis does not call the model nor modify the trials.
