"""Revalidate and import preflight sessions from the previous frozen runner."""

import json
import subprocess
from pathlib import Path

from benchmark import ROOT, atomic_new, digest, frozen_manifest, validate_export
from prompts import render_prompt


def export_session(session):
    run = subprocess.run(["opencode", "session", "export", "--standalone", session],
                         capture_output=True, text=True, check=True, timeout=45)
    return json.loads(run.stdout)


def import_preflight(source, target, cases, manifest, export=export_session):
    source_manifest_path = source / "manifest.json"
    old = json.loads(source_manifest_path.read_text())
    if ({key: value for key, value in old.items() if key != "inputs"} !=
            {key: value for key, value in manifest.items() if key != "inputs"} or
            any(manifest["inputs"].get(key) != value for key, value in old["inputs"].items()
                if key != "benchmark.py")):
        raise ValueError("source lineage differs in prompt, rubric, route, matrix or policy")
    if (target / "migration.json").exists() or any(
            any((target / folder).glob("*.json")) for folder in ("attempts", "results")):
        raise FileExistsError("File exists: migration target is not empty")

    cells = {cell["id"]: cell for cell in manifest["cells"]}
    case_map = {case["id"]: case for case in cases}
    source_results = {path.stem: json.loads(path.read_text())
                      for path in (source / "results").glob("*.json")}
    attempts = []
    results = {}
    seen_sessions = set()
    source_files = sorted((source / "attempts").glob("*.json"))
    if not source_files or set(source_results) - set(cells):
        raise ValueError("source attempts or results are missing or unexpected")
    source_hash = digest(source_manifest_path.read_bytes())
    for path in source_files:
        previous = json.loads(path.read_text())
        cell = cells.get(previous.get("cell_id"))
        if (cell is None or path.name != f'{cell["id"]}-{previous.get("number")}.json' or
                previous.get("model") != cell["model"] or
                previous.get("prompt_sha256") != manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'] or
                not previous.get("session") or previous["session"] in seen_sessions):
            raise ValueError(f"source attempt identity mismatch: {path.name}")
        seen_sessions.add(previous["session"])
        prompt = render_prompt(case_map[cell["case"]], cell["axis"])
        verified = validate_export(export(previous["session"]), prompt, cell["model"])
        if verified["session"] != previous["session"] or verified["cost_usd"] != previous.get("cost_usd"):
            raise ValueError(f"source session/cost mismatch: {path.name}")
        if previous["status"] == "succeeded":
            original = source_results.get(cell["id"])
            if original is None or original.get("session") != verified["session"] or original.get("answer") != verified["answer"]:
                raise ValueError(f"source valid result mismatch: {path.name}")
        source_fields = {"source_attempt": str(path.relative_to(source)),
                         "source_manifest_sha256": source_hash,
                         "source_original_status": previous["status"],
                         "source_error": previous.get("error")}
        if cell["id"] in results:
            record = {**previous, **source_fields, "status": "excluded",
                      "error": "Surplus independent session for an already filled cell"}
        else:
            record = {**previous, **source_fields, **verified, "status": "succeeded",
                      "error": None, "case": cell["case"], "axis": cell["axis"],
                      "repeat": cell["repeat"], "prompt": prompt}
            results[cell["id"]] = record
        attempts.append((path.name, record))
    if set(source_results) - set(results):
        raise ValueError("source result without a revalidated attempt")

    for name, record in attempts:
        atomic_new(target / "attempts" / name, record)
    for cell_id, record in results.items():
        atomic_new(target / "results" / f"{cell_id}.json", record)
    summary = {"source_manifest_sha256": source_hash, "promoted": sorted(results),
               "duplicates": [record["session"] for _, record in attempts if record["status"] == "excluded"],
               "sessions_revalidated": len(attempts)}
    atomic_new(target / "migration.json", summary)
    return summary


if __name__ == "__main__":
    frozen_cases, frozen = frozen_manifest(ROOT)
    print(import_preflight(ROOT.parent, ROOT, frozen_cases, frozen))
