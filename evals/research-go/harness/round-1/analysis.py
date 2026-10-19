#!/usr/bin/env python3
"""Reconstruct quality/success latency from sealed saved judgments, never prices.

Analysis seed is the frozen schedule seed + 1 (20261007021015). Bootstrap
intervals are exploratory: six WHOLE task clusters, not twelve independent tasks.
"""
import argparse
import csv
import io
import itertools
import json
import math
from pathlib import Path
import random
import statistics
import sys

from verify import Auditor, AuditError, CONFIGS, TASKS, require

BOOTSTRAP_DRAWS = 10000
COMPLIANCE = ("full_urls", "word_cap", "english", "fetched_two_sources", "source_rules", "tool_rules")


def median(values):
    return statistics.median(values) if values else None


def p90(values):
    return sorted(values)[math.ceil(.9 * len(values))-1] if values else None


def judgment(record, grade):
    """Return a reconstructed row; neither supplied qualified flags nor cost enter it."""
    attempted = not record["status"].startswith("not_run")
    checks = grade["checks"] if grade else []
    counts = {s: sum(c["status"] == s for c in checks)
              for s in ("supported", "contradicted", "missing", "unverifiable")}
    raw = counts["supported"]-counts["contradicted"] if grade else None
    extras = len(grade["unsupported_extras"]) if grade else 0
    critical = len(grade["critical_errors"]) if grade else 0
    grounded = sum(c["citation_status"] == "entailing" for c in checks)
    qualified = bool(grade and record["operational_complete"] and record["status"] == "completed" and
                     not record["errors"] and not record["source_drift"] and 0 <= record["wall_s"] <= 180 and len(checks) == 6 and
                     counts["supported"] == grounded == 6 and grade["uncertainty"]["status"] == "pass" and
                     grade["citations"] and all(c["support"] == "entailing" and c["anchor_compliance"] for c in grade["citations"]) and
                     all(grade["compliance"][k] for k in COMPLIANCE) and critical == extras == 0)
    return {"case_id": record["case_id"], "block_id": record["block_id"], "task_id": record["task_id"],
            "repetition": record["repetition"], "configuration_id": record["configuration_id"],
            "attempted": attempted, "status": record["status"], "completed": record["operational_complete"],
            "graded": grade is not None, "checks": counts, "grounded_checks": grounded,
            "factual_raw": raw, "unsupported_extra_count": extras,
            "extra_penalty": min(2, .5 * extras), "factual_adjusted": max(-6, raw-min(2, .5*extras)) if raw is not None else None,
            "critical_error_count": critical, "qualified": qualified,
            "wall_s": record["wall_s"], "qualified_wall_s": record["wall_s"] if qualified else None,
            "uncertainty": grade["uncertainty"]["status"] if grade else None,
            "citations": {s: sum(c["support"] == s for c in grade["citations"])
                          for s in ("entailing", "missing", "non_entailing")} if grade else None,
            "compliance": {k: grade["compliance"][k] for k in COMPLIANCE} if grade else None,
            "discovery_chain": grade["compliance"]["discovery_chain"] if grade else None}


def summarize(rows):
    qualified = [r for r in rows if r["qualified"]]
    attempted = [r for r in rows if r["attempted"]]
    graded = [r for r in rows if r["graded"]]
    tasks = []
    for task in sorted(TASKS):
        subset = [r for r in rows if r["task_id"] == task]
        scores = [r["factual_adjusted"] for r in subset if r["graded"]]
        tasks.append({"task_id": task, "planned": len(subset), "attempted": sum(r["attempted"] for r in subset),
                      "qualified": sum(r["qualified"] for r in subset),
                      "qualified_rate": sum(r["qualified"] for r in subset)/len(subset) if subset else None,
                      "quality_mean": statistics.mean(scores) if scores else None,
                      "quality_denominator": len(scores)})
    qualified_times = [r["wall_s"] for r in qualified]
    complete_unqualified = [r["wall_s"] for r in rows if r["completed"] and not r["qualified"]]
    failed = [r["wall_s"] for r in attempted if not r["completed"]]
    contradictions = sum(r["checks"]["contradicted"] for r in attempted)
    critical = sum(r["critical_error_count"] for r in attempted)
    eligible = len(rows) == 12 and len(qualified) >= 10 and all(t["qualified"] >= 1 for t in tasks) and contradictions == critical == 0
    task_means = [t["quality_mean"] for t in tasks]
    return {"planned": len(rows), "attempted": len(attempted), "graded": len(graded), "qualified": len(qualified),
            "qualified_rate": len(qualified)/len(rows) if rows else None,
            "completed": sum(r["completed"] for r in rows),
            "completion_rate": sum(r["completed"] for r in rows)/len(rows) if rows else None,
            "errors": sum(not r["completed"] for r in attempted), "timeouts": sum(r["status"] == "timeout" for r in rows),
            "error_rate_attempted": sum(not r["completed"] for r in attempted)/len(attempted) if attempted else None,
            "timeout_rate_attempted": sum(r["status"] == "timeout" for r in attempted)/len(attempted) if attempted else None,
            "contradictions": contradictions, "critical_errors": critical,
            "unsupported_extras": sum(r["unsupported_extra_count"] for r in graded),
            "grounded_checks": sum(r["grounded_checks"] for r in graded), "graded_checks_denominator": 6*len(graded),
            "task_equal_quality": statistics.mean(task_means) if all(x is not None for x in task_means) else None,
            "task_equal_quality_tasks": sum(x is not None for x in task_means), "eligible": eligible,
            "qualified_latency": {"n": len(qualified_times), "median_s": median(qualified_times), "p90_s": p90(qualified_times)},
            "completed_unqualified_latency": {"n": len(complete_unqualified), "median_s": median(complete_unqualified)},
            "failed_latency": {"n": len(failed), "median_s": median(failed)}, "tasks": tasks}


def pair(rows, left, right):
    blocks = {}
    for row in rows:
        if row["configuration_id"] in {left, right}:
            blocks.setdefault(row["block_id"], {})[row["configuration_id"]] = row
    included, exclusions = [], []
    for block_id, block in sorted(blocks.items()):
        a, b = block[left], block[right]
        ids = {"block_id": block_id, "task_id": a["task_id"], "left_case_id": a["case_id"], "right_case_id": b["case_id"]}
        if a["qualified"] and b["qualified"]:
            included.append({**ids, "left_s": a["wall_s"], "right_s": b["wall_s"],
                             "difference_s": a["wall_s"]-b["wall_s"],
                             "ratio": a["wall_s"]/b["wall_s"] if b["wall_s"] > 0 else None})
        else:
            exclusions.append({**ids, "left_status": a["status"], "right_status": b["status"],
                               "left_qualified": a["qualified"], "right_qualified": b["qualified"],
                               "reason": "not_jointly_qualified"})
    def stats(subset):
        return {"n": len(subset), "median_difference_s": median([r["difference_s"] for r in subset]),
                "median_ratio": median([r["ratio"] for r in subset if r["ratio"] is not None]),
                "left_median_s": median([r["left_s"] for r in subset]), "right_median_s": median([r["right_s"] for r in subset])}
    overall = stats(included)
    taskwise = []
    lout = []
    for task in sorted(TASKS):
        subset = [p for p in included if p["task_id"] == task]
        summary = stats(subset)
        diff = summary["median_difference_s"]
        taskwise.append({"task_id": task, **summary,
                         "outcome": None if diff is None else "left_faster" if diff < 0 else "right_faster" if diff > 0 else "tie"})
        lout.append({"excluded_task_id": task, **stats([p for p in included if p["task_id"] != task])})
    coverage = len(included) >= 6 and len({p["task_id"] for p in included}) >= 4
    return {"left": left, "right": right, "jointly_qualified_blocks": len(included),
            "jointly_qualified_tasks": len({p["task_id"] for p in included}), "coverage_sufficient": coverage,
            "conditional_latency": overall, "decision_latency": overall if coverage else None,
            "included": included, "exclusions": exclusions, "taskwise": taskwise, "leave_one_task_out": lout}


def practical_speed(left, right, paired):
    """Direction uses joint-subset medians, with six-block/four-task coverage."""
    a, b = left["qualified_latency"], right["qualified_latency"]
    p = paired["decision_latency"]
    if not p or a["median_s"] is None or b["median_s"] is None or b["median_s"] <= 0:
        return False
    return (a["median_s"] <= .9*b["median_s"] and a["p90_s"] <= 1.1*b["p90_s"] and
            p["right_median_s"] > 0 and p["left_median_s"] <= .9*p["right_median_s"] and
            all(item["left_median_s"] is not None and item["right_median_s"] > 0 and
                item["left_median_s"] < item["right_median_s"] for item in paired["leave_one_task_out"]))


def recommendation(rows, summaries, pairs):
    eligible = [c for c, s in summaries.items() if s["eligible"]]
    # Pareto descriptive frontier only; not a fabricated ordinal ranking.
    frontier = []
    for c, s in summaries.items():
        def dominates(other):
            q, oq = s["qualified"], other["qualified"]
            t, ot = s["qualified_latency"]["median_s"], other["qualified_latency"]["median_s"]
            return t is not None and ot is not None and oq >= q and ot <= t and (oq > q or ot < t)
        if not any(dominates(o) for oc, o in summaries.items() if oc != c):
            frontier.append(c)
    if not eligible:
        return {"decision": "no_decisive_winner", "reason": "no_eligible_configuration", "winner": None,
                "eligible": [], "quality_tier": [], "frontier": frontier}
    highest = max(summaries[c]["qualified"] for c in eligible)
    tier = [c for c in eligible if summaries[c]["qualified"] == highest]
    if len(tier) == 1:
        winner, reason = tier[0], "highest_qualified_count_among_eligible"
    else:
        winners = []
        for c in tier:
            beats = []
            for other in tier:
                if c != other:
                    p = pair(rows, c, other)
                    beats.append(practical_speed(summaries[c], summaries[other], p))
            if all(beats):
                winners.append(c)
        winner = winners[0] if len(winners) == 1 else None
        reason = "same_quality_tier_practical_speed" if winner else "same_quality_tier_no_robust_speed_advantage"
    return {"decision": "winner" if winner else "no_decisive_winner", "reason": reason, "winner": winner,
            "eligible": eligible, "quality_tier": tier, "frontier": frontier}


def bootstrap(rows, pairs, seed, draws=BOOTSTRAP_DRAWS):
    """One shared draw selects six tasks with replacement, retaining all 12 cells/task."""
    tasks = sorted(TASKS)
    clusters = {t: [r for r in rows if r["task_id"] == t] for t in tasks}
    require(all(len(clusters[t]) == 12 and {r["configuration_id"] for r in clusters[t]} == set(CONFIGS)
                for t in tasks), "analysis: bootstrap requires all six whole task clusters (all configurations/two repetitions)")
    rng = random.Random(seed)
    config_samples = {c: {"quality": [], "qualified_rate": []} for c in CONFIGS}
    pair_samples = {f"{p['left']}|{p['right']}": [] for p in pairs}
    # Precompute each whole task's equal-weight quality/rate. Repetitions are never resampled separately.
    task_stats = {}
    for task, cluster in clusters.items():
        task_stats[task] = {}
        for c in CONFIGS:
            subset = [r for r in cluster if r["configuration_id"] == c]
            scores = [r["factual_adjusted"] for r in subset if r["graded"]]
            task_stats[task][c] = (statistics.mean(scores) if scores else None, sum(r["qualified"] for r in subset)/2)
    pair_clusters = {f"{p['left']}|{p['right']}": {t: [r for r in p["included"] if r["task_id"] == t] for t in tasks} for p in pairs}
    draw_hash = __import__("hashlib").sha256()
    for _ in range(draws):
        selected = [rng.choice(tasks) for _ in range(6)]
        draw_hash.update((",".join(selected)+"\n").encode())
        for c in CONFIGS:
            values = [task_stats[t][c] for t in selected]
            config_samples[c]["qualified_rate"].append(sum(v[1] for v in values)/6)
            if all(v[0] is not None for v in values):
                config_samples[c]["quality"].append(sum(v[0] for v in values)/6)
        for key, tc in pair_clusters.items():
            subset = [p for t in selected for p in tc[t]]
            if subset:
                right = median([p["right_s"] for p in subset])
                if right and right > 0:
                    pair_samples[key].append(median([p["left_s"] for p in subset])/right)
    def interval(values):
        ordered = sorted(values)
        return {"n_valid_draws": len(values), "low": ordered[max(0, math.ceil(.025*len(values))-1)] if values else None,
                "high": ordered[max(0, math.ceil(.975*len(values))-1)] if values else None}
    return {"seed": seed, "draws": draws, "cluster_count": 6, "cluster_unit": "whole_task",
            "cells_per_cluster": 12, "shared_draws_all_configurations": True, "exploratory": True,
            "draws_sha256": draw_hash.hexdigest(),
            "configurations": {c: {k: interval(v) for k, v in samples.items()} for c, samples in config_samples.items()},
            "paired_joint_median_ratio": {k: interval(v) if next(p for p in pairs if f"{p['left']}|{p['right']}" == k)["coverage_sufficient"]
                                          else {"n_valid_draws": len(v), "low": None, "high": None}
                                          for k, v in pair_samples.items()}}


def analyze_saved(a):
    """Consumes a validated graded Auditor; no reads of prior experiments."""
    require(a.index["study_status"] == "completed", "analysis: incomplete/access-blocked studies are not comparisons")
    grades = {a.mapping[blind]: grade for blind, grade in a.effective.items()}
    rows = [judgment(r, grades.get(r["case_id"])) for r in a.records]
    summaries = {c: summarize([r for r in rows if r["configuration_id"] == c]) for c in CONFIGS}
    pairs = [pair(rows, a, b) for a, b in itertools.combinations(CONFIGS, 2)]
    return {"version": 1, "study_status": "completed", "planned_cases": 72,
            "quality_score": "supported +1; contradicted -1; missing/unverifiable 0; extras .5 capped 2; floor -6",
            "latency_definition": "supervised worker launch through exit; qualified successes only",
            "p90_definition": "nearest rank ceil(.9*n)", "task_clusters": 6, "rows": rows,
            "configurations": summaries, "pairs": pairs,
            "bootstrap": bootstrap(rows, pairs, a.protocol["statistics_seed"]),
            "recommendation": recommendation(rows, summaries, pairs)}


def analyze(root):
    a = Auditor(root).frozen().collected()
    if a.index["study_status"] == "access_blocked":
        return {"study_status": "access_blocked", "attempted_cases": 1, "not_run_access_gate": 71,
                "recommendation": "no_decisive_winner", "qualified_latency": None}
    require(a.index["study_status"] == "completed", "analysis: incomplete study; preserve case rows, finish missing collection stage")
    return analyze_saved(a.blind().grades().graded())


def tables(result):
    """Inspectable CSV data, not hidden derived rankings."""
    if result["study_status"] != "completed":
        return {}
    task_rows = [{"configuration_id": c, **t} for c, s in result["configurations"].items() for t in s["tasks"]]
    pair_rows = [{"left": p["left"], "right": p["right"], **r} for p in result["pairs"] for r in p["included"]]
    excluded = [{"left": p["left"], "right": p["right"], **r} for p in result["pairs"] for r in p["exclusions"]]
    leave_out = [{"left": p["left"], "right": p["right"], **r} for p in result["pairs"] for r in p["leave_one_task_out"]]
    output = {}
    for name, records in (("tasks.csv", task_rows), ("paired.csv", pair_rows), ("paired-exclusions.csv", excluded),
                          ("leave-one-task-out.csv", leave_out)):
        stream = io.StringIO()
        fields = list(dict.fromkeys(k for r in records for k in r))
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
        output[name] = stream.getvalue()
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline analysis from sealed saved judgments; never calls models or uses price.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent, help="saved artifact root")
    args = parser.parse_args(argv)
    try:
        result = analyze(args.root)
        directory = args.root.resolve()/"analysis"
        require(not directory.is_symlink(), "analysis: output directory cannot be a symlink")
        directory.mkdir(exist_ok=True)
        name = "results.json" if result["study_status"] == "completed" else "block-report.json"
        destination = directory/name
        require(not destination.is_symlink(), "analysis: output cannot be a symlink")
        destination.write_text(json.dumps(result, indent=2) + "\n")
        for name, content in tables(result).items():
            destination = directory/name
            require(not destination.is_symlink(), "analysis: table output cannot be a symlink")
            destination.write_text(content)
    except (AuditError, KeyError, TypeError, OSError) as exc:
        print(f"ANALYSIS FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {directory} ({result['study_status']}); no price-based recommendation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
