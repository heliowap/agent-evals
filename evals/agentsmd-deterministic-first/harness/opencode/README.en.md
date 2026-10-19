> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Deterministic first in OpenCode

Same experiment as [Codex CLI](../agentsmd-detfirst-isolated/README.md). The current executor uses **OpenCode 2.0.25 + `cli_proxy/cpa-claude-opus-5-5#medium`**, through the local CPA Proxy at `http://127.0.0.1:8317/v1`. It compares an empty `AGENTS.md` with the exact 992-byte snippet. It does not inherit the rest of your global file.

**Opus via CPA completed on 10/10/2026:** 72/72 runs, with 36/36 correct deliveries in each condition, including review of the controls. The snippet had a 5.8% longer observed average duration and 14.9% more reported output tokens. The overall duration difference is inconclusive; the largest increase was in `repeat`. The [Opus analysis](../../agentsmd-opencode-opus-5-5-medium-analise.md) records the audit of the 78 exports, the new grading of the 72 artifacts, the variation per case and the limitations of CPA token accounting.

**Sol pilot completed on 10/10/2026:** used `openai/gpt-6.1-sol#xhigh`, with 72/72 runs and 36/36 correct deliveries in each condition, including the reviewed controls. The snippet increased the average observed duration by 23.5% and the normalized total of tokens by 7.5%. The [final analysis](../../agentsmd-opencode-pilot-r2-analise.md) contains results per case and the exploratory comparison with Codex. The protocol and the original sources are preserved in `results/pilot-r2/frozen-source/` with the hashes checked against `freeze.json`. The script `results/pilot-r2/analyze.py` uses those frozen sources. These results do not measure Opus.

There are 12 cases × 2 conditions × 3 repetitions, for a total of **72 planned runs**. `cases.py`, the rubric and the two instruction files are exact copies of the Codex version. The executor verifies this equality before freezing a round. The order of the pairs, seed `20261010`, prompts and graders are the same. It does not change the Codex executor or results.

## Run in the terminal

Use Python 3.10 or higher, Git and OpenCode 2.0.25. The CPA Proxy must be active at `http://127.0.0.1:8317/v1`, with access to `claude-opus-5-5`. The executor uses the key from `CLIPROXY_API_KEY`, the same variable referenced by the local configuration of the `cli_proxy` provider.

```sh
cd ~/VSCode/Lab/evals/instrucoes-agents/agentsmd-detfirst-opencode
python3 -m unittest -v
python3 run.py preflight --out validation/opus-terminal-preflight
python3 run.py run --out results/opus-5-5-medium-r2
```

`preflight` opens a temporary local server per condition and keeps that server during the whole audit. It waits for the plugins to be activated through `integration.list` before querying configuration, skills and plugins. It does not request inference from the model. `run` repeats this check automatically before starting the tasks and per run. A failure interrupts the round, appears in the terminal and is recorded in JSON and in the report. It does not replace the model, does not reduce the effort and does not automatically repeat inferences that failed.

Output folders must be new. For another attempt, choose another `--out`. `--binary /path/opencode` lets you select the executable, but its version must remain 2.0.25. If `CLIPROXY_API_KEY` is absent, the executor reads the active `cli_proxy` credential from the local OpenCode v2 database, without modifying it. `--auth-file /path/file.json` lets you explicitly select an export from `opencode auth export` or a legacy `auth.json` containing `cli_proxy`. The requested identity is recorded in the configuration, in the command line and checked in the exported session, including in each assistant message.

For an initial test of two cases, before the 72 runs:

```sh
python3 run.py run --out results/smoke-opus-5-5-medium --cases count,repeat --reps 1
```

The default allows up to 600 seconds of agent invocation per run and 7.200 seconds of round budget. This budget can end the round before the 72 runs. Use `--budget-seconds 46800` if you want to reserve time for the 72 ten-minute limits and part of the preparation. The per-run limit covers all the prompts of that case. Preparation, audit and export have separate limits; the round budget is checked between pairs, so it is not a hard shutdown by the clock.

The commands below need neither OpenCode nor network:

```sh
python3 run.py plan --out plans/new-plan
python3 run.py report results/opus-5-5-medium
python3 run.py blind results/opus-5-5-medium
```

## What it measures

| Cases | Observed result |
|---|---|
| `count`, `money`, `convert` | Accuracy of counting, filtered sum and type conversion |
| `rename`, `project_tool`, `repeat` | Batch editing, contract of the existing tool and repetition across two prompts in the same session |
| `guardrail`, `regression` | Executable check that rejects recurrence and accepts valid inputs |
| `independent`, `dependent` | Real execution of independent commands and preservation of order when there is a dependency |
| `out_of_scope`, `judgment` | Respect for the review task and quality of an edit that requires judgment |

The report measures automatic passes, infrastructure failures and time. `out_of_scope` and `judgment` also require [blind review](REVIEW.md). Logs and artifacts allow separately verifying tool use, script reuse, parallelism, extra changes and warnings to the user. Counting tools does not measure quality.

The possible gains are fewer mechanical errors, safeguards that detect recurrences and less effort on repeated tasks. Possible costs include more tokens, preparation of automations without benefit and lost time on simple tasks. This synthetic pilot identifies signals and protocol failures; three repetitions per case do not support a general adoption decision.

The report uses complete pairs, difference of passes with equal weight per case and case-clustered bootstrap. It keeps missing runs visible. Time includes OpenCode boot and internal retries, but excludes audit, export and grading. The native input, output, reasoning and cache counters are kept separate. We do not infer total tokens or price; reported cost of zero does not mean free use. Each export contains the entire history and only the last one goes into the sum, so as not to duplicate the first prompt of the `repeat` case.

## Isolation and evidence

Each run gets a new Git project, XDG directories, discovery home and session database in a temporary folder. The subprocess discards inherited configurations, endpoints and keys. The private configuration pins the CPA route and the `medium` variant; the selected key enters only the private database. `OPENCODE_TEST_HOME` points the discovery of `.agents` and `.claude` to a private directory. `OPENCODE_CONFIG_PROJECT_DISABLE=1` turns off discovery of ancestor directories and their instructions. Only the private global `AGENTS.md` receives the experimental condition.

The `build` agent keeps OpenCode's internal instructions. The configuration turns off the `opencode.skill` plugin, which provides the internal skills `opencode` and `report`, using `plugins: ["-opencode.skill"]`. It loads no external plugins, additional skills or MCPs; it also turns off LSP, formatters, warming and updates. Permissions deny subagent, skill and web tools. The model catalog is not updated over the network. The configuration adds the alias `cli_proxy/cpa-claude-opus-5-5`, with canonical provider `anthropic`, adapter `@opencode/ai/providers/anthropic`, API model `claude-opus-5-5` and `medium` effort. The executor lets OpenCode approve its other tool requests with `--auto`, equally in both conditions. This does not create an operating-system sandbox; the isolation described is of state and of instruction discovery.

Only the selected `cli_proxy` credential is copied with `0600` permission and imported into the private database by `opencode auth import`. The key does not enter the public configuration, the manifest or the audits. After the run, the executor removes the authentication files and the private database that also contains credentials. It does not change the original database or file. An external shutdown with `kill -9` may prevent this cleanup. The temporary directory is in `runtime-path.txt`.

The `preflight` checks version, effective configuration documents, absence of skills and of plugins other than internal ones, including instruction discovery. It compares the two configurations after normalizing the temporary paths. **It does not verify equality of the full prompt sent to the model**, which is not exposed by this OpenCode flow. It explicitly records this limitation. The per-run check occurs after the authentication copy, to also detect additional configuration brought in by the account.

The skill and plugin inventories are queries of the current state and may be empty during initialization. For that reason the audit waits for activation on the same server that will answer the queries. It does not accept an empty list as evidence of isolation. `discovery-probe.json`, in the temporary directory of each audit, preserves IDs, origins and states of the plugins even when validation rejects the result.

Each round writes `freeze.json` before the inferences, with the public provider configuration and hashes of the sources, instructions and protocol. Each run preserves JSONL events, stderr, session exports, effective model identity, audit result, final answer, artifacts and grading in a separate copy. The answer key stays outside the task directory. `blind` exports artifacts without variant labels, but the answer itself may reveal the condition.

Compare first empty versus snippet **inside OpenCode**. Absolute differences between OpenCode and Codex also include tools, internal instructions, execution policies and token counting of each product. Do not attribute these differences to the `AGENTS.md` snippet.

## Validation of this delivery

For Opus via CPA, the 24 offline tests passed. They also verify the selection of provider, model and effort, the exclusive import of the CPA credential and the absence of keys in the public configuration. The plan in `plans/opus-5-5-medium/freeze.json` keeps the same 72 scheduled cases as the Sol round. The round `results/opus-5-5-medium` completed 72/72 in the user's terminal. Its 78 exports confirm the selection of provider, model and effort; all artifacts passed the new offline grading, and the 12 controls passed the assistant's review. This does not attest the identity of the model upstream of the proxy nor replace independent human review. The validation is recorded in `validation/opus-5-5-medium/verification.json`; the sources and the protocol used in the round are preserved in `results/opus-5-5-medium/frozen-source/`.

The tests verify the 12 graders with reference solutions and invalid results, suite parity, balancing of the pairs, discarding of inherited configuration, session identity and continuity without double counting. A simulated CLI tests the complete two-prompt flow and the removal of temporary credentials. This test does not run inference and does not replace validation with the real service.

### Sol validation history

The test of the complete flow also reproduces an initialization in which `plugin.list` returns empty before activation. It requires the executor to wait for this activation and query the same server, besides turning off the catalog of the two internal skills. Another test verifies that preflight failures appear in the terminal. The first attempt in the terminal, preserved in `results/pilot`, ended before any task with the message `Expected only the built-in OpenCode plugins`. After fixing the initialization sequence, `validation/terminal-r2` confirmed the loading of the plugins and revealed the two internal skills, now disabled in the eval environment.

The real test in the terminal completed **4 of 4 runs**, all passed, on the `count` and `repeat` cases, one repetition per condition. The [short test report](../../agentsmd-opencode-smoke-r3-automatico.md) and its exports confirm `openai/gpt-6.1-sol#xhigh`, empty skill catalog in both conditions and continuity of the same session across the two prompts of `repeat`. The counters match the last cumulative export. The temporary copies of credentials and of the databases of each run were removed. This validates the executor's operation; the sample does not demonstrate a gain from the instruction.

The local server is still prevented from starting in this assistant's sandbox, per `validation/activation-fix-local/preflight.json`. The complete round `results/pilot-r2` was run in the user's terminal and completed 72/72. The final audit checked the 78 exports, the model and effort, the cumulative count, the configuration discovery and the artifacts. The 21 offline tests passed after the executor fixes. The final analysis was offline and did not call the model again.

Details of the integration were checked in the documentation for [models](https://opencode.ai/v2/docs/models), [instructions](https://opencode.ai/v2/docs/instructions), [configuration](https://opencode.ai/v2/docs/config) and [API](https://opencode.ai/v2/docs/api), besides OpenCode's local source code. The version is pinned because these interfaces may change.
