# Available tools and search-provider control

## Verified observations

The OpenCode V2 tools reference documents `websearch(query)` and `webfetch(url, format, timeout)`, plus read-only `glob`, `grep` and `read`. This supports two genuinely distinct tool sets rather than calling documentation URL lookup a search-engine evaluation. Source fetched in this session: <https://opencode.ai/v2/docs/tools>.

The search guide lists Exa, Firecrawl, Parallel, Tavily and TinyFish. Search-provider selection is separate from the model provider. With the `random` setting, HTTP 429 can cause a search retry using a different provider; remembered selection and cooldown state can also change after moving a session or restarting a server. Source fetched in this session: <https://opencode.ai/v2/docs/websearch>.

Installed `opencode run --help` was executed read-only in the parent session. It advertises `--standalone`, `--model provider/model#variant`, `--agent`, `--format json`, `--thinking` and `--auto`. Help execution did not submit a prompt or start an evaluation. The documented CLI supports private servers, but advertised flags alone do not prove a restricted model-visible tool catalog or the absence of auxiliary inference. Sources: actual installed command output and <https://opencode.ai/v2/docs/cli>, fetched in this session.

The current parent's Code Mode catalog discovery did not expose a callable search-provider API: lexical search returned model/session/browser utilities, not a search-engine connector. The separate built-in `websearch` tool remains available to the parent. This observation is about the current catalog, not proof that no integration API exists elsewhere.

## Design implications

These are design judgments, not additional facts promised by the documentation:

- Pin one search provider, result format, locale and result count for every candidate. Do not use random selection or silent provider fallback in the comparison.
- Give every web candidate the same logical `websearch` and `webfetch` capabilities. Do not compare Gemini-native grounding against a different search service for the other models without treating that as a separate experiment.
- The codebase suite should expose only bounded directory listing/glob, content search and numbered file reading against a frozen snapshot. No editing, arbitrary shell, network, delegation or session utilities.
- Prefer an explicit minimal tool catalog with verified model-specific wire adapters. A permissions deny list alone does not prove that unrelated intrinsic/session tools are absent.
- Retain complete queries, search results, fetched documents and actual model-visible truncation previews. Log every attempted tool call, but distinguish exploratory fetch failures from a failed final research answer.
- Validate adapter/tool contracts offline, then use counted first real scheduled cases as compatibility gates. Do not spend extra generation calls on a hidden pilot or silently replay rejected cases.

## Still unverified before approval

The selected connected search provider, its usable noninteractive access path, quota, account debit and current service availability have not been inspected or tested here. A later focused parent grep of `~/.config/opencode/opencode.jsonc` for a `websearch` key or a named search-provider selector returned no matches; this does not identify remembered selection or ancestor/project configuration. There were no candidate-generation calls or search-engine smoke queries for this finding. Search credentials must not be inspected or copied into the plan. Final approval should confirm use of an already connected fixed provider; absent access is a setup blocker, not authorization to switch engines or request new credentials silently.

The parent also fetched <https://opencode.ai/v2/docs/console/go/> after the model-contract researcher. The actual wording asks custom clients to send typical coding-agent traffic, identify themselves with their own user agent and send a stable `x-opencode-session` per conversation. The web suite is therefore scoped to developer engineering research, not arbitrary general research. Provider-policy compliance cannot be granted by user consent alone; if workload suitability remains materially unclear before execution, seek first-party clarification or a separately approved route rather than silently assuming an exemption.
