"""Durable trial files and a locked, append-only once-only ledger."""

import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def secrets(credentials):
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)
    values = set(s for s in strings(credentials) if s)
    values.update(s.split(" ", 1)[1] for s in list(values)
                  if s.startswith(("Basic ", "Bearer ")) and " " in s)
    return sorted(values, key=len, reverse=True)


def sanitize(value, hidden):
    """Retain unknown native fields, but never persist credential/header material."""
    if isinstance(value, bytes):
        for secret in hidden:
            value = value.replace(secret.encode("utf-8"), b"[REDACTED]")
        return value
    if isinstance(value, str):
        for secret in hidden:
            value = value.replace(secret, "[REDACTED]")
        # Raw diagnostic responses sometimes echo an Authorization header.
        return re.sub(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s\"<,}]+",
                      r"\1[REDACTED]", value)
    if isinstance(value, list):
        return [sanitize(v, hidden) for v in value]
    if isinstance(value, dict):
        blocked = {"headers", "request_headers", "response_headers", "authorization",
                   "api_key", "apikey", "access_token", "refresh_token", "credentials",
                   "cookie", "set-cookie", "x-api-key"}
        return {sanitize(str(k), hidden): "[REDACTED]" if str(k).lower() in blocked
                else sanitize(v, hidden) for k, v in value.items()}
    return value


def owned(root, relative):
    root = Path(root).absolute()
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("artifact outside trial directory")
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("symlink artifact path")
        if component == root:
            break
    return path


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write(root, relative, value, hidden=(), raw=False, exclusive=False):
    path = owned(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    value = sanitize(value, hidden)
    payload = value if raw else encoded(value)
    if raw and isinstance(payload, str):
        payload = payload.encode("utf-8")
    if exclusive:
        target = path
    else:
        # A killed writer may leave a temp file; it must never block terminal recovery.
        target = owned(root, relative + "." + uuid.uuid4().hex + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(target, flags, 0o600), "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    if not exclusive:
        os.replace(target, path)
    sync_directory(path.parent)
    return digest(payload)


class Ledger:
    def __init__(self, path):
        self.path = Path(path).absolute()
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError("symlink ledger")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    def append(self, event, trial_id, **fields):
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(self.path, flags, 0o600), "r+b") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            rows = [json.loads(line) for line in stream if line.strip()]
            matching = [r for r in rows if r["trial_id"] == trial_id]
            if event == "reserve" and matching:
                raise FileExistsError("trial already reserved; replay prohibited")
            if event != "reserve" and not any(r["event"] == "reserve" for r in matching):
                raise ValueError("unreserved trial")
            if event in ("intent", "start", "response", "terminal", "tool_intent", "tool_start", "tool_result"):
                if any(r["event"] == event and r.get("step") == fields.get("step") and
                       r.get("index") == fields.get("index") for r in matching):
                    raise FileExistsError("duplicate ledger event; replay prohibited")
            if event == "start" and not any(r["event"] == "intent" and
                                            r.get("step") == fields.get("step") for r in matching):
                raise ValueError("start without intent")
            row = {"event": event, "trial_id": trial_id, "utc": utc(), **fields}
            stream.seek(0, os.SEEK_END)
            stream.write(encoded(row))
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(self.path.parent)
        return row


def reserve(spec, credentials, start=None):
    required = {"trial", "task", "configuration", "runtime", "tools", "tool_context",
                "directory", "ledger_path"}
    if set(spec) != required:
        raise ValueError("spec must contain only the frozen public interface fields")
    directory = Path(spec["directory"]).absolute()
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("symlink trial directory")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if owned(directory, "lease.json").exists():
        raise FileExistsError("directory already leased; replay prohibited")
    hidden = secrets(credentials)
    trial_id = spec["trial"]["id"]
    if not isinstance(trial_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", trial_id):
        raise ValueError("unsafe trial id")
    start = time.monotonic() if start is None else start
    record = {"schema_version": 1, "trial_id": trial_id, "trial": spec["trial"],
              "configuration_id": spec["configuration"]["id"], "suite": spec["task"]["suite"],
              "status": "running", "operational_complete": False, "final_answer": "",
              "intermediate_text": [], "session_id": str(uuid.uuid4()), "start_utc": utc(),
              "monotonic_start": start, "deadline": start + spec["runtime"]["limits"]["wall_seconds"],
              "requests": [], "tool_calls": [], "evidence_characters": 0, "errors": [],
              "tool_cycles": 0, "gate": {"status": "not_exercised", "observed_tools": []}}
    Ledger(spec["ledger_path"]).append("reserve", trial_id, directory=str(directory),
                                     session_id=record["session_id"])
    write(directory, "lease.json", {"trial_id": trial_id, "session_id": record["session_id"],
                                  "utc": utc()}, hidden, exclusive=True)
    write(directory, "record.json", record, hidden)
    return record


def terminal(spec, record, hidden):
    record["monotonic_end"] = time.monotonic()
    if record["operational_complete"] and record["monotonic_end"] >= record["deadline"]:
        record["intermediate_text"].append(record["final_answer"])
        record.update(status="timeout", operational_complete=False, final_answer="")
    if not record["operational_complete"]:
        answer = owned(spec["directory"], "final-answer.txt")
        if answer.exists():
            answer.unlink()
    record["end_utc"] = utc()
    record["wall_seconds"] = record["monotonic_end"] - record["monotonic_start"]
    record["stop_dispatch"] = record["status"] in spec["runtime"]["stopping_statuses"]
    observed = sorted({r["name"] for r in record["tool_calls"] if r.get("dispatched")})
    record["gate"] = {"status": "rejected" if record["status"] == "protocol_error" else
                      "exercised" if record["tool_cycles"] else "not_exercised",
                      "tool_cycles": record["tool_cycles"], "observed_tools": observed,
                      "native_rejection": record["status"] == "protocol_error"}
    safe = sanitize(record, hidden)
    write(spec["directory"], "record.json", safe)
    Ledger(spec["ledger_path"]).append("terminal", record["trial_id"], status=record["status"],
                                     record_sha256=digest(encoded(safe)))
    return safe
