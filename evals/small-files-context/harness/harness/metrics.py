"""Extract trial metrics from a Claude Code stream-json transcript.

Each API response appears as several `assistant` events sharing one message id
and repeating the same usage, so usage is counted once per message id. Input
usage is complete in those events; output usage is not, so output totals come
from the final `result` event.
"""
import json
import re

EXPECTED_TOOLS = ["Bash", "Edit", "Read"]
EXPECTED_MODEL = "claude-haiku-5-5"
NETWORK = re.compile(r"\b(curl|wget|pip3?\s+(install|download)|uv\s+(pip|add)|git\s+clone|"
                     r"https?://|python[\d.]*\s+-m\s+pip)\b")
FILE_PRINT = re.compile(r"(^|[|;&]\s*|\s)(cat|head|tail|sed|awk|grep|rg|less|more|nl|bat)\s")


def tokens_of(text):
    return len(text.encode("utf-8")) / 4


def result_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


def parse(path, repo_dir=None):
    init, result = None, None
    usage_by_msg, order = {}, []
    tool_uses, exposures = {}, []
    for line in open(path, encoding="utf-8"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            init = ev
        elif kind == "assistant":
            msg = ev["message"]
            if msg["id"] not in usage_by_msg:
                order.append(msg["id"])
            usage_by_msg[msg["id"]] = msg.get("usage", {})
            for block in msg.get("content", []):
                if block.get("type") == "tool_use":
                    tool_uses[block["id"]] = {"name": block["name"], "input": block.get("input", {})}
        elif kind == "user":
            content = ev.get("message", {}).get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_result" and block.get("tool_use_id") in tool_uses:
                    use = tool_uses[block["tool_use_id"]]
                    exposures.append({**use, "tokens": tokens_of(result_text(block.get("content"))),
                                      "is_error": bool(block.get("is_error"))})
        elif kind == "result":
            result = ev

    per_call = []
    for mid in order:
        u = usage_by_msg[mid]
        per_call.append(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                        + u.get("cache_creation_input_tokens", 0))
    sum_key = lambda k: sum(usage_by_msg[m].get(k, 0) for m in order)

    reads = [e for e in exposures if e["name"] == "Read"]
    bash = [e for e in exposures if e["name"] == "Bash"]
    file_prints = [e for e in bash if FILE_PRINT.search(" " + e["input"].get("command", ""))]
    read_paths = [e["input"].get("file_path", "") for e in reads]
    chunked = {p: read_paths.count(p) for p in set(read_paths) if read_paths.count(p) > 1}
    file_exposures = reads + file_prints
    commands = [e["input"].get("command", "") for e in bash]
    outside = [p for p in read_paths if repo_dir and not p.startswith(str(repo_dir))]

    tools = sorted(init.get("tools", [])) if init else []
    model_usage = sorted((result or {}).get("modelUsage", {}).keys())
    validity = {
        "init_seen": init is not None,
        "tools_ok": tools == EXPECTED_TOOLS,
        "model_ok": bool(init) and init.get("model") == EXPECTED_MODEL,
        "models_used": model_usage,
        "no_mcp": bool(init) and not init.get("mcp_servers"),
        "no_skills": bool(init) and not init.get("skills"),
        "plugins": [p.get("name") for p in (init or {}).get("plugins", [])],
    }
    validity["ok"] = all(validity[k] for k in ("init_seen", "tools_ok", "model_ok", "no_mcp", "no_skills")) \
        and model_usage in ([EXPECTED_MODEL], [])

    res_usage = (result or {}).get("usage", {})
    return {
        "validity": validity,
        "peak_context": max(per_call) if per_call else 0,
        "api_calls": len(order),
        "fresh_input_tokens": sum_key("input_tokens"),
        "cache_read_tokens": sum_key("cache_read_input_tokens"),
        "cache_creation_tokens": sum_key("cache_creation_input_tokens"),
        "output_tokens": res_usage.get("output_tokens"),
        "num_turns": (result or {}).get("num_turns"),
        "cost_usd": (result or {}).get("total_cost_usd"),
        "duration_ms": (result or {}).get("duration_ms"),
        "result_subtype": (result or {}).get("subtype"),
        "terminal_reason": (result or {}).get("terminal_reason"),
        "is_error": (result or {}).get("is_error"),
        "tool_calls": {n: sum(1 for e in tool_uses.values() if e["name"] == n)
                       for n in sorted({e["name"] for e in tool_uses.values()})},
        "file_exposure_tokens": round(sum(e["tokens"] for e in file_exposures)),
        "largest_exposure_tokens": round(max((e["tokens"] for e in file_exposures), default=0)),
        "exposures_over_5k": sum(1 for e in file_exposures if e["tokens"] > 5000),
        "read_calls": len(reads),
        "chunked_reads": chunked,
        "flags": {
            "network": [c for c in commands if NETWORK.search(c)],
            "reads_outside_repo": outside,
        },
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(parse(sys.argv[1]), indent=2))
