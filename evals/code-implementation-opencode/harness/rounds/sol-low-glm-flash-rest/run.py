import argparse
from dataclasses import asdict
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace


ROUND = Path(__file__).resolve().parent
MONEY_ROUND = ROUND.parent / "money-sol-low-glm-flash"
WRAPPER_FILES = ("run.py", "README.md", "test_run.py")
TERMINAL_STATUSES = {"completed", "budget_exceeded", "integration_error", "task_failed"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read evidence: {path}") from error


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def normalized(value):
    return json.loads(json.dumps(value))


def load_context(round_dir=None):
    round_dir = (round_dir or ROUND).resolve()
    provenance = read_json(round_dir / "provenance.json")
    hashes = {name: digest(round_dir / name) for name in WRAPPER_FILES}
    if provenance.get("schema") != 1 or hashes != provenance.get("wrapper_hashes"):
        raise ValueError("Continuation source differs from provenance")
    money_round = Path(provenance["money_round_path"])
    if not money_round.is_absolute() or digest(money_round / "provenance.json") != provenance["money_provenance_sha256"]:
        raise ValueError("Monetary harness provenance changed")
    money_provenance = read_json(money_round / "provenance.json")
    if digest(money_round / "run.py") != money_provenance["wrapper_hashes"]["run.py"]:
        raise ValueError("Monetary orchestrator changed before import")
    spec = importlib.util.spec_from_file_location("implementer_money_rest_source", money_round / "run.py")
    money = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(money)
    context = money.load_context(money_round)
    with money.harness_modules(money_round / "harness") as (bench, domain):
        python = importlib.import_module("tasks_python")
        typescript = importlib.import_module("tasks_typescript")
        selected = tuple(task for task in (*python.TASKS, *typescript.TASKS)
                         if task.phase == "screening" and task.id != "py-money-contract")
        tasks = normalized([asdict(task) for task in selected])
        original = [task for task in context.baseline["tasks"] if task["id"] != "py-money-contract"]
        if len(tasks) != 11 or tasks != original:
            raise ValueError("Continuation TaskSpecs differ from the original eleven cases")
        agenda = bench.schedule(selected, domain.CANDIDATES, 3, context.baseline["seed"])
        if len(agenda) != 99 or len({(row["task"], row["rep"], row["candidate"]) for row in agenda}) != 99:
            raise ValueError("Continuation agenda is not eleven cases times three candidates times three repetitions")
    return SimpleNamespace(round_dir=round_dir, money=money, money_context=context,
                           provenance=provenance, tasks=tasks, schedule=agenda,
                           candidates=context.candidates, baseline=context.baseline)


def inspect_origin(path, context, complete=False):
    money = context.money
    source = context.money_context
    frozen = read_json(path / "round-freeze.json")
    if frozen.get("command") != "run" or frozen.get("round") != "money-sol-low-glm-flash":
        raise ValueError("Money origin must be the executed monetary round")
    if frozen.get("phases") != [source.phases[phase] for phase in money.PHASES]:
        raise ValueError("Money origin agenda or limits differ from the fixed round")
    money.check_round(path, source, frozen)
    files = {"round-freeze.json": digest(path / "round-freeze.json")}
    for name in frozen["source_hashes"]:
        files[f".round-source/{name}"] = digest(path / ".round-source" / name)
    with money.harness_modules(source.round_dir / "harness") as (bench, _):
        for phase in money.PHASES:
            folder = path / phase
            if not folder.exists() and not complete:
                continue
            phase_freeze = bench.check_freeze(folder)
            expected = {**source.phases[phase], "candidates": context.candidates,
                        "seed": context.baseline["seed"], "global_seconds": context.baseline["global_seconds"],
                        "source_hashes": source.provenance["source_hashes"],
                        "catalog_sha256": context.baseline["catalog_sha256"]}
            if any(phase_freeze.get(key) != value for key, value in expected.items()):
                raise ValueError(f"Money {phase} source, cohort, tasks or catalog differs")
            image = phase_freeze["image_spec"]
            if image["tag"] != context.baseline["image_spec"]["image_id"]:
                raise ValueError(f"Money {phase} image selector differs")
            files[f"{phase}/freeze.json"] = digest(folder / "freeze.json")
            files[f"{phase}/models.json"] = digest(folder / "models.json")
            for name in phase_freeze["source_hashes"]:
                files[f"{phase}/.frozen-source/{name}"] = digest(folder / ".frozen-source" / name)
            if not complete:
                continue
            if image["image_id"] != context.baseline["image_spec"]["image_id"]:
                raise ValueError(f"Money {phase} container image differs")
            preflight = read_json(folder / "preflight.json")
            if preflight.get("status") != "passed" or not preflight.get("namespace_validated"):
                raise ValueError(f"Money {phase} preflight is incomplete or blocked")
            files[f"{phase}/preflight.json"] = digest(folder / "preflight.json")
            for row in phase_freeze["schedule"]:
                result_path = folder / "trials" / row["id"] / "result.json"
                if not result_path.exists():
                    raise ValueError("Money origin is incomplete; wait for all nine monetary trials")
                result = read_json(result_path)
                if any(result.get(key) != value for key, value in row.items()):
                    raise ValueError(f"Money {phase} result identity differs from its agenda")
                if result.get("status") in ("started", "not_run"):
                    raise ValueError("Money origin is incomplete; wait for all nine monetary trials")
                if result.get("status") not in TERMINAL_STATUSES:
                    raise ValueError("Money origin has an infrastructure/scope violation or an unknown status")
                if phase == "budget" and not result.get("proof_passed"):
                    raise ValueError("Money budget gate did not pass")
                if phase == "smoke" and not result.get("accepted"):
                    raise ValueError("Money smoke gate did not pass")
                files[f"{phase}/trials/{row['id']}/result.json"] = digest(result_path)
    return files


def core_args(args, context):
    return argparse.Namespace(phase="screening", reps=3, seconds=1200, calls=60,
                              seed=context.baseline["seed"], global_seconds=context.baseline["global_seconds"],
                              block_start=0, block_count=None, binary=shutil.which(args.binary) or args.binary,
                              docker=shutil.which(args.docker) or args.docker, build_image=False,
                              database=Path.home() / ".local/share/opencode/opencode.db",
                              cache=context.money_context.baseline_path / "models.json",
                              image=context.baseline["image_spec"]["image_id"])


def freeze_extension(args, context, origin_hashes, frozen):
    snapshot = args.out / ".round-source"
    snapshot.mkdir()
    hashes = {}
    for name in (*WRAPPER_FILES, "provenance.json"):
        shutil.copyfile(context.round_dir / name, snapshot / name)
        hashes[name] = digest(context.round_dir / name)
    extension = {"schema": 1, "round": "sol-low-glm-flash-rest", "command": args.command,
                 "source_hashes": hashes, "provenance": context.provenance,
                 "money_run": str(args.money_run), "money_origin_hashes": origin_hashes,
                 "tasks": context.tasks, "schedule": context.schedule,
                 "candidates": context.candidates, "reps": 3, "budget": frozen["budget"],
                 "seed": frozen["seed"], "global_seconds": frozen["global_seconds"],
                 "catalog_sha256": frozen["catalog_sha256"], "image_id": args.image,
                 "comparison_trials": {"monetary_origin": 9, "continuation": 99, "complete_screening": 108},
                 "gate_copy_hashes": {}}
    save(args.out / "round-freeze.json", extension)
    return extension


def copy_gates(args, context, extension):
    copies = args.out / "gate-proofs"
    for phase in ("budget", "smoke"):
        source = args.money_run / phase
        destination = copies / phase
        destination.mkdir(parents=True)
        keys = [key for key in extension["money_origin_hashes"] if key.startswith(f"{phase}/")]
        for key in keys:
            relative = Path(key).relative_to(phase)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
            extension["gate_copy_hashes"][str(target.relative_to(args.out))] = digest(target)
    save(args.out / "round-freeze.json", extension)


def guard(args, context, extension):
    current = load_context(context.round_dir)
    if read_json(args.out / "round-freeze.json") != extension:
        raise ValueError("Continuation freeze changed")
    if current.tasks != extension["tasks"] or current.schedule != extension["schedule"] or current.candidates != extension["candidates"]:
        raise ValueError("Continuation tasks, agenda or cohort changed")
    if current.provenance != extension["provenance"]:
        raise ValueError("Continuation provenance changed")
    for name, expected in extension["source_hashes"].items():
        if digest(context.round_dir / name) != expected or digest(args.out / ".round-source" / name) != expected:
            raise ValueError("Continuation orchestrator changed after freezing")
    for relative, expected in extension["money_origin_hashes"].items():
        if digest(args.money_run / relative) != expected:
            raise ValueError("Money origin evidence changed after freezing")
    for relative, expected in extension["gate_copy_hashes"].items():
        if digest(args.out / relative) != expected:
            raise ValueError("Private gate proof changed after freezing")


def report(bench, out):
    summary = bench.report(out)
    path = out / "report.md"
    path.write_text(path.read_text().replace("As seis configurações", "As 3 configurações"))
    return summary


def run_schedule(bench, args, context, frozen, extension, candidates, selected, budget):
    candidate_map = {candidate.id: candidate for candidate in candidates}
    task_map = {task.id: task for task in selected}
    started = time.monotonic()
    try:
        for block in sorted({row["block"] for row in frozen["schedule"]}):
            if time.monotonic() - started >= args.global_seconds:
                break
            bench.runtime.validate_oauth_window(candidates, args.database,
                                               len(candidates) * (budget.seconds + budget.grace + bench.SESSION_MARGIN_SECONDS))
            for row in [row for row in frozen["schedule"] if row["block"] == block]:
                guard(args, context, extension)
                if bench.check_freeze(args.out) != frozen:
                    raise ValueError("Core trial freeze changed after preflight")
                result = bench.run_trial(row, args.out, args, frozen, candidate_map[row["candidate"]], task_map[row["task"]], budget)
                print(f"{row['id']} {row['candidate']} {row['task']} {result['status']} accepted={result['accepted']}", flush=True)
                report(bench, args.out)
                if result["status"] in ("infra_error", "scope_violation"):
                    print("Stopped after infrastructure or scope violation; remaining trials remain visible", flush=True)
                    return 1
    finally:
        summary = report(bench, args.out)
    return 0 if summary["started"] == summary["planned"] else 1


def execute(args, context):
    if args.out == args.money_run or args.money_run in args.out.parents or args.out in args.money_run.parents:
        raise ValueError("Continuation output must be outside the monetary origin")
    with context.money.harness_modules(context.money_context.round_dir / "harness") as (bench, domain):
        if args.command == "report":
            print(json.dumps(report(bench, args.out), ensure_ascii=False, indent=2))
            return 0
        if args.out.exists():
            raise ValueError("Output must be new; prior evidence is never overwritten")
        origin_hashes = inspect_origin(args.money_run, context, complete=args.command in ("run", "preflight"))
        python = importlib.import_module("tasks_python")
        typescript = importlib.import_module("tasks_typescript")
        selected = tuple(task for task in (*python.TASKS, *typescript.TASKS)
                         if task.phase == "screening" and task.id != "py-money-contract")
        candidates = domain.CANDIDATES
        budget = domain.Budget()
        options = core_args(args, context)
        options.command, options.out, options.money_run = args.command, args.out, args.money_run
        args.out.mkdir(parents=True)
        frozen = bench.freeze(args.out, options, selected, candidates, budget)
        if normalized(frozen["tasks"]) != context.tasks or frozen["schedule"] != context.schedule:
            raise ValueError("Core agenda differs from the continuation")
        extension = freeze_extension(options, context, origin_hashes, frozen)
        try:
            guard(options, context, extension)
            if args.command == "plan":
                print(f"Frozen 99 sessions across eleven cases; zero model calls: {args.out}")
                return 0
            if args.command == "validate":
                checked = bench.validate(selected, args.out)
                guard(options, context, extension)
                print(f"Validation {checked['status']}; zero model calls: {args.out / 'validation.json'}")
                return 0 if checked["status"] == "passed" else 1
            copy_gates(options, context, extension)
            guard(options, context, extension)
            checked = bench.preflight(args.out, options, selected, candidates)
            guard(options, context, extension)
            if checked["status"] != "passed":
                print(f"Preflight blocked: {checked['error']}. Zero model calls. Evidence: {args.out / 'preflight.json'}", flush=True)
                return 1
            checked_freeze = bench.check_freeze(args.out)
            if any(normalized(checked_freeze.get(key)) != normalized(value)
                   for key, value in frozen.items() if key != "image_spec"):
                raise ValueError("Core contract, agenda or limits changed during preflight")
            for key in ("tag", "dockerfile_sha256"):
                if checked_freeze["image_spec"][key] != frozen["image_spec"][key]:
                    raise ValueError("Core image selector changed during preflight")
            frozen = checked_freeze
            if frozen["image_spec"]["image_id"] != context.baseline["image_spec"]["image_id"]:
                raise ValueError("Continuation container image differs from the original immutable image")
            gates = [bench.require_gate(args.out / "gate-proofs" / phase, phase, frozen) for phase in ("budget", "smoke")]
            save(args.out / "gates.json", gates)
            guard(options, context, extension)
            if args.command == "preflight":
                print(f"Preflight passed; reused gates; zero model calls: {args.out / 'preflight.json'}")
                return 0
            return run_schedule(bench, options, context, frozen, extension, candidates, selected, budget)
        finally:
            report(bench, args.out)


def main():
    parser = argparse.ArgumentParser(description="Complete eleven remaining implementer cases using the finished corrected monetary round")
    parser.add_argument("command", choices=("plan", "validate", "preflight", "run", "report"))
    parser.add_argument("--money-run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--docker", default="docker")
    args = parser.parse_args()
    args.money_run, args.out = args.money_run.resolve(), args.out.resolve()
    try:
        return execute(args, load_context())
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Blocked: {error}. No further model calls.\n")


if __name__ == "__main__":
    raise SystemExit(main())
