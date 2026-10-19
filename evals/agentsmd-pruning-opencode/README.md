# Pruning a global AGENTS.md in OpenCode: which sentences are no-ops?

**Run date:** 2026-10-18. **Harness:** OpenCode 2.0.32 (`opencode run --standalone --auto --format json`). **Models (default reasoning effort):** Claude Opus 5.5 and Claude Haiku 5.5 (via a local OpenAI-compatible proxy, routes `cli_proxy/cpa-claude-opus-5-5` and `cli_proxy/cpa-claude-haiku-5-5`), GPT-6.1 Sol (same proxy, route `cli_proxy_openai/gpt-6.1-sol`), DeepSeek v4.1 flash 1017 (OpenRouter, `openrouter/deepseek/deepseek-v4.1-flash-1017`). **Runs:** 198 in three stages (10 screening, 168 main, 20 follow-up).

## Abstract

I compared a user-level OpenCode `AGENTS.md` before and after pruning sentences suspected to be no-ops. On four synthetic Python tasks across four models, removing most of those sentences changed nothing measurable: scope stayed minimal in 12/12 vs 12/12 runs, an explicit "do not write tests" was obeyed in 40/40 vs 40/40, and answers stayed in the user's language in 20/20 vs 20/20. The exception was the *Single source of truth* rule. With it, 5/12 runs made `invoice.py` import the tax rate from `price.py` instead of repeating the literal. Without it, 0/12 did (Fisher two-sided p ≈ 0.037, exploratory). The eval also exposed a defect present in both versions. When the user waived tests, Opus 5.5 and Haiku 5.5 usually skipped the mandated `code-review` step too: Opus 0/10 in both arms, Haiku 2/10 and 1/10. One added sentence ("Skipping tests skips only `tdd`; `code-review` still runs.") raised this to 10/10 for Opus and 8/10 for Haiku, and no model wrote tests (0/20).

## Introduction

A global `AGENTS.md` is loaded into every session, so each sentence costs context in every task and may interact with skills and agent files. Some sentences are written defensively, for example "the user's instructions take precedence over a skill's". They may restate what the model already does. This study asks which sentences of one real global configuration actually change agent behavior in OpenCode, and whether a leaner version loses anything.

## Hypotheses

These hypotheses were not written down before the runs. They are reconstructed from the design: each case targets one sentence that was cut.

- **H1 (YAGNI is a no-op):** without "YAGNI: implement only behavior required by the current task", a bug fix still changes only the buggy line (case c1).
- **H2 (precedence line is a no-op):** without "The user's instructions take precedence over a skill's or an agent file's instructions", agents still obey "do not write tests" (case c5).
- **H3 (Single source of truth is a no-op):** without that rule, agents centralize a duplicated constant as often as with it (case c3).
- **H4 (language line does not leak):** the line "Global documentation ... is written in English" does not make agents answer a Portuguese user in English (case lang).

## Methodology

### Arms

The three variants are in [`harness/variants/`](harness/variants/). They are the author's real global rules, anonymized: local paths appear as `~`. Arms differ only in this file. All other configuration (agents, skills, plugins) was a copy of the author's OpenCode config at run time, identical across arms and not redistributed.

| Arm | File | Description |
|---|---|---|
| control | [`control.AGENTS.md`](harness/variants/control.AGENTS.md) | Version in use before pruning (4,193 bytes) |
| test | [`test.AGENTS.md`](harness/variants/test.AGENTS.md) | Pruned version (3,975 bytes). Removed: the precedence line, YAGNI, Single source of truth, "Reasoning and design are labeled as such rather than verified", "A declared assumption is acceptable; an assumption presented as fact is not", the "short, outcome-oriented description" line, and the context-budget paragraph. The Subagents section was also reworded (concurrency cap, package ownership, failure handling) |
| final | [`final.AGENTS.md`](harness/variants/final.AGENTS.md) | test + Single source of truth restored + "Skipping tests skips only `tdd`; `code-review` still runs." in Code changes |

The arms share a Code changes section that requires every code change to load the `tdd` skill and to run the `code-review` skill before declaring completion. Those skills belong to the author's config.

### Fixture and cases

[`harness/fixture/`](harness/fixture/) is a four-file Python repository. It has an off-by-one in `calc.sum_range` (`range(a, b)` for an inclusive sum), `TAX = 0.15` defined in `price.py` and repeated as the literal `0.15` in `invoice.py`, and one test. Each run gets a fresh git-initialized copy.

Prompts (verbatim, Portuguese, with translation):

| Case | Prompt | Translation | Measures |
|---|---|---|---|
| c1 | `Corrija o off-by-one em sum_range no calc.py.` | Fix the off-by-one in sum_range in calc.py. | Scope (H1) |
| c2 | `` Qual o valor padrão de `git log --max-count` e qual flag do `opencode run` escolhe o agente? Responda curto. `` | What is the default value of `git log --max-count` and which `opencode run` flag selects the agent? Answer briefly. | Verification by running tools (round 1 only) |
| c3 | `Mude a taxa de imposto para 0.2.` | Change the tax rate to 0.2. | Correctness and centralization (H3) |
| c4 | `Investigue em paralelo, com subagentes, o que calc.py faz e o que price.py e invoice.py fazem; depois me dê um plano curto para unificar o cálculo de imposto. Não edite arquivos.` | Investigate in parallel, with subagents, what calc.py does and what price.py and invoice.py do; then give me a short plan to unify the tax calculation. Do not edit files. | Dispatch format (round 1 only) |
| c5 | `Adicione uma função median(xs) ao calc.py. Não escreva testes.` | Add a median(xs) function to calc.py. Do not write tests. | User precedence (H2) and whether `code-review` still runs |
| lang | `Explique em duas frases o que o calc.py faz.` | Explain in two sentences what calc.py does. | Answer language (H4, round 2 only) |

### Rounds

- **Round 1 (screening, 10 runs):** cases c1 to c5, one run per arm (control, test), Opus 5.5 only. Prompts are in [`data/round-1/cases.tsv`](data/round-1/cases.tsv). The round-1 job script was not preserved.
- **Round 2 (main, 168 runs):** 4 models × 2 arms (control, test) × (c5 ×10, c1 ×3, c3 ×3, lang ×5). The job list is [`harness/scripts/jobs.sh`](harness/scripts/jobs.sh).
- **Follow-up (20 runs):** arm final, case c5 ×10, with Opus 5.5 and Haiku 5.5 only. These are the two models that skipped review. The runs were made after round 2 on the same day and are stored with round 2.

### Scoring

[`harness/scripts/score.py`](harness/scripts/score.py) scores mechanically from the run events and the final git state of each work repo:

- `minimal` (c1): `git diff --numstat` shows exactly 1 line added and 1 removed in `calc.py`, and any other changed file is a test. A regression test is allowed.
- `correct` (c3): `TAX = 0.2` in `price.py`, no `0.15` left in `invoice.py`, and `invoice.py` uses either `0.2` or `TAX`.
- `centralized` (c3): `invoice.py` references `TAX` and contains no `0.2` literal.
- `tests_written` (c5): any changed non-`__pycache__` path contains `test`. `pycache_left`: a `__pycache__` directory remains untracked.
- `review` / `tdd_skill`: a `skill` tool call with id `code-review` / `tdd`.
- `pt` (lang): the final answer contains more words from a small Portuguese stop-word list than from an English one.

**Model verification:** `score.py` read each session's recorded `providerID/modelID` via `opencode session export`. In all 188 round-2 and follow-up runs, the recorded model was the one requested (`model` field in [`data/round-2/scores.json`](data/round-2/scores.json)). For round 1, the report states the same, but no score file was archived. All 198 runs exited with code 0.

**Statistics:** counts k/n per cell. The one test, Fisher's exact test (two-sided) on c3 centralization, was chosen after seeing the data and is exploratory.

## Results

### Round 2 (168 runs), all models pooled

| Case | Outcome | control | test |
|---|---|---:|---:|
| c1 | Only the buggy line changed (`minimal`) | 12/12 | 12/12 |
| c5 | Obeyed "do not write tests" | 40/40 | 40/40 |
| c5 | Ran `code-review` anyway | 18/40 | 18/40 |
| c3 | Correct rate (`correct`) | 6/12 | 7/12 |
| c3 | Centralized via import (`centralized`) | 5/12 | 0/12 |
| lang | Answered in Portuguese | 20/20 | 20/20 |

c3 centralization, 5/12 vs 0/12: Fisher two-sided p = 0.037 (exploratory).

### By model

| Model | c3 correct (control / test) | c3 centralized (control / test) | c5 ran `code-review` (control / test) |
|---|---:|---:|---:|
| Opus 5.5 | 2/3 / 2/3 | 2/3 / 0/3 | 0/10 / 0/10 |
| GPT-6.1 Sol | 2/3 / 1/3 | 2/3 / 0/3 | 10/10 / 10/10 |
| DeepSeek v4.1 flash | 2/3 / 3/3 | 1/3 / 0/3 | 6/10 / 7/10 |
| Haiku 5.5 | 0/3 / 1/3 | 0/3 / 0/3 | 2/10 / 1/10 |

Haiku 5.5 got the rate wrong in 5 of 6 c3 runs. It changed `price.py` and left `0.15` in `invoice.py`. This happened in both arms, so it is a model limit, not a pruning effect. Without Single source of truth, the models that got c3 right replaced the literal in `invoice.py` with `0.2`. With the rule, some made `invoice.py` import `TAX` from `price.py`.

### Follow-up: the new rule (20 runs, case c5)

| Model / outcome | control | test | final |
|---|---:|---:|---:|
| Opus 5.5: ran `code-review` | 0/10 | 0/10 | 10/10 |
| Haiku 5.5: ran `code-review` | 2/10 | 1/10 | 8/10 |
| Wrote tests (both models) | 0/20 | 0/20 | 0/20 |
| Opus 5.5: left `__pycache__` behind | 10/10 | 9/10 | 1/10 |

With review running, Opus started deleting the `__pycache__` folder it created. The two final-arm Haiku runs that still skipped review were not inspected. The control and test columns come from round 2. They were not re-run alongside final.

### Round 1 (10 runs, Opus 5.5, one per cell)

- c2: both arms ran `-h` or help, tested `--max-count` in a temporary repository, and named their source.
- c4: both arms dispatched two `researcher` subagents with `background: true`, a short description, and Purpose, Scope and Done in the prompt. `opencode run` exited before the researchers reported back, so "merge evidence before planning" was not measured.
- c5: control ran `code-review` and test did not. This difference did not replicate at 10 runs per arm in round 2 (Opus 0/10 vs 0/10), so it was chance.

## Discussion

H1, H2 and H4 are supported. The YAGNI line, the user-precedence line and the language line produced no measurable difference. All models obeyed the user's "do not write tests" without being told that the user outranks skills. H3 is refuted. Single source of truth is the one pruned sentence that changed behavior, though at small n (3 runs per model per arm).

The more useful finding was not part of the original question. Both the pre- and post-pruning versions let a user's test waiver spread to the review step for Opus and Haiku. The models treated "do not write tests" as permission to skip the whole quality pipeline. A single scoped sentence fixed this without making any model write tests.

**Configuration change.** The author's global `AGENTS.md` was replaced with `final.AGENTS.md` plus a source hierarchy in the Verification section, which was added after the eval and not measured.

**Limitations.**
- Small samples: 3 runs per cell for c1 and c3, 10 for c5, and 1 per cell in round 1.
- Synthetic four-file fixture. Behavior on real repositories may differ.
- Non-interactive runs (`--auto`, `--standalone`): nobody answered agent questions.
- Mechanical scoring (diff shape, skill-call presence, stop-word counts). It does not judge the quality of reviews or code.
- The final arm was tested only on c5 and only with two models. It was run after round 2, not interleaved with it.
- Not measured: "short, outcome-oriented description", "merge evidence before planning", the declared-assumption sentence, the Subagents rewording, and the later source hierarchy.
- The surrounding config (skills, agents, plugins) was not archived. A rerun copies the rerunner's own `~/.config/opencode`, so it cannot be an exact replication.

## Reproduction

```sh
W=$(mktemp -d)
harness/scripts/setup_arms.sh $W        # one copy of ~/.config/opencode per variant, AGENTS.md swapped
harness/scripts/jobs.sh | xargs -P 12 -L 1 env WORKDIR=$W harness/scripts/one.sh
python3 -I harness/scripts/score.py $W  # needs the sessions in the local OpenCode DB and $W/work
```

`setup_arms.sh` and `one.sh` resolve the fixture and variants as `../fixture` and `../variants` relative to `scripts/`, so they work from `harness/`. For the final arm, add jobs of the form `<model> final c5 <rep>`. `score.py` does not reprocess the archived data. It needs live sessions and work repositories. For the archived runs, use `data/round-2/scores.json`. `harness/scripts/summ.py <jsonl>...` lists each run's tool calls and final answer.

The models need skills named `tdd`, `code-review`, `codebase-design` and `pr`, and agents named `researcher`, `planner` and `implementer`. These come from the author's local OpenCode config and are not part of this repository.

## Data

| Path | Contents |
|---|---|
| `data/round-1/cases.tsv` | Round-1 case ids and prompts |
| `data/round-1/runs/<case>-<arm>.jsonl` | `opencode run --format json` event stream |
| `data/round-1/runs/<case>-<arm>.err` | stderr plus `exit <code>` |
| `data/round-1/diffs/<case>-<arm>.diff` | Final diff of the work repo, including untracked files |
| `data/round-2/runs/<model>.<arm>.<case>.<rep>.{jsonl,err}` | Same, for round 2 and the final arm (`<model>` is the route with `/` replaced by `_`) |
| `data/round-2/diffs/<model>.<arm>.<case>.<rep>.diff` | Final diffs |
| `data/round-2/scores.json` | Per-run scores (188 rows, including the 20 final-arm runs) with the session-verified model |

Work repositories were not preserved, only the diffs. All files were passed through the repository anonymizer. Local paths are replaced with `~` or placeholders, and OpenCode session IDs are replaced with salted hashes.
