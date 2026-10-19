import argparse
from collections import Counter
from dataclasses import asdict
from itertools import combinations
import json
from pathlib import Path
import random
import shutil
import statistics
import tempfile
import time

from domain import Budget, CANDIDATES
import controller
import grader
import isolation
import runtime
import tasks


PACKAGE = Path(__file__).resolve().parent
PHASES = ("budget", "smoke", "screening", "confirmation")
SESSION_MARGIN_SECONDS = 1200
PREFLIGHT_MARGIN_SECONDS = 480
ARTIFACTS = ("session.json", "observations.jsonl", "terminal.jsonl", "discovery.json", "effective-config.json",
             "run.stdout.jsonl", "run.stderr", "request.txt")


def schedule(selected_tasks, candidates, reps, seed):
    rng = random.Random(seed)
    blocks = [(task.id, rep) for rep in range(1, reps + 1) for task in selected_tasks]
    rng.shuffle(blocks)
    order = list(candidates)
    rng.shuffle(order)
    rows = []
    for index, (task, rep) in enumerate(blocks):
        offset = index % len(order)
        for candidate in order[offset:] + order[:offset]:
            rows.append({"id": f"trial-{len(rows) + 1:04d}", "block": index, "task": task,
                         "rep": rep, "candidate": candidate.id})
    return rows


def freeze(out, args, selected_tasks, candidates, budget):
    source = out / ".frozen-source"
    source.mkdir()
    hashes = {}
    files = sorted([*PACKAGE.glob("*.py"), *PACKAGE.glob("*.js"), PACKAGE / "Dockerfile", PACKAGE / ".dockerignore", PACKAGE / "README.md"])
    for path in files:
        shutil.copyfile(path, source / path.name)
        hashes[path.name] = runtime.source_hash(path)
    shutil.copyfile(args.cache, out / "models.json")
    rows = schedule(selected_tasks, candidates, args.reps, args.seed)
    blocks = sorted({row["block"] for row in rows})
    chosen_blocks = blocks[args.block_start: args.block_start + args.block_count if args.block_count is not None else None]
    rows = [row for row in rows if row["block"] in chosen_blocks]
    if not rows:
        raise ValueError("The selected block range is empty")
    value = {"schema": 1, "phase": args.phase, "source_hashes": hashes,
             "tool_surface": "isolated_terminal_only", "candidates": [runtime.public_candidate(c) for c in candidates],
             "tasks": [asdict(task) for task in selected_tasks], "schedule": rows, "reps": args.reps,
             "seed": args.seed, "budget": asdict(budget), "global_seconds": args.global_seconds,
             "opencode": runtime.VERSION, "catalog_sha256": runtime.source_hash(args.cache),
             "image_spec": {"tag": args.image, "dockerfile_sha256": hashes["Dockerfile"], "image_id": None},
             "native_steps": None, "call_limit_overshoot_allowed": 1, "comparison_tie_ratio": [.95, 1.05],
             "observation": "passive_native_provider", "network": "none", "filesystem": "workspace_only"}
    runtime.save(out / "freeze.json", value)
    return value


def check_freeze(out):
    frozen = json.loads((out / "freeze.json").read_text())
    for name, digest in frozen["source_hashes"].items():
        if runtime.source_hash(out / ".frozen-source" / name) != digest or runtime.source_hash(PACKAGE / name) != digest:
            raise ValueError("Frozen source differs from the running harness")
    if runtime.source_hash(out / "models.json") != frozen["catalog_sha256"]:
        raise ValueError("Frozen native catalog changed")
    return frozen


def validate(selected_tasks, out):
    results = [grader.validate_task(task) for task in selected_tasks if task.phase != "budget"]
    result = {"status": "passed" if all(row["valid"] for row in results) else "failed", "tasks": results,
              "model_calls": 0, "execution": "trusted_baseline_and_reference_only"}
    runtime.save(out / "validation.json", result)
    return result


def docker_validate(selected_tasks, image, docker, out):
    rows = []
    for task in selected_tasks:
        if task.phase == "budget":
            continue
        checks = {}
        for reference in (False, True):
            label = "reference" if reference else "baseline"
            with tempfile.TemporaryDirectory(prefix="trusted-project-") as folder:
                work = Path(folder)
                grader.materialize(task, work, reference)
                checks[label] = grader.grade(task, work, out / "grader-proofs" / task.id / label, image, docker)
        baseline, reference = checks["baseline"], checks["reference"]
        good = (baseline["criteria"]["compilation"]["passed"] and baseline["criteria"]["regression"]["passed"]
                and not baseline["patch_correct"] and reference["patch_correct"])
        rows.append({"task": task.id, "passed": good, **checks})
    if not all(row["passed"] for row in rows):
        raise ValueError("Docker baseline/reference grading failed")
    return rows


def preflight(out, args, selected_tasks, candidates):
    checked = {"status": "blocked", "model_calls": 0, "namespace_validated": False}
    try:
        checked["validation"] = validate(selected_tasks, out)
        if checked["validation"]["status"] != "passed":
            raise ValueError("Trusted baseline/reference validation failed")
        checked["engine_endpoint"] = isolation.engine_endpoint(args.docker)
        checked["daemon"] = json.loads(isolation.docker_command([args.docker, "info", "--format", "{{json .}}"], timeout=20))
        checked["image"] = isolation.image_info(args.docker, args.image, args.build_image)
        image = checked["image"]["id"]
        checked["isolation"] = isolation.prove_isolation(image, args.docker)
        checked["namespace_validated"] = True
        checked["grader"] = docker_validate(selected_tasks, image, args.docker, out)
        planned = len(json.loads((out / "freeze.json").read_text())["schedule"])
        declared_window = oauth_window(args.global_seconds, len(candidates), Budget(args.seconds or (20 if args.phase == "budget" else 1200), args.calls or (2 if args.phase == "budget" else 60)), planned)
        checked["oauth_window_seconds"] = declared_window
        runtime.validate_oauth_window(candidates, args.database, declared_window)
        checked["providers"] = []
        for candidate in candidates:
            with tempfile.TemporaryDirectory(prefix="private-runtime-") as folder:
                root = Path(folder)
                work = root / "project"
                grader.materialize(tasks.SMOKE, work)
                with isolation.CodeContainer(work, image, args.docker) as container:
                    env, expected = runtime.prepare(root, work, candidate, args.binary, args.database,
                                                    out / "models.json", container.id, args.docker, checked["engine_endpoint"])
                    checked["providers"].append(runtime.audit(root, work, args.binary, env, expected, candidate))
        frozen = json.loads((out / "freeze.json").read_text())
        frozen["image_spec"].update(image_id=image, versions=checked["isolation"]["versions"], engine_endpoint=checked["engine_endpoint"])
        runtime.save(out / "freeze.json", frozen)
        checked["status"] = "passed"
    except Exception as error:
        checked["error"] = str(error)
    runtime.save(out / "preflight.json", checked)
    return checked


def oauth_window(global_seconds, candidate_count, budget, planned=None):
    per_session = budget.seconds + budget.grace + SESSION_MARGIN_SECONDS
    full_block = candidate_count * per_session
    scheduled = (planned or candidate_count) * per_session
    return min(global_seconds + full_block, scheduled) + candidate_count * PREFLIGHT_MARGIN_SECONDS


def require_gate(path, phase, frozen):
    if path is None:
        raise ValueError(f"An explicit completed {phase} gate is required")
    gate = json.loads((path / "freeze.json").read_text())
    summary = report(path)
    if gate["phase"] != phase or not summary["gate_passed"]:
        raise ValueError(f"The {phase} gate did not pass")
    expected = {row["id"]: row for row in frozen["candidates"]}
    observed = {row["id"]: row for row in gate["candidates"]}
    if any(observed.get(key) != value for key, value in expected.items()):
        raise ValueError("Gate configuration differs from the selected candidate cohort")
    if gate["image_spec"]["image_id"] != frozen["image_spec"]["image_id"]:
        raise ValueError("Gate container image differs from the frozen image")
    if gate["source_hashes"] != frozen["source_hashes"]:
        raise ValueError("Gate harness sources differ from the frozen sources")
    if gate["catalog_sha256"] != frozen["catalog_sha256"]:
        raise ValueError("Gate native model catalog differs from the frozen catalog")
    return {"phase": phase, "path": str(path.resolve()), "freeze_sha256": runtime.source_hash(path / "freeze.json")}


def copy_artifacts(root, out, secrets):
    for name in ARTIFACTS:
        path = root / name
        if path.exists():
            content = path.read_text(errors="replace")
            for secret in secrets:
                content = content.replace(secret, "[REDACTED]")
            (out / name).write_text(content)


def operational_status(control, parsed, observation, grade, codes):
    if not grade["scope"]["scope_correct"]:
        return "scope_violation"
    if control["reason"]:
        return "budget_exceeded"
    errors = [error for error in codes if error["code"] != "stream_cancelled"]
    if errors or parsed["error_events"] or control["exit_code"] or observation["non_200_requests"] or observation["incomplete_requests"]:
        return "integration_error"
    if parsed["session_completed"]:
        return "completed"
    return "task_failed"


def run_trial(row, out, args, frozen, candidate, task, budget):
    destination = out / "trials" / row["id"]
    destination.mkdir(parents=True)
    result = {**row, "status": "started", "accepted": False, "session_completed": False, "patch_correct": False,
              "requested_identity": candidate.identity, "request_count": 0, "tool_surface": "isolated_terminal_only"}
    runtime.save(destination / "result.json", result)
    started = time.monotonic()
    secrets = []
    with tempfile.TemporaryDirectory(prefix="private-runtime-") as folder:
        root = Path(folder)
        work = root / "project"
        grader.materialize(task, work)
        (root / "request.txt").write_text(task.request)
        try:
            secrets = runtime.credential_secrets(runtime.credential(candidate, args.database)["value"])
            image = frozen["image_spec"]["image_id"]
            with isolation.CodeContainer(work, image, args.docker) as container:
                env, expected = runtime.prepare(root, work, candidate, args.binary, args.database,
                                                out / "models.json", container.id, args.docker, frozen["image_spec"]["engine_endpoint"])
                result["discovery"] = runtime.audit(root, work, args.binary, env, expected, candidate)
                result["preparation_s"] = time.monotonic() - started
                control, export = controller.invoke(candidate, work, root, args.binary, env, container, budget)
                result["control"] = control
                result["task_wall_s"] = control["execution_s"]
                parsed = runtime.parse_session(export, candidate, work)
                result.update(parsed)
                records = runtime.read_requests(root / "observations.jsonl")
                result["requests"] = records
                observation = runtime.verify_requests(candidate, records, parsed["session_id"])
                result.update(observation)
                result["codes"] = [error for record in records for error in record.get("errors", [])]
                grade_started = time.monotonic()
                result["grade"] = grader.grade(task, work, destination / "grading", image, args.docker)
                result["grading_s"] = time.monotonic() - grade_started
                result["patch_correct"] = result["grade"]["patch_correct"]
                operational_errors = [error for error in result["codes"] if error["code"] != "stream_cancelled"]
                result["status"] = operational_status(control, parsed, observation, result["grade"], result["codes"])
                result["accepted"] = result["status"] == "completed" and result["patch_correct"]
                if args.phase == "budget":
                    result["proof_passed"] = (result["status"] == "budget_exceeded" and bool(control["interrupt"] and control["interrupt"].get("interrupted"))
                                              and control["container_stopped"] and not control["hard_kill"]
                                              and result["request_count"] <= budget.calls + 1 and not operational_errors
                                              and result["grade"]["scope"]["scope_correct"])
        except Exception as error:
            result.update(status="infra_error", error=str(error))
            result["grade"] = {"scope": grader.collect_patch(task, work), "patch_correct": False, "not_executed": True}
        finally:
            if "requests" not in result:
                try:
                    result["requests"] = runtime.read_requests(root / "observations.jsonl")
                    result["request_count"] = len(result["requests"])
                except Exception:
                    result["observation_parse_failed"] = True
            copy_artifacts(root, destination, secrets)
            result["trial_wall_s"] = time.monotonic() - started
            content = json.dumps(result, ensure_ascii=False, indent=2)
            for secret in secrets:
                content = content.replace(secret, "[REDACTED]")
            (destination / "result.json").write_text(content + "\n")
    return result


def report(out):
    frozen = json.loads((out / "freeze.json").read_text())
    rows = []
    for row in frozen["schedule"]:
        path = out / "trials" / row["id"] / "result.json"
        rows.append(json.loads(path.read_text()) if path.exists() else {**row, "status": "not_run", "accepted": False})
    ids = [c["id"] for c in frozen["candidates"]]
    summary = {"phase": frozen["phase"], "planned": len(rows), "started": sum(r["status"] != "not_run" for r in rows),
               "accepted": sum(bool(r["accepted"]) for r in rows), "model_calls": sum(r.get("request_count", 0) for r in rows),
               "tool_surface": frozen["tool_surface"], "by_candidate": {}, "by_task": {}, "pairwise": [],
               "gate_passed": False, "automatic_winner": None}
    lines = ["# Resultado do implementador", "", f"Fase `{frozen['phase']}`. {summary['started']} de {len(rows)} tentativas iniciadas. {summary['model_calls']} chamadas de modelo.",
             "", "As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.", "",
             "| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for candidate in ids:
        subset = [r for r in rows if r["candidate"] == candidate]
        times = [r["task_wall_s"] for r in subset if r.get("session_completed") and "task_wall_s" in r]
        item = {"planned": len(subset), "started": sum(r["status"] != "not_run" for r in subset),
                "accepted": sum(r["accepted"] for r in subset), "patch_correct": sum(bool(r.get("patch_correct")) for r in subset),
                "completed": sum(bool(r.get("session_completed")) for r in subset), "statuses": dict(Counter(r["status"] for r in subset)),
                "median_s": statistics.median(times) if times else None,
                "min_s": min(times) if times else None, "max_s": max(times) if times else None,
                "fast_requested": sum(bool(r.get("fast_requested")) for r in subset),
                "fast_served": dict(Counter(r.get("fast_served", "not_observed") for r in subset)),
                "calls": sum(r.get("request_count", 0) for r in subset)}
        summary["by_candidate"][candidate] = item
        median = f"{item['median_s']:.2f}" if times else "n/d"
        lines.append(f"| {candidate} | {len(subset)} | {item['started']} | {item['accepted']} | {item['patch_correct']} | {item['completed']} | {median} | {item['statuses']} |")
    for task in frozen["tasks"]:
        subset = [r for r in rows if r["task"] == task["id"]]
        summary["by_task"][task["id"]] = {candidate: sum(r["accepted"] for r in subset if r["candidate"] == candidate) for candidate in ids}
    for left, right in combinations(ids, 2):
        matched = {(r["task"], r["rep"], r["candidate"]): r for r in rows if r["accepted"]}
        ratios = []
        for task, rep in sorted({(r["task"], r["rep"]) for r in rows}):
            a, b = matched.get((task, rep, left)), matched.get((task, rep, right))
            if a and b and a.get("task_wall_s") and b.get("task_wall_s"):
                ratios.append({"task": task, "rep": rep, "a_over_b": a["task_wall_s"] / b["task_wall_s"]})
        med = statistics.median(r["a_over_b"] for r in ratios) if ratios else None
        summary["pairwise"].append({"a": left, "b": right, "jointly_accepted": len(ratios), "median_a_over_b": med,
                                    "close_time_tie": med is not None and .95 <= med <= 1.05, "observations": ratios})
    if frozen["phase"] == "budget":
        summary["gate_passed"] = all(r.get("proof_passed") for r in rows)
    elif frozen["phase"] == "smoke":
        summary["gate_passed"] = all(r.get("accepted") for r in rows)
    lines += ["", "A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.",
              "", "Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.",
              "", "Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.", ""]
    runtime.save(out / "summary.json", summary)
    (out / "report.md").write_text("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description="OpenCode implementation eval with Docker-isolated terminal")
    parser.add_argument("command", choices=("plan", "validate", "preflight", "run", "report"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", choices=PHASES, default="screening")
    parser.add_argument("--candidates")
    parser.add_argument("--reps", type=int)
    parser.add_argument("--seconds", type=int)
    parser.add_argument("--calls", type=int)
    parser.add_argument("--global-seconds", type=int, default=21600)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--block-start", type=int, default=0)
    parser.add_argument("--block-count", type=int)
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--image", default=isolation.IMAGE_TAG)
    parser.add_argument("--build-image", action="store_true")
    parser.add_argument("--database", type=Path, default=Path.home() / ".local/share/opencode/opencode.db")
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/opencode/models.json")
    parser.add_argument("--budget-proof", type=Path)
    parser.add_argument("--smoke-proof", type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.command == "report":
        print(json.dumps(report(out), ensure_ascii=False, indent=2))
        return
    available = {c.id: c for c in CANDIDATES}
    if args.phase == "confirmation" and not args.candidates:
        parser.error("Confirmation requires explicit finalists")
    names = args.candidates.split(",") if args.candidates else list(available)
    if not names or len(set(names)) != len(names) or any(name not in available for name in names):
        parser.error("Invalid candidate list")
    candidates = tuple(available[name] for name in names)
    args.reps = args.reps if args.reps is not None else (3 if args.phase == "screening" else 5 if args.phase == "confirmation" else 1)
    if args.phase in ("smoke", "budget") and args.reps != 1:
        parser.error("Gate phases require exactly one session per configuration")
    budget = Budget(args.seconds if args.seconds is not None else (20 if args.phase == "budget" else 1200),
                    args.calls if args.calls is not None else (2 if args.phase == "budget" else 60))
    if min(args.reps, budget.seconds, budget.calls, args.global_seconds) < 1 or args.block_start < 0 or (args.block_count is not None and args.block_count < 1):
        parser.error("Invalid repetitions or budget")
    if out.exists():
        parser.error("Output must be new; prior evidence is never overwritten")
    out.mkdir(parents=True)
    selected_tasks = tasks.inventory(args.phase)
    frozen = freeze(out, args, selected_tasks, candidates, budget)
    if args.command == "plan":
        report(out)
        print(f"Frozen {len(frozen['schedule'])} sessions; zero model calls: {out}")
        return
    if args.command == "validate":
        checked = validate(selected_tasks, out)
        print(f"Validation {checked['status']}; zero model calls: {out / 'validation.json'}")
        raise SystemExit(0 if checked["status"] == "passed" else 1)
    args.binary = shutil.which(args.binary) or args.binary
    args.docker = shutil.which(args.docker) or args.docker
    checked = preflight(out, args, selected_tasks, candidates)
    if checked["status"] != "passed":
        report(out)
        parser.exit(1, f"Preflight blocked: {checked['error']}. Zero model calls. Evidence: {out / 'preflight.json'}\n")
    if args.command == "preflight":
        print(f"Preflight passed; zero model calls: {out / 'preflight.json'}")
        return
    frozen = check_freeze(out)
    try:
        gates = []
        if args.phase != "budget":
            gates.append(require_gate(args.budget_proof, "budget", frozen))
        if args.phase in ("screening", "confirmation"):
            gates.append(require_gate(args.smoke_proof, "smoke", frozen))
        runtime.save(out / "gates.json", gates)
    except ValueError as error:
        report(out)
        parser.exit(1, str(error) + ". Zero model calls.\n")
    candidate_map = {c.id: c for c in candidates}
    task_map = {task.id: task for task in selected_tasks}
    started = time.monotonic()
    try:
        for block in sorted({row["block"] for row in frozen["schedule"]}):
            if time.monotonic() - started >= args.global_seconds:
                break
            runtime.validate_oauth_window(candidates, args.database, len(candidates) * (budget.seconds + budget.grace + SESSION_MARGIN_SECONDS))
            for row in [r for r in frozen["schedule"] if r["block"] == block]:
                check_freeze(out)
                result = run_trial(row, out, args, frozen, candidate_map[row["candidate"]], task_map[row["task"]], budget)
                print(f"{row['id']} {row['candidate']} {row['task']} {result['status']} accepted={result['accepted']}", flush=True)
                report(out)
                if result["status"] in ("infra_error", "scope_violation"):
                    print("Stopped after infrastructure or scope violation; remaining trials remain visible", flush=True)
                    return
    finally:
        report(out)


if __name__ == "__main__":
    main()
