> English translation of [DESIGN.md](DESIGN.md). The original is kept verbatim as an archived artifact.

# Haiku 5.5 exploration

Decision: design A, with the capture and diagnostics of design B. The runner keeps a single scheduler and trial loop from the copy of the R2 base; it uses no parallel adapter, monkeypatch, loader or additional JSON plan. The comparison covers only the code and files of the previous fixture.

Interface: `python3 -B exploracao/haiku-5-5/haiku.py run --out exploracao/haiku-5-5/results/round-1`. The wrapper runs five new smokes, requires 5/5 correct with valid evidence and proof of the parameters, then runs 150 trials. `plan`, `validate-offline`, `preflight` and `report` complete the interface. New destinations; no overwriting or automatic resumption.

Cohort: Haiku 5.5 low, medium, high, xhigh and max, route `cli_proxy/cpa-claude-haiku-5-5`, wire `claude-haiku-5-5`, Messages, no Fast. A `Candidate` tuple is the source of the cohort. The six cases, prompts, grader and 23 files come from the frozen base `exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. `cases.py`, `test_cases.py` and `observer.js` stay byte-equivalent.

Controls: five repetitions, seed 20261010, 25 steps, 300 seconds per task process, admission budget between trials of 21600 seconds per phase, context 272000, output 128000 for all. Output is the deliberate experimental change given the previous cap of 32768. Only read/glob/grep/list; private discovery of configurations, plugins and skills. This is not equivalent to operating-system isolation.

Proof of execution: model, identity, variant/effort, Messages route, adaptive thinking and integer max_tokens 128000 in all observed requests. A preflight without inference does not prove forwarding; the smoke proves the request sent, not the provider's internal execution. No inference retries or automatic effort changes.

Export: a dedicated function in runtime.py keeps stdout in a regular 0600 file, stderr captured, timeout and process-group termination. It preserves sanitized bytes before UTF-8/JSON, with exit, timeout, raw and preserved bytes/SHA and failure offset. It does not reserialize, correct or automatically re-export. A synthetic test does not demonstrate the cause of a native OpenCode failure.

Diagnostics: preserve finish/rawFinish of all assistants; distinguish a recovered intermediate limit from a terminal limit. A terminal limit is its own category, outside ordinary incorrect answers and approved pairs. Export/identity failure remains infrastructure, even if there is a limit signal. The report states planned, attempted, stop_reason and exit_code; incomplete coverage exits non-zero.

Provenance: sources/protocol/catalog/executable and the old inventory are verified before and after the phase, including the last trial. The frozen copy describes the code actually used. Do not alter sources or earlier results. Local validation artifacts do not count as inference.

Arena: A 10/10, B 8/10 on five criteria of preservation, execution, native proof, integrity and interface. B added a loader and three duplicated flows. Complete export receipts, intermediate/terminal finishes and explicit coverage were adopted. The readers and the judge used GPT models; there was no cross-family review.

Validation before delivery: previous grade, balanced 150 schedule, configuration and negative proofs, large/invalid/timeout/sanitization export, terminal diagnostics and recovery, 5/5 gate, incomplete coverage and final guard. Native attempt only through the private CLI; if the sandbox blocks port/network, record zero calls and provide the command for the Terminal.
