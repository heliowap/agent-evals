"""Allowlisted blind packets and outcome-independent review obligations."""

import hashlib
import random
from collections import defaultdict
from copy import deepcopy

from .common import digest, indexed, record_index, is_attempted, is_completed, answer, signed


def blind_id(seed, trial_id):
    return "b-" + hashlib.sha256(f"blind-v1\0{seed}\0{trial_id}".encode()).hexdigest()[:24]


def select_review_ids(schedule, per_group=9):
    """Honor frozen review IDs; derive a seeded sample only when none is supplied."""
    if type(per_group) is not int or per_group < 1:
        raise ValueError("review per_group must be a positive integer")
    planned = indexed(schedule["trials"])
    groups = defaultdict(list)
    for trial in schedule["trials"]:
        groups[(trial["suite"], trial["configuration_id"])].append(trial["id"])
    if "review_sample_ids" in schedule:
        selected = schedule["review_sample_ids"]
        if not isinstance(selected, list):
            raise ValueError("frozen review_sample_ids must be a list")
        if any(not isinstance(identity, str) or identity not in planned for identity in selected):
            raise ValueError("frozen review sample contains unknown planned IDs")
        if len(set(selected)) != len(selected):
            raise ValueError("frozen review sample contains duplicate IDs")
        counts = defaultdict(int)
        for identity in selected:
            trial = planned[identity]
            counts[(trial["suite"], trial["configuration_id"])] += 1
        if len(selected) != per_group * len(groups) or any(counts[group] != per_group for group in groups):
            raise ValueError("frozen review sample must have exactly per_group IDs in every suite/configuration group")
        return sorted(selected)
    selected = []
    for group, identities in sorted(groups.items()):
        if len(identities) < per_group:
            raise ValueError("insufficient planned trials for review obligation")
        rng = random.Random(digest([schedule["seed"], "review-v1", list(group)]))
        selected.extend(rng.sample(sorted(identities), per_group))
    return sorted(selected)


def _text(entry, loader):
    if "visible_text" in entry:
        text = entry["visible_text"]
    elif "visible_path" in entry:
        if loader is None:
            raise ValueError("visible_path requires evidence_loader")
        text = loader(entry["visible_path"])
    else:
        raise ValueError("exact visible_text or visible_path required; raw text is not a substitute")
    if not isinstance(text, str):
        raise ValueError("visible evidence must be text")
    expected = entry.get("visible_sha256")
    if expected and hashlib.sha256(text.encode()).hexdigest() != expected:
        raise ValueError("candidate visible evidence hash breach")
    return text


def _reference(evidence, loader):
    # Preserve source facts only, never author/controller metadata or fixtures.
    allowed = ("path", "url", "quote", "start_line", "end_line", "sha256", "hash", "archive_path")
    reference = {key: deepcopy(evidence[key]) for key in allowed if key in evidence}
    if not isinstance(reference.get("quote"), str):
        raise ValueError("reference evidence requires a quote")
    if "archive_path" in reference:
        if loader is None:
            raise ValueError("archived reference requires evidence_loader")
        text = loader(reference["archive_path"])
        if reference["quote"] not in text:
            raise ValueError("reference quote not in frozen archive")
        expected = reference.get("sha256", reference.get("hash"))
        if expected and hashlib.sha256(text.encode()).hexdigest() != expected:
            raise ValueError("frozen reference hash breach")
    reference["support_eligible"] = False
    return reference


def export(records, tasks, gold, evidence_loader, schedule, *, review_per_group=9):
    """Return {packets, private_mapping, review_plan, ...}; do not send mapping to graders.

    records use id/trial_id, status, completed, final_answer, tool_evidence;
    evidence entries use name, status, visible_text/visible_path. See README.
    """
    task_map = tasks if isinstance(tasks, dict) else indexed(tasks)
    planned = indexed(schedule["trials"])
    record_map = record_index(records)
    if set(record_map) - set(planned):
        raise ValueError("execution record outside frozen schedule")
    selected = select_review_ids(schedule, review_per_group)
    packets, mapping = {}, {}
    for identity, trial in sorted(planned.items()):
        task = task_map[trial["task_id"]]
        if task["suite"] != trial["suite"]:
            raise ValueError("task/schedule suite mismatch")
        record = record_map.get(identity)
        if record:
            for field in ("suite", "task_id", "configuration_id", "repetition"):
                actual = record.get(field, record.get("trial", {}).get(field))
                if actual is not None and actual != trial[field]:
                    raise ValueError("record/schedule identity mismatch")
        opaque = blind_id(schedule["seed"], identity)
        attempted, completed = is_attempted(record), is_completed(record)
        criteria = gold[trial["task_id"]]
        units = []
        for unit in criteria["units"]:
            if type(unit["essential"]) is not bool:
                raise ValueError("essential must be boolean")
            units.append({"id": unit["id"], "description": unit["description"],
                          "essential": unit["essential"],
                          "reference_evidence": [_reference(e, evidence_loader) for e in unit["evidence"]]})
        if not units:
            raise ValueError("gold needs at least one unit")
        indexed(units)
        evidence = []
        for number, entry in enumerate((record or {}).get("tool_evidence", []), 1):
            name = entry["name"]
            if name not in ("websearch", "webfetch", "list", "glob", "grep", "read"):
                raise ValueError("unknown evidence tool")
            status = entry["status"]
            text = _text(entry, evidence_loader)
            evidence.append({"id": f"e-{number:04d}", "tool": name, "status": status,
                             "text": text, "support_eligible": status in ("ok", "success") and bool(text.strip())})
        packet = {"schema_version": 1, "blind_id": opaque, "suite": trial["suite"],
                  "prompt": task["prompt"], "completed": completed, "attempted": attempted,
                  "operational_status": (record or {}).get("status", (record or {}).get("terminal_status", "unrun")),
                  "answer": answer(record) if completed else None,
                  "diagnostic_partial_answer": answer(record) if attempted and not completed else None,
                  "units": units, "critical_error_criteria": deepcopy(criteria["critical_errors"]),
                  "acceptable_alternatives": deepcopy(criteria["acceptable_alternatives"]),
                  "reference_answer": criteria["reference_answer"], "candidate_evidence": evidence}
        packets[opaque] = packet
        mapping[opaque] = {"trial_id": identity, "record_hash": digest(record) if record else None}
    return signed({"schema_version": 1, "packets": packets, "private_mapping": mapping,
                   "schedule_hash": digest(schedule), "tasks_hash": digest(task_map), "gold_hash": digest(gold),
                   "review_plan": {"selection": ("explicit frozen schedule.review_sample_ids" if "review_sample_ids" in schedule
                                                  else "seeded planned IDs, not outcomes"), "per_group": review_per_group,
                                   "trial_ids": selected,
                                   "blind_ids": sorted(blind_id(schedule["seed"], i) for i in selected)}})


def pack_jobs(bundle, *, batch_size=4, review=False, base_grades=None):
    """Fresh-session jobs containing <=4 answers; never attach identity mapping."""
    if not 1 <= batch_size <= 4:
        raise ValueError("grader batches must contain 1..4 packets")
    from .sealing import review_obligations
    base_grades = base_grades or {}
    identities = (review_obligations(bundle, base_grades) if review else
                  {i for i, p in bundle["packets"].items() if p["completed"]})
    jobs = []
    for identity in sorted(identities):
        packet = bundle["packets"][identity]
        if not packet["attempted"]:
            continue  # reported as unresolved unrun; never replaced
        jobs.append({"packet": packet, "kind": "semantic" if packet["completed"] else "operational",
                     **({"base_grade": base_grades.get(identity),
                         "base_grade_hash": digest(base_grades.get(identity))} if review else {})})
    return [{"fresh_session_required": True, "grader": "openai/gpt-6.1-sol-fast#high",
             "jobs": jobs[i:i + batch_size]} for i in range(0, len(jobs), batch_size)]
