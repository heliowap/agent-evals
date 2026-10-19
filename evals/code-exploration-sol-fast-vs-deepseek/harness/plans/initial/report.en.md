> English translation of [report.md](report.md). The original is kept verbatim as an archived artifact.

# Sol low with Fast versus DeepSeek max

Verdict: inconclusive. Descriptive pilot of individual exploration in OpenCode.

Planned: 60. Completed: 0. Fast served confirmed: no.

Time covers the OpenCode invocation, tools and internal recoveries. Preparation, auditing, export and grading are left out.

| Configuration | Planned | Completed | Correct | Median of completed, s | Minimum, s | Maximum, s |
|---|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 30 | 0 | 0 | n/a | n/a | n/a |
| deepseek-max | 30 | 0 | 0 | n/a | n/a | n/a |

The time table includes completed incorrect responses. The paired comparisons below require both to be correct.

| Case | Sol correct | DeepSeek correct | Pairs with both correct | Median Sol/DeepSeek |
|---|---:|---:|---:|---:|
| route | 0 | 0 | 0 | n/a |
| config | 0 | 0 | 0 | n/a |
| retry | 0 | 0 | 0 | n/a |
| permission | 0 | 0 | 0 | n/a |
| feature | 0 | 0 | 0 | n/a |
| absence | 0 | 0 | 0 | n/a |

A ratio below 1 means a shorter observed time for Sol in that case. It does not amount to a general conclusion.

## Limits

- If Fast served is unknown, the result compares Sol with Fast requested and routed, without proving service in the Fast class.
- The observer proxy records only selected parameters and metadata. Both models go through it.
- Repetitions of the same case are not independent tasks. The synthetic suite does not qualify the model for every repository.
- It does not measure native delegation, nor the causal effect of Fast. Model, route and effort vary together.
- Session and request identity does not attest which model the proxy executed upstream.
- Remote cache may persist across repetitions. Native cache counters are in the results.
- Reported zero cost does not mean free of charge. It does not estimate real subscription consumption.
- Isolation of discovery and permissions is not equivalent to an operating-system sandbox.
- The report does not automatically declare a winner. Failures, variability, quality and Fast confirmation require review.
