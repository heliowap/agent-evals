"""Artificial artifacts only: no candidate inference or previous evaluation data."""

from copy import deepcopy

from grading import export, seal_base, seal_final, select_review_ids
from grading.common import digest
from grading.schema import GRADER


CONFIGS = ["gemini-low", "gemini-medium", "gemini-high", "deepseek-low", "deepseek-high",
           "deepseek-max", "glm-low", "glm-high", "glm-max"]
REPOS = ["click", "httpx", "cobra", "prometheus", "zod", "opencode"]


def inputs(full=False, no_other=False):
    configs = CONFIGS if full else CONFIGS[:2]
    count = 12 if full else 2
    tasks, gold, records, trials = [], {}, [], []
    for suite in ("web", "code"):
        for number in range(count):
            task_id = f"{suite}-{number}"
            repository = REPOS[number // 2] if full else REPOS[number]
            task = {"schema_version": 1, "id": task_id, "suite": suite,
                    "prompt": "State the frozen floor and the branch constraint.",
                    "cluster_id": f"project-{number // 3}" if suite == "web" else repository}
            if suite == "code":
                task["snapshot_id"] = repository
            tasks.append(task)
            units = [{"id": "floor", "description": "The minimum is three.", "essential": True,
                      "evidence": [{"url": "https://example.org/frozen", "quote": "minimum is three"}]}]
            if not no_other:
                units.append({"id": "branch", "description": "The branch is closed.", "essential": False,
                              "evidence": [{"path": "src/branch.py", "quote": "branch is closed"}]})
            gold[task_id] = {"units": units, "critical_errors": ["Fabricated decisive floor"],
                             "acceptable_alternatives": ["Equivalent wording"],
                             "reference_answer": "The minimum is three; the branch is closed.",
                             "fixtures": {"do_not_export": "CONTROLLER_PRIVATE"}}
            for repeat in range(3):
                for config in configs:
                    identity = f"{task_id}-r{repeat}-{config}"
                    trials.append({"id": identity, "index": len(trials), "suite": suite, "task_id": task_id,
                                   "repetition": repeat, "configuration_id": config,
                                   "block_id": f"{task_id}-{repeat}", "position": configs.index(config)})
                    evidence = [{"name": "websearch", "status": "ok", "visible_text": "found frozen result"},
                                {"name": "webfetch", "status": "ok", "visible_text": "<untrusted>minimum is three; branch is closed.</untrusted>"}] if suite == "web" else [
                        {"name": "read", "status": "ok", "visible_text": "1: minimum is three\n2: branch is closed"}]
                    records.append({"id": identity, "status": "completed", "completed": True,
                                    "final_answer": "The minimum is three; the branch is closed.",
                                    "wall_seconds": 20 + configs.index(config), "tool_evidence": evidence,
                                    "native_history": "NATIVE_PRIVATE", "model": "CANDIDATE_PRIVATE",
                                    "reasoning_effort": "EFFORT_PRIVATE", "metadata": {"latency": "LATENCY_PRIVATE"}})
    schedule = {"seed": 20261007, "configurations": configs, "blocks": [], "trials": trials}
    return records, tasks, gold, schedule


def base_grades(bundle):
    grades = {}
    for identity, packet in bundle["packets"].items():
        if not packet["completed"]:
            continue
        source = next(e for e in packet["candidate_evidence"] if e["tool"] in ("read", "webfetch"))
        grades[identity] = {"blind_id": identity, "units": [
            {"id": u["id"], "correct": True, "supported": True, "rationale": "Artificial correct supported fixture.",
             "evidence": [{"source_id": source["id"], "quote": "minimum is three" if u["id"] == "floor" else "branch is closed"}]}
            for u in packet["units"]], "critical_errors": [], "decisive_unsupported": False,
            "uncertain": False, "auxiliary": {}, "grader": GRADER}
    return grades


def reviews_for(bundle, base):
    from grading.sealing import review_obligations
    result = []
    for number, identity in enumerate(sorted(review_obligations(bundle, base["grades"]))):
        packet = bundle["packets"][identity]
        if not packet["attempted"]:
            continue
        result.append({"blind_id": identity, "kind": "semantic" if packet["completed"] else "operational",
                       "grade": deepcopy(base["grades"].get(identity)), "rationale": "Artificial independent review fixture.",
                       "grader": GRADER, "independent_session": True, "session_id": f"fixture-review-{number}",
                       "base_grade_hash": digest(base["grades"].get(identity))})
    return result


def assembled(records, tasks, gold, schedule, *, full=False, grade_edit=None):
    bundle = export(records, tasks, gold, None, schedule, review_per_group=9 if full else 1)
    grades = base_grades(bundle)
    if grade_edit:
        grade_edit(grades, bundle)
    base = seal_base(bundle, grades)
    reviews = reviews_for(bundle, base)
    return bundle, base, reviews, seal_final(bundle, base, reviews)


def study(full=False, no_other=False):
    records, tasks, gold, schedule = inputs(full, no_other)
    bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=full)
    return records, tasks, gold, schedule, bundle, base, reviews, sealed
