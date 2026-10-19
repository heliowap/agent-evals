> English translation of [DESIGN.md](DESIGN.md). The original is kept verbatim as an archived artifact.

# Haiku 5.5 at all effort levels

Run from the `evals` folder after validating the package:

```sh
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py run \
  --out implementacao/opencode-implementador/results/haiku-5-5
```

The command performs new budget and smoke gates before the complete screening. There are five configurations, `low`, `medium`, `high`, `xhigh` and `max`, on the route `cli_proxy/cpa-claude-haiku-5-5`, with sent model `claude-haiku-5-5`. Each effort receives the 12 cases and three repetitions. The total is 180 comparative trials and ten gate sessions, 190 sessions.

## Sources and controls

The package derives from the 18 files frozen in the original screening. It copies the already verified phase wrapper, without creating another execution loop. Only the candidates in `domain.py`, the task selection in `tasks.py` and the private declaration of variants in `runtime.configuration()` change. `contract.py` keeps the explicit monetary contract of the concluded round. Eleven TaskSpecs are fully identical to the original screening; the monetary Python one is fully identical to the corrected TaskSpec.

Controller, grader, observer, terminal, isolation, dependencies, image by SHA, catalog, seed and other sources stay equivalent to the baseline. Each trial keeps 1,200 seconds, 60 calls and 15 seconds of grace. The global limit stays at six hours per phase. The copy gets its own hashes and gates; it does not reuse proofs from other configurations.

The frozen catalog does not yet contain Haiku 5.5. The user's global configuration already declares the alias and five variants, and the local CLIProxy registry contains the model with the same five efforts. The new private configuration declares those variants explicitly, without importing global configurations, plugins, MCPs or skills. It keeps the experiment limits of 272,000 context tokens and 32,768 output tokens.

The native audit checks provider, alias, sent model and selected effort. The existing call verifier already requires model, effort, route, session and `thinking_type == adaptive`. Those functions stay intact. Gates with any unavailable variant or without proof of interruption/approval block the screening.

## Designs compared

Design A copies the frozen CLI and adapts the cohort and selection data. Design B passes candidates and TaskSpecs directly to the core functions, adding an explicit loop. A received 10/10 and B received 8/10 on the criteria of task preservation, controls, native proof, provenance and simplicity. A keeps a single, already verified loop. We incorporated from B the requirement to freeze the wrapper and provenance externally and to correct the labels of the derived reports to five configurations.

Sketches: `/private/tmp/haiku55-design-a.md` and `/private/tmp/haiku55-design-b.md`. The cross-judge was GPT-5.6 Sol, from the same family available in this session.

## Verification

Real plan with schedules 5/5/180, validation of the 12 projects and references, declaration of the five variants, equality of the TaskSpecs, hashes of the sources and budget, interruption after failed gates, schedules and final reports on failures. The `runtime.py` code outside `configuration()` must remain equivalent to the baseline, and the change inside it must be only the registration of the variants. The origin remains read-only.

The caveats already identified in the profile contracts and import envelope remain documented. We did not change those statements in this round. The functional result keeps the nominal acceptance and distinguishes operational failure, timeout and patch rejection. We do not infer a general absence of bugs or security gaps from this small set.
