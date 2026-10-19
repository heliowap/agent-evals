"""Whole-cluster paired bootstrap, explicit denominators, provisional utility rule."""

import itertools
import math
import random
from collections import Counter, defaultdict

from grading.common import digest, indexed, record_index, is_attempted, is_completed, wall_seconds
from grading.sealing import unblind
from grading.schema import AUXILIARY


MANDATORY_STOP_STATUSES = frozenset({
    "auth_error", "quota_error", "protocol_error", "search_outage", "harness_error",
    "supervisor_cleanup_failure", "credential_hygiene_failure",
})


def _study_state(record_map, rows, review_accounting):
    """Execution-level stops remain authoritative even after the last attempt."""
    reasons = {}

    def add(source, reason, trial_ids, detail=None):
        key = digest([source, reason, detail])
        entry = reasons.setdefault(key, {"source": source, "reason": reason,
                                         "detail": detail, "trial_ids": []})
        entry["trial_ids"].extend(trial_ids)

    for identity, record in sorted(record_map.items()):
        if "study_incomplete" in record and type(record["study_incomplete"]) is not bool:
            raise ValueError("record study_incomplete must be boolean")
        if record.get("study_incomplete") is True:
            add("record.study_incomplete", "execution index marked incomplete", [identity])
        stop = record.get("study_stop")
        if stop is not None:
            if not isinstance(stop, dict):
                raise ValueError("record study_stop must be a dictionary or null")
            label = stop.get("reason", stop.get("status"))
            add("record.study_stop", label if isinstance(label, str) and label else "execution stop recorded",
                [identity], stop)
        status = record.get("status", record.get("terminal_status"))
        if status in MANDATORY_STOP_STATUSES:
            add("record.terminal_status", status, [identity])
    unrun = sorted(row["trial_id"] for row in rows if not row["attempted"])
    if unrun:
        add("schedule/record accounting", "scheduled trials remain unrun", unrun)
    unresolved = review_accounting["unresolved_unrun"]
    if unresolved:
        add("sealed review accounting", "sampled unrun review obligations remain unresolved", [],
            {"blind_ids": unresolved})
    ordered = sorted(reasons.values(), key=lambda r: (r["source"], r["reason"], digest(r["detail"])))
    for reason in ordered:
        reason["trial_ids"] = sorted(set(reason["trial_ids"]))
    return {"incomplete": bool(ordered),
            "provenance": "Hash-verified execution records (normalized execution index state and mandatory terminal statuses), scheduled attempt accounting, and sealed review accounting.",
            "rule": "Any true study_incomplete, non-null study_stop, mandatory terminal status, unrun trial, or unresolved unrun review prevents a qualified winner in either suite, even if all trials were attempted.",
            "mandatory_stop_statuses": sorted(MANDATORY_STOP_STATUSES),
            "stop_reasons": ordered}


def quantile(values, probability):
    if not values:
        return None
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    low = math.floor(location)
    high = math.ceil(location)
    return ordered[low] + (ordered[high] - ordered[low]) * (location - low)


def _mean(values):
    return sum(values) / len(values) if values else None


def _latency(rows, predicate, field="wall_seconds"):
    eligible = [r for r in rows if predicate(r)]
    values = [r[field] for r in eligible if r[field] is not None]
    return {"n": len(values), "missing": len(eligible) - len(values),
            "median": quantile(values, .5), "p90": quantile(values, .9)}


def _task_macro(rows, *, attempted_only=False):
    tasks = defaultdict(list)
    for row in rows:
        if not attempted_only or row["attempted"]:
            tasks[row["task_id"]].append(row["metrics"]["effective_coverage"])
    return _mean([_mean(values) for values in tasks.values()])


def _summary(rows):
    scheduled = len(rows)
    attempted = sum(r["attempted"] for r in rows)
    completed = sum(r["completed"] for r in rows)
    successes = sum(r["metrics"]["practical_success"] for r in rows)
    semantic = [r["metrics"] for r in rows if r["completed"]]
    resource_names = sorted({key for r in rows for key in r["resources"]})
    resources = {}
    for key in resource_names:
        values = [r["resources"].get(key) for r in rows if r["attempted"]]
        known = [v for v in values if type(v) in (int, float) and math.isfinite(v)]
        resources[key] = {"observed_total": sum(known) if known else None,
                          "n_observed": len(known), "n_missing": attempted - len(known)}
    return {"n_scheduled": scheduled, "n_attempted": attempted, "n_unrun": scheduled - attempted,
            "n_completed": completed, "n_semantic": len(semantic),
            "completion_scheduled": completed / scheduled,
            "completion_attempted": completed / attempted if attempted else None,
            "n_success": successes, "success_scheduled": successes / scheduled,
            "success_attempted": successes / attempted if attempted else None,
            "mean_correctness_completed": _mean([m["correctness"] for m in semantic]),
            "mean_supported_fraction_completed": _mean([m["supported_fraction"] for m in semantic]),
            "mean_grounded_coverage_completed": _mean([m["grounded_coverage"] for m in semantic]),
            "effective_coverage_task_macro_scheduled": _task_macro(rows),
            "effective_coverage_task_macro_attempted": _task_macro(rows, attempted_only=True),
            "n_critical_instances": sum(m["critical_errors"] for m in semantic),
            "n_answers_with_critical": sum(bool(m["critical_errors"]) for m in semantic),
            "n_critical_evaluable": len(semantic),
            "complete_wall_seconds": _latency(rows, lambda r: r["completed"]),
            "success_wall_seconds": _latency(rows, lambda r: r["metrics"]["practical_success"]),
            "first_action_seconds": _latency(rows, lambda r: r["attempted"], "first_action_seconds"),
            "first_final_answer_seconds": _latency(rows, lambda r: r["completed"], "first_final_answer_seconds"),
            "request_intervals_seconds": _latency(rows, lambda r: r["attempted"], "request_seconds"),
            "tool_intervals_seconds": _latency(rows, lambda r: r["attempted"], "tool_seconds"),
            "resources": resources,
            "auxiliary": {key: {"n_observed": sum(r["auxiliary"].get(key) is not None for r in rows if r["completed"]),
                                "n_missing": sum(r["auxiliary"].get(key) is None for r in rows if r["completed"]),
                                "observations": [{"trial_id": r["trial_id"], "value": r["auxiliary"][key]}
                                                 for r in rows if r["completed"] and r["auxiliary"].get(key) is not None]}
                          for key in AUXILIARY},
            "statuses": dict(sorted(Counter(r["status"] for r in rows).items()))}


def _bootstrap(rows, configurations, seed, draws):
    """Resample independent clusters, keeping every task/config/repeat within each."""
    cluster_tasks = defaultdict(set)
    task_values = defaultdict(list)
    for row in rows:
        cluster_tasks[row["cluster_id"]].add(row["task_id"])
        task_values[(row["task_id"], row["configuration_id"])].append(row["metrics"]["effective_coverage"])
    clusters = sorted(cluster_tasks)
    if not clusters:
        raise ValueError("suite has no clusters")
    cluster_sums = {}
    for cluster in clusters:
        for config in configurations:
            cluster_sums[(cluster, config)] = sum(_mean(task_values[(task, config)])
                                                  for task in sorted(cluster_tasks[cluster]))
    rng = random.Random(seed)
    samples = {config: [] for config in configurations}
    for _ in range(draws):
        selected = [rng.choice(clusters) for _ in clusters]
        denominator = sum(len(cluster_tasks[c]) for c in selected)
        for config in configurations:
            samples[config].append(sum(cluster_sums[(cluster, config)] for cluster in selected) / denominator)
    point = {config: _task_macro([r for r in rows if r["configuration_id"] == config]) for config in configurations}
    pairs = []
    for left, right in itertools.combinations(configurations, 2):
        differences = [a - b for a, b in zip(samples[left], samples[right])]
        pairs.append({"left": left, "right": right, "difference_left_minus_right": point[left] - point[right],
                      "descriptive_95_percent_interval": [quantile(differences, .025), quantile(differences, .975)],
                      "within_family_effort_contrast": left.rsplit("-", 1)[0] == right.rsplit("-", 1)[0]})
    return {"draws": draws, "seed": seed, "n_independent_clusters": len(clusters), "clusters": clusters,
            "unit": "whole project/evidence family (web) or repository (code); all tasks/configurations/repeats retained",
            "coverage_intervals": {config: [quantile(samples[config], .025), quantile(samples[config], .975)]
                                   for config in configurations},
            "pairwise_contrasts": pairs,
            "within_family_effort_contrasts": [p for p in pairs if p["within_family_effort_contrast"]],
            "interpretation": "Descriptive uncorrected intervals; no formal superiority or post-selection equivalence claim."}


def _recommend(summaries, incomplete):
    rule = {"minimum_completion": .95, "minimum_success": .85,
            "maximum_observed_critical": 0, "coverage_margin": .05}
    if incomplete:
        return {"rule": rule, "qualified": [], "preferred": None, "status": "INCOMPLETE STUDY — NO QUALIFIED WINNER"}
    best = max(s["effective_coverage_task_macro_scheduled"] for s in summaries.values())
    qualified = [config for config, s in summaries.items()
                 if s["completion_scheduled"] >= .95 and s["success_scheduled"] >= .85
                 and s["n_critical_instances"] == 0
                 and s["effective_coverage_task_macro_scheduled"] + .05 + 1e-12 >= best]
    ranked = sorted(qualified, key=lambda c: (
        summaries[c]["success_wall_seconds"]["median"] if summaries[c]["success_wall_seconds"]["median"] is not None else math.inf,
        c))
    timing_missing = any(summaries[c]["success_wall_seconds"]["missing"] for c in qualified)
    preferred = ranked[0] if ranked and not timing_missing else None
    return {"rule": rule, "qualified": sorted(qualified), "preferred": preferred,
            "status": ("No qualified candidate" if not qualified else
                       "Qualified quality candidates; latency preference unresolved (missing observations)" if timing_missing else
                       "Provisional practical preference, not a formal statistical winner"),
            "uncertainty": "Small-cluster descriptive intervals can permit material quality loss; proximity to best is not equivalence."}


def analyze(records, sealed_grades, schedule, tasks, *, draws=10000, seed=None):
    """Join records to the pre-unblinding seal; analyze scheduled and attempted denominators.

    Production draws are fixed at 10,000. Smaller draws require explicit caller input
    for offline fixtures and are labelled in output, never silently substituted.
    """
    if type(draws) is not int or draws < 1:
        raise ValueError("bootstrap draws must be positive")
    seed = schedule["seed"] if seed is None else seed
    planned = indexed(schedule["trials"])
    task_map = tasks if isinstance(tasks, dict) else indexed(tasks)
    record_map = record_index(records)
    joined = unblind(sealed_grades)
    bundle = sealed_grades["bundle"]
    if bundle["schedule_hash"] != digest(schedule) or bundle["tasks_hash"] != digest(task_map):
        raise ValueError("frozen schedule/tasks hash breach")
    if set(joined) != set(planned) or set(record_map) - set(planned):
        raise ValueError("joined ledger does not match frozen schedule")
    rows = []
    for identity, trial in planned.items():
        record = record_map.get(identity)
        grade = joined[identity]
        if grade["record_hash"] != (digest(record) if record else None):
            raise ValueError("execution record hash breach")
        completed, attempted = is_completed(record), is_attempted(record)
        if grade["metrics"]["completed"] != completed:
            raise ValueError("grade/record completion mismatch")
        task = task_map[trial["task_id"]]
        cluster = task["cluster_id"]
        if trial["suite"] == "code":
            if not task.get("snapshot_id"):
                raise ValueError("code task needs frozen snapshot_id for repository bootstrap")
            cluster = task["snapshot_id"]
            if task["cluster_id"] != cluster:
                raise ValueError("code cluster_id must be the frozen repository snapshot_id")
        timing = (record or {}).get("timings", {})
        known_timing = {}
        for field in ("first_action_seconds", "first_final_answer_seconds", "request_seconds", "tool_seconds"):
            value = timing.get(field)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError("invalid observed timing")
            known_timing[field] = value
        rows.append({"trial_id": identity, "task_id": trial["task_id"], "suite": trial["suite"],
                     "configuration_id": trial["configuration_id"], "repetition": trial["repetition"],
                     "cluster_id": cluster, "repository": task.get("snapshot_id"),
                     "attempted": attempted, "completed": completed, "metrics": grade["metrics"],
                     "auxiliary": grade["grade"]["auxiliary"] if grade["grade"] is not None else {},
                     "status": (record or {}).get("status", (record or {}).get("terminal_status", "unrun")),
                     "wall_seconds": wall_seconds(record), "resources": (record or {}).get("resources", {}),
                     **known_timing})
    study_state = _study_state(record_map, rows, sealed_grades["review_accounting"])
    incomplete = study_state["incomplete"]
    suites = {}
    for suite in sorted({r["suite"] for r in rows}):
        suite_rows = [r for r in rows if r["suite"] == suite]
        configs = sorted({r["configuration_id"] for r in suite_rows})
        # Paired task comparisons require every frozen task/config combination.
        task_configs = {(r["task_id"], r["configuration_id"]) for r in suite_rows}
        if task_configs != set(itertools.product({r["task_id"] for r in suite_rows}, configs)):
            raise ValueError("schedule is not paired across tasks/configurations")
        summaries = {c: _summary([r for r in suite_rows if r["configuration_id"] == c]) for c in configs}
        task_slices = {task: {c: _summary([r for r in suite_rows if r["task_id"] == task and r["configuration_id"] == c])
                              for c in configs} for task in sorted({r["task_id"] for r in suite_rows})}
        cluster_slices = {cluster: {c: _summary([r for r in suite_rows if r["cluster_id"] == cluster and r["configuration_id"] == c])
                                    for c in configs} for cluster in sorted({r["cluster_id"] for r in suite_rows})}
        suites[suite] = {"configurations": summaries, "task_slices": task_slices,
                         "repository_or_project_slices": cluster_slices,
                         "bootstrap": _bootstrap(suite_rows, configs, seed, draws),
                         "recommendation": _recommend(summaries, incomplete)}
    return {"schema_version": 1, "study_status": "INCOMPLETE" if incomplete else "ALL SCHEDULED TRIALS ACCOUNTED FOR",
            "incomplete": incomplete, "n_scheduled": len(rows), "n_attempted": sum(r["attempted"] for r in rows),
            "study_state": study_state, "study_stop_reasons": study_state["stop_reasons"],
            "n_unrun": sum(not r["attempted"] for r in rows), "review_accounting": sealed_grades["review_accounting"],
            "input_hashes": {"records": digest(records), "sealed_grades": sealed_grades["sha256"],
                             "schedule": digest(schedule), "tasks": digest(tasks)},
            "bootstrap_draws": draws, "seed": seed, "suites": suites,
            "limitations": ["AI-graded with same-backend review, not human calibration; audits establish integrity, not semantic truth.",
                            "Few independent clusters; 36 repeats are not 36 independent questions. Intervals are descriptive and uncorrected.",
                            "Unrun trials get no scheduled outcome credit and no semantic grade; attempted-only denominators are separate.",
                            "Nonanswers have null semantic grades, not invented correctness; missing auxiliary/timing observations remain unknown.",
                            "Observed zero critical errors does not establish absence of critical risk.",
                            "Live web drift, route/scaffold and unverified effort honoring limit generalization.",
                            "No pooled suite winner, price weighting, prior-study data, retries, or best-of-three selection.",
                            "Wall time includes network/tools; overlapping intervals are not subtracted as pure inference time."]}
