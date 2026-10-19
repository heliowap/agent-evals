"""Live isolation probe (one cheap model call). Usage: python3 probe_isolation.py [workroot] [provider/model]"""
import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from sandbox import build_env, make_snapshot

MODEL = os.environ.get("PROBE_MODEL", "opencode-go/glm-5.3-flash")
MSG = "List every skill name you can load, one per line, nothing else."
SKILL = """---
name: code-review
description: Review a pull request. Load this whenever asked to review code.
---
Reply with the single word CANARY-SKILL-OK when asked for your skill list.
"""
USER_SKILL_DIRS = [Path.home() / ".agents/skills", Path.home() / ".claude/skills", Path.home() / ".config/opencode/skills"]


def run(cmd, cwd, env=None, timeout=300):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def user_skill_names():
    names = set()
    for d in USER_SKILL_DIRS:
        if d.is_dir():
            names |= {p.parent.name for p in d.rglob("SKILL.md")}
            names |= {p.stem for p in d.glob("*.md")}
    return names - {"code-review"}


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="probe-"))
    src = root / "src"
    src.mkdir(parents=True)
    g = lambda *a: run(["git", *a], src).stdout.strip()
    g("init", "-q", "-b", "main")
    (src / "a.py").write_text("x = 1\n"); g("add", "."); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    base = g("rev-parse", "HEAD")
    (src / "a.py").write_text("x = 2\n"); g("add", "."); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "change")
    head = g("rev-parse", "HEAD")
    snap = make_snapshot(src, base, head, root / "snap")
    env = build_env(snap, SKILL)

    r = run(["opencode", "run", "--standalone", "--agent", "reviewer", "--model", MODEL, "--format", "json", MSG], snap, env)
    (root / "run.jsonl").write_text(r.stdout)
    (root / "run.stderr").write_text(r.stderr)
    events = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]
    sid = next((e.get("sessionID") for e in events if e.get("sessionID")), None)
    text = "\n".join(json.dumps(e) for e in events)
    assert sid, f"no sessionID; rc={r.returncode} stderr={r.stderr[-800:]}"
    ex = run(["opencode", "session", "export", "--standalone", sid], snap, env)
    (root / "export.json").write_text(ex.stdout)

    leaked_out = sorted(n for n in user_skill_names() if n in text)
    leaked_export = sorted(n for n in user_skill_names() if f'"{n}"' in ex.stdout or f"<id>{n}</id>" in ex.stdout)
    result = {
        "session": sid,
        "rc": r.returncode,
        "code_review_in_output": "code-review" in text,
        "leaked_user_skills_in_output": leaked_out,
        "leaked_user_skills_in_export": leaked_export,
        "superpowers_in_export": "superpowers" in ex.stdout.lower(),
        "workroot": str(root),
    }
    print(json.dumps(result, indent=1))
    ok = result["code_review_in_output"] and not leaked_out and not leaked_export and not result["superpowers_in_export"]
    print("PROBE", "CLEAN" if ok else "LEAK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
