Decision: Keep or remove the "Deterministic first" section from ~/.config/opencode/AGENTS.md.

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst/results/20261009T214013Z-pilot/report.md). Os links e comandos desta versão acompanham a organização por tema.


Run 20261009T214013Z (pilot): 24 runs, 2,273,514 tokens, 4 min. Completed.

| Task | V | n | pass | tokens median | tokens min-max | time median (s) | steps median | tool calls median | notes |
|---|---|---|---|---|---|---|---|---|---|
| T1-count | A | 3 | 3/3 | 75,499 | 74,929-75,505 | 13.8 | 4 | 3 |  |
| T1-count | B | 3 | 3/3 | 92,915 | 54,475-161,407 | 13.0 | 5 | 4 |  |
| T2-rename | A | 3 | 3/3 | 105,151 | 82,931-105,464 | 12.0 | 5 | 5 |  |
| T2-rename | B | 3 | 3/3 | 81,529 | 59,829-106,092 | 12.7 | 4 | 4 |  |
| T3-rule | A | 3 | 3/3 | 99,448 | 97,348-119,308 | 26.6 | 5 | 6 | kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore'] |
| T3-rule | B | 3 | 3/3 | 137,198 | 117,693-164,388 | 31.4 | 7 | 8 | kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore'] |
| T4-control | A | 3 | 3/3 | 74,535 | 74,524-74,563 | 12.3 | 4 | 6 |  |
| T4-control | B | 3 | 3/3 | 73,217 | 73,214-92,352 | 15.9 | 4 | 6 |  |

## Winner rule applied to this data

- T1-count: B/A tokens 1.23, B/A time 0.94, pass A 100% B 100%
- T2-rename: B/A tokens 0.78, B/A time 1.06, pass A 100% B 100%
- T3-rule: B/A tokens 1.38, B/A time 1.18, pass A 100% B 100%
- T4-control: B/A tokens 0.98, B/A time 1.29, pass A 100% B 100%

Pass rate A 12/12, B 12/12; median per-task B/A token ratio 1.11.
Rule outcome: keep A.

Infra failures: 0
Runs where session total != sum of agent messages: 0
