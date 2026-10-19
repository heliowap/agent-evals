Decision: Keep or remove the "Deterministic first" section from ~/.config/opencode/AGENTS.md.

Run 20261009T215927Z (pilot-sol-fast-high), model openai/gpt-6.1-sol-fast#high: 24 runs, 2,203,827 tokens, 8 min. Completed.

| Task | V | n | pass | tokens median | tokens min-max | time median (s) | steps median | tool calls median | notes |
|---|---|---|---|---|---|---|---|---|---|
| T1-count | A | 3 | 3/3 | 33,929 | 33,684-35,641 | 10.4 | 3 | 2 |  |
| T1-count | B | 3 | 3/3 | 42,636 | 36,100-87,919 | 10.9 | 3 | 2 |  |
| T2-rename | A | 3 | 3/3 | 91,862 | 90,947-99,541 | 48.0 | 6 | 13 |  |
| T2-rename | B | 3 | 3/3 | 75,878 | 72,969-98,478 | 34.0 | 5 | 14 |  |
| T3-rule | A | 3 | 3/3 | 90,469 | 68,460-95,241 | 46.1 | 7 | 19 | kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore'] |
| T3-rule | B | 3 | 3/3 | 80,006 | 71,591-86,942 | 55.1 | 6 | 8 | kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore']; kinds=['hook', 'gitignore'] |
| T4-control | A | 3 | 3/3 | 166,825 | 151,301-167,199 | 29.3 | 12 | 15 |  |
| T4-control | B | 3 | 3/3 | 148,956 | 122,907-154,346 | 30.3 | 11 | 14 |  |

## Winner rule applied to this data

- T1-count: B/A tokens 1.26, B/A time 1.05, pass A 100% B 100%
- T2-rename: B/A tokens 0.83, B/A time 0.71, pass A 100% B 100%
- T3-rule: B/A tokens 0.88, B/A time 1.19, pass A 100% B 100%
- T4-control: B/A tokens 0.89, B/A time 1.03, pass A 100% B 100%

Pass rate A 12/12, B 12/12; median per-task B/A token ratio 0.89.
Rule outcome: B wins (remove the section).

Infra failures: 0
Runs where session total != sum of agent messages: 0
