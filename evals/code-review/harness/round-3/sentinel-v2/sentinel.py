# round-3/sentinel-v2/sentinel.py
"""Sentinel v2: rank the functions a PR changes so a reviewer knows where to look first.

Output is hints only: nothing is ever removed from the review.

Needs lizard (not installed globally). Canonical test command, from round-3/:
    uv run --with lizard==1.24.0 python3 -m unittest discover -s sentinel-v2 -v
"""
import json, re, subprocess
from pathlib import Path

import jev as jev_client

QUESTIONS = {
    "changes_public_contract":
        "The change alters the inputs, outputs, or errors that callers of this function observe",
    "removes_guard":
        "The change removes or weakens a validation, null check, bounds check, or fallback",
    "changes_error_handling":
        "The change alters how errors or exceptions are raised, caught, or propagated",
    "changes_state_mutation":
        "The change alters what shared or persistent state the function writes",
    "is_cosmetic":
        "The change only renames, reformats, adds logging, or edits comments",
}
RISK_KEYS = ("changes_public_contract", "removes_guard", "changes_error_handling", "changes_state_mutation")
UNCERTAIN = (0.35, 0.65)
DIFF_CAP = 3000
TOP_N = 5

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
_HUNK_NUMS = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")


_C_ESCAPES = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "\\": 92}


def _git(cwd, *args) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=cwd, check=True,
                          capture_output=True, text=True, errors="replace").stdout


def _unquote(p: str) -> str:
    """Decode a git C-quoted path (`"a/q\\"t.py"`, octal escapes for non-ASCII bytes); others pass through."""
    if not (len(p) >= 2 and p[0] == '"' and p[-1] == '"'):
        return p
    body, out, i = p[1:-1], bytearray(), 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out += c.encode()
            i += 1
        elif len(body[i + 1:i + 4]) == 3 and all(ch in "01234567" for ch in body[i + 1:i + 4]):
            out.append(int(body[i + 1:i + 4], 8))
            i += 4
        else:
            out.append(_C_ESCAPES.get(body[i + 1], ord(body[i + 1])))
            i += 2
    return out.decode("utf-8", errors="replace")


def _parse_diff(diff: str) -> dict:
    """{new_path: [hunk]} for files that exist at HEAD; hunk = {new_start, new_count, added, removed, text}."""
    files, path, hunk = {}, None, None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path, hunk = None, None
        elif line.startswith("+++ ") and hunk is None:
            target = _unquote(line[4:].rstrip("\t"))
            path = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            if path is not None:
                files.setdefault(path, [])
        elif line.startswith("--- ") and hunk is None:
            continue
        elif path is not None and (m := _HUNK.match(line)):
            hunk = {"new_start": int(m.group(3)), "new_count": int(m.group(4) or "1"),
                    "added": 0, "removed": 0, "lines": [line]}
            files[path].append(hunk)
        elif hunk is not None and path is not None and line[:1] in "+-\\":
            hunk["lines"].append(line)
            if line.startswith("+"):
                hunk["added"] += 1
            elif line.startswith("-"):
                hunk["removed"] += 1
    return files


def _touches(h: dict, start: int, end: int) -> tuple[bool, int]:
    """Does hunk h touch function [start, end] (new-file lines)? Returns (touches, added lines inside)."""
    if h["new_count"] == 0:
        # Pure deletion after new line n. Inside when both neighbours are in the function. When n is the
        # function's last line (e.g. a Python body's tail was deleted), count it only if every deleted
        # line is indented, so a top-level statement removed after a closing `}` is not attributed.
        n = h["new_start"]
        if start <= n and n + 1 <= end:
            return True, 0
        removed = [l[1:] for l in h["lines"][1:] if l.startswith("-")]
        tail = n == end and removed and all(r[:1] in (" ", "\t") or not r.strip() for r in removed)
        return bool(tail), 0
    lo, hi = h["new_start"], h["new_start"] + h["new_count"] - 1
    inside = max(0, min(hi, end) - max(lo, start) + 1)
    return inside > 0, inside


def _innermost(funcs, pred):
    """The smallest-span function satisfying pred, or None (lizard reports nested functions separately)."""
    cands = [f for f in funcs if pred(f)]
    return min(cands, key=lambda f: (f.end_line - f.start_line, -f.start_line)) if cands else None


def changed_functions_report(snapshot: Path, base: str) -> tuple[list[dict], list[str]]:
    """(functions, skipped_files) for the `base...HEAD` diff inside `snapshot`.

    functions: at HEAD, in lizard-supported languages, each {file, function, start, end, ccn,
    added_lines, removed_lines, diff}. Each changed line is attributed only to the innermost function
    containing it, so an outer function appears only if it has changed lines outside its changed
    inner functions. `removed_lines` counts every removed line of each hunk attributed to the function.
    skipped_files: changed files that exist at HEAD but lizard has no reader for (.md, .json, ...).
    Deleted files are ignored. A non-deleted file that `git show HEAD:<path>` can't read raises.
    The git invocation pins prefixes, rename handling, quoting and diff drivers, so user git config
    (diff.noprefix, diff.dstPrefix, diff.renames, external diff tools) can't change the paths parsed.
    """
    import lizard
    from lizard_languages import get_reader_for

    snapshot = Path(snapshot)
    diff = _git(snapshot, "diff", "--no-ext-diff", "--no-color", "--src-prefix=a/", "--dst-prefix=b/",
                "--no-renames", "--unified=0", f"{base}...HEAD")
    out, skipped = [], []
    for path, hunks in _parse_diff(diff).items():
        if get_reader_for(path) is None:
            skipped.append(path)
            continue
        if not hunks:
            continue
        try:
            source = _git(snapshot, "show", f"HEAD:{path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"cannot read HEAD:{path} in {snapshot}: {e.stderr.strip()}") from e
        funcs = lizard.analyze_file.analyze_source_code(path, source).function_list
        stats = {}  # id(func) -> [added, set(hunk index)]
        for i, h in enumerate(hunks):
            if h["new_count"] == 0:
                owners = [_innermost(funcs, lambda f: _touches(h, f.start_line, f.end_line)[0])]
            else:
                owners = [_innermost(funcs, lambda f, n=n: f.start_line <= n <= f.end_line)
                          for n in range(h["new_start"], h["new_start"] + h["new_count"])]
            for f in owners:
                if f is not None:
                    s = stats.setdefault(id(f), [0, set()])
                    s[0] += h["new_count"] > 0
                    s[1].add(i)
        for f in funcs:
            if id(f) not in stats:
                continue
            added, idx = stats[id(f)]
            out.append({"file": path, "function": f.name, "start": f.start_line, "end": f.end_line,
                        "ccn": f.cyclomatic_complexity, "added_lines": added,
                        "removed_lines": sum(hunks[i]["removed"] for i in sorted(idx)),
                        "diff": "\n".join("\n".join(hunks[i]["lines"]) for i in sorted(idx)) + "\n"})
    return out, skipped


def changed_functions(snapshot: Path, base: str) -> list[dict]:
    """Functions from changed_functions_report (skipped files dropped)."""
    return changed_functions_report(snapshot, base)[0]


def jev_questions(fn: dict, hunk_text: str) -> dict:
    """Request body for one function. State is text only: file, function name, and the diff with
    hunk line numbers stripped, capped at DIFF_CAP chars. No numeric features (ccn, counts) are sent.

    "No numbers" means no numeric features we compute. Digits that are part of the text itself are kept:
    file paths (`src/v2/api.py`), function names (`parse_v1`) and code in the diff. Tests check this with
    digit-free names."""
    diff = "\n".join(_HUNK_NUMS.sub("@@", line) for line in hunk_text.splitlines())
    if len(diff) > DIFF_CAP:
        marker = "\n[diff truncated]"
        diff = diff[:DIFF_CAP - len(marker)] + marker
    return {"model": jev_client.MODEL,
            "state": {"file": str(fn["file"]), "function": str(fn["function"]), "diff": diff},
            "questions": {k: {"type": "noul", "instructions": v} for k, v in QUESTIONS.items()}}


def _risk(p: float) -> float:
    """Nouls carry no confidence field; an answer in the UNCERTAIN band [0.35, 0.65] is treated as
    "don't know" and counts as 0, so uncertain answers never lift priority."""
    return 0.0 if UNCERTAIN[0] <= p <= UNCERTAIN[1] else p


def rank(fns: list[dict], answers: list) -> list[dict]:
    """Top TOP_N functions by priority. answers[i] is {question: noul} for fns[i], or None if Jev failed.

    priority = max(risk signals, uncertain ones as 0) * (1 - is_cosmetic); Jev failure falls back to the
    structural min(1, ccn/20) with jev "unavailable". Ties: higher ccn, then more added lines.
    """
    scored = []
    for fn, a in zip(fns, answers, strict=True):
        if a is None:
            priority, signals, status = min(1, fn["ccn"] / 20), {}, "unavailable"
        else:
            priority = max(_risk(a[k]) for k in RISK_KEYS) * (1 - a["is_cosmetic"])
            signals, status = dict(a), "ok"
        scored.append(({"file": fn["file"], "function": fn["function"], "start": fn["start"], "end": fn["end"],
                        "ccn": fn["ccn"], "priority": priority, "signals": signals, "jev": status},
                       fn.get("added_lines", 0)))
    scored.sort(key=lambda t: (-t[0]["priority"], -t[0]["ccn"], -t[1]))
    return [item for item, _ in scored[:TOP_N]]


def hotspots(case_dir: Path, snapshot: Path, jev=jev_client.ask, allow_partial: bool = False) -> list[dict]:
    """Rank a case's changed functions, cached in case_dir/hotspots.json.

    `jev(payload, *, case, function) -> {question: noul}`. jev_client.JevError marks that function
    "unavailable"; anything else (JevUnknownCost, missing key) propagates and nothing is written.
    If any returned item is "unavailable", the list is returned but not cached unless allow_partial,
    so a later run can retry those functions.
    """
    case_dir = Path(case_dir)
    cache = case_dir / "hotspots.json"
    if cache.exists():
        return json.loads(cache.read_text())
    case = json.loads((case_dir / "case.json").read_text())
    fns = changed_functions(snapshot, case["base"])
    answers = []
    for fn in fns:
        try:
            answers.append(jev(jev_questions(fn, fn["diff"]), case=case["id"],
                               function=f"{fn['file']}:{fn['function']}"))
        except jev_client.JevError:
            answers.append(None)
    out = rank(fns, answers)
    if not allow_partial and any(o["jev"] == "unavailable" for o in out):
        return out
    tmp = cache.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=1) + "\n")
    tmp.replace(cache)
    return out
