Decision: Keep or remove the "Deterministic first" section from ~/.config/opencode/AGENTS.md.

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst/results/20261009T213951Z-smoke2/report.md). Os links e comandos desta versão acompanham a organização por tema.


Run 20261009T213951Z (smoke2): 2 runs, 147,695 tokens, 0 min. Completed.

| Task | V | n | pass | tokens median | tokens min-max | time median (s) | steps median | tool calls median | notes |
|---|---|---|---|---|---|---|---|---|---|
| T4-control | A | 1 | 1/1 | 74,529 | 74,529-74,529 | 10.6 | 4 | 6 |  |
| T4-control | B | 1 | 1/1 | 73,166 | 73,166-73,166 | 10.0 | 4 | 6 |  |

## Winner rule applied to this data

- T4-control: B/A tokens 0.98, B/A time 0.94, pass A 100% B 100%

Pass rate A 1/1, B 1/1; median per-task B/A token ratio 0.98.
Rule outcome: keep A.

Infra failures: 0
Runs where session total != sum of agent messages: 0
