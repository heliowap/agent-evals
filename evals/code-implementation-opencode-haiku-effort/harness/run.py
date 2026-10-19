import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace


ROUND = Path(__file__).resolve().parent
PHASES = ("budget", "smoke", "screening")
WRAPPER_FILES = ("run.py", "README.md", "test_run.py")
MODULES = ("bench", "controller", "domain", "grader", "isolation", "runtime", "tasks",
           "tasks_python", "tasks_typescript", "contract")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
RUNTIME_ANCHOR = '        model["modelID"] = candidate.wire_model\n'
RUNTIME_VARIANTS = ('        model["variants"] = [{"id": effort, "settings": {"effort": effort}}\n'
                    '                             for effort in ("low", "medium", "high", "xhigh", "max")]\n')
DOMAIN_COHORT = '''CANDIDATES = (
    *(Candidate(f"haiku-{effort}", "cli_proxy", "cpa-claude-haiku-5-5", effort, "cli_proxy",
                "http://127.0.0.1:8317/v1", effort, False, "claude-haiku-5-5", "messages", "key")
      for effort in ("low", "medium", "high", "xhigh", "max")),
)
'''
TASK_SELECTION = '''TASKS = tuple(
    replace(task, id="py-money-contract-v2", request=REQUEST,
            files={**task.files, "README.md": task.files["README.md"].replace(task.request, REQUEST)})
    if task.id == "py-money-contract" else task
    for task in PYTHON_TASKS + TYPESCRIPT_TASKS
)
'''.rstrip()


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


def source_hashes(folder):
    paths = [*folder.glob("*.py"), *folder.glob("*.js"), folder / "Dockerfile", folder / ".dockerignore", folder / "README.md"]
    return {path.name: digest(path) for path in sorted(paths)}


def verify_provenance(round_dir):
    provenance = read_json(round_dir / "provenance.json")
    if provenance.get("schema") != 1:
        raise ValueError("Unsupported round provenance schema")
    try:
        baseline_path = Path(provenance["baseline_path"])
        origin_path = Path(provenance["contract_origin_path"])
        if not baseline_path.is_absolute() or not origin_path.is_absolute():
            raise ValueError("Provenance evidence paths must be absolute")
        if digest(baseline_path / "freeze.json") != provenance["baseline_freeze_sha256"]:
            raise ValueError("Baseline freeze differs from provenance")
        baseline = read_json(baseline_path / "freeze.json")
        expected = provenance["baseline_source_hashes"]
        if expected != baseline["source_hashes"] or source_hashes(baseline_path / ".frozen-source") != expected:
            raise ValueError("Baseline source differs from provenance")
        if provenance["allowed_changes"] != {"modified": ["domain.py", "runtime.py", "tasks.py"], "added": ["contract.py"]}:
            raise ValueError("Round changes exceed the permitted cohort, variants and contract selection")
        current = source_hashes(round_dir / "harness")
        if set(current) != set(expected) | {"contract.py"} or current != provenance["source_hashes"]:
            raise ValueError("Round harness source or file set differs from provenance")
        for name, value in expected.items():
            if name not in ("domain.py", "runtime.py", "tasks.py") and current[name] != value:
                raise ValueError(f"Core source is not byte-equivalent to baseline: {name}")
        original_runtime = (baseline_path / ".frozen-source/runtime.py").read_text()
        if original_runtime.count(RUNTIME_ANCHOR) != 1:
            raise ValueError("Baseline runtime has no unique variant registration boundary")
        expected_runtime = original_runtime.replace(RUNTIME_ANCHOR, RUNTIME_ANCHOR + RUNTIME_VARIANTS)
        if (round_dir / "harness/runtime.py").read_text() != expected_runtime:
            raise ValueError("Runtime changes exceed explicit Anthropic variant registration")
        original_domain = (baseline_path / ".frozen-source/domain.py").read_text()
        expected_domain = original_domain[:original_domain.index("CANDIDATES = (")] + DOMAIN_COHORT
        if (round_dir / "harness/domain.py").read_text() != expected_domain:
            raise ValueError("Domain changes exceed the fixed Haiku cohort")
        original_tasks = (baseline_path / ".frozen-source/tasks.py").read_text()
        selection_anchor = "TASKS = PYTHON_TASKS + TYPESCRIPT_TASKS"
        if original_tasks.count(selection_anchor) != 1:
            raise ValueError("Baseline tasks have no unique selection boundary")
        expected_tasks = ("from dataclasses import replace\nfrom contract import REQUEST\n" + original_tasks).replace(
            selection_anchor, TASK_SELECTION)
        if (round_dir / "harness/tasks.py").read_text() != expected_tasks:
            raise ValueError("Task changes exceed corrected monetary selection")
        if digest(baseline_path / "models.json") != baseline["catalog_sha256"] or baseline["catalog_sha256"] != provenance["catalog_sha256"]:
            raise ValueError("Native catalog differs from provenance")
        if digest(origin_path / "freeze.json") != provenance["contract_origin_freeze_sha256"]:
            raise ValueError("Completed corrected contract freeze differs from provenance")
        origin = read_json(origin_path / "freeze.json")
        if origin["dataset_revision"]["id"] != "money-contract-v2" or len(origin["tasks"]) != 1:
            raise ValueError("Contract origin is not the corrected monetary round")
        request = origin["tasks"][0]["request"]
        if hashlib.sha256(request.encode()).hexdigest() != provenance["contract_sha256"]:
            raise ValueError("Corrected contract differs from provenance")
        if {name: digest(round_dir / name) for name in WRAPPER_FILES} != provenance["wrapper_hashes"]:
            raise ValueError("Round orchestrator source differs from provenance")
    except (KeyError, TypeError, OSError) as error:
        raise ValueError("Incomplete round provenance or baseline evidence") from error
    return provenance, baseline_path, baseline, origin


@contextmanager
def harness_modules(folder):
    saved = {name: sys.modules.pop(name, None) for name in MODULES}
    sys.path.insert(0, str(folder))
    try:
        yield importlib.import_module("bench"), importlib.import_module("domain")
    finally:
        sys.path.pop(0)
        for name, previous in saved.items():
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous


def load_context(round_dir=None):
    round_dir = (round_dir or ROUND).resolve()
    provenance, baseline_path, baseline, origin = verify_provenance(round_dir)
    with harness_modules(round_dir / "harness") as (bench, domain):
        candidates = [bench.runtime.public_candidate(candidate) for candidate in domain.CANDIDATES]
        if candidates != provenance["candidates"]:
            raise ValueError("Candidate identities differ from provenance")
        selected = normalized([asdict(task) for task in bench.tasks.inventory("screening")])
        expected = [origin["tasks"][0] if task["id"] == "py-money-contract" else task
                    for task in baseline["tasks"]]
        if len(selected) != 12 or selected != expected:
            raise ValueError("Screening TaskSpecs differ from the original eleven and corrected monetary case")
        if hashlib.sha256(bench.tasks.REQUEST.encode()).hexdigest() != provenance["contract_sha256"]:
            raise ValueError("Executable contract differs from the corrected contract")
        if [(candidate.id, candidate.selection, candidate.wire_model, candidate.effort,
             candidate.credential_provider, candidate.upstream, candidate.protocol,
             candidate.auth_type, candidate.fast) for candidate in domain.CANDIDATES] != [
                 (f"haiku-{effort}", f"cli_proxy/cpa-claude-haiku-5-5#{effort}", "claude-haiku-5-5", effort,
                  "cli_proxy", "http://127.0.0.1:8317/v1", "messages", "key", False) for effort in EFFORTS]:
            raise ValueError("Haiku model, route or effort cohort differs from the fixed round")
        phases = {}
        for phase in PHASES:
            reps = 3 if phase == "screening" else 1
            selected = bench.tasks.inventory(phase)
            phases[phase] = {"phase": phase, "reps": reps,
                             "budget": asdict(domain.Budget(20, 2) if phase == "budget" else domain.Budget()),
                             "tasks": normalized([asdict(item) for item in selected]),
                             "schedule": bench.schedule(selected, domain.CANDIDATES, reps, baseline["seed"])}
    return SimpleNamespace(round_dir=round_dir, baseline_path=baseline_path, baseline=baseline,
                           provenance=provenance, phases=phases, candidates=candidates)


def selected_phases(phase):
    return PHASES if phase == "all" else PHASES[:PHASES.index(phase) + 1]


def phase_command(args, context, phase):
    item = context.phases[phase]
    command = [sys.executable, "-B", str(context.round_dir / "harness/bench.py"), args.command,
               "--out", str(args.out / phase), "--phase", phase,
               "--reps", str(item["reps"]), "--seconds", str(item["budget"]["seconds"]),
               "--calls", str(item["budget"]["calls"]), "--seed", str(context.baseline["seed"]),
               "--global-seconds", str(context.baseline["global_seconds"]),
               "--cache", str(context.baseline_path / "models.json"),
               "--image", context.baseline["image_spec"]["image_id"],
               "--binary", args.binary, "--docker", args.docker]
    if phase != "budget":
        command += ["--budget-proof", str(args.out / "budget")]
    if phase == "screening":
        command += ["--smoke-proof", str(args.out / "smoke")]
    return command


def freeze_round(args, context):
    if args.out.exists():
        raise ValueError("Output must be new; prior evidence is never overwritten")
    args.out.mkdir(parents=True)
    snapshot = args.out / ".round-source"
    snapshot.mkdir()
    names = (*WRAPPER_FILES, "provenance.json")
    for name in names:
        shutil.copyfile(context.round_dir / name, snapshot / name)
    value = {"schema": 1, "round": "haiku-5-5", "command": args.command,
             "source_hashes": {name: digest(context.round_dir / name) for name in names},
             "provenance": context.provenance, "candidates": context.candidates,
             "phases": [context.phases[phase] for phase in selected_phases(args.phase)],
             "seed": context.baseline["seed"], "global_seconds": context.baseline["global_seconds"],
             "catalog_sha256": context.baseline["catalog_sha256"],
             "image_id": context.baseline["image_spec"]["image_id"],
             "commands": {phase: phase_command(args, context, phase) for phase in selected_phases(args.phase)}}
    save(args.out / "round-freeze.json", value)
    return value


def check_round(out, context, frozen):
    current = load_context(context.round_dir)
    if read_json(out / "round-freeze.json") != frozen:
        raise ValueError("Round agenda or evidence changed after freezing")
    if current.provenance != frozen["provenance"] or current.candidates != frozen["candidates"]:
        raise ValueError("Round provenance or cohort changed after freezing")
    if [current.phases[item["phase"]] for item in frozen["phases"]] != frozen["phases"]:
        raise ValueError("Round contract, agenda or budget changed after freezing")
    for name, expected in frozen["source_hashes"].items():
        if digest(context.round_dir / name) != expected or digest(out / ".round-source" / name) != expected:
            raise ValueError("Round orchestrator changed after freezing")


def inspect_phase(out, context, phase, command):
    with harness_modules(context.round_dir / "harness") as (bench, _):
        frozen = bench.check_freeze(out)
        expected = {**context.phases[phase], "candidates": context.candidates,
                    "seed": context.baseline["seed"], "global_seconds": context.baseline["global_seconds"],
                    "source_hashes": context.provenance["source_hashes"],
                    "catalog_sha256": context.baseline["catalog_sha256"]}
        if any(frozen.get(name) != value for name, value in expected.items()):
            raise ValueError("Phase contract, cohort, agenda or source differs from the fixed round")
        image = frozen["image_spec"]
        if image["tag"] != context.baseline["image_spec"]["image_id"]:
            raise ValueError("Phase image selector differs from the original immutable image")
        if command in ("preflight", "run") and image["image_id"] != context.baseline["image_spec"]["image_id"]:
            raise ValueError("Phase container image differs from the original image")
        summary = bench.report(out)
        if command == "plan":
            return True, summary
        if command == "validate":
            return read_json(out / "validation.json")["status"] == "passed", summary
        if command == "preflight":
            return read_json(out / "preflight.json")["status"] == "passed", summary
        complete = summary["started"] == summary["planned"]
        safe = all(not set(item["statuses"]) & {"infra_error", "scope_violation", "not_run"}
                   for item in summary["by_candidate"].values())
        if phase in ("budget", "smoke"):
            bench.require_gate(out, phase, frozen)
        return complete and safe, summary


def report_round(out):
    frozen = read_json(out / "round-freeze.json")
    rows = []
    for item in frozen["phases"]:
        phase = item["phase"]
        path = out / phase / "summary.json"
        summary = read_json(path) if path.exists() else None
        report = out / phase / "report.md"
        if report.exists():
            report.write_text(report.read_text().replace("As seis configurações", f"As {len(frozen['candidates'])} configurações"))
        rows.append({"phase": phase, "planned": len(item["schedule"]), "summary": summary})
    value = {"round": frozen["round"], "planned": sum(row["planned"] for row in rows), "phases": rows,
             "model_calls": sum((row["summary"] or {}).get("model_calls", 0) for row in rows)}
    save(out / "round-summary.json", value)
    return value


def execute(args, context, run_process=None):
    if args.command == "report":
        check_round(args.out, context, read_json(args.out / "round-freeze.json"))
        print(json.dumps(report_round(args.out), ensure_ascii=False, indent=2))
        return 0
    current = load_context(context.round_dir)
    if current.provenance != context.provenance or current.phases != context.phases:
        raise ValueError("Round changed before freezing")
    frozen = freeze_round(args, context)
    run_process = run_process or subprocess.run
    try:
        for item in frozen["phases"]:
            phase = item["phase"]
            check_round(args.out, context, frozen)
            print(f"Phase {phase}: {len(item['schedule'])} sessions", flush=True)
            completed = run_process(frozen["commands"][phase], check=False)
            check_round(args.out, context, frozen)
            if completed.returncode:
                print(f"Stopped after {phase}; subprocess exit={completed.returncode}", flush=True)
                return 1
            passed, _ = inspect_phase(args.out / phase, context, phase, args.command)
            if not passed:
                print(f"Stopped after incomplete or failed {phase}; remaining phases remain visible", flush=True)
                return 1
        return 0
    finally:
        report_round(args.out)


def main():
    parser = argparse.ArgumentParser(description="Haiku 5.5 implementation comparison across five efforts with fresh gates")
    parser.add_argument("command", choices=("plan", "validate", "preflight", "run", "report"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", choices=("all", *PHASES), default="all")
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--docker", default="docker")
    args = parser.parse_args()
    args.out = args.out.resolve()
    try:
        return execute(args, load_context())
    except (ValueError, OSError) as error:
        parser.exit(1, f"Blocked: {error}. No further model calls.\n")


if __name__ == "__main__":
    raise SystemExit(main())
