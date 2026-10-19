from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import selectors
import shutil
import signal
import socket
import sqlite3
import subprocess
import threading
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

    @property
    def selection(self):
        return f"{self.provider}/{self.model}#{self.variant}"

    @property
    def identity(self):
        return {"providerID": self.provider, "id": self.model, "variant": self.variant}


CANDIDATES = (
    Candidate("sol-fast-low", "cli_proxy_openai", "gpt-6.1-sol", "fast-low", "cli_proxy",
              "http://127.0.0.1:8317/v1", "low", True),
    Candidate("deepseek-max", "opencode-go", "deepseek-v4.1-flash", "max", "opencode-go",
              "https://opencode.ai/zen/go/v1", "max", False),
)


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


def private_env(root, work):
    for name in ["home", "config/opencode", "data", "cache/opencode", "state", "tmp"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ.get("PATH", os.defpath), "LANG": "en_US.UTF-8", "PWD": str(work),
            "OPENCODE_TEST_HOME": str(root / "home"), "TMPDIR": str(root / "tmp"),
            "OPENCODE_CONFIG_PROJECT_DISABLE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            **{f"XDG_{name}_HOME": str(root / name.lower()) for name in ["CONFIG", "DATA", "CACHE", "STATE"]}}


def configuration(candidate, endpoint):
    model = {"name": candidate.model, "limit": {"context": 272000, "output": 32768},
             "capabilities": {"tools": True, "input": ["text"], "output": ["text"]},
             "variants": [{"id": candidate.variant, "settings": {"reasoningEffort": candidate.effort},
                           "body": {"reasoning_effort": candidate.effort,
                                    **({"service_tier": "priority"} if candidate.fast else {})}}]}
    provider = {"settings": {"baseURL": endpoint}, "models": {candidate.model: model}}
    if candidate.fast:
        provider.update(name="CLI Proxy OpenAI", canonical="openai", package="@opencode/ai/providers/openai/chat")
    permissions = [{"action": "*", "resource": "*", "effect": "deny"}]
    permissions += [{"action": name, "resource": "*", "effect": "allow"}
                    for name in ["read", "glob", "grep", "list"]]
    permissions.append({"action": "external_directory", "resource": "*", "effect": "deny"})
    return {"model": candidate.selection, "default_agent": AGENT, "update": "disable", "share": "disabled",
            "warming": False, "plugins": ["-opencode.skill"], "skills": [], "instructions": [],
            "mcp": {}, "lsp": False, "formatter": False, "providers": {candidate.provider: provider},
            "permissions": permissions,
            "agents": {AGENT: {"mode": "all", "system": SYSTEM, "steps": 25, "permissions": permissions},
                       "title": {"disabled": True}, "summary": {"disabled": True}}}


def credential(candidate, database):
    override = "CLIPROXY_API_KEY" if candidate.fast else "OPENCODE_GO_API_KEY"
    if key := os.environ.get(override):
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
    if value.get("type") != "key" or not value.get("key"):
        raise ValueError(f"Expected key authentication for {candidate.credential_provider}")
    return {"id": "cred_navigation", "integrationID": candidate.provider, "label": "Navigation",
            "active": True, "value": value}


def prepare(root, work, candidate, endpoint, binary, database, cache, import_auth=True):
    env = private_env(root, work)
    config = configuration(candidate, endpoint)
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


def audit(root, work, binary, env, expected):
    with local_server(binary, work, env) as server:
        api(binary, work, server, "integration.list")
        entries = api(binary, work, server, "config.get")
        skills = api(binary, work, server, "skill.list")["data"]
        plugins = api(binary, work, server, "plugin.list")["data"]
    inventory = [{"id": p.get("id"), "source_type": p.get("source", {}).get("type"),
                  "status": p.get("state", {}).get("status")} for p in plugins]
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
    if skills or not plugins or any(p["source_type"] != "builtin" for p in inventory):
        raise ValueError("Unexpected skills or external plugins")
    save(root / "effective-config.json", observed)
    return public


def request_metadata(body):
    reasoning = body.get("reasoning") or {}
    return {"model": body.get("model"), "reasoning_effort": body.get("reasoning_effort", reasoning.get("effort")),
            "service_tier": body.get("service_tier"), "stream": body.get("stream"),
            "max_tokens": body.get("max_tokens", body.get("max_completion_tokens"))}


def response_metadata(body):
    response = body.get("response") or body
    return {key: response[key] for key in ["model", "service_tier", "usage"] if key in response}


@contextmanager
def observer(candidate, records, timeout):
    upstream = urlsplit(candidate.upstream)
    connections = set()
    sockets = set()
    connection_lock = threading.Lock()
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            connection = None
            response = None
            upstream_socket = None
            started = time.monotonic()
            record = {"request": {}, "responses": [], "status": None, "first_event_s": None}
            records.append(record)
            try:
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    record["error"] = "Unexpected endpoint"
                    return
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                body = json.loads(raw)
                record["request"] = request_metadata(body)
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in {"host", "connection", "content-length", "accept-encoding"}}
                connection_type = http.client.HTTPSConnection if upstream.scheme == "https" else http.client.HTTPConnection
                connection = connection_type(upstream.hostname, upstream.port, timeout=min(timeout, 15))
                with connection_lock:
                    connections.add(connection)
                connection.connect()
                upstream_socket = connection.sock
                with connection_lock:
                    cancelled = stopping.is_set()
                    if not cancelled:
                        sockets.add(upstream_socket)
                if cancelled:
                    record["error"] = "Observer cancelled"
                    return
                connection.sock.settimeout(timeout)
                connection.request("POST", upstream.path.rstrip("/") + "/chat/completions", raw, headers)
                response = connection.getresponse()
                record["status"] = response.status
                self.send_response(response.status)
                self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
                if retry_after := response.getheader("Retry-After"):
                    self.send_header("Retry-After", retry_after)
                self.send_header("Connection", "close")
                self.end_headers()
                if "text/event-stream" in response.getheader("Content-Type", ""):
                    for line in response:
                        if record["first_event_s"] is None:
                            record["first_event_s"] = time.monotonic() - started
                        self.wfile.write(line)
                        self.wfile.flush()
                        if line.startswith(b"data:"):
                            try:
                                metadata = response_metadata(json.loads(line[5:]))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                continue
                            if metadata and metadata not in record["responses"]:
                                record["responses"].append(metadata)
                else:
                    data = response.read()
                    self.wfile.write(data)
                    try:
                        metadata = response_metadata(json.loads(data))
                        if metadata:
                            record["responses"].append(metadata)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
            except (OSError, ValueError, http.client.HTTPException):
                record["error"] = "Observer transport failure"
                self.close_connection = True
            finally:
                record["wall_s"] = time.monotonic() - started
                if response:
                    response.close()
                if connection:
                    connection.close()
                    with connection_lock:
                        connections.discard(connection)
                        sockets.discard(upstream_socket)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        stopping.set()
        server.shutdown()
        with connection_lock:
            active = list(connections)
            active_sockets = list(sockets)
        for upstream_socket in active_sockets:
            try:
                upstream_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        for connection in active:
            connection.close()
        server.server_close()
        thread.join(timeout=5)


def verify_requests(candidate, records):
    if not records:
        raise ValueError("No observed model requests")
    for record in records:
        requested = record["request"]
        if requested.get("model") != candidate.model or requested.get("reasoning_effort") != candidate.effort:
            raise ValueError("Observed request changed model or reasoning effort")
        if candidate.fast and requested.get("service_tier") not in {"priority", "fast"}:
            raise ValueError("Fast was not forwarded to the provider")
    successful = [r for r in records if r["status"] == 200 and not r.get("error")]
    tiers = [r.get("service_tier") for call in successful for r in call["responses"] if r.get("service_tier")]
    confirmed = bool(successful) and all(
        (reported := [r["service_tier"] for r in call["responses"] if r.get("service_tier")])
        and all(tier in {"priority", "fast"} for tier in reported) for call in successful)
    return {"request_settings_verified": True, "fast_requested": candidate.fast,
            "fast_forwarded": candidate.fast, "served_tiers": sorted(set(tiers)),
            "fast_served": ("confirmed" if confirmed else "not_confirmed" if tiers else "unknown") if candidate.fast else "not_requested",
            "request_count": len(records), "non_200_requests": sum(r["status"] != 200 for r in records)}


def parse_session(data, candidate, work):
    info, messages = data["info"], data["messages"]
    if info.get("model") != candidate.identity or Path(info["location"]["directory"]).resolve() != work.resolve():
        raise ValueError("Session model, variant, or workspace mismatch")
    users = [m for m in messages if m["type"] == "user"]
    assistants = [m for m in messages if m["type"] == "assistant"]
    idle = [m for m in messages if m["type"] == "idle"]
    if any(m.get("model") != candidate.identity or m.get("agent") != AGENT for m in assistants):
        raise ValueError("Assistant changed identity during the task")
    if len(users) != 1 or not assistants or not idle or idle[-1]["outcome"] != "succeeded":
        raise TaskFailure("Session did not complete one task")
    final = "\n".join(p["text"] for p in assistants[-1]["content"] if p["type"] == "text")
    if not final.strip() or assistants[-1].get("error"):
        raise TaskFailure("Missing final answer")
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
    return {"session_id": info["id"], "observed_identity": info["model"], "final": final,
            "tools": tools, "usage": totals, "reported_cost_usd": info.get("cost"),
            "error_events": [m["error"] for m in assistants if m.get("error")]}


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_candidate(candidate):
    return {**asdict(candidate), "selection": candidate.selection}
