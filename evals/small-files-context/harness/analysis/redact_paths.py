"""Replace machine-specific absolute paths in result files with relative ones.

Usage: python3 -B analysis/redact_paths.py results [more paths ...]

Run on the machine that produced the results, before publishing. Patterns are
built from this machine's temp directory, home, and package root, so nothing
user-specific is hard-coded here.

  <tmp>/sfb-trial-*/repo/<path>       -> <path>          (the trial's clone)
  <tmp>/sfb-trial-*/repo              -> .
  <claude tmp>/<project>/<session>/scratchpad -> <scratchpad>
  <claude tmp>, <tmp>                 -> <tmp>
  <package root>/<path>               -> <path>
  <home>                              -> ~
  owner column of `ls -l` output      -> user

Byte counts change slightly, so per-trial `metrics.json` (computed before
redaction) can differ by a few tokens from metrics recomputed on redacted
transcripts. Peak context comes from API usage and is unaffected.
"""
import getpass
import os
import pathlib
import re
import sys
import tempfile

PKG = pathlib.Path(__file__).resolve().parent.parent
HOME = str(pathlib.Path.home())
TMP_REAL = os.path.realpath(tempfile.gettempdir())          # /tmp/folders/.../T
TMP_ALIASES = sorted({TMP_REAL, TMP_REAL.removeprefix("/private")}, key=len, reverse=True)
CLAUDE_TMP = "(?:/private)?/tmp/claude-" + str(os.getuid())
TMP = "(?:" + "|".join(map(re.escape, TMP_ALIASES)) + ")"

RULES = [
    (re.compile(TMP + r"/sfb-trial-[A-Za-z0-9_]+/repo/"), ""),
    (re.compile(TMP + r"/sfb-trial-[A-Za-z0-9_]+/repo\b"), "."),
    (re.compile(TMP + r"/sfb-trial-[A-Za-z0-9_]+"), "<tmp>/sfb-trial"),
    (re.compile(CLAUDE_TMP + r"/-[A-Za-z0-9_-]+/[0-9a-f-]{36}/scratchpad"), "<scratchpad>"),
    (re.compile(CLAUDE_TMP + r"(?:/-[A-Za-z0-9_-]+)?"), "<tmp>"),
    (re.compile(TMP), "<tmp>"),
    (re.compile(re.escape(str(PKG)) + "/"), ""),
    (re.compile(re.escape(str(PKG)) + r"\b"), "."),
    (re.compile(re.escape(HOME) + r"\b"), "~"),
    # truncated leftovers, e.g. inside a sed error message: "mp/claude-501/-private-var-..."
    (re.compile(r"[\w/]*claude-" + str(os.getuid()) + r"(?:/-[A-Za-z0-9_-]+)?"), "<tmp>"),
    (re.compile(r"\b" + re.escape(getpass.getuser()) + r"(?=\s+staff\b)"), "user"),  # `ls -l` owner
]
TEXT_SUFFIXES = {".jsonl", ".json", ".txt", ".patch", ".log", ".md"}


def redact(text):
    for pattern, repl in RULES:
        text = pattern.sub(repl, text)
    return text


def main():
    changed = 0
    for root in sys.argv[1:]:
        for path in sorted(pathlib.Path(root).rglob("*")):
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                old = path.read_text(encoding="utf-8")
                new = redact(old)
                if new != old:
                    path.write_text(new, encoding="utf-8")
                    changed += 1
    print(f"{changed} files redacted")


if __name__ == "__main__":
    main()
