> English translation of [agentsmd-opencode-opus-5-5-medium-analysis.md](agentsmd-opencode-opus-5-5-medium-analysis.md). The original is kept verbatim as an archived artifact.

# Result of Opus 5.5 medium via CPA

Reading version published at the root of `evals/`. [Original preserved for audit](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/analysis.md). The links and commands in this version follow the organization by theme.


The Deterministic first snippet brought no accuracy gain in this sample. Both conditions delivered 36/36 correct tasks. With the snippet, the mean duration was 5.8% greater and the reported output tokens rose 14.9%. The overall time difference is small compared with the variation between cases; there is not enough evidence of a general worsening of speed.

OpenCode 2.0.25, cli_proxy/cpa-claude-opus-5-5#medium. There are 12 synthetic cases, three repetitions per condition, 36 pairs and 72 runs on 10/10/2026. The order within the pairs was balanced, with each condition first in 18 pairs.

| Metric | Empty AGENTS | With the snippet | Difference |
|---|---:|---:|---:|
| Correct deliveries | 36/36 | 36/36 | 0 p.p. |
| Mean time, s | 12.70 | 13.43 | +5.8% |
| Median time, s | 12.23 | 13.64 | +11.5% |
| Reported output tokens | 28,740 | 33,034 | +14.9% |
| Tool calls | 159 | 165 | +3.8% |

The treatment was faster in 18/36 pairs. The exploratory 95% interval by bootstrap clustered on the 12 cases was [-7.0%, +24.1%] for the difference in mean duration. This calculation was chosen after the round; it is not a pre-registered confirmatory test. The interval includes zero.

## Where the behavior changed

In repeat, the median went from 12.53 s to 24.42 s. All three runs with the snippet were slower than all three without it. The control already computed the JSONs with Python. The treatment created a temporary script on the second turn and added inspections or validation reruns. The delivery remained correct in both conditions. Evidence: tool-events.json of trial-0019, 0020, 0035, 0036, 0051 and 0052.

Excluding repeat only as a sensitivity analysis, the time difference is -1.6%. Therefore, the global increase is concentrated in this case, not uniformly distributed across the suite.

The snippet did not increase the observed parallelism. The three independent checks overlapped in 1/3 runs of the control and 0/3 with the snippet. The six numerical results were correct; the frozen rubric records overlap as behavior, without making it an accuracy requirement. Thus, 72/72 correct deliveries does not mean perfect obedience to every sentence of the block. Evidence: *-timing.json files of trials 0045, 0046, 0059, 0060, 0071 and 0072.

The guardrail and regression safeguards passed in 6/6 deliveries of each condition, including probes and reintroduction of the failure in copies of the artifacts. There was no prevention advantage within these cases. The control also generated customers.json with Python in the three repetitions of convert; the instruction was not necessary for this behavior in Opus.

## Duration per case

Median and minimum-to-maximum range, in seconds. Three repetitions per cell.

| Case | Empty: median; min to max | Snippet: median; min to max |
|---|---:|---:|
| count | 12.45; 10.87 to 12.68 | 11.03; 10.76 to 11.06 |
| money | 8.98; 7.92 to 9.23 | 8.00; 7.68 to 8.53 |
| convert | 10.57; 10.31 to 15.68 | 14.51; 13.82 to 16.18 |
| rename | 12.72; 9.51 to 19.68 | 14.60; 10.99 to 16.99 |
| project_tool | 8.76; 7.93 to 9.15 | 10.79; 10.70 to 11.41 |
| repeat | 12.53; 11.97 to 14.88 | 24.42; 22.48 to 25.43 |
| guardrail | 15.92; 14.47 to 17.72 | 16.13; 15.78 to 16.37 |
| regression | 15.72; 15.47 to 21.41 | 16.10; 15.15 to 16.90 |
| out_of_scope | 17.75; 17.60 to 18.25 | 13.95; 13.46 to 15.58 |
| judgment | 8.25; 8.24 to 8.73 | 8.41; 7.47 to 12.77 |
| independent | 12.31; 12.14 to 17.55 | 14.22; 10.30 to 16.81 |
| dependent | 9.93; 9.33 to 10.72 | 7.90; 7.30 to 9.67 |

## Audit and limits

78 exports were checked, including the continuity of the two repeat prompts. Provider, alias, medium variant and build agent match in all the assistant messages. The counters match the last cumulative export. The 72 artifacts were graded again in separate copies, including the mutations used to test recurrence prevention. No new inference was made in this analysis.

The 12 subjective controls passed the original rubric. The reviews of the artifacts without labels were sealed before consulting the current key. The assistant already knew the design, the aggregate automatic report and the Sol round. The shuffling uses the same seed as the previous round, and the wording suggests the treatment in some cases. There is no independent human review nor guaranteed blinding. The hashes confirm absence of changes in out_of_scope and exclusive change of message.md in judgment.

There was no infrastructure failure nor final assistant error. There were two calls to the nonexistent tool tool_write, recovered afterward: trial-0037 in the treatment and trial-0042 in the control. There were also two shell commands with exit 1 in the control: head -0 incompatible with macOS in trial-0008 and reading of absent optional files in trial-0010. The four runs ended correct. The runner's recoverable_error_events field contains message errors, not all tool errors; this audit consulted tool-events.json directly.

Time measures the agent invocations, including initialization, tools and any internal retries; it excludes preparation, audit, export and grading. There is no profile nor server telemetry to separate inference, proxy, network and initialization. The tool execution intervals are summed without overlap in metrics.tsv, but the rest of the time cannot be attributed to a specific component. No causal performance bottleneck was identified.

CPA reported native input of only 2 tokens in 307 messages and 4 tokens in six messages, zero reasoning and high cache volumes. We preserved input, read cache, write cache and output separate in analysis.json. The 14.9% increase refers only to reported output; it does not equal an increase in cost or total tokens. Zero reasoning in the counter does not prove absence of reasoning. The cost reported by OpenCode was not reconciled with the proxy's billing.

Configuration and discovery match the preflight in both conditions and in all trials; there are no additional skills. This does not prove full equality of the HTTP prompt. The exports confirm the selection on the client, without attesting the identity actually served by the upstream provider. Sources, protocol and variants are in frozen-source/, checked against freeze.json. The raw data of the round were preserved.

## Exploratory comparison with Sol in OpenCode

| Condition | Sol xhigh, mean in s | Opus medium via CPA, mean in s | Difference |
|---|---:|---:|---:|
| empty | 34.14 | 12.70 | -62.8% |
| deterministic | 42.17 | 13.43 | -68.1% |

Both rounds delivered 72/72 accepted results on the same suite. Opus via CPA took less observed time, but model, effort, provider and time of the round changed together. The rounds were not interleaved; this does not isolate an effect of the model or the provider. CPA's token accounting prevents directly carrying over the normalization used in the previous Codex/OpenCode comparison.

## Recommendation

Keeping the block removed from the global AGENTS remains the choice supported by these pilots. No quality gain appeared in the three configurations evaluated, and the cost of creating a script in repeat recurred in Opus. This does not prove that each recommendation of the block is useless. The suite is small, synthetic and already at the accuracy ceiling; benefits in harder real tasks, future reuse or recurrence outside these probes were not measured. The overall time difference in this round remains inconclusive.

Offline reproduction: `python3 instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/analyze.py`. Data: [analysis.json](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/analysis.json), [metrics.tsv](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/metrics.tsv), [review-seal.json](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/review-seal.json).
