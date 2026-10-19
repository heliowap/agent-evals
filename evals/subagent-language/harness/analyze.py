"""Audit a completed pilot without altering frozen sources or original results."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics

from cases import exact
import telemetry


def describe(values):
    return {"n": len(values), "sum": sum(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


def metric(row, key):
    return row[key] if key in ("wall_s", "response_count") else row["usage"][key]


def analyze(base, skip_docs_hash=False):
    frozen = json.loads((base / "freeze.json").read_text())
    for name, expected in frozen["source_sha256"].items():
        # Published copy: README.md was anonymized (home path replaced), so its hash no longer matches.
        if skip_docs_hash and name.endswith(".md"):
            continue
        if hashlib.sha256((base / "frozen-source" / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen source changed: {name}")
    rows = []
    for planned in frozen["schedule"]:
        trial = base / planned["id"]
        row = json.loads((trial / "result.json").read_text())
        if row["status"] != "completed":
            raise ValueError(f"This audit requires a completed run: {planned['id']}")
        observed = telemetry.collect(sorted((trial / "rollouts").glob("*.jsonl")), row["session_id"],
                                     frozen["model"], frozen["effort"], row["cli_usage_raw"])
        if not observed["measurement_valid"] or observed["usage"] != row["usage"]:
            raise ValueError(f"Native telemetry not reconciled: {planned['id']}")
        case = frozen["cases"][row["case"]]
        expected = copy.deepcopy(case["expected"])
        if row["case"] == "fornecedor":
            expected["elegiveis"] = ["Alfa", "Épsilon", "Gama"]
        actual = json.loads((trial / "work/answer.json").read_text())
        checks = {"answer_exact": exact(actual, expected),
                  "inputs_intact": all((trial / "work" / name).read_text() == content
                                       for name, content in case["files"].items()),
                  "report_present": bool((trial / "work/report.md").read_text().strip())}
        decisions_correct = copy.deepcopy(actual)
        if row["case"] == "fornecedor" and isinstance(decisions_correct, dict):
            names = decisions_correct.get("elegiveis")
            if isinstance(names, list) and len(names) == 3 and set(names) == set(expected["elegiveis"]):
                decisions_correct["elegiveis"] = expected["elegiveis"]
        row["audited_grade"] = {"checks": checks, "automatic_pass": all(checks.values()),
                                "decisions_correct_ignoring_supplier_order": exact(decisions_correct, expected),
                                "explanation_review": "pending"}
        rows.append(row)
    metrics = ("total_tokens", "input_tokens", "output_tokens", "cached_input_tokens", "wall_s", "response_count")
    conditions = {}
    for variant in ("default", "pt", "en"):
        group = [r for r in rows if r["variant"] == variant]
        conditions[variant] = {"n": len(group), "original_pass": sum(r["grade"]["automatic_pass"] for r in group),
                               "corrected_pass": sum(r["audited_grade"]["automatic_pass"] for r in group),
                               "decisions_correct_ignoring_supplier_order": sum(r["audited_grade"]["decisions_correct_ignoring_supplier_order"] for r in group),
                               "protocol_pass": sum(r["protocol_pass"] for r in group),
                               "metrics": {k: describe([metric(r, k) for r in group]) for k in metrics},
                               "subagent_output_tokens": sum(r["subagent_usage"]["output_tokens"] for r in group),
                               "communication_observability": dict(sum((Counter(r["communication_observability"]) for r in group), Counter()))}
    comparisons = []
    for baseline in ("default", "pt"):
        for case in (None, *frozen["cases"]):
            group = [r for r in rows if r["variant"] == baseline and (case is None or r["case"] == case)]
            paired = [(a, next(b for b in rows if b["variant"] == "en" and (b["case"], b["rep"]) == (a["case"], a["rep"]))) for a in group]
            comparison = {"baseline": baseline, "case": case or "all", "n_pairs": len(paired), "metrics": {}}
            for k in metrics:
                deltas = [100 * (metric(b, k) / metric(a, k) - 1) for a, b in paired]
                comparison["metrics"][k] = {"ratio_of_sums_pct": 100 * (sum(metric(b, k) for a, b in paired) / sum(metric(a, k) for a, b in paired) - 1),
                                            "paired_delta_pct": describe(deltas), "english_lower_pairs": sum(v < 0 for v in deltas)}
            comparisons.append(comparison)
    return {"source_run": str(base), "model": frozen["model"], "effort": frozen["effort"],
            "frozen_sources_verified": True, "native_telemetry_reconciled_trials": len(rows),
            "quality_correction": {"reason": "Portuguese alphabetical order places Épsilon before Gama.",
                                   "old_expected": ["Alfa", "Gama", "Épsilon"], "corrected_expected": ["Alfa", "Épsilon", "Gama"],
                                   "changed_trials": [r["id"] for r in rows if r["grade"]["automatic_pass"] != r["audited_grade"]["automatic_pass"]]},
            "verdict": "inconclusive_for_adoption", "conditions": conditions, "comparisons": comparisons,
            "quality_failures": [{"id": r["id"], "case": r["case"], "variant": r["variant"], "grade": r["audited_grade"]}
                                 for r in rows if not r["audited_grade"]["automatic_pass"]],
            "limitations": ["Four synthetic tasks, five repetitions each; repetitions are not independent new tasks.",
                            "Explanations have not received the prescribed blind human review.",
                            "Encrypted inter-agent messages prevent complete language-compliance assessment.",
                            "Service load and cache state were not controlled; no latency profile isolates the bottleneck.",
                            "Raw token totals are not a monetary cost estimate."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-docs-hash", action="store_true",
                        help="skip the hash check of frozen *.md files (needed for the anonymized published copy)")
    args = parser.parse_args()
    result = analyze(args.run, args.skip_docs_hash)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Audited {result['native_telemetry_reconciled_trials']} trials: {args.out}")
