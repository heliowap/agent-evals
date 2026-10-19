"""Data-only code-task integrity audit. Never import or execute snapshot code."""

from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPOSITORIES = ("click", "httpx", "cobra", "prometheus", "zod", "opencode")
TYPES = {"semanticlocation": 2, "multifileflow_config": 6,
         "negative_boundary": 2, "testcoverage_localization": 2}
FIXTURES = {"correct", "wrong", "omitted", "unsupported", "contradictory", "alternativevalid"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(root=ROOT):
    root = Path(root)
    return tuple(json.loads((root / path).read_text(encoding="utf-8")) for path in (
        "tasks/code/tasks.json", "gold/code/gold.json", "gold/code/navigation.json"))


def safe_path(path):
    require(isinstance(path, str) and bool(path), "path must be nonempty text")
    parsed = PurePosixPath(path)
    require(not parsed.is_absolute() and ".." not in parsed.parts and
            str(parsed) == path and "\\" not in path, f"unsafe path: {path}")
    return path


def span_text(lines, item):
    start, end = item.get("start_line"), item.get("end_line")
    require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
            f"invalid span: {item.get('path')}:{start}-{end}")
    return "\n".join(lines[start - 1:end])


def verify(root=ROOT, *, tasks=None, gold=None, navigation=None):
    """Verify public task/gold artifacts; raise ValueError on invalid inputs.

    Fixture labels are author-reviewed semantic expectations, not machine truth
    judgments. Their shape and mutation patterns are checked, not their prose.
    """
    root = Path(root).resolve()
    loaded = load(root)
    tasks = loaded[0] if tasks is None else tasks
    gold = loaded[1] if gold is None else gold
    navigation = loaded[2] if navigation is None else navigation
    require(isinstance(tasks, list) and len(tasks) == 12, "need twelve tasks")
    expected_ids = [f"C{i:02d}" for i in range(1, 13)]
    require([task.get("id") for task in tasks] == expected_ids, "task IDs/order must be C01-C12")
    require(isinstance(gold, dict) and set(gold) == set(expected_ids), "gold task IDs mismatch")
    require(isinstance(navigation, dict) and set(navigation) == set(expected_ids),
            "navigation task IDs mismatch")
    require(Counter(task.get("snapshot_id") for task in tasks) ==
            Counter({repo: 2 for repo in REPOSITORIES}), "need two tasks per repository")
    require(Counter(item.get("task_type") for item in gold.values()) == Counter(TYPES),
            "task-type counts mismatch")
    runtime = json.loads((root / "contracts/runtime.json").read_text(encoding="utf-8"))
    limits = runtime["suites"]["code"]
    total_units = total_quotes = max_calls = max_characters = 0
    unit_ids = set()
    manifests, sources = {}, {}

    def source(repo, path):
        path = safe_path(path)
        key = (repo, path)
        if key not in sources:
            manifest = manifests[repo]
            require(path in manifest["files"], f"source missing from manifest: {repo}/{path}")
            snapshot = root / "corpus" / repo
            file = snapshot / path
            require(file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(snapshot.resolve()),
                    f"source outside snapshot or missing: {repo}/{path}")
            raw = file.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            require(digest == manifest["files"][path]["sha256"], f"source hash mismatch: {repo}/{path}")
            text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            lines = text.split("\n")
            if text.endswith("\n"):
                lines.pop()
            sources[key] = (digest, lines)
        return sources[key]

    for task in tasks:
        task_id, repo = task["id"], task["snapshot_id"]
        require(set(task) == {"schema_version", "id", "suite", "prompt", "cluster_id", "snapshot_id"},
                f"unexpected public fields: {task_id}")
        require(type(task["schema_version"]) is int and task["schema_version"] == 1 and
                task["suite"] == "code" and task["cluster_id"] == repo, f"bad task schema: {task_id}")
        require(isinstance(task["prompt"], str) and "?" in task["prompt"] and
                "snapshot" in task["prompt"] and any(phrase in task["prompt"] for phrase in
                ("without running code or tests", "do not run code or tests")),
                f"missing question/scope/no-execution condition: {task_id}")
        item = gold[task_id]
        manifest_path = f"corpus-manifests/{repo}.json"
        require(item["manifest"]["path"] == manifest_path, f"manifest path mismatch: {task_id}")
        raw_manifest = (root / manifest_path).read_bytes()
        require(hashlib.sha256(raw_manifest).hexdigest() == item["manifest"]["sha256"],
                f"manifest hash mismatch: {task_id}")
        manifests[repo] = json.loads(raw_manifest)
        require(manifests[repo]["name"] == repo, f"manifest identity mismatch: {task_id}")
        units = item["units"]
        require(isinstance(units, list) and 4 <= len(units) <= 6, f"need 4-6 units: {task_id}")
        require([u["id"] for u in units] == [f"{task_id}.U{i}" for i in range(1, len(units) + 1)],
                f"unit IDs/order mismatch: {task_id}")
        require(any(u.get("essential") is True for u in units), f"no essential units: {task_id}")
        used_paths = set()
        for unit in units:
            require(unit["id"] not in unit_ids, f"duplicate unit: {unit['id']}")
            unit_ids.add(unit["id"])
            require(type(unit.get("essential")) is bool, f"essential flag not boolean: {unit['id']}")
            require("weight" not in unit and isinstance(unit.get("description"), str) and unit["description"],
                    f"bad unit description/weight: {unit['id']}")
            require(isinstance(unit.get("evidence"), list) and unit["evidence"],
                    f"unit has no evidence: {unit['id']}")
            for evidence in unit["evidence"]:
                path = evidence["path"]
                digest, lines = source(repo, path)
                used_paths.add(path)
                require(item["source_hashes"].get(path) == digest, f"gold source hash mismatch: {task_id}/{path}")
                require(evidence.get("hash_reference") == f"source_hashes[{path}]",
                        f"invalid evidence hash reference: {unit['id']}")
                require(isinstance(evidence.get("quote"), str) and evidence["quote"] and
                        evidence["quote"] == span_text(lines, evidence),
                        f"quote mismatch: {unit['id']}:{path}:{evidence.get('start_line')}")
                total_quotes += 1
            total_units += 1
        require(set(item["source_hashes"]) == used_paths, f"unused/missing source hashes: {task_id}")
        for field in ("critical_errors", "acceptable_alternatives"):
            require(isinstance(item.get(field), list) and item[field] and
                    all(isinstance(text, str) and text for text in item[field]), f"missing {field}: {task_id}")
        require(isinstance(item.get("reference_answer"), str) and item["reference_answer"],
                f"missing reference answer: {task_id}")
        if item["task_type"] == "negative_boundary":
            closed = item.get("closed_branch_evidence")
            require(isinstance(closed, list) and closed and set(closed) <= {u["id"] for u in units},
                    f"negative lacks closed-branch references: {task_id}")
        fixtures = item["fixtures"]
        require(isinstance(fixtures, dict) and set(fixtures) == FIXTURES, f"missing fixture kinds: {task_id}")
        ids = [u["id"] for u in units]
        n = len(ids)
        expected = {
            "correct": ["correct_supported"] * n,
            "alternativevalid": ["correct_supported"] * n,
            "wrong": ["incorrect_unsupported"] + ["correct_supported"] * (n - 1),
            "contradictory": ["contradictory_unsupported"] + ["correct_supported"] * (n - 1),
            "omitted": ["correct_supported"] * (n - 1) + ["omitted"],
            "unsupported": ["correct_unsupported"] * n,
        }
        for kind, fixture in fixtures.items():
            require(isinstance(fixture.get("answer"), str) and fixture["answer"],
                    f"empty fixture answer: {task_id}/{kind}")
            require(fixture.get("expected_unit_labels") == expected[kind],
                    f"fixture label expectation mismatch: {task_id}/{kind}")
            expected_evidence = [] if kind == "unsupported" else ids[:-1] if kind == "omitted" else ids
            require(fixture.get("evidence_units") == expected_evidence,
                    f"fixture evidence assignment mismatch: {task_id}/{kind}")
        require(len({fixture["answer"] for fixture in fixtures.values()}) >= 5,
                f"fixture mutations not distinct: {task_id}")
        route = navigation[task_id]
        require(isinstance(route, list) and route, f"empty navigation: {task_id}")
        require(len(route) <= limits["tool_calls"] and len(route) + 1 <= limits["model_steps"],
                f"navigation exceeds tool/step caps: {task_id}")
        characters = 0
        reads = []
        for operation in route:
            tool, path = operation.get("tool"), safe_path(operation.get("path"))
            require(tool in {"grep", "glob", "list", "read"}, f"prohibited navigation tool: {task_id}")
            if tool == "read":
                _, lines = source(repo, path)
                text = span_text(lines, operation)
                # Conservative numbered-text overhead; discovery calls reserve
                # their full frozen result cap rather than guessing grep volume.
                size = len(text) + (operation["end_line"] - operation["start_line"] + 1) * 24
                require(size <= runtime["limits"]["result_characters"], f"read exceeds result cap: {task_id}")
                characters += size
                reads.append(operation)
            else:
                require(path in manifests[repo]["files"] or
                        any(p.startswith(path + "/") for p in manifests[repo]["files"]),
                        f"navigation location missing from manifest: {repo}/{path}")
                require(isinstance(operation.get("intent"), str) and operation["intent"],
                        f"discovery lacks intent: {task_id}")
                characters += runtime["limits"]["result_characters"]
        require(characters <= limits["evidence_characters"], f"navigation exceeds evidence cap: {task_id}")
        for unit in units:
            for evidence in unit["evidence"]:
                require(any(read["path"] == evidence["path"] and
                            read["start_line"] <= evidence["start_line"] <= evidence["end_line"] <= read["end_line"]
                            for read in reads), f"navigation omits evidence: {unit['id']}")
        max_calls = max(max_calls, len(route))
        max_characters = max(max_characters, characters)
    return {"tasks": len(tasks), "repositories": len(manifests), "units": total_units,
            "quotes": total_quotes, "source_files": len(sources), "fixtures": len(tasks) * len(FIXTURES),
            "max_navigation_calls": max_calls, "max_navigation_characters": max_characters}


def main():
    try:
        counts = verify()
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests/codetasks"), pattern="test_*.py")
        require(suite.countTestCases() > 0, "no data-verifier tests discovered")
        result = unittest.TextTestRunner(verbosity=1, stream=sys.stdout).run(suite)
        if not result.wasSuccessful():
            return 1
        print("PASS " + " ".join(f"{key}={value}" for key, value in counts.items()))
        print("PASS data integrity and author-reviewed fixture-label contracts; not semantic truth or human calibration")
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
