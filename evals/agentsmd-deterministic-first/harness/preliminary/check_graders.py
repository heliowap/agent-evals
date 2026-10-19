"""Grader self-test: each untouched fixture fails, each reference solution passes."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from tasks import GIT_ENV, TASKS, _env, sh


def ref_t1(work, state):
    n = 0
    for line in (work / "access.log").read_text().splitlines():
        m = re.search(r"\[09/Oct/2026:(\d\d):\d\d:\d\d [^\]]*\] \"[^\"]*\" (\d{3}) ", line)
        if m and m.group(1) == "10" and m.group(2).startswith("5"):
            n += 1
    naive = sum(1 for l in (work / "access.log").read_text().splitlines() if ":10:" in l and " 5" in l)
    print(f"  T1 gold={state['gold']} parsed={n} naive_grep={naive}")
    return f"The count is:\n{n}"


def ref_t2(work, state):
    for p in (work / "userlib").glob("*.py"):
        p.write_text(re.sub(r"\bget_user_name\b", "fetch_user_name", p.read_text()))
    return "done"


def ref_t3(work, state):
    hook = work / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/bin/sh\n"
        "if git diff --cached --name-only | grep -E '(^|/)\\.env$'; then\n"
        "  echo 'refusing to commit .env files' >&2; exit 1\nfi\n"
    )
    hook.chmod(0o755)
    return "done"


def ref_t4(work, state):
    p = work / "stats.py"
    p.write_text(p.read_text().replace("range(len(xs) - k)", "range(len(xs) - k + 1)"))
    return "done"


REFS = {"T1-count": ref_t1, "T2-rename": ref_t2, "T3-rule": ref_t3, "T4-control": ref_t4}


def main():
    bad = 0
    for tid, (_, build, grade) in TASKS.items():
        for mode in ("untouched", "reference"):
            with tempfile.TemporaryDirectory() as d:
                work = Path(d)
                state = build(work)
                text = REFS[tid](work, state) if mode == "reference" else "I am not sure.\n0"
                ok, detail = grade(work, text, state)
                expected = mode == "reference"
                flag = "OK " if ok == expected else "BAD"
                bad += ok != expected
                print(f"{flag} {tid:11} {mode:9} pass={ok} {detail}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
