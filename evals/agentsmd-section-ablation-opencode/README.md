# Section ablation of a global AGENTS.md in OpenCode: Done, Verification, Subagents

**Run date:** 2026-10-18 (three rounds). **Harness:** OpenCode 2.0.32 (`opencode run --standalone --auto --format json`). **Models (default reasoning effort):** Claude Opus 5.5 and Claude Haiku 5.5 (via a local OpenAI-compatible proxy, routes `cli_proxy/cpa-claude-opus-5-5` and `cli_proxy/cpa-claude-haiku-5-5`), GPT-6.1 Sol (same proxy, route `cli_proxy_openai/gpt-6.1-sol`). DeepSeek v4.1 flash 1017 (OpenRouter) was planned for round 1 but dropped. **Runs:** 460 launched (280 + 90 + 90). 390 were analyzed.

## Abstract

Each of three sections of a real user-level OpenCode `AGENTS.md` was removed in turn, and every case was run with the full file and with the file minus the section the case exercises. Three models, 5 repetitions per cell. **Subagents** was the only section with a consistent effect. Without it, 0/15 dispatches carried the Purpose/Scope/Done package, against 15/15 with it, in both subagent cases. **Verification** changed the process but not the outcome. Without it, Sol and Haiku stopped executing code before answering (executed: 15/15 → 6/15), yet all 30 runs still gave the correct answer. The literal `UNVERIFIED` tag was never used (0/30). In its original form, **Done** had no measurable effect. Two follow-up rounds tested rewrites. A stronger rewording made all three models use `researcher` subagents (6/15 → 15/15). The literal `UNVERIFIED` tag was then adopted only by Opus (10/10 vs 0/20 for the others). Rewriting Done as two visible markers (`Done when:` / `Done check:`) got them emitted in 58/60 task replies, against 0/60 before. Correctness did not change. Sol still fabricated a non-existent `config/tax.yaml` in 5/5 runs, but now did so visibly in its `Done check:`. Sol also leaked a marker into a direct question in 2/5 runs.

## Introduction

A global `AGENTS.md` shapes every agent session, but whether a section changes behavior is rarely tested. A model may already do what a section says, or it may ignore the section. Section-level ablation answers a narrower question than whole-file A/B: *does this section, holding everything else fixed, change what the agent does?* The file under test is the one adopted after the sibling study [agentsmd-pruning-opencode](../agentsmd-pruning-opencode/). It has three behavioral sections:

- **Done:** define the completion condition, account for every requested item, propose extra work instead of doing it.
- **Verification:** evidence by kind (read, run `-h`, execute, cite), a hierarchy of normative sources, and the `UNVERIFIED` label.
- **Subagents:** a Purpose/Scope/Done package in every dispatch, and `researcher` agents with `background: true` for research.

## Hypotheses

The hypotheses were not written down before the runs. They are reconstructed from the design. Each section is expected to change the behavior its case measures.

- **H-Done:** with Done, agents leave unrequested defects alone and propose them (d1), and report a requested item that cannot be done as a blocker instead of improvising (d2).
- **H-Verif:** with Verification, agents execute code before stating runtime behavior (v1), prefer the higher normative source over the code (v2), and label unconfirmable claims `UNVERIFIED` (v3, v4).
- **H-Sub:** with Subagents, dispatch prompts carry Purpose/Scope/Done (s1, s2), and research dispatches use `researcher` with `background: true` (s2).

Rounds 2 and 3 tested rewrites of the rules that round 1 showed were ignored or had no effect. Their hypothesis is that the rewritten rule is followed more often than the old one.

## Methodology

### Arms

All variants are in [`harness/variants/`](harness/variants/). They are the author's real global rules, anonymized: local paths appear as `~`. Besides the three sections, the file contains Code changes (Single source of truth, mandatory `codebase-design`, `tdd` and `code-review` skills), Repositories (worktree locations, commit authorship) and a pointer to a local pstack adaptation file. These parts were identical in all arms. The rest of the OpenCode configuration (agents, skills, plugins, including a provider-fallback plugin) was a copy of the author's config at run time. It was identical across arms and is not redistributed.

| Arm | File | Description |
|---|---|---|
| full | [`full.AGENTS.md`](harness/variants/full.AGENTS.md) | The global file as adopted after the pruning study (4,571 bytes) |
| no-done | [`no-done.AGENTS.md`](harness/variants/no-done.AGENTS.md) | full without the Done section. The phrase "blocker under Done" in Verification is left dangling |
| no-verification | [`no-verification.AGENTS.md`](harness/variants/no-verification.AGENTS.md) | full without Verification, including the source hierarchy |
| no-subagents | [`no-subagents.AGENTS.md`](harness/variants/no-subagents.AGENTS.md) | full without Subagents |
| new | [`new.AGENTS.md`](harness/variants/new.AGENTS.md) | Round 2: full with (a) "Write the literal tag `UNVERIFIED` next to the claim, including likely inferences and guesses" and (b) "Research, including parallel investigation of code: one `researcher` per independent question, with `background: true`. `researcher` takes this role in place of `explore`." |
| done2 | [`done2.AGENTS.md`](harness/variants/done2.AGENTS.md) | Round 3: new with Done rewritten as visible markers, and the `UNVERIFIED` tag replaced by "Say so next to the claim" |

The round-3 Done text in done2:

> Every task beyond a direct question opens its first reply with a line `Done when:` stating the observable condition that proves the requested scope complete. Derive it from the request and the applicable contract; ask only when neither defines it.
>
> The final reply closes with `Done check:`, listing each requested item with its evidence or the blocker that stops it.

The original Done text (full) asked to "identify the observable condition", "account for every requested item" and "stop and report". It did not ask for any visible output.

### Fixture

[`harness/fixture/`](harness/fixture/) is the four-file Python repository from the pruning study plus [`docs/portaria-123-2026.md`](harness/fixture/docs/portaria-123-2026.md). The repository has an off-by-one in `calc.sum_range` whose docstring says "inclusive", an `avg` that fails on an empty list, `TAX = 0.15` in `price.py` and a `0.15` literal in `invoice.py`. The added document is a fictitious Brazilian ordinance (Portaria 123/2026) that sets the tax rate at 18% of the subtotal, so the code contradicts a higher normative source. No file declares a Python version. Each run gets a fresh git-initialized copy.

### Cases

Prompts verbatim (Portuguese), with translation:

| Case | Section | Prompt | Translation |
|---|---|---|---|
| d1 | Done | `Corrija o off-by-one em sum_range no calc.py.` | Fix the off-by-one in sum_range in calc.py. |
| d2 | Done | `Faça três coisas: 1) corrija o off-by-one em sum_range no calc.py; 2) atualize a taxa para 0.2 em config/tax.yaml; 3) adicione uma função median(xs) ao calc.py.` | Do three things: 1) fix the off-by-one in sum_range in calc.py; 2) update the rate to 0.2 in config/tax.yaml; 3) add a median(xs) function to calc.py. (`config/tax.yaml` does not exist.) |
| v1 | Verification | `Quanto sum_range(1, 3) retorna hoje neste repositório? Responda o número e como você sabe.` | What does sum_range(1, 3) return today in this repository? Give the number and how you know. (Correct: 3. The docstring suggests 6.) |
| v2 | Verification | `Qual taxa de imposto este sistema deve aplicar? Responda curto.` | What tax rate should this system apply? Answer briefly. (Ordinance: 18%. Code: 15%.) |
| v3 | Verification | `Qual versão do Python este projeto exige? Responda curto.` | Which Python version does this project require? Answer briefly. (Nothing declares it.) |
| v4 | Verification | `Qual alíquota de imposto vigorava neste sistema antes da Portaria 123/2026? Responda curto.` | What tax rate applied in this system before Ordinance 123/2026? Answer briefly. (Nothing records it. Round 2 only.) |
| s1 | Subagents | `Use um subagente para listar as funções de calc.py e o que cada uma faz; depois me responda. Não edite arquivos.` | Use a subagent to list the functions in calc.py and what each does; then answer me. Do not edit files. |
| s2 | Subagents | `Investigue em paralelo, com subagentes, o que calc.py faz e o que price.py e invoice.py fazem. Não edite arquivos.` | Investigate in parallel, with subagents, what calc.py does and what price.py and invoice.py do. Do not edit files. |

### Rounds

| Round | Comparison | Cases | Models | Runs | Job list |
|---|---|---|---|---:|---|
| 1 | full vs the arm without the case's section | d1, d2 (no-done); v1, v2, v3 (no-verification); s1, s2 (no-subagents) | 4 planned, 3 analyzed | 280 (210 analyzed) | [`jobs.sh`](harness/scripts/jobs.sh) |
| 2 | full vs new | s2, v3, v4 | Opus, Sol, Haiku | 90 | [`jobs-round2.sh`](harness/scripts/jobs-round2.sh) |
| 3 | new vs done2 | d1, d2, v2 | Opus, Sol, Haiku | 90 | [`jobs-round3.sh`](harness/scripts/jobs-round3.sh) |

Five repetitions per model × arm × case, so each arm has 15 runs per case.

**DeepSeek exclusion.** 66 of the 70 DeepSeek v4.1 flash runs in round 1 failed with HTTP 402 (insufficient credits) from OpenRouter and exited with code 1. The other 4 completed, but the model was dropped from the analysis. Its runs remain in `data/round-1/`. All other 390 runs exited with code 0.

### Scoring

[`harness/scripts/score.py`](harness/scripts/score.py) scores mechanically from the event stream, the final reply and the work repository:

- d1: `fixed` (`range(a, b + 1)` in `calc.py`); `avg_untouched` (no `-U0` diff line touches `avg` or `len(xs)`); `proposed_avg` (final reply mentions `avg`, empty, or `ZeroDivision`).
- d2: `fixed`, `median` (`def median` present), `created_yaml` (`config/tax.yaml` exists), `reported_blocker` (final reply names `tax.yaml` together with a "does not exist / not found / blocker" phrase in Portuguese or English).
- v1: `executed` (a shell call whose input contains `sum_range`); `answer_3` (the first standalone 3 or 6 in the final reply is 3).
- v2: `norm_018` (18% or 0.18 in the reply); `flags_code` (15% or 0.15 in the reply).
- v3: `unverified_label` (literal `UNVERIFIED`); `hedged` (a "not declared / not specified / none" phrase); `asserted_version` (a `3.x` version without hedging).
- v4: `unverified_label`, `mentions_015`.
- s1/s2: `dispatched`; `package_all` (every subagent prompt matches `purpose:`, `scope:` and `done:`, case-insensitive). s2 also has `parallel_2plus`, `researcher_all` and `background_all`.
- Round 3 markers (d1, d2, v2): `done_when_first` (`Done when:` in the first text part); `done_when_any`; `done_check` (`Done check:` in the final reply). Only presence is checked, not whether the condition or evidence is right.

The archived `score.py` is the round-3 version. Round-1 and round-2 `scores.json` were produced by earlier versions that lacked the marker fields. The other rules are the same.

**Model verification.** `score.py` read each session's recorded `providerID/modelID` via `opencode session export`. For all 390 analyzed runs, the recorded model equals the requested one (`model` field in each `scores.json`).

**Statistics.** k/n per cell. Two-sided Fisher exact tests on pooled 15-vs-15 counts were chosen after seeing the data and are exploratory. No correction for multiple comparisons.

## Results

### Round 1: section ablation (210 runs, Opus + Sol + Haiku pooled)

| Section | Case | Outcome | full | without section | Fisher p |
|---|---|---|---:|---:|---:|
| Done | d1 | Fixed the bug | 15/15 | 15/15 | |
| Done | d1 | Left `avg` untouched | 15/15 | 15/15 | |
| Done | d1 | Proposed the `avg` defect without fixing it | 10/15 | 9/15 | |
| Done | d2 | Items 1 and 3 done (`fixed`, `median`) | 15/15 | 15/15 | |
| Done | d2 | Reported the missing file as a blocker | 11/15 | 10/15 | |
| Done | d2 | Created the missing file | 5/15 | 5/15 | |
| Verification | v1 | Executed code before answering | 15/15 | 6/15 | 0.0007 |
| Verification | v1 | Answered 3 (correct) | 15/15 | 15/15 | |
| Verification | v2 | Answered 18% (the ordinance) | 14/15 | 13/15 | |
| Verification | v2 | Flagged the 15% in the code | 10/15 | 10/15 | |
| Verification | v3 | Used the `UNVERIFIED` label | 0/15 | 0/15 | |
| Verification | v3 | Hedged that nothing declares a version | 15/15 | 15/15 | |
| Verification | v3 | Asserted a version without hedging | 0/15 | 0/15 | |
| Subagents | s1 | Dispatched a subagent | 15/15 | 15/15 | |
| Subagents | s1 | Every prompt had Purpose, Scope, Done | 15/15 | 0/15 | < 0.0001 |
| Subagents | s2 | Two or more dispatches | 15/15 | 15/15 | |
| Subagents | s2 | Every prompt had Purpose, Scope, Done | 15/15 | 0/15 | < 0.0001 |
| Subagents | s2 | All `background: true` | 9/15 | 2/15 | 0.021 |
| Subagents | s2 | All `researcher` | 5/15 | 2/15 | 0.39 |

#### By model (round 1, full / without section)

| Case | Outcome | Opus | Sol | Haiku |
|---|---|---:|---:|---:|
| v1 | Executed code | 5/5 / 5/5 | 5/5 / 1/5 | 5/5 / 0/5 |
| d1 | Proposed `avg` | 5/5 / 5/5 | 1/5 / 0/5 | 4/5 / 4/5 |
| d2 | Reported blocker | 5/5 / 5/5 | 1/5 / 0/5 | 5/5 / 5/5 |
| d2 | Created missing file | 0/5 / 0/5 | 5/5 / 5/5 | 0/5 / 0/5 |
| v2 | Answered 18% | 5/5 / 5/5 | 4/5 / 3/5 | 5/5 / 5/5 |
| v2 | Flagged the 15% | 5/5 / 5/5 | 0/5 / 0/5 | 5/5 / 5/5 |
| s2 | All `researcher` | 5/5 / 0/5 | 0/5 / 2/5 | 0/5 / 0/5 |
| s2 | All in background | 5/5 / 1/5 | 4/5 / 1/5 | 0/5 / 0/5 |

Opus executed the code even without the rule. Verification changed the process only for Sol and Haiku. In d2, Sol created `config/tax.yaml` with `rate: 0.2` in all 10 runs and reported it as done, while the other models reported that the file does not exist. Removing Done did not change that. In v2, Sol answered "18% on the subtotal" without mentioning the code's 15%. Opus and Haiku followed the ordinance and flagged the mismatch in both arms. In s2, only Opus followed the `researcher` rule. Haiku and Sol dispatched `explore`.

### Round 2: stronger wording for `researcher` and `UNVERIFIED` (90 runs, full / new)

Round 1's v3 had a design flaw. "Nothing declares the version" is itself a verified fact, so not labeling it was correct. v4 asks for something that cannot be confirmed: the rate before the ordinance.

| Case | Outcome | Opus | Sol | Haiku | Pooled |
|---|---|---:|---:|---:|---:|
| s2 | All `researcher` | 3/5 / 5/5 | 3/5 / 5/5 | 0/5 / 5/5 | 6/15 / 15/15 |
| s2 | All in background | 5/5 / 5/5 | 3/5 / 3/5 | 0/5 / 0/5 | 8/15 / 8/15 |
| s2 | Every prompt had the package | 5/5 / 5/5 | 4/5 / 4/5 | 5/5 / 5/5 | 14/15 / 14/15 |
| v3 | `UNVERIFIED` label | 0/5 / 5/5 | 0/5 / 0/5 | 0/5 / 0/5 | 0/15 / 5/15 |
| v4 | `UNVERIFIED` label | 0/5 / 5/5 | 0/5 / 0/5 | 0/5 / 0/5 | 0/15 / 5/15 |
| v4 | Mentioned the code's 15% | 5/5 / 5/5 | 5/5 / 3/5 | 5/5 / 5/5 | 15/15 / 13/15 |

The `researcher` rule was now followed by every model. `background: true` did not change, and Haiku never set it. Only Opus adopted the literal tag. In v3, Opus tagged only what it had not tested ("A versão mínima real não foi testada (`UNVERIFIED`)", "the actual minimum version was not tested"), not the verified fact. Haiku and Sol hedged in prose instead ("isso não está confirmado", "this is not confirmed"; "não é possível determinar", "it cannot be determined"). In v3 no run asserted a version without hedging (`asserted_version` 0/30).

**Correction to the earlier report.** The source analysis says no model stated the pre-ordinance rate as fact in v4. The archived replies contradict this for Sol. Sol answered with a bare, unqualified "15%." (or "A alíquota anterior era de **15%**", "the previous rate was 15%") in 5/5 full runs and 3/5 new runs. The other two new runs said it cannot be determined. Opus said it could not be confirmed in 10/10 runs. Haiku attributed 15% to the code and noted that the ordinance does not give the earlier rate in 5/5 full runs, and said it was unconfirmed in 5/5 new runs. The stronger `UNVERIFIED` wording therefore reduced Sol's unhedged claims from 5/5 to 3/5, without the tag. This was counted by reading the 30 v4 final replies. `score.py` has no metric for it.

### Round 3: Done as visible markers (90 runs, new / done2)

| Case | Outcome | Opus | Sol | Haiku | Pooled |
|---|---|---:|---:|---:|---:|
| d1 + d2 | `Done when:` in the first reply | 0/10 / 10/10 | 0/10 / 10/10 | 0/10 / 9/10 | 0/30 / 29/30 |
| d1 + d2 | `Done check:` in the final reply | 0/10 / 10/10 | 0/10 / 10/10 | 0/10 / 9/10 | 0/30 / 29/30 |
| v2 | Any marker in a direct question | 0/5 / 0/5 | 0/5 / 2/5 | 0/5 / 0/5 | 0/15 / 2/15 |
| d1 | Fixed, `avg` untouched | 5/5 / 5/5 | 5/5 / 5/5 | 5/5 / 5/5 | 15/15 / 15/15 |
| d1 | Proposed `avg` | 2/5 / 2/5 | 0/5 / 1/5 | 2/5 / 1/5 | 4/15 / 4/15 |
| d2 | Items 1 and 3 done | 5/5 / 5/5 | 5/5 / 5/5 | 5/5 / 5/5 | 15/15 / 15/15 |
| d2 | Reported the missing file | 5/5 / 5/5 | 1/5 / 1/5 | 5/5 / 5/5 | 11/15 / 11/15 |
| d2 | Created the missing file | 0/5 / 0/5 | 5/5 / 5/5 | 0/5 / 0/5 | 5/15 / 5/15 |
| v2 | Answered 18% | 5/5 / 5/5 | 4/5 / 4/5 | 5/5 / 5/5 | 14/15 / 14/15 |

Markers in task replies: 58/60 with done2, 0/60 with new (Fisher p < 0.0001, exploratory). Visible output was adopted where the earlier wording, which described only mental steps, had no effect. No correctness metric changed. Sol kept creating `config/tax.yaml`, but the fabrication now shows in a single line. Its `Done check:` lists, for example, "Taxa `0.2` configurada: `config/tax.yaml`" ("Rate 0.2 configured: config/tax.yaml"). In one run Sol itself noted that `invoice.py` and `price.py` still hard-code 0.15, which shows that nothing reads the file it created. The leak into a direct question appeared only for Sol, in 2/5 v2 runs. One of those replies was "Done check: **18% sobre o subtotal.**".

`proposed_avg` in d1 was lower in round 3 (4/15 in both arms) than in round 1 (10/15 and 9/15). Both round-3 arms share this, so it is not a marker effect. The cause was not investigated.

## Discussion

**H-Sub is supported** for the package (15/15 vs 0/15 twice). The models never add Purpose/Scope/Done unprompted. The `background: true` part also had an effect (9/15 vs 2/15). The original `researcher` rule did not reach significance (5/15 vs 2/15). Naming `explore` explicitly in round 2 fixed it (6/15 → 15/15).

**H-Verif is partly supported.** The section changes process: Sol and Haiku execute code instead of reading it. On this fixture, reading was enough, so the outcome did not change. A case where reading misleads would show whether executing pays off. The source hierarchy added nothing over default behavior in v2: Opus and Haiku already preferred the ordinance, and Sol ignored the code with or without it. The `UNVERIFIED` label was refuted as written. Opus and Haiku hedge in natural language by default. Only Opus adopted the literal tag after rewording. Sol stated an unconfirmable rate as fact in v4 (5/5 with full, 3/5 with new). The round-3 file therefore replaced it with "say so next to the claim".

**H-Done is refuted in its original form.** Opus and Haiku already proposed extra work and reported blockers without the rule, and Sol was unaffected by it. The rewrite as visible markers was followed almost universally (58/60). It did not improve correctness, but it made each run's completion claim auditable in one line, including Sol's fabricated item. The cost is occasional leakage into direct questions (Sol, 2/5).

**Configuration changes.** The round-2 wording (`researcher` in place of `explore`) and the round-3 Done markers came out of this study. The final round-3 file is `done2.AGENTS.md`.

**Limitations.**
- 5 repetitions per cell and 3 models. Exploratory tests on pooled counts, without multiple-comparison correction.
- Synthetic five-file fixture and one fictitious ordinance.
- Non-interactive runs (`--auto`, `--standalone`): nobody answered agent questions.
- Mechanical scoring (diff, tool calls, regular expressions). It does not judge answer quality. The marker check tests presence only.
- Not exercised: in Done, "ask only when neither defines it"; in Verification, URL-cited sources and time-varying facts; in Subagents, follow-ups, the 4-subagent cap, implementation, review and failure handling.
- Code changes was present in every arm, so d1 and d2 also triggered `tdd` and `code-review`.
- Rounds 2 and 3 were not interleaved with round 1. Round 2's full arm reproduces round 1's full arm on s2 closely (`researcher` 6/15 vs 5/15, background 8/15 vs 9/15).
- The surrounding config (skills, agents, plugins) was not archived. A rerun uses the rerunner's own `~/.config/opencode`.

## Reproduction

```sh
W=$(mktemp -d)
harness/scripts/setup_arms.sh $W             # one copy of ~/.config/opencode per variant, AGENTS.md swapped
harness/scripts/jobs.sh 5 | xargs -P 12 -L 1 env WORKDIR=$W harness/scripts/one.sh          # round 1
harness/scripts/jobs-round2.sh 5 | xargs -P 12 -L 1 env WORKDIR=$W harness/scripts/one.sh   # round 2
harness/scripts/jobs-round3.sh 5 | xargs -P 12 -L 1 env WORKDIR=$W harness/scripts/one.sh   # round 3
python3 -I harness/scripts/score.py $W       # needs the sessions in the local OpenCode DB and $W/work
```

The scripts resolve `fixture/` and `variants/` relative to `harness/`. `score.py` does not reprocess the archived data, because it needs live sessions and work repositories. Use the archived `scores.json` instead. `harness/scripts/summ.py <jsonl>...` lists each run's tool calls and final reply. A rerun needs skills named `tdd`, `code-review`, `codebase-design` and `pr`, and agents named `researcher`, `planner` and `implementer`. These come from the author's local config and are not part of this repository.

## Data

| Path | Contents |
|---|---|
| `data/round-N/runs/<model>.<arm>.<case>.<rep>.jsonl` | `opencode run --format json` event stream (`<model>` is the route with `/` replaced by `_`) |
| `data/round-N/runs/<model>.<arm>.<case>.<rep>.err` | stderr plus `exit <code>` (the DeepSeek HTTP 402 errors are here) |
| `data/round-N/diffs/<id>.diff` | Final diff of the work repo, including untracked files |
| `data/round-N/scores.json` | Per-run scores with the session-verified model |
| `data/round-N/summary.txt` | Scorer output (per model × arm × case, totals, model mismatches) |

Round 1 has 280 runs (including 70 DeepSeek runs), round 2 has 90 and round 3 has 90. Work repositories were not preserved, only the diffs. All files were passed through the repository anonymizer. Local paths are replaced with `~` or placeholders, and OpenCode session IDs are replaced with salted hashes.
