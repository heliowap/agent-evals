> English translation of [revisao-de-codigo-rodada-2-comparacao.md](revisao-de-codigo-rodada-2-comparacao.md). The original is kept verbatim as an archived artifact.

# Code-review benchmark — round 2 (exploratory comparison)

Reading version published at the root of `evals/`. [Original preserved for audit](revisao-de-codigo/round-2/revision-2/comparison.md). The links and commands of this version follow the organization by topic.


**300/300 valid reviews**: 25 configurations × 3 cases × 2 axes × 2 independent runs. A valid session does not make all targets comparable: the Axios / Standards case omitted from the prompt the condition needed to demonstrate the test failure. The numbers below preserve the blind adjudication, but **do not support an overall six-target score**. See the [methodological review](revisao-de-codigo-rodada-2-metodologia.md).

## Coverage by case and axis

| Case | Axis | Target found (raw) | Claims refuted (raw) | Verified extra mentions | Unverifiable |
| --- | --- | ---: | ---: | ---: | ---: |
| axios-10852 | spec | 42/50 | 0 | 47 | 7 |
| axios-10852 | standards | 10/50 | 1 | 53 | 0 |
| requests-6991 | spec | 47/50 | 1 | 23 | 11 |
| requests-6991 | standards | 47/50 | 4 | 34 | 1 |
| rust-161834 | spec | 39/50 | 4 | 62 | 21 |
| rust-161834 | standards | 48/50 | 0 | 0 | 10 |

**Attention:** Axios / Standards (10/50) is not demonstrable from the material received alone; Requests / Spec (47/50) concerns a direct call of the helper, not a demonstrated failure of a normal request.

## Configurations (raw counts; no overall score or ranking)

| Configuration | Standards / 6* | Spec / 6† | Refuted‡ | Extras§ | Inconclusive | Median s [IQR] | Valid cost reported US$ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-6-luna#high` | 4/6 | 3/6 | 0 | 5 | 0 | 20,7 [16,9–24,2] | 0,00000 |
| `openai/gpt-6-luna-fast#high` | 4/6 | 5/6 | 0 | 5 | 0 | 13,4 [10,6–17,0] | 0,00000 |
| `openai/gpt-6-luna#xhigh` | 4/6 | 4/6 | 1 | 6 | 0 | 40,9 [32,8–72,0] | 0,00000 |
| `openai/gpt-6-luna-fast#xhigh` | 4/6 | 4/6 | 0 | 6 | 0 | 24,0 [19,1–34,1] | 0,00000 |
| `openai/gpt-6-luna#max` | 5/6 | 5/6 | 0 | 5 | 0 | 49,8 [36,9–62,7] | 0,00000 |
| `openai/gpt-6-luna-fast#max` | 4/6 | 5/6 | 0 | 4 | 0 | 31,8 [27,3–43,1] | 0,00000 |
| `openai/gpt-6-sol#low` | 5/6 | 6/6 | 0 | 6 | 0 | 9,7 [7,5–9,9] | 0,00000 |
| `openai/gpt-6-sol#medium` | 4/6 | 5/6 | 1 | 5 | 0 | 19,7 [16,8–24,7] | 0,00000 |
| `openai/gpt-6-sol#high` | 4/6 | 6/6 | 0 | 6 | 0 | 19,0 [16,3–26,0] | 0,00000 |
| `openai/gpt-6-sol#xhigh` | 5/6 | 6/6 | 0 | 9 | 0 | 27,4 [21,7–32,1] | 0,00000 |
| `openai/gpt-6-sol#max` | 4/6 | 6/6 | 0 | 7 | 0 | 46,3 [34,8–53,7] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#low` | 4/6 | 6/6 | 0 | 7 | 3 | 5,8 [4,9–7,6] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#medium` | 4/6 | 6/6 | 0 | 5 | 3 | 12,9 [10,3–17,2] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#high` | 6/6 | 4/6 | 0 | 2 | 3 | 38,4 [18,6–43,7] | 0,00000 |
| `cli_proxy/devin/swe-2#medium` | 5/6 | 5/6 | 1 | 16 | 2 | 21,9 [19,5–26,9] | 0,00000 |
| `cli_proxy/devin/swe-2#high` | 5/6 | 5/6 | 1 | 12 | 5 | 47,2 [38,7–56,3] | 0,00000 |
| `cli_proxy/devin/swe-2#max` | 6/6 | 6/6 | 1 | 16 | 3 | 83,1 [68,6–90,3] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#low` | 4/6 | 6/6 | 0 | 17 | 6 | 16,4 [14,7–17,8] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#medium` | 4/6 | 6/6 | 0 | 15 | 3 | 19,2 [17,9–19,5] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#high` | 4/6 | 6/6 | 0 | 16 | 4 | 22,9 [21,4–23,4] | 0,00000 |
| `openrouter/z-ai/glm-5.3-flash#high` | 4/6 | 5/6 | 2 | 11 | 5 | 16,7 [12,8–20,3] | 0,01786 |
| `openrouter/z-ai/glm-5.3-flash#max` | 4/6 | 6/6 | 1 | 16 | 6 | 50,6 [37,7–62,3] | 0,05524 |
| `openrouter/deepseek/deepseek-v4.1-flash#high` | 4/6 | 6/6 | 1 | 10 | 2 | 37,4 [17,2–68,2] | 0,07152 |
| `openrouter/deepseek/deepseek-v4.1-flash#max` | 4/6 | 6/6 | 1 | 12 | 5 | 65,0 [36,3–114,5] | 0,21108 |
| `openrouter/xiaomi/mimo-v2.6-flash#none` | 0/6 | 0/6 | 0 | 0 | 0 | 6,7 [4,0–8,1] | 0,01195 |

- `*` One of the three Standards targets, Axios, is not demonstrable from the prompt: the per-model counts are historical, not a comparable score.
- `†` Requests / Spec records the conditional behavior of `build_digest_header()`, with no proof of regression in the normal flow.
- `‡` The raw total includes the claim `b0026`, whose refutation depends on code omitted from the prompt; do not treat it as a confirmed false positive.
- `§` The extra mentions include targets of the other axis and factual observations; they are not equivalent to novel defects.

## Limits and audit

- **0 missing cells**; the 25 configurations have two results per case/axis, with no route swap.
- The prompt asked for fewer than 400 words; by whitespace count, **30/300 responses have 400 or more** (29 exceed 400; maximum 470). 24/36 CPA Opus responses exceed this limit. The run did not exclude them; the unequal length also affects the opportunity to find extras.
- **304 attempts** archived, including 4 excluded. A MiMo attempt without a final response had its cost reconciled, but did not become a valid review.
- **US$ 0,37721 reported by OpenRouter** across all attempts on that route, including excluded ones; the value is not the account total nor a billing limit imposed by the provider.
- US$ 0 reported in the OAuth and `cli_proxy` sessions **does not demonstrate a real cost of zero**. The Fast route is the variant requested; there is no independent proof of service acceleration.
- A target requires location, mechanism and consequence on the correct axis. Extras were classified separately; unverifiable hypotheses were not counted as false, with the exception of the contested classification of `b0026`.
- One blind pass per response, with no second independent adjudicator. See the [answer key](revisao-de-codigo/round-2/revision-2/grading-rubric.md), [seal prior to identification](revisao-de-codigo/round-2/revision-2/blind-seal.json), [decisions](revisao-de-codigo/round-2/revision-2/adjudication.json) and [map](revisao-de-codigo/round-2/revision-2/blind-map.json). The [300 sanitized exports](revisao-de-codigo/round-2/revision-2/session-evidence.json) allow re-verifying prompt, model/variant, agent, completion, absence of tool parts, response, tokens and reported cost; the reasoning and the original CLI event stream were not archived.
- There are three PRs and two repetitions per cell; do not compare numerically with the earlier Click round. This sample does not measure the causal effect of the new prompts nor the full execution of the skill.
