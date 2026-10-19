"""Audit real execution accounting, without inventing a compatibility exercise."""

import argparse
from collections import Counter
import json
from pathlib import Path

from .storage import digest


def audit_execution(execution, runtime, ledger_path=None):
    execution = Path(execution)
    ledger_path = Path(ledger_path) if ledger_path else execution / "ledger.jsonl"
    if not ledger_path.exists():
        return {"status": "not_executed", "errors": [], "trials": 0}
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
    if not rows:
        return {"status": "not_executed", "errors": [], "trials": 0}
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    reservations = [row for row in rows if row["event"] == "reserve"]
    check(len({r["trial_id"] for r in reservations}) == len(reservations), "duplicate reservations")
    for event in ("intent", "start", "response", "terminal", "tool_intent", "tool_start", "tool_result"):
        keys = [(r["trial_id"], r.get("step"), r.get("index")) for r in rows if r["event"] == event]
        check(len(keys) == len(set(keys)), "duplicate " + event)
    configs = {c["id"]: c for c in runtime["configurations"]}
    for lease in reservations:
        trial_id = lease["trial_id"]
        directory = Path(lease["directory"])
        check(directory.resolve().is_relative_to(execution.resolve()), trial_id + ": directory outside execution")
        if not directory.resolve().is_relative_to(execution.resolve()):
            continue
        record_path = directory / "record.json"
        if not record_path.exists():
            errors.append(trial_id + ": missing record")
            continue
        record = json.loads(record_path.read_text())
        events = [r for r in rows if r["trial_id"] == trial_id]
        suite = runtime["suites"][record["suite"]]
        configuration = configs.get(record["configuration_id"], {})
        check(record["trial_id"] == trial_id, trial_id + ": record identity")
        terminals = [r for r in events if r["event"] == "terminal"]
        check(len(terminals) == 1, trial_id + ": missing terminal")
        if terminals:
            check(digest(record_path.read_bytes()) == terminals[0]["record_sha256"], trial_id + ": terminal hash")
        intents = [r for r in events if r["event"] == "intent"]
        starts = [r for r in events if r["event"] == "start"]
        requests = record["requests"]
        check(len(requests) == len(intents), trial_id + ": intent accounting")
        check(len(requests) <= suite["model_steps"], trial_id + ": model step cap")
        check(sum(r["starts"] for r in requests) == len(starts), trial_id + ": starts accounting")
        prior_assistants = []
        for request in requests:
            prefix = trial_id + ": step " + str(request["step"])
            path = directory / request["request_path"]
            check(path.resolve().is_relative_to(directory.resolve()), prefix + ": unsafe request path")
            if not path.exists() or not path.resolve().is_relative_to(directory.resolve()):
                errors.append(prefix + ": missing request")
                continue
            body = json.loads(path.read_text())
            check(digest(path.read_bytes()) == request["request_sha256"], prefix + ": request hash")
            check([m for m in body["messages"] if m["role"] == "assistant"] == prior_assistants,
                  prefix + ": native history lost or reconstructed")
            if "gemini" in configuration.get("model", "").lower():
                tail = body["messages"][-1]
                check(tail.get("role") == "user" and isinstance(tail.get("content"), str)
                      and bool(tail["content"].strip()), prefix + ": illegal Gemini tail")
            if request["step"] == suite["model_steps"]:
                check("tools" not in body, prefix + ": tools exposed at final step")
                check(body["messages"][-1] == {"role": "user", "content": runtime["last_step_instruction"]},
                      prefix + ": missing final instruction")
            if request.get("assistant"):
                prior_assistants.append(request["assistant"])
            if request.get("response_path"):
                response = directory / request["response_path"]
                check(response.resolve().is_relative_to(directory.resolve()) and response.exists() and
                      digest(response.read_bytes()) == request["response_sha256"], prefix + ": response hash")
            check(request["starts"] in (0, 1), prefix + ": repeated send")
            check(not request["starts"] or any(e["event"] == "intent" and e.get("step") == request["step"]
                                              for e in events), prefix + ": start without intent")
        calls = record["tool_calls"]
        check(len(calls) == sum(e["event"] == "tool_intent" for e in events), trial_id + ": tool intent accounting")
        counts = Counter()
        total_visible = 0
        for index, call in enumerate(calls, 1):
            counts[call["name"]] += 1
            check(call["index"] == index and call["name_attempt"] == counts[call["name"]],
                  trial_id + ": tool request accounting")
            allowed = (counts[call["name"]] <= suite["tool_limits"].get(call["name"], 0)
                       if "tool_limits" in suite else index <= suite["tool_calls"])
            check(not call["dispatched"] or allowed, trial_id + ": dispatch above tool cap")
            check(not call["dispatched"] or call["step"] < suite["model_steps"], trial_id + ": final-step dispatch")
            check(call["dispatched"] == any(e["event"] == "tool_start" and e.get("index") == index for e in events),
                  trial_id + ": tool start accounting")
            visible = call.get("visible_characters", 0)
            check(0 <= visible <= runtime["limits"]["result_characters"], trial_id + ": per-result evidence cap")
            total_visible += visible
            if call.get("visible_path"):
                path = directory / call["visible_path"]
                if path.resolve().is_relative_to(directory.resolve()) and path.exists():
                    payload = json.loads(path.read_text())
                    check(len(payload["text"]) == visible, trial_id + ": visible character accounting")
                    check(not call["truncated"] or payload["truncated"], trial_id + ": silent truncation")
                else:
                    errors.append(trial_id + ": missing visible evidence")
        check(total_visible == record["evidence_characters"] and total_visible <= suite["evidence_characters"],
              trial_id + ": cumulative evidence cap")
        cycles = len({c["step"] for c in calls if c["dispatched"]})
        check(cycles == record["tool_cycles"], trial_id + ": tool cycle accounting")
        check(bool(record["final_answer"].strip()) if record["operational_complete"] else not record["final_answer"],
              trial_id + ": nonanswer accounting")
        if record["operational_complete"]:
            check(record["status"] == "completed" and requests[-1]["finish_reason"] == "stop" and
                  record["monotonic_end"] < record["deadline"], trial_id + ": invalid completion")
    reserved_ids = {r["trial_id"] for r in reservations}
    check(all(r["trial_id"] in reserved_ids for r in rows), "events without reservation")
    return {"status": "failed" if errors else "passed", "errors": errors, "trials": len(reservations),
            "starts": sum(r["event"] == "start" for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution", required=True, type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parents[2] / "contracts/runtime.json")
    args = parser.parse_args()
    result = audit_execution(args.execution, json.loads(args.runtime.read_text()), args.ledger)
    print(json.dumps(result, indent=2))
    return int(result["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
