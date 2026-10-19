from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import secrets
import selectors
import shutil
import signal
import sqlite3
import subprocess
import time
from urllib.parse import urlsplit


VERSION = "2.0.26"
AGENT = "navigator"
SYSTEM = "You explore source code and return evidence for the requested question. Read relevant files, follow the active call paths, and distinguish active code from unused code. Do not modify files. Return only the requested JSON object."


@dataclass(frozen=True)
class Candidate:
    id: str
    provider: str
    model: str
    variant: str
    credential_provider: str
    upstream: str
    effort: str
    fast: bool
    wire_model: str
    protocol: str
    auth_type: str

    @property
    def selection(self):
        return f"{self.provider}/{self.model}#{self.variant}"

    @property
    def identity(self):
        return {"providerID": self.provider, "id": self.model, "variant": self.variant}


OUTPUT_LIMIT = 128000
EFFORTS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_CANDIDATES = tuple(
    Candidate(f"haiku-{effort}", "cli_proxy", "cpa-claude-haiku-5-5", effort, "cli_proxy",
              "http://127.0.0.1:8317/v1", effort, False, "claude-haiku-5-5", "messages", "key")
    for effort in EFFORTS
)
CANDIDATES = DEFAULT_CANDIDATES


class TaskFailure(ValueError):
    pass


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def command(argv, work, env, timeout):
    started = time.monotonic()
    process = subprocess.Popen(argv, cwd=work, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return {"exit_code": process.returncode, "timeout": timed_out,
            "wall_s": time.monotonic() - started,
            "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")}


def export_session(binary, session_id, work, env, artifacts, secret_values=(), timeout=45):
    started = time.monotonic()
    raw_path = artifacts / ".export-raw"
    stderr_path = artifacts / ".export-stderr"
    timed_out = False
    interruption = None
    try:
        with os.fdopen(os.open(raw_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as stdout:
            with os.fdopen(os.open(stderr_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as stderr:
                process = subprocess.Popen([binary, "session", "export", "--standalone", session_id],
                                           cwd=work, env=env, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                except BaseException as exc:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    interruption = exc
        raw = raw_path.read_bytes()
        err = stderr_path.read_bytes()
        clean = raw
        spellings = {spelling.encode() for v in secret_values if v for spelling in [v, json.dumps(v, ensure_ascii=True)[1:-1], json.dumps(v, ensure_ascii=False)[1:-1]]}
        for value in sorted(spellings, key=len, reverse=True):
            clean = clean.replace(value, b"<REDACTED>")
            err = err.replace(value, b"<REDACTED>")
        for name, value in [("session.json", clean), ("export.stderr", err)]:
            with os.fdopen(os.open(artifacts / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as stream:
                stream.write(value)
        receipt = {"exit_code": process.returncode, "timeout": timed_out,
                   "wall_s": time.monotonic() - started,
                   "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                   "preserved_bytes": len(clean), "preserved_sha256": hashlib.sha256(clean).hexdigest(),
                   "stdout_type": "regular_file", "json_error": None}
        try:
            data = json.loads(clean.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            offset = exc.start if isinstance(exc, UnicodeDecodeError) else len(exc.doc[:exc.pos].encode("utf-8"))
            receipt["json_error"] = {"type": type(exc).__name__, "byte_offset": offset,
                                     "line": getattr(exc, "lineno", None), "column": getattr(exc, "colno", None)}
            data = None
        save(artifacts / "export.json", receipt)
        if interruption is not None:
            raise interruption
        if process.returncode or timed_out or data is None:
            raise ValueError("Session export failed; sanitized bytes and receipt preserved")
        return data
    finally:
        raw_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def private_env(root, work):
    for name in ["home", "config/opencode", "data", "cache/opencode", "state", "tmp"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ.get("PATH", os.defpath), "LANG": "en_US.UTF-8", "PWD": str(work),
            "OPENCODE_TEST_HOME": str(root / "home"), "TMPDIR": str(root / "tmp"),
            "OPENCODE_CONFIG_PROJECT_DISABLE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
            "OPENCODE_OBSERVATION_FILE": str(root / "observations.jsonl"),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            **{f"XDG_{name}_HOME": str(root / name.lower()) for name in ["CONFIG", "DATA", "CACHE", "STATE"]}}


def configuration(candidate, plugin_dir):
    model = {"limit": {"context": 272000, "output": OUTPUT_LIMIT},
             "capabilities": {"tools": True, "input": ["text"], "output": ["text"]}}
    provider = {"models": {candidate.model: model}}
    if candidate.protocol == "messages":
        model["modelID"] = candidate.wire_model
        model["variants"] = [{"id": effort, "settings": {"effort": effort}} for effort in EFFORTS]
        provider.update(name="CLI Proxy", canonical="anthropic", package="@opencode/ai/providers/anthropic",
                        settings={"baseURL": candidate.upstream})
    elif candidate.provider == "cli_proxy_google":
        model["modelID"] = candidate.wire_model
        model["variants"] = [{"id": candidate.variant, "settings": {"reasoningEffort": candidate.effort}}]
        provider.update(name="CLI Proxy (Google)", canonical="google", package="@opencode/ai/providers/openai-compatible",
                        settings={"baseURL": candidate.upstream})
    permissions = [{"action": "*", "resource": "*", "effect": "deny"}]
    permissions += [{"action": name, "resource": "*", "effect": "allow"}
                    for name in ["read", "glob", "grep", "list"]]
    permissions.append({"action": "external_directory", "resource": "*", "effect": "deny"})
    return {"model": candidate.selection, "default_agent": AGENT, "update": "disable", "share": "disabled",
            "warming": False, "plugins": ["-opencode.skill", str(plugin_dir)], "skills": [], "instructions": [],
            "mcp": {}, "lsp": False, "formatter": False, "providers": {candidate.provider: provider},
            "permissions": permissions,
            "agents": {AGENT: {"mode": "all", "system": SYSTEM, "steps": 25, "permissions": permissions},
                       "title": {"disabled": True}, "summary": {"disabled": True}}}


def credential(candidate, database):
    override = {"cli_proxy": "CLIPROXY_API_KEY", "opencode-go": "OPENCODE_GO_API_KEY"}.get(candidate.credential_provider)
    if override and (key := os.environ.get(override)):
        value = {"type": "key", "key": key}
    else:
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(credential)")}
            ordering = "active DESC, time_created DESC, id DESC" if "active" in columns else "time_created DESC, id DESC"
            row = connection.execute("SELECT value FROM credential WHERE integration_id = ? ORDER BY "
                                     + ordering + " LIMIT 1", (candidate.credential_provider,)).fetchone()
        if not row:
            raise ValueError(f"Missing credential for {candidate.credential_provider}")
        value = json.loads(row[0])
    if value.get("type") != candidate.auth_type:
        raise ValueError(f"Expected {candidate.auth_type} authentication for {candidate.credential_provider}")
    if candidate.auth_type == "key" and not value.get("key"):
        raise ValueError(f"Missing key for {candidate.credential_provider}")
    if candidate.auth_type == "oauth":
        if value.get("methodID") not in {"chatgpt-browser", "chatgpt-headless"} or not all(value.get(k) for k in ["access", "refresh", "expires"]):
            raise ValueError("Expected a complete native OpenCode ChatGPT OAuth credential")
        if value["expires"] / 1000 <= time.time() + 600:
            raise ValueError("OpenCode OAuth needs renewal before an isolated trial")
    return {"id": "cred_navigation", "integrationID": candidate.provider, "label": "Navigation",
            "active": True, "value": value}


def credential_secrets(value):
    return [value[k] for k in ["key", "access", "refresh"] if isinstance(value.get(k), str) and value[k]]


def validate_oauth_window(candidates, database, duration):
    for candidate in candidates:
        if candidate.auth_type == "oauth":
            value = credential(candidate, database)["value"]
            if value["expires"] / 1000 <= time.time() + duration + 900:
                raise ValueError("Renew OAuth in the normal OpenCode session before this run; its isolated copy must outlive the whole budget")


def prepare(root, work, candidate, binary, database, cache, import_auth=True):
    env = private_env(root, work)
    plugin_dir = root / "observer"
    plugin_dir.mkdir()
    shutil.copyfile(Path(__file__).with_name("observer.js"), plugin_dir / "server.js")
    save(plugin_dir / "package.json", {"name": "navigation-observer", "type": "module"})
    config = configuration(candidate, plugin_dir)
    save(root / "config/opencode/opencode.json", config)
    (root / "config/opencode/AGENTS.md").write_text("")
    shutil.copyfile(cache, root / "cache/opencode/models.json")
    version = command([binary, "--version"], work, env, 20)
    if version["exit_code"] or version["stdout"].strip() != f"opencode v{VERSION}":
        raise ValueError(f"Expected OpenCode {VERSION}; got {version['stdout'].strip()!r}")
    if import_auth:
        auth = root / "auth.json"
        try:
            with os.fdopen(os.open(auth, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as stream:
                json.dump([credential(candidate, database)], stream)
            imported = command([binary, "auth", "import", "--standalone", str(auth)], work, env, 45)
            if imported["timeout"] or imported["exit_code"]:
                if "Standalone server exited before reporting readiness" in imported["stderr"]:
                    raise ValueError("OpenCode could not start its standalone server for private credential import")
                raise ValueError("Private credential import failed; diagnostics withheld to protect credentials")
        finally:
            auth.unlink(missing_ok=True)
    return env, config


@contextmanager
def local_server(binary, work, env):
    server_env = {**env, "OPENCODE_PASSWORD": secrets.token_urlsafe(32)}
    with (work.parent / "server.stderr").open("wb") as stderr:
        process = subprocess.Popen([binary, "serve", "--stdio", "--port", "0"], cwd=work, env=server_env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                   start_new_session=True)
        try:
            data = b""
            deadline = time.monotonic() + 45
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while b"\n" not in data:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise ValueError("Private OpenCode server readiness timeout")
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError("Private OpenCode server could not start")
                    data += chunk
            yield {"url": json.loads(data.split(b"\n", 1)[0])["url"], "env": server_env}
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            process.stdout.close()


def api(binary, work, server, operation):
    result = command([binary, "api", "--server", server["url"], operation,
                      "--param", f"location[directory]={work.resolve()}"], work, server["env"], 45)
    if result["timeout"] or result["exit_code"]:
        raise ValueError(f"OpenCode {operation} failed")
    return json.loads(result["stdout"])


def audit(root, work, binary, env, expected, candidate=None):
    with local_server(binary, work, env) as server:
        api(binary, work, server, "integration.list")
        entries = api(binary, work, server, "config.get")
        skills = api(binary, work, server, "skill.list")["data"]
        plugins = api(binary, work, server, "plugin.list")["data"]
        models = api(binary, work, server, "model.list")["data"] if candidate else []
    inventory = [{"id": p.get("id"), "source_type": p.get("source", {}).get("type"),
                  "status": p.get("state", {}).get("status"),
                  "path": p.get("source", {}).get("path")} for p in plugins]
    documents = [entry for entry in entries if entry["type"] == "document"]
    public = {"plugins": inventory, "skills": [s.get("id") for s in skills],
              "sources": [{"type": entry.get("type"), "path": entry.get("path")} for entry in entries]}
    save(root / "discovery.json", public)
    if len(documents) != 1 or Path(documents[0].get("path", "")).resolve() != root / "config/opencode/opencode.json":
        raise ValueError("Unexpected configuration sources")
    for entry in entries:
        if entry.get("path") and not Path(entry["path"]).resolve().is_relative_to(root):
            raise ValueError("Configuration source outside private runtime")
    observed = documents[0]["info"]
    normalized = json.loads(json.dumps(expected))
    provider, model = normalized["model"].split("/", 1)
    model, variant = model.split("#", 1)
    normalized["model"] = {"providerID": provider, "model": model, "variant": variant}
    if observed != expected and observed != normalized:
        raise ValueError("Effective configuration changed")
    external = [p for p in inventory if p["source_type"] != "builtin"]
    if skills or not plugins or len(external) != 1 or external[0]["id"] != "navigation-observer" or external[0]["source_type"] != "local":
        raise ValueError("Unexpected skills or external plugins")
    if Path(external[0].get("path") or "").resolve() != root / "observer/server.js":
        raise ValueError("Unexpected observation plugin source")
    if external[0]["status"] != "active":
        raise ValueError("Observation plugin failed to activate")
    if any(p["status"] != "active" for p in inventory):
        raise ValueError("A native plugin failed to activate")
    log = root / "observations.jsonl"
    if not log.exists() or not any(json.loads(line).get("event") == "ready" for line in log.read_text().splitlines()):
        raise ValueError("Observation plugin did not record readiness")
    if candidate:
        matched = [m for m in models if m.get("providerID") == candidate.provider and m.get("id") == candidate.model]
        if len(matched) != 1:
            raise ValueError("Requested native model is unavailable")
        model = matched[0]
        variant = next((v for v in model.get("variants", []) if v["id"] == candidate.variant), None)
        if not variant or model.get("modelID", model["id"]) != candidate.wire_model:
            raise ValueError("Native model or effort variant does not match the requested selection")
        settings = variant.get("settings", {})
        effort = settings.get("effort") if candidate.protocol == "messages" else settings.get("reasoningEffort")
        if effort != candidate.effort or (candidate.fast and model.get("body", {}).get("service_tier") != "priority"):
            raise ValueError("Native effort or Fast mode is unavailable")
        public["model"] = {"id": model["id"], "providerID": model["providerID"], "modelID": candidate.wire_model,
                           "variant": candidate.variant, "effort": effort, "fast": candidate.fast,
                           "auth_type": candidate.auth_type}
        save(root / "discovery.json", public)
    save(root / "effective-config.json", observed)
    return public


def read_requests(log):
    if not log.exists():
        return []
    calls = {}
    for line in log.read_text().splitlines():
        event = json.loads(line)
        if event["event"] in {"ready", "handshake"}:
            continue
        call_id = event["call_id"]
        if event["event"] == "request":
            if call_id in calls:
                raise ValueError("Observation reused a call identity")
            calls[call_id] = {"call_id": call_id, "request": event["request"], "responses": [], "status": None,
                              "transport": event["transport"], "url": event.get("url"), "session_id": event["session_id"],
                              "agent": event["agent"], "kind": event["kind"], "identity": event["identity"],
                              "started_ms": event["at_ms"], "first_event_s": None, "complete": False}
            continue
        if call_id not in calls:
            raise ValueError("Observation response has no matching request")
        call = calls[call_id]
        if event.get("identity") != call["identity"] or event.get("session_id") != call["session_id"]:
            raise ValueError("Observation identity changed within a call")
        if event.get("status") is not None:
            call["status"] = event["status"]
        if response := event.get("response"):
            if call["first_event_s"] is None:
                call["first_event_s"] = (event["at_ms"] - call["started_ms"]) / 1000
            if response not in call["responses"]:
                call["responses"].append(response)
        if event["event"] == "error":
            call["error"] = "Observed provider or transport failure"
        if event["event"] == "end":
            call["complete"] = True
        call["wall_s"] = (event["at_ms"] - call["started_ms"]) / 1000
    return list(calls.values())


def verify_requests(candidate, records, session_id=None):
    if not records:
        raise ValueError("No observed model requests")
    sessions = {r.get("session_id") for r in records}
    if len(sessions) != 1 or None in sessions or (session_id is not None and sessions != {session_id}):
        raise ValueError("Observed requests do not belong to the single task session")
    for record in records:
        requested = record["request"]
        if requested.get("model") != candidate.wire_model or requested.get("reasoning_effort") != candidate.effort:
            raise ValueError("Observed request changed model or reasoning effort")
        if record.get("identity") != candidate.identity or record.get("agent") != AGENT or record.get("kind") != "primary":
            raise ValueError("Observed request changed session identity or task kind")
        upstream = urlsplit(candidate.upstream)
        url = urlsplit(record.get("url") or "")
        scheme = {"wss": "https", "ws": "http"}.get(url.scheme, url.scheme)
        suffix = {"responses": "/responses", "messages": "/messages", "chat": "/chat/completions"}[candidate.protocol]
        if (scheme, url.netloc, url.path) != (upstream.scheme, upstream.netloc, upstream.path.rstrip("/") + suffix):
            raise ValueError("Observed request changed provider route")
        if candidate.protocol == "messages" and requested.get("thinking_type") != "adaptive":
            raise ValueError("Anthropic adaptive thinking was not forwarded")
        if type(requested.get("max_tokens")) is not int or requested["max_tokens"] != OUTPUT_LIMIT:
            raise ValueError("Observed request changed output cap")
        if candidate.fast and requested.get("service_tier") not in {"priority", "fast"}:
            raise ValueError("Fast was not forwarded to the provider")
    successful = [r for r in records if r["status"] == 200 and not r.get("error")]
    tiers = [r.get("service_tier") for call in successful for r in call["responses"] if r.get("service_tier")]
    terminal_tiers = [[r["service_tier"] for r in call["responses"]
                       if r.get("event_type") == "response.completed" and r.get("service_tier")] for call in successful]
    confirmed = bool(successful) and all(call.get("complete") and reported and all(t in {"priority", "fast"} for t in reported)
                                        for call, reported in zip(successful, terminal_tiers))
    served = [tier for reported in terminal_tiers for tier in reported]
    return {"request_settings_verified": True, "fast_requested": candidate.fast,
            "fast_forwarded": candidate.fast, "served_tiers": sorted(set(tiers)),
            "terminal_served_tiers": sorted(set(served)),
            "fast_served": ("confirmed" if confirmed else "not_confirmed" if served else "unknown") if candidate.fast else "not_requested",
            "output_limit": OUTPUT_LIMIT, "adaptive_forwarded": True,
            "request_count": len(records), "non_200_requests": sum(r["status"] != 200 for r in records),
            "incomplete_requests": sum(not r.get("complete") for r in records),
            "observed_error_requests": sum(bool(r.get("error")) for r in records),
            "transports": sorted({r["transport"] for r in records})}


def parse_session(data, candidate, work):
    info, messages = data["info"], data["messages"]
    if info.get("model") != candidate.identity or Path(info["location"]["directory"]).resolve() != work.resolve():
        raise ValueError("Session model, variant, or workspace mismatch")
    users = [m for m in messages if m["type"] == "user"]
    assistants = [m for m in messages if m["type"] == "assistant"]
    idle = [m for m in messages if m["type"] == "idle"]
    if any(m.get("model") != candidate.identity or m.get("agent") != AGENT for m in assistants):
        raise ValueError("Assistant changed identity during the task")
    if len(users) != 1 or not assistants:
        raise TaskFailure("Session did not contain one task")
    final = "\n".join(p["text"] for p in assistants[-1]["content"] if p["type"] == "text")
    finishes = [{"id": m.get("id"), "finish": m.get("finish"), "rawFinish": m.get("rawFinish")} for m in assistants]
    limited = [i for i, m in enumerate(assistants) if m.get("finish") == "length" or m.get("rawFinish") == "max_tokens"]
    terminal_limit = len(assistants) - 1 in limited
    delivery = "output_limit_reached" if terminal_limit else "completed"
    if not terminal_limit and (not final.strip() or assistants[-1].get("error") or not idle or idle[-1].get("outcome") != "succeeded"):
        delivery = "task_error"
    tools = [p for m in assistants for p in m["content"] if p["type"] == "tool"]
    forbidden = [p.get("name", p.get("tool")) for p in tools
                 if p.get("name", p.get("tool")) not in {"read", "glob", "grep", "list"}]
    if forbidden:
        raise ValueError("Unexpected tools in explorer session")
    totals = {}
    for name, keys in {"input_tokens": ["input"], "output_tokens": ["output"], "reasoning_tokens": ["reasoning"],
                       "cached_input_tokens": ["cache", "read"], "cache_write_tokens": ["cache", "write"]}.items():
        values = []
        for message in assistants:
            value = message.get("tokens")
            for key in keys:
                value = value.get(key) if isinstance(value, dict) else None
            values.append(value)
        totals[name] = sum(values) if all(type(v) in (int, float) and v >= 0 for v in values) else None
    return {"delivery": delivery, "finishes": finishes, "terminal_output_limit": terminal_limit,
            "intermediate_output_limits": len(limited) - int(terminal_limit),
            "recovered_output_limit": bool(limited) and not terminal_limit and delivery == "completed",
            "session_id": info["id"], "observed_identity": info["model"], "final": final,
            "tools": tools, "usage": totals, "reported_cost_usd": info.get("cost"),
            "error_events": [m["error"] for m in assistants if m.get("error")]}


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_candidate(candidate):
    return {**asdict(candidate), "selection": candidate.selection}
