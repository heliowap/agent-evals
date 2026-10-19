"""Copy prior results only after verifying immutable lineage and every valid session."""

import fcntl
import json
import os
from pathlib import Path

from benchmark import (ROOT, atomic_new, digest, frozen_manifest, pending_cells,
                       reconciled_cost, validate_export)
from import_preflight import export_session
from prompts import render_prompt


def migrate_revision(source, target, cases, manifest, export=export_session):
    with (source / ".run.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("source runner is still running") from exc
        try:
            if list((source / "attempts").glob("*.started")):
                raise ValueError("source has an in-flight or interrupted attempt")
            old_path = source / "manifest.json"
            old = json.loads(old_path.read_text())
            if (any(digest((source / name).read_bytes()) != value
                    for name, value in old["inputs"].items()) or
                    {key: value for key, value in old.items() if key != "inputs"} !=
                    {key: value for key, value in manifest.items() if key != "inputs"} or
                    any(manifest["inputs"].get(name) != value for name, value in old["inputs"].items()
                        if name != "benchmark.py")):
                raise ValueError("source lineage differs in prompt, rubric, route, matrix or policy")
            if json.loads((target / "cost-resolution.json").read_text()).get("source_manifest_sha256") != digest(old_path.read_bytes()):
                raise ValueError("cost resolution source manifest differs")
            if ((target / "migration.json").exists() or
                    any(any((target / folder).glob("*.json")) for folder in ("attempts", "results"))):
                raise FileExistsError("migration target is not empty")
            pending_cells(old, source)
            cells = {cell["id"]: cell for cell in manifest["cells"]}
            cases_by_id = {case["id"]: case for case in cases}
            attempts = sorted((source / "attempts").glob("*.json"))
            results = sorted((source / "results").glob("*.json"))
            result_data = {path.stem: json.loads(path.read_text()) for path in results}
            seen_sessions = set()
            for path in attempts:
                record = json.loads(path.read_text())
                cell = cells.get(record.get("cell_id"))
                if (cell is None or path.name != f'{cell["id"]}-{record.get("number")}.json' or
                        record.get("model") != cell["model"] or
                        record.get("prompt_sha256") != manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}']):
                    raise ValueError(f"source attempt mismatch: {path.name}")
                session = record.get("session")
                if session:
                    if session in seen_sessions:
                        raise ValueError(f"reused session: {session}")
                    seen_sessions.add(session)
                if record["model"].startswith("openrouter/") and record.get("cost_usd") is None:
                    reconciled_cost(target, path, record)
                if record.get("status") == "succeeded" and result_data.get(cell["id"]) != record:
                    raise ValueError(f"valid result does not match attempt: {path.name}")
            for path in results:
                record = result_data[path.stem]
                cell = cells[record["cell_id"]]
                prompt = render_prompt(cases_by_id[cell["case"]], cell["axis"])
                verified = validate_export(export(record["session"]), prompt, cell["model"])
                if (record.get("prompt") != prompt or
                        any(record.get(key) != verified[key] for key in
                            ("session", "answer", "used_model", "tokens", "cost_usd"))):
                    raise ValueError(f"source response differs from export: {path.name}")

            for folder, files in (("attempts", attempts), ("results", results)):
                (target / folder).mkdir(parents=True, exist_ok=True)
                for path in files:
                    with (target / folder / path.name).open("xb") as copied:
                        copied.write(path.read_bytes())
                        copied.flush()
                        os.fsync(copied.fileno())
            summary = {"source_manifest_sha256": digest(old_path.read_bytes()),
                       "valid_results": len(results), "attempts": len(attempts),
                       "source_result_sha256": {p.name: digest(p.read_bytes()) for p in results},
                       "source_attempt_sha256": {p.name: digest(p.read_bytes()) for p in attempts}}
            atomic_new(target / "migration.json", summary)
            return summary
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    frozen_cases, frozen = frozen_manifest(ROOT)
    report = migrate_revision(ROOT.parent / "revision-1", ROOT, frozen_cases, frozen)
    print(f'Migrated {report["valid_results"]} valid results and {report["attempts"]} attempts')
