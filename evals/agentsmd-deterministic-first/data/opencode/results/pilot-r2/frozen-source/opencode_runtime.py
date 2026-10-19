"""OpenCode v2 adapter. All state belongs to this experiment, not the user's config."""
import hashlib
from contextlib import closing, contextmanager
import json
import os
from pathlib import Path
import signal
import secrets
import selectors
import sqlite3
import subprocess
import time

VERSION = "2.0.25"
MODEL = "openai/gpt-6.1-sol"
EFFORT = "xhigh"
MODEL_REF = {"providerID": "openai", "id": "gpt-6.1-sol", "variant": EFFORT}
SELECTION = f"{MODEL}#{EFFORT}"


def command(argv, work, env, timeout):
    start = time.monotonic()
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
    return {"exit_code": process.returncode, "timeout": timed_out, "wall_s": time.monotonic() - start,
            "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")}


def config():
    return {"model": SELECTION, "default_agent": "build", "update": "disable", "share": "disabled",
            "shell": "/bin/sh", "warming": False, "plugins": ["-opencode.skill"], "skills": [], "instructions": [],
            "mcp": {}, "lsp": False, "formatter": False,
            "permissions": [{"action": action, "resource": "*", "effect": "deny"}
                            for action in ["subagent", "task", "skill", "websearch", "webfetch"]]}


def auth_path(root):
    return root / "auth-import.json"


def agents_path(root):
    return root / "config" / "opencode" / "AGENTS.md"


def database_credential(database):
    # Read just the selected OpenAI credential. Never copy history/configuration or write the source DB.
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(credential)")}
        order = "active DESC, time_created DESC, id DESC" if "active" in columns else "time_created DESC, id DESC"
        row = db.execute("SELECT id, label, value FROM credential WHERE integration_id = ? ORDER BY "
                         + order + " LIMIT 1", ("openai",)).fetchone()
    if not row:
        raise ValueError("No OpenAI credential in OpenCode database; run opencode auth login first")
    return {"id": row[0], "integrationID": "openai", "label": row[1], "active": True, "value": json.loads(row[2])}


def load_credential(source=None):
    if source is None:
        directory = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "opencode"
        database = directory / "opencode.db"
        if database.exists():
            return database_credential(database)
        source = directory / "auth.json"
    data = json.loads(Path(source).read_text())
    if isinstance(data, list):
        entries = [e for e in data if e.get("integrationID") == "openai"]
        if not entries:
            raise ValueError("No OpenAI credential in the supplied auth export")
        return next((e for e in entries if e.get("active")), entries[-1])
    entry = data.get("openai")
    if not isinstance(entry, dict) or not entry:
        raise ValueError("No OpenAI credential in legacy auth file; run opencode auth login first")
    if entry.get("type") == "api":
        value = {"type": "key", "key": entry["key"]}
    elif entry.get("type") == "oauth":
        value = {"type": "oauth", "methodID": "chatgpt-browser",
                 **{key: entry[key] for key in ["refresh", "access", "expires"]}}
        if entry.get("accountId"):
            value["metadata"] = {"accountID": entry["accountId"]}
    else:
        raise ValueError("Unsupported legacy OpenAI credential type")
    return {"id": "cred_eval_openai", "integrationID": "openai", "label": "Eval OpenAI", "active": True, "value": value}


def save_credential(entry, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Create with private permissions before writing credentials.
    with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as stream:
        json.dump([entry], stream)
    destination.chmod(0o600)


def copy_auth(source, destination):
    save_credential(load_credential(source), destination)


def prepare(root, work, raw, binary="opencode", auth_file=None):
    root, work = root.resolve(), work.resolve()
    for name in ["home", "config/opencode", "data/opencode", "cache", "state", "tmp"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", os.defpath), "LANG": "en_US.UTF-8", "PWD": str(work),
           "OPENCODE_TEST_HOME": str(root / "home"), "TMPDIR": str(root / "tmp"),
           "OPENCODE_CONFIG_PROJECT_DISABLE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "Eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
           "GIT_COMMITTER_NAME": "Eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid",
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
           **{f"XDG_{name}_HOME": str(root / name.lower()) for name in ["CONFIG", "DATA", "CACHE", "STATE"]}}
    agents_path(root).write_bytes(raw)
    config_path = root / "config/opencode/opencode.json"
    config_path.write_text(json.dumps(config(), indent=2) + "\n")
    version = command([binary, "--version"], work, env, 15)
    if version["exit_code"] or version["stdout"].strip() != f"opencode v{VERSION}":
        raise ValueError(f"Expected OpenCode {VERSION}; got {version['stdout'].strip()!r}")
    if auth_file:
        copy_auth(auth_file, auth_path(root))
        imported = command([binary, "auth", "import", "--standalone", str(auth_path(root))], work, env, 45)
        if imported["timeout"] or imported["exit_code"]:
            raise ValueError("Cannot import private OpenAI credential; auth diagnostics omitted to protect secrets")
    return env, {"version": VERSION, "model": MODEL, "effort": EFFORT,
                 "config": config(), "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                 "agents_sha256": hashlib.sha256(raw).hexdigest(), "agents_bytes": len(raw),
                 "project_config_disabled": True, "home_is_private": True,
                 "audit_scope": "Configuration/discovery isolation; not a dump of the model's full system prompt"}


@contextmanager
def local_server(binary, work, env):
    """Keep one private server alive while the audit waits for plugin activation."""
    server_env = {**env, "OPENCODE_PASSWORD": secrets.token_urlsafe(32)}
    stderr_path = work.parent / "audit-server.stderr"
    with stderr_path.open("wb") as stderr:
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
                        raise ValueError("OpenCode audit server did not report readiness within 45 seconds")
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError(f"OpenCode audit server exited before readiness; see {stderr_path}")
                    data += chunk
            endpoint = json.loads(data.split(b"\n", 1)[0])["url"]
            yield {"url": endpoint, "env": server_env}
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
        raise ValueError(f"OpenCode {operation} failed: " + result["stderr"][-1500:])
    return json.loads(result["stdout"])


def live_audit(root, work, env, binary):
    # Inventory endpoints expose snapshots and do not wait for initial activation.
    # integration.list waits on Plugin.awaitActivation. All requests must share this server.
    with local_server(binary, work, env) as server:
        api(binary, work, server, "integration.list")
        entries = api(binary, work, server, "config.get")
        skills = api(binary, work, server, "skill.list")["data"]
        plugins = api(binary, work, server, "plugin.list")["data"]
    inventory = [{"id": p.get("id"), "source_type": p.get("source", {}).get("type"),
                  "status": p.get("state", {}).get("status")} for p in plugins]
    # Preserve a secret-free snapshot even when validation rejects discovery.
    (root / "discovery-probe.json").write_text(json.dumps({"plugins": inventory,
        "skill_ids": [s.get("id") if isinstance(s, dict) else str(s) for s in skills],
        "config_sources": [{"type": e.get("type"), "path": e.get("path")} for e in entries]}, indent=2) + "\n")
    expected_path = (root / "config/opencode/opencode.json").resolve()
    documents = [e for e in entries if e["type"] == "document"]
    if len(documents) != 1 or Path(documents[0].get("path", "")).resolve() != expected_path:
        raise ValueError("Unexpected configuration documents in OpenCode")
    for entry in entries:
        if entry.get("path") and not Path(entry["path"]).resolve().is_relative_to(root.resolve()):
            raise ValueError("Configuration discovery escaped the private runtime")
    actual = documents[0]["info"]
    expected = config()
    expected["model"] = {"providerID": "openai", "model": "gpt-6.1-sol", "variant": EFFORT}
    if actual != expected and actual != config():
        raise ValueError("Effective OpenCode configuration differs from the frozen configuration")
    if skills:
        raise ValueError("Unexpected skills in isolated catalog: " + json.dumps([s.get("id") for s in skills]))
    if not plugins:
        raise ValueError("OpenCode plugin inventory is empty after activation completed")
    external = [p for p in inventory if p["source_type"] != "builtin"]
    if external:
        raise ValueError("Unexpected non-builtin OpenCode plugins: " + json.dumps(external))
    ids = sorted(p["id"] for p in plugins)
    instruction = next((p for p in plugins if p.get("id") == "opencode.config.instruction"), None)
    if not instruction or instruction.get("state", {}).get("status") != "active":
        raise ValueError("AGENTS.md discovery plugin is not active")
    normalized = json.loads(json.dumps(entries).replace(str(root.resolve()), "<RUNTIME>"))
    return {"config_entries": normalized, "skills": [], "builtin_plugins": ids}


def audit_pair(root, texts, binary="opencode"):
    audits = {}
    for name, raw in texts.items():
        base = root / name
        work = base / "work"
        work.mkdir(parents=True)
        env, audit = prepare(base, work, raw, binary)
        audit["discovery"] = live_audit(base, work, env, binary)
        audits[name] = audit
    equal = audits["empty"]["discovery"] == audits["deterministic"]["discovery"]
    if not equal:
        raise ValueError("OpenCode discovery differs beyond treatment and temporary paths")
    return {"equal_configuration_and_discovery": True, "full_prompt_equality_verified": False,
            "model_inference_calls": 0, "variants": audits}


def argv(binary, work, final_path, prompt, sid=None):
    args = [binary, "run", "--standalone", "--auto", "--format", "json", "--model", SELECTION,
            "--agent", "build"]
    args += ["--session", sid] if sid else ["--title", "eval-trial"]
    return args + [prompt]


def session_id(stdout):
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    ids = {e["sessionID"] for e in events if e.get("sessionID")}
    if len(ids) != 1:
        raise ValueError("Expected one session ID in the OpenCode event stream")
    return ids.pop()


def parse_export(data, sid, work, expected_turns):
    info, messages = data["info"], data["messages"]
    if info["id"] != sid or info.get("model") != MODEL_REF:
        raise ValueError("Actual session/model/effort differs from the requested one")
    if Path(info["location"]["directory"]).resolve() != work.resolve():
        raise ValueError("Session ran in a different workspace")
    users = [i for i, m in enumerate(messages) if m["type"] == "user"]
    if len(users) != expected_turns:
        raise ValueError("Unexpected number of user turns in exported session")
    current = messages[users[-1] + 1:]
    idle = [m for m in current if m["type"] == "idle"]
    if not idle or idle[-1]["outcome"] != "succeeded":
        raise ValueError("OpenCode did not finish the latest turn successfully")
    assistants = [m for m in messages if m["type"] == "assistant"]
    if any(m.get("model") != MODEL_REF or m.get("agent") != "build" for m in assistants):
        raise ValueError("Assistant switched model, variant or agent during the trial")
    latest = [m for m in current if m["type"] == "assistant"]
    final = "\n".join(p["text"] for p in latest[-1]["content"] if p["type"] == "text") if latest else ""
    if not final.strip() or latest[-1].get("error"):
        raise ValueError("No final response after the latest prompt")
    usage = [m.get("tokens") for m in assistants]
    totals = {}
    for name, keys in {"input_tokens": ["input"], "output_tokens": ["output"],
                       "reasoning_tokens": ["reasoning"], "cached_input_tokens": ["cache", "read"],
                       "cache_write_tokens": ["cache", "write"]}.items():
        values = []
        for value in usage:
            for key in keys:
                value = value.get(key) if isinstance(value, dict) else None
            values.append(value)
        totals[name] = sum(values) if values and all(type(v) in (int, float) and v >= 0 for v in values) else None
    return {"session_id": sid, "final": final, "usage_raw": usage, **totals,
            "tools": [p for m in assistants for p in m["content"] if p["type"] == "tool"],
            "error_events": [m["error"] for m in assistants if m.get("error")],
            "reported_cost_usd": info.get("cost"), "actual_model": info["model"]}
