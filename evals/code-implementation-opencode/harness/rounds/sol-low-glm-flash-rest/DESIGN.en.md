> English translation of [DESIGN.md](DESIGN.md). The original is kept verbatim as an archived artifact.

# Complete the implementer screening

The user asked for the complete screening. The monetary round already started covers one of the 12 cases and must continue untouched. The continuation selects the other 11 original cases, with three repetitions of the same three candidates. That is 99 additional trials and 108 comparatives in the complete set.

```sh
python3 -B implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest/run.py run \
  --money-run implementacao/opencode-implementador/results/money-sol-low-glm-flash \
  --out implementacao/opencode-implementador/results/sol-low-glm-flash-rest
```

The command must start after the monetary round finishes. Functional failures are legitimate results and do not prevent the continuation; incomplete evidence or an infrastructure/scope violation prevents new calls.

## Chosen shape

The new runner imports the existing monetary harness without changing its 19 sources. The 11 `TaskSpec`s come from `tasks_python` and `tasks_typescript`, filtered by the screening phase and by the exclusion of `py-money-contract`. Each field must match the freeze of the original screening. The `Candidate` tuple stays the same as in the round already started.

The existing functions receive explicit tasks and candidates. The runner calls `freeze`, `preflight`, `require_gate`, `run_trial` and `report`; it does not replace core functions or inventories in memory. Its small loop keeps the global limit before each block, OAuth verification per block, verification before each trial, incremental report, stop on infrastructure/scope violation, and final report.

The gates already completed are copied to the new output. The verification that rewrites reports operates only on those copies. Origin, hashes, catalog, image, cohort and limits must match; no gate is repeated or loosened. The runner additionally seals its own sources, the TaskSpecs, the schedule and the hashes of the origin evidence, and checks that seal before each trial.

The output directory is new and sits outside the monetary origin. The continuation does not write sources, freezes, results or documentation of the run already started.

## Synthesis and verification

Explicit selection by argument received 10/10 in the design review. The alternative of swapping the inventory in memory received 8/10 and was rejected because it adds invisible state to the original guard, besides passing original proofs to a function that rewrites reports. We incorporated from it the adapter's additional seal and the checks before each trial.

Model the Domain keeps `TaskSpec` and `Candidate` as the canonical structures. Laziness Protocol keeps the core and its functions, with no other controller. Prove It Works requires a real plan of 99 sessions and baseline/reference validation of the 11 cases.

The tests must prove the exact schedule, exclusion of the monetary case, full equivalence of the tasks, gate compatibility, prior completion of the origin, preservation of the original proofs, limits and OAuth, stop after a violation, and rejection of changes to the sources/data. Plan and validate remain without inference.

The design review used the available GPT family. Real gates cover the executor and the configurations; the new selection and its seal require their own verification.
