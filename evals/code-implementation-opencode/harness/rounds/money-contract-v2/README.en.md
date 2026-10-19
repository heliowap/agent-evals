> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Repeat only the corrected monetary case

Round concluded with 18/18 approvals and 105 model calls. The [results report](../../../../implementacao-opencode-resultado.md) compares the two versions of the contract and records the corrected analysis of the screening. The [raw summary](../../results/money-contract-v2/summary.json) keeps the series of this round.

This round repeats `py-money-contract` with the explicit contract of [request.txt](request.txt). The new case receives the identifier `py-money-contract-v2`. There are 18 trials, with six candidates and three repetitions per candidate.

The strings must match the ASCII grammar `[+-]?[0-9]+(?:\.[0-9]+)?` in full. The request requires rejecting `.1`, `1.`, spaces, exponents and underscores with `ValueError`. The request also states explicitly `ValueError` for `make_invoice` inputs that are not lists and requires exact calculation under low decimal precision.

The project README delivered to the agent contains this same request. The initial code files, the public tests, the private acceptance, the reference and the scope remain the same as in the original screening.

## Run the round

Use the Terminal with Docker available, as in the previous rounds:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py run \
  --out implementacao/opencode-implementador/results/money-contract-v2
```

The output directory must be new. The executor preserves earlier results. The Docker image already used in the screening is sufficient.

The output `results/money-contract-v2` already contains the concluded round. For a new repetition, choose another output directory.

The candidates are Sonnet medium, Sonnet high, Sol medium Fast, Sol high Fast, Opus medium and DeepSeek max. Identities, efforts, OAuth routes and providers come from the frozen round. Each trial keeps the limit of 20 minutes and 60 model calls. The round has a global cap of six hours and stops between complete blocks. Eighteen trials do not mean eighteen model calls.

The preflight checks the revised case, baseline, reference, isolation, tools and configuration of the six candidates before any inference. Infrastructure or scope failures end the round. The remaining trials stay visible as not executed.

## Check without using models

The plan freezes the schedule and does not call models:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py plan \
  --out implementacao/opencode-implementador/validation/money-contract-v2-plan
```

The validation runs only trusted baseline and reference code:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py validate \
  --out implementacao/opencode-implementador/validation/money-contract-v2-validate
```

## Evidence and interpretation

`harness/` is an exact copy of the 18 frozen sources of the screening. `provenance.json` records their hashes and the origin. The runner separately freezes its code and the revised request. A later change to those sources blocks the next run.

The `budget-r4` and `smoke` gates remain mandatory and keep the original criteria. Since the core is identical, there are no new budget or smoke sessions. The executor applies these gates to verified local copies and records their origin, without writing to the historical results. The design and the alternatives are in [DESIGN.md](DESIGN.md).

The results of the new round measure the explicit contract. Preserve the original series as evidence of the incomplete contract. Do not use the original failures over `.1` as proof of inability to follow instructions, nor consider those patches automatically correct on the other criteria.

The tier served remains separate from Fast requested. The screening round observed `default` on the Sol models, despite requesting Fast. This executor does not promise that the provider will honor the priority request.
