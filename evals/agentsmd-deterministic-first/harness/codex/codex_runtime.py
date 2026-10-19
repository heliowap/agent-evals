"""Codex CLI adapter with an audited, process-local instruction environment."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

VERSION = "codex-cli 0.162.1"
MODEL = "gpt-6.1-sol"
EFFORT = "xhigh"


def command(argv, work, env, timeout):
    start = time.monotonic()
    process = subprocess.Popen(argv, cwd=work, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
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
            "wall_s": time.monotonic() - start,
            "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")}


def config_text(disabled=()):
    return '\n'.join([
        f'model = "{MODEL}"', f'model_reasoning_effort = "{EFFORT}"',
        'sandbox_mode = "workspace-write"', 'approval_policy = "never"',
        'web_search = "disabled"', '[features]', 'plugins = false', 'apps = false',
        'hooks = false', 'multi_agent = false', 'memories = false', 'shell_snapshot = false',
        '[skills]', 'config = [' + ', '.join('{path = ' + json.dumps(p) + ', enabled = false}' for p in disabled) + ']', ''])


def text_parts(messages):
    return [c.get("text", "") for m in messages for c in m.get("content", [])]


def prepare(root, work, raw, binary="codex", auth_file=None):
    codex_state = root / "codex-state"
    codex_state.mkdir()
    tmp = root / "tmp"
    tmp.mkdir()
    # This changes only the child process's supported config root, never the user's shell/config.
    env = {"PATH": os.environ.get("PATH", os.defpath), "LANG": "en_US.UTF-8",
           "CODEX_HOME": str(codex_state), "TMPDIR": str(tmp), "PWD": str(work),
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "Eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
           "GIT_COMMITTER_NAME": "Eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid",
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    (codex_state / "AGENTS.md").write_bytes(raw)
    config = codex_state / "config.toml"
    config.write_text(config_text())
    git = command(["git", "init", "-q", "--template=", "-b", "main"], work, env, 15)
    if git["exit_code"]:
        raise ValueError("Cannot initialize isolated project")
    version = command([binary, "--version"], work, env, 15)
    if version["exit_code"] or version["stdout"].strip() != VERSION:
        raise ValueError("Codex version differs from pinned version")
    # Discover the actual catalog offline, then disable every exposed SKILL.md.
    # In 0.162.1 folder paths do not disable a skill; its SKILL.md path does.
    probe = command([binary, "--no-daemon", "debug", "prompt-input", "EVAL_CONTEXT_PROBE"], work, env, 25)
    if probe["exit_code"]:
        raise ValueError("Cannot inspect Codex's model-visible context: " + probe["stderr"][-500:])
    discovered = json.loads(probe["stdout"])
    disabled = []
    for text in text_parts(discovered):
        roots = dict(re.findall(r'- `(r\d+)` = `([^`]+)`', text))
        for alias, relative in re.findall(r'\(file: (r\d+)/([^\n]+?)\)', text):
            disabled.append(str(Path(roots[alias]) / relative))
    config.write_text(config_text(sorted(set(disabled))))
    probe = command([binary, "--no-daemon", "debug", "prompt-input", "EVAL_CONTEXT_PROBE"], work, env, 25)
    if probe["exit_code"]:
        raise ValueError("Context audit failed")
    messages = json.loads(probe["stdout"])
    texts = text_parts(messages)
    if any("<skills_instructions>" in text for text in texts):
        raise ValueError("Skills still present in evaluated context")
    instruction_messages = [t for t in texts if "# AGENTS.md instructions" in t]
    if raw:
        if len(instruction_messages) != 1:
            raise ValueError("Expected exactly one AGENTS.md source")
        body = re.search(r'<INSTRUCTIONS>\s*([\s\S]*?)\s*</INSTRUCTIONS>', instruction_messages[0])
        if not body or body.group(1).strip() != raw.decode().strip():
            raise ValueError("Effective AGENTS.md differs from treatment")
    elif instruction_messages:
        raise ValueError("Empty control inherited AGENTS.md instructions")
    if auth_file:
        shutil.copyfile(auth_file, codex_state / "auth.json")
        (codex_state / "auth.json").chmod(0o600)
    return env, {"version": VERSION, "model": MODEL, "effort": EFFORT,
                 "disabled_skills": len(disabled), "context": messages,
                 "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                 "agents_sha256": hashlib.sha256(raw).hexdigest(), "agents_bytes": len(raw)}


def argv(binary, work, final_path, prompt, sid=None):
    args = [binary, "--no-daemon", "exec"]
    if sid:
        args += ["resume"]
    else:
        args += ["--sandbox", "workspace-write", "--cd", str(work)]
    args += ["--model", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"',
             "--ignore-rules", "--json", "--output-last-message", str(final_path)]
    if sid:
        args += [sid]
    return args + [prompt]


def normalized_context(audit):
    texts = text_parts(audit["context"])
    cwd = next(re.search(r'<cwd>([^<]+)</cwd>', text).group(1) for text in texts if "<cwd>" in text)
    root = str(Path(cwd).parent)
    messages = []
    for message in audit["context"]:
        text = "\n".join(c.get("text", "") for c in message.get("content", []))
        text = re.sub(r'# AGENTS.md instructions[\s\S]*?</INSTRUCTIONS>', "", text).strip()
        if text:
            messages.append({"role": message["role"], "text": text.replace(root, "<RUNTIME>")})
    return messages


def audit_pair(root, texts, binary="codex"):
    audits = {}
    for name, raw in texts.items():
        base = root / name
        work = base / "work"
        work.mkdir(parents=True)
        _, audit = prepare(base, work, raw, binary)
        audits[name] = audit
    equal = normalized_context(audits["empty"]) == normalized_context(audits["deterministic"])
    if not equal:
        raise ValueError("Model-visible context differs beyond treatment and temporary paths")
    return {"equal_except_treatment": True, "normalization": "Model-visible role/text only; remove treatment wrapper and normalize temporary root paths. IDs and internal timestamps are not prompt text.", "conditions": audits}


def parse(stdout):
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    started = [e["thread_id"] for e in events if e.get("type") == "thread.started"]
    failures = [e for e in events if e.get("type") == "turn.failed"]
    completed = [e for e in events if e.get("type") == "turn.completed"]
    if not started or failures or len(completed) != 1:
        raise ValueError("No unique completed Codex turn: " + json.dumps(failures)[:400])
    items = [e["item"] for e in events if e.get("type") == "item.completed"]
    texts = [i.get("text", "") for i in items if i.get("type") == "agent_message"]
    if not texts:
        raise ValueError("No final agent message")
    return {"session_id": started[-1], "final": texts[-1], "usage": completed[0].get("usage"),
            "error_events": [e for e in events if e.get("type") == "error"],
            "tools": [i for i in items if i.get("type") in {"command_execution", "file_change", "mcp_tool_call", "web_search"}]}
