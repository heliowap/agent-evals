> English translation of [DESIGN.md](DESIGN.md). The original is kept verbatim as an archived artifact.

# Sol low Fast and GLM Flash on the corrected monetary contract

## Problem

The three new candidates need to run the same `money-contract-v2` contract. The earlier gates do not contain these configurations. Changing the historical sources would invalidate their provenance.

## Usage

```sh
python3 -B implementacao/opencode-implementador/rounds/money-sol-low-glm-flash/run.py run \
  --out implementacao/opencode-implementador/results/money-sol-low-glm-flash
```

One command runs three interruption proofs, three smokes and nine monetary trials, sequentially. Each phase writes to its own directory. The gates must pass before the next phase. The output must be new.

## Shape

The package contains `run.py`, the provenance and a copy of the frozen sources. `Candidate` remains the type that gathers identity, variant, effort, protocol and authentication. The fixed cohort contains Sol 6.1 low Fast via native OAuth and GLM 5.3 Flash high and max via OpenCode Go.

`harness/domain.py` changes only the cohort. `harness/tasks.py` selects only the corrected monetary case for screening. A contract constant in `harness/contract.py` takes part in the executor's freezing of the sources. The other core files keep the bytes of the original snapshot. The new `TaskSpec` must be fully equal to that of the corrected monetary round.

The runner verifies the origin and the hashes, freezes its own source and coordinates subprocesses of the existing CLI. `bench.py` keeps the preparation, audit, verification before each trial, OAuth control, execution, approval and reports. The runner consults the phase result even when the subprocess returns zero. The Docker image is selected by the SHA256 of the original screening, with no new build or resolution by mutable tag.

There are 20 seconds and two calls in the interruption proof; smoke and comparison keep 1200 seconds and 60 calls per session. The tolerance remains 15 seconds. There are no flags to change candidates, repetitions or limits.

## Synthesis decision

Alternative B, an independent package over the frozen CLI, is the basis. It avoids copying the execution loop and the session controls into another runner. The review scored B 9/10 and A 8/10 on the criteria recorded in `validation/money-extra-models-work.md`.

From alternative A, we incorporated the fixed cohort and tests of full equality of the task. The current cache is identical to the previous catalog, so the three phases can keep the frozen catalog. Composition by importing functions from the previous runner was rejected because it would require another phase loop and coordination of global modules.

Model the Domain guides the use of the already existing `Candidate` tuple. Laziness Protocol guides the reuse of the complete CLI, without another trial controller. Prove It Works guides validating the CLI and the real task before presenting the command.

## Risks and verification

A new copy of the sources receives new hashes, with the differences recorded. It will not be described as a fully identical core: the cohort and the inventory change, while runtime, controller, isolation and grader remain the same.

The tests must verify the 3/3/9 schedule, fully equal task, tampered contract and sources blocked, rejection of old gates, stopping after failed gates or an incomplete phase, and preservation of the historical artifacts. The real validation of baseline and reference continues without model calls.

The native discovery of the variants will be confirmed in the preflight of the OpenCode 2.0.26 binary. The static reading of the 2.0.22 checkout does not replace that confirmation. Fast sent as priority remains separate from the returned metadata.

The designs and the review used the inherited model of the GPT family available. The models from other families indicated in the skills were not available in this session.
