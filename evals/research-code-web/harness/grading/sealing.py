"""Immutable originals, separate review/adjudication, and pre-unblinding seals."""

from copy import deepcopy

from .common import digest, indexed, signed, verify_signed
from .schema import GRADER, validate_grade, derive_metrics


def seal_base(bundle, grades):
    verify_signed(bundle)
    expected = {i for i, packet in bundle["packets"].items() if packet["completed"]}
    if set(grades) != expected:
        raise ValueError("base grade set must equal all completed answers")
    validated = {i: validate_grade(grades[i], bundle["packets"][i]) for i in sorted(expected)}
    return signed({"schema_version": 1, "bundle_hash": bundle["sha256"], "grades": validated,
                   "grade_hashes": {i: digest(g) for i, g in validated.items()}})


def review_obligations(bundle, grades):
    return set(bundle["review_plan"]["blind_ids"]) | {
        i for i, g in grades.items() if g["critical_errors"] or g["uncertain"]}


def _decisions(grade):
    if grade is None:
        return None
    return {"units": sorted((u["id"], u["correct"], u["supported"]) for u in grade["units"]),
            "critical_errors": grade["critical_errors"],
            "decisive_unsupported": grade["decisive_unsupported"], "uncertain": grade["uncertain"],
            "auxiliary": grade["auxiliary"]}


def seal_final(bundle, base_seal, reviews, adjudications=()):
    """Seal final grades only after every attempted review obligation is resolved.

    Sampled unrun obligations remain explicitly unresolved; they cannot be replaced.
    Fresh-session provenance is asserted by the orchestrator, not proved by JSON.
    """
    verify_signed(bundle)
    verify_signed(base_seal)
    if base_seal != seal_base(bundle, base_seal["grades"]):
        raise ValueError("base seal hash/grade breach")
    grades = base_seal["grades"]
    packets = bundle["packets"]
    required = review_obligations(bundle, grades)
    unrun = {i for i in required if not packets[i]["attempted"]}
    review_map = indexed(reviews, "blind_id")
    adjudication_map = indexed(adjudications, "blind_id")
    if set(review_map) != required - unrun:
        raise ValueError("missing/extra independent review obligation")
    final = deepcopy(grades)
    disagreements = []
    sessions = set()
    semantic = operational = 0
    for identity, review in sorted(review_map.items()):
        packet = packets[identity]
        kind = "semantic" if packet["completed"] else "operational"
        if (review.get("kind") != kind or review.get("grader") != GRADER
                or review.get("independent_session") is not True
                or not isinstance(review.get("session_id"), str) or not review["session_id"].strip()
                or not isinstance(review.get("rationale"), str) or not review["rationale"].strip()
                or review.get("base_grade_hash") != digest(grades.get(identity))):
            raise ValueError("invalid fresh-session review/provenance/base link")
        # A review session may handle <=4 packets, but never mix grading and review.
        sessions.add(review["session_id"])
        reviewed = validate_grade(review.get("grade"), packet)
        if packet["completed"]:
            semantic += 1
        else:
            operational += 1
        if _decisions(reviewed) != _decisions(grades.get(identity)):
            disagreements.append(identity)
    for session in sessions:
        if sum(r["session_id"] == session for r in reviews) > 4:
            raise ValueError("review batch exceeds four answers")
    if set(adjudication_map) != set(disagreements):
        raise ValueError("every disagreement needs separate blinded adjudication")
    for identity, event in adjudication_map.items():
        if (event.get("grader") != GRADER or not isinstance(event.get("rationale"), str)
                or not event["rationale"].strip() or event.get("base_grade_hash") != digest(grades[identity])
                or event.get("review_hash") != digest(review_map[identity])):
            raise ValueError("invalid separate adjudication history")
        final[identity] = validate_grade(event.get("grade"), packets[identity])
    final = {i: final.get(i) for i in sorted(packets)}
    metrics = {i: derive_metrics(packets[i], final[i]) for i in sorted(packets)}
    return signed({"schema_version": 1, "stage": "final-before-unblinding",
                   "calibration": "Same-backend AI review; not human calibration",
                   "bundle": deepcopy(bundle), "base_seal": deepcopy(base_seal),
                   "reviews": sorted(deepcopy(list(reviews)), key=lambda r: r["blind_id"]),
                   "adjudications": sorted(deepcopy(list(adjudications)), key=lambda r: r["blind_id"]),
                   "final_grades": final, "metrics": metrics,
                   "review_accounting": {"planned_sample": len(bundle["review_plan"]["blind_ids"]),
                                         "total_obligations": len(required), "semantic_reviewed": semantic,
                                         "operational_reviewed": operational,
                                         "unresolved_unrun": sorted(unrun), "missing_attempted": [],
                                         "disagreements": sorted(disagreements)}})


def validate_sealed(document):
    verify_signed(document)
    reproduced = seal_final(document["bundle"], document["base_seal"],
                            document["reviews"], document["adjudications"])
    if document != reproduced:
        raise ValueError("sealed final grades/metrics/history breach")
    return document


def unblind(document):
    validate_sealed(document)
    mapping = document["bundle"]["private_mapping"]
    return {mapping[i]["trial_id"]: {"grade": document["final_grades"][i],
                                     "metrics": document["metrics"][i],
                                     "record_hash": mapping[i]["record_hash"]} for i in mapping}
