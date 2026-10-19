"""Concise English Markdown tables and atomic, hash-checked reproducible artifacts."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

from grading.common import digest, load, save, signed, verify_signed
from .statistics import analyze


def _number(value):
    return "unknown" if value is None else f"{value:.3f}"


def render_report(metrics):
    lines = ["# Research evaluation results", "", f"**{metrics['study_status']}**", "",
             f"Scheduled: {metrics['n_scheduled']}; attempted: {metrics['n_attempted']}; unrun: {metrics['n_unrun']}.",
             "Scheduled rates include unrun as no outcome credit; semantic means use completed answers only.", ""]
    if metrics["incomplete"]:
        lines.extend(["**INCOMPLETE STUDY — NO QUALIFIED WINNER in either suite.**", ""])
        lines.extend(["### Execution / accounting reasons", "", metrics["study_state"]["provenance"], ""])
        for reason in metrics["study_stop_reasons"]:
            detail = ("; recorded stop: " + json.dumps(reason["detail"], sort_keys=True, ensure_ascii=False)
                      if reason["detail"] is not None else "")
            lines.append(f"- **{reason['reason']}** — {reason['source']}; "
                         f"{len(reason['trial_ids'])} affected scheduled IDs{detail}.")
        lines.extend(["", "All scheduled trials being attempted does not clear an execution-level stop.", ""])
    review = metrics["review_accounting"]
    lines.extend([f"Same-backend AI review (not human calibration): planned sample {review['planned_sample']}; "
                  f"semantic reviewed {review['semantic_reviewed']}; operational reviewed {review['operational_reviewed']}; "
                  f"unresolved unrun {len(review['unresolved_unrun'])}; disagreements {len(review['disagreements'])}.", ""])
    for suite, data in metrics["suites"].items():
        lines.extend([f"## {suite.capitalize()} suite", "", data["recommendation"]["status"], "",
                      "Preferred configuration: " + (data["recommendation"]["preferred"] or "none") + ".", "",
                      "| Configuration | Scheduled / attempted / unrun | Complete n / rate | Success n / rate | Semantic n: correct / supported / grounded | Effective coverage | Critical instances / evaluable n | Success median / p90 (n) | Complete median / p90 (n) |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for config, s in data["configurations"].items():
            success, complete = s["success_wall_seconds"], s["complete_wall_seconds"]
            lines.append(f"| {config} | {s['n_scheduled']} / {s['n_attempted']} / {s['n_unrun']} | "
                         f"{s['n_completed']} / {_number(s['completion_scheduled'])} | {s['n_success']} / {_number(s['success_scheduled'])} | "
                         f"{s['n_semantic']}: {_number(s['mean_correctness_completed'])} / {_number(s['mean_supported_fraction_completed'])} / {_number(s['mean_grounded_coverage_completed'])} | "
                         f"{_number(s['effective_coverage_task_macro_scheduled'])} | {s['n_critical_instances']} / {s['n_critical_evaluable']} | "
                         f"{_number(success['median'])} / {_number(success['p90'])} ({success['n']}) | "
                         f"{_number(complete['median'])} / {_number(complete['p90'])} ({complete['n']}) |")
        bootstrap = data["bootstrap"]
        lines.extend(["", f"Whole-cluster bootstrap: {bootstrap['draws']} draws, seed {bootstrap['seed']}, "
                      f"{bootstrap['n_independent_clusters']} independent clusters. All repeats/configurations retained.", "",
                      "### Paired effective-coverage contrasts", "",
                      "Descriptive, uncorrected 95% intervals. No formal superiority or post-selection equivalence inference.", "",
                      "| Left − right | Difference | 95% interval | Predeclared within-family effort pair |",
                      "|---|---:|---:|---|"])
        for pair in bootstrap["pairwise_contrasts"]:
            low, high = pair["descriptive_95_percent_interval"]
            lines.append(f"| {pair['left']} − {pair['right']} | {_number(pair['difference_left_minus_right'])} | "
                         f"[{_number(low)}, {_number(high)}] | {'yes' if pair['within_family_effort_contrast'] else 'no'} |")
        for title, key in (("Task slices", "task_slices"), ("Repository / project-family slices", "repository_or_project_slices")):
            lines.extend(["", "### " + title, "", "| Slice | Configuration | Scheduled / attempted | Complete / success | Effective coverage | Critical instances |",
                          "|---|---|---:|---:|---:|---:|"])
            for name, configs in data[key].items():
                for config, s in configs.items():
                    lines.append(f"| {name} | {config} | {s['n_scheduled']} / {s['n_attempted']} | "
                                 f"{s['n_completed']} / {s['n_success']} | {_number(s['effective_coverage_task_macro_scheduled'])} | {s['n_critical_instances']} |")
        lines.extend(["", "Recommendation rule: ≥95% completion, ≥85% practical success, zero observed critical errors; "
                      "within 0.05 of best effective coverage, then lowest success median. A utility judgment, not a statistical winner.",
                      "Small-cluster uncertainty can permit material quality loss; proximity is not evidence of equivalence.", ""])
    lines.extend(["## Limitations", ""] + ["- " + item for item in metrics["limitations"]] + ["",
                  "Saved JSON contains attempted-only rates, missing-timing counts, operational statuses, resource observations and all slice statistics."])
    return "\n".join(lines) + "\n"


def _save_report(path, text):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(text.encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # report originals, like JSON inputs, cannot be replaced
    finally:
        os.unlink(temporary)


def write_artifacts(directory, records, sealed_grades, schedule, tasks, *, draws=10000, seed=None):
    """Write into a caller-owned output directory; never choose a parent report path."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    metrics = analyze(records, sealed_grades, schedule, tasks, draws=draws, seed=seed)
    inputs = signed({"records": records, "sealed_grades": sealed_grades, "schedule": schedule, "tasks": tasks})
    saved_metrics = signed(metrics)
    report = render_report(metrics)
    manifest = signed({"schema_version": 1, "stage": "final", "inputs_hash": inputs["sha256"],
                       "metrics_hash": saved_metrics["sha256"],
                       "report_sha256": hashlib.sha256(report.encode()).hexdigest(),
                       "draws": draws, "seed": metrics["seed"]})
    save(directory / "inputs.json", inputs, immutable=True)
    save(directory / "metrics.json", saved_metrics, immutable=True)
    _save_report(directory / "report.md", report)
    save(directory / "final.json", manifest, immutable=True)  # publication marker last
    return manifest


def audit_artifacts(path):
    path = Path(path)
    directory = path if path.is_dir() else path.parent
    final = load(directory / "final.json")
    inputs = load(directory / "inputs.json")
    metrics = load(directory / "metrics.json")
    report = (directory / "report.md").read_text(encoding="utf-8")
    for document in (final, inputs, metrics):
        verify_signed(document)
    if (final["inputs_hash"] != inputs["sha256"] or final["metrics_hash"] != metrics["sha256"]
            or final["report_sha256"] != hashlib.sha256(report.encode()).hexdigest()):
        raise ValueError("saved data/report hash breach")
    reproduced = analyze(inputs["records"], inputs["sealed_grades"], inputs["schedule"], inputs["tasks"],
                         draws=final["draws"], seed=final["seed"])
    if signed(reproduced) != metrics or render_report(reproduced) != report:
        raise ValueError("reproduced tables/data differ from saved artifacts")
    return final
