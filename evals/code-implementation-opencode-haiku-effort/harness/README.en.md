> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Haiku 5.5 in the complete implementation eval

This round compares Haiku 5.5 at the `low`, `medium`, `high`, `xhigh` and `max` efforts, using OpenCode 2.0.26 and the route `cli_proxy/cpa-claude-haiku-5-5`. The model sent to CLIProxy is `claude-haiku-5-5`. The alias and the variants are declared in the private configuration; the run does not import the user's global configuration.

Run from the `evals` folder:

```sh
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py run \
  --out implementacao/opencode-implementador/results/haiku-5-5
```

The command runs five budget-interruption proofs, five smokes and 180 comparative trials: 12 cases, three repetitions and five efforts. That is 190 sequential sessions. The two gates are new to this cohort and must pass before screening. In the budget proof, `budget_exceeded` with `proof_passed=True` is expected; `accepted` remains false.

The screening keeps eleven TaskSpecs from the original round in full and replaces only the monetary Python one with the corrected `money-contract-v2` TaskSpec. The monetary TypeScript case is also part of the 12 cases. Initial files, reference, private tests and approval rules are the same as in those sources. The ambiguities already recorded in the profile contract and in the import envelope remain; this round adds no requirements to those statements.

The budget proof allows 20 seconds and two calls. Smoke and screening allow 1.200 seconds and 60 calls per session, with 15 seconds of controller tolerance. Each phase keeps the global six-hour limit and the original seed. The configurations are alternated in blocks of case and repetition. The frozen catalog and the Docker image by SHA are the same as in the original round; a missing image blocks the preflight.

The frozen catalog does not yet include Haiku 5.5. For that reason `runtime.configuration()` explicitly registers the five Anthropic variants, keeping the experiment's limits: 272.000 context tokens and 32.768 output tokens. No other part of the runtime changes. The native audit must find the alias, the model sent and the selected effort. The observed calls must preserve model, effort, route, session and `thinking_type=adaptive`. This identity does not attest the backend upstream of CLIProxy.

The core differs from the baseline only in the cohort of `domain.py`, in the selection of `tasks.py`, in the registration of the variants in `runtime.py` and in the new `contract.py`. The other files keep the frozen bytes. The wrapper verifies that each change corresponds exactly to these boundaries before importing the core. The core verifies the hashes of the 19 harness files before each trial. Wrapper, README, tests, provenance, schedule and external budget are verified before and after each phase; the trial loop remains the original.

`plan` freezes the 5/5/180 schedules without calling models. `validate` also runs the projects and references of the 12 cases without calling models. `preflight` verifies Docker, isolation and native discovery without inference. All use the same CLI and require a new output. `--phase budget` limits the sequence to the first gate; `--phase smoke` includes both; `--phase screening` is equivalent to the default `all`.

Each phase writes to `budget/`, `smoke/` or `screening/`. `round-freeze.json` records the sources, commands and schedules. `round-summary.json` gathers the state of the phases and the call count. To update only the reports of an existing output, use `report --out PATH`. The labels of the derived reports are adjusted for five configurations, without changing the frozen generator.

Failures of gates, infrastructure, scope, changes to sources or incomplete phases interrupt the sequence and keep the remaining attempts visible. A functional failure in screening does not prevent the other trials. The result measures execution and acceptance in these small projects; it does not demonstrate a general absence of bugs or security gaps. No candidate is promoted automatically.
