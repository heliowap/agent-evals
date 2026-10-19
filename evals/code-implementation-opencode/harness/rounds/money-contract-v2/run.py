import argparse
from contextlib import contextmanager
from dataclasses import asdict, replace
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace


ROUND = Path(__file__).resolve().parent
TASK_ID = "py-money-contract-v2"
BASE_TASK_ID = "py-money-contract"
REVISION_ID = "money-contract-v2"
REVISION_FILES = ("run.py", "request.txt", "provenance.json")
HARNESS_MODULES = ("bench", "controller", "domain", "grader", "isolation", "runtime", "tasks", "tasks_python", "tasks_typescript")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return json.loads(json.dumps(value))


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read evidence: {path}") from error


def source_files(folder):
    return {path.name for path in [*folder.glob("*.py"), *folder.glob("*.js"), folder / "Dockerfile", folder / ".dockerignore", folder / "README.md"]}


def verify_provenance(round_dir):
    provenance = read_json(round_dir / "provenance.json")
    if provenance.get("schema") != 1:
        raise ValueError("Unsupported rerun provenance schema")
    try:
        baseline_path = Path(provenance["baseline_path"])
        expected = provenance["source_hashes"]
        if not baseline_path.is_absolute() or not isinstance(expected, dict):
            raise ValueError("Rerun provenance requires an absolute baseline path and source hashes")
        if digest(baseline_path / "freeze.json") != provenance["baseline_freeze_sha256"]:
            raise ValueError("Baseline freeze differs from rerun provenance")
        baseline = read_json(baseline_path / "freeze.json")
        if expected != baseline["source_hashes"]:
            raise ValueError("Rerun source hashes differ from the baseline freeze")
        for folder in (round_dir / "harness", baseline_path / ".frozen-source"):
            if source_files(folder) != set(expected):
                raise ValueError(f"Frozen harness file set differs: {folder}")
            if any(digest(folder / name) != expected[name] for name in expected):
                raise ValueError(f"Frozen harness source differs: {folder}")
        if digest(baseline_path / "models.json") != baseline["catalog_sha256"]:
            raise ValueError("Baseline native catalog differs from its freeze")
    except (KeyError, TypeError, OSError) as error:
        raise ValueError("Incomplete rerun provenance or baseline evidence") from error
    return provenance, baseline_path, baseline


def import_harness(folder):
    saved = {name: sys.modules.pop(name, None) for name in HARNESS_MODULES}
    sys.path.insert(0, str(folder))
    try:
        bench = importlib.import_module("bench")
        domain = importlib.import_module("domain")
        return bench, domain, {name: sys.modules[name] for name in HARNESS_MODULES}
    finally:
        sys.path.pop(0)
        for name, previous in saved.items():
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous


@contextmanager
def activate_harness(context):
    saved = {name: sys.modules.get(name) for name in HARNESS_MODULES}
    sys.modules.update(context.modules)
    sys.path.insert(0, str(context.round_dir / "harness"))
    try:
        yield
    finally:
        sys.path.pop(0)
        for name, previous in saved.items():
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous


def load_context(round_dir=None):
    round_dir = (round_dir or ROUND).resolve()
    provenance, baseline_path, baseline = verify_provenance(round_dir)
    bench, domain, modules = import_harness(round_dir / "harness")
    if baseline["phase"] != "screening" or baseline["reps"] != 3:
        raise ValueError("This rerun requires the original three-repetition screening")
    if [bench.runtime.public_candidate(candidate) for candidate in domain.CANDIDATES] != baseline["candidates"]:
        raise ValueError("Baseline candidates differ from the frozen harness")
    originals = [task for task in bench.tasks.inventory("screening") if task.id == BASE_TASK_ID]
    recorded = [task for task in baseline["tasks"] if task["id"] == BASE_TASK_ID]
    if len(originals) != 1 or len(recorded) != 1:
        raise ValueError("The baseline must contain exactly one original money task")
    original, original_frozen = originals[0], recorded[0]
    if normalized(asdict(original)) != original_frozen:
        raise ValueError("Original money task differs from the baseline freeze")
    request = (round_dir / "request.txt").read_text().strip()
    if not request or request == original.request:
        raise ValueError("The revised contract must be nonempty and differ from the original")
    if original.files["README.md"].count(original.request) != 1:
        raise ValueError("The original README must contain the original request exactly once")
    files = {**original.files, "README.md": original.files["README.md"].replace(original.request, request)}
    task = replace(original, id=TASK_ID, request=request, files=files)
    budget = domain.Budget(**baseline["budget"])
    return SimpleNamespace(round_dir=round_dir, package=round_dir.parents[1], baseline_path=baseline_path,
                           provenance=provenance, baseline=baseline, bench=bench, domain=domain,
                           modules=modules, task=task, candidates=domain.CANDIDATES, budget=budget,
                           revision_hashes={name: digest(round_dir / name) for name in REVISION_FILES})


def fixed_args(command, out, context, binary="opencode", docker="docker"):
    baseline = context.baseline
    return argparse.Namespace(command=command, out=out, phase="screening", reps=3,
                              seed=baseline["seed"], seconds=context.budget.seconds, calls=context.budget.calls,
                              global_seconds=baseline["global_seconds"], block_start=0, block_count=None,
                              binary=shutil.which(binary) or binary, docker=shutil.which(docker) or docker,
                              image=baseline["image_spec"]["tag"], build_image=False,
                              database=Path.home() / ".local/share/opencode/opencode.db",
                              cache=context.baseline_path / "models.json",
                              budget_proof=out / "gate-proofs/budget", smoke_proof=out / "gate-proofs/smoke")


def freeze_revision(out, args, context):
    if {name: digest(context.round_dir / name) for name in REVISION_FILES} != context.revision_hashes:
        raise ValueError("Rerun source changed before freezing")
    if (context.round_dir / "request.txt").read_text().strip() != context.task.request:
        raise ValueError("The revised task does not match the current contract")
    frozen = context.bench.freeze(out, args, (context.task,), context.candidates, context.budget)
    snapshot = out / ".rerun-source"
    snapshot.mkdir()
    hashes = {}
    for name in REVISION_FILES:
        shutil.copyfile(context.round_dir / name, snapshot / name)
        hashes[name] = digest(snapshot / name)
    if hashes != context.revision_hashes:
        raise ValueError("Rerun source changed while freezing")
    revision = {"id": REVISION_ID, "base_task": BASE_TASK_ID, "task": TASK_ID,
                "baseline_path": str(context.baseline_path),
                "baseline_freeze_sha256": context.provenance["baseline_freeze_sha256"],
                "contract_sha256": hashes["request.txt"], "source_hashes": hashes}
    frozen["dataset_revision"] = revision
    context.bench.runtime.save(out / "freeze.json", frozen)
    context.bench.runtime.save(out / "revision.json", revision)
    return frozen


def check_revision(out, context):
    verify_provenance(context.round_dir)
    frozen = context.bench.check_freeze(out)
    revision = frozen.get("dataset_revision")
    if not isinstance(revision, dict) or read_json(out / "revision.json") != revision:
        raise ValueError("Dataset revision differs from its frozen evidence")
    expected = {"id": REVISION_ID, "base_task": BASE_TASK_ID, "task": TASK_ID,
                "baseline_path": str(context.baseline_path),
                "baseline_freeze_sha256": context.provenance["baseline_freeze_sha256"],
                "contract_sha256": digest(context.round_dir / "request.txt"),
                "source_hashes": {name: digest(context.round_dir / name) for name in REVISION_FILES}}
    if revision != expected:
        raise ValueError("Rerun contract or implementation changed after freezing")
    if any(digest(out / ".rerun-source" / name) != value for name, value in revision["source_hashes"].items()):
        raise ValueError("Frozen rerun source changed")
    if frozen["tasks"] != [normalized(asdict(context.task))]:
        raise ValueError("Frozen task differs from the revised contract")
    if (context.round_dir / "request.txt").read_text().strip() != context.task.request:
        raise ValueError("The revised task does not match the current contract")
    fixed = {"phase": "screening", "reps": 3, "seed": context.baseline["seed"],
             "budget": asdict(context.budget), "global_seconds": context.baseline["global_seconds"],
             "candidates": [context.bench.runtime.public_candidate(candidate) for candidate in context.candidates],
             "schedule": context.bench.schedule((context.task,), context.candidates, 3, context.baseline["seed"])}
    if any(frozen.get(name) != expected for name, expected in fixed.items()):
        raise ValueError("Frozen agenda, cohort or budget differs from this fixed rerun")
    return frozen


def copy_gate_proofs(out, context):
    evidence = []
    for phase in ("budget", "smoke"):
        original = context.package / "results" / ("budget-r4" if phase == "budget" else "smoke")
        gate = read_json(original / "freeze.json")
        if gate.get("phase") != phase:
            raise ValueError(f"The fixed {phase} gate has an unexpected phase")
        files = [Path("freeze.json")]
        for row in gate["schedule"]:
            trial_id = row["id"]
            if not isinstance(trial_id, str) or Path(trial_id).name != trial_id:
                raise ValueError("Gate contains an unsafe trial path")
            files.append(Path("trials") / trial_id / "result.json")
        if any(not (original / name).is_file() for name in files):
            raise ValueError(f"The {phase} gate is incomplete")
        destination = out / "gate-proofs" / phase
        hashes = {}
        for name in files:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / name, target)
            hashes[name.as_posix()] = digest(target)
        evidence.append({"phase": phase, "origin": str(original.resolve()),
                         "copy": str(destination.resolve()), "source_hashes": hashes})
    context.bench.runtime.save(out / "gate-provenance.json", evidence)
    return evidence


def execute(args, context):
    with activate_harness(context):
        return execute_active(args, context)


def execute_active(args, context):
    out, bench = args.out, context.bench
    if args.command == "report":
        print(json.dumps(bench.report(out), ensure_ascii=False, indent=2))
        return 0
    if out.exists():
        raise ValueError("Output must be new; prior evidence is never overwritten")
    out.mkdir(parents=True)
    frozen = freeze_revision(out, args, context)
    if args.command == "plan":
        bench.report(out)
        print(f"Frozen {len(frozen['schedule'])} sessions for {TASK_ID}; zero model calls: {out}")
        return 0
    if args.command == "validate":
        checked = bench.validate((context.task,), out)
        print(f"Validation {checked['status']}; zero model calls: {out / 'validation.json'}")
        return 0 if checked["status"] == "passed" else 1
    checked = bench.preflight(out, args, (context.task,), context.candidates)
    if checked["status"] != "passed":
        bench.report(out)
        print(f"Preflight blocked: {checked['error']}. Zero model calls. Evidence: {out / 'preflight.json'}", file=sys.stderr)
        return 1
    if args.command == "preflight":
        check_revision(out, context)
        print(f"Preflight passed; zero model calls: {out / 'preflight.json'}")
        return 0
    try:
        frozen = check_revision(out, context)
        copy_gate_proofs(out, context)
        gates = [bench.require_gate(args.budget_proof, "budget", frozen),
                 bench.require_gate(args.smoke_proof, "smoke", frozen)]
        bench.runtime.save(out / "gates.json", gates)
        candidates = {candidate.id: candidate for candidate in context.candidates}
        started = time.monotonic()
        for block in sorted({row["block"] for row in frozen["schedule"]}):
            if time.monotonic() - started >= args.global_seconds:
                break
            bench.runtime.validate_oauth_window(context.candidates, args.database,
                                                len(context.candidates) * (context.budget.seconds + context.budget.grace + bench.SESSION_MARGIN_SECONDS))
            for row in (row for row in frozen["schedule"] if row["block"] == block):
                frozen = check_revision(out, context)
                result = bench.run_trial(row, out, args, frozen, candidates[row["candidate"]], context.task, context.budget)
                print(f"{row['id']} {row['candidate']} {row['task']} {result['status']} accepted={result['accepted']}", flush=True)
                bench.report(out)
                if result["status"] in ("infra_error", "scope_violation"):
                    print("Stopped after infrastructure or scope violation; remaining trials remain visible", flush=True)
                    return 1
        return 0
    finally:
        bench.report(out)


def main():
    parser = argparse.ArgumentParser(description="Fixed 18-trial rerun of the explicit money contract")
    parser.add_argument("command", choices=("plan", "validate", "preflight", "run", "report"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--docker", default="docker")
    parsed = parser.parse_args()
    try:
        context = load_context()
        return execute(fixed_args(parsed.command, parsed.out.resolve(), context, parsed.binary, parsed.docker), context)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Rerun blocked: {error}. Zero further model calls.\n")


if __name__ == "__main__":
    raise SystemExit(main())
