"""Paths, trial preparation and grading shared by the harness commands."""
import json
import os
import pathlib
import re
import shutil
import subprocess

PKG = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = PKG / "tasks"
FIXTURE_DIR = PKG / "build" / "fixture"
VENV = PKG / ".venv"
PYTHON = VENV / "bin" / "python"
TASK_IDS = ["t1-basic-auth-colon", "t2-mount-multisegment", "t3-uuid-filter", "t4-request-id"]
ARMS = ["a", "b"]
FIXTURE_MTIME = 1791590400  # 2026-10-10T00:00:00Z

GIT_ENV = {"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-10-10T00:00:00Z"}

# One sentence per arm, appended to every task prompt, so both arms know where the code is.
LAYOUT = {
    "a": "The bottle source code is in `bottle.py` and the tests are in `test/`. "
         "Run the tests with `python -m pytest test`.",
    "b": "The bottle source code is in the `bottle/` package: `bottle/__init__.py` executes the "
         "numbered files in `bottle/` in order, in one shared module namespace, so together they "
         "form the `bottle` module. The tests are in `test/`. "
         "Run the tests with `python -m pytest test`.",
}


def load_task(task_id):
    task = json.loads((TASKS_DIR / task_id / "task.json").read_text())
    task["prompt"] = (TASKS_DIR / task_id / "prompt.md").read_text().strip()
    return task


def prompt_for(task, arm):
    return task["prompt"] + "\n\n" + LAYOUT[arm]


def source_files(tree):
    return sorted(p for p in pathlib.Path(tree).rglob("*.py")
                  if not {".git", "test", "__pycache__"} & set(p.relative_to(tree).parts))


def apply_replacements(tree, pairs):
    """Apply (old, new) pairs; each old string must occur exactly once in the source files."""
    for old, new in pairs:
        hits = [(p, p.read_text(encoding="utf-8").count(old)) for p in source_files(tree)]
        hits = [(p, n) for p, n in hits if n]
        if len(hits) != 1 or hits[0][1] != 1:
            raise ValueError(f"{old[:60]!r}: expected one occurrence, found {hits}")
        path = hits[0][0]
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def git(tree, *args, capture=False):
    env = {**os.environ, **GIT_ENV}
    r = subprocess.run(["git", "-C", str(tree), *args], check=True, env=env,
                       capture_output=capture, text=True)
    return r.stdout if capture else None


def prepare(task_id, arm, dest):
    """Clone the arm fixture to dest and apply the task setup inside the single commit,
    so the injected bug does not show up in git history."""
    dest = pathlib.Path(dest)
    subprocess.run(["git", "clone", "-q", str(FIXTURE_DIR / arm), str(dest)], check=True)
    git(dest, "remote", "remove", "origin")
    task = load_task(task_id)
    if task["setup"]:
        apply_replacements(dest, task["setup"])
        git(dest, "commit", "-q", "-a", "--amend", "--no-edit", "--reset-author")
    # A fresh clone has mtime "now", which makes the upstream test
    # test_sendfile.py::TestSendFile::test_ims flaky (it assumes the file is
    # older than the current second). Pin every file to the fixture date.
    for p in dest.rglob("*"):
        if ".git" not in p.relative_to(dest).parts:
            os.utime(p, (FIXTURE_MTIME, FIXTURE_MTIME), follow_symlinks=False)
    return dest


def run_pytest(tree, targets, timeout=300):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        r = subprocess.run([str(PYTHON), "-m", "pytest", "-q", "-rfE", "-p", "no:cacheprovider", *targets],
                           cwd=tree, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "passed": 0, "failed": 0, "summary": "timeout"}
    lines = r.stdout.strip().splitlines()
    summary = lines[-1] if lines else r.stderr.strip()[-200:]
    count = lambda word: int(m.group(1)) if (m := re.search(rf"(\d+) {word}", summary)) else 0
    failures = [l.split(" ", 1)[1].split(" - ")[0] for l in lines if l.startswith(("FAILED ", "ERROR "))]
    return {"ok": r.returncode == 0, "passed": count("passed"),
            "failed": count("failed") + count("error"), "summary": summary, "failures": failures}


def grade(task_id, tree, workdir):
    """Grade the final state of tree on a copy, so the agent's directory stays untouched."""
    copy = pathlib.Path(workdir) / "graded"
    shutil.copytree(tree, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    tests = copy / "test"
    shutil.copy2(TASKS_DIR / "hidden_support.py", tests / "hidden_support.py")
    shutil.copy2(TASKS_DIR / task_id / "test_hidden.py", tests / "test_hidden.py")
    hidden = run_pytest(copy, ["test/test_hidden.py"])
    visible = run_pytest(copy, ["test", "--ignore=test/test_hidden.py"])
    shutil.rmtree(copy)
    return {"pass": hidden["ok"] and visible["ok"], "hidden": hidden, "visible": visible}
