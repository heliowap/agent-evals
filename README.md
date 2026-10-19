# Agent evals

Small, controlled experiments on how coding agents behave under different configurations: instruction files, reasoning effort, model routes, tools and delegation. Each study is written as a short paper and ships its harness and anonymized raw data, so the numbers can be checked against the runs that produced them.

The studies were run between September and October 2026 with OpenCode, Codex CLI and Claude Code. Most are pilots: few repetitions, synthetic fixtures and mechanical scoring. Read each paper's Discussion before reusing a conclusion.

## Studies

### Agent instructions (`AGENTS.md`)

| Study | Question | Main finding |
|---|---|---|
| [agentsmd-deterministic-first](evals/agentsmd-deterministic-first/) | Does a "Deterministic first" block improve coding-agent outcomes? (216 runs) | No correctness change: 36/36 with and without it in all three configurations, with the control at ceiling. Run time rose 6–24%. |
| [agentsmd-pruning-opencode](evals/agentsmd-pruning-opencode/) | Which sentences of a global `AGENTS.md` are no-ops? (198 runs, 4 models) | Most pruned sentences changed nothing. Single source of truth did (5/12 vs 0/12). One added sentence restored code review when tests are skipped (Opus 0/10 → 10/10). |
| [agentsmd-section-ablation-opencode](evals/agentsmd-section-ablation-opencode/) | Which sections (Done, Verification, Subagents) change behavior? (510 runs, 3 models) | Subagents: delegation package 15/15 vs 0/15. Verification changes process, not results. Done had no effect until rewritten as visible markers (58/60 vs 0/60). With dated history, both the old and an extended source-hierarchy rule picked the right side of a code/doc divergence (60/60); the extension added dates to reports. |
| [subagent-language](evals/subagent-language/) | Does an English inter-agent rule save tokens on Portuguese tasks? (60 runs, Codex) | No: total tokens +2.6%, output −6.2%, time −3.5%. Not adopted. |

### Code review, exploration and implementation

| Study | Question | Main finding |
|---|---|---|
| [code-review](evals/code-review/) | Can tool-less LLM reviewers find pre-registered defects in public PRs? (412 reviews) | Quoted-rule violations are almost always found (56/56); behavioral defects rarely (17/56). At least 52 false claims in 112 round-1 answers. |
| [code-exploration-sol-fast-vs-deepseek](evals/code-exploration-sol-fast-vs-deepseek/) | Which model/effort/route works best as a read-only explorer? (330 trials) | Sonnet 5.5 medium, Opus low and Opus medium tied at 27/30; Sonnet medium fastest. Citation failures, not wrong answers, drove most misses. |
| [code-exploration-haiku-5-5](evals/code-exploration-haiku-5-5/) | How does Haiku 5.5's reasoning effort affect exploration? (150 trials) | High and xhigh 28/30; high about twice as fast. Max was slower and worse (24/30). |
| [code-implementation-opencode](evals/code-implementation-opencode/) | Can delegated implementers pass hidden acceptance tests? (342 trials) | After one under-specified contract was fixed, configurations differed on time and calls, not pass rate (215/216 corrected screening). |
| [code-implementation-opencode-haiku-effort](evals/code-implementation-opencode-haiku-effort/) | Haiku 5.5 as implementer across five efforts (interrupted, 100/180 trials) | Low to xhigh 20/20; max 6/20, spending its output budget on reasoning and writing no patch. |
| [serena-haiku-opencode](evals/serena-haiku-opencode/) | Does the Serena MCP server help Haiku 5.5? (120 trials) | No pass-rate gain; worse in high-effort exploration (7/15 vs 12/15). Serena was rarely used. |
| [small-files-context](evals/small-files-context/) | Do files under ~5k tokens reduce agent context? (24 trials) | No: peak context ratio 1.15 (95% CI 0.99–1.29). Stopped by a pre-specified rule. |

### Research and terminal tasks

| Study | Question | Main finding |
|---|---|---|
| [research-go](evals/research-go/) | DeepSeek V4.1 Flash vs GLM 5.3 Flash for source-grounded documentation research (2 × 72 cases) | No configuration met the pre-set bar (≥10/12 qualified answers). DeepSeek low did best (5/12) and fastest; GLM 0/12, mostly on length and citations. |
| [research-code-web](evals/research-code-web/) | Web search/fetch and code exploration with three flash models (156 of 648 trials) | Stopped by a search outage; no winner. DeepSeek often exhausted its tool budget on code tasks; the lowest effort was fastest in every family. |
| [terminal-bench-4-pilot](evals/terminal-bench-4-pilot/) | GLM-5.3-Flash vs SWE-2 on three Terminal-Bench 4.0 tasks | Neither model passed a task (0/3 each); near misses on individual tests. |

### Notes

- [OpenRouter community benchmark results](notes/openrouter-community-benchmarks.md): what OpenRouter's benchmark API exposes, checked live on 2026-10-06. Not an eval.

## Layout and conventions

Each study has `README.md` (the paper), `harness/` and `data/`. See [docs/conventions.md](docs/conventions.md) for the paper structure, what is excluded and how data was anonymized. [tools/anonymize.py](tools/anonymize.py) copied every published file; [tools/scan.py](tools/scan.py) checks the repository for leftover identifiers and secrets.

Model routes such as `cli_proxy/...` are provider IDs of a local OpenAI-compatible proxy; each paper says how the answering model was verified.

## License

Code (scripts, harnesses, `tools/`) is under the [MIT License](LICENSE). Papers, documentation and data are under [CC BY 4.0](LICENSE-DATA). Third-party material quoted or included in the data, such as Terminal-Bench task instructions, upstream source files edited by agents and model outputs about public repositories, stays under its original license; each paper cites its source.
