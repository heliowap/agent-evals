"""Canonical JSON, durable writes, and the explicit execution-record adapter."""

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value, immutable=False):
    """Publish fully written JSON atomically; immutable publication never replaces."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if immutable:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def indexed(items, key="id"):
    result = {}
    for item in items:
        identity = item[key]
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError("missing/duplicate identity: " + str(identity))
        result[identity] = item
    return result


def record_id(record):
    return record.get("id", record.get("trial_id", record.get("trial", {}).get("id")))


def record_index(records):
    return indexed([dict(record, id=record_id(record)) for record in records])


def is_attempted(record):
    if record is None:
        return False
    status = record.get("status", record.get("terminal_status"))
    if not isinstance(status, str) or not status:
        raise ValueError("terminal record requires a status")
    if status in ("unrun", "stopped_unrun"):
        if record.get("attempted") is True:
            raise ValueError("unrun record claims attempted")
        return False
    if record.get("attempted") is False:
        raise ValueError("non-unrun record claims not attempted")
    return True


def answer(record):
    value = record.get("final_answer", "") if record else ""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("final_answer must be text (normalize engine record first)")
    return value


def is_completed(record):
    if not is_attempted(record):
        return False
    status = record.get("status", record.get("terminal_status"))
    declared = record.get("completed", status in ("completed", "complete"))
    if type(declared) is not bool:
        raise ValueError("completed must be boolean")
    if declared and (status not in ("completed", "complete") or not answer(record).strip()):
        raise ValueError("inconsistent completed record")
    if declared and wall_seconds(record) is not None and wall_seconds(record) > 240:
        raise ValueError("completed answer outside frozen 240-second deadline")
    return declared


def wall_seconds(record):
    if not record:
        return None
    value = record.get("wall_seconds", record.get("timings", {}).get("wall_seconds"))
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
        raise ValueError("invalid wall_seconds")
    return value


def signed(payload):
    return dict(payload, sha256=digest(payload))


def verify_signed(document):
    payload = {key: value for key, value in document.items() if key != "sha256"}
    if document.get("sha256") != digest(payload):
        raise ValueError("artifact hash breach")
    return payload
