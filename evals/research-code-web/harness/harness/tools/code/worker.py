"""Fixed worker. Snapshot text is never imported, evaluated, or executed."""

import errno
import fnmatch
import json
import os
from pathlib import Path
import re
import stat
import sys


class Rejected(Exception):
    pass


def result(status, text, **metadata):
    return {"status": status, "text": text, "archives": {}, "metadata": metadata}


def relative(value, root_ok=True, pattern=False):
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise Rejected("Expected a relative POSIX path or pattern.")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise Rejected("Absolute paths are not allowed.")
    parts = value.split("/")
    if ".." in parts or any(part == "" for part in parts):
        raise Rejected("Traversal and empty path components are not allowed.")
    if value == "." and root_ok:
        return ""
    if "." in parts or (not pattern and not root_ok and value == "."):
        raise Rejected("Dot components are not allowed.")
    return value


def hidden(path):
    return any(part.startswith(".") for part in path.split("/"))


def matches(path, pattern):
    """Full segment fnmatchcase, recursive ** including zero segments."""
    segments = path.split("/")
    patterns = pattern.split("/")
    # Dynamic programming avoids exponential glob backtracking.
    current = {0}
    for part in patterns:
        following = set()
        for index in current:
            if part == "**":
                following.update(range(index, len(segments) + 1))
            elif index < len(segments) and fnmatch.fnmatchcase(segments[index], part):
                following.add(index + 1)
        current = following
    return len(segments) in current


def safe_path(root, path, file=False):
    current = root
    for segment in path.split("/") if path else []:
        current = current / segment
        try:
            mode = current.lstat().st_mode
        except OSError:
            raise Rejected("Snapshot path is unavailable.") from None
        if stat.S_ISLNK(mode):
            raise Rejected("Symlinks are not allowed.")
    if file and not stat.S_ISREG(current.stat().st_mode):
        raise Rejected("Path is not a regular snapshot file.")
    return current


def file_lines(root, path):
    target = safe_path(root, path, file=True)
    if target.stat().st_size > 16 * 1024 * 1024:
        raise Rejected("File exceeds the 16 MiB safety limit.")
    # Split only on LF; Unicode separators and carriage returns remain text.
    with target.open("r", encoding="utf-8", newline="\n") as stream:
        for number, line in enumerate(stream, 1):
            yield number, line.removesuffix("\n")


def execute(payload):
    name, args, context = payload["name"], payload["arguments"], payload["context"]
    root = Path(context["snapshot_root"])
    manifest = context["manifest"]["files"]
    files = sorted(relative(path, root_ok=False) for path in manifest)
    dirs = {""}
    for path in files:
        components = path.split("/")
        dirs.update("/".join(components[:index]) for index in range(1, len(components)))
    path = relative(args.get("path", "."))
    safe_path(root, path)
    start = args.get("offset", 1)
    limit = args.get("limit", 2000 if name == "read" else 100)
    include_hidden = args.get("hidden", False)
    if name == "read":
        if path not in manifest:
            raise Rejected("File is not in the assigned manifest.")
        page = []
        total = 0
        for number, line in file_lines(root, path):
            total = number
            if start <= number < start + limit:
                page.append(f"{path}:{number}: {line}")
        more = start + len(page) <= total
        return result("ok", "\n".join(page), offset=start, returned=len(page), total=total,
                      unit="lines", truncated=more, next_offset=start + len(page) if more else None,
                      path=path, source_sha256=manifest[path].get("sha256"))
    if name in {"list", "glob"} and path not in dirs:
        raise Rejected("Path is not a manifest directory.")
    if name == "grep" and path not in dirs and path not in manifest:
        raise Rejected("Path is not in the assigned manifest.")
    prefix = path + "/" if path else ""
    eligible = [item for item in files if (item == path or item.startswith(prefix))
                and (include_hidden or not hidden(item))]
    if name == "list":
        entries = set()
        for item in eligible:
            rest = item[len(prefix):]
            first, separator, _ = rest.partition("/")
            entries.add(prefix + first + ("/" if separator else ""))
        output = sorted(entries)
    elif name == "glob":
        pattern = relative(args["pattern"], root_ok=False, pattern=True)
        output = [item for item in eligible if matches(item[len(prefix):], pattern)]
    elif name == "grep":
        include = relative(args.get("include", "**"), root_ok=False, pattern=True)
        pattern = re.escape(args["pattern"]) if args.get("literal", False) else args["pattern"]
        try:
            regex = re.compile(pattern, 0 if args.get("caseSensitive", True) else re.IGNORECASE)
        except re.error:
            raise Rejected("Invalid Python regular expression.") from None
        output = []
        count = 0
        for item in eligible:
            rel = item[len(prefix):] if item != path else item.rsplit("/", 1)[-1]
            if not matches(rel, include):
                continue
            for number, line in file_lines(root, item):
                if regex.search(line):
                    count += 1
                    if count >= start:
                        output.append(f"{item}:{number}: {line}")
                    if len(output) > limit:
                        return result("ok", "\n".join(output[:limit]), offset=start, returned=limit,
                                      unit="matching_lines", truncated=True, next_offset=start + limit,
                                      total=None, scanned_all=False)
        return result("ok", "\n".join(output), offset=start, returned=len(output), total=count,
                      unit="matching_lines", truncated=False, next_offset=None, scanned_all=True)
    else:
        raise Rejected("Unknown tool.")
    page = output[start - 1:start - 1 + limit]
    more = start - 1 + len(page) < len(output)
    return result("ok", "\n".join(page), offset=start, returned=len(page), total=len(output),
                  unit="entries", truncated=more, next_offset=start + len(page) if more else None)


def isolation_probe(context):
    # Fixed negative actions, never reachable through dispatch's candidate schemas.
    import socket
    import subprocess
    root = Path(context["snapshot_root"])
    probes = {}

    def denied(label, action):
        try:
            action()
        except OSError as error:
            probes[label] = error.errno in {errno.EPERM, errno.EACCES}
        else:
            probes[label] = False

    denied("outside_read", lambda: (root.parent / "goldlike.txt").read_text())
    denied("snapshot_write", lambda: (root / "source.txt").write_text("OVERWRITE"))
    denied("shell_exec", lambda: subprocess.run(["/bin/sh", "-c", "exit 0"], check=True))
    # Seatbelt permits allocation of an unconnected AF_INET descriptor; it
    # checks network policy on connect/bind/send. Record that fact, not a false
    # claim that socket() itself is denied. No network fd is inherited.
    socket_created = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM):
            socket_created = True
    except OSError as error:
        if error.errno not in {errno.EPERM, errno.EACCES}:
            raise
    def connection():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as channel:
            channel.settimeout(0.5)
            channel.connect(("127.0.0.1", 9))
    denied("network_connect", connection)
    return result("ok", "Actual OS isolation probes completed.", probes=probes,
                  unconnected_socket_creation_allowed=socket_created)


def main():
    payload = json.load(sys.stdin)
    try:
        output = isolation_probe(payload["context"]) if sys.argv[1:] == ["--isolation-probe"] else execute(payload)
    except Rejected as error:
        output = result("rejected", str(error))
    except (OSError, UnicodeError):
        output = result("rejected", "Snapshot file cannot be read as UTF-8 plaintext.")
    except Exception:
        output = result("error", "Invalid worker context or unexpected worker failure.", stop_reason="harness_error")
    print(json.dumps(output, ensure_ascii=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
