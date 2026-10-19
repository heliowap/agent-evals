"""Read native per-response usage, deduplicated across all saved Codex rollouts."""
import json
import re
from collections import Counter

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
COMMUNICATION = {"spawn_agent", "send_message", "followup_task"}


def read_events(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def totals(records):
    return {key: sum(r["usage"][key] for r in records)
            if records and all(type(r["usage"].get(key)) is int for r in records) else None
            for key in FIELDS}


def collect(paths, root_id, model, effort, cli_usage):
    threads, records, messages, calls = {}, {}, [], []
    encrypted_values = set()
    issues = []
    for path in paths:
        events = read_events(path)
        metas = [e["payload"] for e in events if e.get("type") == "session_meta"]
        if not metas:
            issues.append(f"missing_session_meta:{path.name}")
            continue
        meta = metas[-1]
        tid = meta["id"]
        if tid in threads:
            issues.append(f"duplicate_session:{tid}")
        source = meta.get("source")
        spawn = source.get("subagent", {}).get("thread_spawn", {}) if isinstance(source, dict) else {}
        thread = {"id": tid, "parent": spawn.get("parent_thread_id"),
                  "agent_path": spawn.get("agent_path", "/root"), "forked_from": meta.get("forked_from_id"),
                  "models": set(), "efforts": set(), "started": set(), "completed": set(),
                  "final": "", "errors": [], "last_usage": None}
        threads[tid] = thread
        for event in events:
            p = event.get("payload", {})
            kind = event.get("type")
            if kind == "turn_context":
                thread["models"].add(p.get("model"))
                thread["efforts"].add(p.get("effort"))
            elif kind == "token_usage_record":
                if p.get("thread_id") != tid:
                    issues.append(f"foreign_usage_record:{tid}")
                key = (p.get("thread_id"), p.get("response_id"))
                if not all(key):
                    issues.append("usage_record_without_identity")
                    continue
                previous = records.get(key)
                if previous and previous["usage"] != p["usage"]:
                    issues.append(f"conflicting_usage:{key}")
                records[key] = p
                thread["last_usage"] = p.get("thread_token_usage")
            elif kind == "event_msg":
                if p.get("type") == "task_started":
                    thread["started"].add(p.get("turn_id"))
                elif p.get("type") == "task_complete":
                    thread["completed"].add(p.get("turn_id"))
                    thread["final"] = p.get("last_agent_message") or ""
                elif p.get("type") in {"error", "turn_aborted", "task_failed"}:
                    thread["errors"].append(p)
            elif kind == "response_item":
                encrypted_values.update(c["encrypted_content"] for c in p.get("content", [])
                                        if c.get("type") == "encrypted_content" and isinstance(c.get("encrypted_content"), str))
                tool = p.get("name", "").split(".")[-1]
                if p.get("type") in {"function_call", "custom_tool_call"}:
                    call = {"thread_id": tid, "tool": tool, "call_id": p.get("call_id")}
                    calls.append(call)
                    if tool in COMMUNICATION:
                        try:
                            args = json.loads(p.get("arguments", "{}"))
                        except ValueError:
                            args = {}
                            issues.append("unreadable_communication_arguments")
                        call["args"] = args
                        messages.append({"thread_id": tid, "kind": tool, "text": args.get("message", ""),
                                         "language": None})

    root = threads.get(root_id)
    if root is None:
        issues.append("root_rollout_missing")
    for tid, thread in threads.items():
        own = [r for (rid, _), r in records.items() if rid == tid]
        thread["usage"] = totals(own)
        thread["responses"] = len(own)
        if not own or any(thread["usage"][k] is None for k in ("input_tokens", "output_tokens", "total_tokens")):
            issues.append(f"missing_usage:{tid}")
        elif thread["usage"]["input_tokens"] + thread["usage"]["output_tokens"] != thread["usage"]["total_tokens"]:
            issues.append(f"inconsistent_token_total:{tid}")
        if thread["last_usage"] is None or any(thread["usage"][k] != thread["last_usage"].get(k)
                                                for k in ("input_tokens", "output_tokens", "total_tokens")):
            issues.append(f"response_sum_differs_from_thread_counter:{tid}")
        if thread["models"] != {model} or thread["efforts"] != {effort}:
            issues.append(f"model_or_effort_mismatch:{tid}")
        if not thread["started"] or thread["started"] != thread["completed"]:
            issues.append(f"unfinished_turns:{tid}")
        if thread["errors"]:
            issues.append(f"thread_errors:{tid}")
        if tid != root_id:
            if thread["parent"] != root_id or thread["forked_from"]:
                issues.append(f"unexpected_parent_or_fork:{tid}")
            messages.append({"thread_id": tid, "kind": "subagent_final", "text": thread["final"], "language": None})
            if not thread["final"]:
                issues.append(f"missing_subagent_final:{tid}")
        for key in ("models", "efforts", "started", "completed"):
            thread[key] = sorted(thread[key], key=str)

    spawns = [c for c in calls if c["tool"] == "spawn_agent"]
    protocol = (len(threads) == 3 and len(spawns) == 2
                and all(c["thread_id"] == root_id and c.get("args", {}).get("fork_turns") == "none" for c in spawns)
                and all(t["parent"] == root_id and not t["forked_from"] for t in threads.values() if t["id"] != root_id))
    usage = totals(list(records.values()))
    root_usage = root["usage"] if root else {}
    # Some CLI versions expose root-only totals; others aggregate the team. Never add them.
    cli_scope = next((scope for scope, counter in [("root", root_usage), ("team", usage)]
                      if all(cli_usage.get(k) == counter.get(k) and cli_usage.get(k) is not None
                             for k in ("input_tokens", "output_tokens"))), "unreconciled")
    if cli_scope == "unreconciled":
        issues.append("cli_usage_not_reconciled")
    for message in messages:
        if message["text"] in encrypted_values or re.fullmatch(r"gAAAA[A-Za-z0-9_-]{75,}={0,2}", message["text"]):
            message.update(text=None, language="unobservable", observability="encrypted")
        elif not message["text"]:
            message.update(language="unobservable", observability="missing")
        else:
            message["observability"] = "readable"
    visibility = dict(Counter(m["observability"] for m in messages))
    return {"usage": usage, "root_usage": root_usage,
            "subagent_usage": totals([r for (tid, _), r in records.items() if tid != root_id]),
            "response_count": len(records), "tool_calls": dict(Counter(c["tool"] for c in calls)),
            "subagents": max(0, len(threads) - int(root is not None)), "protocol_pass": protocol,
            "measurement_valid": not issues, "issues": issues, "cli_usage_scope": cli_scope,
            "threads": list(threads.values()), "communications": messages,
            "communication_observability": visibility,
            "language_audit_complete": bool(messages) and all(m["observability"] == "readable" for m in messages)}
