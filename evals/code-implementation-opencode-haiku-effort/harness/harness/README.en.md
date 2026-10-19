> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Implementer eval in OpenCode

Status: plan approved and runner implemented. There are 20 TypeScript/Node and Python tasks, plus the smoke test and the interruption proof. Running with models depends on the gates described below; there is no comparative result for this role yet. The goal is to select configurations to receive a bounded task and deliver a working change, preserving the rest of the project.

## Configurations

| Configuration | OpenCode selection | Reason to compare |
|---|---|---|
| Sonnet 5.5 medium | `cli_proxy/cpa-claude-sonnet-5-5#medium` | Initial candidate for bounded changes; good local result in the exploration role |
| Sonnet 5.5 high | `cli_proxy/cpa-claude-sonnet-5-5#high` | Check whether additional effort improves implementation, without extrapolating from the exploration eval |
| Sol 6.1 medium, Fast selected | `openai/gpt-6.1-sol-fast#medium` | OpenAI candidate with native OAuth; the previous test got all literal answers right |
| Sol 6.1 high, Fast selected | `openai/gpt-6.1-sol-fast#high` | Measure the gain from effort on code with a control within the same family |
| Opus 5.5 medium | `cli_proxy/cpa-claude-opus-5-5#medium` | Higher-capability reference for tasks that require judgment |
| DeepSeek V4.1 Flash max | `opencode-go/deepseek-v4.1-flash#max` | Representative of the Go subscription on a route already exercised locally |

These are comparison hypotheses, not a ranking of implementers. The [OpenAI documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol) describes Sol for complex coding work and supports medium and high. The [Anthropic announcement](https://www.anthropic.com/claude-sonnet-5-5) describes Sonnet for bounded tasks and bug fixes, and Opus for complex work requiring more judgment. The choice of efforts and the composition of the matrix are decisions of this design, not recommendations proven by vendor benchmarks.

DeepSeek is listed in the [Go offering](https://opencode.ai/docs/go/) and in the local catalog. GLM-5.3 and Kimi K2.7 Code may be added in a later expansion, if the goal becomes comparing Go alternatives. Not adding them now limits the size of the first matrix.

Gemini stays out of the initial round until backend identity, effort and agent termination are verified. The [second exploration round](../../exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/analysis.md) had 17 errors at termination due to the limit, answered with the identifier `gemini-3.8-flash-n` and showed stream flags whose cause was not preserved.

Both Sol configurations keep Fast selected to maintain the OAuth configuration already in use. The report must distinguish selection, forwarded priority and the terminal tier actually served. The previous trials returned default; no budget or result presumes Fast was served. The published API costs do not estimate consumption of the OAuth, Anthropic-via-CLIProxy or Go subscriptions.

## Role and deliverable

Each session receives a delegation with the desired behavior, acceptance criteria, constraints, entry points and public test commands. The candidate may explore, edit files and run checks inside the project. It does not receive a suggested solution, hidden tests or grader feedback.

A user message starts each trial. The agent may run several cycles of editing and public tests. There is no second corrective message, no auxiliary reviewer helping during the run, and no web, MCP or subagents. Instructions and tools are the same across all configurations. The final response is free text with a summary; JSON or exact citations are not required.

The deliverable evaluated is the patch actually produced. A claim of success does not replace tests. The role is a delegated implementer, not an agent that must discover and clarify an open issue before working.

Example of a public statement:

> Add cursor pagination to the order listing. The cursor must preserve the ordering by date and ID, including when two orders have the same date. A following page must not repeat items. Preserve the tenant filter and the behavior of clients that do not supply a cursor. Start from the orders handler and the indicated repository. Include tests and run the project's public commands.

## Screening tasks

There are 12 distinct cases, six TypeScript/Node and six Python. Each case uses a small project with explicit layers and dependencies. The scenarios represent patterns from real projects, with new contracts; curation may incorporate real snapshots when a reproducible equivalent task exists. Avoid isolated functions whose only job is to complete a few lines.

| Family | TypeScript/Node case | Python case |
|---|---|---|
| Cross-layer feature | Cursor pagination with stable ordering and compatibility | Batch import with validation, summary and atomicity |
| Correctness and side effects | Retry of an idempotent operation without duplicating effects | Transaction rollback with publishing only after commit |
| Authorization and scope | New operation without cross-tenant access | Query with tenant, owner and soft deletion |
| Validation and contracts | Missing, null and empty fields with an explicit contract | Monetary values and limits without improper rounding |
| Streaming and cleanup | Cancellation of an async iterator releasing the resource once | Early closing of a generator and cleanup on exceptions |
| Refactoring with preservation | Consolidate conversions and remove a specified internal API | Unify exporters preserving interfaces and behavior |

The confirmation set uses eight new tasks, four per language, covering the same families. No confirmation case may be used to choose finalists or adjust prompts. Renaming the screening cases is not enough.

Before admitting a task, run the baseline and the reference solution in the grader. The baseline must fail the new requirement and the reference must pass. In a refactoring, the behavioral tests may pass from the start; the public structural requirement must distinguish the requested change. Never require equality with the reference patch.

The hidden tests verify behaviors described in the statement, including their edges. They do not add surprise requirements. Dependencies and clocks are fixed, with external network replaced by deterministic local components when it is not part of the task.

## Full approval

An attempt receives full approval only when it satisfies all the criteria:

1. The session ends normally within the budget, with the requested identity and effort.
2. The patch implements the whole contract, as shown by the private acceptance tests.
3. The original regression, compilation and type-check suite keeps passing in the grader's trusted environment.
4. The diff respects the task's public scope. It does not modify the evaluation mechanism, nor replace behavior with fixed returns for the examples.
5. The explicit structural requirements, when there are any, are met.

Record `patch_correct`, `session_completed`, regressions, scope violation, limit exceeded and integration failure separately. This makes it possible to show a correct patch left by an interrupted session without pretending to full approval. Every attempt started enters the operational denominator; a transport failure does not become evidence of inability to implement.

Tests written or edited by the candidate are part of the deliverable, but do not define the result. The grader reapplies only the permitted patch on a clean copy and uses the original suite, trusted dependencies and its private tests. A refactoring may have several valid patches.

## Diff quality

Functional approval is the primary metric. Diff review is secondary and blind to model, effort and route. Its rubric has four criteria, each from zero to two:

- Clarity and coherence with the project's patterns.
- Changes pertinent to the contract, without unrequested changes.
- Tests in the deliverable that exercise relevant behavior and regressions.
- Handling of limits, errors and resources in the cases where this is part of the task.

The score does not compensate for a failed functional test. Number of lines and files is descriptive; it does not penalize a solution for being larger or smaller. If an LLM judge is adopted, evaluate the patches under neutral identifiers, on the same rubric, with human review of disagreements. Account for that judge's calls separately. The initial plan does not depend on LLM scores to decide approval.

## Phases and size

| Phase | Composition | Planned sessions |
|---|---|---:|
| Termination proofs | One per configuration, with reduced budget | 6 |
| Implementation smoke | One small change per configuration | 6 |
| Screening | 12 cases × 6 configurations × 3 repetitions | 216 |
| Confirmation | 8 new cases × 2 finalists × 5 repetitions | 80 |
| Total, if all phases are run | | 308 |

That is 302 smoke and comparison sessions, plus six termination proofs that also use models. Session, step, model call and tool call are different counts. The total of calls, tokens and any LLM review cannot yet be estimated without the smoke. Do not add checks without inference to model consumption.

Three repetitions support exploratory screening of approval, not a claim of latency advantage. Select finalists by functional approval balanced per case, with operational errors exposed and critical defects highlighted. If the results do not distinguish two configurations with confidence, report the tie; do not force an elimination over a small time difference. A third finalist would add 40 confirmation sessions, totaling 348.

Confirmation allows comparing five repetitions per task, median and range, plus pairs in which both delivered approved patches. Do not call each finalist's 40 attempts 40 independent tasks; they are eight tasks. Do not mix screening and confirmation to declare a result about cases that influenced the selection.

## Budget and termination

The initial proposal is a limit of 20 minutes per task and a target of 60 model calls per session. The smoke calibrates this budget for representative tasks before freezing the comparison. All configurations receive the same limit. Reasoning, internal attempts and retries count toward consumption.

Use an external controller that follows the session and interrupts it on reaching the budget. The local version offers `session.interrupt`; the `budget` phase must prove interruption, termination of subprocesses and capture of the patch. A call already in progress may finish during the interruption, and the report must record any overrun. The external timeout is the last barrier.

Do not configure the comparative budget only as `agent.steps=60`. The local OpenCode adds an assistant turn on reaching any native limit; raising 25 to 60 shifts the mechanism that failed on Gemini. The effective configuration must verify that the native limit does not trigger this path before the controller does. The same termination policy applies to all integrations.

Freeze the global budget per batch after the smoke. Since the OAuth validity must cover each batch, long rounds may be split only between complete case-and-repetition blocks. Renewal happens in the normal OpenCode session, without rotating refresh tokens on a disposable copy. We do not promise a total duration based on the explorer's time.

## Isolation, transport and measurement

Each trial receives a private filesystem and state. OpenCode and the providers run on the host; the only tool available to the agent is `terminal`, executed in a Linux container without network and with only the project mounted. Reading, editing and tests use this same tool in all six configurations. The native read, edit and shell tools are removed. Therefore, the result measures implementation with this isolated terminal, not OpenCode's usual set of tools. The gate verifies the effective list and rejects tools outside the terminal.

Hidden tests and solutions stay outside the candidate's filesystem. The grader receives the patch on a clean copy in another container, restores the original public checks and adds its private checks. `external_directory=deny` alone would not be operating-system isolation. The preflight requires real proofs of mounting, denied access to external files, disabled network and termination of subprocesses.

Pre-install dependencies before measurement, with frozen versions and lockfiles. Installation must not vary by candidate. Public tests, code and normal context remain available; experiment artifacts, solutions and fix history stay out. Project directories and prompts do not reveal that there is a comparison or a judge.

Keep OpenCode, native OAuth, variants, frozen local cache and HTTP/WebSocket observation. CLIProxy is accessed by OpenCode on the host at `127.0.0.1:8317`; the code container does not need to reach providers. Skills are disabled. The only local plugins are the passive observer and the isolated terminal. The Docker endpoint is resolved on the host and frozen without mounting credentials or the socket inside the container.

Record the observer's original error code, distinguishing stream cancellation, transport failure, unsuccessful HTTP, limit exceeded and task failure. Do not repeat the loss of information from the Gemini round. Metadata sent and received remain separate; the chosen name does not prove the model executed upstream.

The schedule is sequential, organized by case and repetition blocks with balanced order. Each candidate uses a new session, but remote cache may persist. Measure the complete invocation, including public tests run by the agent. Show external preparation and grading separately. Input, output, reasoning and cache tokens do not equate to comparable subscription consumption.

## Runner and usage

`domain.py` defines tasks, configurations and budget. `tasks_python.py` and `tasks_typescript.py` hold the projects and the private verifiers. `bench.py` freezes sources, catalog, schedule and parameters; runs the gates and generates `summary.json` and `report.md`. `controller.py` follows calls and time, using `session.interrupt` on the same server as the session. `runtime.py` prepares the private OpenCode and verifies transport, identity and effort. `grader.py` reapplies the permitted patch without running candidate code on the host. The explorer's files remain separate.

Requirements: OpenCode 2.0.26, credentials in the normal installation, local catalog at `~/.cache/opencode/models.json`, accessible Docker and active CLIProxy. The image pins Node 24.9.0, TypeScript 5.9.3 and the Python provided by the image; the preflight records actual versions and freezes the image content ID. Local fixture validation uses the host's Python/Node and the TypeScript 5.9.3 present in the Bun cache; this check does not replace validation in the containers.

Run from the root of this repository. Each `--out` must be new; earlier evidence is not overwritten.

```sh
python3 -B implementacao/opencode-implementador/bench.py validate \
  --out implementacao/opencode-implementador/results/validate-screening
python3 -B implementacao/opencode-implementador/bench.py validate \
  --phase confirmation --candidates sonnet-medium,sol-fast-medium \
  --out implementacao/opencode-implementador/results/validate-confirmation

python3 -B implementacao/opencode-implementador/bench.py run \
  --phase budget --build-image \
  --out implementacao/opencode-implementador/results/budget
python3 -B implementacao/opencode-implementador/bench.py run \
  --phase smoke \
  --budget-proof implementacao/opencode-implementador/results/budget \
  --out implementacao/opencode-implementador/results/smoke
python3 -B implementacao/opencode-implementador/bench.py run \
  --phase screening \
  --budget-proof implementacao/opencode-implementador/results/budget \
  --smoke-proof implementacao/opencode-implementador/results/smoke \
  --out implementacao/opencode-implementador/results/screening
```

The two names in the confirmation validation command serve only to require an explicit list; validation does no inference and does not choose finalists. After screening, use the chosen finalists in `run --phase confirmation --candidates ...`, with the same `--budget-proof` and `--smoke-proof`. That is 80 sessions for two finalists.

`plan` freezes the schedule without inference; `preflight` verifies the environment, references in the container, native configuration and export of an empty session without calling models; `report --out PATH` recalculates the report. The export uses the CLI identifier `experimental.session.export`. `--block-start` and `--block-count` delimit complete case/repetition blocks for new batches. The default global budget is six hours; the OAuth validity must cover this batch, and the runner only starts another block before the global limit. A block in progress may exceed it. Adjust `--global-seconds` and the number of blocks to the available period, renewing OAuth in the normal installation before starting.

The required OAuth window includes the last complete block and conservative margins for preparation, grader and audit. These margins are reserve limits, not duration estimates. Validity is checked again before each block; the private copy does not renew tokens. The report shows the median, observed minimum/maximum and time ratios between approved pairs; it does not compute a confidence interval nor prove a statistical advantage by itself.

The interruption proof uses 20 seconds and two calls as reduced limits. Smoke and comparison initially use 1,200 seconds and 60 calls per session. The controller records which limit triggered, any excess call, native interruption and container stop. There is no automatic retry of an attempt. The report separates planned, started and not executed; the operational approval rate uses all started attempts, including failures.

In the `budget` phase, `budget_exceeded` is expected and the metric is `proof_passed`, shown per trial. `accepted=False` indicates that the session did not complete an implementation; it is not the criterion of the interruption proof. Proceed to the smoke only when `gate_passed=true` and all six proofs pass. The `budget-r3` round passed five proofs and revealed a race in the HTTP observer: the pending read tried to close an already cancelled stream, producing a false `ERR_INVALID_STATE`. The observer now ends the pending read without operating on the cancelled stream; real read or cancellation failures are still recorded. The fix requires a new gate with the same six configurations and new frozen sources.

Files and catalog must remain the same as at the gates, including this README. If the smoke justifies changing the budget or code, use new directories and redo the gates before the comparison. Blind diff review remains secondary and manual; the runner does not invent a score nor choose a winner automatically.

## Design decision and next steps

Two independent sketches compared bounded tasks and snapshots of real repositories. The review gave both 9/10: the first reduces initial curation, the second increases representativeness. The chosen basis is the bounded set, incorporating contextualized projects and requirements derived from real work. The comparison avoids mainly measuring the discovery of an issue, and the confirmation reserves new tasks.

Foundational Thinking guided the separation between task, configuration and result. Explain the Number requires distinguishing correct patch, completed session, integration failure and time. Independent work stays in the curation and validation of each task; credentials, schedule and reports have one owner. All comparative sessions remain sequential.

Next operational gate: complete the interruption proof and run the smoke. In the `budget-r2` round reported by the user, isolation, tools and configuration audit passed. The first trial recorded two Sol calls and failed on the terminal's return contract and on session export. Both were fixed; confirmation of the gates with the fixes remains pending. Here, access to the Docker socket returns permission denied and opening loopback returns EPERM; this prevents running the real gates in this sandbox.

If a namespace or version command returns a failure, `preflight.json` keeps `isolation.namespace` and `isolation.versions`, with the exit code, stdout and stderr of each command. The credentials proof requires the file to be inaccessible: absence or `PermissionError` are valid results for an unprivileged process. A preflight failure continues to block inferences. After fixing the runner, repeat the gate in a new `--out`; the existing image can be reused without `--build-image` when the Dockerfile has not changed.

`control.json` is saved before export to preserve limits, interruption and container termination if the export fails. The terminal returns its result in `content`; it does not declare `output` without an output schema. The optional regression `verify_native_terminal.mjs` runs the plugin's return in the validator of the local OpenCode checkout, with dependencies already installed. It requires Bun, `OPENCODE_SOURCE`, `OPENCODE_DEPS` and `OPENCODE_EFFECT`; the Effect version must match the catalog of that checkout. This proof uses the local code and a controlled Docker process, without a server or models; the real gate remains mandatory for the OpenCode 2.0.26 binary.
