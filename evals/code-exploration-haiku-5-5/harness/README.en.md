> English translation of [README.md](README.md). The original is kept verbatim as an archived artifact.

# Haiku 5.5: reading, code search and exploration

Run from the root of `evals`:

```sh
python3 -B exploracao/haiku-5-5/bench.py run \
  --cache exploracao/haiku-5-5/models.json \
  --budget-seconds 86400 \
  --out exploracao/haiku-5-5/results/full-1
```

This command directly runs the complete pilot, with a private preflight at the five efforts and 150 trials: six cases × five repetitions × Haiku low, medium, high, xhigh and max. Each effort receives 30 comparative trials. The `bench.py` defaults already select all these cases and efforts. No resumption, overwriting, inference retry or automatic effort swap.

The previous smoke in `results/round-1` finished five sessions and verified model, effort, adaptive thinking and cap across the 27 calls. There were three full approvals; medium failed on the type of `chain` and high on an extra citation. For that reason the historical wrapper did not start the pilot. These quality failures are results to measure, not criteria to prevent the full collection. The command above does not reuse nor alter the old gate, does not repeat the smokes and keeps the same strict grader.

```sh
python3 -B exploracao/haiku-5-5/bench.py plan --cache exploracao/haiku-5-5/models.json --budget-seconds 86400 --out exploracao/haiku-5-5/results/full-plan-1
python3 -B exploracao/haiku-5-5/haiku.py validate-offline --out exploracao/haiku-5-5/results/full-check-1
python3 -B exploracao/haiku-5-5/bench.py report --out exploracao/haiku-5-5/results/full-1
```

`--binary`, `--database` and `--cache` allow choosing the native resources. By default it uses `opencode`, the usual SQLite in read-only mode and the frozen catalog included in the package. Credentials never appear in the report; private import uses an ephemeral 0600 file. `report` rebuilds local reports without inference.

## Protocol

OpenCode 2.0.26; model `cli_proxy/cpa-claude-haiku-5-5#<effort>`; wire `claude-haiku-5-5`; Messages at `http://127.0.0.1:8317/v1/messages`; thinking adaptive; Fast disabled. All observed requests must preserve identity, effort and `max_tokens` integer 128000. This proof shows parameters sent; it does not attest which model the provider executed internally.

Controls equal across efforts: 300 seconds per task process, 25 steps, context 272000, output 128000, seed 20261010, five repetitions. The output cap was deliberately changed from 32768 to 128000: this is a new experimental configuration. The [published limit of Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) allows 128K of output.

The complete pilot uses an admission budget of 86400 seconds. This 24-hour ceiling avoids the six-hour cutoff of the previous wrapper; it is not a duration forecast. The tasks alone may consume up to 150 × 300 = 45000 seconds if all reach the timeout, in addition to preparation and export. Before starting each trial, the core checks the elapsed time. Preparation, audit and export have their own limits; the global budget is not a hard deadline of the complete process. A pilot may end incomplete; missing trials remain visible and the exit is non-zero. Infrastructure errors or fixture alteration interrupt the phase; output limit, timeout, task error and incorrect delivered response continue the collection.

The schedule interleaves efforts per case and repetition, with balanced rotations: each effort occupies each position six times in the pilot. The measured region is the `opencode run` process, including boot, tools and native recoveries. It excludes fixture construction, credential import, audit, export and grader. Paired comparisons require full approval of both in the same case/repetition. Terminal output limits stay outside incorrect responses and approved pairs.

Allowed tools: read, glob, grep and list. Shell, web, editing, skills, MCP, LSP, formatters and native delegation disabled. Discovery uses private HOME/XDG and configuration. This is not equivalent to an operating-system sandbox. Native plugins remain active, along with the verified local observer; the user's skills and external plugins are not imported.

## Corpus, capture and integrity

The six cases investigate active route, configuration precedence, retry, permission, feature flag and absence of a route. The 23 files, prompts, responses and grader come from the frozen R2 base at `../sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. `cases.py`, `test_cases.py` and `observer.js` are byte-equivalent; `provenance.json` records origin and hashes. `bench.py` keeps a single scheduler and loop; `runtime.py` adapts the cohort, cap, capture and diagnosis; `haiku.py` adds the gate and envelopes. `test_haiku.py` contains new proofs, without models. The catalog comes from the historical copy `implementacao/opencode-implementador/results/screening/models.json`.

Native export uses stdout in a regular 0600 file, preserving sanitized bytes before decoding/parsing. `export.json` records exit, timeout, sizes, raw/sanitized hashes and offset of invalid JSON/UTF-8. The capture does not reserialize, correct or repeat exports. Synthetic capture proofs do not show the cause of a failure in the native binary.

`finish` and `rawFinish` of all assistants are preserved. `length`/`max_tokens` on the last assistant identifies a terminal limit; an intermediate limit followed by a valid delivery records recovery. Export or identity failures remain infrastructure; limits are not inferred from the number of tokens.

The direct runner freezes the package sources and the catalog. It verifies sources/protocol/catalog before the trials and after the phase, including the last trial. Each session has a private audit, verified identity and request parameters, and a fixture checked after execution. The plan and validations do no inference; preflight only proves discovery. Earlier results stay intact at their existing destinations.

The `haiku.py run` wrapper remains available for the previous protocol, with five new smokes, a gate of 5/5 full approvals, 150 trials conditioned on the gate and additional envelopes of integrity for the executable and the historical inventory. The direct pilot does not produce these campaign envelopes. Its results, freezing, report and status stay directly in `results/full-1`, without `smoke` and `pilot` subfolders. The `bench.py report` command rebuilds this report; do not use `haiku.py report` for the direct pilot. The historical snapshots in `results/round-1` continue to describe the old protocol.

The suite has six synthetic tasks; five repetitions measure operational variation, not 30 new problems. It allows comparing these configurations on this corpus, without certifying general reliability or declaring a winner automatically. A reported cost of zero does not mean free use; remote cache may persist. Design reviews used only models of the GPT family.
