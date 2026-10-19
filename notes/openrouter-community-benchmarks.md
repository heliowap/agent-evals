# OpenRouter community benchmark results

**Checked:** 2026-10-06. **Evidence: live unauthenticated GET requests and official documentation**, starting with the [documentation index][index]. No credentials were accessed, no model calls or evaluation runs were made. Authenticated benchmark behavior remains **UNVERIFIED**: no OpenRouter API key was available in the environment. Documented behavior below is distinct from the live checks.

## Verified live access

| Tested URL | HTTP | Observed result |
| --- | --- | --- |
| `https://openrouter.ai/api/v1/models?sort=intelligence-high-to-low&limit=3` | 200 | Three model rows, `total_count`, and `links.next`; embedded benchmark scores. |
| `https://openrouter.ai/api/v1/models?sort=coding-high-to-low&limit=3` | 200 | Three rows; coding sorting worked on the returned sample. |
| `https://openrouter.ai/api/v1/models?sort=design-arena-elo-high-to-low&limit=3` | 200 | Three rows; Design Arena sorting worked on the returned sample. |
| `https://openrouter.ai/api/v1/models?min_intelligence_index=50&sort=intelligence-high-to-low&limit=2` | 200 | Two rows; `total_count` 11, sample intelligence scores 57.6. |
| `https://openrouter.ai/api/v1/models?max_intelligence_index=50&sort=intelligence-high-to-low&limit=2` | 200 | Two rows; `total_count` 279, sample intelligence scores 49.6. |
| `https://openrouter.ai/api/v1/models?sort=intelligence-high-to-low&offset=3&limit=3` | 200 | Three rows after the first three results. |
| `https://openrouter.ai/api/v1/benchmarks` | 401 | `No cookie auth credentials found`; not anonymously accessible in this test. |
| `https://openrouter.ai/api/v1/benchmarks?source=unsupported&max_results=1` | 400 | Validation named `artificial-analysis`, `design-arena`, and `openrouter` as accepted sources. |

Valid-source benchmark requests with `max_results`, and a search request with `include_run_config=true`, also returned 401. Successful authenticated filtering, default behavior, and rate limits remain **UNVERIFIED**.

The public model rows contained `id`, `canonical_slug`, `benchmarks.artificial_analysis` (`intelligence_index`, `coding_index`, `agentic_index`), and `benchmarks.design_arena[]` (`arena`, `category`, `elo`, `win_rate`, `rank`). Missing index scores were `null`. Batch aliases repeated canonical models and scores: deduplicate using `canonical_slug`.

Examples observed in these live responses—not scores measured locally:

| Model | AA intelligence | AA coding | AA agentic |
| --- | ---: | ---: | ---: |
| `anthropic/claude-opus-5.5` | 57.6 | null | null |
| `anthropic/claude-fable-5.1` | 53.4 | 81.6 | 57.9 |
| `moonshotai/kimi-k3` | 43.6 | 76.2 | 50 |

The tested embedded benchmark objects lacked score-update timestamps, run details, and historical series. Historical retrieval remains **UNVERIFIED**; no history/date-selection parameter was present in the inspected benchmark OpenAPI contract or reference.

## Existing scores

The [benchmark reference][benchmarks] documents `GET https://openrouter.ai/api/v1/benchmarks`, combining these sources:

| Source | Documented metrics |
| --- | --- |
| `artificial-analysis` | Intelligence, Coding, and Agentic composite indices; nullable scores; input/output pricing in USD per token. |
| `design-arena` | Arena/category, head-to-head Elo, win rate (0–100%), average generation time in milliseconds, tournament placement counts, and nullable pricing. |
| `openrouter` — classic evals | `gpqa_diamond`, `tau_bench_verified_airline`: aggregate accuracy (0–1), run-accuracy standard deviation (null for a single run), average task cost in USD, total tasks across runs, and latest public-run timestamp. |
| `openrouter` — search evals | `search_browsecomp`, `search_hle`, `search_dsqa`, `search_widesearch`: headline score (0–1), tasks, average task cost/latency, search engine/surface, and latest qualifying-run timestamp. WideSearch uses item-weighted F1; the others use strict accuracy. |

Search scores publish each model's highest-scoring eligible evaluation configuration, combining same-configuration runs by task-weighted mean. They are not an unselected mean across every configuration. Scores from different sources/metrics should not be treated as one interchangeable scale. [Source][benchmarks]

The [Models guide][models] additionally documents optional `benchmarks.design_arena` on catalog models, containing arena/category, Elo, win rate, and rank. Rank is among models listed on OpenRouter, **not the full external leaderboard**; models without data omit the field.

## Documented access, identifiers, and filtering — runtime UNVERIFIED except where tested above

- **Authentication:** the benchmark docs require any valid OpenRouter API key; [authentication docs][auth] specify `Authorization: Bearer <API_KEY>`. Documented limits: 30 requests/minute/key and 500 requests/day/account. Existing/public scores therefore do not imply anonymous API access. [Source][benchmarks]
- **Identity:** benchmark items use `model_permaslug`, described as a stable OpenRouter identifier; Design Arena falls back to its upstream model ID when unmapped. The catalog separately documents request `id` and permanent `canonical_slug`; confirm actual mappings rather than joining on display names. [Sources][benchmarks] [and][models]
- **`source`:** `artificial-analysis`, `design-arena`, `openrouter`; omitted means all sources, with source-dependent item shapes.
- **`task_type`:** `coding`, `intelligence`, `agentic`, `search`; maps to Artificial Analysis indices or Design Arena categories, while `search` selects OpenRouter search results only.
- **`benchmark_type`:** any of the six eval names above. A `search_*` value selects search results only; a classic value narrows OpenRouter items but leaves other sources unchanged. Use `source=openrouter` when those other sources are unwanted.
- **Search options:** `search_engine` (string), `search_surface` (`server-tool` or `plugin`), and `include_run_config` (documented default `false`). Published configuration exposes only `max_agent_turns`, `reasoning_effort`, and `temperature`.
- **Design Arena options:** `arena=models|builders|agents` (documented default `models` for that source); `category` (string, omitted means all categories).
- **`max_results`:** integer ≥1; omitted means all matches. No model filter, date-range selector, or pagination cursor is listed for benchmarks. [Filter source][benchmarks]; also corroborated by the [official SDK docs][sdk].

## History and reuse

The documented response is an updated score snapshot/aggregate, **not a benchmark-score time series**: `meta.as_of` gives the last data update, and OpenRouter's `last_run_timestamp` gives the newest relevant run. Classic rows summarize runs; search rows summarize the selected configuration. Neither timestamps nor the documented `version=v1` provide an as-of query or raw historical run records. No historical benchmark retrieval contract was found in the inspected documentation; this is not proof that an undocumented service does not exist. [Source][benchmarks]

Historical data elsewhere is not the same thing: [daily model rankings][usage] document dated token-usage totals, date filters, and day/week/month aggregation, while [app rankings][apps] document token/request totals over date windows. These measure traffic, **not benchmark quality**. [Auto Exacto][exacto] describes current endpoint benchmark scores over a rolling 32-day window and separately daily real-traffic tool-call error rates; neither establishes a historical community-score API.

`meta` also includes source URL, citation, unique model count, and filters. The docs require attribution when republishing; mixed-source results have a null citation and require attribution by each item's `source`. Preserve these metadata with any locally collected snapshots. [Source][benchmarks]

[index]: https://openrouter.ai/docs/llms.txt
[benchmarks]: https://openrouter.ai/docs/api/api-reference/benchmarks/list-benchmarks.md
[models]: https://openrouter.ai/docs/guides/overview/models.md
[auth]: https://openrouter.ai/docs/api_reference/authentication.md
[sdk]: https://openrouter.ai/docs/client-sdks/python/sdks/benchmarks/README.md
[usage]: https://openrouter.ai/docs/api/api-reference/datasets/daily-token-totals-for-top-50-models.md
[apps]: https://openrouter.ai/docs/api/api-reference/datasets/top-apps-by-token-usage.md
[exacto]: https://openrouter.ai/docs/guides/routing/auto-exacto.md
