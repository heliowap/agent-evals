"""Freeze two public Click review cases. One-off benchmark preparation."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = [
    {
        "id": "click-3773",
        "base": "150d1071d69c5cdad7de78590013ffe56cf9e3bb",
        "head": "20fff386596bc1a3d92e3b5c47c81e3f17083da6",
        "spec": """Source: https://github.com/pallets/click/issues/3362
The issue reports: "If an option containing a hyphen in its name is printed at the line break limit, it’s broken at the hyphen."
Its HelpFormatter(width=65) reproduction expects the usage lines to contain intact options:
  --max-retry-count --disable-cache-mode
  --config-file-location --user-auth-token
Actual output splits `--max-\n               retry-count` and `--config-file-\n               location`.
The request concerns help usage wrapping, not all text formatting.
""",
        "standard_ranges": [(".github/pull_request_template.md", 16, 26), ("docs/contributing.md", 33, 41)],
        "context_ranges": [("src/click/_textwrap.py", 33, 55), ("src/click/formatting.py", 60, 76)],
        "sources": ["https://github.com/pallets/click/pull/3773", "https://github.com/pallets/click/issues/3362"],
    },
    {
        "id": "click-3868",
        "base": "6aabf099bfdd4c1e75fe8d0e0d4241372b988ab1",
        "head": "425104296015c9ffb63fbbe4d9db12d3ae0ef12a",
        "spec": """Sources: https://github.com/pallets/click/issues/3840 and https://github.com/pallets/click/pull/3868
The issue reports that `click.edit()` intermittently fails to launch `notepad.exe` on Windows with WinError 87 or 14001.
The PR states: "Use `_split_editor_command` on Windows to split in non-POSIX mode preserving backslashes while respecting quotes."
It also proposes resolving the editor executable with `shutil.which` and adding regression tests.
Assess both the original issue and the PR's stated solution. Do not assume actual Windows process-launch behavior without evidence.
""",
        "standard_ranges": [("docs/contributing.md", 33, 43), (".github/pull_request_template.md", 16, 26)],
        "context_ranges": [("src/click/_termui_impl.py", 683, 710), ("src/click/_termui_impl.py", 730, 770)],
        "sources": ["https://github.com/pallets/click/pull/3868", "https://github.com/pallets/click/issues/3840"],
    },
]


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def excerpt(repo, name, start, end):
    lines = (repo / name).read_text().splitlines()
    return f"{name} (lines {start}-{end}):\n" + "\n".join(
        f"{i}: {lines[i - 1]}" for i in range(start, min(end, len(lines)) + 1)
    )


def prepare():
    frozen = []
    for case in CASES:
        repo = ROOT / ".fixtures" / case["id"]
        assert git(repo, "rev-parse", "HEAD") == case["head"]
        assert git(repo, "rev-parse", case["base"]) == case["base"]
        diff = git(repo, "diff", f"{case['base']}...HEAD")
        assert diff.startswith("diff --git")
        frozen.append({
            "id": case["id"],
            "base": case["base"],
            "head": case["head"],
            "diff_command": f"git diff {case['base']}...HEAD",
            "commits": git(repo, "log", f"{case['base']}..HEAD", "--oneline"),
            "diff": diff,
            "spec": case["spec"],
            "standards": "\n\n".join(excerpt(repo, *part) for part in case["standard_ranges"]),
            "context": "\n\n".join(excerpt(repo, *part) for part in case["context_ranges"]),
            "sources": case["sources"],
        })
    (ROOT / "fixtures.json").write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n")
    print("Frozen", len(frozen), "cases")


if __name__ == "__main__":
    prepare()
