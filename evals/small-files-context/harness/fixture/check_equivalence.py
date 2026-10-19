"""Equivalence gate: arm B must be arm A's bottle, cut into files.

Checks, all required:
  source     the parts, minus their header line, rebuild bottle.py exactly,
             with the one moved method put back in place
  namespace  both arms export the same names with the same types, and every
             function and method has an identical AST (bytecode is not
             compared: CPython compiles name lookups differently depending on
             what else is in the compilation unit)
  globals    every function defined in B uses the bottle module dict as its
             globals, so assigning bottle.X affects all parts
  tests      both arms collect the same test cases and pass the same ones
  sizes      no file in B (outside .git and __pycache__) exceeds MAX_BYTES

Usage: python3 -B fixture/check_equivalence.py BUILD_DIR --python PYTHON
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import MAX_BYTES, PART_HEADER  # noqa: E402

PROBE = r'''
import ast, json, sys, textwrap, types, inspect
sys.path.insert(0, sys.argv[1])
import bottle
ns = vars(bottle)
skip = {"__file__", "__path__", "__spec__", "__loader__", "__package__", "__cached__",
        "__builtins__", "__doc__", "_BOTTLE_PARTS"}

def code_sig(code):
    return ast.dump(ast.parse(textwrap.dedent(inspect.getsource(code))))

def funcs_of(obj):
    for k, v in sorted(vars(obj).items()):
        if isinstance(v, (staticmethod, classmethod)):
            v = v.__func__
        if isinstance(v, property):
            for f in (v.fget, v.fset, v.fdel):
                if f: yield k, f
        elif isinstance(v, types.FunctionType):
            yield k, v

names, codes, bad_globals = {}, {}, []
for k, v in sorted(ns.items()):
    if k in skip:
        continue
    names[k] = type(v).__name__
    if isinstance(v, types.FunctionType) and v.__module__ == "bottle":
        codes[k] = code_sig(v.__code__)
        if v.__globals__ is not ns:
            bad_globals.append(k)
    if isinstance(v, type) and v.__module__ == "bottle":
        for m, f in funcs_of(v):
            codes[f"{k}.{m}"] = code_sig(f.__code__)
            if f.__globals__ is not ns:
                bad_globals.append(f"{k}.{m}")
print(json.dumps({"names": names, "codes": codes, "bad_globals": bad_globals,
                  "file": bottle.__file__}))
'''


def probe(python, arm):
    out = subprocess.run([python, "-I", "-B", "-c", PROBE, str(arm)], check=True,
                         capture_output=True, text=True, cwd=arm).stdout
    return json.loads(out)


def pytest_cases(python, arm):
    r = subprocess.run([python, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rA", "test"],
                       capture_output=True, text=True, cwd=arm)
    cases = {}
    for line in r.stdout.splitlines():
        m = re.match(r"(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) test/[^:]+::(\S+)", line)
        if m:
            cases[m.group(2)] = m.group(1)
    return cases, r.stdout.strip().splitlines()[-1]


def check_source(build, manifest):
    original = (build / "a" / "bottle.py").read_bytes().splitlines(keepends=True)
    pkg = build / "b" / "bottle"
    init = (pkg / "__init__.py").read_bytes()
    rebuilt, moved = [], None
    for part in manifest["parts"]:
        data = (build / "b" / part["file"]).read_bytes()
        assert data.startswith(PART_HEADER), part["file"]
        body = data[len(PART_HEADER):]
        if part["file"].endswith("_cast.py"):
            moved = part
            continue
        rebuilt.append(body)
    s, e = moved["source_lines"][0]
    method = original[s - 1:e]
    # The method left the class together with the blank lines that followed it.
    tail = e
    while tail < len(original) and original[tail].strip() == b"":
        tail += 1
    head_lines = init.split(b"\n# Bottle's source is split")[0]
    expected_rest = b"".join(original[:s - 1] + original[tail:])
    got = head_lines + b"".join(rebuilt)
    moved_body = (build / "b" / moved["file"]).read_bytes()
    reindented = b"".join(b"    " + l if l.strip() else l for l in moved_body.splitlines(keepends=True)
                          [2:2 + len(method)])
    ok_rest = got == expected_rest
    ok_method = reindented == b"".join(method)
    return {"ok": ok_rest and ok_method, "rest_identical": ok_rest, "method_identical": ok_method}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--python", required=True)
    args = ap.parse_args()
    build = pathlib.Path(args.build).resolve()
    args.python = str(pathlib.Path(args.python).absolute())
    manifest = json.loads((build / "manifest.json").read_text())
    report = {}

    report["source"] = check_source(build, manifest)

    pa, pb = probe(args.python, build / "a"), probe(args.python, build / "b")
    name_diff = sorted(set(pa["names"].items()) ^ set(pb["names"].items()))
    code_diff = sorted(k for k in set(pa["codes"]) | set(pb["codes"])
                       if pa["codes"].get(k) != pb["codes"].get(k))
    report["namespace"] = {"ok": not name_diff and not code_diff, "names": len(pa["names"]),
                           "functions": len(pa["codes"]), "name_diff": name_diff,
                           "code_diff": code_diff, "b_file": pb["file"]}
    report["globals"] = {"ok": not pb["bad_globals"], "bad": pb["bad_globals"]}

    ca, sa = pytest_cases(args.python, build / "a")
    cb, sb = pytest_cases(args.python, build / "b")
    report["tests"] = {"ok": ca == cb and bool(ca), "a": sa, "b": sb,
                       "differing_cases": sorted(set(ca.items()) ^ set(cb.items()))[:20]}

    big = [str(p.relative_to(build / "b")) for p in (build / "b").rglob("*")
           if p.is_file() and not {".git", "__pycache__"} & set(p.parts)
           and p.stat().st_size > MAX_BYTES]
    report["sizes"] = {"ok": not big, "over": big}

    report["ok"] = all(v["ok"] for v in report.values())
    print(json.dumps(report, indent=2))
    (build / "equivalence.json").write_text(json.dumps(report, indent=2) + "\n")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
