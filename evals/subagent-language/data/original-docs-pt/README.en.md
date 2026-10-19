> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Language in communication between subagents

Pilot completed on October 11, 2026: 60/60 runs in `results/run-20261011-165334/`,
with no infrastructure errors, with the protocol followed and telemetry reconciled.
The earlier check in `results/run-20261011-161200/` is outside this sample.
Python 3.10+, Git and Codex CLI 0.162.1.
Uses the existing Codex login, with `gpt-6.1-sol` and `high` effort by default.
Requires no external Python dependencies and no additional API key.

## Audited result of the first round

Open the [interactive visualization of the results](show-me-resultados-idioma.html)
to switch the reference, explore the pairs by metric and look up the 60
runs. The HTML works offline and can be regenerated with `python3 build_visual.py`.

The pilot did not demonstrate a general token reduction from adding the English
instruction. There were fewer output tokens and a shorter observed cumulative time, but the total
tokens increased relative to the default behavior. Adoption remains inconclusive.

| Comparison | Total tokens | Output tokens | Cumulative time |
|---|---:|---:|---:|
| English vs default | +2,6% | −6,2% | −3,5% |
| English vs mandatory Portuguese | −0,5% | −5,0% | −3,4% |

These percentages compare the sum of the 20 runs of each condition. They are not the
median of the paired differences. In the English/default comparison, the paired medians
are +2,4% in total tokens, −3,6% in output and −2,4% in time.
The total-token deltas across the 20 pairs range from −18,6% to +41,6%; the time ones,
from −23,1% to +17,9%. English uses fewer total tokens in 9/20 pairs and finishes
earlier in 13/20. Five repetitions per task do not eliminate this variability.

| Condition | Total tokens summed | Output summed | Time summed, seconds | Model calls |
|---|---:|---:|---:|---:|
| Default | 5.113.021 | 98.292 | 2.050,8 | 370 |
| Mandatory Portuguese | 5.274.575 | 97.022 | 2.048,9 | 382 |
| Mandatory English | 5.247.771 | 92.196 | 1.979,6 | 383 |

Inputs dominate the volume. Against the default, English had 2,8% more input
tokens and 13 additional model calls, despite the smaller output. This combination
arithmetically explains why less output did not reduce the total. It does not determine whether
the difference came from tokenization, prose length or strategy. There was no
latency profile separating generation, tools, cache and service load;
the observed time should not be treated as a reproducible speed gain.

The audit identified an error in the answer key for `fornecedor`: the originally
expected order was Alfa, Gama, Épsilon. The request required alphabetical order in Portuguese,
so the correct one is Alfa, Épsilon, Gama. The correction was applied equally to
all conditions, without changing prompts, answers or original records.
Fourteen failures become passes; one pass becomes a failure for ordering.
After the correction, the automatic result is **20/20 default, 19/20 Portuguese and 20/20
English**. The only failure is `trial-0035`, exclusively because of the order of the names.
Ignoring that ordering requirement, the structured decisions are correct in 60/60.
This does not replace the blind review of the explanations, which is still pending.

There are 120 readable final returns and 271 encrypted messages. Full adherence to the
language cannot be verified. The frozen sources were checked by hash;
the counters were recomputed from the rollouts of all 60 runs.
The numerical results and the correction are in [pilot-analysis.json](pilot-analysis.json).
The round's original `report.md` preserves the grades from the old answer key; use this
reassessment to interpret quality. The short check was not included in the calculations.

To reproduce the audit without calling models:

```sh
python3 analyze.py results/run-20261011-165334 --out pilot-analysis.json
```

A next round should investigate the reused history and the number of calls,
besides language, with new tasks. These data do not justify recommending English
between agents as a general saving in consumption or monetary cost.

## Question and scope

Does adding an instruction in Portuguese for the agents to communicate in English
reduce tokens and time on tasks requested and delivered in Portuguese, while preserving
quality? The main comparison is `en` against `default`; the secondary one is `en`
against `pt`. The pilot does not assume that Portuguese consumes a fixed percentage more.

| Condition | Global instruction |
|---|---|
| `default` | Communicate with the user in Portuguese; no language rule between agents |
| `pt` | User in Portuguese and communication between agents in Portuguese |
| `en` | User in Portuguese and communication between agents in English |

The `pt` and `en` conditions use the same sentence, changing only the requested language.
The block covers delegations and replies, preserving quotations and identifiers.
The exact strings are in `run.py` and are preserved in `freeze.json` before execution.
The cost of the instruction is part of the measurement, including when it reappears in the context.

This first pilot restricts collaboration to two direct subagents, created
with `fork_turns="none"`. The orchestrator chooses the division of work and may
exchange additional messages. This measures the instruction in a flow with mandatory
delegation and a clean initial context for each child. It does not estimate the gain when
the agent freely chooses how many subagents to create, nor when it inherits the entire
history. A later study should vary these factors and use real tasks.

## Tasks and size

| Task | Work | Automatic answer key |
|---|---|---|
| `incidente` | Cross-reference operational evidence and change history | Cause, rollback, affected queues and evidence of loss |
| `fornecedor` | Cross-reference requirements and proposals | Eligibility, exclusions, cost and tie-breaker |
| `acessos` | Apply a policy to 16 requests | Decisions including exceptions and time limits |
| `conciliacao` | Cross-reference closing rules and events | Orders included and net revenue per channel |

That is four tasks × three conditions × five repetitions = **60 runs**, with
120 planned subagents in addition to the 60 orchestrators. Do not confuse five
repetitions with five different tasks. The documents are synthetic and in Portuguese.
Answer keys are not placed in the agents' working folder.

Each block contains the same task/repetition in the three conditions. The blocks are
shuffled with a fixed seed and the six permutations of the conditions are distributed
with frequencies that differ by at most one block. Runs of different conditions
are sequential; the subagents may work in parallel within a run.
Model, effort, tools, files and the rule for creating children are the same.

## How to run

In a terminal with normal network access and a Codex login already available:

```sh
cd ~/VSCode/Lab/evals/comunicacao-subagentes/idioma-piloto
python3 run.py run
```

The command creates a new folder `results/run-AAAAMMDD-HHMMSS`, verifies isolation
before the first inference, shows progress and updates `report.md` after each
run. It consumes the login's quota. It does not switch model or provider automatically.

To verify access to the model in another environment, use the short three-condition
check, separate from the pilot sample:

```sh
python3 run.py run --cases incidente --reps 1
```

Check that the three runs finished as `completed`, with `protocol_pass=true`,
three sessions in `telemetry.json`, reconciled counters and two subagent returns.
If the check works, run the full command. Do not add the check to the sample.
A protocol deviation is recorded and does not interrupt the round; infrastructure
errors, timeout or telemetry errors do interrupt. Incomplete output returns code 1.

To choose parameters explicitly:

```sh
python3 run.py run --model gpt-6.1-sol --effort high --reps 5 --timeout 300
```

The limit is 300 seconds per run, including all agents, but excluding
preparation and grading. The round's admission budget is 21.600 seconds.
A block only starts if three individual limits and a 180-second reserve
for preparation fit. This is an admission limit, not a hard deadline for the
whole round. On timeout, the executor terminates the process group and preserves
the partial records. Ctrl-C also preserves whatever is available.
There is no retry by the harness and no resuming of an existing folder. Codex's internal
retries are subject to the timeout and may have no consumption reported by the service.
An incomplete round must be analyzed as incomplete, without silently filling gaps
with a new round.

Commands without inference and report regeneration:

```sh
python3 -m unittest -v test_eval.py
python3 run.py plan
python3 run.py preflight
python3 run.py report --out results/run-AAAAMMDD-HHMMSS
```

`--out` lets you choose a new folder; for `report`, it names the existing folder.
`--auth-file` selects another authentication file without printing its content.

## Metrics and counting

The main consumption is `input_tokens + output_tokens`, summed across all sessions
of the trial. `token_usage_record` records consumption per response. The collector deduplicates
by `(thread_id, response_id)` and checks that the sum matches the last
cumulative counter of the session itself. The CLI's final counter is reconciled as consumption
of the orchestrator or the team and is never summed again. Divergence interrupts the round.
Missing required fields invalidate the measurement, instead of becoming zero.

Cache is part of the input; reasoning is part of the output. Both appear separately,
without being added to the total. Also record consumption of the orchestrator and the children,
number of model responses, tool calls and number of subagents.
There is no automatic conversion to reais/dollars or claim about plan cost.
Repeated input tokens are observed consumption, not unique text produced.

Time is wall-clock, from process launch to its termination, including
coordination, tools, waiting and generation. The durations of children
running simultaneously are not summed. Preparation, file copying and grading are outside
this time. The pilot measures the experience of this CLI, not just model latency.

The report shows per task paired percentage differences, medians and extremes,
with `100 × (en / reference − 1)`. Negative values indicate reduction. It presents both
complete runs measurable regardless of correctness and the subset
in which both sides passed the answer key and the protocol. This second analysis
may suffer selection bias. Failures, not-started runs and deviations are explicit.
Incomplete consumption of failed calls does not count as savings.

A difference in tokens may come from tokenization, shorter responses, fewer
rounds or a different strategy. This pilot does not separate these causes. Do not estimate
latency savings from tokens: measure both. Remote cache and service load
are not controlled; the alternating order reduces, but does not eliminate, their influence.

## Quality, language and decision

`answer.json` has exact grading with types, keys and values defined in the task.
The grader requires preserved inputs and `report.md` to be present, but does not confuse
presence of text with quality. The explanation and the Portuguese require blind
human review according to [REVIEW.md](REVIEW.md). The returns and messages between agents are kept
in `language-review.json`, with language labels initially empty.
The language of internal reasoning is neither requested nor inferred.

The real check revealed that the CLI encrypts delegations and intermediate messages
in the rollouts. The collector recognizes the `encrypted_content` blocks, marks those
messages as `unobservable` and does not export the encrypted content as prose for
review. `communication_observability` shows the coverage; `language_audit_complete`
indicates availability of text in all messages, not approval of the language.
In the check, two final returns per condition are readable; four messages
in `default`/`pt` and six in `en` are not observable. This limits the audit of
adherence, but does not invalidate the comparison of the assigned instruction on tokens and time.
`protocol_pass` covers the delegation structure, not the language. The original
results were preserved; the updated audit is in `smoke-audit.json`.

The main analysis keeps the assigned condition even when the language instruction
is disobeyed. This adherence is part of the instruction's practical usefulness. An analysis
restricted to those who obeyed may be exploratory and must be identified separately.

The automatic report keeps the adoption verdict inconclusive. Even five
repetitions on four tasks do not demonstrate quality non-inferiority nor
generalize to programming, web research or inherited history. Before a
confirmation, define the minimum useful gain, the acceptable regression margin and new cases.
Do not choose the best wording on these tasks and present the same sample as confirmation.

## Isolation and files

Each trial gets its own temporary directory, Git repository, Codex state and configuration.
`CODEX_HOME` is set only in the child process environment. The authentication
file is copied to the temporary state with 0600 permission and removed
at shutdown. The user's real profile and instructions are not changed.
Skills, plugins, apps, memory, hooks and web are disabled. Agents are enabled.

The adapter derives from the runtime in `instrucoes-agents/agentsmd-detfirst-isolated/`,
with explicit subagent configuration and parameterized model/effort. The local copy
allows freezing the entire implementation of this pilot without changing old studies.
The `codex debug prompt-input` inspection disables discovered skills and compares the
instructions actually visible. This is not an HTTP capture nor full isolation of
filesystem reads; the agent could read files outside the working folder.

`freeze.json` stores tasks, answer keys, conditions, order and source hashes before
the first inference. `frozen-source/` stores the corresponding version. Each trial
preserves the prompt, inspected context, events, stderr, rollouts of all
sessions, final artifacts, grades and metrics. Credentials are not copied to results.

The agent options follow the [official Codex reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The telemetry format is checked against the installed CLI and pinned to version
0.162.1. A version change requires reviewing the collector before generating new results.
