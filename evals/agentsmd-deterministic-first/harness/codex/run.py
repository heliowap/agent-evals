"""Paired Codex CLI A/B study. All commands except run are offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import tempfile
import time

from cases import CASES, build, grade, snapshot
import codex_runtime as runtime
from codex_runtime import command

ROOT = Path(__file__).resolve().parent
VARIANTS = ("empty", "deterministic")
VERSION = runtime.VERSION


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def variants():
    values = {v: (ROOT / "variants" / v / "AGENTS.md").read_bytes() for v in VARIANTS}
    if values["empty"] != b"" or not values["deterministic"].startswith(b"Deterministic first\n"):
        raise ValueError("Invalid treatment files: control must be zero bytes")
    return values


def schedule(reps, seed, selected):
    rng = random.Random(seed)
    pairs = [(c, r) for r in range(1, reps + 1) for c in selected]
    rng.shuffle(pairs)
    firsts = list(VARIANTS) * (len(pairs) // 2) + ([rng.choice(VARIANTS)] if len(pairs) % 2 else [])
    rng.shuffle(firsts)
    return [{"case": c, "rep": r, "variant": v, "id": f"trial-{i * 2 + j + 1:04}"}
            for i, ((c, r), first) in enumerate(zip(pairs, firsts))
            for j, v in enumerate((first, VARIANTS[1 - VARIANTS.index(first)]))]


def manifest(reps, seed, selected, model=runtime.MODEL):
    return {"model": model, "effort": runtime.EFFORT, "runtime": VERSION, "seed": seed, "repetitions": reps,
            "variant_sha256": {v: digest(raw) for v, raw in variants().items()},
            "source_sha256": {p.name: digest(p.read_bytes()) for p in sorted(ROOT.glob("*.py"))},
            "protocol_sha256": digest((ROOT / "README.md").read_bytes()),
            "review_rubric_sha256": digest((ROOT / "REVIEW.md").read_bytes()),
            "cases": {c: CASES[c] for c in selected}, "schedule": schedule(reps, seed, selected)}


def init_git(work, env):
    for args in [["init", "-q", "--template=", "-b", "main"], ["add", "-A"], ["commit", "-qm", "fixture"]]:
        p = command(["git", *args], work, env, 15)
        if p["exit_code"]:
            raise RuntimeError(p["stderr"])


def grade_copy(case, work, final, state, target):
    shutil.copytree(work, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    try:
        return grade(case, target, final, state)
    except (OSError, ValueError, SyntaxError, subprocess.TimeoutExpired) as exc:
        return {"automatic_pass": False, "checks": {"readable_executable_artifact": False},
                "needs_blind_review": case in {"out_of_scope", "judgment"},
                "observations": {"artifact_error": str(exc)}}


def run_trial(row, out, runtime_root, args):
    trial = out / row["id"]
    trial.mkdir()
    base = runtime_root / row["id"]
    work = base / "work"
    work.mkdir(parents=True)
    raw = variants()[row["variant"]]
    state = build(row["case"], work)
    save(trial / "initial-files.json", snapshot(work))
    rec = {**row, "status": "running", "wall_s": 0.0, "model": runtime.MODEL, "effort": runtime.EFFORT,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save(trial / "result.json", rec)
    sid, turns, tool_events, error_events = None, [], [], []
    try:
        env, audit = runtime.prepare(base, work, raw, args.binary, args.auth_file)
        init_git(work, env)
        save(trial / "isolation.json", audit)
        for i, prompt in enumerate(CASES[row["case"]]["prompts"]):
            remaining = args.timeout - rec["wall_s"]
            if remaining <= 0:
                raise TimeoutError("Trial deadline exhausted")
            cmd = runtime.argv(args.binary, work, trial / f"turn-{i + 1}-final.txt", prompt, sid)
            response = command(cmd, work, env, remaining)
            rec["wall_s"] += response["wall_s"]
            (trial / f"turn-{i + 1}.jsonl").write_text(response["stdout"])
            (trial / f"turn-{i + 1}.stderr").write_text(response["stderr"])
            if response["timeout"]:
                raise TimeoutError("Agent deadline exceeded")
            if response["exit_code"] != 0:
                raise ValueError("Codex CLI exited with error: " + response["stderr"][-500:])
            parsed = runtime.parse(response["stdout"])
            if sid and parsed["session_id"] != sid:
                raise ValueError("Continuation used another session")
            sid = parsed["session_id"]
            turns.append(parsed["usage"])
            tool_events.extend(parsed["tools"])
            error_events.extend(parsed["error_events"])
        rec["usage_raw"] = turns
        rec["usage_semantics"] = "cumulative_session_last_turn"
        for key in ["input_tokens", "cached_input_tokens", "output_tokens"]:
            value = turns[-1].get(key) if turns and isinstance(turns[-1], dict) else None
            rec[key] = value if isinstance(value, int) else None
        rec["tool_calls"] = len(tool_events)
        rec["recoverable_error_events"] = error_events
        rec["session_id"] = sid
        (trial / "final.txt").write_text(parsed["final"])
        save(trial / "tool-events.json", tool_events)
        rec["grade"] = grade_copy(row["case"], work, parsed["final"], state, base / "grading")
        if (base / "codex-state" / "AGENTS.md").read_bytes() != raw:
            raise ValueError("Treatment changed during the trial")
        rec["status"] = "completed"
    except TimeoutError as exc:
        rec.update(status="timeout", error=str(exc))
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        rec.update(status="infra_error", error=str(exc))
    finally:
        (base / "codex-state" / "auth.json").unlink(missing_ok=True)
    save(trial / "result.json", rec)
    shutil.copytree(work, trial / "work", ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return rec


def report(out):
    frozen = json.loads((out / "freeze.json").read_text())
    rows = []
    for planned in frozen["schedule"]:
        path = out / planned["id"] / "result.json"
        row = json.loads(path.read_text()) if path.exists() else {**planned, "status": "not_run"}
        rows.append(row)
    lines = ["# Resultado do piloto", "", "Veredito: inconclusivo. Este piloto não decide adoção.", "",
             "Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.", "",
             "| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |", "|---|---|---:|---:|---:|---:|"]
    deltas = []
    for case in frozen["cases"]:
        for variant in VARIANTS:
            subset = [r for r in rows if r["case"] == case and r["variant"] == variant]
            done = [r for r in subset if r["status"] == "completed"]
            passed = sum(r["grade"]["automatic_pass"] for r in done)
            times = [r["wall_s"] for r in done]
            med = f"{statistics.median(times):.2f}" if times else "—"
            lines.append(f"| {case} | {variant} | {len(subset)} | {len(done)} | {passed} | {med} |")
        case_pairs = []
        for rep in range(1, frozen["repetitions"] + 1):
            pair = {r["variant"]: r for r in rows if r["case"] == case and r["rep"] == rep}
            if all(pair[v]["status"] == "completed" for v in VARIANTS):
                case_pairs.append(int(pair["deterministic"]["grade"]["automatic_pass"]) - int(pair["empty"]["grade"]["automatic_pass"]))
        if case_pairs:
            deltas.append(statistics.mean(case_pairs))
    if deltas:
        rng = random.Random(frozen["seed"])
        bootstrap = sorted(statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(5000))
        lines += ["", f"Diferença exploratória de passes automáticos, com peso igual por caso: {statistics.mean(deltas):+.1%}.",
                  f"Intervalo bootstrap por caso de 95%: [{bootstrap[125]:+.1%}, {bootstrap[4874]:+.1%}].",
                  "Apenas pares completos; não mede tarefas ausentes nem substitui revisão dos controles. Casos sintéticos não estimam a distribuição do seu trabalho."]
    statuses = {s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})}
    lines += ["", "Estados: " + json.dumps(statuses, ensure_ascii=False), "",
              "Tokens de entrada, saída e cache vêm do último usage_raw, acumulado da sessão. Resultados históricos sem usage_semantics podem somar turnos sobrepostos; não usar esses totais derivados. Cache não é somado novamente à entrada; custo monetário não é inferido. Campos ausentes permanecem desconhecidos.",
              "Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação e correção. Não é throughput do modelo."]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    return statuses


def blind(out):
    frozen = json.loads((out / "freeze.json").read_text())
    rows = [r for r in frozen["schedule"] if (out / r["id"] / "final.txt").exists()]
    random.Random(frozen["seed"] + 1).shuffle(rows)
    destination = out / "blind"
    destination.mkdir(exist_ok=False)
    key = {}
    for i, row in enumerate(rows):
        label = f"sample-{i + 1:04}"
        target = destination / label
        target.mkdir()
        key[label] = row["id"]
        task = CASES[row["case"]]
        save(target / "task.json", {"case": row["case"], "prompts": task["prompts"]})
        shutil.copy(out / row["id"] / "final.txt", target / "final.txt")
        shutil.copytree(out / row["id"] / "work", target / "work")
        save(target / "review.json", {"outcome_pass": None, "evidence": "", "reviewer": ""})
    save(out / "blind-key.json", key)
    return len(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    for name in ["plan", "run"]:
        s = commands.add_parser(name)
        s.add_argument("--out", type=Path, required=True)
        s.add_argument("--reps", type=int, default=3)
        s.add_argument("--seed", type=int, default=20261010)
        s.add_argument("--cases", default=",".join(CASES))
        if name == "run":
            s.add_argument("--auth-file", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "auth.json")
            s.add_argument("--binary", default="codex")
            s.add_argument("--timeout", type=int, default=600)
            s.add_argument("--budget-seconds", type=int, default=7200)
    for name in ["report", "blind"]:
        commands.add_parser(name).add_argument("out", type=Path)
    commands.add_parser("preflight").add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.command == "preflight":
        args.out.mkdir(parents=True, exist_ok=False)
        root = Path(tempfile.mkdtemp(prefix="detfirst-preflight-"))
        save(args.out / "preflight.json", runtime.audit_pair(root, variants()))
        print("PASS: contexts match apart from treatment; no model requests."); return
    if args.command == "report":
        print(report(args.out)); return
    if args.command == "blind":
        print(f"Exported {blind(args.out)} blinded artifacts; mapping kept outside blind/."); return
    selected = args.cases.split(",")
    if args.reps < 1 or len(set(selected)) != len(selected) or set(selected) - CASES.keys():
        p.error("Use positive repetitions and unique known case IDs")
    if args.command == "run" and (args.timeout <= 0 or args.budget_seconds < args.timeout * 2):
        p.error("Use a positive timeout and enough budget for at least one full pair")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    frozen = manifest(args.reps, args.seed, selected, runtime.MODEL)
    save(args.out / "freeze.json", frozen)
    if args.command == "plan":
        print(f"Plan: {len(frozen['schedule'])} trials. No model calls. {args.out / 'freeze.json'}"); return
    save(args.out / "limits.json", {"timeout_per_trial_s": args.timeout, "study_budget_s": args.budget_seconds,
         "stop_rule": "First infra failure; no caller retries. No automatic resume."})
    runtime_root = Path(tempfile.mkdtemp(prefix="detfirst-isolated-"))
    (args.out / "runtime-path.txt").write_text(str(runtime_root) + "\n")
    try:
        save(args.out / "preflight.json", runtime.audit_pair(runtime_root / "preflight", variants(), args.binary))
    except (ValueError, OSError, KeyError) as exc:
        save(args.out / "preflight.json", {"status": "failed", "error": str(exc)})
        print(report(args.out))
        return
    start = time.monotonic()
    for i, row in enumerate(frozen["schedule"]):
        # Admit an entire pair only if both worst-case deadlines fit the remaining budget.
        if i % 2 == 0 and time.monotonic() - start + 2 * args.timeout > args.budget_seconds:
            break
        result = run_trial(row, args.out, runtime_root, args)
        print(row["id"], row["case"], row["variant"], result["status"], flush=True)
        if result["status"] != "completed":
            break
    print(report(args.out))


if __name__ == "__main__":
    main()
