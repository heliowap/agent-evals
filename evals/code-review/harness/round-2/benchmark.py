"""Freeze, run and audit the second code-review benchmark (stdlib only)."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import random
import re
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from prompts import render_prompt


ROOT = Path(__file__).resolve().parent
TEMP_ROOT = Path("/tmp/opencode")
SEED = 20260926
OPENROUTER_LIMIT = 10.0
REVIEW_AGENT = "benchmark-review"
# V2's effective policy is an ordered permission array. The closest .opencode
# config wins over global configuration; agent rules are appended last.
DENY_ALL = [{"action": "*", "resource": "*", "effect": "deny"}]
TOOL_POLICY = {
    "permissions": DENY_ALL,
    "agents": {REVIEW_AGENT: {
        "description": "Tool-free, source-only code-review benchmark",
        "mode": "primary",
        "system": "Respond from the provided text only; never call tools.",
        "permissions": DENY_ALL,
    }},
}
# Listed catalog prices, not a substitute for the per-session reported charge.
ROUTE_PRICES_USD_PER_MILLION = {
    "openrouter/z-ai/glm-5.3-flash": {"input": 0.04, "output": 0.5},
    "openrouter/deepseek/deepseek-v4.1-flash": {"input": 0.3, "output": 1.2},
    "openrouter/xiaomi/mimo-v2.6-flash": {"input": 0.14, "output": 0.28},
}
# OpenRouter's 2026-09-26 catalog lists the top provider's context and maximum
# completion tokens. Reserving both maxima plus USD 0.10 is deliberately
# conservative; an account-side limit is needed for an absolute billing cap.
OPENROUTER_TOKEN_LIMITS = {
    "openrouter/z-ai/glm-5.3-flash": {"input": 1048576, "output": 131072},
    "openrouter/deepseek/deepseek-v4.1-flash": {"input": 1048576, "output": 943718},
    "openrouter/xiaomi/mimo-v2.6-flash": {"input": 1048576, "output": 131072},
}
MODELS = tuple(
    f"openai/gpt-6-luna{suffix}#{effort}"
    for effort in ("high", "xhigh", "max") for suffix in ("", "-fast")
) + tuple(f"openai/gpt-6-sol#{effort}" for effort in ("low", "medium", "high", "xhigh", "max")) + tuple(
    f"cli_proxy/gemini-3.8-flash#{effort}" for effort in ("low", "medium", "high")
) + tuple(f"cli_proxy/devin/swe-2#{effort}" for effort in ("medium", "high", "max")) + tuple(
    f"cli_proxy/cpa-claude-opus-5-5#{effort}" for effort in ("low", "medium", "high")
) + tuple(f"openrouter/z-ai/glm-5.3-flash#{effort}" for effort in ("high", "max")) + tuple(
    f"openrouter/deepseek/deepseek-v4.1-flash#{effort}" for effort in ("high", "max")
) + ("openrouter/xiaomi/mimo-v2.6-flash#none",)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def build_manifest(cases, seed=SEED):
    if len(cases) != 3 or len({case["id"] for case in cases}) != 3:
        raise ValueError("Exactly three distinct cases required")
    if len({case["repo"] for case in cases}) != 3:
        raise ValueError("Cases must come from three different repositories")
    cells = [
        {"id": f"{case['id']}-{axis}-m{index:02}-r{repeat}", "case": case["id"],
         "axis": axis, "model": model, "repeat": repeat}
        for case in cases for axis in ("standards", "spec")
        for index, model in enumerate(MODELS) for repeat in (1, 2)
    ]
    random.Random(seed).shuffle(cells)
    return {"seed": seed, "models": list(MODELS), "case_ids": [case["id"] for case in cases],
            "tool_policy_sha256": digest(json_bytes(TOOL_POLICY)),
            "route_prices_usd_per_million": ROUTE_PRICES_USD_PER_MILLION,
            "openrouter_token_limits": OPENROUTER_TOKEN_LIMITS,
            "pricing_source": "OpenCode model catalog and https://openrouter.ai/api/v1/models on 2026-09-26; listed USD per million tokens, not actual billing",
            "prompt_hashes": {f"{case['id']}:{axis}": digest(render_prompt(case, axis).encode())
                              for case in cases for axis in ("standards", "spec")},
            "cells": cells}


def validate_fixtures(cases):
    if len(cases) != 3 or len({case.get("repo") for case in cases}) != 3:
        raise ValueError("three distinct repositories required")
    for case in cases:
        for key in ("id", "repo", "issue", "pr", "commits", "diff", "context", "standards"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"{case.get('id', '<unknown>')}: missing {key}")
        for key in ("base", "head"):
            if not re.fullmatch(r"[0-9a-f]{40}", case.get(key, "")):
                raise ValueError(f"{case['id']}: invalid {key} SHA")
        if not case["diff"].startswith("diff --git "):
            raise ValueError(f"{case['id']}: missing pinned diff")
        if (not case.get("sources") or
                not all(url.startswith(("https://github.com/", "https://docs.pytest.org/en/8.4.x/"))
                        for url in case["sources"])):
            raise ValueError(f"{case['id']}: missing primary sources")


def validate_rubric(cases, rubric):
    if any(word in rubric.upper() for word in ("RASCUNHO", "NÃO CONGELADO", "FALTA UM TERCEIRO")):
        raise ValueError("draft rubric cannot be frozen")
    positions = {case["head"]: rubric.find(case["head"]) for case in cases}
    if any(position < 0 for position in positions.values()):
        raise ValueError("rubric missing a pinned case head")
    for case in cases:
        start = positions[case["head"]]
        end = min((position for position in positions.values() if position > start), default=len(rubric))
        section = rubric[start:end]
        if "*Spec*" not in section or "*Standards*" not in section:
            raise ValueError(f"rubric missing an axis for {case['id']}")


def inputs(root=ROOT):
    return {name: digest((root / name).read_bytes())
            for name in ("fixtures.json", "prompts.py", "grading-rubric.md", "benchmark.py",
                         "blind.py", "prepare_fixtures.py")}


def frozen_manifest(root=ROOT):
    cases = json.loads((root / "fixtures.json").read_text())
    validate_fixtures(cases)
    validate_rubric(cases, (root / "grading-rubric.md").read_text())
    path = root / "manifest.json"
    data = json.loads(path.read_text())
    expected = build_manifest(cases, data["seed"])
    expected["inputs"] = inputs(root)
    if data != expected:
        raise ValueError("Frozen manifest mismatch: sources, matrix or queue changed")
    return cases, data


def atomic_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".writing-", delete=False) as tmp:
        temporary = Path(tmp.name)
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.write("\n")
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        os.link(temporary, path)  # Exclusive: never replace a previous result or attempt.
    finally:
        temporary.unlink()


def expected_identity(model):
    provider, model_id = model.split("/", 1)
    model_id, separator, variant = model_id.partition("#")
    return {"providerID": provider, "id": model_id,
            "variant": variant if separator else "default"}


def validate_export(export, prompt, model, event_text=None):
    info = export.get("info", {})
    if info.get("outcome") != "succeeded" or not info.get("id"):
        raise ValueError("session outcome or session ID invalid")
    if info.get("agent") != REVIEW_AGENT:
        raise ValueError("session agent mismatch; no-tools policy not verified")
    identity = expected_identity(model)
    if info.get("model") != identity:
        raise ValueError("session model/route/effort mismatch")
    messages = export.get("messages", [])
    if any(m.get("type") == "agent-switched" and m.get("agent") != REVIEW_AGENT for m in messages):
        raise ValueError("unexpected agent switch in session")
    if any(m.get("type") not in ("user", "assistant", "idle", "agent-switched") for m in messages):
        raise ValueError("tool or unexpected message in session")
    users = [m for m in messages if m.get("type") == "user"]
    assistants = [m for m in messages if m.get("type") == "assistant"]
    if len(users) != 1 or len(assistants) != 1:
        raise ValueError("unexpected number of user/assistant messages")
    try:
        # OpenCode exports user text as JSON-escaped quoted text with literal newlines.
        actual_prompt = json.loads(users[0]["text"], strict=False)
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("exported prompt cannot be decoded") from exc
    if actual_prompt != prompt:
        raise ValueError("exported prompt mismatch")
    assistant = assistants[0]
    if assistant.get("agent") != REVIEW_AGENT:
        raise ValueError("assistant agent mismatch; no-tools policy not verified")
    if assistant.get("model") != identity:
        raise ValueError("assistant model/route/effort mismatch")
    if assistant.get("finish") != "stop":
        raise ValueError("assistant response truncated or unfinished")
    parts = assistant.get("content", [])
    if any(p.get("type") not in ("text", "reasoning", "step-start", "step-finish") for p in parts):
        raise ValueError("tool or unexpected content in session")
    answer = "\n".join(p["text"] for p in parts if p.get("type") == "text" and p.get("text"))
    if not answer.strip() or (event_text is not None and event_text.strip() != answer.strip()):
        raise ValueError("empty answer or event/export mismatch")
    cost = info.get("cost")
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or
                             not math.isfinite(cost) or cost < 0):
        raise ValueError("invalid reported cost")
    return {"session": info["id"], "answer": answer, "used_model": identity,
            "tokens": info.get("tokens"), "cost_usd": cost}


class RejectedReview(ValueError):
    def __init__(self, message, session=None, cost=None):
        super().__init__(message)
        self.session = session
        self.cost = cost


def review_env():
    # The harness supplies provider routing through OPENCODE_CONFIG_CONTENT.
    # Preserve it and add V2 deny rules in that highest-priority configuration.
    configured = json.loads(os.environ.get("OPENCODE_CONFIG_CONTENT") or "{}")
    if not isinstance(configured, dict):
        raise ValueError("OpenCode runtime configuration must be a JSON object")
    configured = {**configured, "permissions": DENY_ALL,
                  "agents": {**configured.get("agents", {}), **TOOL_POLICY["agents"]}}
    return {**os.environ, "OPENCODE_CONFIG_CONTENT": json.dumps(configured)}


def run_review(prompt, model, workdir, timeout=240):
    config_path = Path(workdir) / ".opencode" / "opencode.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(TOOL_POLICY), encoding="utf-8")
    run = subprocess.run(["opencode", "run", "--standalone", "--model", model,
                          "--agent", REVIEW_AGENT, "--format", "json", prompt],
                         cwd=workdir, env=review_env(), stdin=subprocess.DEVNULL,
                         text=True, capture_output=True, timeout=timeout)
    try:
        events = [json.loads(line) for line in run.stdout.splitlines() if line.startswith("{")]
    except json.JSONDecodeError as exc:
        raise RejectedReview(f"invalid JSON event: {exc}") from exc
    event_sessions = {e["sessionID"] for e in events if e.get("sessionID")}
    if len(event_sessions) > 1:
        raise RejectedReview("multiple sessions in CLI events; charge unknown")
    session = next(iter(event_sessions), None)
    if not session:
        raise RejectedReview(f"no exported session; exit={run.returncode}; {run.stderr[-500:]}")
    try:
        exported = subprocess.run(["opencode", "session", "export", "--standalone", session],
                                  cwd=workdir, env=review_env(), stdin=subprocess.DEVNULL, text=True,
                                  capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise RejectedReview("session export timed out; charge unknown", session) from exc
    if exported.returncode:
        raise RejectedReview(f"session export failed: {exported.stderr[-500:]}", session)
    try:
        transcript = json.loads(exported.stdout)
    except json.JSONDecodeError as exc:
        raise RejectedReview("invalid exported session JSON", session) from exc
    if transcript.get("info", {}).get("id") != session:
        raise RejectedReview("exported session ID mismatch; charge unknown", session)
    cost = transcript.get("info", {}).get("cost")
    if run.returncode or any(e.get("type") == "error" for e in events):
        raise RejectedReview(f"API/CLI error; exit={run.returncode}; {run.stderr[-500:]}", session, cost)
    if any("tool" in e.get("type", "").lower() or "tool" in e.get("part", {}).get("type", "").lower()
           for e in events):
        raise RejectedReview("tool event occurred", session, cost)
    event_text = "\n".join(e["part"]["text"] for e in events
                           if e.get("type") == "text" and e.get("part", {}).get("text"))
    try:
        return validate_export(transcript, prompt, model, event_text)
    except ValueError as exc:
        raise RejectedReview(str(exc), session, cost) from exc


def attempts_for(root, cell_id):
    return sorted((root / "attempts").glob(f"{cell_id}-[12].json"))


def session_used(root, session):
    return any(json.loads(path.read_text()).get("session") == session
               for directory in ("attempts", "results") for path in (root / directory).glob("*.json"))


def pending_cells(manifest, root=ROOT):
    pending = []
    sessions = set()
    expected = {f'{cell["id"]}.json' for cell in manifest["cells"]}
    unexpected = {path.name for path in (root / "results").glob("*.json")} - expected
    if unexpected:
        raise ValueError(f"unexpected result files: {sorted(unexpected)}")
    for cell in manifest["cells"]:
        result = root / "results" / f'{cell["id"]}.json'
        if result.exists():
            record = json.loads(result.read_text())
            if (record.get("cell_id") != cell["id"] or record.get("model") != cell["model"] or
                    record.get("case") != cell["case"] or record.get("axis") != cell["axis"] or
                    record.get("repeat") != cell["repeat"] or
                    record.get("status") != "succeeded" or not record.get("session") or
                    not record.get("answer", "").strip() or
                    record.get("used_model") != expected_identity(cell["model"]) or
                    record.get("prompt_sha256") != manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}']):
                raise ValueError(f"result mismatch for {cell['id']}")
            if record["session"] in sessions:
                raise ValueError(f"session reused across cells: {record['session']}")
            sessions.add(record["session"])
            continue
        attempts = attempts_for(root, cell["id"])
        if any(json.loads(path.read_text()).get("status") == "succeeded" for path in attempts):
            raise ValueError(f"successful attempt without result for {cell['id']}; recover or inspect")
        if len(attempts) < 2:
            pending.append(cell)
    return pending


def openrouter_spend(root=ROOT):
    total = 0.0
    for path in (root / "attempts").glob("*.started"):
        if not path.with_suffix(".json").exists() and json.loads(path.read_text()).get("model", "").startswith("openrouter/"):
            raise ValueError(f"unknown OpenRouter cost in interrupted {path.name}; halt that route")
    for path in (root / "attempts").glob("*.json"):
        attempt = json.loads(path.read_text())
        if attempt.get("model", "").startswith("openrouter/"):
            cost = attempt.get("cost_usd")
            if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
                raise ValueError(f"unknown OpenRouter cost in {path.name}; halt that route")
            total += cost
    return total


def openrouter_reserve(model):
    route = model.split("#", 1)[0]
    price = ROUTE_PRICES_USD_PER_MILLION[route]
    limits = OPENROUTER_TOKEN_LIMITS[route]
    return (price["input"] * limits["input"] + price["output"] * limits["output"]) / 1_000_000 + 0.10


def recover_interrupted(root=ROOT):
    for path in (root / "attempts").glob("*.started"):
        started = json.loads(path.read_text())
        attempt = path.with_suffix(".json")
        if not attempt.exists():
            atomic_new(attempt, {**started, "number": int(path.stem.rsplit("-", 1)[1]),
                                 "status": "excluded", "session": None, "cost_usd": None,
                                 "error": "Process interrupted before a verified export; charge unknown"})
        else:
            record = json.loads(attempt.read_text())
            result = root / "results" / f'{started["cell_id"]}.json'
            if record.get("status") == "succeeded" and not result.exists():
                if not record.get("answer") or not record.get("session"):
                    raise ValueError(f"successful attempt missing recovery data: {attempt.name}")
                atomic_new(result, record)
        path.unlink()


@contextmanager
def run_lock(root):
    path = root / ".run.lock"
    with path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock.seek(0)
        lock.truncate()
        lock.write(f"pid={os.getpid()}\n")
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def run_cell(cell, case, manifest, root=ROOT, timeout=240):
    prompt = render_prompt(case, cell["axis"])
    prompt_hash = digest(prompt.encode())
    if prompt_hash != manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}']:
        raise ValueError("prompt changed since manifest freeze")
    for number in range(len(attempts_for(root, cell["id"])) + 1, 3):
        if cell["model"].startswith("openrouter/"):
            try:
                spent = openrouter_spend(root)
            except ValueError as exc:
                print(f"PAUSED {cell['id']}: {exc}", flush=True)
                return "paused"
            reserve = openrouter_reserve(cell["model"])
            if spent + reserve > OPENROUTER_LIMIT:
                print(f"PAUSED OpenRouter: USD {spent:.4f} reported, USD {reserve:.4f} reserved", flush=True)
                return "paused"
        start = time.perf_counter()
        marker = root / "attempts" / f'{cell["id"]}-{number}.started'
        atomic_new(marker, {"cell_id": cell["id"], "model": cell["model"],
                            "prompt_sha256": prompt_hash})
        with tempfile.TemporaryDirectory(prefix="code-review-v2-", dir=TEMP_ROOT if TEMP_ROOT.is_dir() else None) as wd:
            try:
                review = run_review(prompt, cell["model"], wd, timeout)
                if session_used(root, review["session"]):
                    raise RejectedReview("session reused across attempts", review["session"], review["cost_usd"])
                error = None
            except (RejectedReview, subprocess.TimeoutExpired) as exc:
                review = {"session": getattr(exc, "session", None), "cost_usd": getattr(exc, "cost", None)}
                error = str(exc)[-1500:]
        elapsed = round(time.perf_counter() - start, 3)
        attempt = {"cell_id": cell["id"], "model": cell["model"], "number": number,
                   "session": review.get("session"), "cost_usd": review.get("cost_usd"),
                   "elapsed_seconds": elapsed, "status": "excluded" if error else "succeeded",
                   "error": error, "prompt_sha256": prompt_hash}
        if not error:
            result = {**attempt, **review, "case": cell["case"], "axis": cell["axis"],
                      "repeat": cell["repeat"], "prompt": prompt}
            atomic_new(root / "attempts" / f'{cell["id"]}-{number}.json', result)
            atomic_new(root / "results" / f'{cell["id"]}.json', result)
            marker.unlink()
            print(f"OK {cell['id']} {elapsed:.1f}s", flush=True)
            return "succeeded"
        atomic_new(root / "attempts" / f'{cell["id"]}-{number}.json', attempt)
        marker.unlink()
        print(f"EXCLUDED {cell['id']} attempt {number}: {error}", flush=True)
    return "excluded"


def show_status(manifest, root=ROOT):
    pending = pending_cells(manifest, root)
    valid = len(list((root / "results").glob("*.json")))
    exhausted = len(manifest["cells"]) - valid - len(pending)
    attempts = list((root / "attempts").glob("*.json"))
    try:
        cost = f"USD {openrouter_spend(root):.5f} reported"
    except ValueError as exc:
        cost = str(exc)
    print(f"valid={valid}/300 pending={len(pending)} exhausted={exhausted} attempts={len(attempts)} OpenRouter={cost}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--model", help="Only run the exact frozen route/model/effort ID")
    parser.add_argument("--case")
    parser.add_argument("--axis", choices=("standards", "spec"))
    parser.add_argument("--limit", type=int, default=0, help="Maximum cells attempted this invocation")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    if args.freeze:
        if (ROOT / "manifest.json").exists():
            raise SystemExit("manifest.json already exists; no silent re-freeze")
        cases = json.loads((ROOT / "fixtures.json").read_text())
        validate_fixtures(cases)
        validate_rubric(cases, (ROOT / "grading-rubric.md").read_text())
        manifest = build_manifest(cases)
        manifest["inputs"] = inputs(ROOT)
        atomic_new(ROOT / "manifest.json", manifest)
        print(f"FROZEN {len(manifest['cells'])} cells; source hashes: {manifest['inputs']}")
        return
    cases, manifest = frozen_manifest(ROOT)
    if args.dry_run:
        print(f"{len(manifest['cells'])} cells, {len(manifest['models'])} models; seed={manifest['seed']}")
        print("first five IDs:", *[cell["id"] for cell in manifest["cells"][:5]])
    elif args.status:
        show_status(manifest)
    else:
        if args.model and args.model not in MODELS:
            raise SystemExit("Requested model is not in the frozen matrix")
        cases_by_id = {case["id"]: case for case in cases}
        with run_lock(ROOT):
            recover_interrupted(ROOT)
            count = 0
            for cell in pending_cells(manifest):
                if args.model and cell["model"] != args.model or args.case and cell["case"] != args.case or args.axis and cell["axis"] != args.axis:
                    continue
                outcome = run_cell(cell, cases_by_id[cell["case"]], manifest, timeout=args.timeout)
                if outcome != "paused":
                    count += 1
                if args.limit and count >= args.limit:
                    break
        show_status(manifest)


if __name__ == "__main__":
    main()
