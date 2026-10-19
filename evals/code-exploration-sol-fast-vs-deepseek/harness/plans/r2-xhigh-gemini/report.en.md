> English translation of [report.md](report.md). The original is kept verbatim as an archived artifact.

# Comparison of explorers in OpenCode

Inconclusive verdict. Descriptive pilot of individual exploration.

Planned 120. Completed 0. Fast served confirmed: no.

Time covers the OpenCode invocation, tools and internal recoveries. Preparation, audit, export and grading are left out.

| Configuration | Planned | Completed | Correct | Incorrect | Errors | Absent | Median, s | Minimum, s | Maximum, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sonnet-xhigh | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| sol-fast-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| gemini-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |
| gemini-high | 30 | 0 | 0 | 0 | 0 | 30 | n/a | n/a | n/a |

The time table includes completed incorrect answers. Paired comparisons require both to be correct on the same task and repetition.

| Case | Configuration A | Configuration B | Correct pairs | Median A/B | A faster | B faster | Ties |
|---|---|---|---:|---:|---:|---:|---:|
| route | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| route | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| route | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| route | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| config | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| config | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| config | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| retry | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| retry | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| permission | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| permission | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| feature | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| feature | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-xhigh | sol-fast-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-xhigh | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sonnet-xhigh | gemini-high | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-medium | gemini-medium | 0 | n/a | 0 | 0 | 0 |
| absence | sol-fast-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |
| absence | gemini-medium | gemini-high | 0 | n/a | 0 | 0 | 0 |

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
