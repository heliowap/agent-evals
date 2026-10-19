import asyncio
import json
from pathlib import Path

import yaml
from opencode_v2_agent import download_binary

ROOT = Path(__file__).resolve().parent


async def command(*args, input=None, output_path=None):
    process = await asyncio.create_subprocess_exec(*args, stdin=asyncio.subprocess.PIPE if input else None,
                                                  stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    output, _ = await process.communicate(input.encode() if input else None)
    if output_path:
        output_path.write_text(output.decode())
    if process.returncode:
        raise RuntimeError(output.decode()[-4000:])
    return output.decode()


async def smoke(env, arm=None, output_dir=None):
    output_dir = output_dir or ROOT
    output_dir.mkdir(parents=True, exist_ok=True)
    binary = await asyncio.to_thread(download_binary, "arm64")
    name = "tbeval-opencode-v2-smoke"
    await command("docker", "run", "--detach", "--name", name, "--memory", "2g", "--cpus", "2",
                  "--security-opt", "no-new-privileges:true", "node:22-bookworm-slim", "sleep", "infinity")
    try:
        await command("docker", "cp", str(binary), name + ":/usr/local/bin/opencode")
        await command("docker", "exec", name, "sh", "-c", "mkdir -p /root/.config/opencode /app && chmod +x /usr/local/bin/opencode")
        config = yaml.safe_load((ROOT / "pilot.yaml").read_text())
        evidence = []
        for agent in config["agents"]:
            selected_arm = "glm" if agent["model_name"].startswith("opencode-go/") else "swe"
            if arm and selected_arm != arm:
                continue
            settings = agent["kwargs"]["opencode_config"]
            await command("docker", "exec", "-i", name, "sh", "-c", "cat > /root/.config/opencode/opencode.json", input=json.dumps(settings))
            variable = "TBEVAL_GLM_TOKEN" if agent["model_name"].startswith("opencode-go/") else "TBEVAL_SWE_TOKEN"
            model = agent["model_name"] + "#high"
            prompt = "Use the shell tool to compute 17 * 19 with python or node. Do not read any credentials or other files. Return the number."
            output = await command("docker", "exec", "--workdir", "/app", "-e", "TBEVAL_API_KEY=" + env[variable],
                                   "-e", f"XDG_DATA_HOME=/tmp/smoke-{selected_arm}/data",
                                   "-e", f"XDG_STATE_HOME=/tmp/smoke-{selected_arm}/state",
                                   name, "opencode", "run", "--standalone", "--auto", "--format", "json", "--model", model, prompt,
                                   output_path=output_dir / (variable.lower() + "-smoke.jsonl"))
            events = []
            for line in output.splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            errors = [e for e in events if e.get("type") == "error"]
            text = "\n".join(e.get("part", {}).get("text", "") for e in events if e.get("type") == "text")
            if errors or not any(e.get("type") == "tool_use" for e in events) or "323" not in text:
                raise RuntimeError(f"Smoke failed for {model}: " + output[-3000:])
            record = {"model": model, "event_types": sorted({e.get("type", "") for e in events}),
                      "tool_calls": sum(e.get("type") == "tool_use" for e in events)}
            evidence.append(record)
            print(json.dumps(record), flush=True)
        (output_dir / (f"smoke-evidence-{arm or 'both'}.json")).write_text(json.dumps(evidence, indent=2) + "\n")
    finally:
        await command("docker", "rm", "--force", name)
