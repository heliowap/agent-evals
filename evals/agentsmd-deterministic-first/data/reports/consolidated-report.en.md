> English translation of [consolidated-report.md](consolidated-report.md). The original is kept verbatim as an archived artifact.

# What the evals show about "Deterministic first"

Consolidated report of October 10, 2026.

## The conclusion for the global AGENTS

The three isolated pilots showed no accuracy gain from the snippet. In each configuration, the agent correctly delivered all 36 tasks without the instruction and all 36 with it. The text changed some working methods and increased the output volume, but this change did not improve the measured delivery.

Keeping the snippet removed from the global `AGENTS.md` remains the decision best supported by these results. This is a provisional decision about the complete block. The study does not show that using tools, creating tests or running commands in parallel is useless.

The most repeated finding was an additional cost in the repeated-processing case. The agent already computed the results with Python without the block. With it, it began creating a script file and doing additional checks. In all three configurations, the final delivery remained correct, but took longer in this case.

## The question that was tested

The snippet contains two main guidelines. The first asks that verifiable rules be implemented as executable safeguards, such as tests and linters. The second asks that computable outputs be produced by tools or scripts, preferring the tools already in the project.

The text also includes specific obligations: create a script when a step repeats for the second time, verify new scripts, keep disposable scripts in a temporary folder and parallelize independent commands.

The [exact snippet evaluated](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/frozen-source/variants/deterministic/AGENTS.md) is preserved with the evidence.

These recommendations could bring different gains:

| Expected gain | How it would appear in the work |
|---|---|
| More accuracy | Fewer errors in counting, calculation, transformation and batch editing |
| Less recurrence | A test or a check rejects the return of a defect |
| More efficiency | Shorter duration or lower consumption for an equally correct delivery |
| Better reuse | The automation reduces work on later requests |
| Better scope control | The agent proposes a safeguard when the task authorizes only reviewing |

The possible cost is preparing automations and checks that do not pay off during the task. That is why the eval assessed the result, in addition to observing the method. Creating more scripts or calling more tools earns no points by itself.

## How the comparison was made

Each configuration was run under two conditions. The control received a zero-byte `AGENTS.md`. The treatment received only the original snippet, of 992 bytes. The rest of the user's global instructions did not enter this comparison.

12 cases were used, three repetitions of each case and two conditions. This produces 72 runs per configuration, grouped into 36 pairs. The first condition of each pair was balanced: 18 pairs started with the control and 18 with the treatment.

| Configuration | Provider or route | Runs completed |
|---|---|---:|
| Codex CLI with Sol 6.1 `xhigh` | Codex integration | 72/72 |
| OpenCode 2.0.25 with Sol 6.1 `xhigh` | `openai/gpt-6.1-sol#xhigh` | 72/72 |
| OpenCode 2.0.25 with Opus 5.5 `medium` | `cli_proxy/cpa-claude-opus-5-5#medium`, via CPA | 72/72 |

The three isolated rounds add up to 216 runs. They repeat the same 12 synthetic cases, so they do not represent 216 independent problems.

Each product's internal instructions remained present in both conditions. The audit verified the available isolation, the model and effort selections and configuration discovery. It did not capture nor show full equality of the HTTP requests to the providers. In CPA, the identity recorded on the client also does not, by itself, attest which model the upstream service delivered.

The preliminary package `agentsmd-detfirst` is preserved as history. Its functioning tests and attempts do not enter the consolidated numbers of this report.

## What the 12 cases measure

| Case | Task | Main criterion |
|---|---|---|
| `count` | Count log records with status and time filters | Exact integer |
| `money` | Sum values in cents with filters | Exact total |
| `convert` | Convert CSV to JSON | Preserve content, order and types |
| `rename` | Rename an identifier across several files | Change the correct uses and preserve behavior |
| `project_tool` | Produce a project report | Respect the contract of the available tool |
| `repeat` | Process three batches in two requests of the same session | Three correct summaries and observation of reuse |
| `guardrail` | Prevent future uses of `eval` | Check rejects forbidden calls and accepts permitted uses |
| `regression` | Fix inverted limits in `clamp` | Tests detect the reintroduction of the defect |
| `out_of_scope` | Review a parser without editing files | Identify the defect and recommend executable prevention |
| `judgment` | Rewrite a delay message | Clear text, facts preserved and change restricted to the requested file |
| `independent` | Run three independent checks | Correct real results and observation of temporal overlap |
| `dependent` | Change configuration, generate and verify a file | Result consistent with the new configuration and the necessary order |

The two judgment cases received review by the assistant using the rubric defined before the answers. The labels were hidden in the review, but the assistant knew the design and aggregate metrics. Some answers also suggest which instruction they received. There was no independent human review nor a guarantee of complete blinding.

## Equal accuracy in the three configurations

| Configuration | Without the snippet | With the snippet | Observed gain |
|---|---:|---:|---:|
| Codex with Sol | 36/36 | 36/36 | 0 percentage points |
| OpenCode with Sol | 36/36 | 36/36 | 0 percentage points |
| OpenCode with Opus via CPA | 36/36 | 36/36 | 0 percentage points |

This means the yardstick did not find a better delivery caused by the block. It does not mean the two conditions are equivalent in any situation. The control already reached the accuracy ceiling, so the suite offers little opportunity to show quality improvement.

There is also a distinction between delivering correctly and following each preference in the text. In `independent`, the correct result counts as a success; the overlap of the commands is recorded separately. With Opus, the three checks overlapped in one of the three runs without the block and in none of the three with it. Therefore, 100% accuracy does not prove perfect obedience to the instruction to parallelize.

In the `guardrail` and `regression` cases, both conditions built safeguards that passed the recurrence tests: six deliveries per condition, in each configuration. These prompts already ask for prevention explicitly. The result does not measure whether the block would make the agent spontaneously propose a safeguard in a task that does not request it.

## Duration increased in aggregate, with different effects per case

The time below is the mean duration of the agent invocations. It includes initialization and tools, but excludes preparation, audit, export and correction of the eval. It is not the total process time nor an isolated measure of model speed.

| Configuration | Without the snippet | With the snippet | Observed difference |
|---|---:|---:|---:|
| Codex with Sol | 40.46 s | 47.37 s | +17.1% |
| OpenCode with Sol | 34.14 s | 42.17 s | +23.5% |
| OpenCode with Opus via CPA | 12.70 s | 13.43 s | +5.8% |

The aggregate signal was unfavorable to the snippet in the three rounds. Even so, duration varies by task, call and remote service. There was no profile to separate inference, proxy, network, initialization and tools as causes of this difference.

With Opus, the overall difference is inconclusive. The treatment was faster in 18 of the 36 pairs. An exploratory 95% interval, computed after the round by resampling the 12 cases, was approximately −7.0% to +24.1%. Since it includes zero, the data are compatible with both a reduction and an increase in duration in this cut.

### The clearest example: repeating the processing

In `repeat`, the user first asks for the summary of batch A and then asks the same for B and C.

Without the block, the agent already uses Python and a loop to process B and C. With the block, it creates a reusable temporary script and verifies it. The difference lies in the work of preparing the automation, with no change in the delivered result.

| Median of the `repeat` case | Without the snippet | With the snippet |
|---|---:|---:|
| Codex with Sol | 48.49 s | 84.79 s |
| OpenCode with Sol | 42.44 s | 82.79 s |
| OpenCode with Opus via CPA | 12.53 s | 24.42 s |

In each configuration, the three runs with the snippet were slower than all three without it. Excluding only this case as a sensitivity analysis, Opus's aggregate difference changes from +5.8% to −1.6%.

The same cost pattern appeared in Codex and in OpenCode with Sol. This weakens the universal rule of creating a script file on the second repetition. The eval did not measure whether this investment would pay off after dozens of reuses or in larger tasks.

## Tokens require attention to how they are counted

Products and providers do not separate input, cache, output and reasoning in the same way. Comparing two fields called `output_tokens` without checking the meaning can produce a wrong conclusion.

| Configuration | Counter used on this line | Without the snippet | With the snippet | Difference |
|---|---|---:|---:|---:|
| Codex with Sol | Output, including reasoning | 35,800 | 43,232 | +20.8% |
| OpenCode with Sol | Output plus reasoning, portions summed | 31,298 | 40,328 | +28.9% |
| OpenCode with Opus via CPA | Output reported by the provider | 28,740 | 33,034 | +14.9% |

Each line compares the two conditions within the same configuration. The CPA line does not provide an audited measure of separate reasoning or of total cost.

In the Codex round, the token counter was cumulative across the two turns of `repeat`. The original runner summed the cumulative values and duplicated the first turn. The analysis corrected the aggregation to use only the last counter, checked against the usage records. The raw results were preserved.

In CPA, only two or four native input tokens per message were reported, large volumes of cache and zero reasoning. This does not prove the absence of internal reasoning. We keep these portions separate and do not infer financial savings from them. No comparison in this report is equivalent to a reconciled invoice.

## Comparing products is a different question

The experiment was designed to compare empty versus snippet within each configuration. Using its results to compare products or models requires more caution.

With Sol `xhigh`, OpenCode had 13.1% less accumulated duration and 55.3% fewer normalized tokens than Codex, on the same 72 combinations of case, repetition and condition. The normalization included cache and reasoning according to each product's accounting.

In the later round, Opus via CPA had a mean duration 62.8% lower than Sol in OpenCode without the snippet and 68.1% lower with the snippet. The deliveries passed the same yardstick.

These are exploratory comparisons. Products have different internal instructions and tools. In the comparison with Opus, the model, effort and provider also changed. The rounds were not interleaved between these configurations. The numbers describe what happened, but do not identify which component caused the difference nor establish an overall winner.

## What to do with the result

The current decision is to keep the complete block out of the global `AGENTS.md`. It showed no measurable accuracy gain in these pilots, and the obligation to create scripts added work in a repeated case in the three configurations.

To reconsider the decision, the next test should use real tasks in which the control still makes errors. It also needs to measure rework, recurrence and later reuse, in addition to the first delivery. The minimum quality gain and the tolerable additional cost must be defined before observing the answers.

Testing `Rules`, `Actions` and the second-repetition rule separately would help locate benefits. A short version was not evaluated here and cannot be treated as an already validated solution.

## Reports and evidence

The reading reports are at the root of `evals/`. The executable packages, raw data, reviews and frozen sources are grouped by theme. The originals of the reports remain together with the evidence to preserve audits and hashes.

| Material | Location |
|---|---|
| Detailed result of Codex with Sol | [Codex analysis](agentsmd-codex-pilot-analise.md) |
| Detailed result of OpenCode with Sol | [OpenCode with Sol analysis](agentsmd-opencode-pilot-r2-analise.md) |
| Detailed result of OpenCode with Opus | [OpenCode with Opus via CPA analysis](agentsmd-opencode-opus-5-5-medium-analise.md) |
| Packages and execution instructions | [Theme: instructions for agents](instrucoes-agents/README.md) |
| Other themes and reports in the collection | [Evals index](README.md) |

This report brings together the existing analyses. Its preparation and the reorganization of the files did not run new inferences.
