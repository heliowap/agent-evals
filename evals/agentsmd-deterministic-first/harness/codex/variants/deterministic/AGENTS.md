Deterministic first

- **Rules.** When a rule can be enforced by a guardrail (a plugin, a
  permission or policy, a git hook, a linter, a test), build the guardrail
  instead of writing the rule into `AGENTS.md`, a skill or an agent file, and
  tell the user which guardrail you built and why. When building one falls
  outside the task, propose it at the end instead. Written rules are for
  judgment calls no guardrail can check.
- **Actions.** When a program can produce the output (a count, a
  calculation, a search, a bulk edit, a format or schema conversion), compute
  it with a tool or a script instead of generating it. Prefer the project's
  own tools, then a configuration of them, then a new script; run a new
  script on a sample or check its diff before trusting it. Script a step the
  second time it repeats. One-off scripts go in the temp directory; tell the
  user before adding a permanent script or tool to a repository or config.
  Run independent commands in parallel.
