> English translation of [grading-rubric.md](grading-rubric.md). The original is kept verbatim as an archived artifact.

# Predefined answer key for the review test

The four findings below were fixed before reading the responses. Each case has one **Spec** finding and one **Standards** finding; scoring does not mix the axes. The research and primary sources are in `fixture-research.md`; the blind prompts are in `fixtures.json` and in the files under `results/`.

| Case | Axis | Verifiable finding (1 point) |
| --- | --- | --- |
| [Click #3773](https://github.com/pallets/click/pull/3773) | Spec | `break_on_hyphens = False` was added as a class attribute, but `textwrap.TextWrapper.__init__` creates the **instance** attribute with the default `True`; the example from [issue #3362](https://github.com/pallets/click/issues/3362) still breaks `--max-retry-count` and `--config-file-location`. |
| Click #3773 | Standards | The diff adds no regression test that fails without the change, contrary to the [.github/pull_request_template.md](https://github.com/pallets/click/blob/20fff386596bc1a3d92e3b5c47c81e3f17083da6/.github/pull_request_template.md#L18-L21). |
| [Click #3868](https://github.com/pallets/click/pull/3868) | Spec | The PR's promise to respect quotes in the editor command line is not fulfilled for quotes **inside** an argument: with `WIN=True`, `C:\tools\vim.exe --arg="a b"` produces three tokens, `['C:\\tools\\vim.exe', '--arg="a', 'b"']`, not two. Do not infer from this that the original `notepad` failure persists, nor that the real launch was tested on Windows. |
| Click #3868 | Standards | The `t[1:-1] if ... else t` added to `_termui_impl.py` contradicts the express prohibition of ternary expressions in [docs/contributing.md](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38). |

## Scoring and cautions

- Count a hit only if the response identifies the **concrete cause**, on the right axis, with the affected location; a generic comment about tests, quotes or `textwrap` is not enough. Each axis/case is worth 0 or 1.
- Count verifiably incorrect claims separately as false positives: for example, saying that #3773 changed all text wrapping (the added configuration has no effect) or that #3868 proved a `CreateProcess` failure on Windows (the reproduction covers only parsing). Do not automatically mark other plausible findings as false positives: first adjudicate the evidence.
- Record omissions, off-axis findings, call failures, provider-reported cost in USD and observed duration. `high` and `max` measure two configurations of each model, not two independent repetitions. Two diffs from a single project do not justify statistical generalization.
- No effort variant is advertised for `opencode/mimo-v2.6-flash-free`; it enters only in the default configuration. `opencode/space-bunny-free` enters at `xhigh` and `max`, without attributing a definitive identity to the stealth model.
