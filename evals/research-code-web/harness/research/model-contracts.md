# Model and harness contracts — Q3

Research snapshot: 2026-10-07. This is a plan-only contract investigation, not an availability or inference test. Scope prohibits candidate calls and configuration changes and requires final approval before execution. [S1]

## Answer

- The provisional matrix contains nine configurations: Gemini Flash low/medium/high; DeepSeek Flash low/high/max; GLM Flash low/high/max. The native vendor contracts support those exact sets. [S2, G1, D1, Z1]
- Gemini 3.8 Flash **does not support minimal**; do not add a tenth Gemini configuration. DeepSeek has a native thinking-off mode, but that mode is not an advertised Go variant and its Go route is UNVERIFIED. [G1, D1, S2]
- Gemini's current OpenCode provider uses an OpenAI-compatible local proxy; its source translates literal `reasoning_effort` into Gemini `generationConfig.thinkingConfig.thinkingLevel`. Go publicly lists both selected IDs on Chat Completions. [C1, C2, O1, O2]
- Source-level request shaping is verified; installed proxy equivalence, actual backend identity, effort honoring, account entitlement and remaining quota are UNVERIFIED. No cross-family token-budget equivalence is established. [C3, C4, U1–U5]

## Evidence

Each numbered source below was read or fetched during this investigation. `CPA` means `~/VSCode/Lab/CLIProxyAPI`; `OC` means `~/VSCode/Lab/opencode`. Local source citations describe the checkout, not a proven running binary.

### Exact matrix and routes

| OpenCode configuration reference | Intended wire model ID | Advertised effort | Native effort | Public/configured route | Evidence |
| --- | --- | --- | --- | --- | --- |
| `cli_proxy_google/gemini-3.8-flash#low` | `gemini-3.8-flash` | low | low | `http://127.0.0.1:8317/v1/chat/completions` | S2, C1, C2, G1 |
| `cli_proxy_google/gemini-3.8-flash#medium` | `gemini-3.8-flash` | medium | medium | same proxy route | S2, C1, C2, G1 |
| `cli_proxy_google/gemini-3.8-flash#high` | `gemini-3.8-flash` | high | high | same proxy route | S2, C1, C2, G1 |
| `opencode-go/deepseek-v4.1-flash#low` | `deepseek-v4.1-flash` | low | low | `https://opencode.ai/zen/go/v1/chat/completions` | S2, O1, O2, D1 |
| `opencode-go/deepseek-v4.1-flash#high` | `deepseek-v4.1-flash` | high | high | same Go route | S2, O1, O2, D1 |
| `opencode-go/deepseek-v4.1-flash#max` | `deepseek-v4.1-flash` | max | max | same Go route | S2, O1, O2, D1 |
| `opencode-go/glm-5.3-flash#low` | `glm-5.3-flash` | low | low | `https://opencode.ai/zen/go/v1/chat/completions` | S2, O1, O2, Z1 |
| `opencode-go/glm-5.3-flash#high` | `glm-5.3-flash` | high | high | same Go route | S2, O1, O2, Z1 |
| `opencode-go/glm-5.3-flash#max` | `glm-5.3-flash` | max | max | same Go route | S2, O1, O2, Z1 |

- `python3` enumerating `canonical_candidates[*].advertised_variants` in `catalog-observation.json` → `total_configurations 9`; these are model×effort configurations, not nine HTTP requests or nine completed research invocations. [S2; command run in this session]
- `catalog-observation.json:9–10` → exclude `cli_proxy_google/cpa-ag-gemini-3.8-flash-high` as the parent-declared duplicate; **ASSUMPTION:** “Gemini 3.8” means the previously studied Flash SKU. Confirm at final approval; if the user meant Pro, ask for the exact SKU and route rather than substituting or adding it. Actual duplicate backend resolution remains U2. [S2]
- Google model-specific page and current thinking table → Gemini 3.8 Flash native levels are exactly low/medium/high, default medium; minimal is explicitly unsupported and returns an error. A generic/deprecated Gemini 3 Flash table is not evidence for a fourth 3.8 level. [G1, G2, G3]
- DeepSeek thinking guide → native enabled-thinking efforts are low/high/max, default high; Chat Completions can disable thinking with `thinking.type: disabled`. Responses uses `reasoning.effort: none` for disabled thinking; neither implies a Go Chat Completions `reasoning_effort: none` contract. [D1]
- DeepSeek thinking guide → minimal maps to low; medium and xhigh map to high; ultra maps to max. These compatibility synonyms are not additional independent effort configurations. [D1]
- Z.AI Flash-specific page and ChatCompletionVisionRequest schema → GLM-5.3-Flash accepts low/high/max `reasoning_effort`, default max, and forced thinking; `thinking.type` only supports enabled for this model. Do not import none/minimal/medium/xhigh behavior from GLM-5.2 or the broader schema enum. [Z1, Z2]
- Go public models response → `deepseek-v4.1-flash` and `glm-5.3-flash` are present, with public list metadata only; the fetched response does not expose efforts or account-specific access. [O2]
- DeepSeek release announcement → direct DeepSeek API uses `deepseek-flash` for V4.1 Flash; Go's selected public ID is `deepseek-v4.1-flash`. Do not replace one route's ID with the other's or assume Go aliases resolve identically. [D2, O1, O2]

### Verified fields and translation boundaries

- `~/.config/opencode/opencode.jsonc:1493–1533` → target provider has `canonical: google`, package `@opencode/ai/providers/openai-compatible`, baseURL `http://127.0.0.1:8317/v1`, and low/medium/high variant `settings.reasoningEffort` literals. A script parsed JSONC and printed only allowlisted public route/model fields; credentials, environment values and auth stores were not inspected. [C1]
- `OC/packages/ai/src/protocols/openai-chat.ts:782–797` → `options.reasoningEffort` lowers to top-level `reasoning_effort`; `fromRequest:825–849` supplies Chat Completions model/messages/tools and streaming request fields. This is source-level behavior, not a wire capture of the installed application. [C5]
- `CPA/internal/api/server_routes.go:62–71` → proxy registers authenticated `/v1/chat/completions`; `gemini_openai_request.go:37–55` passes supplied `generationConfig` through and maps non-auto literal `reasoning_effort` to `generationConfig.thinkingConfig.thinkingLevel`; auto maps to `thinkingBudget: -1`. [C2]
- `CPA/internal/thinking/apply.go:311–398` → parsed model suffix intent can override body intent, then capability validation/normalization and provider application run. `extractOpenAIConfig:888–898` reads `reasoning_effort`, treating none separately. Do not describe the entire proxy as unconditional pass-through. [C3]
- `CPA/internal/thinking/provider/gemini/apply.go:115–150` → level application removes competing budget/snake-case fields and writes `generationConfig.thinkingConfig.thinkingLevel`; Antigravity's analogous code writes `request.generationConfig.thinkingConfig.thinkingLevel`. These are different output envelopes. [C6]
- `CPA/internal/runtime/executor/gemini_executor.go:280–307` → streaming execution translates, applies thinking, caps max output, sanitizes signatures, then applies payload rules before forming the upstream `streamGenerateContent` request. Active payload rules could alter the final field; their current configuration was not inspected. [C4]
- Google Generate Content thinking guide → native REST thinking field is `generationConfig.thinkingConfig.thinkingLevel`; Interactions uses `generation_config.thinking_level`. Neither is the top-level OpenAI field. Preserve endpoint-specific casing and nesting in adapters. [G2, G4]
- DeepSeek and Z.AI native API docs → both current selected families define top-level `reasoning_effort` with low/high/max. This confirms native fields, **not** every Go upstream's pass-through or honoring. [D1, Z1, Z2; U3]
- OpenCode Go guide → a custom client should identify itself with its own user agent and maintain a stable `x-opencode-session` per conversation for routing/caching; selected model endpoints are Chat Completions. Do not impersonate OpenCode's user agent. [O1]
- Google Generate Content guide → function-call thought signatures must be returned; retain complete original parts and do not merge signed and unsigned parts. [G4]
- DeepSeek thinking guide → when `tools` is present, fully replay historical assistant `reasoning_content`, even for turns without a tool call; omission can cause HTTP 400. [D1]
- Z.AI thinking guide → preserve reasoning with tool results; preserved thinking requires full, unmodified, correctly ordered historical `reasoning_content`. Its native Coding Plan enables preserved thinking by default, while its standard API does not; Go's upstream/default is UNVERIFIED. [Z3; U3]

### Harness recommendations — judgments, not observed candidate results

1. **Minimal shared logical scaffold; route-aware protocol adapters.** Share prompts, logical tool names/JSON schemas, caps and canonical result text, but preserve each route's native history fields, tool-call identifiers, signatures and SSE framing. The existing Gemini route is a Chat shim with source-verified Gemini translation, not a configured native Google runtime. A proposed native Gemini Generate Content route through the same proxy would be a separately approved harness/route choice, not a silent configuration substitution. Rationale: native protocol differences and existing configuration above. [C1–C6, G4, D1, Z3]
2. **Do not send optional `thinking` in the common Go request.** Send the selected literal top-level `reasoning_effort`, keep `thinking`, `clear_thinking` and provider-specific stream knobs out unless their exact Go route contract is separately established and approved. Native forced/default thinking already exists for the selected vendor contracts, but Go honoring/defaults remain U3. The assignment reports older GLM failures after adding `thinking`; this investigation did not read those run records or reproduce them, so that historical failure claim is UNVERIFIED. [D1, Z1–Z3; U3, U6]
3. **Offline contract checks before approved inference.** Proposed tests: each matrix row produces the intended model/effort and endpoint; absent optional thinking fields stay absent; no suffix silently overrides effort; full reasoning/signature replay survives tool results; fragmented SSE arguments reconstruct correctly; usage and finish/truncation states remain distinguishable. These are future field/fixture unit tests, not live smoke tests; implementation requires approval. Rationale: source translation/normalization and native continuity obligations. [C2–C6, G4, D1, Z3, S1]
4. **First counted real case is the compatibility gate.** After final approval, the first scheduled real task for each configuration exercises tool call → result → continuation → sourced final answer. Count its latency, errors and all requests; no warmup/probe/smoke inference precedes it. If it reveals a contract mismatch, record failure, stop that configuration and seek approval for a repair/restart; do not silently add calls or discard the case. This is a proposed gate, not proof of current compatibility. [S1; rationale G4, D1, Z3]
5. **Equal tool capabilities, not uniform optional wire fields.** For the web suite, propose the same external SERP service and fetch normalizer for every candidate; no Gemini-only Google grounding or GLM-native search. For the codebase suite, propose the same read-only glob/grep/read implementations, repository snapshot and result caps. For identical tool arguments, return byte-identical canonical text and truncation markers; models may choose different arguments and thus see different results. Native function-call envelopes may differ without changing logical tool capability. Search-service choice and exact caps belong to the parent tool/task plan. [S1; native tool distinction G1, Z2]
6. **Do not equate effort labels across families.** Analyze each family×effort as its own configuration and compare measured performance, not claimed equal reasoning budgets. Proxy numeric conversions are implementation mappings, not vendor token guarantees; the documented Gemini controls are dynamic levels, and DeepSeek compatibility mapping collapses multiple labels. [G2, G4, D1, C7]
7. **Go usage-policy approval checkpoint.** Read-only code research fits the intended coding-agent context more directly than arbitrary web research. The Go guide says clients should send typical coding-agent traffic; general web-evaluation permission is not explicitly established by that wording. The parent should resolve workload suitability before approval rather than assume subscription access authorizes any benchmark. [O1; U7]

### Measurement contract — proposed capture, not extra execution

- Google Generate Content docs → native `usageMetadata.thoughtsTokenCount` and `candidatesTokenCount` distinguish reasoning and answer tokens; low output limits can truncate thinking before an answer. Record effective requested caps and native finish status rather than assume equal visible-answer caps. [G4]
- `CPA/.../gemini_openai_response.go:90–129` → proxy can return `modelVersion` as Chat `model`, aggregates candidate+thought tokens into `completion_tokens`, adds positive thought count as `completion_tokens_details.reasoning_tokens`, and maps cache counts. Missing reasoning metadata is not automatically zero. Whether the actual selected upstream returns those fields is U2/U4. [C8]
- DeepSeek cache guide → implicit cache is enabled natively and best-effort; native usage fields are `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens`. [D3]
- Z.AI cache/API docs → native cached-token field is `usage.prompt_tokens_details.cached_tokens`; cache is implicit. Native availability does not prove Go forwards this metadata. [Z2, Z4; U4]
- OpenCode V2 provider guide → its transport can retry timed-out requests up to three times. A whole research task, a logical model step, a client HTTP attempt, and an upstream attempt are distinct counting units. Avoid wrapping a new harness around an opaque retrying orchestration layer without exposing its attempts. [O3; OC/AGENTS.md:185–189]
- **Proposed logging:** per whole task and per HTTP attempt, capture sanitized request body/hash, logical schema hash, route/model/effort intent, stable per-task session ID, start/first event/first visible answer/end timing, tool durations/counts, response model/version if supplied, finish reason, usage/cached/reasoning/visible-output tokens, HTTP status and retry/error class. Never capture credentials/auth headers or account data. Keep available native state for replay separately from scored answer text. Missing metadata stays unknown. Rationale: translation and continuity sources above. [C2–C8, G4, D1, Z3–Z4]
- **Proposed cache controls:** separately identify first task in a fresh conversation and subsequent scheduled work; use observed cache-token metadata for hit/miss strata. A fresh session is not proof of an upstream cold cache. Do not add cache-priming calls, disable a provider's native caching only on one route, or infer cache hits from latency alone. Rationale: implicit/best-effort caching and Go affinity contract. [O1, D3, Z4]
- **Proposed attempt accounting:** set explicit independent-client retry/timeout policy only after approval; count every client send and report hidden upstream retries/routing as unknown unless the approved transport supplies non-secret metadata. One completed research invocation can require multiple generation requests and tool executions. Proxy/source retry behavior or a public model list cannot certify account quota headroom. [O3, S1; U1, U4]

## Unknowns and next look

| ID | UNVERIFIED claim | What was tried / next authorized place to look |
| --- | --- | --- |
| U1 | Entitlement, remaining quota, provider availability and live tool compatibility for this account | Only public Go metadata and parent catalog were read. Do not access account data or credentials here. Compatibility becomes observable in the first **approved, counted real case**, not an extra probe. |
| U2 | Canonical Gemini proxy ID and duplicate alias resolve to the same backend/version; installed process matches checkout | Config selects the canonical route; source lists Gemini and Antigravity variants. No model calls, live logs, credential stores or proxy runtime configuration were accessed. After approval, retain response model/version metadata from real cases; metadata remains provider-reported, not independent identity attestation. |
| U3 | Each Go/proxy effort is forwarded unchanged and honored; Go upstream thinking/history defaults | Native vendor docs and local lowering/CPA translator were read; the local OpenCode tree has no matching Go server implementation in the searched services. The public Go model list has no effort contract. Seek a first-party Go route/schema statement or response metadata on approved cases; acceptance alone does not prove effort honoring. |
| U4 | Full native usage, cache and upstream retry metadata survives both routes | Native usage docs and Gemini response translation read; no new candidate response exists. Capture whatever appears in approved real cases; explicitly retain unknowns for hidden retries and absent usage. |
| U5 | Equal reasoning budgets across families or a reliable Gemini 3.8 off/none mode | No equal-budget contract found. Gemini 3.8 explicitly rejects minimal; current model table lists only low/medium/high. Do not extrapolate 2.5 disable controls or generic older Flash guidance. |
| U6 | Older Go 72-call study's accepted literal efforts/omitted thinking and particular thinking-induced failures | The parent assignment describes those observations; no old inference records were opened in this investigation. Parent can cite its own sanitized request-wire records; backend honoring must still remain unknown. |
| U7 | General web-research eval traffic complies with Go's intended usage | Official Go guide asks for typical coding-agent requests. Seek provider clarification/public acceptable-use guidance for the proposed workload before execution approval; do not imitate another client. |
| U8 | DeepSeek native disabled-thinking mode is usable through this Go Chat route | Native DeepSeek toggle documented; not an advertised parent variant; no Go-specific disabled-thinking contract established. Ask whether “all efforts” means all enabled effort levels (nine configurations) or also native thinking modes. Add a disabled mode only after route contract and final approval, never as a guessed none variant. |

## Source register

- **S1:** `~/VSCode/Lab/evals/research-eval-design-20261007T184125Z/scope.json:2–13` → two suites, three provisional routes, zero authorized candidate calls, no configuration changes, final approval requirement.
- **S2:** `~/VSCode/Lab/evals/research-eval-design-20261007T184125Z/catalog-observation.json:3–12` → parent-observed canonical variants, duplicate exclusion and Flash assumption; not upstream honoring proof.
- **G1:** https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash → exact SKU, supported thinking levels and explicit minimal error.
- **G2:** https://ai.google.dev/gemini-api/docs/thinking → current native thinking/default table and Interactions contract; page reports last updated 2026-09-25.
- **G3:** https://ai.google.dev/gemini-api/docs/gemini-3 → deprecated generic guide; not authoritative for 3.8 defaults or minimal.
- **G4:** https://ai.google.dev/gemini-api/docs/generate-content/thinking.md.txt → endpoint-specific REST fields, signatures, summaries, thought/output counts and output-cap behavior.
- **D1:** https://api-docs.deepseek.com/guides/thinking_mode → native effort/toggle/default/mapping and reasoning replay requirements.
- **D2:** https://api-docs.deepseek.com/news/news260910 → V4.1 Flash release and direct API ID/alias policy.
- **D3:** https://api-docs.deepseek.com/guides/kv_cache → implicit cache behavior and native hit/miss fields.
- **Z1:** https://docs.z.ai/guides/vlm/glm-5.3-flash.md → exact Flash SKU, forced thinking, model code and parameter guidance.
- **Z2:** https://docs.z.ai/api-reference/llm/chat-completion.md → native request/response OpenAPI, exact Flash effort enum/default and cache/finish fields.
- **Z3:** https://docs.z.ai/guides/capabilities/thinking-mode.md → forced/default, interleaved/preserved reasoning and endpoint-dependent preserved-thinking defaults.
- **Z4:** https://docs.z.ai/guides/capabilities/cache.md → implicit native cache and cached-token response field.
- **O1:** https://opencode.ai/v2/docs/console/go/ → Go endpoints/IDs, custom-client own UA/session header and intended traffic.
- **O2:** https://opencode.ai/zen/go/v1/models → public unauthenticated GET returned both selected IDs; no inference or account data.
- **O3:** https://opencode.ai/v2/docs/providers → V2 provider/model configuration, modelID semantics and documented timeout/retry behavior.
- **C1:** `~/.config/opencode/opencode.jsonc:1493–1533,1538–1576` → allowlisted config extraction verified canonical Google package/baseURL and exact variant settings; no credential fields emitted.
- **C2:** `CPA/internal/api/server_routes.go:62–71`; `CPA/internal/translator/gemini/openai/chat-completions/gemini_openai_request.go:29–55,68–73` → proxy endpoint and Chat→Gemini request translation.
- **C3:** `CPA/internal/thinking/apply.go:311–398,888–898` → suffix priority, capability normalization and source effort parsing.
- **C4:** `CPA/internal/runtime/executor/gemini_executor.go:280–307` → streaming translation/thinking/caps/signatures/payload-rule order.
- **C5:** `OC/packages/ai/src/protocols/openai-chat.ts:782–797,825–849` → generic Chat request lowering of literal reasoning effort.
- **C6:** `CPA/internal/thinking/provider/gemini/apply.go:115–150`; `CPA/internal/thinking/provider/antigravity/apply.go:96–126` → provider-specific native thinking envelope construction.
- **C7:** `CPA/internal/thinking/convert.go:9–44` → proxy implementation level-to-budget mapping, not equal vendor compute.
- **C8:** `CPA/internal/translator/gemini/openai/chat-completions/gemini_openai_response.go:90–129` → response model/version and native usage translation.

Snapshot verification commands: `git rev-parse HEAD && git status --porcelain -- internal/thinking internal/translator/gemini internal/registry/models/models.json` in CPA returned `221c0f0391d3b7968e0db18123b55b89388829b3` and no status lines for those paths; the analogous command for `packages/ai/src/protocols/openai-chat.ts packages/core/src/provider` in OC returned `077444b94b9728a6fc42732efd6ff68357a734b0` and no status lines for those paths. These commands do not identify the running binaries. CPA registry source at `internal/registry/models/models.json:978–997,4147–4166` also lists low/medium/high for Gemini 3.8 Flash and its Antigravity high-named variant.

Documentation discovery failures retained: guessed `https://opencode.ai/v2/console/go` and `/v2/docs/go` returned 404; the fetched official V2 index `https://opencode.ai/v2/llms.txt` identified the successful O1 path. No inference endpoint was called to investigate those errors.
