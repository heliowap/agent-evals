Decision: Keep or remove the "Deterministic first" section from ~/.config/opencode/AGENTS.md.

Run 20261009T213750Z (smoke): 2 runs, 380,628 tokens, 1 min. Completed.

| Task | V | n | pass | tokens median | tokens min-max | time median (s) | steps median | tool calls median | notes |
|---|---|---|---|---|---|---|---|---|---|
| T4-control | A | 1 | 1/1 | 277,990 | 277,990-277,990 | 72.5 | 11 | 11 |  |
| T4-control | B | 1 | 0/1 | 102,638 | 102,638-102,638 | 42.5 | 5 | 4 |  |

## Winner rule applied to this data

- T4-control: B/A tokens 0.37, B/A time 0.59, pass A 100% B 0%

Pass rate A 1/1, B 0/1; median per-task B/A token ratio 0.37.
Rule outcome: keep A.

Infra failures: 0
Runs where session total != sum of agent messages: 0
