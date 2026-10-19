"""Independent unit labels, evidence eligibility, and frozen success rule."""

from copy import deepcopy

GRADER = "openai/gpt-6.1-sol-fast#high"
AUXILIARY = ("citation_coverage", "citation_entailment", "source_authority", "unsupported_extras",
             "uncertainty", "usability", "tool_navigation")


def validate_grade(grade, packet):
    if not packet["completed"]:
        if grade is not None:
            raise ValueError("nonanswers have null semantic grades")
        return None
    required = {"blind_id", "units", "critical_errors", "decisive_unsupported", "uncertain", "auxiliary", "grader"}
    if not isinstance(grade, dict) or set(grade) != required:
        raise ValueError("grade must match exact base schema")
    if grade["blind_id"] != packet["blind_id"] or grade["grader"] != GRADER:
        raise ValueError("wrong blind identity or grader provenance")
    for key in ("decisive_unsupported", "uncertain"):
        if type(grade[key]) is not bool:
            raise ValueError(key + " must be boolean")
    if not isinstance(grade["critical_errors"], list):
        raise ValueError("critical_errors must be instances in a list")
    if not isinstance(grade["auxiliary"], dict) or set(grade["auxiliary"]) - set(AUXILIARY):
        raise ValueError("unknown auxiliary fields")
    result = deepcopy(grade)
    result["auxiliary"] = {key: grade["auxiliary"].get(key) for key in AUXILIARY}
    expected = {unit["id"] for unit in packet["units"]}
    if not isinstance(grade["units"], list) or len(grade["units"]) != len(expected):
        raise ValueError("grade must label every unit exactly once")
    seen = set()
    evidence = {entry["id"]: entry for entry in packet["candidate_evidence"]}
    for unit in grade["units"]:
        if not isinstance(unit, dict) or set(unit) != {"id", "correct", "supported", "rationale", "evidence"}:
            raise ValueError("unit schema mismatch")
        if unit["id"] not in expected or unit["id"] in seen:
            raise ValueError("missing/duplicate/unknown unit")
        seen.add(unit["id"])
        if type(unit["correct"]) is not bool or type(unit["supported"]) is not bool:
            raise ValueError("unit labels must be independent booleans")
        if not isinstance(unit["rationale"], str) or not unit["rationale"].strip():
            raise ValueError("unit rationale required")
        if not isinstance(unit["evidence"], list) or (unit["supported"] and not unit["evidence"]):
            raise ValueError("support requires actual candidate-visible evidence")
        for citation in unit["evidence"]:
            if not isinstance(citation, dict) or set(citation) != {"source_id", "quote"}:
                raise ValueError("evidence needs source_id and exact quote")
            source = evidence.get(citation["source_id"])
            if not source or not source["support_eligible"]:
                raise ValueError("support cannot come from gold, unread or unsuccessful sources")
            quote = citation["quote"]
            if not isinstance(quote, str) or not quote.strip() or quote not in source["text"]:
                raise ValueError("support quote not in exact candidate-visible text")
    return result


def derive_metrics(packet, grade):
    grade = validate_grade(grade, packet)
    if grade is None:
        return {"completed": False, "correctness": None, "supported_fraction": None,
                "grounded_coverage": None, "effective_coverage": 0.0, "practical_success": False,
                "critical_errors": 0, "critical_evaluable": False, "research_observed": False}
    labels = {unit["id"]: unit for unit in grade["units"]}
    grounded = {identity: label["correct"] and label["supported"] for identity, label in labels.items()}
    essential = [grounded[u["id"]] for u in packet["units"] if u["essential"]]
    other = [grounded[u["id"]] for u in packet["units"] if not u["essential"]]
    tools = {e["tool"] for e in packet["candidate_evidence"] if e["support_eligible"]}
    researched = {"websearch", "webfetch"} <= tools if packet["suite"] == "web" else "read" in tools
    coverage = sum(grounded.values()) / len(labels)
    success = (all(essential) and (not other or 5 * sum(other) >= 4 * len(other))
               and not grade["critical_errors"] and not grade["decisive_unsupported"] and researched)
    return {"completed": True, "correctness": sum(u["correct"] for u in labels.values()) / len(labels),
            "supported_fraction": sum(u["supported"] for u in labels.values()) / len(labels),
            "grounded_coverage": coverage, "effective_coverage": coverage,
            "practical_success": success, "critical_errors": len(grade["critical_errors"]),
            "critical_evaluable": True, "research_observed": researched}
