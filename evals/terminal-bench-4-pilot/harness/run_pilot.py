import argparse
import asyncio
import json
import os
import secrets
import shutil
import subprocess
import time
from pathlib import Path

import aiohttp
import json5
from aiohttp import web

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
PORT = 18319


def credential(value):
    if value.startswith("{env:") and value.endswith("}"):
        return os.environ[value[5:-1]]
    if value.startswith("{file:") and value.endswith("}"):
        return Path(value[6:-1]).expanduser().read_text().strip()
    return value


def active_go_key():
    result = subprocess.run(
        ["opencode", "api", "get", "/api/credential"],
        text=True, capture_output=True, timeout=30, check=False,
    )
    if result.returncode:
        raise RuntimeError("Could not read active credentials through the OpenCode API")
    entries = json.loads(result.stdout)["data"]
    active = [entry for entry in entries if entry["integrationID"] == "opencode-go" and entry["active"]]
    if len(active) != 1 or active[0]["value"]["type"] != "key":
        raise RuntimeError("Expected one active OpenCode Go API key")
    return active[0]["value"]["key"]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--arm", choices=("glm", "swe"))
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    config = json5.loads((Path.home() / ".config/opencode/opencode.jsonc").read_text())
    proxy = config["providers"]["cli_proxy_openai"]["settings"]
    go_key = active_go_key()
    routes = {
        "glm": {"base": "https://opencode.ai/zen/go/v1", "key": go_key, "model": "glm-5.3-flash"},
        "swe": {"base": proxy["baseURL"], "key": credential(proxy["apiKey"]), "model": "devin/swe-2"},
    }
    tokens = {name: secrets.token_urlsafe(32) for name in routes}
    env = dict(os.environ)
    env.update(TBEVAL_GLM_TOKEN=tokens["glm"], TBEVAL_SWE_TOKEN=tokens["swe"])
    env["PYTHONPATH"] = str(ROOT)
    env["TMPDIR"] = "/private/tmp/opencode"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = ROOT / f"gateway-{stamp}.jsonl"
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=300))

    async def forward(request):
        arm, path = request.match_info["arm"], request.match_info["path"]
        route = routes.get(arm)
        if route is None or not secrets.compare_digest(request.headers.get("Authorization", ""), "Bearer " + tokens[arm]):
            raise web.HTTPUnauthorized()
        if request.method == "GET" and path == "models":
            return web.json_response({"object": "list", "data": [{"id": route["model"], "object": "model"}]})
        if request.method != "POST" or path != "chat/completions":
            raise web.HTTPForbidden()
        body = await request.json()
        if body.get("model") != route["model"]:
            raise web.HTTPForbidden()
        headers = {"Authorization": "Bearer " + route["key"], "Content-Type": "application/json"}
        for key in ("User-Agent", "x-opencode-session"):
            if key in request.headers:
                headers[key] = request.headers[key]
        start = time.monotonic()
        entry = {"arm": arm, "model": body["model"], "reasoning_effort": body.get("reasoning_effort"),
                 "stream": body.get("stream"), "tools": len(body.get("tools", [])),
                 "session_present": bool(headers.get("x-opencode-session"))}
        try:
            async with session.post(route["base"] + "/chat/completions", json=body, headers=headers) as upstream:
                entry["status"] = upstream.status
                response = web.StreamResponse(status=upstream.status, headers={"Content-Type": upstream.headers.get("Content-Type", "application/json")})
                await response.prepare(request)
                async for chunk in upstream.content.iter_any():
                    await response.write(chunk)
                await response.write_eof()
                return response
        except (aiohttp.ClientError, ConnectionError, asyncio.TimeoutError) as error:
            entry["error_type"] = type(error).__name__
            raise web.HTTPBadGateway()
        finally:
            entry["seconds"] = round(time.monotonic() - start, 3)
            with log.open("a") as file:
                file.write(json.dumps(entry) + "\n")

    app = web.Application(client_max_size=32 * 1024 * 1024)
    app.router.add_route("*", "/{arm}/v1/{path:.*}", forward)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", PORT)
    proc = None
    try:
        if not args.dry_run:
            await site.start()
        if args.smoke:
            from smoke import smoke
            await smoke(env, args.arm, ROOT / "validation" / stamp)
            return
        if args.resume:
            job = args.resume.resolve()
            for trial in job.iterdir():
                if not trial.is_dir() or not (trial / "config.json").exists():
                    continue
                result_path = trial / "result.json"
                result = json.loads(result_path.read_text()) if result_path.exists() else {}
                if result and (result.get("exception_info") or {}).get("exception_type") != "CancelledError":
                    continue
                archive = ROOT / "interruptions" / f"{job.name}-{stamp}" / trial.name
                archive.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(trial), str(archive))
                print(f"Archived interrupted trial: {archive}", flush=True)
            command = [str(WORKSPACE / ".venv/bin/harbor"), "job", "resume", "--job-path", str(job)]
        else:
            command = [str(WORKSPACE / ".venv/bin/harbor"), "run", "--config", str(ROOT / "pilot.yaml"),
                       "--job-name", "tb4-pilot-" + stamp]
        if args.dry_run:
            command.append("--dry-run")
        if args.install_only:
            command.append("--install-only")
        print("Validating preflight without execution." if args.dry_run else "Authenticated loopback gateway active; starting pilot.", flush=True)
        proc = await asyncio.create_subprocess_exec(*command, cwd=WORKSPACE, env=env)
        code = await proc.wait()
        if code:
            raise RuntimeError(f"Harbor exited {code}")
    finally:
        if proc is not None and proc.returncode is None:
            proc.terminate()
            await proc.wait()
        await runner.cleanup()
        await session.close()
        print("Gateway stopped; temporary tokens revoked.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
