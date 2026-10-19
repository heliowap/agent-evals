"""Parse a reviewer agent's final text into structured findings.

Contract: sections BLOCKING / WARNING / NIT, bullet findings `path:line — why`,
`(none)` under empty sections, last non-empty line
`SUMMARY: N BLOCKING, N WARNING, N NIT`. Never raises; anything off-contract is
reported in `problems` and clears `format_ok`.
"""
import re

SEVERITIES = ("BLOCKING", "WARNING", "NIT")

HEADER_RE = re.compile(r"^\s*(?:#+\s*)?[*_]*\s*(BLOCKING|WARNING|NIT)S?\s*[*_]*\s*:?\s*[*_]*\s*$", re.I)
BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+(.*)$")
NONE_RE = re.compile(r"^(?:[-*+]\s*)?[*_`]*\(?\s*none\s*\)?[.]?[*_`]*\s*$", re.I)
HEADER_INLINE_RE = re.compile(
    r"^\s*(?:#+\s*)?[*_]*\s*(BLOCKING|WARNING|NIT)S?\s*[*_]*(?:\s*:|\s+[\u2014\-]\s)\s*[*_]*\s*(.+)$")
PATH_RE = re.compile(r"`?(?<![\w./\-:])([\w./\-]*[A-Za-z_][\w./\-]*)`?:(\d+)(?:-\d+)?`?")
SUMMARY_RE = re.compile(
    r"^\s*[*_]*SUMMARY[*_]*\s*:\s*(\d+)\s+BLOCKING\s*,\s*(\d+)\s+WARNING\s*,\s*(\d+)\s+NITS?\s*[*_.]*\s*$", re.I)


def _empty(problems):
    return {"findings": [], "summary": None, "format_ok": False, "problems": problems}


def _new_finding(severity, body, problems):
    m = PATH_RE.search(body)
    if m:
        path, line = m.group(1), int(m.group(2))
    else:
        path, line = None, None
        if "finding without path:line" not in problems:
            problems.append("finding without path:line")
    return {"severity": severity, "path": path, "line": line, "text": body.strip()}


def parse_review(text):
    try:
        return _parse(text)
    except Exception as e:  # never crash the harness
        return _empty([f"parser error: {type(e).__name__}: {e}"])


def _parse(text):
    if not isinstance(text, str):
        return _empty(["input is not text"])
    text = text.replace("\ufeff", "").replace("\r\n", "\n")
    problems = []
    findings = []
    summary = None
    summary_idx = None
    seen = []
    section = None
    current = None

    lines = text.split("\n")
    nonempty = [i for i, l in enumerate(lines) if l.strip()]
    if not nonempty:
        return _empty(["empty output"])

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            continue
        sm = SUMMARY_RE.match(stripped)
        if sm:
            if summary is not None:
                problems.append("multiple SUMMARY lines")
            summary = dict(zip(SEVERITIES, map(int, sm.groups())))
            summary_idx = i
            section, current = None, None
            continue
        if stripped.upper().lstrip("*_#").startswith("SUMMARY") and (
                section is None or i == nonempty[-1]):
            problems.append(f"malformed SUMMARY: {stripped[:80]}")
            section, current = None, None
            continue
        hm = HEADER_RE.match(stripped) or HEADER_INLINE_RE.match(stripped)
        if hm:
            section = hm.group(1).upper()
            if section in seen:
                problems.append(f"duplicate section {section}")
            seen.append(section)
            current = None
            if hm.re is HEADER_RE:
                continue
            raw = stripped = hm.group(2).strip()
        if section is None:
            continue  # preamble, or trailing text after SUMMARY (reported below)
        if NONE_RE.match(stripped):
            current = None
            continue
        bm = BULLET_RE.match(stripped)
        indented = raw[:1] in (" ", "\t")
        if bm:
            current = _new_finding(section, bm.group(1), problems)
            findings.append(current)
        elif indented and current is not None:
            current["text"] += "\n" + stripped
        else:
            # unbulleted content inside a section: keep it as a finding so
            # nothing (especially BLOCKING) is silently dropped
            problems.append(f"unbulleted line in {section}: {stripped[:80]}")
            current = _new_finding(section, stripped, problems)
            findings.append(current)

    for s in SEVERITIES:
        if s not in seen:
            problems.append(f"missing section {s}")
    if summary is None:
        problems.append("missing SUMMARY")
    else:
        if summary_idx != nonempty[-1]:
            problems.append("SUMMARY not last line")
        counts = {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES}
        if counts != summary:
            problems.append("SUMMARY count mismatch")

    return {"findings": findings, "summary": summary, "format_ok": not problems, "problems": problems}
