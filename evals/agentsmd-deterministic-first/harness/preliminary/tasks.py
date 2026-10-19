"""Task fixtures and deterministic graders.

build(work) creates the fixture in an empty directory and returns the private
state the grader needs (kept outside the agent's workdir).
grade(work, final_text, state) returns (passed, detail).
"""

import random
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def sh(args, cwd, **kw):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, **kw)


GIT_ENV = {
    "GIT_AUTHOR_NAME": "eval",
    "GIT_AUTHOR_EMAIL": "eval@example.invalid",
    "GIT_COMMITTER_NAME": "eval",
    "GIT_COMMITTER_EMAIL": "eval@example.invalid",
}


def git_init(work):
    sh(["git", "init", "-q", "-b", "main"], work)
    sh(["git", "add", "-A"], work)
    sh(["git", "commit", "-q", "-m", "initial"], work, env={**_env(), **GIT_ENV})


def _env():
    import os

    return dict(os.environ)


# T1-count: 5xx responses in a time window. Decoys: 5xx-looking numbers in the
# path and in the byte count, and 5xx statuses just outside the window.

T1_PROMPT = (
    "In access.log, how many requests got a 5xx status code with a timestamp "
    "from 10:00:00 (inclusive) to 11:00:00 (exclusive) on 09/Oct/2026? "
    "End your reply with the number alone on the last line."
)


def t1_build(work):
    rng = random.Random(20261009)
    start = datetime(2026, 10, 9, 8, 0, 0)
    lines, gold = [], 0
    paths = ["/", "/items/{}", "/api/v1/orders/{}", "/search?q=x{}", "/static/app.{}.js"]
    statuses = [200] * 70 + [201, 204, 301, 302, 304, 400, 401, 403, 404, 404, 429] + [500, 502, 503, 504] * 3
    for _ in range(3000):
        t = start + timedelta(seconds=rng.randrange(6 * 3600))
        status = rng.choice(statuses)
        path = rng.choice(paths).format(rng.choice([rng.randrange(1, 999), 500, 503, 502]))
        size = rng.choice([rng.randrange(100, 99999), 500, 503, 5040])
        ip = f"10.{rng.randrange(256)}.{rng.randrange(256)}.{rng.randrange(1, 255)}"
        ts = t.strftime("%d/%b/%Y:%H:%M:%S +0000")
        lines.append((t, f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {size} "-" "curl/8.4"'))
        if 500 <= status <= 599 and t.hour == 10:
            gold += 1
    for t, s in [(datetime(2026, 10, 9, 9, 59, 59), 500), (datetime(2026, 10, 9, 11, 0, 0), 503)]:
        ts = t.strftime("%d/%b/%Y:%H:%M:%S +0000")
        lines.append((t, f'10.0.0.1 - - [{ts}] "GET /edge HTTP/1.1" {s} 512 "-" "curl/8.4"'))
    lines.sort(key=lambda x: x[0])
    (work / "access.log").write_text("\n".join(l for _, l in lines) + "\n")
    return {"gold": gold}


def t1_grade(work, final_text, state):
    last = final_text.strip().splitlines()[-1].strip() if final_text.strip() else ""
    m = re.fullmatch(r"\**`?(\d[\d,]*)`?\**\.?", last)
    got = int(m.group(1).replace(",", "")) if m else None
    return got == state["gold"], f"gold={state['gold']} got={got!r} last_line={last[:80]!r}"


# T2-rename: bulk rename across a package without touching the _legacy sibling.

T2_PROMPT = (
    "Rename the function get_user_name to fetch_user_name everywhere in this "
    "repository (definition and all call sites). Do not change "
    "get_user_name_legacy. The tests must pass."
)

T2_MODULES = 12


def t2_build(work):
    pkg = work / "userlib"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "core.py").write_text(
        "def get_user_name(user):\n"
        "    return user['first'] + ' ' + user['last']\n\n\n"
        "def get_user_name_legacy(user):\n"
        "    return user['last'] + ', ' + user['first']\n"
    )
    for i in range(T2_MODULES):
        (pkg / f"feature_{i:02d}.py").write_text(
            "from userlib.core import get_user_name, get_user_name_legacy\n\n\n"
            f"def greet_{i}(user):\n"
            f"    return 'Hi {i}, ' + get_user_name(user)\n\n\n"
            f"def label_{i}(user):\n"
            f"    return get_user_name(user).upper() + ' / ' + get_user_name_legacy(user)\n"
        )
    tests = work / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("")
    calls = "\n".join(
        f"        self.assertEqual(feature_{i:02d}.greet_{i}(U), 'Hi {i}, Ada Lovelace')"
        for i in range(T2_MODULES)
    )
    imports = ", ".join(f"feature_{i:02d}" for i in range(T2_MODULES))
    (tests / "test_users.py").write_text(
        "import unittest\n"
        f"from userlib import {imports}\n"
        "from userlib.core import fetch_user_name, get_user_name_legacy\n\n"
        "U = {'first': 'Ada', 'last': 'Lovelace'}\n\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_names(self):\n"
        "        self.assertEqual(fetch_user_name(U), 'Ada Lovelace')\n"
        "        self.assertEqual(get_user_name_legacy(U), 'Lovelace, Ada')\n"
        "    def test_features(self):\n"
        f"{calls}\n"
        "        self.assertEqual(feature_00.label_0(U), 'ADA LOVELACE / Lovelace, Ada')\n"
    )
    git_init(work)
    src = "\n".join(p.read_text() for p in sorted(pkg.glob("*.py")))
    return {
        "legacy": len(re.findall(r"\bget_user_name_legacy\b", src)),
        "renamed": len(re.findall(r"\bget_user_name\b", src)),
        "tests": (tests / "test_users.py").read_text(),
    }


def t2_grade(work, final_text, state):
    (work / "tests" / "test_users.py").write_text(state["tests"])
    src = "\n".join(p.read_text() for p in sorted((work / "userlib").glob("*.py")))
    old = len(re.findall(r"\bget_user_name\b", src))
    new = len(re.findall(r"\bfetch_user_name\b", src))
    legacy = len(re.findall(r"\bget_user_name_legacy\b", src))
    t = sh(["python3", "-m", "unittest", "-q"], work)
    ok = old == 0 and new == state["renamed"] and legacy == state["legacy"] and t.returncode == 0
    return ok, f"old={old} new={new}/{state['renamed']} legacy={legacy}/{state['legacy']} tests_rc={t.returncode}"


# T3-rule: "make sure" means committing a .env file must fail or be ignored.

T3_PROMPT = "Make sure nobody can commit .env files in this repository."


def t3_build(work):
    (work / "README.md").write_text("# service\n\nA small service.\n")
    (work / "AGENTS.md").write_text("# Agent notes\n\n- Keep functions small.\n")
    (work / "app.py").write_text("print('hello')\n")
    git_init(work)
    return {"agents_md": (work / "AGENTS.md").read_text()}


def t3_grade(work, final_text, state):
    kinds = []
    hooks_path = sh(["git", "config", "--get", "core.hooksPath"], work).stdout.strip()
    hook_dir = work / hooks_path if hooks_path else work / ".git" / "hooks"
    if any(p.is_file() and not p.name.endswith(".sample") for p in hook_dir.glob("pre-commit*")):
        kinds.append("hook")
    gi = work / ".gitignore"
    if gi.exists() and ".env" in gi.read_text():
        kinds.append("gitignore")
    agents = work / "AGENTS.md"
    if agents.exists() and agents.read_text() != state["agents_md"]:
        kinds.append("agents_md")
    probes = [work / ".env", work / "backend" / ".env"]
    for p in probes:
        p.parent.mkdir(exist_ok=True)
        p.write_text("SECRET=1\n")
    env = {**_env(), **GIT_ENV}
    sh(["git", "add", "-A"], work, env=env)
    sh(["git", "commit", "-q", "-m", "probe"], work, env=env)
    tracked = sh(["git", "ls-tree", "-r", "--name-only", "HEAD"], work).stdout.split()
    leaked = [n for n in tracked if n in (".env", "backend/.env")]
    return not leaked, f"kinds={kinds or ['none']} leaked={leaked}"


# T4-control: off-by-one bug, unrelated to the section.

T4_PROMPT = "The tests in this repository fail. Fix the bug."


def t4_build(work):
    (work / "stats.py").write_text(
        "def moving_sum(xs, k):\n"
        "    \"\"\"Sum of each window of k consecutive items.\"\"\"\n"
        "    return [sum(xs[i:i + k]) for i in range(len(xs) - k)]\n"
    )
    (work / "test_stats.py").write_text(
        "import unittest\nfrom stats import moving_sum\n\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_windows(self):\n"
        "        self.assertEqual(moving_sum([1, 2, 3, 4], 2), [3, 5, 7])\n"
        "        self.assertEqual(moving_sum([5], 1), [5])\n"
        "        self.assertEqual(moving_sum([1, 2], 3), [])\n"
    )
    git_init(work)
    return {"tests": (work / "test_stats.py").read_text()}


def t4_grade(work, final_text, state):
    (work / "test_stats.py").write_text(state["tests"])
    t = sh(["python3", "-m", "unittest", "-q", "test_stats"], work)
    return t.returncode == 0, f"tests_rc={t.returncode}"


TASKS = {
    "T1-count": (T1_PROMPT, t1_build, t1_grade),
    "T2-rename": (T2_PROMPT, t2_build, t2_grade),
    "T3-rule": (T3_PROMPT, t3_build, t3_grade),
    "T4-control": (T4_PROMPT, t4_build, t4_grade),
}
