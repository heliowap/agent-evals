"""Verify every task in both arms: the hidden tests fail after setup and pass with
the reference solution, and the visible suite passes in both states.

Usage: python3 -B harness/verify_tasks.py --out DIR
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ARMS, TASK_IDS, apply_replacements, grade, load_task, prepare  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = pathlib.Path(ap.parse_args().out)
    out.mkdir(parents=True)
    results, ok = [], True
    for task_id in TASK_IDS:
        task = load_task(task_id)
        for arm in ARMS:
            work = out / f"{task_id}-{arm}"
            tree = prepare(task_id, arm, work / "repo")
            before = grade(task_id, tree, work)
            apply_replacements(tree, task["reference"])
            after = grade(task_id, tree, work)
            good = (not before["hidden"]["ok"] and before["visible"]["ok"] and after["pass"])
            ok &= good
            results.append({"task": task_id, "arm": arm, "ok": good,
                            "before_hidden": before["hidden"]["summary"],
                            "before_visible": before["visible"]["summary"],
                            "before_visible_failures": before["visible"]["failures"],
                            "after_hidden": after["hidden"]["summary"],
                            "after_visible": after["visible"]["summary"]})
            print(f"{'OK ' if good else 'BAD'} {task_id} {arm}: before hidden "
                  f"[{before['hidden']['summary']}] after hidden [{after['hidden']['summary']}] "
                  f"visible [{after['visible']['summary']}]")
    (out / "verify.json").write_text(json.dumps({"ok": ok, "results": results}, indent=2) + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
