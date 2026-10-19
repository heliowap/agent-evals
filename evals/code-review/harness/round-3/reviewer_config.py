"""Verbatim copies of the production reviewer config.

Source: <user>/gh-agents @ aac254a
- REVIEWER_AGENT: agents/opencode.json -> agent.reviewer
- REVIEW_PROMPT: .github/workflows/agents.yml, step `id: review`, `with.prompt`
- ACTION_CONFIG_CONTENT: same step, `env.OPENCODE_CONFIG_CONTENT`
"""

REVIEWER_AGENT = {
    "mode": "primary",
    "description": "Automatic PR review in CI: BLOCKING/WARNING/NIT format, path:line findings, never approves, never edits.",
    "model": "opencode-go/glm-5.3-flash",
    "permission": {
        "edit": "deny",
        "webfetch": "deny",
        "websearch": "deny",
        "bash": {
            "*": "deny",
            "git diff*": "allow",
            "git log*": "allow",
            "git show*": "allow",
            "git rev-parse*": "allow",
            "git merge-base*": "allow",
            "gh pr view*": "allow",
            "gh pr diff*": "allow",
            "gh issue view*": "allow"
        }
    },
    "prompt": "You are the automated reviewer for this pull request. Load the `code-review` skill and apply it: the fixed point is the PR base (merge-base with the target branch); the spec comes from the PR body and the issues it references. Read the repo's AGENTS.md/CONTRIBUTING.md if present. Required output: one comment with BLOCKING, WARNING and NIT sections, `path:line` on every finding, and a final line `SUMMARY: N BLOCKING, N WARNING, N NIT`. Skip files under `docs/` and `*.md` unless they are the subject of the change. Never approve, never request changes formally, never edit files: you comment, a human decides. Write in the language the repo uses for review comments (default: English)."
}

REVIEW_PROMPT = 'Review this pull request. Output one review with three sections —\n`BLOCKING`, `WARNING`, `NIT` — each finding as `path:line` plus why\nit matters, `(none)` under empty sections, and a final line exactly\n`SUMMARY: <n> BLOCKING, <n> WARNING, <n> NIT`. Do not edit files.\n'

ACTION_CONFIG_CONTENT = '{"default_agent":"reviewer","permission":{"edit":"deny"}}'
