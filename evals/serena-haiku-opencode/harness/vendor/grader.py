import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile
import time

from .domain import TaskSpec


TSC_VERSION = "5.9.3"
DEFAULT_TSC = Path.home() / ".bun/install/cache/typescript@5.9.3@@@1/bin/tsc"
GENERATED = (".build/", "__pycache__/", ".pytest_cache/")


def materialize(task, root, reference=False):
    root.mkdir(parents=True, exist_ok=True)
    files = {**task.files, **(task.reference if reference else {})}
    for name, content in files.items():
        path = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Task contains an unsafe path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def snapshot(root):
    files, violations = {}, []
    for base, dirs, names in os.walk(root, followlinks=False):
        for name in dirs[:] + names:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                violations.append({"path": relative, "reason": "symlink"})
                if name in dirs:
                    dirs.remove(name)
            elif stat.S_ISREG(mode):
                if generated(relative):
                    continue
                if path.stat().st_size > 2_097_152:
                    violations.append({"path": relative, "reason": "file_size"})
                    continue
                try:
                    files[relative] = path.read_text()
                except UnicodeDecodeError:
                    violations.append({"path": relative, "reason": "non_text"})
            elif not stat.S_ISDIR(mode):
                violations.append({"path": relative, "reason": "special_file"})
    return files, violations


def generated(path):
    return path.startswith(GENERATED) or "__pycache__" in Path(path).parts or path.endswith(".pyc")


def collect_patch(task, work):
    files, violations = snapshot(work)
    changed = sorted(name for name in set(task.files) | set(files) if task.files.get(name) != files.get(name) and not generated(name))
    allowed = lambda name: any(name.startswith(prefix) for prefix in task.allowed)
    violations += [{"path": name, "reason": "outside_scope"} for name in changed if not allowed(name)]
    patch = {name: files.get(name) for name in changed if allowed(name)}
    return {"files": patch, "changed_files": changed, "violations": violations,
            "scope_correct": not violations, "file_count": len(changed),
            "added_lines": sum(len(value.splitlines()) for value in patch.values() if value is not None),
            "removed_lines": sum(len(task.files.get(name, "").splitlines()) for name in patch)}


def apply_patch(task, root, patch):
    materialize(task, root)
    for name, content in patch.items():
        if not any(name.startswith(prefix) for prefix in task.allowed) or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Unsafe grader patch")
        if name.startswith("checks/"):
            continue
        path = root / name
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


def commands(task, node="node", tsc=None):
    compile_command = [node, str(tsc or DEFAULT_TSC), "-p", "tsconfig.json"] if task.language == "typescript" else [sys.executable, "-B", "-m", "compileall", "-q", "src"]
    public = [node, "checks/public.cjs"] if task.language == "typescript" else [sys.executable, "-B", "checks/public.py"]
    private = [node, ".acceptance.cjs"] if task.language == "typescript" else [sys.executable, "-B", ".acceptance.py"]
    structure = [node, ".structural.cjs"] if task.language == "typescript" else [sys.executable, "-B", ".structural.py"]
    return {"compilation": compile_command, "regression": public, "acceptance": private,
            **({"structural": structure} if task.structural else {})}


def private_scripts(task, root):
    suffix = "cjs" if task.language == "typescript" else "py"
    (root / f".acceptance.{suffix}").write_text(task.acceptance)
    if task.structural:
        (root / f".structural.{suffix}").write_text(task.structural)


def check_runner(argv, root, language, name):
    marker = "CHECK_COMPLETE_" + secrets.token_hex(24)
    if language == "typescript":
        runner = root / f".runner-{name}.cjs"
        runner.write_text("Promise.resolve(require('./" + argv[-1] + "')).then(() => console.log(" + json.dumps(marker) + "), error => { console.error(error); process.exitCode = 1; });\n")
    else:
        runner = root / f".runner-{name}.py"
        runner.write_text("import runpy\nrunpy.run_path(" + repr(argv[-1]) + ", run_name='__main__')\nprint(" + repr(marker) + ", flush=True)\n")
    return [argv[0], *(["-B"] if language == "python" else []), runner.name], marker


def require_completion(result, marker):
    completed = marker in result.get("stdout", "").splitlines()
    return {**result, "passed": result["passed"] and completed, "check_completed": completed,
            "stdout": result.get("stdout", "").replace(marker, "[check completed]")}


def run_local(argv, root):
    started = time.monotonic()
    try:
        process = subprocess.run(argv, cwd=root, env={**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"},
                                 capture_output=True, text=True, timeout=30)
        return {"passed": process.returncode == 0, "exit_code": process.returncode,
                "stdout": process.stdout, "stderr": process.stderr, "wall_s": time.monotonic() - started}
    except subprocess.TimeoutExpired:
        return {"passed": False, "exit_code": None, "timeout": True, "wall_s": time.monotonic() - started}


def validate_task(task, *, node=None, tsc=None):
    results = {}
    if task.language == "typescript":
        version = subprocess.run([node or "node", str(tsc or DEFAULT_TSC), "--version"], capture_output=True, text=True, timeout=15)
        if version.returncode or version.stdout.strip() != "Version " + TSC_VERSION:
            raise ValueError("Trusted validation requires TypeScript 5.9.3")
    for reference in (False, True):
        with tempfile.TemporaryDirectory(prefix="trusted-project-") as folder:
            root = Path(folder)
            materialize(task, root, reference)
            private_scripts(task, root)
            checks = {}
            for name, argv in commands(task, node or "node", tsc).items():
                if name != "compilation":
                    argv, marker = check_runner(argv, root, task.language, name)
                    checks[name] = require_completion(run_local(argv, root), marker)
                else:
                    checks[name] = run_local(argv, root)
            results["reference" if reference else "baseline"] = checks
    baseline, reference = results["baseline"], results["reference"]
    results["valid"] = (baseline["compilation"]["passed"] and baseline["regression"]["passed"]
                        and not all(c["passed"] for c in baseline.values()) and all(c["passed"] for c in reference.values()))
    results["task"] = task.id
    return results


def grade(task, work, out, image, docker="docker"):
    from .isolation import CodeContainer
    patch = collect_patch(task, work)
    out.mkdir(parents=True, exist_ok=True)
    (out / "patch.json").write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n")
    checks = {}
    with tempfile.TemporaryDirectory(prefix="clean-project-") as folder:
        root = Path(folder)
        apply_patch(task, root, patch["files"])
        private_scripts(task, root)
        invocations = {}
        for name, argv in commands(task, "node", "/usr/local/bin/tsc").items():
            if task.language == "typescript" and name == "compilation":
                argv = ["tsc", "-p", "tsconfig.json"]
            if task.language == "python":
                argv[0] = "python3"
                if name == "compilation":
                    argv = ["python3", "-B", "-c", "import pathlib; [compile(p.read_text(), str(p), 'exec') for p in pathlib.Path('src').rglob('*.py')]"]
            invocations[name] = check_runner(argv, root, task.language, name) if name != "compilation" else (argv, None)
        with CodeContainer(root, image, docker=docker, readonly=True) as container:
            for name, (argv, marker) in invocations.items():
                result = container.exec_argv(argv, timeout=60)
                checks[name] = require_completion(result, marker) if marker else result
    correct = patch["scope_correct"] and all(check["passed"] for check in checks.values())
    result = {"scope": patch, "criteria": checks, "patch_correct": correct, "image": image}
    (out / "grade.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result
