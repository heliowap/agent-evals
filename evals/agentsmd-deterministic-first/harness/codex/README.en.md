> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Isolated eval of Deterministic first

Status: pilot completed on 10/10/2026. All 72 runs passed, including the
12 controls reviewed against the rubric. There was a quality tie and a longer
observed duration with the snippet. See the [full analysis](../../agentsmd-codex-pilot-analise.md).

It compares Codex CLI 0.162.1, `gpt-6.1-sol`, reasoning effort `xhigh`, with two
private global instruction files. `variants/empty/AGENTS.md` has zero
bytes. `variants/deterministic/AGENTS.md` contains only the snippet supplied by the
user, without rewriting. The real global `AGENTS.md` is not changed.

This experiment measures the effect of the snippet on the CLI's basic configuration.
It does not measure its marginal effect on the user's complete set of instructions and skills. The
model's system prompt and the CLI's internal instructions remain
the same in both conditions. They may already induce part of the tested behavior.
The experiment evaluates the whole snippet; it does not attribute causality to each sentence.

## Hypotheses and criteria

Main hypothesis: the snippet increases the proportion of tasks delivered correctly.
Secondary hypotheses: it reduces consumption and duration for correct deliveries, increases
tool reuse and creates checks that detect recurrence of errors.
Possible harms: unnecessary scripts, out-of-scope changes, excess
automation for subjective decisions and concurrent execution of dependent steps.

Correctness and obedience are separate measures. Using a script, running commands in
parallel or creating a test does not raise the result score by itself. The exception is
when the task itself asks for a verifiable prevention. In that case, the grader
introduces the defect and verifies that the protection works, including on valid cases.

The pilot has 12 synthetic tasks, two conditions and three repetitions: 72 runs
in 36 pairs. The repetitions measure variability over the same data. They are not 36
independent tasks. Three repetitions do not support a conclusion about speed;
a confirmatory study would use at least five and new real cases.

| Case | Group | Result evaluated |
|---|---|---|
| count | actions | Exact count with time limits and numbers that confuse naive searches |
| money | actions | Integer sum, with negative values and filters by currency/state |
| convert | actions | Conversion with correct types, leading zeros, Unicode, quotes and line breaks |
| rename | actions | Renaming across several modules, preserving a similar name and behavior |
| project_tool | actions | Correct report when the project already offers a tool |
| repeat | actions | Three correct summaries in two turns of the same session |
| guardrail | rules | Checker rejects forbidden calls and accepts comments, strings and methods |
| regression | rules | Correct code and a test that fails when the defect reappears |
| out_of_scope | controls | Correct review and prevention proposal, without editing files |
| judgment | controls | Adequate text, with all facts preserved and no additional changes |
| independent | actions | Real results of three commands; overlap is a secondary observation |
| dependent | controls | Configuration and generated artifact correspond to the same state |

For `out_of_scope` and `judgment`, the automatic checks are partial. Acceptance
depends on the blind review defined in `REVIEW.md`. Do not count these checks as
sufficient proof of quality. The groups have artificial composition; the average
does not estimate the gain in the user's everyday work.

## Isolation and evidence

Each run has its own working directory, Git repository, Codex state and
temporary files. The runner uses an environment dictionary specific to the
child process and points the supported `CODEX_HOME` setting to that state.
It does not change `HOME`, the user's shell variable or their installed configuration.
Only the indicated authentication file is copied, with 0600 permission. It
stays in the temporary state, outside the results, and is not printed.

The CLI runs with `--no-daemon`, `workspace-write` sandbox and `never` approval.
Plugins, apps, hooks, memory and multi-agent are disabled in the private
configuration. The temporary directory has its own Git. There are no symlinks to the
global configuration, nor runner skills or instructions inside the cases.

Before any inference, `codex debug prompt-input` reveals the instructions
that will be presented to the model. The preparation discovers and disables each skill
by the path of its `SKILL.md` and repeats the inspection. In the pinned version, disabling
only the folder path does not remove the skill. The run stops if a skills
catalog still exists, if the empty condition has `AGENTS.md` instructions, or if the
other condition does not contain exactly the expected snippet. `isolation.json`
preserves the inspected context, hashes and requested configuration.

This isolation prevents automatic inheritance of instructions. It is not complete
isolation from operating-system reads: an agent command could still
read files outside the case. The answer key stays in the controller process, not in the
working directory. Inspecting the context is not a capture of the HTTP request to the
provider. Version, model and effort are fixed in the arguments/configuration;
the remote service and its implementation are not controlled by this study.

The instructions loaded by Codex combine global and local scopes. The official
documentation describes this discovery in
[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
The configuration options are in the
[official reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The effective behavior of disabling skills is verified by the installed CLI.

## Execution

Dependencies: Python 3.10+, Git and the indicated version of Codex CLI, with login already
available. The tasks do not depend on external Python packages.

```sh
cd ~/VSCode/Lab/evals/instrucoes-agents/agentsmd-detfirst-isolated
python3 -m unittest -v test_eval.py
python3 run.py preflight --out validation/isolated-context
python3 run.py plan --out plans/pilot
python3 run.py run --out results/pilot
python3 run.py report results/pilot
python3 run.py blind results/pilot
```

The `plan` command is offline. `run` uses the model and effort chosen by the user,
with no fallback, and consumes the login's quota. `--auth-file /caminho/auth.json` allows
selecting the authentication file. The default is that of the installed Codex. Do not put
credentials in the terminal or in the study files.

A small access round uses the same cases, but is separate from the pilot:

```sh
python3 run.py run --out results/smoke --cases count --reps 1 --timeout 120 --budget-seconds 300
```

The results directory must be new. `freeze.json` records hashes of the
code, protocol, variants, cases and order before the first inference.
The pairs are drawn with seed 20261010 and the order of conditions is balanced.
One condition runs at a time, to reduce resource contention. The parallelism
rule is evaluated within the task. `repeat` continues only its own
session, never a session from the other condition.

The default limit is 600 seconds of agent per run and 7200 seconds of round
budget. A pair only starts if both individual limits still fit in the
balance. Preparation and grading are additional to the individual limit. The runner
interrupts the process group on timeout, preserves the events and stops at the first
infrastructure failure. It does not retry or switch model/provider. Any internal
retries of the CLI are subject to the same limit. Interruption or exhaustion
of the budget leave runs `not_run`; they do not count as hits.

## Metrics and analysis

Record per run: result of each check, final answer, artifacts,
CLI events, tool calls, time and reported tokens. Preserve
failures, timeouts and absences. Fast errors are not speed gains.

Input and output are the native counters of `turn.completed`; cache is reported
separately, without adding it again to the input. Missing fields stay unknown.
The counter is cumulative in the session, including after `exec resume`. Use only the
last terminal event, without summing overlapping turns. The audit of the 72 rollouts
confirmed this semantics. The totals derived from the six `repeat` cases in the original
pilot duplicate the first turn; the analysis uses the corrected `usage_raw[-1]` and
preserves the original JSONs. Do not infer reais,
dollars, OAuth being free or reasoning tokens that are not reported.

The report separates cases and conditions, shows the planned denominator and computes
an exploratory difference of automatic passes on the complete pairs. The interval
uses bootstrap by case, not by repetition, preserving the pairing. Read the failure
rate alongside this analysis; differential exclusion can bias the result.
Blind review and behavioral inspection are recorded separately. Times of
incorrect deliveries do not justify an efficiency recommendation.

The pilot always produces an inconclusive verdict on adoption. It serves to locate
effects, costs and failures of the cases. Before a confirmation, freeze new tasks,
the minimum useful improvement and the regression/cost tolerance. Do not tune the snippet based
on the cases and then present those same cases as independent confirmation.

## Validation status

`verification.json` records the local tests and the context inspection performed.
These checks validate the execution/grading mechanism, they do not prove a gain from the snippet.
The earlier evaluation in `../agentsmd-detfirst/` remains independent of this study.

On 10/10/2026, the short round `results/smoke/` attempted one run and stopped before
a model response: `workspace routing discovery failed`, accompanied by
connection errors when updating the catalog. The other condition stayed `not_run`.
There is no valid comparison of quality, tokens or speed in that round.
In the run requested next, `results/pilot-20261010-r1/` attempted the first
of the 72 scheduled cases and stopped with the same error; 71 were left not started.
The diagnosis confirmed `CODEX_SANDBOX_NETWORK_DISABLED=1` and a DNS failure for
chatgpt.com in the controlling environment. These two attempts were left incomplete.
The round `results/pilot/`, run in the user's terminal, completed 72/72.

The [analysis](../../agentsmd-codex-pilot-analise.md) reconciles scores, review of the controls and
corrected tokens. The protocol, rubric and sources used in the round are in
`results/pilot/frozen-source/`, checked against the hashes in `freeze.json`
before the counter correction. Cases, treatment and scores were not changed.
The regression test for the count reproduced the duplication before the fix.
