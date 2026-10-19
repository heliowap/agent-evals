# Does telling Codex subagents to talk to each other in English save tokens on Portuguese tasks? A 60-run pilot

- **Run dates:** 2026-10-11. Three-trial smoke check from about 19:12 UTC; main run frozen at 19:53 UTC, 60 trials finished by about 21:35 UTC. Audit and answer-key correction made after the run, the same day.
- **Tools:** Codex CLI 0.162.1 (version pinned and checked before every trial), model `gpt-6.1-sol`, reasoning effort `high` for the orchestrator and both subagents. Python 3.14 standard library only. macOS arm64.
- **Status:** pilot complete, 60/60 trials measurable. The blind human review of explanation quality and message language has **not** been done.

## Abstract

We tested whether adding one global instruction ("use English in delegations, messages and replies between agents") cuts token use and time when the user's task is written in Portuguese and the deliverables must be in Portuguese. Codex orchestrators had to delegate to exactly two subagents on four synthetic analysis tasks. We ran three conditions (no inter-agent language rule, Portuguese required, English required) × four tasks × five repetitions = 60 paired trials. **English did not reduce total tokens.** Summed over 20 trials per condition, English against the default used +2.6% total tokens (5,247,771 vs 5,113,021), −6.2% output tokens and −3.5% cumulative wall time. Input tokens make up about 98% of the total and rose 2.8%, along with 13 more model calls. English used fewer total tokens in only 9 of 20 pairs. Per-pair deltas ranged from −18.6% to +41.6%. After correcting a faulty answer key, accuracy was 20/20 (default), 19/20 (Portuguese) and 20/20 (English). The one failure was a list-ordering error. The adoption verdict is **inconclusive**: these data do not support recommending English between agents as a general way to save tokens or money.

## 1. Introduction

Many users write agent instructions in their own language. Tokenizers are usually more efficient on English, so a common piece of advice is to make agents "think and talk in English" internally and translate only at the edges. In a multi-agent workflow, the inter-agent traffic (delegation briefs, intermediate messages, subagent reports) is invisible to the user. It could be switched to English at no cost to the user experience, if switching actually saves anything.

This pilot measures that claim in a controlled setting. The question for agent configuration: should a global `AGENTS.md` for Portuguese-speaking users include an English-only rule for inter-agent communication?

## 2. Hypotheses

The hypotheses were not formally pre-registered. They are reconstructed from the frozen design (`freeze.json`, the package README written before the run, and the analysis plan in `run.py`):

- **H1 (primary):** `en` uses fewer total tokens (input + output, all sessions) than `default`.
- **H2:** `en` takes less wall-clock time than `default`.
- **H3 (secondary):** the same holds for `en` against `pt`. This comparison isolates the language choice from the mere presence of a language rule, because `pt` and `en` use the same sentence with only the language swapped.
- **H4 (quality guard):** `en` does not lower answer accuracy or Portuguese report quality.

The design explicitly did not assume that Portuguese costs a fixed percentage more. It did not set a minimum useful gain or a non-inferiority margin. This is why the planned verdict could only be "inconclusive" or a call for a confirmatory study.

## 3. Methodology

### 3.1 Harness

`harness/run.py` drives the Codex CLI non-interactively (`codex exec`). Each trial gets its own temporary directory, Git repository, `CODEX_HOME`, `config.toml` and global `AGENTS.md`. The `AGENTS.md` holds the treatment text and nothing else. The user's real profile and instructions are never touched. The credentials file is copied in with mode 0600 and deleted at the end. It is never written to the results.

Config (`harness/runtime.py`): `sandbox_mode = "workspace-write"`, `approval_policy = "never"`, web search disabled, plugins/apps/hooks/memories disabled, every discovered skill disabled by its `SKILL.md` path (78 skills per condition), `[agents] enabled = true`, `max_concurrent_threads_per_session = 2`, and subagent model and effort equal to the orchestrator's.

Before the first inference, a preflight runs `codex debug prompt-input` for each condition. It checks that the model-visible context is identical except for the treatment text (`equal_except_treatment: true`, see `data/validation/preflight/` and each run's `preflight.json`). This is not an HTTP capture, and file-system reads outside the work folder were not blocked.

### 3.2 Conditions

The treatment is the full content of the global `AGENTS.md`. Verbatim (Portuguese), each followed by an English translation:

| Condition | Global `AGENTS.md` (verbatim) | English translation |
|---|---|---|
| `default` | `Comunique-se com o usuário em português.` | Communicate with the user in Portuguese. |
| `pt` | `Comunique-se com o usuário em português.`<br>`Nas delegações, mensagens e respostas entre agentes, use português e instrua os subagentes a fazer o mesmo. Preserve citações, identificadores e conteúdos que precisem permanecer no idioma original.` | Communicate with the user in Portuguese. In delegations, messages and replies between agents, use Portuguese and instruct subagents to do the same. Preserve quotations, identifiers and content that must remain in the original language. |
| `en` | `Comunique-se com o usuário em português.`<br>`Nas delegações, mensagens e respostas entre agentes, use inglês e instrua os subagentes a fazer o mesmo. Preserve citações, identificadores e conteúdos que precisem permanecer no idioma original.` | Communicate with the user in Portuguese. In delegations, messages and replies between agents, use English and instruct subagents to do the same. Preserve quotations, identifiers and content that must remain in the original language. |

The instruction is written in Portuguese on purpose: the realistic case is a Portuguese-speaking user's config. Its own token cost is part of the measurement, including when it recurs in context.

### 3.3 Tasks

Every trial prompt is a common preamble plus a task prompt (`harness/cases.py`). The common preamble, verbatim:

```text
Trabalhe somente com os arquivos desta pasta. Use exatamente dois subagentes
diretos, com fork_turns="none", sem outros descendentes. Escolha a divisão de trabalho,
envie a cada um o contexto necessário e aguarde a conclusão de ambos. Use o mesmo
modelo e esforço desta sessão. Os subagentes devem retornar suas análises por mensagem;
somente você deve escrever os arquivos finais. Pode haver perguntas e correções entre vocês.
Entregue answer.json conforme o contrato solicitado e report.md em português, explicando
as decisões, evidências e ressalvas. Responda ao usuário em português. Preserve os
arquivos de entrada. Use apenas ferramentas locais; a tarefa dispensa acesso à internet.
```

> English translation: Work only with the files in this folder. Use exactly two direct subagents, with fork_turns="none", and no other descendants. Choose the division of work, send each the context it needs and wait for both to finish. Use the same model and effort as this session. The subagents must return their analyses by message; only you may write the final files. Questions and corrections between you are allowed. Deliver answer.json according to the requested contract and report.md in Portuguese, explaining the decisions, evidence and caveats. Reply to the user in Portuguese. Preserve the input files. Use only local tools; the task does not need internet access.

The four task prompts, verbatim, with translations:

**`incidente`** (incident diagnosis; inputs `operacao.md`, `mudanca.md`):

```text
Diagnostique o incidente cruzando operacao.md e mudanca.md. Identifique
a causa mais sustentada, o componente a reverter, as filas que exigem reprocessamento e
se há evidência de perda definitiva. Em answer.json use exatamente as chaves causa,
reverter, reprocessar e perda_confirmada. causa deve ser um dos códigos C1, C2, C3;
reverter deve ser o nome do componente; reprocessar é uma lista ordenada de IDs de filas;
perda_confirmada é booleano. Explique também por que as alternativas são menos sustentadas.
```

> Diagnose the incident by cross-checking operacao.md and mudanca.md. Identify the best-supported cause, the component to roll back, the queues that need reprocessing, and whether there is evidence of permanent loss. In answer.json use exactly the keys causa, reverter, reprocessar and perda_confirmada. causa must be one of the codes C1, C2, C3; reverter must be the component name; reprocessar is a sorted list of queue IDs; perda_confirmada is a boolean. Also explain why the alternatives are less well supported.

**`fornecedor`** (vendor selection; inputs `requisitos.md`, `propostas.md`):

```text
Escolha o fornecedor elegível de menor custo em 12 meses, cruzando
requisitos.md e propostas.md. Em answer.json use exatamente escolhido, elegiveis,
custo_12_meses_centavos e excluidos. elegiveis é uma lista de nomes em ordem alfabética;
excluidos mapeia cada nome inelegível para a lista ordenada dos códigos de requisitos
violados. Explique os cálculos, os motivos de exclusão e o desempate se necessário.
```

> Choose the eligible vendor with the lowest 12-month cost by cross-checking requisitos.md and propostas.md. In answer.json use exactly escolhido, elegiveis, custo_12_meses_centavos and excluidos. elegiveis is a list of names in alphabetical order; excluidos maps each ineligible name to the sorted list of violated requirement codes. Explain the calculations, the exclusion reasons and the tie-break if needed.

**`acessos`** (access policy over 16 requests; inputs policy and requests):

```text
Aplique a política aos pedidos. Em answer.json use exatamente permitidos
e negados, ambas listas de IDs em ordem crescente. No report.md explique cada decisão
negada e os casos de exceção ou fronteira. Não invente aprovações ausentes.
```

> Apply the policy to the requests. In answer.json use exactly permitidos and negados, both lists of IDs in ascending order. In report.md explain each denial and the exception or boundary cases. Do not invent missing approvals.

**`conciliacao`** (sales reconciliation; inputs `regras.md`, `eventos.json`):

```text
Concilie as vendas conforme regras.md e eventos.json. Em answer.json
use exatamente pedidos_incluidos (lista ordenada), receita_liquida_centavos (inteiro)
e por_canal_centavos (objeto com loja e web). Explique exclusões, duplicatas e estornos.
```

> Reconcile the sales according to regras.md and eventos.json. In answer.json use exactly pedidos_incluidos (sorted list), receita_liquida_centavos (integer) and por_canal_centavos (object with loja and web). Explain exclusions, duplicates and refunds.

All input documents are synthetic and in Portuguese (full text in `harness/cases.py` and `data/results/*/freeze.json`). Answer keys are never placed in the agents' work folder.

### 3.4 Design and schedule

4 tasks × 3 conditions × 5 repetitions = 60 trials (60 orchestrators, 120 planned subagents). Each block holds one task/repetition in all three conditions. Blocks were shuffled with a fixed seed (20261011). The six condition orderings were spread across blocks with frequencies differing by at most one. Trials ran one after another; the two subagents could run in parallel within a trial. Timeout: 300 s per trial (all agents included). No retries, no resumption. An earlier three-trial smoke check (`data/results/run-20261011-161200/`, one `incidente` trial per condition) is kept separate and excluded from every figure below.

### 3.5 Measurements

- **Tokens:** `input_tokens + output_tokens`, summed over every session in the trial (orchestrator and subagents). `harness/telemetry.py` reads per-response `token_usage_record` entries from the session rollouts. It deduplicates by `(thread_id, response_id)`, checks that the sum equals each session's last cumulative counter, and reconciles the CLI's final counter as orchestrator usage without double counting. A mismatch aborts the run. Cached input is a subset of input and reasoning is a subset of output; both are reported but not added.
- **Time:** wall clock from process launch to exit, including coordination, tools, waiting and generation; setup and grading excluded. Concurrent subagent durations are not summed.
- **Model calls:** number of model responses across all sessions.
- **Protocol:** `protocol_pass` checks the delegation structure (exactly two direct subagents, no descendants). It does not check language.
- **Accuracy:** exact match of `answer.json` against the key (types, keys, values), plus input files unchanged and a non-empty `report.md`.
- **Language:** `language-review.json` per trial lists every inter-agent message for human labelling.

Comparisons use `100 × (en / reference − 1)`; negative values favour English. We report both the ratio of sums over the 20 trials and the median of the 20 paired deltas. With five repetitions per task, no significance test was planned. All per-task breakdowns are descriptive.

## 4. Results

All 60 trials completed with exit code 0. None had infrastructure errors or timeouts, all passed `protocol_pass`, and native telemetry was reconciled for all 60. These figures were recomputed for this publication from the 60 `result.json` files, and by re-running `analyze.py` on the anonymized copy, which reproduces `data/pilot-analysis.json` exactly.

### 4.1 Totals by condition (20 trials each)

| Condition | Total tokens | Input tokens | of which cached | Output tokens | of which reasoning | Wall time, s | Model calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| `default` | 5,113,021 | 5,014,729 | 4,372,480 | 98,292 | 5,339 | 2,050.8 | 370 |
| `pt` | 5,274,575 | 5,177,553 | 4,499,328 | 97,022 | 4,818 | 2,048.9 | 382 |
| `en` | 5,247,771 | 5,155,575 | 4,472,704 | 92,196 | 5,235 | 1,979.6 | 383 |

Medians per trial: total tokens 257,571 / 251,188 / 253,534; wall time 102.7 / 101.4 / 98.2 s (default / pt / en).

### 4.2 English against each reference

| Metric | `en` vs `default`: ratio of sums | paired median [min; max] | `en` lower | `en` vs `pt`: ratio of sums | paired median | `en` lower |
|---|---:|---:|---:|---:|---:|---:|
| Total tokens | +2.6% | +2.4% [−18.6; +41.6] | 9/20 | −0.5% | −0.1% [−20.9; +52.9] | 11/20 |
| Input tokens | +2.8% | +2.4% | 9/20 | −0.4% | −0.1% | 12/20 |
| Output tokens | −6.2% | −3.6% [−29.0; +12.3] | 12/20 | −5.0% | −2.8% | 13/20 |
| Wall time | −3.5% | −2.4% [−23.1; +17.9] | 13/20 | −3.4% | −3.1% [−16.8; +8.3] | 12/20 |
| Model calls | +3.5% | +2.8% | 7/20 | +0.3% | 0.0% | 6/20 |

Split by agent role (exploratory, `en` vs `default`): orchestrator total tokens +1.5%, subagent total tokens +5.0%; orchestrator output −5.3%, subagent output −8.1% (29,259 vs 31,828).

### 4.3 By task, `en` vs `default` (5 pairs each)

| Task | Total tokens, ratio of sums | paired median | `en` lower | Wall time, ratio of sums | `en` faster |
|---|---:|---:|---:|---:|---:|
| `incidente` | +2.8% | +4.6% | 2/5 | −0.9% | 2/5 |
| `fornecedor` | +5.8% | +4.8% | 2/5 | −0.8% | 3/5 |
| `acessos` | −1.3% | −6.3% | 3/5 | −6.0% | 5/5 |
| `conciliacao` | +2.9% | +0.2% | 2/5 | −6.1% | 3/5 |

The direction changes across tasks, and the within-task spread is larger than any average effect.

### 4.4 Accuracy (with answer-key correction)

| Condition | Original automatic grade | Corrected grade | Decisions correct ignoring vendor list order | Protocol |
|---|---:|---:|---:|---:|
| `default` | 15/20 | 20/20 | 20/20 | 20/20 |
| `pt` | 16/20 | 19/20 | 20/20 | 20/20 |
| `en` | 15/20 | 20/20 | 20/20 | 20/20 |

**Correction to the original key.** The frozen key for `fornecedor` expected `elegiveis = ["Alfa", "Gama", "Épsilon"]`. That is Unicode code-point order, where `É` sorts after `G`. The prompt asked for alphabetical order, and in Portuguese alphabetical order `Épsilon` comes before `Gama`. We checked all 15 `fornecedor` answers in the raw `work/answer.json` files. 14 of 15 listed `["Alfa", "Épsilon", "Gama"]` and all other fields were correct, so the original grader failed them. One (`trial-0035`, `pt`) listed `["Alfa", "Gama", "Épsilon"]` and was the only original pass. The audit (`harness/analyze.py`) applies the corrected key to all conditions without changing prompts, answers or original records. As a result, 14 fails became passes and 1 pass became a fail. The original `report.md` and `summary.json` in the run folder still show the old grades. This matches the curated summary of the study.

### 4.5 Language compliance

Of 391 inter-agent messages, 271 (69.3%) were stored encrypted by the CLI (`encrypted_content`): all delegations (`spawn_agent`) and intermediate `send_message` calls. Only the 120 subagent final returns were readable, 40 per condition. Encrypted messages: default 87, pt 88, en 96. **Whether delegations followed the language rule cannot be observed**, so full compliance is unknown.

The human language labels were never filled in. As an **exploratory** check for this publication, we ran a crude stop-word count over the 120 readable returns (Portuguese vs English function words). It classified 40/40 `default` and 40/40 `pt` returns as Portuguese. In `en`, 38/40 were English and 2/40 (both in `trial-0010`) were bare JSON with no prose. So where the returns can be seen, the English rule was followed. This heuristic is not the prescribed blind review.

### 4.6 Explanation quality

The blind review of `report.md` explanations (`harness/REVIEW.md`; 60 shuffled samples in `data/results/run-20261011-165334/blind-review/`) is pending: all 60 entries in `ratings.json` are `null`. H4 is therefore tested only for structured answers.

### 4.7 Hypotheses

| Hypothesis | Outcome |
|---|---|
| H1: `en` < `default` in total tokens | **Not supported.** +2.6% (sums), +2.4% (median), lower in 9/20 pairs |
| H2: `en` faster than `default` | **Weak, unconfirmed tendency.** −3.5% (sums), faster in 13/20; no latency profiling, service load uncontrolled |
| H3: `en` < `pt` | **Not supported for total tokens** (−0.5%, 11/20). Output −5.0%, time −3.4% |
| H4: no quality loss | **Supported for structured answers** (20/20 vs 20/20 after correction). **Untested for explanations** |

## 5. Discussion

**Why less output did not mean fewer tokens.** Output tokens are under 2% of the total. Each call re-reads a long, mostly cached context (the system prompt, tool schemas, task files, the conversation so far), so input dominates. English produced about 6% fewer output tokens, consistent with denser tokenization of English prose. But `en` trials made 13 more model calls and used 2.8% more input, which more than offset the output saving. The data cannot tell whether the extra calls come from the language rule (e.g. translation overhead, more back-and-forth `send_message` traffic: 56 in `en` vs 47 in the other two) or from noise. Per-pair variation of −19% to +42% shows that strategy variance (how many turns, how much context is re-read) swamps any tokenization effect at this sample size.

**Configuration decision.** The English inter-agent rule was **not adopted**. The pilot does not justify recommending English between agents as a general token or cost saving for Portuguese-speaking users. A follow-up study would need to measure reused history and call counts as well as language, on new tasks, with a minimum useful gain and an acceptable regression margin fixed in advance.

**Limitations and threats to validity.**
- Four synthetic tasks with five repetitions each. Repetitions are not new tasks, and the results do not generalize to coding, web research or inherited history.
- The workflow was forced: exactly two direct subagents with `fork_turns="none"` (clean child context). Free choice of subagent count and full-history forking were not tested.
- One model, one effort level, one CLI version.
- 69% of inter-agent messages were encrypted, so language compliance is only partly observable.
- No blind human review of explanation quality or language.
- Remote cache state and service load were not controlled. Order balancing reduces their influence but does not remove it. There was no latency profile separating generation, tools, cache and queueing, so the time difference should not be read as a reproducible speed gain.
- Raw token totals are not a monetary cost estimate (cached and uncached input are priced differently).
- The answer key was corrected after the run. The correction is mechanical (collation), applied identically to all conditions, and made without unblinding conditions for quality judgements. It still shows that the key was not checked before the run.
- The agents could in principle read files outside the work folder; isolation is by configuration, not by sandboxing reads.

## 6. Reproduction

Requirements: Python 3.10+, Git, Codex CLI 0.162.1 with an existing login. Running the study uses the login's quota. All commands below are run from `harness/`.

```sh
# no inference
python3 -m unittest -v test_eval.py
python3 run.py plan
python3 run.py preflight

# smoke check (3 trials; do not merge into the sample)
python3 run.py run --cases incidente --reps 1

# full pilot (creates a new results/run-YYYYMMDD-HHMMSS)
python3 run.py run --model gpt-6.1-sol --effort high --reps 5 --timeout 300
```

Re-run the audit on the published data without calling any model:

```sh
python3 analyze.py ../data/results/run-20261011-165334 --out /tmp/pilot-analysis.json --skip-docs-hash
```

The output matches `data/pilot-analysis.json` except for the `source_run` path. Two small changes were made to the published harness relative to the run:
- `analyze.py` gained an opt-in `--skip-docs-hash` flag. Anonymization replaced a home path in the frozen `README.md`, so its SHA-256 no longer matches `freeze.json`. All frozen `.py` files and `REVIEW.md` still match their recorded hashes.
- `build_visual.py` reads from `../data/` instead of its own folder.

All other harness files are byte-identical to the frozen sources. The report generator in `run.py` and the HTML view still produce Portuguese text.

## 7. Data

```text
data/
├── pilot-analysis.json        # audited figures, corrected key, per-task comparisons (output of analyze.py)
├── smoke-audit.json           # audit of the 3-trial smoke check
├── verification.json          # unit tests (16 passed), preflight summary, source hashes
├── show-me-resultados-idioma.html  # offline interactive view (Portuguese UI), built by build_visual.py
├── original-docs-pt/          # original Portuguese package README and review protocol
├── validation/preflight/      # standalone context preflight
└── results/
    ├── run-20261011-161200/   # smoke check, 3 trials (excluded from analysis)
    └── run-20261011-165334/   # main pilot, 60 trials
        ├── freeze.json        # conditions, prompts, keys (original), schedule, seed, source hashes
        ├── frozen-source/     # harness as run
        ├── preflight.json     # per-condition model-visible context audit
        ├── summary.json, report.md   # original automatic report (old key; Portuguese)
        ├── blind-key.json, blind-review/   # blinded samples and empty ratings.json
        └── trial-NNNN/
            ├── prompt.txt, final.txt, events.jsonl, stderr.txt
            ├── isolation.json         # effective config / context inspection
            ├── rollouts/*.jsonl       # all Codex session rollouts (inter-agent messages encrypted)
            ├── telemetry.json         # reconciled per-session usage
            ├── language-review.json   # inter-agent messages for labelling (labels empty)
            ├── result.json            # status, grade (original key), usage, tool calls
            └── work/                  # input files + answer.json + report.md
```

Everything was copied through the repository anonymizer. Session and thread IDs are Codex UUIDs generated per temporary `CODEX_HOME` and kept as-is. Nothing was excluded apart from Python bytecode caches. The study is about 22 MB.
