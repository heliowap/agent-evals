> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Sol low Fast and GLM Flash on the monetary case

This round uses the corrected contract of `money-contract-v2`, with the same initial files, reference, private tests and approval rules. The cohort contains Sol 6.1 low Fast via OpenCode's native OAuth and GLM 5.3 Flash high and max via OpenCode Go.

```sh
python3 -B implementacao/opencode-implementador/rounds/money-sol-low-glm-flash/run.py run \
  --out implementacao/opencode-implementador/results/money-sol-low-glm-flash
```

There are 15 sequential sessions. Three prove the budget interruption, three run the smoke and nine compare the monetary case, with three repetitions per configuration. The gates are new and must pass before the next phase. In the budget gate, `budget_exceeded` with `proof_passed=True` is the expected result.

The budget proof allows 20 seconds and two calls. Smoke and the monetary case allow 1200 seconds and 60 calls per session. The controller keeps the 15-second tolerance. The frozen catalog, the immutable identifier of the existing image and OpenCode 2.0.26 are the same as in the previous round. A removed image blocks the preflight. The configuration, state and personal tools remain isolated by the original executor.

`plan`, `validate` and `preflight` use the same CLI. `plan` and `validate` make no model calls. `preflight` verifies Docker, isolation and native discovery without inference. `--phase budget` limits the sequence to the budget gate; `--phase smoke` includes both gates; `--phase screening` is equivalent to `all`. The output must be new, including when repeating an interrupted round.

Each phase writes to `budget/`, `smoke/` or `screening/`. `round-freeze.json` records the 15 sessions, the sources, the origin of the contract and the commands. `round-summary.json` gathers the state of the phases. To update the report of an existing output, use `report --out PATH`.

The runner adjusts the count of configurations in the derived Markdown reports to the cohort of three candidates, without changing the frozen source of the generator.

The core changed only in `domain.py` for the cohort, in `tasks.py` to select the corrected contract and in the new `contract.py`. The other files keep the bytes of the original snapshot. The executor also freezes and verifies `contract.py` before each trial. The runner verifies its snapshot before and after each phase and interrupts the sequence if there is a failed gate, invalid infrastructure or scope, or an incomplete phase even with a zero return from the subprocess.

Fast requested as `priority` and the returned `service_tier` are separate metadata. A `default` return on OAuth does not demonstrate absence of acceleration. This comparison measures the whole task, including commands and checks made by the agents. Three repetitions of one case do not determine a general choice of implementer.
