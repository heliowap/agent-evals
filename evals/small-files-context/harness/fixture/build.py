"""Build the arm A and arm B fixtures from bottle at a pinned commit.

Arm A is the upstream layout: a single bottle.py. Arm B executes the same
source, cut into files of at most MAX_BYTES, in one shared module namespace
(see LOADER). Both arms get the same test suite; B splits oversized test files.

Usage: python3 -B fixture/build.py --out DIR [--source DIR]
"""
import argparse
import ast
import json
import pathlib
import re
import shutil
import subprocess
import sys

COMMIT = "8ec5fe29420d14998c0d86885083983eaea8b839"
REPO = "https://github.com/bottlepy/bottle.git"
MAX_BYTES = 20_000
HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE.parent / ".cache" / f"bottle-{COMMIT[:7]}"

# Copied into both arms. AGENTS.md (upstream PR rules), docs/ and .github/ are
# left out on purpose: they are unrelated to the tasks and only add noise.
COMMON = ["LICENSE", "AUTHORS", "README.rst", "Makefile", "pyproject.toml", ".gitignore"]

SECTIONS = {
    "Command-line interface": "cli",
    "Imports and Helpers used everywhere else": "helpers",
    "Exceptions and Events": "exceptions",
    "Routing": "routing",
    "Application Object": "app",
    "HTTP and WSGI Tools": "http",
    "Plugins": "plugins",
    "Common Utilities": "utils",
    "Application Helper": "app_helpers",
    "HTTP Utilities and MISC (TODO)": "http_utils",
    "Multipart Handling": "multipart",
    "Server Adapter": "servers",
    "Application Control": "app_control",
    "Template Adapters": "templates",
    "Constants and Globals": "globals",
}

PART_HEADER = b"# Part of the bottle module. See bottle/__init__.py.\n"

LOADER = '''
# Bottle's source is split into the files listed in _BOTTLE_PARTS. They are
# executed in order in this module's namespace, so together they behave exactly
# like the original single-file bottle.py: every top-level name defined in any
# of them is a global of the `bottle` module, and there are no imports between
# them. To find where a name is defined, search the files in this directory.
_BOTTLE_PARTS = (
{parts})

import os as _bottle_os
for _bottle_part in _BOTTLE_PARTS:
    _bottle_path = _bottle_os.path.join(_bottle_os.path.dirname(__file__), _bottle_part)
    with open(_bottle_path, 'rb') as _bottle_file:
        exec(compile(_bottle_file.read(), _bottle_path, 'exec'), globals())
del _bottle_os, _bottle_part, _bottle_path, _bottle_file
'''

MAIN = b"import bottle\n\nbottle.main()\n"

# Bottle (21,468 bytes) exceeds MAX_BYTES on its own and a class cannot span
# files, so this one method moves to its own part and is attached afterwards.
MOVED_METHOD = ("Bottle", "_cast")


def fetch(source):
    if source:
        return pathlib.Path(source)
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", REPO, str(CACHE)], check=True)
        subprocess.run(["git", "-C", str(CACHE), "checkout", "-q", COMMIT], check=True)
    head = subprocess.run(["git", "-C", str(CACHE), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        sys.exit(f"cache at {CACHE} is {head}, expected {COMMIT}")
    return CACHE


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower().strip("_")


def split_bottle(src):
    """Return (init_head, parts) where parts is a list of (name, bytes, origin)."""
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    doc = tree.body[0]
    assert isinstance(doc, ast.Expr) and isinstance(doc.value, ast.Constant)
    head_end = doc.end_lineno  # shebang, coding line and module docstring
    body = tree.body[1:]

    # Section starts: the '####' line above each '# Title ####' line.
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(rb"# (.+?) #{5,}\s*$", line)
        if m:
            title = m.group(1).decode()
            starts[i] = SECTIONS[title]  # i is 0-based index of the title line
    section_at = {}
    for title_idx, slug in starts.items():
        section_at[title_idx - 1] = slug  # the rule line above the title

    # Each statement owns the lines after the previous statement, so leading
    # comments and section banners travel with the statement that follows.
    spans = []
    prev_end = head_end
    for node in body:
        spans.append([prev_end, node.end_lineno, node])  # 0-based start, exclusive end
        prev_end = node.end_lineno
    spans[-1][1] = len(lines)

    sections = []
    for start, end, node in spans:
        banner = [i for i in section_at if start <= i < end]
        if banner and banner[0] > start:
            # Banner sits inside this span's leading gap: cut the gap there.
            cut = banner[0]
            if sections:
                sections[-1][1].append((start, cut, None))
            start = cut
        if banner and len(sections) == 1 and sections[0][0] == "preamble":
            sections[0][0] = section_at[start]  # fold the preamble into the first section
        elif banner or not sections:
            sections.append([section_at.get(start, "preamble"), []])
        sections[-1][1].append((start, end, node))

    parts = []
    for slug, stmts in sections:
        chunks = [[]]
        for stmt in stmts:
            s, e, node = stmt
            text = b"".join(lines[s:e])
            if isinstance(node, ast.ClassDef) and node.name == MOVED_METHOD[0]:
                cls_text, method_text, (ms, me) = extract_method(lines, s, e, node)
                size = len(PART_HEADER) + sum(len(c[3]) for c in chunks[-1]) + len(cls_text)
                if chunks[-1] and size > MAX_BYTES:
                    chunks.append([])
                chunks[-1].append((s, e, node, cls_text))
                chunks.append([(ms, me, "moved", method_text)])
                chunks.append([])
                continue
            size = len(PART_HEADER) + sum(len(c[3]) for c in chunks[-1]) + len(text)
            if chunks[-1] and size > MAX_BYTES:
                chunks.append([])
            chunks[-1].append((s, e, node, text))
        merged = []
        for c in chunks:
            if c and all(piece[2] is None for piece in c) and merged:
                # Whitespace-only gap: keep it with the code that precedes it in bottle.py.
                target = merged[-2] if merged[-1][0][2] == "moved" else merged[-1]
                target.extend(c)
            elif c:
                merged.append(c)
        chunks = merged
        for chunk in chunks:
            if chunk[0][2] == "moved":
                name = f"{slug}_{snake(MOVED_METHOD[0])}{MOVED_METHOD[1]}"
            elif len(chunks) == 1:
                name = slug
            else:
                named = [c for c in chunk if isinstance(c[2], (ast.ClassDef, ast.FunctionDef))]
                biggest = max(named, key=lambda c: len(c[3]))[2].name if named else "misc"
                name = f"{slug}_{snake(biggest)}"
            data = PART_HEADER + b"".join(c[3] for c in chunk)
            origin = [[c[0] + 1, c[1]] for c in chunk if c[0] is not None]
            parts.append([name, data, origin])

    for i, part in enumerate(parts, 1):
        part[0] = f"{i:02d}_{part[0]}.py"
        assert len(part[1]) <= MAX_BYTES, (part[0], len(part[1]))
    return b"".join(lines[:head_end]), parts


def extract_method(lines, s, e, cls):
    method = next(n for n in cls.body if getattr(n, "name", None) == MOVED_METHOD[1])
    m_start = (method.decorator_list[0].lineno if method.decorator_list else method.lineno) - 1
    m_end = method.end_lineno
    # Also take the blank lines that follow the method, so the class keeps its spacing.
    while m_end < e and lines[m_end].strip() == b"":
        m_end += 1
    cls_text = b"".join(lines[s:m_start] + lines[m_end:e])
    body = b"".join(l[4:] if l.startswith(b"    ") else l for l in lines[m_start:method.end_lineno])
    name = MOVED_METHOD[1].encode()
    moved = (b"\n" + body + b"\n\n"
             + MOVED_METHOD[0].encode() + b"." + name + b" = " + name + b"\n"
             + b"del " + name + b"\n")
    return cls_text, moved, (m_start, method.end_lineno)


# Test files over MAX_BYTES, split by top-level class. Each new file repeats
# the original header (imports). Werkzeug sample data moves to data modules.
TEST_SPLITS = {
    "test_environ.py": {
        "test_environ.py": ["TestRequest"],
        "test_environ_response.py": ["TestResponse"],
        "test_environ_redirect.py": ["TestRedirect", "TestWSGIHeaderDict"],
    },
    "test_multipart.py": {
        "test_multipart.py": ["BaseMultipartTest", "TestHeaderParser",
                              "TestMultipartParser", "TestBrokenMultipart"],
        "test_multipart_werkzeug.py": ["TestWerkzeugExamples"],
    },
}


def split_tests(test_dir, out_dir):
    manifest = {}
    for fname, layout in TEST_SPLITS.items():
        src = (test_dir / fname).read_bytes()
        lines = src.splitlines(keepends=True)
        tree = ast.parse(src)
        classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        first = min(n.lineno for n in classes.values()) - 1
        header = b"".join(lines[:first])
        span = lambda n: b"".join(lines[n.lineno - 1:n.end_lineno]) + b"\n\n"
        for out_name, names in layout.items():
            text = header
            if out_name == "test_multipart_werkzeug.py":
                text += b"from .test_multipart import BaseMultipartTest\n"
                text += b"from .multipart_samples_2 import browser_test_cases\n\n\n"
            text += b"".join(span(classes[n]) for n in names)
            (out_dir / out_name).write_bytes(text.rstrip(b"\n") + b"\n")
            manifest[f"test/{out_name}"] = {"from": f"test/{fname}", "classes": names}
        if fname == "test_multipart.py":
            data = [n for n in tree.body if not isinstance(n, (ast.ClassDef, ast.Import, ast.ImportFrom))]
            data = [n for n in data if n.lineno > classes["TestBrokenMultipart"].end_lineno]
            cases = [n for n in data if isinstance(n, ast.Assign)
                     and isinstance(n.targets[0], ast.Subscript)]
            prelude = b"".join(lines[data[0].lineno - 1:cases[0].lineno - 1])
            chunk = lambda ns: b"".join(lines[ns[0].lineno - 1:ns[-1].end_lineno]) + b"\n"
            half = 3
            s1 = b"import base64\n\n" + prelude + chunk(cases[:half])
            s2 = (b"import base64\n\nfrom .multipart_samples_1 import b64d, browser_test_cases\n\n"
                  + chunk(cases[half:]))
            (out_dir / "multipart_samples_1.py").write_bytes(s1)
            (out_dir / "multipart_samples_2.py").write_bytes(s2)
            manifest["test/multipart_samples_1.py"] = {"from": f"test/{fname}", "data": "browser_test_cases[0:3]"}
            manifest["test/multipart_samples_2.py"] = {"from": f"test/{fname}", "data": "browser_test_cases[3:]"}
    return manifest


def copy_common(src, dst):
    dst.mkdir(parents=True)
    for name in COMMON:
        shutil.copy2(src / name, dst / name)
    shutil.copytree(src / "test", dst / "test",
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))


def git_init(path):
    env = {"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-10-10T00:00:00Z",
           "PATH": "/usr/bin:/bin:/opt/homebrew/bin"}
    for cmd in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
        subprocess.run(["git", "-C", str(path), *cmd], check=True, env=env)


def build(src, out):
    out = pathlib.Path(out)
    if out.exists():
        sys.exit(f"{out} exists; use a new directory")
    original = (src / "bottle.py").read_bytes()

    a = out / "a"
    copy_common(src, a)
    (a / "bottle.py").write_bytes(original)

    b = out / "b"
    copy_common(src, b)
    head, parts = split_bottle(original)
    pkg = b / "bottle"
    pkg.mkdir()
    listing = "".join(f"    {p[0]!r},\n" for p in parts)
    (pkg / "__init__.py").write_bytes(head + LOADER.format(parts=listing).encode())
    (pkg / "__main__.py").write_bytes(MAIN)
    for name, data, _ in parts:
        (pkg / name).write_bytes(data)
    for f in TEST_SPLITS:
        (b / "test" / f).unlink()
    tests = split_tests(src / "test", b / "test")

    too_big = [str(p.relative_to(b)) for p in b.rglob("*") if p.is_file() and p.stat().st_size > MAX_BYTES]
    if too_big:
        sys.exit(f"arm B files over {MAX_BYTES} bytes: {too_big}")

    manifest = {
        "commit": COMMIT,
        "max_bytes": MAX_BYTES,
        "moved_method": ".".join(MOVED_METHOD),
        "parts": [{"file": f"bottle/{n}", "bytes": len(d), "source_lines": o} for n, d, o in parts],
        "tests": tests,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    git_init(a)
    git_init(b)
    print(f"built {a} and {b}: {len(parts)} parts, largest {max(len(d) for _, d, _ in parts)} bytes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", help="existing checkout at COMMIT (default: clone into .cache)")
    args = ap.parse_args()
    build(fetch(args.source), args.out)
