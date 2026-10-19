"""No-model isolation check: start a private `opencode serve` with build_env's env and list
skills/plugins/agents/config sources through its API. `opencode debug config` cannot be used for
this: it asks the shared background service, which ignores the caller's env.

Usage: python3 probe_static.py [workroot]
"""
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from sandbox import build_env

SKILL = "---\nname: code-review\ndescription: Review a pull request.\n---\nbody\n"


def query(env, directory, port=48731, warmup=15):
    p = subprocess.Popen(["opencode", "serve", "--port", str(port)], env=env, cwd=directory,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        pw = None
        while pw is None:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("opencode serve exited")
            if "password" in line:
                pw = line.split()[-1]
        auth = "Basic " + base64.b64encode(f"opencode:{pw}".encode()).decode()
        q = urllib.parse.urlencode({"location[directory]": str(directory)})
        get = lambda ep: json.load(urllib.request.urlopen(urllib.request.Request(
            f"http://127.0.0.1:{port}/api/{ep}?{q}", headers={"Authorization": auth}), timeout=60))
        get("config")
        time.sleep(warmup)  # skills/plugins register asynchronously after the first location request
        return {ep: get(ep) for ep in ("config", "skill", "plugin", "agent")}
    finally:
        p.terminate()
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="probe-static-"))
    snap = root / "snap"
    snap.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=snap, check=True)
    env = build_env(snap, SKILL)
    r = query(env, snap)
    skills = [(s["id"], s.get("path", "")) for s in r["skill"]["data"]]
    plugins = [p["source"].get("target") for p in r["plugin"]["data"] if p["source"]["type"] != "builtin"]
    agents = [a["id"] for a in r["agent"]["data"]]
    sources = [e.get("path") for e in r["config"] if e.get("type") == "document"]
    non_builtin = [s for s in skills if not s[1].startswith("/builtin/")]
    report = {"skills": skills, "non_builtin_plugins": plugins, "agents": agents, "config_documents": sources}
    print(json.dumps(report, indent=1))
    ok = [s[0] for s in non_builtin] == ["code-review"] and not plugins and "reviewer" in agents \
        and not any(s and str(Path.home() / ".config") in s for s in sources)
    print("STATIC", "CLEAN" if ok else "LEAK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
