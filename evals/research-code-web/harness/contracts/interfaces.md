# Frozen package interfaces

The user's execution request and choice of 648 trials supersede the original proposal's zero-call authorization. All preparation uses the explicitly retained GPT-6.1 Sol Fast high controller, not candidate inference. No provider or account configuration changes or installations are authorized. Preparation stops on unresolved access or isolation rather than inventing capabilities.

## Inputs

`contracts/runtime.json` defines all nine configurations and resource limits. `contracts/search.json` will record the verified fixed external search access contract without secrets. Tools native to a provider are not enabled merely because an upstream API documents them. The measured unit is the disclosed actually available model/route/tool configuration.

`tasks/<suite>/tasks.json` is an array of objects with `schema_version:1`, `id`, `suite` (`web` or `code`), `prompt`, `cluster_id`, and optional `snapshot_id` (one of click,httpx,cobra,prometheus,zod,opencode). Only these public task fields enter candidate input. Web prompts contain no answer URLs.

`gold/<suite>/gold.json` maps task IDs to objects containing `units` (each has `id`, `description`, `essential`, `evidence`), `critical_errors`, `acceptable_alternatives`, `reference_answer`, and `fixtures`. Evidence contains `path`/`url`, `quote`, optional `start_line`/`end_line`, and a hash or a reference to a hashed archived source. The task author validates every quote against the actual source. Every scored criterion must be inferable from the prompt. Units use equal weight; essential flags determine task success, not a hidden score multiplier. Fixtures include correct, omitted, wrong, unsupported, contradictory and alternate-valid cases. Reference evidence never enters the candidate view.

`schedule.json` has `seed`, `configurations`, `blocks`, `trials`. Each trial has `id`, `index`, `suite`, `task_id`, `repetition`, `configuration_id`, `block_id`, `position`. All task/configuration combinations have three repetitions. Review obligations are selected from planned IDs before execution.

## Tools

Each tools package exports `tools()` returning OpenAI Chat function schemas, and `dispatch(name, arguments, context, deadline)` returning a JSON-serializable object with `status`, `text`, `archives` (mapping safe filenames to text; encode raw bytes as base64), and `metadata`. `text` is the exact uncapped candidate evidence; the trial engine applies explicit per-result and cumulative character truncation, surrounds content with untrusted-data delimiters, and stores both originals and the exact visible result. Core archives tool output before model continuation. Errors are tool results, not invented evidence. `metadata.stop_reason` may be one of the frozen stopping statuses. No source-derived instructions are obeyed.

Web `context` includes `search_contract` and broker credentials through process-local environment only; no secrets are returned. `websearch` takes `query`; `webfetch` takes `url`, optional `offset` (characters) and `limit` (characters), bounded by core. Each continuation consumes a fetch allowance. Search is model-free through the authenticated existing OpenCode service API with an explicit engine. The service-normalized JSON is archived as such, not falsely called a raw upstream SERP.

Code `context` includes only the assigned resolved `snapshot_root` and manifest. Tools are `list`, `glob`, `grep`, `read`; schemas define exact optional arguments. Code dispatch executes a sandboxed worker with no network, writes, arbitrary commands or outside-snapshot access. Tool implementation/interpreter reads required to run are declared. Gold, user worktrees, credentials and other trial data remain inaccessible. Actual negative isolation probes must pass before candidate calls.

## Core execution

`harness.core.runner.run_trial(spec, credentials, transport=None, dispatcher=None)` returns a terminal record, using injected transport/dispatcher only for offline tests. `spec` has `trial`, `task`, `configuration`, `runtime`, `tools`, `tool_context`, `directory`, `ledger_path`. It contains no gold. Direct Chat transport sends one POST per step with no retry. Credentials supplied ephemerally contain only required route/service credentials. All artifacts are sanitized before writing; no credential stores copied or readable by tool workers.

Every request records the original full assistant object, including reasoning/signature/tool-call fields, and replays it without reconstruction. For Gemini only, after all tool results, a fixed nonempty user continuation is appended when the request otherwise does not end with a nonempty user message. No assistant prefill or empty user tail is sent. The last-step instruction is sent before the final allowed step and tools are omitted. These fixed control messages contain no task-specific guidance.

The engine durably reserves an ID and logs each request intent/start exactly once, persists sanitized request/response hashes, tool evidence, final answer separately from intermediate text, native history/metadata, timings and terminal state. A supervisor enforces 240 seconds for the whole invocation and collects partial evidence. Interrupted/uncertain sends are never replayed. Completion requires a nonempty final answer and normal finish inside deadline. Tool-only, truncated or partial output is not a completed answer. First trials per configuration per suite are counted compatibility gates; absence of tool use is not native rejection. Ordinary timeout/limit failures continue; frozen blocking classes stop dispatch.

## Grading and analysis

Blind packets include opaque IDs, prompt, gold and exact candidate-visible evidence, not model/effort/latency or native reasoning. Each unit gets independent `correct` and `supported` booleans plus rationale/evidence. Grades include critical error instances, uncertain flags, auxiliary citation/usability/unsupported-extra measures and grader provenance. Completed answer semantic scores use explicit evaluable n; nonanswers have no fabricated semantic grade. Operational failures receive zero outcome credit only in all-attempt effective coverage/success.

Practical success requires every essential unit correct and supported, >=80% of other units (vacuous when none), no critical or decisive unsupported claim, operational completion, and observed search+fetch for web or file-read for code. All critical/uncertain grades and the 162 preselected IDs receive independent fresh-session review; sampled unrun IDs are reported unrun, not reviewed. Original grades are immutable; adjudication is separate and sealed before unblinding. Same-backend AI review is disclosed, not called human calibration. Analysis uses cluster resampling, separate suites and the frozen practical recommendation thresholds.
