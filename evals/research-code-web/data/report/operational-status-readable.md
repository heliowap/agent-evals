# Operational evaluation outcome

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](pesquisa/research-eval-design-20261007T184125Z/report/operational-status.md). Os links e comandos desta versão acompanham a organização por tema.


**INCOMPLETE — NO QUALIFIED WINNER.**

Of 648 scheduled trials, 156 were attempted, 126 returned a final answer, 30 ended without an operationally completed answer, and 492 were not run.

Execution stopped on trial 156 after the fixed Exa/OpenCode search broker reported transport or response decoding unavailable. This is a shared-tool failure, not evidence that GLM’s factual reasoning is wrong. The precise transport cause remains UNVERIFIED.

Gemini returned final answers in all 51 attempted Gemini trials; no prefill rejection was recorded. This establishes observed operational completion only, not answer accuracy.

The following tables are operational observations, **not quality rankings**. Semantic grading is pending at this snapshot.

## Read-only code exploration

| Configuration | Attempted | Final answers | Operational completion | Completed-answer median (s) |
|---|---:|---:|---:|---:|
| deepseek-high | 9 | 4 | 44.4% | 43.21 |
| deepseek-low | 9 | 6 | 66.7% | 55.62 |
| deepseek-max | 9 | 2 | 22.2% | 85.81 |
| gemini-high | 9 | 9 | 100.0% | 118.14 |
| gemini-low | 9 | 9 | 100.0% | 45.02 |
| gemini-medium | 9 | 9 | 100.0% | 94.88 |
| glm-high | 9 | 9 | 100.0% | 69.63 |
| glm-low | 9 | 8 | 88.9% | 36.23 |
| glm-max | 9 | 4 | 44.4% | 68.05 |

## Web search/fetch

| Configuration | Attempted | Final answers | Operational completion | Completed-answer median (s) |
|---|---:|---:|---:|---:|
| deepseek-high | 8 | 8 | 100.0% | 45.91 |
| deepseek-low | 8 | 8 | 100.0% | 30.72 |
| deepseek-max | 8 | 5 | 62.5% | 84.28 |
| gemini-high | 8 | 8 | 100.0% | 54.53 |
| gemini-low | 8 | 8 | 100.0% | 20.38 |
| gemini-medium | 8 | 8 | 100.0% | 45.23 |
| glm-high | 9 | 8 | 88.9% | 53.11 |
| glm-low | 9 | 7 | 77.8% | 74.45 |
| glm-max | 9 | 6 | 66.7% | 139.24 |

## Integrity

- Audit passed: 648 terminal records, 1,032 client generation starts; no replayed starts.
- All 9,076 frozen input files remain unchanged; credential scan found zero matches.
- Trial 49 lacks its historical supervisor receipt; recovery preserved its valid terminal record and disclosed the limitation.
- Repeated server restarts were reported by the harness; process and tool outages prevent a complete comparison.
- Blind semantic grades, their independent review and final-grade seal were not available at this operational snapshot.

Machine-readable observations: `pesquisa/research-eval-design-20261007T184125Z/report/operational-status.json`. The planned semantic report is `report.md`, published only after grading and audit.
