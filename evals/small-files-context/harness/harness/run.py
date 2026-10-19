"""Run trials: one Claude Code session per (stage, repetition, task, arm).

Usage:
  python3 -B harness/run.py plan  --stage {smoke,1,2}
  python3 -B harness/run.py run   --stage {smoke,1,2} --out results/NAME

Each trial runs on a fresh clone outside this package (so no parent directory
contributes instructions), is graded on a copy, and leaves in its results
directory: stream.jsonl, stderr.txt, diff.patch, grade.json, metrics.json and
trial.json. Completed trials (with trial.json) are skipped, so an interrupted
stage can be resumed; an incomplete trial directory stops the run for inspection.
"""
import argparse
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import metrics  # noqa: E402
from common import ARMS, TASK_IDS, VENV, git, grade, load_task, prepare, prompt_for  # noqa: E402

CLAUDE_VERSION = "2.1.296"
MODEL = "claude-haiku-5-5"
EFFORT = "high"
MAX_TURNS = 20
TIMEOUT_S = 15 * 60
STAGES = {"smoke": [0], "1": [1, 2, 3], "2": [4, 5]}
TURN_CAP_PROBE = {"task": "t4-request-id", "arm": "a", "max_turns": 2}


def schedule(stage):
    """Interleave arms within each task and repetition; alternate which arm goes first."""
    trials = []
    if stage == "smoke":
        for arm in ARMS:
            trials.append({"stage": "smoke", "rep": 0, "task": TASK_IDS[0], "arm": arm, "max_turns": MAX_TURNS})
        trials.append({"stage": "smoke", "rep": 0, "probe": "turn-cap", **TURN_CAP_PROBE})
        return trials
    for rep in STAGES[stage]:
        for i, task in enumerate(TASK_IDS):
            arms = ARMS if (rep + i) % 2 == 0 else ARMS[::-1]
            for arm in arms:
                trials.append({"stage": stage, "rep": rep, "task": task, "arm": arm, "max_turns": MAX_TURNS})
    return trials


def trial_id(t):
    stage = "smoke" if t["stage"] == "smoke" else f"s{t['stage']}"
    return f"{stage}-r{t['rep']}-{t['task']}-{t['arm']}" + ("-turncap" if t.get("probe") else "")


def claude_cmd(prompt, max_turns):
    return ["claude", "-p", prompt, "--safe-mode", "--tools", "Bash,Read,Edit",
            "--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands",
            "--model", MODEL, "--effort", EFFORT, "--max-turns", str(max_turns),
            "--no-session-persistence", "--dangerously-skip-permissions",
            "--output-format", "stream-json", "--verbose"]


def agent_env():
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["PATH"] = f"{VENV / 'bin'}:{env.get('PATH', '/usr/bin:/bin')}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_trial(t, out_dir):
    tdir = out_dir / "trials" / trial_id(t)
    tdir.mkdir(parents=True)  # fails if it exists: no overwrite
    work = pathlib.Path(tempfile.mkdtemp(prefix="sfb-trial-")).resolve()
    repo = prepare(t["task"], t["arm"], work / "repo")
    prompt = prompt_for(load_task(t["task"]), t["arm"])
    record = {**t, "id": trial_id(t), "prompt": prompt, "repo": str(repo),
              "claude_version": CLAUDE_VERSION, "model": MODEL, "effort": EFFORT,
              "timeout_s": TIMEOUT_S, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    start = time.monotonic()
    with open(tdir / "stream.jsonl", "wb") as out, open(tdir / "stderr.txt", "wb") as err:
        proc = subprocess.Popen(claude_cmd(prompt, t["max_turns"]), cwd=repo, stdout=out, stderr=err,
                                stdin=subprocess.DEVNULL, env=agent_env(), start_new_session=True)
        try:
            record["exit_code"] = proc.wait(timeout=TIMEOUT_S)
            record["timed_out"] = False
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            record["exit_code"] = proc.wait()
            record["timed_out"] = True
    record["wall_s"] = round(time.monotonic() - start, 1)

    git(repo, "add", "-A")
    (tdir / "diff.patch").write_text(git(repo, "diff", "--cached", "HEAD", capture=True))
    g = grade(t["task"], repo, work)
    (tdir / "grade.json").write_text(json.dumps(g, indent=2) + "\n")
    m = metrics.parse(tdir / "stream.jsonl", repo_dir=work)
    (tdir / "metrics.json").write_text(json.dumps(m, indent=2) + "\n")
    record["pass"] = g["pass"]
    (tdir / "trial.json").write_text(json.dumps(record, indent=2) + "\n")
    shutil.rmtree(work)
    return record, m


def check_cli():
    v = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout
    if not v.startswith(CLAUDE_VERSION):
        sys.exit(f"claude {v.strip()!r}; this eval is pinned to {CLAUDE_VERSION}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["plan", "run"])
    ap.add_argument("--stage", required=True, choices=list(STAGES))
    ap.add_argument("--out")
    args = ap.parse_args()
    trials = schedule(args.stage)
    if args.command == "plan":
        for t in trials:
            print(trial_id(t))
        print(f"{len(trials)} trials")
        return
    check_cli()
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(trials, 1):
        tdir = out_dir / "trials" / trial_id(t)
        if (tdir / "trial.json").exists():
            print(f"[{i}/{len(trials)}] {trial_id(t)} already complete, skipped", flush=True)
            continue
        if tdir.exists():
            sys.exit(f"{tdir} exists without trial.json (interrupted trial); inspect and move it aside")
        record, m = run_trial(t, out_dir)
        print(f"[{i}/{len(trials)}] {record['id']}: pass={record['pass']} "
              f"peak={m['peak_context']} turns={m['num_turns']} wall={record['wall_s']}s "
              f"cost=${m['cost_usd']} end={m['result_subtype']} valid={m['validity']['ok']}"
              + (" TIMEOUT" if record["timed_out"] else ""), flush=True)


if __name__ == "__main__":
    main()
