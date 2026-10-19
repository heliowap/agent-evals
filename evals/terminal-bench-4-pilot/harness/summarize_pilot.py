import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def seconds(phase):
    if not phase or not phase.get("started_at") or not phase.get("finished_at"):
        return None
    return round((datetime.fromisoformat(phase["finished_at"]) - datetime.fromisoformat(phase["started_at"])).total_seconds(), 2)


def summarize(job):
    config = yaml.safe_load((ROOT / "pilot.yaml").read_text())
    rows = []
    for path in sorted(job.glob("*/result.json")):
        result = json.loads(path.read_text())
        if not result.get("finished_at"):
            continue
        agent = result["config"]["agent"]
        rewards = (result.get("verifier_result") or {}).get("rewards") or {}
        reward = rewards.get("reward")
        if reward is None and len(rewards) == 1:
            reward = next(iter(rewards.values()))
        error = result.get("exception_info")
        rows.append({
            "task": result["task_name"], "model": agent["model_name"],
            "variant": agent["kwargs"].get("variant"), "reward": reward,
            "passed": not error and reward is not None and reward > 0,
            "error_type": error["exception_type"] if error else None,
            "agent_seconds": seconds(result.get("agent_execution")),
            "trial_seconds": seconds(result), "metrics": result.get("agent_result"),
            "result_path": str(path),
        })
    expected_per_model = len(config["datasets"][0]["task_names"]) * config["n_attempts"]
    aggregates = []
    for agent in config["agents"]:
        trials = [row for row in rows if row["model"] == agent["model_name"]]
        costs = [(trial["metrics"] or {}).get("cost_usd") for trial in trials]
        complete = len(trials) == expected_per_model
        aggregates.append({
            "model": agent["model_name"], "variant": agent["kwargs"]["variant"],
            "finished": len(trials), "expected": expected_per_model,
            "passed": sum(trial["passed"] for trial in trials),
            "errors": sum(trial["error_type"] is not None for trial in trials),
            "accuracy": sum(trial["passed"] for trial in trials) / expected_per_model if complete else None,
            "reported_cost_usd": sum(cost for cost in costs if cost is not None) if any(cost is not None for cost in costs) else None,
            "cost_coverage": sum(cost is not None for cost in costs),
            "agent_seconds": round(sum(trial["agent_seconds"] or 0 for trial in trials), 2),
        })
    summary = {"job": str(job), "scope": "3-task TB4 pilot, k=1; not an official score", "models": aggregates, "trials": rows}
    (job / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = ["# TB4 pilot — GLM-5.3-Flash vs SWE-2", "", "3-task subset, k=1. Not an official score and not a sample large enough for a general ranking.", "",
             "| Model (high) | Finished | Passed | Errors | Reported cost USD |", "| --- | ---: | ---: | ---: | ---: |"]
    for model in aggregates:
        cost = model["reported_cost_usd"]
        cost_text = f"{cost:.6f} ({model['cost_coverage']}/{model['finished']} trials)" if cost is not None else "not reported"
        lines.append(f"| {model['model']} | {model['finished']}/{model['expected']} | {model['passed']} | {model['errors']} | {cost_text} |")
    lines.extend(["", "| Task | Model | Reward | Error | Agent time (s) |", "| --- | --- | ---: | --- | ---: |"])
    for row in rows:
        lines.append(f"| {row['task']} | {row['model']} | {row['reward']} | {row['error_type'] or '—'} | {row['agent_seconds']} |")
    lines.extend(["", "Errors stay in the denominator. Missing/zero cost does not prove the model was free, especially on the local proxy. Costs are harness telemetry, not an invoice; earlier integration tests are not included in this sum.",
                  "", "Input tokens include cache; do not add cache again. Durations reflect local Docker Desktop, possibly with amd64 emulation on an ARM64 Mac. No official CI was computed because k=1."])
    (job / "comparison.md").write_text("\n".join(lines) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("job", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.job)["models"], indent=2))
