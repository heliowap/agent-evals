"""Run the AGENTS.md "Deterministic first" A/B eval. See CARD.md."""

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from tasks import TASKS

HERE = Path(__file__).parent
MODEL = "cli_proxy/cpa-claude-opus-5-5"
VARIANTS = ("A", "B")
DECISION = 'Keep or remove the "Deterministic first" section from ~/.config/opencode/AGENTS.md.'


def tok_total(t):
    return t["input"] + t["output"] + t.get("reasoning", 0) + t["cache"]["read"] + t["cache"]["write"]


def add_tok(a, b):
    return {
        "input": a["input"] + b["input"],
        "output": a["output"] + b["output"],
        "reasoning": a.get("reasoning", 0) + b.get("reasoning", 0),
        "cache": {k: a["cache"][k] + b["cache"][k] for k in ("read", "write")},
    }


ZERO = {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}}


def run_one(root, variants, task_id, rep, v, timeout, model):
    prompt, build, grade = TASKS[task_id]
    rdir = root / "runs" / f"{task_id}-r{rep}-{v}"
    work = rdir / "work"
    work.mkdir(parents=True)
    state = build(work)
    rec = {"task": task_id, "rep": rep, "variant": v, "model": model, "agents_md_sha256": variants[v]["agents_md_sha256"]}
    env = {**os.environ, "XDG_CONFIG_HOME": variants[v]["xdg_config_home"], "PWD": str(work)}
    cmd = ["opencode", "run", "--standalone", "--auto", "--format", "json", "-m", model,
           "--title", f"eval agentsmd {task_id} r{rep} {v}", prompt]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout)
        stdout, stderr, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr, rc = "TIMEOUT", None
    rec["wall_s"] = round(time.monotonic() - t0, 2)
    rec["exit_code"] = rc
    (rdir / "events.jsonl").write_text(stdout)
    (rdir / "stderr.txt").write_text(stderr)

    sid = None
    for line in stdout.splitlines():
        try:
            sid = json.loads(line).get("sessionID") or sid
        except json.JSONDecodeError:
            pass
        if sid:
            break
    rec["session_id"] = sid
    if rc is None or not sid:
        rec["infra_failure"] = "timeout" if rc is None else "no_session"
        return rec
    ex = subprocess.run(["opencode", "session", "export", sid], capture_output=True, text=True)
    (rdir / "export.json").write_text(ex.stdout)
    try:
        d = json.loads(ex.stdout)
    except json.JSONDecodeError:
        rec["infra_failure"] = "export_failed"
        return rec

    msgs = d["messages"]
    asst = [m for m in msgs if m.get("type") == "assistant"]
    tok = ZERO
    for m in asst:
        tok = add_tok(tok, m.get("tokens") or ZERO)
    texts = [c["text"] for m in asst for c in m.get("content", []) if c.get("type") == "text"]
    tools = [c.get("name") or c.get("tool") or c.get("type") for m in asst for c in m.get("content", [])
             if c.get("type") not in ("text", "reasoning")]
    outcome = next((m.get("outcome") for m in reversed(msgs) if m.get("type") == "idle"), None)
    info = d["info"]
    rec["actual_model"] = info.get("model")
    rec.update({
        "tokens": tok, "tokens_total": tok_total(tok),
        "info_tokens_total": tok_total(info["tokens"]), "cost": info.get("cost"),
        "time_s": round((info["time"]["idle"] - info["time"]["created"]) / 1000, 2) if info["time"].get("idle") else None,
        "steps": len(asst), "tool_calls": len(tools), "tools": sorted(set(map(str, tools))),
        "outcome": outcome, "errors": [m.get("error") for m in asst if m.get("finish") == "error"],
    })
    rec["location"] = (info.get("location") or {}).get("directory")
    if not rec["location"] or os.path.realpath(rec["location"]) != os.path.realpath(work):
        rec["infra_failure"] = f"wrong_directory={rec['location']}"
        return rec
    provider, selected = model.split("/", 1)
    model_id, _, variant = selected.partition("#")
    if rec["actual_model"] != {"providerID": provider, "id": model_id, "variant": variant or "default"}:
        rec["infra_failure"] = f"wrong_model={rec['actual_model']}"
        return rec
    if outcome != "succeeded" or rec["errors"]:
        rec["infra_failure"] = f"outcome={outcome}"
        return rec
    final = texts[-1] if texts else ""
    rec["passed"], rec["grade_detail"] = grade(work, final, state)
    return rec


def median(xs):
    return statistics.median(xs) if xs else None


def report(records, out, card_note):
    ok = [r for r in records if not r.get("infra_failure")]
    lines = [f"Decision: {DECISION}", "", card_note, ""]
    lines += ["| Task | V | n | pass | tokens median | tokens min-max | time median (s) | steps median | tool calls median | notes |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    per = {}
    for tid in TASKS:
        for v in VARIANTS:
            rs = [r for r in ok if r["task"] == tid and r["variant"] == v]
            if not rs:
                continue
            toks = [r["tokens_total"] for r in rs]
            passed = sum(r["passed"] for r in rs)
            per[(tid, v)] = {"pass": passed / len(rs), "tok": median(toks), "time": median([r["time_s"] for r in rs])}
            notes = "; ".join(r["grade_detail"].split(" leaked")[0] for r in rs) if tid == "T3-rule" else ""
            lines.append(f"| {tid} | {v} | {len(rs)} | {passed}/{len(rs)} | {median(toks):,.0f} | {min(toks):,}-{max(toks):,} | "
                         f"{median([r['time_s'] for r in rs]):.1f} | {median([r['steps'] for r in rs])} | "
                         f"{median([r['tool_calls'] for r in rs])} | {notes} |")
    lines += ["", "## Winner rule applied to this data", ""]
    tasks_both = [t for t in TASKS if (t, "A") in per and (t, "B") in per]
    for t in tasks_both:
        a, b = per[(t, "A")], per[(t, "B")]
        lines.append(f"- {t}: B/A tokens {b['tok'] / a['tok']:.2f}, B/A time {b['time'] / a['time']:.2f}, "
                     f"pass A {a['pass']:.0%} B {b['pass']:.0%}")
    pa = [r["passed"] for r in ok if r["variant"] == "A"]
    pb = [r["passed"] for r in ok if r["variant"] == "B"]
    if pa and pb and tasks_both:
        ratio = median([per[(t, "B")]["tok"] / per[(t, "A")]["tok"] for t in tasks_both])
        win = sum(pb) / len(pb) >= sum(pa) / len(pa) and ratio <= 0.9
        lines += ["", f"Pass rate A {sum(pa)}/{len(pa)}, B {sum(pb)}/{len(pb)}; median per-task B/A token ratio {ratio:.2f}.",
                  f"Rule outcome: {'B wins (remove the section)' if win else 'keep A'}."]
    infra = [r for r in records if r.get("infra_failure")]
    lines += ["", f"Infra failures: {len(infra)}" + "".join(f"\n- {r['task']} r{r['rep']} {r['variant']}: {r['infra_failure']}" for r in infra)]
    drift = [r for r in ok if r["info_tokens_total"] != r["tokens_total"]]
    lines.append(f"Runs where session total != sum of agent messages: {len(drift)}")
    (out / "report.md").write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--budget-hours", type=float, default=2.0)
    ap.add_argument("--budget-tokens", type=int, default=3_000_000)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--label", default="pilot")
    args = ap.parse_args()
    tasks = args.tasks.split(",")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = HERE / "results" / f"{ts}-{args.label}"
    out.mkdir(parents=True)
    root = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode" / "agentsmd-eval" / ts
    subprocess.run([sys.executable, str(HERE / "make_variants.py"), str(root)], check=True, capture_output=True)
    variants = json.loads((root / "variants.json").read_text())
    (out / "variants.json").write_text(json.dumps(variants, indent=2))
    (out / "args.json").write_text(json.dumps({**vars(args), "workdirs": str(root)}, indent=2))

    records, used_tok, infra_streak, max_pair = [], 0, 0, (0.0, 0)
    start = time.monotonic()
    stop = None
    with ThreadPoolExecutor(2) as pool, open(out / "results.jsonl", "w") as f:
        for rep in range(1, args.reps + 1):
            for tid in tasks:
                elapsed = time.monotonic() - start
                if elapsed + max_pair[0] > args.budget_hours * 3600 or used_tok + max_pair[1] > args.budget_tokens:
                    stop = f"budget: {elapsed / 60:.0f} min, {used_tok:,} tokens used before {tid} r{rep}"
                    break
                order = VARIANTS if rep % 2 else VARIANTS[::-1]
                p0 = time.monotonic()
                pair = list(pool.map(lambda v: run_one(root, variants, tid, rep, v, args.timeout, args.model), order))
                pair_tok = sum(r.get("tokens_total", 0) for r in pair)
                used_tok += pair_tok
                max_pair = (max(max_pair[0], time.monotonic() - p0), max(max_pair[1], pair_tok))
                for r in pair:
                    records.append(r)
                    f.write(json.dumps(r) + "\n")
                    f.flush()
                    infra_streak = infra_streak + 1 if r.get("infra_failure") else 0
                    print(f"[{(time.monotonic() - start) / 60:5.1f}m] {tid} r{rep} {r['variant']}: "
                          f"{'INFRA ' + r['infra_failure'] if r.get('infra_failure') else ('PASS' if r['passed'] else 'FAIL')} "
                          f"tok={r.get('tokens_total')} t={r.get('time_s')}s", flush=True)
                if infra_streak >= 3:
                    stop = "3 consecutive infra failures"
                    break
            if stop:
                break
    note = (f"Run {ts} ({args.label}), model {args.model}: {len(records)} runs, {used_tok:,} tokens, "
            f"{(time.monotonic() - start) / 60:.0f} min. " + (f"Stopped early: {stop}." if stop else "Completed."))
    report(records, out, note)
    print(note)
    print(f"Report: {out / 'report.md'}")


if __name__ == "__main__":
    main()
