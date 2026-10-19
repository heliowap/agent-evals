"""Once-only direct Go researcher harness. Help, plan, seal and export are offline.

Only the explicitly approved `execute` command consumes ephemeral GO_API_KEY.
No credential store, OpenCode configuration or ambient agent interface is used.
"""
import argparse
import copy
import datetime
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import webfetch

ROOT = Path(__file__).resolve().parent
RUNTIME = Path("/private/tmp/opencode/researcher-eval-20261007T021014Z")
ENDPOINT = "https://opencode.ai/zen/go/v1/chat/completions"
SEED = 20261007021014
CONFIGURATIONS = [{"id": family + "-" + effort, "model": model, "effort": effort}
                  for family, model in [("deepseek", "deepseek-v4.1-flash"), ("glm", "glm-5.3-flash")]
                  for effort in ("low", "high", "max")]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    if exclusive:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temp = path.with_name(path.name + ".tmp")
        with temp.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)


def owned_path(root, relative):
    root = Path(root).resolve()
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("path outside owned root or symlink")
    return path


def make_schedule():
    """Two randomized cyclic Latin squares; all first reps before second reps."""
    rng = random.Random(SEED)
    configs = copy.deepcopy(CONFIGURATIONS)
    columns = configs[:]
    rng.shuffle(columns)
    rows = list(range(6))
    rng.shuffle(rows)
    first = next(i for i, c in enumerate(columns) if c["id"] == "deepseek-low")
    rows.remove(first)
    rows.insert(0, first)
    blocks, cases = [], []
    counts = {c["id"]: {str(p): 0 for p in range(1, 7)} for c in configs}
    for repetition in (1, 2):
        tasks = ["T" + str(i) for i in range(1, 7)]
        rng.shuffle(tasks)
        if repetition == 2:
            rng.shuffle(rows)
        for task, row in zip(tasks, rows):
            block = {"id": "B" + str(len(blocks) + 1), "task_id": task,
                     "repetition": repetition, "case_ids": []}
            for position in range(1, 7):
                c = columns[(row + position - 1) % 6]
                opaque = "c-" + format(rng.getrandbits(96), "024x")
                case = {"id": opaque, "index": len(cases) + 1, "block_id": block["id"],
                        "position": position, "task_id": task, "repetition": repetition,
                        "configuration_id": c["id"], "model": c["model"], "effort": c["effort"]}
                cases.append(case)
                block["case_ids"].append(opaque)
                counts[c["id"]][str(position)] += 1
            blocks.append(block)
    return {"seed": SEED, "algorithm": "Python Random MT19937; shuffled columns; cyclic Latin rows; first row rotated to DeepSeek LOW; shuffled task assignments per repetition; second row permutation shuffled; 96-bit independent opaque IDs", "configurations": configs, "blocks": blocks, "cases": cases, "position_counts": counts}


def visible_words(text):
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https://\S+", "", text)
    text = re.sub(r"[`*_#>|~]", "", text)
    return len(text.split())


def usage_summary(raw_steps):
    """Inclusive native totals, never double-count cached/reasoning subsets."""
    fields = ["prompt_tokens", "completion_tokens", "reasoning_tokens", "cache_read_tokens",
              "cache_write_tokens", "uncached_input_tokens", "non_reasoning_output_tokens", "reported_cost"]
    rows = []
    for raw in raw_steps:
        u = raw if isinstance(raw, dict) else {}
        prompt, completion = u.get("prompt_tokens"), u.get("completion_tokens")
        details = u.get("prompt_tokens_details")
        details = details if isinstance(details, dict) else {}
        cached = details.get("cached_tokens", u.get("prompt_cache_hit_tokens"))
        # Native aliases describe the SAME subset, not additive contributions.
        written = details.get("cache_write_tokens", u.get("cache_creation_input_tokens"))
        output_details = u.get("completion_tokens_details")
        reasoning = output_details.get("reasoning_tokens") if isinstance(output_details, dict) else None
        known = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0
        def difference(total, *subsets):
            return total - sum(subsets) if all(known(x) for x in (total,) + subsets) and total >= sum(subsets) else None
        # Nonoverlapping residual input; never add read/write subsets to native
        # totals. If a subset is absent, this residual remains unknown.
        uncached = difference(prompt, cached, written)
        # A reported miss count resolves unknown write accounting only if native supplies it.
        if known(u.get("prompt_cache_miss_tokens")) and known(prompt) and known(cached) and prompt == cached + u["prompt_cache_miss_tokens"]:
            uncached = u["prompt_cache_miss_tokens"]
        values = [prompt, completion, reasoning, cached, written, uncached,
                  difference(completion, reasoning), u.get("cost")]
        rows.append({f: v if known(v) else None for f, v in zip(fields, values)})
    totals = {f: sum(r[f] for r in rows) if rows and all(r[f] is not None for r in rows) else None for f in fields}
    return {"complete": bool(rows) and all(totals[f] is not None for f in fields[:-1]),
            "totals_complete": bool(rows) and totals["prompt_tokens"] is not None and totals["completion_tokens"] is not None,
            "subsets_complete": bool(rows) and all(totals[f] is not None for f in fields[2:-1]),
            "known_fields": {f: totals[f] is not None for f in fields}, "raw_steps": raw_steps, **totals}


def append_post_start(path, row):
    """Sequential single-writer global intent ledger; durable before transmission."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ValueError("symlink POST ledger")
    with path.open("ab") as stream:
        stream.write((json.dumps(row, ensure_ascii=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def redact_secret(value, key):
    if isinstance(value, str):
        return value.replace(key, "[REDACTED_AUTH]") if key else value
    if isinstance(value, list):
        return [redact_secret(v, key) for v in value]
    if isinstance(value, dict):
        return {redact_secret(k, key): redact_secret(v, key) for k, v in value.items()}
    return value


def request_body(case, messages, step, tools, protocol):
    if case["model"] not in protocol["models"] or case["effort"] not in protocol["efforts"]:
        raise ValueError("unfrozen configuration")
    body = {"model": case["model"], "reasoning_effort": case["effort"],
            "messages": copy.deepcopy(messages), "max_tokens": protocol["limits"]["max_tokens"],
            "stream": False, "thinking": protocol["thinking"]}
    if step <= protocol["limits"]["tool_steps"]:
        body["tools"] = copy.deepcopy(tools)
    return body


def post_go(body, key, session, deadline, mark_started):
    """Exactly one direct POST; http.client has no retry/redirect machinery."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("case deadline exhausted")
    conn = http.client.HTTPSConnection("opencode.ai", timeout=remaining)
    try:
        encoded = json.dumps(body, ensure_ascii=False).encode()
        headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
                   "User-Agent": webfetch.USER_AGENT, "x-opencode-session": session}
        mark_started()
        conn.request("POST", "/zen/go/v1/chat/completions", body=encoded, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        return response.status, raw
    finally:
        conn.close()


def access_denial(http_status, payload):
    error = payload.get("error", payload) if isinstance(payload, dict) else payload
    text = json.dumps(error).lower()
    return http_status in (401, 403) or (http_status >= 400 and any(
        term in text for term in ("global regions", "privacy settings", "region", "entitlement", "unauthorized", "invalid api key", "subscription", "authentication")))


def new_record(case, status="not_run"):
    return {"case_id": case["id"], "schedule_index": case["index"], "block_id": case["block_id"],
            "task_id": case["task_id"], "repetition": case["repetition"], "configuration_id": case["configuration_id"],
            "model": case["model"], "effort": case["effort"], "status": status, "operational_complete": False,
            "start_utc": None, "end_utc": None, "monotonic_start": None, "monotonic_end": None,
            "wall_s": None, "assistant_span_s": None, "inference_steps": 0, "requests": [], "fetches": [],
            "answer_path": None, "visible_words": 0, "usage": usage_summary([]), "errors": [],
            "cleanup": {}, "source_drift": [], "session_id": None, "history_path": None}


def run_case(spec, key, transport=None, fetcher=None):
    """Public worker interface, also exercised with injected offline transports.

    spec contains a public task and source HASHES, never gold. Every write precedes
    any dependent network action. Parent supervises/collects even killed workers.
    """
    transport, fetcher = transport or post_go, fetcher or webfetch.fetch_document
    case, task, protocol = spec["case"], spec["task"], spec["protocol"]
    directory = Path(spec["directory"])
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Once-only lease survives crashes; existence is rejection, not resume.
    save_json(directory / "lease.json", {"case_id": case["id"], "intent_utc": utc()}, exclusive=True)
    prefix = "execution/cases/" + case["id"] + "/"
    ledger_path = Path(spec["ledger_path"])
    record = new_record(case, "running")
    record.update(start_utc=utc(), monotonic_start=time.monotonic(), session_id=str(uuid.uuid4()), history_path=prefix + "history.json")
    deadline = spec.get("deadline", time.monotonic() + protocol["limits"]["wall_s"])
    messages = [{"role": "system", "content": spec["system"]}, {"role": "user", "content": task["prompt"]}]
    contents, raw_usage = [], []
    first_post_start, last_post_end = None, None
    source_by_url = {s["url"].split("#")[0]: s for s in spec.get("sources", [])}

    def persist():
        record["inference_steps"] = len(record["requests"])
        record["usage"] = usage_summary([r["native_usage"] for r in record["requests"]])
        record["visible_words"] = visible_words("\n".join(contents))
        save_json(directory / "record.json", redact_secret(record, key))
        save_json(directory / "history.json", redact_secret(messages, key))

    def store(name, raw):
        path = owned_path(directory, name)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if isinstance(raw, bytes):
            raw = raw.replace(key.encode(), b"[REDACTED_AUTH]") if key else raw
        else:
            raw = redact_secret(raw, key).encode("utf-8")
        path.write_bytes(raw)
        return prefix + name

    persist()
    try:
        for step in range(1, protocol["limits"]["inference_steps"] + 1):
            body = request_body(case, messages, step, spec["tools"], protocol)
            name = "requests/" + str(step)
            save_json(directory / (name + "-body.json"), redact_secret(body, key), exclusive=True)
            intent_utc = utc()
            request = {"step": step, "intent_utc": intent_utc, "started_utc": intent_utc, "ended_utc": None, "elapsed_s": None,
                       "request_path": prefix + name + "-body.json", "response_path": None,
                       "http_status": None, "error": None, "usage": usage_summary([None]), "native_usage": None,
                       "intent_logged": True, "client_post_started_utc": None, "client_post_starts": 0}
            record["requests"].append(request)
            persist()
            before = time.monotonic()

            def mark_started():
                nonlocal first_post_start
                if request["client_post_starts"]:
                    raise ValueError("duplicate client POST boundary; replay prohibited")
                now = time.monotonic()
                started = utc()
                append_post_start(ledger_path, {"case_id": case["id"], "step": step,
                                             "request_path": request["request_path"], "started_utc": started})
                if first_post_start is None:
                    first_post_start = now
                request.update(started_utc=started, client_post_started_utc=started, client_post_starts=1, client_post_monotonic_start=now)
                persist()

            try:
                status, raw = transport(body, key, record["session_id"], deadline, mark_started)
                last_post_end = time.monotonic()
                request.update(ended_utc=utc(), elapsed_s=last_post_end - before)
                request["http_status"] = status
                request["response_path"] = store(name + "-response.json", raw)
                native = json.loads(raw)
                request["native_usage"] = native.get("usage") if isinstance(native, dict) else None
                request["usage"] = usage_summary([request["native_usage"]])
                raw_usage.append(request["native_usage"])
                if not 200 <= status < 300 or native.get("error"):
                    request["error"] = native.get("error", {"http_status": status})
                    record["status"] = "access_gate_error" if access_denial(status, native) else "provider_error"
                    record["errors"].append(request["error"])
                    break
                choices = native.get("choices")
                if not isinstance(choices, list) or len(choices) != 1:
                    raise ValueError("expected exactly one native choice")
                choice = choices[0]
                assistant = choice["message"]
                if assistant.get("role") != "assistant" or not isinstance(assistant.get("content"), (str, type(None))):
                    raise ValueError("invalid native assistant schema")
                # Preserve full native assistant reasoning/tool calls in order, not reconstructed text.
                messages.append(copy.deepcopy(assistant))
                contents.append(assistant.get("content") or "")
                calls = assistant.get("tool_calls") or []
                if step == protocol["limits"]["inference_steps"] and calls:
                    record.update(status="step_limit", errors=["terminal call returned forbidden tools"])
                    break
                if not calls:
                    record["operational_complete"] = choice.get("finish_reason") == "stop" and bool((assistant.get("content") or "").strip())
                    record["status"] = "completed" if record["operational_complete"] else "incomplete"
                    break
                if not isinstance(calls, list) or len(calls) > 32:
                    raise ValueError("invalid or excessive tool call batch")
                persist()
                for call in calls:
                    if len(record["fetches"]) >= protocol["limits"]["fetch_attempts"]:
                        messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps({"status": "rejected", "error": "32 fetch attempt cap exhausted", "text": None})})
                        persist()
                        continue
                    fetch_start, fetch_utc = time.monotonic(), utc()
                    fetch_id = "f" + str(len(record["fetches"]) + 1)
                    f = {"id": fetch_id, "requested_url": None, "final_url": None, "status": "rejected", "redirects": [],
                         "started_utc": fetch_utc, "ended_utc": None, "elapsed_s": None, "raw_path": None,
                         "text_path": None, "model_text_path": None, "raw_sha256": None, "text_sha256": None,
                         "model_text_sha256": None, "raw_bytes": 0, "text_bytes": 0, "truncated": False,
                         "error": None, "frozen_source_match": None, "tool_call_id": call.get("id"),
                         "tool_name": (call.get("function") or {}).get("name"), "arguments_valid": False}
                    record["fetches"].append(f)
                    persist()  # Attempt evidence even if fetch blocks or worker is killed.
                    try:
                        function = call.get("function") or {}
                        args = json.loads(function.get("arguments", "null"))
                        if call.get("type") != "function" or function.get("name") != "webfetch" or not isinstance(args, dict) or set(args) != {"url"} or not isinstance(args["url"], str):
                            raise ValueError("only webfetch with one string URL is allowed")
                        f["requested_url"] = args["url"]
                        f["arguments_valid"] = True
                        if len(record["fetches"]) > protocol["limits"]["fetch_attempts"]:
                            raise ValueError("32 fetch attempt cap exhausted")
                        fetched = fetcher(args["url"], task["id"], deadline)
                        for field in ("final_url", "status", "redirects", "truncated", "error", "http_status", "content_type"):
                            f[field] = fetched.get(field)
                        for kind in ("raw", "text", "model_text"):
                            value = fetched.get(kind)
                            if value is not None:
                                encoded = value if isinstance(value, bytes) else value.encode()
                                f[kind + "_path"] = store("fetches/" + fetch_id + "-" + kind + (".bin" if kind == "raw" else ".txt"), value)
                                f[kind + "_sha256"] = sha(encoded)
                                if kind in ("raw", "text"):
                                    f[kind + "_bytes"] = len(encoded)
                        frozen = source_by_url.get((args["url"]).split("#")[0]) or source_by_url.get(f["final_url"])
                        if frozen and fetched.get("text") is not None:
                            f["frozen_source_match"] = {"raw": f["raw_sha256"] == frozen["raw_sha256"], "text": f["text_sha256"] == frozen["text_sha256"]}
                            canonical = frozen.get("canonical_url", frozen["url"])
                            if not f["frozen_source_match"]["text"] and canonical in task["required_source_urls"]:
                                record["source_drift"].append({"url": canonical, "fetch_id": fetch_id, "kind": "required_main_content"})
                        output = {"status": f["status"], "url": f["final_url"], "http_status": f.get("http_status"), "truncated": f["truncated"],
                                  "error": f["error"], "text": fetched.get("model_text") if f["status"] == "ok" else None}
                    except (ValueError, TypeError, KeyError) as exc:
                        f["error"] = str(exc)
                        output = {"status": "rejected", "error": str(exc), "text": None}
                    f.update(ended_utc=utc(), elapsed_s=time.monotonic() - fetch_start)
                    exact_result = json.dumps(output, ensure_ascii=False)
                    f["tool_result_path"] = store("fetches/" + fetch_id + "-tool-result.json", exact_result)
                    f["tool_result_sha256"] = sha(redact_secret(exact_result, key).encode())
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": exact_result})
                    persist()
                    if record["source_drift"]:
                        record["status"] = "source_drift"
                        break
                if record["source_drift"]:
                    break
            except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:
                request["error"] = {"type": type(exc).__name__, "message": str(exc)}
                if len(raw_usage) < len(record["requests"]):
                    raw_usage.append(None)
                record["status"] = "timeout" if isinstance(exc, TimeoutError) else "harness_error"
                record["errors"].append(request["error"])
                break
            finally:
                if request["ended_utc"] is None:
                    last_post_end = time.monotonic()
                    request.update(ended_utc=utc(), elapsed_s=last_post_end - before)
                persist()
        if record["status"] == "running":
            record["status"] = "step_limit"
    finally:
        answer = "\n\n".join(t for t in contents if t.strip())
        record["answer_path"] = store("answer.txt", answer) if answer else None
        record.update(end_utc=utc(), monotonic_end=time.monotonic())
        record["wall_s"] = record["monotonic_end"] - record["monotonic_start"]
        if first_post_start is not None and last_post_end is not None:
            record["assistant_span_s"] = last_post_end - first_post_start
        persist()
    return redact_secret(record, key)


def supervise(command, stdin, env, cwd, timeout):
    """Launch a new owned session, hard-kill only its group, await and drain."""
    start, start_utc = time.monotonic(), utc()
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env, cwd=cwd, start_new_session=True)
    timed_out, killed = False, False
    try:
        out, err = process.communicate(stdin, timeout=max(0.001, timeout - (time.monotonic() - start)))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        killed = True
        out, err = process.communicate()
    finally:
        # Worker must not leave even unexpected descendants. Never scan/kill other groups.
        try:
            os.killpg(process.pid, signal.SIGKILL)
            killed = True
        except ProcessLookupError:
            pass
        process.wait()
    try:
        os.killpg(process.pid, 0)
        absent = False
    except ProcessLookupError:
        absent = True
    end = time.monotonic()
    return {"stdout": out, "stderr": err, "returncode": process.returncode,
            "timeout": timed_out, "start_utc": start_utc, "end_utc": utc(),
            "monotonic_start": start, "monotonic_end": end, "wall_s": end - start,
            "cleanup": {"owned_pgid": process.pid, "kill_sent": killed, "worker_awaited": True,
                        "output_drained": True, "owned_group_absent": absent}}


def save_cleanup(root, relative_directory, key, owned_pgids, runtime_root=RUNTIME, scan_runtime=False):
    """Save actual owned-group probes, supplied-key scans and write-scope proof.

    This checks only groups created by this controller and only declared evidence
    paths. It does not inspect credentials/configuration or snapshot the host.
    """
    root, runtime_root = Path(root).resolve(), Path(runtime_root).resolve()
    directory = owned_path(root, relative_directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    probes, remaining = [], []
    for pgid in sorted(set(owned_pgids)):
        try:
            os.killpg(pgid, 0)
            absent = False
        except ProcessLookupError:
            absent = True
        probes.append({"pgid": pgid, "absent": absent, "checked_utc": utc()})
        if not absent:
            remaining.append(pgid)
    process_path = relative_directory + "/processes.json"
    save_json(root / process_path, {"owned_only": True, "remaining": remaining,
                                  "runtime_root": str(runtime_root), "probes": probes})
    scanned, scan_errors, matches = [], [], 0
    secret_bytes = set()
    if key:
        secret_bytes = {key.encode(), json.dumps(key, ensure_ascii=True)[1:-1].encode(),
                        json.dumps(key, ensure_ascii=False)[1:-1].encode()}
    bases = [root / "execution"] + ([runtime_root] if scan_runtime else [])
    for base in bases:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
            if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
                scan_errors.append({"path": label, "error": "outside-boundary or symlink; not read"})
                continue
            if path.is_file():
                raw = path.read_bytes()
                scanned.append(label)
                if any(needle and needle in raw for needle in secret_bytes):
                    matches += 1
    scan_path = relative_directory + "/credentials.json"
    save_json(root / scan_path, {"redacted_before_persistence": True, "secret_matches": matches,
                               "scanned_paths": scanned, "scan_errors": scan_errors,
                               "external_secret_paths_read": False,
                               "scan_scope": "runner-owned evidence and optional owned runtime; exact ephemeral key including JSON encodings"})
    try:
        check_seal(root)
        frozen_unchanged = True
    except (ValueError, OSError, KeyError):
        frozen_unchanged = False
    boundary_path = relative_directory + "/write-boundary.json"
    save_json(root / boundary_path, {"frozen_inputs_unchanged": frozen_unchanged,
                                   "write_roots": ["execution", str(runtime_root)],
                                   "outside_write_operations": 0,
                                   "scope": "reviewed runner write boundaries only; no assertion about parent provisioning or unrelated host activity"})
    return {"owned_processes_remaining": len(remaining), "owned_process_check_path": process_path,
            "credential_scan_path": scan_path, "external_state_unchanged": frozen_unchanged,
            "write_boundary_check_path": boundary_path, "owned_group_absent": not remaining,
            "credential_artifacts_clean": matches == 0 and not scan_errors,
            "external_secret_paths_read": False}


def frozen_files(root):
    root = Path(root)
    required = ["runner.py", "webfetch.py", "dataset.py", "verify.py", "analysis.py", "protocol.json", "system.txt",
                "tools.json", "schedule.json", "scope.json", "plan.md", "contracts.md", "dataset/tasks.json", "dataset/gold.json", "dataset/sources.json", "preflight/workflow.json"]
    for name in required:
        if not owned_path(root, name).is_file():
            raise ValueError("missing freeze input: " + name)
    paths = set(required)
    workflow = read_json(root / "preflight/workflow.json")
    paths.update(workflow.get("review_paths", []))
    paths.update(p.name for p in root.glob("*.py") if p.is_file())
    for folder in ("dataset", "api-evidence", "tests", "preflight"):
        for path in (root / folder).rglob("*"):
            if path.is_symlink():
                raise ValueError("symlink freeze input")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                paths.add(path.relative_to(root).as_posix())
    return {name: sha(owned_path(root, name).read_bytes()) for name in sorted(paths)}


def seal(root=ROOT):
    root = Path(root)
    if (root / "freeze.json").exists() or (root / "execution").exists():
        raise ValueError("already sealed/executed; replacement prohibited")
    schedule = read_json(root / "schedule.json")
    if schedule != make_schedule():
        raise ValueError("schedule is not the frozen seeded Latin realization")
    workflow = read_json(root / "preflight/workflow.json")
    expected = {"owner": "parent", "candidate_post_starts": 0, "credential_provisioning": "parent_owned",
                "external_secret_paths_imported": False, "runtime_root": str(RUNTIME),
                "worker_bounds_verified": True, "protocol_reviewed": True, "api_evidence_reviewed": True}
    if any(workflow.get(k) != value for k, value in expected.items()) or not workflow.get("created_utc"):
        raise ValueError("parent-owned workflow/review proof is absent or incompatible")
    files = frozen_files(root)
    manifest = {"version": 1, "created_utc": utc(), "files": files,
                "schedule_sha256": files["schedule.json"], "no_candidate_calls_before_seal": True}
    save_json(root / "freeze.json", manifest, exclusive=True)
    save_json(root / "private/freeze-receipt.json", {"freeze_sha256": sha((root / "freeze.json").read_bytes())}, exclusive=True)
    return manifest


def check_seal(root=ROOT):
    root = Path(root)
    manifest = read_json(root / "freeze.json")
    receipt = read_json(root / "private/freeze-receipt.json")
    if receipt["freeze_sha256"] != sha((root / "freeze.json").read_bytes()):
        raise ValueError("modified freeze manifest")
    if not manifest.get("no_candidate_calls_before_seal") or manifest["files"] != frozen_files(root):
        raise ValueError("modified or incomplete freeze")
    if manifest["schedule_sha256"] != sha((root / "schedule.json").read_bytes()):
        raise ValueError("schedule changed")
    return manifest


def run_study(root, launch, finalize=None):
    """Controller seam: a launch callback returns one terminal record per attempt."""
    root = Path(root)
    check_seal(root)
    (root / "execution").mkdir(mode=0o700)  # Atomic once-only reservation; never resume.
    (root / "execution/post-starts.jsonl").touch(exist_ok=False)
    schedule = read_json(root / "schedule.json")
    index = {"study_status": "incomplete", "gate_case_id": schedule["cases"][0]["id"], "gate_status": "pending",
             "planned_cases": 72, "attempted_cases": 0, "terminal_cases": 0, "terminal_records": 0,
             "attempted_terminal_cases": 0, "cases": [], "cleanup": {}}
    stop = None
    for case in schedule["cases"]:
        directory = root / "execution/cases" / case["id"]
        directory.mkdir(parents=True, mode=0o700)
        lease = {"case_id": case["id"], "intent_utc": utc(), "attempted": stop is None}
        save_json(directory / "intent.json", lease, exclusive=True)
        if stop:
            record = new_record(case, stop)
        else:
            index["attempted_cases"] += 1
            save_json(root / "execution/index.json", index)
            try:
                check_seal(root)
                record = launch(case, directory)
            except Exception as exc:
                # No replay, and preserve whatever durable worker evidence was collected.
                record = read_json(directory / "record.json") if (directory / "record.json").exists() else new_record(case)
                record.update(status="harness_error", operational_complete=False)
                record["errors"].append({"type": type(exc).__name__, "message": "controller launch/collection failed; no replay"})
            if case["index"] == 1:
                index["gate_status"] = "passed" if record["status"] == "completed" else record["status"]
                if record["status"] == "access_gate_error":
                    index["gate_status"] = "access_blocked"
                    index["study_status"] = "access_blocked"
                    stop = "not_run_access_gate"
                elif record["status"] != "completed":
                    stop = "not_run_first_failure"
            if record["source_drift"]:
                stop = "not_run_source_drift"
            elif record["status"] == "access_gate_error" and case["index"] != 1:
                stop = "not_run_access_denial"
            elif record["status"] == "harness_error" or not record.get("cleanup", {}).get("owned_group_absent", False):
                stop = stop or "not_run_harness_failure"
        save_json(directory / "record.json", record)
        index["cases"].append("execution/cases/" + case["id"] + "/record.json")
        index["terminal_records"] += 1
        index["terminal_cases"] += 1
        if not record["status"].startswith("not_run"):
            index["attempted_terminal_cases"] += 1
        save_json(root / "execution/index.json", index)
    if not stop:
        index["study_status"] = "completed"
    # A custom/offline launcher supplies its own truthful proof. Do not manufacture
    # secret/process assertions when no execution-controller finalizer was supplied.
    index["cleanup"] = finalize(index) if finalize else {"proof_complete": False}
    save_json(root / "execution/index.json", index)
    return index


def execute(root=ROOT):
    """Only future approved invocation uses auth; no database provisioning helper."""
    root = Path(root)
    check_seal(root)
    if (root / "execution").exists() or RUNTIME.exists():
        raise ValueError("once-only execution/runtime already exists")
    key = os.environ.pop("GO_API_KEY", None)
    if not key or len(key) < 8 or any(ord(c) < 33 for c in key):
        raise ValueError("approved ephemeral GO_API_KEY is required")
    RUNTIME.mkdir(mode=0o700)
    tasks = {t["id"]: t for t in read_json(root / "dataset/tasks.json")}
    sources = read_json(root / "dataset/sources.json")
    # Controller alone reads source manifest, not gold; hashes and URLs only enter worker.
    source_hashes = [{k: s[k] for k in ("url", "raw_sha256", "text_sha256", "canonical_url") if k in s} for s in sources]
    protocol, tools = read_json(root / "protocol.json"), read_json(root / "tools.json")
    system = (root / "system.txt").read_text()

    def launch(case, directory):
        workspace = RUNTIME / "cases" / case["id"]
        workspace.mkdir(parents=True, mode=0o700)
        evidence = workspace / "evidence"
        spec = {"case": case, "task": tasks[case["task_id"]], "sources": source_hashes,
                "protocol": protocol, "tools": tools, "system": system, "directory": str(evidence),
                "freeze_sha256": sha((root / "freeze.json").read_bytes()), "ledger_path": str(root / "execution/post-starts.jsonl")}
        token = str(uuid.uuid4())
        save_json(workspace / "worker-authorization.json", {"token": token, "freeze_sha256": spec["freeze_sha256"]}, exclusive=True)
        env = {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8", "HOME": str(workspace),
               "TMPDIR": str(workspace), "GO_API_KEY": key, "OWNED_WORKER_TOKEN": token, "PYTHONDONTWRITEBYTECODE": "1"}
        outcome = supervise([sys.executable, "-I", "-B", str(root / "runner.py"), "_worker"],
                            json.dumps(spec).encode(), env, workspace, protocol["limits"]["wall_s"])
        if evidence.exists():
            shutil.copytree(evidence, directory, dirs_exist_ok=True)
        record = read_json(directory / "record.json") if (directory / "record.json").exists() else new_record(case)
        for field in ("start_utc", "end_utc", "monotonic_start", "monotonic_end", "wall_s", "cleanup"):
            record[field] = outcome[field]
        if outcome["timeout"]:
            record.update(status="timeout", operational_complete=False)
            record["errors"].append("supervisory deadline; owned worker killed and awaited; no replay")
            for request in record["requests"]:
                if request["ended_utc"] is None:
                    request["error"] = {"type": "SupervisoryTimeout", "message": "ambiguous interrupted request; not replayed"}
                    request.update(ended_utc=outcome["end_utc"], elapsed_s=max(0, outcome["monotonic_end"] - request.get("client_post_monotonic_start", outcome["monotonic_start"])))
            for fetch in record["fetches"]:
                if fetch["ended_utc"] is None:
                    fetch.update(status="interrupted", error="supervisory timeout", ended_utc=outcome["end_utc"])
        elif outcome["returncode"] != 0 or record["status"] == "running":
            record.update(status="harness_error", operational_complete=False)
            record["errors"].append("owned worker exited abnormally; no replay")
        if not record["answer_path"] and (directory / "history.json").exists():
            history = read_json(directory / "history.json")
            partial = "\n\n".join(m["content"] for m in history if m.get("role") == "assistant" and isinstance(m.get("content"), str) and m["content"].strip())
            if partial:
                (directory / "answer.txt").write_text(partial, encoding="utf-8")
                record["answer_path"] = "execution/cases/" + case["id"] + "/answer.txt"
                record["visible_words"] = visible_words(partial)
        record["usage"] = usage_summary([r.get("native_usage") for r in record["requests"]])
        (workspace / "worker-authorization.json").unlink()
        for stream in ("stdout", "stderr"):
            (directory / (stream + ".txt")).write_bytes(outcome[stream].replace(key.encode(), b"[REDACTED_AUTH]"))
        save_json(directory / "record.json", redact_secret(record, key))
        proof = save_cleanup(root, "execution/cases/" + case["id"] + "/cleanup", key,
                             [outcome["cleanup"]["owned_pgid"]], scan_runtime=True)
        record["cleanup"].update(proof)
        if not proof["credential_artifacts_clean"] or proof["owned_processes_remaining"] or not proof["external_state_unchanged"]:
            record.update(status="harness_error", operational_complete=False)
            record["errors"].append("cleanup/integrity proof failed; halt for parent review")
        save_json(workspace / "cleanup.json", record["cleanup"])
        return redact_secret(record, key)

    def finalize(index):
        groups = [read_json(root / p)["cleanup"]["owned_pgid"] for p in index["cases"]
                  if read_json(root / p).get("cleanup", {}).get("owned_pgid") is not None]
        return save_cleanup(root, "execution/cleanup", key, groups, scan_runtime=True)

    return run_study(root, launch, finalize)


def redact_identity(text):
    """Redact explicit self-identification, not factual documentation references."""
    pattern = re.compile(r"\b(?:I am|I'm|as|this (?:answer|response) (?:is|was) (?:by|from))\s+(?:(?:an?|the)\s+)?(?:OpenCode(?:\s+Go)?|DeepSeek|GLM|Z\.AI)[^\n.!?]*(?:[.!?]|$)", re.I)
    changes = []
    def replacement(match):
        replacement_text = "[Explicit self-identification redacted]"
        changes.append({"original": match.group(), "replacement": replacement_text, "reason": "self_identification"})
        return replacement_text
    return pattern.sub(replacement, text), changes


def canonical_url(url, sources):
    if not isinstance(url, str):
        return None
    base = url.split("#")[0]
    return next((s.get("canonical_url", s["url"]).split("#")[0] for s in sources
                 if base in {s.get(k, "").split("#")[0] for k in ("url", "final_url", "canonical_url")}), base)


def mechanical_compliance(root, record, task, sources):
    """Saved-only scope/catalog/bounds evidence, never semantic grounding grades."""
    def allowed(url):
        try:
            clean = webfetch.validate_url(url, task["id"])
            return any(re.fullmatch(p, clean) for p in task["allowed_url_patterns"])
        except (ValueError, TypeError):
            return False
    source_rules = True
    successful = []
    for fetch in record["fetches"]:
        urls = [fetch["requested_url"]]
        if fetch["final_url"]:
            urls.append(fetch["final_url"])
        for redirect in fetch["redirects"]:
            urls.extend([redirect["from"], redirect["to"]] if isinstance(redirect, dict) else [redirect])
        source_rules = source_rules and all(allowed(u) for u in urls)
        if fetch["status"] == "ok" and not fetch["error"] and fetch["text_path"] and fetch["model_text_path"] and allowed(fetch["final_url"]):
            successful.append(fetch)
    # HTML/Markdown mirrors and identical extracted documents are one content
    # source. Union both relations so repeated canonical references cannot inflate n.
    groups = []
    for fetch in successful:
        identities = {("url", canonical_url(fetch["final_url"], sources)), ("text", fetch["text_sha256"])}
        merged = identities.copy()
        untouched = []
        for group in groups:
            if group & identities:
                merged |= group
            else:
                untouched.append(group)
        groups = untouched + [merged]
    history = read_json(owned_path(root, record["history_path"])) if record["history_path"] else []
    calls = [call for message in history if message.get("role") == "assistant" for call in (message.get("tool_calls") or [])]
    tool_rules = len(record["fetches"]) <= 32 and record["inference_steps"] <= 8 and len(calls) <= 32
    for call in calls:
        try:
            args = json.loads(call["function"]["arguments"])
            valid = call.get("type") == "function" and call["function"]["name"] == "webfetch" and isinstance(args, dict) and set(args) == {"url"} and isinstance(args["url"], str)
        except (ValueError, KeyError, TypeError):
            valid = False
        tool_rules = tool_rules and valid
    if record["inference_steps"] == 8 and record["requests"]:
        response_path = record["requests"][-1]["response_path"]
        if response_path:
            native = read_json(owned_path(root, response_path))
            tool_rules = tool_rules and not any(c.get("message", {}).get("tool_calls") for c in native.get("choices", []))
    return {"word_cap": record["visible_words"] <= 400, "source_rules": bool(source_rules),
            "tool_rules": bool(tool_rules), "fetched_two_sources": len(groups) >= 2,
            "distinct_fetched_pages": len(groups), "requested_tool_calls": len(calls)}


def blind_export(root=ROOT):
    root = Path(root)
    check_seal(root)
    execution = read_json(root / "execution/index.json")
    if len(execution["cases"]) != 72 or execution.get("terminal_records", len(execution["cases"])) != 72 or (root / "blind").exists() or (root / "private/unblind.json").exists():
        raise ValueError("execution not terminal or export already exists")
    schedule = read_json(root / "schedule.json")
    tasks = {t["id"]: t for t in read_json(root / "dataset/tasks.json")}
    gold = read_json(root / "dataset/gold.json")["tasks"]  # Controller-only grading export.
    sources = read_json(root / "dataset/sources.json")
    rng = random.Random(read_json(root / "protocol.json")["blind_seed"])
    assignment, mapping, redactions, sealed_hashes, record_hashes = {}, {}, {}, {}, {}
    for configuration in schedule["configurations"]:
        # Each shard gets one repetition of every task for every configuration.
        for task_id in tasks:
            pair = [c for c in schedule["cases"] if c["configuration_id"] == configuration["id"] and c["task_id"] == task_id]
            rng.shuffle(pair)
            for shard, case in zip(("a", "b"), pair):
                assignment[case["id"]] = shard
    order = schedule["cases"][:]
    rng.shuffle(order)
    index = {"shards": {"a": [], "b": []}, "cases": []}
    for case in order:
        opaque = "b-" + format(rng.getrandbits(128), "032x")
        directory = root / "blind/cases" / opaque
        directory.mkdir(parents=True, mode=0o700)
        record_path = "execution/cases/" + case["id"] + "/record.json"
        record = read_json(root / record_path)
        answer = owned_path(root, record["answer_path"]).read_text() if record["answer_path"] else ""
        answer, changes = redact_identity(answer)
        redactions[opaque] = changes
        source_entries = []
        fetched_paths, reference_paths, archive_paths = {}, {}, {}
        def add_source(url, text, status, fetched_url=None, preview=None):
            name = "sources/s" + str(len(source_entries) + 1) + ".txt"
            (directory / "sources").mkdir(exist_ok=True)
            (directory / name).write_text(text, encoding="utf-8")
            relative = "blind/cases/" + opaque + "/" + name
            entry = {"url": url, "source_path": relative, "status": status,
                     "frozen": status == "frozen_reference", "citation_support_eligible": status == "fetched"}
            if fetched_url:
                entry["fetched_url"] = fetched_url
                entry["candidate_visible_path"] = relative
                if preview is not None and preview != text:
                    shown_name = name.removesuffix(".txt") + "-visible.txt"
                    (directory / shown_name).write_text(preview, encoding="utf-8")
                    entry["candidate_visible_path"] = "blind/cases/" + opaque + "/" + shown_name
                    sealed_hashes[entry["candidate_visible_path"]] = sha((root / entry["candidate_visible_path"]).read_bytes())
            source_entries.append(entry)
            sealed_hashes[relative] = sha((root / relative).read_bytes())
            return relative
        for fetch in record["fetches"]:
            if fetch["text_path"] and fetch["model_text_path"] and fetch["status"] == "ok":
                canonical = canonical_url(fetch["final_url"], sources)
                path = add_source(canonical, owned_path(root, fetch["text_path"]).read_text(), "fetched",
                                  fetch["final_url"], owned_path(root, fetch["model_text_path"]).read_text())
                fetched_paths.setdefault((canonical, fetch["text_sha256"]), path)
        for source in sources:
            canonical = source.get("canonical_url", source["url"])
            if canonical in tasks[case["task_id"]]["required_source_urls"]:
                path = add_source(canonical, owned_path(root, source["text_path"]).read_text(), "frozen_reference")
                reference_paths.setdefault(canonical, path)
                archive_paths[source["text_path"]] = fetched_paths.get((canonical, source["text_sha256"]), path)
        rubric = copy.deepcopy(gold[case["task_id"]])
        # Replace all archive/identity-bearing evidence paths recursively, preserving rubric semantics.
        def blind_rubric(value):
            if isinstance(value, list):
                return [blind_rubric(v) for v in value]
            if isinstance(value, dict):
                out = {k: blind_rubric(v) for k, v in value.items() if k not in {"archive_path", "raw_path", "text_path"}}
                if value.get("archive_path") in archive_paths:
                    out["source_path"] = archive_paths[value["archive_path"]]
                elif "url" in out and out["url"].split("#")[0] in reference_paths:
                    out["source_path"] = reference_paths[out["url"].split("#")[0]]
                return out
            return value
        mechanical = mechanical_compliance(root, record, tasks[case["task_id"]], sources)
        payload = {"blind_id": opaque, "task_id": case["task_id"], "prompt": tasks[case["task_id"]]["prompt"],
                   "answer": answer, "sources": source_entries, "rubric": blind_rubric(rubric),
                   "mechanical": {"attempted": not record["status"].startswith("not_run"), "operational_complete": record["operational_complete"],
                       "visible_words": record["visible_words"], **mechanical,
                       "fetch_attempts": len(record["fetches"]), "truncated_fetches": sum(bool(f["truncated"]) for f in record["fetches"]),
                       "semantic_grading": "required; not automatically assigned" if answer.strip() else "not gradable: empty answer; no semantic grade",
                       "explicit_self_identification_redacted": bool(changes)}}
        save_json(directory / "case.json", payload, exclusive=True)
        mapping[opaque] = case["id"]
        record_hashes[case["id"]] = sha((root / record_path).read_bytes())
        sealed_hashes["blind/cases/" + opaque + "/case.json"] = sha((directory / "case.json").read_bytes())
        index["cases"].append(opaque)
        index["shards"][assignment[case["id"]]].append(opaque)
    save_json(root / "blind/index.json", index, exclusive=True)
    sealed_hashes["blind/index.json"] = sha((root / "blind/index.json").read_bytes())
    save_json(root / "private/redactions.json", redactions, exclusive=True)
    save_json(root / "private/unblind.json", {"mapping": mapping, "sealed_hashes": sealed_hashes,
              "freeze_sha256": sha((root / "freeze.json").read_bytes()), "record_hashes": record_hashes}, exclusive=True)
    return index


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "seal", "execute", "blind-export", "_worker"],
                        help="plan is saved-only; execute requires parent approval and ephemeral GO_API_KEY; _worker is internal")
    args = parser.parse_args(argv)
    os.umask(0o077)
    if args.command == "plan":
        saved = read_json(ROOT / "schedule.json")
        if saved != make_schedule():
            raise ValueError("saved schedule differs from seeded plan")
        print(json.dumps({"cases": len(saved["cases"]), "first": saved["cases"][0], "position_counts": saved["position_counts"]}, indent=2))
    elif args.command == "seal":
        print(json.dumps(seal(), indent=2))
    elif args.command == "execute":
        print(json.dumps(execute(), indent=2))
    elif args.command == "blind-export":
        print(json.dumps(blind_export(), indent=2))
    else:
        key = os.environ.pop("GO_API_KEY", None)
        token = os.environ.pop("OWNED_WORKER_TOKEN", None)
        if not key:
            raise ValueError("worker requires ephemeral key")
        spec = json.load(sys.stdin)
        workspace = Path.cwd().resolve()
        if not workspace.is_relative_to(RUNTIME) or Path(spec["directory"]).resolve() != workspace / "evidence":
            raise ValueError("worker outside owned runtime")
        if Path(spec["ledger_path"]).resolve() != ROOT / "execution/post-starts.jsonl":
            raise ValueError("worker POST ledger outside owned execution path")
        authorization = read_json(workspace / "worker-authorization.json")
        if not token or token != authorization["token"] or spec["freeze_sha256"] != authorization["freeze_sha256"] or spec["freeze_sha256"] != sha((ROOT / "freeze.json").read_bytes()):
            raise ValueError("worker requires matching sealed controller authorization")
        run_case(spec, key)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print("Runner stopped: " + type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(2)
