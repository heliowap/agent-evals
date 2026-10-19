# Adversarial review: GPT-6-Astra medium, 2026-10-18

Run with `codex exec -m gpt-6-astra -c model_reasoning_effort="medium" -s read-only` (Codex CLI 0.162.1 via CLIProxy) against README.md as of that date and the bottle clone at commit `8ec5fe2`. About 70.7k tokens. Dispositions are in the package README, section Review.

## Prompt

> You are an adversarial reviewer of an evaluation design. Your job is to find reasons this experiment would produce a wrong, misleading, or uninterpretable answer. Do not be polite; do not praise. Do not modify any file.
> 
> The design is in ./README.md (read it fully). The codebase it uses is a clone of bottlepy/bottle at /tmp/bottle-probe/src (bottle.py plus test/). Verify factual claims against the code and the README where you can (sizes, how tests touch module globals, feasibility of the split, feasibility of the example tasks). You may run read-only shell commands. Also check the agent configuration: Claude Code 2.1.296, `claude --help` is available locally; do not run `claude -p` (it costs money).
> 
> Attack in particular:
> 1. Construct validity: does A (one 44k-token file) vs B (split ≤5k-token modules) actually measure "small files help agents", or something else (structure, naming, package layout, training-data familiarity)?
> 2. Statistical power: 2 arms × 4 tasks × N=3 = 24 trials, a 20% token-difference threshold. Is the decision rule sound? What noise should be expected? Is "success" with N=3 meaningful?
> 3. Confounds introduced by the split (who does it, how re-exports work, global state), by contamination (bottle in training data), and by the hidden tests.
> 4. Agent setup: only Bash/Read/Edit, no subagents, 20 max turns, 15 min, effort high, Haiku 5.5, --safe-mode with OAuth. Could the 20-turn cap or Read tool truncation of large files dominate the result? Does Read truncate a 4,566-line file?
> 5. Metric validity: total tokens including cache reads, "read a file over 5k tokens" flag, cost. Which metric actually answers the question? Are cache reads double-counted across turns?
> 6. The decision rule for running arm C and the hook validation cases.
> 7. Anything missing that would make the result unusable.
> 
> Output format: a numbered list of findings, ordered by severity (critical / major / minor). For each: the problem, evidence (file:line or command output), and a concrete fix. End with a short verdict: run as-is, run after fixes, or redesign.

## Output

1. **[Critical] A/B does not isolate file size.** B changes a module into a package, introduces import boundaries, re-exports, module names, source paths, initialization order, and navigation/name conventions. It therefore tests “single-file monolith versus package architecture,” not “same architecture with smaller files.” The split also changes `__module__`, `__file__`, pickling/introspection, dynamic imports, and stack traces.  
   **Evidence:** `README.md:15-17,38-45`; `bottle.py:3761-3779,4447-4488` relies on globals and dynamic module names.  
   **Fix:** Use multiple layouts with the same package topology, or compare controlled file-size variants while holding import structure and symbol ownership constant. Treat the split as a separate treatment and report it as such.

2. **[Critical] B is not behaviorally equivalent by construction.** Re-exporting names cannot preserve assignments to globals. `bottle.DEBUG`, `bottle.NORUN`, `TEMPLATE_PATH`, `HTTP_CODES`, `request`, and `response` are read internally by code that may live in other modules. Assigning through the package namespace can update only the re-export, not the defining module.  
   **Evidence:** `bottle.py:2844-2847`, `3770-3779`, `4030`, `4371-4373`, `4430-4492`; tests mutate globals at `test/test_wsgi.py:57-68`, `test/test_outputfilter.py:45`, and bind `bottle.request`/`bottle.response` at `test/test_contextlocals.py:22-41`.  
   **Fix:** Define and test an explicit shared-state mechanism before trials. Add equivalence tests for every public mutable global, dynamic import, error template, extension import, and `bottle.__file__` use. If equivalence requires refactoring, the experiment is no longer “move code only.”

3. **[Critical] The proposed task set is not yet valid, and one example contradicts the fixture.** The current route filter explicitly accepts negative integers: `r'-?\d+'`; an actual run matches `/-3` as `{'id': -3}`. The signed-cookie implementation already exists and has dedicated tests. “Signed cookies fail only in integration” and “config option affecting both request and response” are not reproducible specifications.  
   **Evidence:** `bottle.py:289-293`; command result: `Router.match('/-3')` returned `{'id': -3}`; `test/test_securecookies.py:12-40`.  
   **Fix:** Specify exact setup patches, expected old behavior, desired behavior, hidden-test cases, and affected public API before constructing fixtures. Verify each task fails before the agent runs and passes after the intended patch.

4. **[Critical] The stated execution limits may not be executable.** The command uses `--max-turns`, but `claude 2.1.296 --help` does not list that option. It also does not enforce a 15-minute timeout; the shell command has no timeout wrapper. `$MAX_TURNS` and `$EFFORT` are unspecified in the shown command.  
   **Evidence:** `README.md:66-71,119`; local `claude --help` output contains no `--max-turns`.  
   **Fix:** Run a trial-shaped command and fail the harness if any option is rejected. Enforce wall time externally, set explicit values in the runner, and record actual turns, timeout status, and exit reason.

5. **[Critical] Read-tool behavior creates a treatment confound.** Claude Code’s Read tool is line-limited (default roughly 2,000 lines), so a 4,566-line `bottle.py` cannot be read in one call. Arm A therefore forces chunked reads or Bash workarounds, while B offers many independently readable files. That is a real navigation/tool interaction treatment, not merely a token-size treatment.  
   **Evidence:** `README.md:36,88-91`; the fixture is 4,566 lines (`wc -l bottle.py`).  
   **Fix:** Decide whether the research question includes tool-level file navigation. If it does, measure reads/chunks and report that explicitly. If it does not, provide an equivalent indexed access interface or compare layouts under a controlled reading protocol.

6. **[Critical] N=3 per task has essentially no statistical power.** Each arm has only 12 trials, and each task has three binary observations. One success changes a task rate by 33 percentage points. There is no meaningful estimate of per-task pass probability, no confidence interval rule, and no defensible basis for “clearly higher” or “within noise.”  
   **Evidence:** `README.md:25-30,102-104`.  
   **Fix:** Predefine a statistical model and uncertainty interval, use substantially more independent repetitions, or label this strictly as a qualitative pilot. Do not make a keep/delete decision from raw N=3 rates.

7. **[Major] The 20% token rule is unsupported and ambiguously calculated.** “Expected noise” is asserted but not measured. The rule does not say mean versus median, whether comparisons are paired by task/repetition, how failures are counted, or whether a 20% reduction is relative to A’s mean, per-task ratios, or pooled totals. A single outlier can decide the result.  
   **Evidence:** `README.md:23-30`.  
   **Fix:** Pilot the same agent/tasks repeatedly to estimate variance, pre-register an estimand, use paired per-task comparisons, and report uncertainty rather than a naked threshold.

8. **[Major] “Total tokens including cache” is not a valid single context metric.** Cache-read tokens are repeated cached context, with different billing semantics from fresh input. Summing them can double-count identical context across turns and rewards or penalizes cache behavior rather than agent work. Cost, input tokens, output tokens, and peak context are different quantities.  
   **Evidence:** `README.md:94-100`; `README.md:86` already records cached system context.  
   **Fix:** Report fresh input tokens, cache-read tokens, cache-creation tokens, output tokens, peak context, tool-call count, and cost separately. Choose one primary endpoint before execution.

9. **[Major] The “read a file over 5,000 tokens” metric is not observable as specified.** It depends on transcript parsing, misses Bash reads unless command output is reconstructed, and treats one large read differently from ten equivalent chunks. It also does not measure how much of a file was actually useful to the model.  
   **Evidence:** `README.md:88-91,99`; search is explicitly performed through Bash.  
   **Fix:** Instrument all file-access paths, record byte/line ranges and returned output, and report total bytes/tokens exposed plus peak per-call exposure.

10. **[Major] Training contamination is not merely conservative toward A.** Bottle’s API and source organization may be familiar to the model, favoring A; conversely, B’s new module names and package layout may be unfamiliar. The direction and size of the bias are unknown. Agents can also use Bash network access unless the harness blocks it; “no WebFetch” does not establish no internet.  
    **Evidence:** `README.md:47,88-90`; only tool restriction is `Bash,Read,Edit`.  
    **Fix:** Disable network and restrict filesystem access. Use a less training-exposed fixture or measure the same experiment on multiple repositories and report contamination as a limitation.

11. **[Major] The split itself is an uncontrolled human/model intervention.** “An agent performs the split; a human reviews it” gives B extra construction work and an unquantified review process. A’s fixture needs no analogous intervention. The exact split quality, module names, re-export policy, and review changes are not standardized.  
    **Evidence:** `README.md:38-43,116-121`.  
    **Fix:** Freeze B as a reviewed artifact before task trials, publish the split manifest and diff, and count construction/review outside trial metrics. Use an independent equivalence test suite.

12. **[Major] Conditional arm C cannot measure hook effect.** C runs only after a favorable A/B result, so it is selected on the outcome it is later used to contextualize. There is no split/no-hook versus split/hook paired control, and no rule defines “hinders,” “helps,” or “similar.”  
    **Evidence:** `README.md:17-30`.  
    **Fix:** Pre-register C and run it regardless, with matched tasks and repetitions in B and C. Estimate the incremental hook effect separately from the file-size effect.

13. **[Major] The hook may never affect an agent task.** A pre-commit hook runs on commit, but the task instructions do not require staging or committing. With `Edit` and Bash available, an agent can finish without invoking the hook, making C identical to B.  
    **Evidence:** `README.md:106-114`; no commit requirement appears in the task or agent protocol.  
    **Fix:** Require a commit or explicit hook invocation as part of every C task, and record whether the hook actually ran and how many times.

14. **[Minor] Hook semantics are underspecified and the validation matrix is incomplete.** “Files not authored by agents” has no reliable definition. Exemptions by marker or extension are easy to spoof and unspecified for binary files, symlinks, renames, submodules, executable files, and staged mode changes. The rounding rule is explicitly left unresolved.  
    **Evidence:** `README.md:110-114`.  
    **Fix:** Specify exact exemption predicates, byte encoding, rounding/comparison (`bytes > 20,000`), and Git object cases; test them before C.

15. **[Minor] The fixture accounting is easy to misread.** `test/` contains 30 files total and 28 Python files; there are 27 `test_*.py` files. The README’s “27 files (~183 KB)” is only true under an unstated counting convention.  
    **Evidence:** `find test -maxdepth 1 -type f` returned 30; `find ... -name '*.py'` returned 28; Python files total 183,482 bytes.  
    **Fix:** State exactly which files are counted and how sizes are computed.

**Verdict: redesign.** The current pilot cannot support the stated causal claim or its decision rule. At minimum, freeze a behaviorally equivalent split, replace the task examples with verified injected defects, enforce the actual runtime limits, block network/filesystem escape, define valid token estimands, and use a pre-registered uncertainty analysis with more repetitions.
