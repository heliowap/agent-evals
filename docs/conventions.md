# Conventions

## Layout

Each study lives in `evals/<slug>/`:

| Path | Contents |
|---|---|
| `README.md` | The paper (structure below) |
| `harness/` | Runners, scorers, case definitions, prompt variants and fixtures needed to rerun the study |
| `data/` | Anonymized raw data: run events, scores, diffs, logs and summaries |

All prose written for this repository is in English. The studies were run with Portuguese-language harnesses, so some archived artifacts are in Portuguese and keep their original bytes, because recorded hashes cover them or because they are the historical record. Human-written documents among them (harness READMEs, design docs, rubrics, decision logs, earlier reports) have an English sibling (`*.en.md`, `*.en.tsv`). Machine-generated reports, frozen source copies, validation logs and model output stay in their original language as raw data; each paper describes what they contain.

Large text files are stored gzipped (`*.gz`). Third-party code, binaries and upstream corpora are not redistributed; the README cites the upstream URL and revision instead.

## Paper structure

1. **Title**, run dates, tool versions, and a one-paragraph **Abstract** stating the main finding.
2. **Introduction**: the question and why it matters for agent configuration.
3. **Hypotheses**: what was expected before the runs, stated so the results can confirm or refute them. When hypotheses were not written down before the runs, say so.
4. **Methodology**: harness, models and routes, arms or conditions, cases, repetitions, scoring rules, and statistics. Prompts appear verbatim in the language they were run in, followed by an English translation.
5. **Results**: tables of the measured outcomes, by arm and by model, with counts (k/n), not only percentages.
6. **Discussion**: interpretation, what changed in the configuration as a result, limitations and threats to validity.
7. **Reproduction** and **Data**: commands, and the layout of `data/`.

Post hoc tests are labelled exploratory. Numbers come from the archived data; a correction to an earlier report is stated as such.

## Anonymization

Every file in `harness/` and `data/` is copied through `tools/anonymize.py`, which:
- replaces local paths, the user name, host names and private IPs with placeholders (`~`, `<user>`, `<host>`, `<REDACTED_IP>`);
- redacts API keys, tokens and private keys (`<REDACTED_SECRET>`);
- replaces OpenCode session IDs with salted hashes, so runs stay linkable inside a dataset but cannot be matched to the original machine;
- drops provider configs, auth files, databases, virtualenvs and binaries.

`tools/scan.py` must report `findings=0` for the whole repository before a push.

Model routes such as `cli_proxy/...` or `cli_proxy_openai/...` are provider IDs of a local OpenAI-compatible proxy. They name the model that was requested; each study states how the answering model was verified.
