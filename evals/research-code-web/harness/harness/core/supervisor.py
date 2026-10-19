"""A whole-invocation hard deadline, including spawn and worker initialization."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .storage import reserve, secrets, terminal, write


def _group_absent(group):
    if group is None:
        return True
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _kill_owned(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def supervise_trial(spec, credentials):
    start = time.monotonic()
    record = reserve(spec, credentials, start=start)
    hidden = secrets(credentials)
    process = None
    reason = None
    supervisor_errors = []
    cleanup_start = None
    cleanup = {"owned_process_group": None, "terminated": False, "drained": False,
               "waited": False, "returncode": None, "group_absent": None}
    try:
        if time.monotonic() >= record["deadline"]:
            raise subprocess.TimeoutExpired("worker startup", 0)
        root = Path(__file__).resolve().parents[2]
        # No credential store location or ambient account configuration is passed.
        environment = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONUNBUFFERED": "1", "LANG": "en_US.UTF-8"}
        process = subprocess.Popen([sys.executable, "-B", "-m", "harness.core.worker"],
                                   cwd=root, env=environment, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        cleanup["owned_process_group"] = process.pid
        envelope = json.dumps({"spec": spec, "credentials": credentials, "record": record}).encode("utf-8")
        _, stderr = process.communicate(envelope, timeout=max(0, record["deadline"] - time.monotonic()))
        cleanup["drained"] = True
        cleanup["waited"] = process.returncode is not None
        if process.returncode:
            reason = "harness_error"
            supervisor_errors.append("worker exited " + str(process.returncode))
            # The worker never prints credentials; still redact any diagnostic before persistence.
            if stderr:
                supervisor_errors.append(stderr.decode("utf-8", errors="replace")[-4000:])
    except subprocess.TimeoutExpired:
        reason = "timeout"
        cleanup_start = time.monotonic()
        if process is not None:
            cleanup["terminated"] = True
            # No extra grace for worker activity beyond the invocation deadline.
            _kill_owned(process)
            process.communicate()
            cleanup.update(drained=True, waited=process.returncode is not None)
    except Exception as error:
        reason = "harness_error"
        cleanup_start = time.monotonic()
        supervisor_errors.append(type(error).__name__ + ": " + str(error))
        if process is not None:
            # Only the process group created by this supervisor may be terminated.
            _kill_owned(process)
            process.communicate()
            cleanup.update(terminated=True, drained=True, waited=process.returncode is not None)
    if process is not None:
        cleanup["returncode"] = process.returncode
        if not _group_absent(process.pid):
            cleanup_start = cleanup_start or time.monotonic()
            cleanup["descendants_remained_after_wait"] = True
            _kill_owned(process)
            cleanup["terminated"] = True
        cleanup["group_absent"] = _group_absent(process.pid)
    else:
        cleanup.update(group_absent=True, not_spawned=True)
    cleanup_end = time.monotonic()
    cleanup["cleanup_seconds"] = cleanup_end - cleanup_start if cleanup_start is not None else 0
    path = Path(spec["directory"]) / "record.json"
    if path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(spec["ledger_path"]).read_text().splitlines() if line]
    rows = [row for row in rows if row["trial_id"] == record["trial_id"]]
    durable_terminal = any(row["event"] == "terminal" for row in rows)
    # Durable terminals are immutable even if the worker subsequently fails during shutdown.
    if not durable_terminal:
        record["errors"].extend(supervisor_errors)
        record["cleanup"] = cleanup
        record["status"] = reason or "harness_error"
        record["operational_complete"] = False
        record["final_answer"] = ""
        for request in record["requests"]:
            started = any(row["event"] == "start" and row.get("step") == request["step"] for row in rows)
            request["starts"] = int(started)
            request["ambiguous_in_flight"] = started and not any(
                row["event"] == "response" and row.get("step") == request["step"] for row in rows)
        for call in record["tool_calls"]:
            started = any(row["event"] == "tool_start" and row.get("index") == call["index"] for row in rows)
            call["dispatched"] = started
            call["ambiguous_in_flight"] = started and not any(
                row["event"] == "tool_result" and row.get("index") == call["index"] for row in rows)
        record["tool_cycles"] = len({call["step"] for call in record["tool_calls"] if call["dispatched"]})
        record = terminal(spec, record, hidden)
    warnings = list(supervisor_errors)
    if durable_terminal and reason:
        warnings.append("durable terminal retained despite abnormal worker shutdown: " + reason)
    if not cleanup["group_absent"]:
        warnings.append("owned process group still exists after termination; absence not proven")
    if process is not None and not (cleanup["waited"] and cleanup["drained"]):
        warnings.append("worker wait/drain incomplete")
    now = time.monotonic()
    receipt = {"schema_version": 1, "trial_id": record["trial_id"], "cleanup": cleanup,
               "status": "warning" if warnings else "passed", "stop_dispatch": bool(warnings),
               "warnings": warnings, "worker_shutdown_reason": reason,
               "terminal_preexisting": durable_terminal, "monotonic_start": start, "monotonic_end": now,
               "supervisor_wall_seconds": now - start, "record_wall_seconds": record["wall_seconds"],
               "deadline": record["deadline"], "deadline_exceeded_seconds": max(0, now - record["deadline"]),
               "latency_scope": "Supervisor wall includes spawn, wait, drain, cleanup and terminal recovery "
               "through receipt construction. Worker activity has no deadline grace. Cleanup/receipt persistence "
               "may exceed the deadline and is not candidate inference latency."}
    write(spec["directory"], "supervisor-receipt.json", receipt, hidden, exclusive=True)
    return record
