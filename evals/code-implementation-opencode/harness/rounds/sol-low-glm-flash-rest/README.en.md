> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Complete the screening with Sol low Fast and GLM Flash

After the monetary command that has already started finishes, run in the `evals` folder:

```sh
python3 -B implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest/run.py run \
  --money-run implementacao/opencode-implementador/results/money-sol-low-glm-flash \
  --out implementacao/opencode-implementador/results/sol-low-glm-flash-rest
```

These are **99 additional trials**: the other 11 original screening cases, three configurations and three repetitions. The corrected monetary round provides the remaining nine trials, making **108 comparatives**. There will be no new calls for budget, smoke or monetary.

| Configuration | Route | Effort |
|---|---|---|
| Sol 6.1 low Fast | Native OpenCode OAuth | low, Fast requested |
| GLM 5.3 Flash high | OpenCode Go | high |
| GLM 5.3 Flash max | OpenCode Go | max |

The runner requires the nine monetary results to be complete and the budget/smoke gates to be approved. A functional failure in the monetary case does not block the other cases; incomplete execution or an infrastructure/scope violation blocks before creating the output and before calling models. The monetary results stay in their origin, without copying or renaming those trials.

The gates are copied to `gate-proofs/` inside the new output. The core revalidates these copies, without rewriting the origin. Catalog, immutable image, 19 harness files, candidates, prompts, tests and isolation remain the same. The 11 TaskSpecs are compared in full with the original screening. The only different selection is excluding the monetary case that has already been run.

The limits remain 1,200 seconds and 60 calls per trial, with 15 seconds of grace, and 21,600 global seconds for the continuation. The global limit is checked before each block, as in the original executor. OAuth is validated per block; sources, schedule, origin evidence and gate copies are checked before each trial. There is a stop after `infra_error` or `scope_violation`; remaining trials stay visible as `not_run`, and an incomplete continuation returns an error.

The preflight validates baseline/reference, Docker, namespace, image and provider configurations without inference. If it is blocked, the output states the reason and records zero calls. Do not reuse an existing output: choose another `--out` for a new attempt.

To inspect the schedule or validate the 11 cases without models or Docker, use `plan` or `validate` in place of `run`, with a new output. These two commands can run while the monetary origin is in progress. `preflight` and `run` require it to be complete. `report` updates only the continuation's reports.

Local verification:

```sh
python3 -B -m unittest discover -s implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest -p test_run.py
```

The execution tests replace only the model/environment access with temporary fixtures; plan and validation exercise the real core. They do not run model calls nor write to the monetary round.
