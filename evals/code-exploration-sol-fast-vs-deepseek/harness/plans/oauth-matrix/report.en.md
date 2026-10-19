> English translation of [report.md](report.md). The original is kept verbatim as an archived artifact.

# Comparison of explorers in OpenCode

Inconclusive verdict. Descriptive pilot of individual exploration.

Planned 210. Completed 0. Fast served confirmed: no.

Time covers the OpenCode invocation, tools and internal recoveries. Preparation, audit, export and grading are left out.

| Configuration | Planned | Completed | Correct | Incorrect | Errors | Absent | Median, s | Minimum, s | Maximum, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| deepseek-max | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| sonnet-low | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| sonnet-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| sonnet-high | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| opus-low | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| opus-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |

The time table includes completed incorrect answers. Paired comparisons require both to be correct on the same task and repetition.

| Case | Configuration A | Configuration B | Correct pairs | Median A/B | A faster | B faster | Ties |
|---|---|---|---:|---:|---:|---:|---:|
| route | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| route | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| route | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| route | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| route | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| route | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| route | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| config | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| config | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| config | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| config | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| config | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| retry | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| retry | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| retry | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| permission | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| permission | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| permission | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| feature | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| feature | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| feature | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | deepseek-max | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-low | 0 | n/a | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| absence | deepseek-max | opus-low | 0 | n/a | 0 | 0 | 0 |
| absence | deepseek-max | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-low | sonnet-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-low | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-low | opus-low | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-low | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-medium | sonnet-high | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-medium | opus-low | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-medium | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-high | opus-low | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-high | opus-medium | 0 | n/a | 0 | 0 | 0 |
| absence | opus-low | opus-medium | 0 | n/a | 0 | 0 | 0 |

An A/B ratio below 1 indicates a lower observed time for A. The counts describe observations and do not declare a winner.

## Limits

- Requested Fast needs confirmation from the service. Absence of metadata does not confirm service in the Fast class.
- Passive observation records selected parameters and metadata without redirecting the providers' calls.
- Repetitions of the same case are not independent tasks. The synthetic suite does not qualify the model for every repository.
- It does not measure native delegation, nor the causal effect of Fast. Model, route and effort vary together.
- The identity of the session and request does not attest which model was executed upstream.
- Remote cache may persist across repetitions. Native cache counters are in the results.
- Reported zero cost does not mean free of charge. It does not estimate actual consumption of the subscriptions.
- Isolation of discovery and permissions is not equivalent to an operating-system sandbox.
- The report does not automatically declare a winner. Failures, variability, quality and confirmation of Fast require review.
