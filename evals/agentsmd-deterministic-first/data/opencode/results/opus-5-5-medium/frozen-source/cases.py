"""Synthetic task fixtures. Gold state stays with the controller, outside work/."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys


CASES = {
    "count": {
        "group": "actions",
        "prompts": ["Count requests in access.log with status 500–599 and timestamp on 2026-10-09 from 10:00:00 inclusive to 11:00:00 exclusive. Write the integer to answer.txt."],
        "behavior": "Compute from status and timestamp fields, not decoy numbers."},
    "money": {
        "group": "actions",
        "prompts": ["In invoices.csv, total amount_cents for paid rows with currency BRL. Write only the integer total to answer.txt."],
        "behavior": "Compute the filtered total without rounding or omissions."},
    "convert": {
        "group": "actions",
        "prompts": ["Convert customers.csv to customers.json as an array in original row order. Keep id and note as strings, including leading zeros and embedded newlines. Convert active to a boolean and blank age to null, otherwise an integer."],
        "behavior": "Use a parser; preserve types, quoting, Unicode and multiline fields."},
    "rename": {
        "group": "actions",
        "prompts": ["Rename get_user_name to fetch_user_name throughout userlib, including definitions, imports and calls. Preserve get_user_name_legacy and all current behavior."],
        "behavior": "Bulk change exact identifiers; verify sample or diff."},
    "project_tool": {
        "group": "actions",
        "prompts": ["Produce report.json from orders.json using this project's order-report contract. The available interface is documented in README.md."],
        "behavior": "Prefer the existing project command to reimplementing it."},
    "repeat": {
        "group": "actions",
        "prompts": ["For batch-a.csv, count rows whose state is ready by region. Save a JSON object to a-summary.json.", "Now do the same for batch-b.csv and batch-c.csv, saving b-summary.json and c-summary.json."],
        "behavior": "Reuse automation by the second step; keep one-off scripts temporary."},
    "guardrail": {
        "group": "rules",
        "prompts": ["Prevent future uses of Python's eval builtin in src from passing this repository's standard check. The existing check is documented in README.md. Ordinary comments, strings and obj.eval method calls must remain valid."],
        "behavior": "Enforce a rule through the existing checker/config rather than prose."},
    "regression": {
        "group": "rules",
        "prompts": ["clamp(value, low, high) should reject low > high with ValueError. Fix this recurring defect and make sure our standard unittest command catches it if someone reintroduces it. Preserve behavior for valid bounds."],
        "behavior": "Deliver a working guardrail; a written warning cannot pass."},
    "out_of_scope": {
        "group": "controls",
        "prompts": ["Review parser.py for a concrete defect in parse_enabled. Values other than the exact strings true and false should raise ValueError. Do not change any files. Explain the defect and recommend how to prevent recurrence."],
        "behavior": "Propose a guardrail, without building it in a read-only review."},
    "judgment": {
        "group": "controls",
        "prompts": ["Rewrite only message.md to explain a delayed export in a calm, concise tone. Preserve every fact. This is a one-time wording change."],
        "behavior": "Use judgment; avoid mechanizing a subjective tone preference."},
    "independent": {
        "group": "actions",
        "prompts": ["Run the three independent health checks in checks/ and write their actual returned values as a JSON object in health.json, keyed alpha, beta and gamma."],
        "behavior": "Run independent commands concurrently; preserve actual outputs."},
    "dependent": {
        "group": "controls",
        "prompts": ["Change settings.json mode to strict, regenerate manifest.json with python3 generate.py, then verify it with python3 verify.py. Both generated content and verification must correspond to the new setting."],
        "behavior": "Keep dependent edit, generation and verification in order."},
}


def write(work, name, text):
    p = work / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def snapshot(work):
    return {str(p.relative_to(work)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(work.rglob("*")) if p.is_file()
            and ".git" not in p.relative_to(work).parts
            and "__pycache__" not in p.relative_to(work).parts}


def build(case, work):
    rng = random.Random(20261010)
    gold = {}
    if case == "count":
        lines, count = [], 0
        for i in range(1400):
            hour, minute, second = rng.randrange(9, 12), rng.randrange(60), rng.randrange(60)
            status = rng.choice([200, 201, 404, 429, 500, 502, 599, 600])
            lines.append(f"2026-10-09T{hour:02}:{minute:02}:{second:02}Z GET /item/500 {status} 503")
            count += 10 <= hour < 11 and 500 <= status <= 599
        lines += ["2026-10-09T10:00:00Z GET / 500 0", "2026-10-09T11:00:00Z GET / 500 0"]
        write(work, "access.log", "\n".join(lines) + "\n")
        gold = {"answer.txt": str(count + 1)}
    elif case == "money":
        rows, total = ["id,state,currency,amount_cents"], 0
        for i in range(950):
            state, currency, amount = rng.choice(["paid", "void", "pending"]), rng.choice(["BRL", "USD"]), rng.randrange(-9500, 900000)
            rows.append(f"{i},{state},{currency},{amount}")
            if state == "paid" and currency == "BRL":
                total += amount
        write(work, "invoices.csv", "\n".join(rows) + "\n")
        gold = {"answer.txt": str(total)}
    elif case == "convert":
        rows = [{"id": f"{i:05}", "note": ["olá, mundo", 'a "quote"', "two\nlines", ""][i % 4],
                 "active": i % 3 == 0, "age": None if i % 4 == 0 else i % 90} for i in range(87)]
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=["id", "note", "active", "age"])
        writer.writeheader()
        writer.writerows({**r, "active": str(r["active"]).lower(), "age": "" if r["age"] is None else r["age"]} for r in rows)
        write(work, "customers.csv", stream.getvalue())
        gold = {"customers.json": rows}
    elif case == "rename":
        write(work, "userlib/__init__.py", "")
        write(work, "userlib/core.py", "def get_user_name(user):\n    return user['first'] + ' ' + user['last']\n\ndef get_user_name_legacy(user):\n    return user['last'] + ', ' + user['first']\n")
        for i in range(8):
            write(work, f"userlib/feature_{i}.py", "from userlib.core import get_user_name, get_user_name_legacy\n\ndef label(user):\n    return get_user_name(user) + ' / ' + get_user_name_legacy(user)\n")
    elif case == "project_tool":
        orders = [{"id": i, "state": rng.choice(["paid", "pending"]), "cents": rng.randrange(9999)} for i in range(180)]
        write(work, "orders.json", json.dumps(orders))
        write(work, "README.md", "# Order report\n\nRun `python3 report_orders.py orders.json report.json`. It counts paid orders and sums their cents.\n")
        write(work, "report_orders.py", "import json, sys\nrows = json.load(open(sys.argv[1]))\nrows = [r for r in rows if r['state'] == 'paid']\njson.dump({'count': len(rows), 'cents': sum(r['cents'] for r in rows)}, open(sys.argv[2], 'w'))\n")
        paid = [r for r in orders if r["state"] == "paid"]
        gold = {"report.json": {"count": len(paid), "cents": sum(r["cents"] for r in paid)}}
    elif case == "repeat":
        for batch in "abc":
            rows, counts = ["region,state"], {}
            for _ in range(120):
                region, state = rng.choice(["NE", "SE", "N", "S"]), rng.choice(["ready", "blocked"])
                rows.append(f"{region},{state}")
                if state == "ready":
                    counts[region] = counts.get(region, 0) + 1
            write(work, f"batch-{batch}.csv", "\n".join(rows) + "\n")
            gold[f"{batch}-summary.json"] = counts
    elif case == "guardrail":
        write(work, "README.md", "# Checks\n\nRun `python3 check.py`. Policy is in checks.json.\n")
        write(work, "checks.json", '{"forbidden_builtins": []}\n')
        write(work, "check.py", "import ast, json, pathlib, sys\nforbidden = set(json.load(open('checks.json'))['forbidden_builtins'])\nbad = []\nfor p in pathlib.Path('src').rglob('*.py'):\n    for n in ast.walk(ast.parse(p.read_text())):\n        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in forbidden:\n            bad.append(str(p))\nprint('\\n'.join(bad))\nsys.exit(bool(bad))\n")
        write(work, "src/app.py", "def identity(x):\n    return x\n")
    elif case == "regression":
        write(work, "bounds.py", "def clamp(value, low, high):\n    return max(low, min(high, value))\n")
        write(work, "test_bounds.py", "import unittest\nfrom bounds import clamp\n\nclass BoundsTest(unittest.TestCase):\n    def test_valid(self):\n        self.assertEqual(clamp(5, 0, 10), 5)\n        self.assertEqual(clamp(-2, 0, 10), 0)\n        self.assertEqual(clamp(12, 0, 10), 10)\n")
        write(work, "README.md", "# Bounds\n\nStandard check: `python3 -m unittest discover -v`.\n")
    elif case == "out_of_scope":
        write(work, "parser.py", "def parse_enabled(value):\n    return bool(value)\n")
    elif case == "judgment":
        write(work, "message.md", "The export scheduled for 14:00 UTC is delayed. It will be ready by 16:00 UTC. Existing data is unaffected. We will send an email when it is ready. THIS IS A DELAY, DO NOT PANIC.\n")
    elif case == "independent":
        for name, value in [("alpha", 17), ("beta", 29), ("gamma", 43)]:
            write(work, f"checks/{name}.py", f"import json, time\nstart = time.monotonic_ns()\ntime.sleep(0.2)\nend = time.monotonic_ns()\nopen('{name}-timing.json', 'w').write(json.dumps([start, end]))\nprint({value})\n")
        gold = {"health.json": {"alpha": 17, "beta": 29, "gamma": 43}}
    elif case == "dependent":
        write(work, "settings.json", '{"mode": "permissive"}\n')
        write(work, "generate.py", "import json, hashlib\nraw = open('settings.json', 'rb').read()\njson.dump({'mode': json.loads(raw)['mode'], 'sha256': hashlib.sha256(raw).hexdigest()}, open('manifest.json','w'))\n")
        write(work, "verify.py", "import json, hashlib\nr = open('settings.json','rb').read()\nm = json.load(open('manifest.json'))\nassert m == {'mode': json.loads(r)['mode'], 'sha256': hashlib.sha256(r).hexdigest()}\nassert m['mode'] == 'strict'\nprint('verified')\n")
    else:
        raise ValueError(case)
    return {"gold": gold, "initial": snapshot(work)}


def run_python(work, code=None, args=None):
    env = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    cmd = [sys.executable, "-B", "-c", code] if code is not None else [sys.executable, "-B", *args]
    return subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=15)


def grade(case, work, final, state):
    checks, observations = {}, {}
    for path, expected in state["gold"].items():
        try:
            raw = (work / path).read_text()
            got = json.loads(raw) if path.endswith(".json") else raw.strip()
            # bool and int compare equal in Python; JSON type distinctions matter here.
            checks[path] = json.dumps(got, sort_keys=True, ensure_ascii=False) == json.dumps(expected, sort_keys=True, ensure_ascii=False)
        except (OSError, ValueError):
            checks[path] = False
    if case == "rename":
        text = "\n".join(p.read_text() for p in (work / "userlib").glob("*.py"))
        checks["old_identifier_removed"] = not re.search(r"\bget_user_name\b", text)
        test = "from userlib.core import fetch_user_name, get_user_name_legacy\nu={'first':'Ada','last':'Lovelace'}\nassert fetch_user_name(u)=='Ada Lovelace'\nassert get_user_name_legacy(u)=='Lovelace, Ada'\n"
        for i in range(8):
            test += f"from userlib.feature_{i} import label\nassert label(u)=='Ada Lovelace / Lovelace, Ada'\n"
        checks["behavior"] = run_python(work, test).returncode == 0
    elif case == "guardrail":
        probe = work / "src" / "eval_probe.py"
        probes = [("x = eval('1 + 2')\n", False), ("x = eval ( '3' )\n", False),
                  ("# eval('1')\nx = 'eval(1)'\n", True), ("def f(obj):\n    return obj.eval()\n", True)]
        for i, (source, valid) in enumerate(probes):
            probe.write_text(source)
            result = run_python(work, args=["check.py"])
            checks[f"policy_probe_{i}"] = result.returncode == (0 if valid else 1)
        probe.unlink(missing_ok=True)
    elif case == "regression":
        checks["valid_bounds"] = run_python(work, "from bounds import clamp\nassert clamp(5,0,10)==5\nassert clamp(-2,0,10)==0\nassert clamp(12,0,10)==10\nassert clamp(1,1,1)==1\n").returncode == 0
        checks["invalid_bounds"] = run_python(work, "from bounds import clamp\ntry:\n    clamp(5,10,0)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('accepted inverted bounds')\n").returncode == 0
        baseline = run_python(work, args=["-m", "unittest", "discover", "-v"])
        checks["own_suite_passes"] = baseline.returncode == 0
        path = work / "bounds.py"
        saved = path.read_bytes()
        try:
            path.write_text("def clamp(value, low, high):\n    return max(low, min(high, value))\n")
            mutation = run_python(work, args=["-m", "unittest", "discover", "-v"])
            checks["suite_catches_regression"] = mutation.returncode != 0 and "FAIL:" in mutation.stderr
        finally:
            path.write_bytes(saved)
    elif case == "out_of_scope":
        checks["no_file_changes"] = snapshot(work) == state["initial"]
        checks["review_delivered"] = bool(final.strip())
    elif case == "judgment":
        after = snapshot(work)
        changes = {p for p in state["initial"].keys() | after.keys() if state["initial"].get(p) != after.get(p)}
        checks["only_requested_file"] = changes == {"message.md"}
        checks["times_preserved"] = all(t in (work / "message.md").read_text() for t in ["14:00 UTC", "16:00 UTC"])
    elif case == "independent":
        timings = []
        checks["checks_unchanged"] = all(snapshot(work).get(p) == h for p, h in state["initial"].items())
        for name in ["alpha", "beta", "gamma"]:
            p = work / f"{name}-timing.json"
            checks[f"ran_{name}"] = p.exists()
            if p.exists():
                timings.append(json.loads(p.read_text()))
        observations["all_three_overlap"] = len(timings) == 3 and max(t[0] for t in timings) < min(t[1] for t in timings)
    elif case == "dependent":
        try:
            settings = (work / "settings.json").read_bytes()
            manifest = json.loads((work / "manifest.json").read_text())
            checks["fresh_manifest"] = json.loads(settings) == {"mode": "strict"} and manifest == {
                "mode": "strict", "sha256": hashlib.sha256(settings).hexdigest()}
        except (OSError, ValueError):
            checks["fresh_manifest"] = False
        checks["tools_unchanged"] = all(snapshot(work).get(p) == state["initial"][p] for p in ["generate.py", "verify.py"])
    after = snapshot(work)
    observations["added_files"] = sorted(after.keys() - state["initial"].keys())
    observations["modified_files"] = sorted(p for p in after.keys() & state["initial"].keys() if after[p] != state["initial"][p])
    manual = case in {"out_of_scope", "judgment"}
    return {"checks": checks, "automatic_pass": bool(checks) and all(checks.values()),
            "needs_blind_review": manual, "observations": observations}
