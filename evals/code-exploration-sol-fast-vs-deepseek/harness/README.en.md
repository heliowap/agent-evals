> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Comparison of explorers in OpenCode

The runner compares configurations in the same code-exploration role. It measures answer correctness, evidence and completion time. The OAuth pilot completed 210 trials. Sonnet medium, Opus low and Opus medium reached 27/30 full approvals. Sonnet medium had the lowest median time. Read the [final analysis](results/pilot-oauth-matrix/analysis.md), which separates literal answer from full approval. The historical two-configuration smoke used Sol through CLIProxy and stays outside the OAuth pilot. The default selection keeps the seven configurations of that pilot; four additional configurations allow a second independent round.

The [second round](results/pilot-r2-xhigh-gemini/analysis.md) closed 120 attempts, with 103 completed answers and 17 fatal errors on Gemini. Sonnet xhigh had 24/30 approvals and Sol medium 17/30. Gemini medium had 23/30 and high 12/30. The errors coincide with the 25-step limit and require separating model behavior from an incompatibility at shutdown. The Gemini answers also identify `gemini-3.8-flash-n`, and the stream records have markings of unknown cause. The initial indication for Sonnet medium remains provisional; the rounds do not form a paired comparison.

| Configuration | OpenCode selection | Effort | Authentication and route |
|---|---|---|---|
| `sol-fast-low` | `openai/gpt-6.1-sol-fast#low` | low with native Fast | OpenCode OAuth, ChatGPT |
| `deepseek-max` | `opencode-go/deepseek-v4.1-flash#max` | max | OpenCode Go subscription |
| `sonnet-low` | `cli_proxy/cpa-claude-sonnet-5-5#low` | low | CLIProxy, Anthropic protocol |
| `sonnet-medium` | `cli_proxy/cpa-claude-sonnet-5-5#medium` | medium | CLIProxy, Anthropic protocol |
| `sonnet-high` | `cli_proxy/cpa-claude-sonnet-5-5#high` | high | CLIProxy, Anthropic protocol |
| `opus-low` | `cli_proxy/cpa-claude-opus-5-5#low` | low | CLIProxy, Anthropic protocol |
| `opus-medium` | `cli_proxy/cpa-claude-opus-5-5#medium` | medium | CLIProxy, Anthropic protocol |
| `sonnet-xhigh` | `cli_proxy/cpa-claude-sonnet-5-5#xhigh` | xhigh | CLIProxy, Anthropic protocol |
| `sol-fast-medium` | `openai/gpt-6.1-sol-fast#medium` | medium with native Fast | OpenCode OAuth, ChatGPT |
| `gemini-medium` | `cli_proxy_google/gemini-3.8-flash#medium` | medium | CLIProxy, Chat Completions protocol |
| `gemini-high` | `cli_proxy_google/gemini-3.8-flash#high` | high | CLIProxy, Chat Completions protocol |

Sol uses the builtin `openai` integration and the full OAuth credential from the local database. OpenCode expands Fast mode into `gpt-6.1-sol-fast`, with the `low` or `medium` variant selected for the round. The model sent remains `gpt-6.1-sol`, with `reasoning.effort` corresponding to the variant and `service_tier=priority`. The runner keeps the native WebSocket and the HTTP fallback.

Sonnet and Opus use `http://127.0.0.1:8317/v1/messages`. The effort comes from the native Anthropic variants, which send `thinking.type=adaptive` and `output_config.effort`. DeepSeek keeps the Go provider at `https://opencode.ai/zen/go/v1`, with `reasoning_effort=max`.

Gemini uses the local `cli_proxy_google` integration, with canonical `google` and the package `@opencode/ai/providers/openai-compatible`. The explicit medium and high variants use `settings.reasoningEffort`, sent as `reasoning_effort` to `http://127.0.0.1:8317/v1/chat/completions`. The runner imports a copy of the `cli_proxy` credential into this private integration. It does not require a separate Google credential. The observation verifies the effort sent to CLIProxy, without attesting its translation or the model executed upstream.

You need OpenCode **2.0.26**, Python 3.10 or later, the local catalog `~/.cache/opencode/models.json` and the local credentials `openai`, `cli_proxy` and `opencode-go`. The preflight checks the model and variant resolved by the executable. It does not substitute models or reduce effort on failure.

## Run

Run from `~/VSCode/Lab/evals`.

Check the graders, the schedule and the records without calling models:

```sh
python3 -B -m unittest discover -s exploracao/sol-fast-vs-deepseek -v
node --test exploracao/sol-fast-vs-deepseek/test_observer.mjs
```

Freeze the plan of 210 runs without inference:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py plan \
  --out exploracao/sol-fast-vs-deepseek/plans/oauth-matrix
```

Check configuration, private authentication, catalog and observer, without inference:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py preflight \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/validation/oauth-terminal
```

Run the seven-session smoke to check the real calls:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/smoke-oauth-matrix
```

Run the full pilot in another folder:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --out exploracao/sol-fast-vs-deepseek/results/pilot-oauth-matrix
```

That is six cases × five repetitions × seven configurations, a total of **210 planned sessions**. Each session has one user message and up to 25 agent steps. A step can make several tool calls. Additional calls from retries remain recorded.

Each case-and-repetition block contains all configurations. The seed `20261010` shuffles the blocks and a base order. Rotations of that order balance the positions: across 30 blocks, each configuration occupies each position four or five times. Sessions are sequential.

The default limit is 300 seconds per task and 21,600 seconds for the round, checked between runs. A task in progress can exceed the global budget up to its individual limit, plus preparation. Use `--timeout` and `--budget-seconds` before freezing to change these limits. The previous smoke does not allow estimating the duration of the five new agents.

The original OAuth credential is read without writing. The preflight requires its token to last for the full budget, the individual limit and a 900-second margin. This avoids rotating a refresh token in a disposable copy. If this control fails, renew the session in regular OpenCode or reduce the budget before starting another round.

The runner stops after failures of preparation, export, configuration, identity, observation or project change. Task or provider errors, incorrect answers and timeouts remain visible without interrupting the next cases. It does not automatically repeat inferences. Internal OpenCode recoveries count in the time and events.

To select a subset:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --candidates sol-fast-low,sonnet-medium,opus-low \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/subset-oauth
```

To regenerate a report without inference:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py report \
  --out exploracao/sol-fast-vs-deepseek/results/pilot-oauth-matrix
```

### Run the second round

Run the four-session smoke in a new folder:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --candidates sonnet-xhigh,sol-fast-medium,gemini-medium,gemini-high \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/smoke-r2-xhigh-gemini
```

Run the six cases with five repetitions, a total of **120 sessions**, in another folder:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --candidates sonnet-xhigh,sol-fast-medium,gemini-medium,gemini-high \
  --out exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini
```

This round keeps the prompts, project, graders, observation and limits of the previous pilot. Each configuration receives 30 sessions. Across 30 blocks, each configuration occupies each position seven or eight times. The report produces six paired comparisons among the four configurations. Results from different rounds remain separate, since they do not share the same execution block.

`plan`, `preflight` and `run` require a new folder. `run` creates its own freeze and repeats the preflight. The plan is for review and is not consumed by `run`. A new round does not delete earlier attempts.

`--binary`, `--database` and `--cache` select executable, database and catalog. `CLIPROXY_API_KEY` and `OPENCODE_GO_API_KEY` can supply the two keys. Sol requires native OAuth and does not accept replacing that authentication with a key. Credentials do not enter the public configuration.

## Cases and grading

The six cases use the same synthetic Python application with 23 files. Legacy code and similar functions serve as plausible alternatives. The question names the active dispatcher to delimit the task.

| Case | Required deliverable |
|---|---|
| `route` | Follow the order POST to the call to the database transport |
| `config` | Identify precedence and preserve an empty environment value |
| `retry` | Find the limit, exceptions and boundary of the repetition |
| `permission` | Resolve the filter by tenant, owner, publication and deletion |
| `feature` | Identify the renderer with a tenant flag disabled |
| `absence` | Demonstrate that a route exists only in the legacy code |

The agent returns JSON with the answer and citations of file, symbol, line and exact excerpt. Grading requires the correct literal answer, correct types, valid evidence and the necessary excerpts. Fabricated, incomplete or out-of-symbol citations fail. The execution proofs of the fixtures and the reference solutions are in `test_cases.py`, outside the project visible to the agent.

JSON format and exact citation are part of the contract. A format failure can fail a semantically correct answer. The result records `answer_correct` and `evidence_correct` separately to allow review of this effect. Grading does not judge open explanations or the usefulness of free text.

## Isolation and observation

Each task receives a private project, discovery home, XDG directories and session database. All configurations use the `navigator` agent, the same instructions and the same limits. Permissions allow only reading, searching and listing. Shell, editing, web, skills and subagents are denied.

Discovery of ancestor configurations is disabled. The audit allows the internal plugins and exactly one local observation plugin. It checks its origin, activation and readiness record. The agent has no access to that plugin's directory.

`observer.js` registers OpenCode's HTTP and WebSocket hooks. It keeps native URLs and authentication. It does not alter requests or frames. In HTTP, one pass over the stream collects metadata and delivers the same bytes, status and headers to the consumer. It does not wait for the whole stream before delivering it. All models use this observer.

The capture keeps only identity, session, agent, call type, URL without query, model sent, effort, Fast, usage, status and times. It does not record headers, prompts, tools or tokens in this capture. The exported sessions keep the project's messages and tools.

Fast keeps three states of evidence:

1. The native selection uses the Fast model and the requested effort variant.
2. Each observed call sends `service_tier=priority` and the requested effort.
3. The terminal `response.completed` responses report `service_tier=priority` or `fast` in all successful and complete calls.

The initial `response.created` state may report `auto`. The terminal class is the evidence used for service. Without a terminal class, Fast served remains **unknown**. A different or incomplete terminal class prevents confirmation. The runner keeps both states for audit. Effort sent does not prove how much internal reasoning the model performed.

The private copy of the credential is imported with `0600` permission. The file is removed after import and the private database is removed on finish. An abrupt external shutdown may prevent cleanup. Isolation of discovery and permissions is not equivalent to an operating-system sandbox.

## Interpreting the results

`freeze.json` records sources, protocol, catalog, configurations, cases, order and limits before inference. It includes the observer's hash. Each attempt keeps the prompt, events, session export, tools, answer, observed parameters, grading and the identity of all assistant messages.

The report reads the configurations from the freeze itself. The earlier smoke remains with two models. The OAuth round is independent and its times are not mixed with those of the old route. The verified historical sources are in `results/smoke/frozen-source`.

`report.md` and `summary.json` show hits, errors, incorrect answers and absences. Times include boot, tools and internal recoveries. They exclude preparation, audit, export and grading. The general table includes completed incorrect answers. There are 21 paired comparisons in the full matrix. Each requires both of its models to be correct on the same case and repetition.

Input, output, reasoning and cache are kept separate in each `result.json`. They do not represent comparable consumption of the subscriptions. The identity of the session and request also does not attest which model a proxy executed upstream.

The comparison measures complete configurations, including model, effort and route. It does not identify the isolated effect of Fast. Five repetitions measure operational variation, but six cases remain six distinct tasks. The synthetic suite does not establish the best explorer for all projects. The report keeps the verdict inconclusive until analysis of quality, variability and real metadata.

## References

- [OpenCode V2 agents](https://opencode.ai/v2/docs/agents).
- [OpenCode V2 models and variants](https://opencode.ai/v2/docs/models).
- [OpenAI Fast mode](https://developers.openai.com/api/docs/guides/fast-mode).
- [OpenCode Go](https://opencode.ai/docs/go/).
- [Expansion decision and local sources](validation/matrix-design.md).
