> English translation of [DESIGN.md](DESIGN.md). The original is kept verbatim as an archived artifact.

# Repeat the monetary contract with explicit instructions

The original case left two rules incomplete. The private test rejects strings such as `.1` and `1.`, but the request does not define the grammar. The API also requires `ValueError` for inputs that are not lists. The revision makes these requirements explicit, along with independence from the caller's decimal precision.

## Comparison of the designs

| Design | Change | Sessions with models |
|---|---|---:|
| Specific runner and frozen core | External revision of the contract and selection of one case through the existing functions | 18 |
| Alter the original CLI and inventory | Add a case filter and change the sources covered by the gates | 30, including six budget proofs and six smoke sessions |

The specific runner uses an exact copy of the 18 frozen sources of the screening. `TaskSpec` remains the structure that gathers request, initial files, reference, acceptance and scope. The revision changes the identifier, the request and the copy of the request in the project README. Initial code, public tests, private acceptance, reference and scope remain the same.

The caller uses `python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py run --out implementacao/opencode-implementador/results/money-contract-v2`. The round contains six candidates and three repetitions of the single case `py-money-contract-v2`.

## Boundaries between modules

`run.py` verifies provenance, builds the revised `TaskSpec` and freezes its own source and the contract. The existing functions of `harness/bench.py` do scheduling, preflight, comparison of the gates, execution and report. `harness/controller.py` remains responsible for interruption. `harness/grader.py` remains responsible for functional approval.

The runner uses the following operations:

1. Verify the copy of the core against the hashes of the original `freeze.json`.
2. Build the revised case and check the preserved fields.
3. Freeze the schedule of 18 trials, the contract and the runner source.
4. Run preflight without inference and apply the existing gates without changing their criteria.
5. Check both freezes before each trial and run complete blocks.
6. Produce a separate result, without combining the two versions of the contract.

`require_gate` rewrites derived reports when reading a proof. Therefore, the runner passes copies of the gates to this function and records the original hashes and paths. The historical results receive no writes.

The existing gates prove the identical core. They do not prove the revised contract. The local validation and the preflight of the new round verify baseline, reference and case selection before any model call.

## Verification

The plan must contain only the revised case, the same six candidates and three repetitions, totaling 18 trials. Later changes to the contract or the runner must block execution before the next model call. Baseline and reference must keep the same compilation, regression and acceptance results as the previous version. Infrastructure or scope failures end the round and keep the remaining trials as not executed.
