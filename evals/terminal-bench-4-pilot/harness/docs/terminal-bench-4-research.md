# Terminal-Bench 4.0: preparing GLM-5.3-Flash vs SWE-2

*English translation of the original Portuguese preparation note. URLs, code, configuration snippets and figures are unchanged.*

Research on primary sources, consulted on **2026-10-06**. No packages were installed, no accounts authenticated, no sandboxes created, no inference requests made and no paid runs started. No local configuration/credential files were read. The applicable global instructions were taken into account; no additional `AGENTS.md` files were found in `evals`, `docs` or the ancestors checked.

## Conclusions for choosing the architecture

- **TB4.0.0 has 66 tasks; `-k 5` means 330 trials per model, 660 for the comparison**, before oracle/retries. Three tasks require an H100; do not substitute the L4 from the pricing example. The main score is accuracy over all attempts, not pass@5. [B1][B2][B3][B4]
- **Harbor integrates `opencode`**: the same harness can be kept in both arms, changing only model/provider and credential. The adapter installs OpenCode **inside each sandbox**; it does not reuse this machine's session/configuration. It supports ATIF and the options `version`, `variant`, `opencode_config` and `disable_web_search`. [H1][H2][H3]
- The local IDs given are `opencode-go/glm-5.3-flash` and `cli_proxy_openai/devin/swe-2`. They are OpenCode references, **not universal LiteLLM IDs**. The custom provider and its authentication must also exist in the sandbox. The adapter splits provider/model at the **first** `/`, preserving `devin/swe-2`. [H2][H4][O1]
- **Using the Mac's loopback proxy as the `baseURL` of an agent installed on Modal is not enough.** There, `127.0.0.1` refers to the sandbox, not the Mac; an allowlist does not create private connectivity. Modal allows public egress by default, but that does not make the local loopback reachable. [H2][M3]
- The option with the least infrastructure is **Terminus-2 in both arms, Harbor running locally and Modal sandboxes for the tasks**. Terminus-2/LiteLLM performs inference in the host Python process, so SWE-2 can keep using the loopback proxy without publishing the proxy or sending its key to the sandbox. This **changes the harness** relative to the OpenCode option; do not mix OpenCode in one arm and Terminus-2 in the other. [T1][T2][T3]
- If OpenCode is a requirement, first choose an authorised, directly reachable SWE-2 endpoint, or a private/authenticated per-trial transport. **Do not recommend a public `0.0.0.0` bind, an open port-forward, an unauthenticated tunnel URL or copying the local credentials directory.** The security section below separates documented components from integration work still needed.

## Harbor + OpenCode: what is confirmed

The code was checked at commit **`1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4`** of the official `harbor-framework/harbor` repository. At that point `pyproject.toml` declares Harbor `0.24.0`, Python `>=3.12`, LiteLLM `>=1.92.0` and a Modal extra with `modal>=1.5.4`. The latest official release checked is `v0.24.0` (2026-10-05); the OpenCode and Terminus-2 adapter files at that tag were compared with the commit and were identical. This does not prove that all transitive dependencies are pinned. [H0][H2][T2][H5]

### Installation and harness version

- The adapter runs `npm i -g opencode-ai@<version>`; without `version` it uses `@latest`. It installs dependencies such as curl, bash, coreutils, Node/npm and uses nvm on non-musl images. Pin **the same exact OpenCode version** in both arms; do not use `latest` in a reproducible comparison. [H2][H3]
- The actual invocation is `opencode --model=<provider/model> run --format=json --thinking --dangerously-skip-permissions -- <instruction>`, with stdout collected and converted to ATIF. `--thinking` includes thinking blocks in the output; it is not the same as fixing the model's reasoning effort. [H2]
- `opencode_config` is a **JSON overlay object** passed in `agents[].kwargs` or `--ak`; do not assume `--ak config=/file` works: the OpenCode adapter does not declare the `native_config` capability. The configuration is written to `~/.config/opencode/opencode.json` inside the sandbox. [H1][H2]
- The adapter still generates the legacy fields `provider`, `options.baseURL` and `permission`. The V2 documentation uses `providers`, `settings.baseURL` and `permissions`. **Do not conclude this is automatically incompatible:** the official migration guide confirms support for V1 configuration, allows coexistence at top level and gives precedence to the native V2 form. Each nested provider entry must use a single format. Validate the binary version, the flags used by the adapter and the JSON events before the full batch. [H2][O1][O2][O3]

### Credentials and base URL

Harbor's credential registry knows `openai` (`OPENAI_API_KEY`, `OPENAI_BASE_URL`/`OPENAI_API_BASE`) and `opencode` (`OPENCODE_API_KEY`), but **contains neither `opencode-go` nor `cli_proxy_openai`** at the commit checked. So do not count on automatic forwarding for these two IDs. `export` or `--env-file` on the host does not forward variables indiscriminately to the sandbox. Use `agents[].env` or `--ae` explicitly. The Trial code also applies these variables during agent setup. [H4][H6][H7]

The public catalogue used by OpenCode registers `opencode-go` with `env: ["OPENCODE_API_KEY"]`, base `https://opencode.ai/zen/go/v1`, and `glm-5.3-flash` with tool calling, interleaved reasoning in `reasoning_content`, a 1,000,000-token context and 131,072-token output. Treat the limits as catalogue metadata, not as an acceptance test of the endpoint. The Go documentation confirms the ID and `/chat/completions`; a public read of `/models` returned `glm-5.3-flash`. [O4][O5]

#### Proposed configuration structure for OpenCode V2

`agents` excerpt for a Harbor job. The Harbor and OpenCode V2 fields are documented; the combination **has not yet been run**. Replace the version and endpoint after the transport decision. The variables to the right of `${...}` must be provided by a secrets manager/controlled environment, without writing values to the repository. [H2][H3][H6][H8][O1][O2][O4]

```yaml
agents:
  - name: opencode
    model_name: opencode-go/glm-5.3-flash
    n_concurrent: 1
    env:
      OPENCODE_API_KEY: '${GLM_GO_API_KEY}'
    kwargs:
      version: '<VERSAO_EXATA_OPENCODE_V2_VALIDADA>'
      opencode_config:
        $schema: https://opencode.ai/config.json
        providers:
          opencode-go:
            settings:
              apiKey: '{env:OPENCODE_API_KEY}'
  - name: opencode
    model_name: cli_proxy_openai/devin/swe-2
    n_concurrent: 1
    env:
      SWE_PROXY_API_KEY: '${SWE_PROXY_API_KEY}'
    kwargs:
      version: '<MESMA_VERSAO_EXATA_OPENCODE_V2_VALIDADA>'
      opencode_config:
        $schema: https://opencode.ai/config.json
        providers:
          cli_proxy_openai:
            name: SWE-2 evaluation endpoint
            env: [SWE_PROXY_API_KEY]
            package: '@opencode/ai/providers/openai-compatible'
            settings:
              baseURL: https://ENDPOINT_AUTORIZADO_E_ALCANCAVEL/v1
              apiKey: '{env:SWE_PROXY_API_KEY}'
            models:
              devin/swe-2:
                modelID: devin/swe-2
                capabilities:
                  tools: true
                  input: [text]
                  output: [text]
```

(Placeholders kept as in the original: `VERSAO_EXATA_OPENCODE_V2_VALIDADA` = exact validated OpenCode V2 version; `MESMA_VERSAO_…` = the same exact version; `ENDPOINT_AUTORIZADO_E_ALCANCAVEL` = authorised and reachable endpoint.)

Notes:

1. `modelID: devin/swe-2` is an interpretation of the reference supplied by the user, **not confirmation of the name the upstream accepts**. Confirm the inventory/model mapping through a redacted read, without opening secret files or making inference calls at this stage.
2. The Go entry keeps the native provider, to preserve its own handling of session, cache and reasoning. Do not blindly replace it with the generic OpenAI runtime. [O1][O4]
3. SWE-2 limits/pricing were not filled in the example: the local catalogue/billing and the variant must be validated. These metadata affect compaction and costs; missing pricing can produce an apparent missing/zero cost. [H2][O1]
4. The adapter does not automatically infer a `baseURL` for custom providers from a generic variable; the overlay matters. When `opencode_config` is present, the code still removes the inferred endpoint for connection purposes, leaving routing opaque. On tasks with an allowlist, use `agents[].extra_allowed_hosts` for the actual Go/gateway domain — this adds a network exception, which must be recorded in the methodology. [H2][H4][H8][H9]
5. Model keys sent to the installed agent are accessible to code it can execute. Per-phase scoping **is not an absolute barrier** against an agent that copies the key into a file. Use a restricted key, quotas/expiry/revocation, and redact artifacts before publishing; Modal credentials must stay exclusively in the Harbor process. [H6][H7]

## Terminus-2 + LiteLLM: an alternative without exposing the proxy

Terminus-2 is a reference agent with a tmux terminal and logic outside the container. The code instantiates `harbor.llms.lite_llm.LiteLLM` on the host. `api_base`, `temperature`, `reasoning_effort`, `model_info`, `llm_kwargs`, `llm_call_kwargs` and `session_id_headers` are confirmed kwargs. The default backend is LiteLLM; `use_responses_api` defaults to `false`. For a Chat Completions-compatible API, LiteLLM documents `openai/<ID_UPSTREAM>`, `api_base` and an API key. Do not append `/chat/completions` to the base. [T1][T2][T3][L1]

**Structure for two separate jobs**, without putting API keys in `agents[].env`, because the model is called on the host. The `OPENAI_API_KEY` must be made available only to the correct Harbor process for each job; do not export all keys globally. [T1][T3][H6]

```yaml
# Braço GLM; combinar com o mesmo dataset, k, environment e timeouts do SWE.
agents:
  - name: terminus-2
    model_name: openai/glm-5.3-flash
    n_concurrent: 1
    kwargs:
      api_base: https://opencode.ai/zen/go/v1
      session_id_headers: [x-opencode-session]
      llm_call_kwargs:
        extra_headers:
          User-Agent: terminal-bench-comparison/1.0
```

(Comment translation: "GLM arm; combine with the same dataset, k, environment and timeouts as SWE.")

```yaml
# Braço SWE; PORTA_LOCAL é a porta previamente confirmada, sem ler segredos.
agents:
  - name: terminus-2
    model_name: openai/devin/swe-2
    n_concurrent: 1
    kwargs:
      api_base: http://127.0.0.1:PORTA_LOCAL/v1
      session_id_headers: [x-opencode-session]
      llm_call_kwargs:
        extra_headers:
          User-Agent: terminal-bench-comparison/1.0
```

(Comment translation: "SWE arm; PORTA_LOCAL is the previously confirmed local port, without reading secrets.")

`PORTA_LOCAL` makes the second example deliberately not ready to run. `openai/devin/swe-2` depends on confirming that the proxy accepts `devin/swe-2`. Both must use the same Harbor release, parsing options, compaction, output/turn limits and documented effort; arbitrarily limiting turns may move the comparison away from the official rules.

Go allows other coding agents, but asks for a **User-Agent identifying the client** and a stable `x-opencode-session` per conversation. The current Terminus-2 code implements `session_id_headers`, injects the ID into the headers and also passes `llm_call_kwargs` to the auxiliary summarisation calls. These points must be inspected in the pilot; do not invent a single fixed session ID shared across trials. [O4][T2]

For models LiteLLM does not recognise, `model_info` allows registering limits/costs (`max_input_tokens`, `max_output_tokens`, `input_cost_per_token`, `output_cost_per_token`). Fill them from the provider's sources and the chosen policy, not with figures from older models. The wrapper uses `drop_params=True`; a configured parameter may be dropped for lack of support, so record the actual request. If cost calculation fails, the wrapper may return `0.0`: **that does not prove the call was free**. [T2][T3]

## Network security: what it solves and what it does not

### Operational preference

1. **Local proxy + Modal, without publishing the proxy:** choose Terminus-2 for both and run Harbor on the same host as the proxy. The remote sandbox receives only the task's commands/files; LLM calls and keys stay on the host. This follows directly from the documented architecture/code, not from an assumed tunnel. [T1][T2][T3]
2. **Same OpenCode for both:** an authorised direct endpoint is the simplest option, if available. Otherwise, design a restricted/authenticated gateway or a private per-trial tunnel. The Mac proxy keeps its loopback bind; a gateway must restrict models and routes, authenticate with a dedicated token and expire/revoke access when the job ends. A bridge with an outbound connector does not need to open a public port on the Mac. **This bridge is not a ready-made feature of the Harbor adapter researched**; it requires separate implementation/validation.

### SSH tunnel: an official component, not a ready Harbor command

OpenSSH documents reverse forwarding with `-R`, for example in the form:

```bash
ssh -N -T -a \
  -o ExitOnForwardFailure=yes \
  -o StrictHostKeyChecking=yes \
  -R 127.0.0.1:PORTA_REMOTA:127.0.0.1:PORTA_PROXY_LOCAL \
  -p PORTA_SSH USUARIO@HOST_SSH_AUTENTICADO
```

(Placeholders: remote port, local proxy port, SSH port, user@authenticated SSH host.)

The remote listener stays on loopback, and so does the local destination; do not use `-R '*:...'`, `GatewayPorts yes` or `-A`. Pin the host key and use a dedicated key. The model installed in the sandbox could then talk to the remote listener without the inference API being public. [S1]

**Concrete gap:** Harbor's official `sshd_config` for streaming uses **`AllowTcpForwarding local` and `GatewayPorts no`**; therefore it **does not accept that remote `-R` as shown**. In addition, an ephemeral per-trial sandbox requires an init/cleanup hook, a guarantee of listener isolation and access to the right namespace (Compose may differ). Do not present `harbor --stream` + `ssh -R` as a ready recipe. Changing that policy means custom integration, to be authorised and tested. [S2]

Modal tunnels (`modal.forward`, `Sandbox.tunnels`) publish ports **from the Modal container to the Internet**, not the Mac's loopback. A random URL + TLS is not an authorisation control; the documentation says anyone with the URL can access the service. Sandbox Connect Tokens authenticate HTTP/WS access **to the sandbox**; they do not by themselves solve Mac proxy → sandbox. [M3][M4]

ASP is only an **RFC draft** in the Harbor documentation: do not assume local OpenCode with remote tools is ready to use. The text says Modal SSH/ASP was not validated in that MVP. [H10]

## Modal: dependencies, authentication and GPU

Official commands for **a future authorised phase**, not run in this research: [H11][M1][M2]

```bash
uv tool install 'harbor[modal]'
modal token new
```

The Modal documentation also shows `pip install modal` and `modal setup`. Harbor's preflight accepts an existing `~/.modal.toml` **or** `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` in the host environment. The file's existence does not guarantee a valid token; do not read or copy its contents to the sandbox. Pin the Harbor release and dependencies instead of using a floating installation when preparing the comparison. [H5][M1][M2]

- Select `environment.type: modal` or `-e modal`. Harbor passes the task's CPUs/RAM/GPU to the sandbox; `--override-gpus` exists, but changing GPU, CPU, RAM, disk or timeout may invalidate comparability. The GPU is for the **task**, not for serving GLM/SWE via APIs. [H8][H12][M2]
- Harbor Modal uses `gpu_types[0]` if there are several types and forms `<type>:<n>`. If there is no type, it uses `any`. With `modal_vm_runtime=true`, GPUs are rejected. Modal confirms that GPU sandboxes are only supported with `runtime="gvisor"`; VM and GPU are not interchangeable. [M2][M5]
- Harbor Modal supports Compose, but network allowlist/per-phase policy capabilities are limited to single-container. The gVisor/Compose code uses host networking **inside Modal**, not the Mac's host network. Do not confuse this with access to local `127.0.0.1`. [M2][H9][H12]
- Modal requires a valid payment method for GPU use. Starter advertises 100 containers and 10-GPU concurrency; actual account quotas must be checked by the user. Harbor concurrency does not raise provider/model quotas. [M1][M6]
- Harbor uses a default 24 h lifetime in the Modal adapter; the plain Modal SDK defaults to 5 minutes. Agent timeout is not the same as sandbox lifetime. Keep `delete: true`; monitor leftover resources and avoid accidental `--no-delete`. [M2][M5]

## Runs, concurrency, metrics and costs

### Confirmed Harbor controls

| Concept | CLI | Config | Semantics |
| --- | --- | --- | --- |
| Attempts per task and agent | `-k` | `n_attempts` | Default 1; does not automatically mean `pass@k` |
| Simultaneous trials | `-n` | `n_concurrent_trials` | Default 4; global limit |
| `agent.run()` phases per agent | — | `agents[].n_concurrent` | Not greater than the global limit |
| Shared concurrency pool | — | `agents[].concurrency_group` | Members must use the same limit |
| Re-runs on exception | `-r` | `retry.max_retries` | Default 0; not statistical replication |
| Maximum tasks | `-l` | `datasets[].n_tasks` | Applied after filters |
| Validate without running/downloading | `--dry-run` | — | Checks config, kwargs, credentials and sources |
| Show configuration | `--print-config` | — | Do not run with a literal secret in the config |

Sources: [H8][H12][H13]. Even `dry-run` is left to the preparation phase: nothing was installed or authenticated here. For a comparison with T tasks, 2 models and k attempts, there are **2 × T × k planned trials**, before retries; a pilot/subset is not a full-benchmark score.

### Metrics to preserve

OpenCode converts `step_finish` events into ATIF with input/output, cache and reasoning tokens and the cost reported by the harness; it sums input + cache read into `prompt_tokens` and keeps cache separately. Costs of `0` become a missing field in parts of the adapter. Do not recompute input pricing over all `prompt_tokens` without subtracting cache, and do not confuse metadata pricing with an invoice. [H2]

Recommended comparison report: reward/result per task and attempt, the dataset's official aggregate, paired difference with uncertainty, agent and total duration, setup/API/infra failures separated, tokens/cache/reasoning, and LLM and sandbox costs separated. Do not silently drop tasks with errors and do not pick the best of k as if it were the mean of runs. This list is a methodological recommendation; the official TB4 requirements are covered in the dataset section.

### Model costs

- **GLM-5.3-Flash on Go:** USD **0.15 input / 0.50 output / 0.03 cached read per million tokens**; Go plan USD 10/month, Go Plus USD 40/month. The page advertises a monthly GLM Flash allowance of USD 60/180 respectively, with a 5 h window = 20%, weekly = 50%. This is subscription accounting; do not promise incremental payment identical to the computed cost. `Use balance` can enable paid fallback after the quota — check that it does not trigger unauthorised spending. [O4]
- **SWE-2:** the Cognition/Devin source publishes a list price of USD **3 input / 15 output / 0.30 cached input per million**, a free promotion for self-serve until 2026-10-15 and a 75% enterprise discount until 2026-12-31 (USD 0.75 / 3.75 / 0.075). These are **Devin Desktop/CLI** prices, not a guarantee of pricing/access for the local `cli_proxy_openai` proxy. The High/Medium/Max variant and the plan need confirming; older models on the LiteLLM Cognition page do not confirm SWE-2. [C1][L2]
- There is no defensible total budget without an authorised pilot, per-task duration, GPU mix, tokens/cache and the actual plan/quotas. A zero price in the log or an in-app promotion does not prove an external benchmark is free.

### Modal costs: use the Sandboxes table

The page distinguishes general Functions prices from **Sandbox + Notebooks**. For Harbor Modal, the sandbox table consulted publishes CPU USD **0.00003942/core/s**, memory USD **0.00000667/GiB/s**, GPU at general prices: L4 USD 0.000222/s, A10 0.000306/s, L40S 0.000542/s, A100 40GB 0.000583/s, A100 80GB 0.000694/s, H100 0.001097/s. **Do not use the general Functions CPU/RAM pricing, which is roughly 3× lower.** A Modal core is physical, equivalent to 2 vCPU; check the billing unit before projecting a Harbor request. [M6]

Planning estimate: `Σ segundos × (cores faturados × tarifa_CPU + GiB faturados × tarifa_RAM + GPU × tarifa_GPU)` (seconds × (billed cores × CPU rate + billed GiB × RAM rate + GPU × GPU rate)), plus build/storage/egress/plan where applicable. Modal charges CPU/memory according to usage/reservation rules; computing from declared resources is an approximation, not a guaranteed invoice. A purely arithmetic example, **not a TB4 estimate**: 30 min with 4 physical cores + 8 GiB ≈ USD 0.38; plus one L4 ≈ USD 0.40, total ≈ USD 0.78. [M6]

Starter advertises USD 30 of monthly credits; a pinned region may cost 1.15–1.75×. Credits do not justify starting a run without authorisation, and more concurrency does not automatically reduce total compute. [M6]

## Terminal-Bench 4.0: dataset, resources and official protocol

### Identifiers and reproducible downloads

The official Run page prescribes Harbor, a GPU-capable sandbox (Modal used by the authors) and five attempts. The identifier is **`terminal-bench/terminal-bench@4.0.0`**, not `terminal-bench@4.0` nor the 2.0 version shown in generic Harbor examples. [B1]

```bash
# Exemplo oficial: documentação, NÃO executado.
harbor run -d terminal-bench/terminal-bench@4.0.0 \
  -e modal -a claude-code -m anthropic/claude-sonnet-5 -k 5

# Análise local, sem publicar:
harbor view jobs
```

(Comment translations: "Official example: documentation, NOT run." / "Local analysis, without publishing.")

For the two models in this comparison, the right structure is to swap the agent/model according to the chosen plan, keep `-k 5` and choose an authorised concurrency, or use a job YAML with two agents. **Do not copy the command above as if it already configured the local providers.** [B1][H8][H13]

Shared config base (complete with the `agents` of the chosen architecture; concurrency 2 is a conservative proposal, not a TB4 rule): [H8][H13][B5]

```yaml
job_name: tb4-glm-flash-vs-swe2
jobs_dir: jobs
n_attempts: 5
n_concurrent_trials: 2
retry:
  max_retries: 0
environment:
  type: modal
  delete: true
datasets:
  - name: terminal-bench/terminal-bench
    ref: sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732
```

Commands confirmed for future preparation: `harbor run --dry-run --config comparison.yaml` validates without downloading tasks/running a job; `harbor job schema` prints the schema. **`harbor run --config comparison.yaml` starts potentially paid work**, so only after explicit authorisation. If there are two Terminus-2 jobs, use separate names and configure the corresponding host key in each process; do not share a wrong `OPENAI_API_KEY` across endpoints. [H8][H13]

| Official pin/asset | Value consulted |
| --- | --- |
| Release/tag | `v4.0.0` |
| Release commit | `452bf305c6daa62fc59061d22133a7cbc7c1572e` |
| Canonical dataset in the leaderboard pipeline | `terminal-bench/terminal-bench@sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732` |
| Prebuilt tarball | `terminal-bench-prebuilt-v4.0.0.tar.gz`, 452,093,597 bytes |
| Published tarball SHA256 | `6d2c57cbcb1a75b5cdc0b0f989747fa68cdc65df8ff0a6893045a70ced7e668e` |
| Image manifest | `prebuilt-images.json`, 151,063 bytes, 66 tasks/157 images |
| Published manifest SHA256 | `35930574da44fe4e90f6741562a9596cdbf02d2b64d639b6c2b7ab2582a4b0e6` |

Sources: the official release API, the manifest and the pinned pipeline. Each image in the manifest has an individual digest and `pinned_ref`. The Hub package digest **is not** the GitHub tarball checksum. The release has `immutable: false` in the API; for a comparison, prefer digest/commit and record the images. The hashes were read from official sources, **not recomputed locally**; the large tarball was not downloaded. Its 452 MB do not represent the aggregate space of all images/dependencies. [B2][B3][B5]

A documented future download is `harbor download 'terminal-bench/terminal-bench@4.0.0'`; SHA256 refs are also supported by the Hub. The Run page installation does not pin a Harbor release: record a concrete version/lock/config of the harness and dependencies. [B1][B6][H5][H11]

### Per-task resources — not a single-machine requirement

The manifest reports **66 tasks**, confirmed by enumerating the release's 66 `tasks/*/task.toml` files and by the official pipeline constant `EXPECTED_TASK_COUNT=66`. The distribution below was derived from a public read of those TOMLs, without running the benchmark. [B3][B4][B7]

| Agent environment field | Distribution across 66 tasks |
| --- | --- |
| `cpus` | 2: 44 tasks; 4: 14; 8: 6; 16: 2 |
| `memory_mb` | 4,096: 35; 8,192: 22; 16,384: 8; 32,768: 1 |
| GPU | 1 H100: 3; `gpus=0`: 55; field omitted: 8 |
| `storage_mb` | 10,240: 47; the rest between 4,096 and **1,024,000 MB** |
| Agent timeout | **28,800 s (8 h)** in all 66 |

An omitted GPU does not request a GPU according to the Harbor schema. CPU/RAM are per-environment resources; the provider's request/limit policy and billing unit matter. Requested storage **does not guarantee** that Modal enforces/allocates that size: the current storage sizing matrix does not list Modal. Do not claim the evaluation can run on the Mac just because it has enough CPU/RAM. [B8][H8][M2]

| GPU task | CPU | RAM MB | Storage MB | GPU | Verifier timeout |
| --- | ---: | ---: | ---: | --- | ---: |
| `fp8-rmsnorm-gemm` | 4 | 16,384 | 30,720 | 1 H100 | 18,000 s |
| `jax-speedrun-gpu` | 16 | 32,768 | 1,024,000 | 1 H100 | 7,200 s |
| `math-eval-grader` | 8 | 16,384 | 30,720 | 1 H100 | 900 s |

**JAX also requires a separate verifier with 16 CPU, 32,768 MB RAM, 1 H100 and 1,024,000 MB storage.** `environment_mode="separate"` appears in **65/66 tasks**; only six specify resources for the separate environment, and JAX is the only one that explicitly requests a GPU in that block. Do not assume the verifier reuses the agent's container/GPU for free, nor that trial concurrency equals the total number of containers. Build, verification and collection add time/cost beyond the agent timeout. [B7][B9][B10][B11]

8 h is the **ceiling of each agent execution**, not an estimated duration of a task or of the whole job. The 4.0 announcement reports eight tasks removed and 19 fixed/recalibrated. Do not reuse TB3 results as TB4. [B12]

### k, concurrency and score integrity

- The Run page uses `-k 5`; with 66 tasks that is **330 trials per model**. Two arms = **660 trials**, before oracle validation/retries. [B1][B4]
- The release README recommends validating the sandbox with **oracle 5×** and shows concurrencies of 500 for the oracle / 100 for the agent. An official pipeline config has 330 concurrent trials. These are cloud examples, **not a low-cost recommendation nor a universal requirement**. Start with low concurrency and raise it only after measuring quotas; Modal Starter advertises 100 containers and GPU concurrency 10. Separate verifiers/sidecars increase demand. [B13][B14][M6]
- Official rules: the same unmodified canonical dataset, full coverage, **≥5 attempts per task**, no CPU/RAM/GPU/storage or timeout overrides and no raised timeout multiplier. Errors count as failures and stay in the denominator; reward-hacking disqualifications become reward zero. These rules matter for comparability even in an internal evaluation. **TB4 community submissions are closed** in the source consulted. [B4][B15]
- Do not publish automatically: `harbor upload jobs/<name>` / `--upload` creates an upload (private by default according to Run), but leaderboard eligibility requires public trials. This research made no upload. Review secrets, logs and licence/anti-contamination before any sharing. [B1][B15]

### Main metric and 95% CI

The official pipeline code consulted at commit **`7f1992f81f2f06a185eb55e69403cfa00b5dc981`** counts success as `reward > 0`; an error without a reward is a failure. [B16]

```text
accuracy (%) = 100 × successful trials / total trials
SE (%) = 100 × sqrt((1/N²) × Σ_i p_i(1-p_i)/(k_i-1))
95% CI = accuracy ± 1.96 × SE
```

`N` is the number of tasks; `k_i` the number of attempts for the task and `p_i` its success proportion. Do not replace this with a binomial CI that treats the 330 attempts as independent observations. For the difference between models, add a per-task paired analysis (a recommendation, not the official leaderboard formula).

The pipeline also computes pass@2–5 via `1 − C(n−c,k)/C(n,k)`, averaged per task, but **do not confuse this secondary metric with the main accuracy or with the `-k` flag**. Tokens shown are `input_tokens + output_tokens`, with cache separate and not added again; cost is the sum of `cost_usd` over the trials selected by the pipeline. Disqualification reduces reward, it does not erase cost. [B16]

### Official observed costs — not a budget for GLM/SWE

A public read of the official leaderboard on 2026-10-06 found 32 rows with 330 trials. Examples of published telemetry: [B17][B18]

| Harness/model/effort | Accuracy | Published cost for 330 trials |
| --- | ---: | ---: |
| Claude Code / Opus 5.5 / max | 64.85% ± 3.11 pp | USD 4,718.65 |
| Codex / GPT-6.1 Sol / max | 58.18% ± 3.11 pp | USD 634.24 |
| Codex / GPT-6 Luna / max | 16.36% ± 2.72 pp | USD 72.14 |

Official read API: `POST https://api.harborframework.com/functions/v1/leaderboard-read`, public payload `{ "package": "terminal-bench/terminal-bench", "name": "4-0-0", "page": 1, "page_size": 100 }`. This POST queries data; it does not start a job. [B17][B18]

**Limitations:** these rows use other models/harnesses and are not a GLM/SWE estimate. The aggregation selects the latest attempt and sums trial telemetry; it does not break out infrastructure, image build, storage, downloads or all earlier retries. Some rows have partial cost. Do not interpret them as total invoice cost. No fixed official TB4 budget or guaranteed total time was found. [B5][B16][B17]

## Decisions and validations still needed

1. **Harness:** keep OpenCode for both (priority if the goal is the local harness) or approve Terminus-2 for both to avoid the network bridge.
2. **SWE transport:** an authorised direct endpoint, a private authenticated per-trial integration, or keeping the host proxy with Terminus-2. Do not open the proxy publicly to solve networking.
3. **Identity/config:** exact OpenCode version, upstream mapping of `devin/swe-2`, variant/reasoning, context/output limits, streaming/tools schema and usage reporting. Availability in local OpenCode does not prove access from the sandbox or LiteLLM.
4. **Credentials:** the user provides restricted keys through a secure environment, not via chat; validate quota/plan/rate limits without printing secrets. Never forward Modal tokens to the agent.
5. **Dataset and TB4 rules:** pin the same snapshot/digest; decide full vs pilot/subset, k, concurrency, network exceptions and retry policy before the batch. Do not edit tasks/tests to favour a model.
6. **Budget:** a monetary/allowance ceiling and a stop at the limit, with LLM, proxy and Modal costs broken out. Go with balance fallback and the temporary SWE promotion require attention to dates.
7. **Later pilot, only when authorised:** validate ATIF parsing, logs/reward, GPU/runtime, cleanup, Go session, tools, compaction and accounting. This note contains no functional evidence of execution.

## Primary sources

- [H0] [Harbor commit consulted](https://github.com/harbor-framework/harbor/commit/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4) and [release v0.24.0](https://github.com/harbor-framework/harbor/releases/tag/v0.24.0).
- [H1] [Harbor: pre-integrated agents](https://docs.harborframework.com/agents/pre-integrated-agents).
- [H2] [OpenCode adapter, official pinned code](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/agents/installed/opencode.py).
- [H3] [Agent options/version](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/agents/options.py).
- [H4] [Provider credential registry/model connection](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/agents/model_connection.py).
- [H5] [Harbor dependencies and version](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/pyproject.toml).
- [H6] [Harbor: environment variables](https://docs.harborframework.com/jobs/environment-variables).
- [H7] [Trial: scoped env in setup/run](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/trial/trial.py).
- [H8] [Harbor: job configs/schema](https://docs.harborframework.com/jobs/configs).
- [H9] [Harbor: network policies](https://docs.harborframework.com/tasks/network-policies).
- [H10] [Harbor: ASP RFC draft](https://docs.harborframework.com/sandboxes/asp).
- [H11] [Harbor: installation](https://docs.harborframework.com/getting-started/installation).
- [H12] [Harbor: pre-integrated sandboxes/capabilities](https://docs.harborframework.com/sandboxes/pre-integrated-sandboxes).
- [H13] [Harbor: run a job](https://docs.harborframework.com/jobs/run-a-job).
- [O1] [OpenCode V2: providers, endpoint, modelID, env](https://opencode.ai/v2/docs/providers).
- [O2] [OpenCode V2: config](https://opencode.ai/v2/docs/config).
- [O3] [OpenCode V2: migration/V1 compatibility](https://opencode.ai/v2/docs/migrate-v1).
- [O4] [OpenCode Go: models, endpoints, prices, quotas and clients](https://opencode.ai/v2/docs/console/go/).
- [O5] [models.dev catalogue used by OpenCode](https://models.dev/api.json) and [public Go inventory](https://opencode.ai/zen/go/v1/models).
- [T1] [Historical official Terminus-2 documentation: independent execution](https://github.com/harbor-framework/harbor/blob/26106c6d9c66848a1440faf5724d336affac52aa/docs/content/docs/agents/terminus-2.mdx). Some defaults in the text are outdated; for options/defaults use T2.
- [T2] [Terminus-2: current pinned implementation](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/agents/terminus_2/terminus_2.py).
- [T3] [Harbor LiteLLM wrapper: requests, model_info and cost](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/llms/lite_llm.py).
- [L1] [LiteLLM: OpenAI-compatible endpoints](https://docs.litellm.ai/docs/providers/openai_compatible).
- [L2] [LiteLLM: Cognition](https://docs.litellm.ai/docs/providers/cognition), primary source for LiteLLM behaviour; does not replace provider confirmation for SWE-2.
- [C1] [Cognition/Devin: SWE-2 models/pricing](https://docs.devin.ai/desktop/models).
- [M1] [Modal: getting started/authentication/GPU payment method](https://modal.com/docs/guide/).
- [M2] [Harbor Modal: preflight, GPU/runtime, resources and secrets](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/environments/modal.py).
- [M3] [Modal: sandbox networking/security](https://modal.com/docs/guide/sandbox-networking).
- [M4] [Modal: tunnels/security](https://modal.com/docs/guide/tunnels).
- [M5] [Modal: sandboxes/runtimes/timeouts](https://modal.com/docs/guide/sandboxes).
- [M6] [Modal: published prices and quotas](https://modal.com/pricing).
- [S1] [Official OpenSSH manual: `-R`, `-a`, `-N`, `-T`, host keys](https://man.openbsd.org/ssh.1).
- [S2] [Harbor SSH: `sshd_config` with local forwarding only](https://github.com/harbor-framework/harbor/blob/1537850ff2e89ae3c0a3c376e7bc753d9c6e7fe4/src/harbor/environments/ssh.py#L208-L225).
- [B1] [Terminal-Bench 4.0: official Run page](https://www.tbench.ai/run).
- [B2] [Release v4.0.0](https://github.com/harbor-framework/terminal-bench/releases/tag/v4.0.0) and [official assets/digests API](https://api.github.com/repos/harbor-framework/terminal-bench/releases/tags/v4.0.0).
- [B3] [Official prebuilt manifest](https://github.com/harbor-framework/terminal-bench/releases/download/v4.0.0/prebuilt-images.json).
- [B4] [Canonical validation: 66 tasks, ≥5 attempts, overrides](https://github.com/harbor-framework/terminal-bench/blob/7f1992f81f2f06a185eb55e69403cfa00b5dc981/leaderboard/src/leaderboard/ci/static_analysis.py).
- [B5] [Pipeline: dataset digest and latest-attempt](https://github.com/harbor-framework/terminal-bench/blob/7f1992f81f2f06a185eb55e69403cfa00b5dc981/leaderboard/src/leaderboard/core/hub.py).
- [B6] [Harbor Hub download](https://docs.harborframework.com/harbor-hub/download) and [dataset refs](https://docs.harborframework.com/datasets/datasets).
- [B7] [Tasks at the release commit](https://github.com/harbor-framework/terminal-bench/tree/452bf305c6daa62fc59061d22133a7cbc7c1572e/tasks) and [public Git tree](https://api.github.com/repos/harbor-framework/terminal-bench/git/trees/v4.0.0?recursive=1).
- [B8] [Harbor resources/support matrix](https://docs.harborframework.com/tasks/resources) and [task configuration/defaults](https://docs.harborframework.com/tasks/configuration).
- [B9] [FP8 task TOML](https://raw.githubusercontent.com/harbor-framework/terminal-bench/452bf305c6daa62fc59061d22133a7cbc7c1572e/tasks/fp8-rmsnorm-gemm/task.toml).
- [B10] [JAX task TOML](https://raw.githubusercontent.com/harbor-framework/terminal-bench/452bf305c6daa62fc59061d22133a7cbc7c1572e/tasks/jax-speedrun-gpu/task.toml).
- [B11] [Math grader task TOML](https://raw.githubusercontent.com/harbor-framework/terminal-bench/452bf305c6daa62fc59061d22133a7cbc7c1572e/tasks/math-eval-grader/task.toml).
- [B12] [Official TB4 announcement](https://www.tbench.ai/news/terminal-bench-4-0).
- [B13] [README pinned at the release](https://raw.githubusercontent.com/harbor-framework/terminal-bench/v4.0.0/README.md).
- [B14] [Official Opus 5 run config](https://github.com/harbor-framework/terminal-bench/blob/7f1992f81f2f06a185eb55e69403cfa00b5dc981/leaderboard/runs/tb-4-0-0-opus-5-claude-code.json).
- [B15] [Rules and closure of community submissions](https://github.com/harbor-framework/terminal-bench/blob/7f1992f81f2f06a185eb55e69403cfa00b5dc981/leaderboard/SUBMIT.md).
- [B16] [Official metrics/CI/pass@k/tokens/cost](https://github.com/harbor-framework/terminal-bench/blob/7f1992f81f2f06a185eb55e69403cfa00b5dc981/leaderboard/src/leaderboard/core/metrics.py).
- [B17] [Public leaderboard read API](https://api.harborframework.com/functions/v1/leaderboard-read) and [official TB4 leaderboard](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench/4?tab=leaderboard&leaderboard=4-0-0).
- [B18] [Official leaderboard-read documentation](https://docs.harborframework.com/harbor-hub/leaderboards).
