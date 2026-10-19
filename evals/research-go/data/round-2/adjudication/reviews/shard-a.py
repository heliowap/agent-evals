import argparse
import collections
import hashlib
import json
import pathlib
import re
import urllib.parse


ROOT = pathlib.Path(__file__).resolve().parents[2]
EMPTY_IDS = {
    "b-2dd10cd45b30bafb9c72e022bc21c5b1",
    "b-c0ac18602b6b5a2914734d1ff3efd71d",
    "b-4e6c5af7249eee402edded8319c55af5",
}
OVERRIDE_IDS = {
    "b-5b021b4d6cbe51bb8f302234e0448287",
    "b-875d48e2c3bc7b3f7881801a553e4450",
    "b-6cd6175cd4fa6aee177667789b7ba632",
    "b-fdb35d4bddba6dd2651da284ec356999",
}
GRADE_KEYS = {
    "blind_id", "task_id", "checks", "uncertainty", "citations",
    "critical_errors", "unsupported_extras", "compliance", "ambiguous", "notes",
}
STATUS = {"supported", "contradicted", "missing", "unverifiable"}
CITATION_STATUS = {"entailing", "missing", "non_entailing"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def presentation(text):
    text = re.sub(r"\[([^\]]*)\]\(https://[^\s\)]+\)", r"\1", text)
    text = text.replace("`", "").replace("**", "")
    return " ".join(text.split())


def base(url):
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), parsed.query, ""))


def https(url):
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def digest_map(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify():
    allowed = {"blind/index.json", "preflight/grading-guide.md", "contracts.md", "adjudication/reviews/shard-a.json"}

    def read(relative):
        require(relative in allowed, f"Read outside public shard-A allowlist: {relative}")
        path = ROOT / relative
        require(path.resolve().is_relative_to(ROOT), f"Escaping path: {relative}")
        return path.read_text(encoding="utf-8")

    def load(relative):
        return json.loads(read(relative))

    index = load("blind/index.json")
    ids = index["shards"]["a"]
    require(len(ids) == 36 and len(set(ids)) == 36, "Shard A must contain 36 distinct IDs")
    receipt = load("adjudication/reviews/shard-a.json")
    require(receipt["blind_review"] is True and receipt["passed"] is True, "Review is not passed/blind")
    require(receipt["source_based"] is True and receipt["blind_inputs_only"] is True, "Missing blind source declaration")
    require(receipt["reviewer_type"] == "AI: GPT-6.1 Sol Fast High", "Wrong reviewer declaration")
    cases = {}
    snapshots = {}
    initial_hashes = {}
    effective = []
    reviewed = []
    empties = []
    source_checks = 0
    fetched_proofs = 0

    for blind_id in ids:
        case_path = f"blind/cases/{blind_id}/case.json"
        allowed.add(case_path)
        case_text = read(case_path)
        case = json.loads(case_text)
        cases[blind_id] = case
        require(case["blind_id"] == blind_id, "Case identity mismatch")
        source_map = {}
        snapshot = hashlib.sha256(case_text.encode())
        for source in case["sources"]:
            for key in ("source_path", "candidate_visible_path"):
                if source.get(key):
                    relative = source[key]
                    require(relative.startswith(f"blind/cases/{blind_id}/sources/"), "Cross-case source path")
                    require(".." not in pathlib.PurePosixPath(relative).parts, "Invalid source path")
                    allowed.add(relative)
                    body = read(relative)
                    snapshot.update(relative.encode())
                    snapshot.update(hashlib.sha256(body.encode()).digest())
            source_map[source["source_path"]] = source
        snapshots[blind_id] = snapshot.hexdigest()
        grade_path = f"grades/shard-a/{blind_id}.json"
        override_path = f"adjudication/{blind_id}.json"
        if not case["answer"]:
            require(blind_id in EMPTY_IDS, "Unexpected empty answer")
            require(not (ROOT / grade_path).exists() and not (ROOT / override_path).exists(), "Fabricated empty grade/override")
            empties.append(blind_id)
            continue
        require(blind_id not in EMPTY_IDS, "Expected empty row has an answer")
        allowed.add(grade_path)
        initial_text = read(grade_path)
        initial = json.loads(initial_text)
        initial_hashes[grade_path] = hashlib.sha256(initial_text.encode()).hexdigest()
        if blind_id in OVERRIDE_IDS:
            allowed.add(override_path)
            override = load(override_path)
            require(set(override) == {"blind_id", "initial_grade_path", "rationale", "effective_grade"}, "Override schema mismatch")
            require(override["blind_id"] == blind_id and override["initial_grade_path"] == grade_path, "Override provenance mismatch")
            require(bool(override["rationale"]), "Missing override rationale")
            grade = override["effective_grade"]
            require(grade != initial, "No genuine override change")
            require(grade["compliance"] == initial["compliance"], "Review must not repair mechanical/URL compliance")
        else:
            require(not (ROOT / override_path).exists(), "Unaccounted shard-A override")
            grade = initial

        def evidence(items, fetched=False, literal=False):
            nonlocal source_checks, fetched_proofs
            require(isinstance(items, list), "Evidence must be a list")
            for item in items:
                require(set(item) >= {"url", "source_path", "quote"}, "Evidence schema mismatch")
                require(item["source_path"] in source_map, "Evidence is not a case source")
                source = source_map[item["source_path"]]
                require(https(item["url"]) and base(item["url"]) == base(source["url"]), "Evidence official URL mismatch")
                body = read(item["source_path"])
                quote = item["quote"]
                require(isinstance(quote, str) and bool(quote), "Empty source quote")
                require(quote in body if literal else presentation(quote) in presentation(body), f"Source quote not in saved body: {item['source_path']} {quote!r}")
                source_checks += 1
                if fetched:
                    require(source["status"] == "fetched" and source.get("citation_support_eligible") is True and not source.get("frozen"), "Frozen/unfetched citation grounding")
                    visible = read(source.get("candidate_visible_path", source["source_path"]))
                    require(presentation(quote) in presentation(visible), "Proof was not candidate-visible")
                    fetched_proofs += 1

        def validate(value, strict):
            require(set(value) == GRADE_KEYS, "Grade schema mismatch")
            require(value["blind_id"] == blind_id and value["task_id"] == case["task_id"], "Grade identity mismatch")
            require([check["id"] for check in value["checks"]] == [f"C{n}" for n in range(1, 7)], "Six checks required")
            require(type(value["ambiguous"]) is bool and isinstance(value["notes"], str), "Notes/ambiguity schema")
            require(isinstance(value["citations"], list), "Citation list schema")
            for check in value["checks"]:
                require(set(check) == {"id", "status", "answer_quote", "evidence", "rationale", "citation_status"}, "Check schema mismatch")
                require(check["status"] in STATUS and check["citation_status"] in CITATION_STATUS, "Invalid check status")
                require(bool(check["rationale"]), "Missing check rationale")
                quote = check["answer_quote"]
                if check["status"] == "missing":
                    require(quote == "" and check["citation_status"] == "missing", "Missing check must have empty quote")
                else:
                    require(bool(quote), "Asserted check requires quote")
                    require(quote in case["answer"] if strict else presentation(quote) in presentation(case["answer"]), "Answer quote is not a saved span")
                    require(bool(check["evidence"]), "Asserted check needs source proof")
                evidence(check["evidence"], literal=strict and blind_id in OVERRIDE_IDS)
                if check["citation_status"] == "entailing":
                    candidates = [citation for citation in value["citations"] if citation["support"] == "entailing" and check["answer_quote"] in citation["answer_quote"]]
                    require(bool(candidates), "Entailing check lacks claim-level citation coverage")
                    require(any(base(citation["url"]) in {base(item["url"]) for item in citation["evidence"]} for citation in candidates), "Citation lacks cited-page evidence")
            uncertainty = value["uncertainty"]
            require(set(uncertainty) == {"status", "answer_quote", "rationale", "evidence"}, "Uncertainty schema")
            require(uncertainty["status"] in {"pass", "omit", "fail"} and bool(uncertainty["rationale"]), "Uncertainty judgment")
            require(uncertainty["answer_quote"] in case["answer"], "Uncertainty quote must be literal")
            if uncertainty["status"] != "omit":
                require(bool(uncertainty["answer_quote"]) and bool(uncertainty["evidence"]), "Uncertainty proof absent")
            evidence(uncertainty["evidence"], literal=strict and blind_id in OVERRIDE_IDS)
            for citation in value["citations"]:
                require(set(citation) == {"answer_quote", "url", "support", "anchor_compliance", "rationale", "evidence"}, "Citation schema")
                require(citation["support"] in CITATION_STATUS and type(citation["anchor_compliance"]) is bool, "Citation judgment")
                require(citation["answer_quote"] in case["answer"] and citation["url"] in case["answer"] and https(citation["url"]), "Citation is not literal usable HTTPS in answer")
                require(bool(citation["rationale"]), "Missing citation rationale")
                evidence(citation["evidence"], fetched=citation["support"] == "entailing", literal=strict and blind_id in OVERRIDE_IDS)
                if citation["support"] == "entailing":
                    require(bool(citation["evidence"]), "Entailing citation has no proof")
                    require(any(base(item["url"]) == base(citation["url"]) for item in citation["evidence"]), "Entailing citation uses a different page")
                fragment = urllib.parse.urlsplit(citation["url"]).fragment
                if fragment and citation["anchor_compliance"]:
                    anchor_urls = []
                    for source in case["sources"]:
                        if base(source["url"]) == base(citation["url"]):
                            anchor_urls.extend(re.findall(r'https://[^\s<>"\)]+', read(source["source_path"])))
                    require(any(base(url) == base(citation["url"]) and urllib.parse.urlsplit(url).fragment == fragment for url in anchor_urls), "Unverified literal anchor")
            for field in ("critical_errors", "unsupported_extras"):
                require(isinstance(value[field], list), "Extra/critical list schema")
                for finding in value[field]:
                    require(set(finding) == {"answer_quote", "rationale", "evidence"}, "Extra/critical schema")
                    require(bool(finding["answer_quote"]) and finding["answer_quote"] in case["answer"] and bool(finding["rationale"]), "Extra/critical answer proof")
                    require(bool(finding["evidence"]), "Extra/critical source proof")
                    evidence(finding["evidence"], literal=strict and blind_id in OVERRIDE_IDS)
            compliance = value["compliance"]
            flags = {"full_urls", "word_cap", "english", "fetched_two_sources", "source_rules", "tool_rules"}
            require(set(compliance) == flags | {"discovery_chain"}, "Compliance schema")
            require(all(type(compliance[key]) is bool for key in flags), "Compliance flags must be booleans")
            for key in ("word_cap", "fetched_two_sources", "source_rules", "tool_rules"):
                require(compliance[key] == case["mechanical"][key], "Changed mechanical constraint")
            require(compliance["word_cap"] == (case["mechanical"]["visible_words"] <= 400), "Word-cap mismatch")
            if compliance["full_urls"]:
                require(all(citation["anchor_compliance"] for citation in value["citations"]), "Full URLs true with invalid anchor")
            require(isinstance(compliance["discovery_chain"], str), "Discovery-chain disclosure required")

        validate(initial, strict=False)
        validate(grade, strict=True)
        fetched = [source for source in case["sources"] if source["status"] == "fetched" and source.get("citation_support_eligible")]
        canonical = {base(source["url"]) for source in fetched}
        contents = {hashlib.sha256(read(source["source_path"]).encode()).hexdigest() for source in fetched}
        require(case["mechanical"]["fetched_two_sources"] == (len(canonical) >= 2 and len(contents) >= 2), "Canonical/content source dedup mismatch")
        reviewed.append(blind_id)
        effective.append(grade)

    require(len(reviewed) == 33 and len(empties) == 3 and set(empties) == EMPTY_IDS, "Incomplete 33+3 coverage")
    require(receipt["reviewed_ids"] == reviewed and receipt["empty_ids"] == empties, "Receipt coverage mismatch")
    require(receipt["initial_grade_paths"] == [f"grades/shard-a/{blind_id}.json" for blind_id in reviewed], "Initial paths mismatch")
    require(set(receipt["override_paths"]) == {f"adjudication/{blind_id}.json" for blind_id in OVERRIDE_IDS}, "Override coverage mismatch")
    require(set(receipt["case_reviews"]) == set(reviewed) and all(receipt["case_reviews"].values()), "Independent review findings coverage missing")
    require(receipt["initial_grades_sha256"] == digest_map(initial_hashes), "Immutable initial grades changed")
    require(receipt["blind_cases_sha256"] == digest_map(snapshots), "Immutable blind inputs changed")
    counts = {
        "reviewed": len(reviewed), "empty": len(empties), "overrides": len(OVERRIDE_IDS),
        "critical_errors": sum(len(grade["critical_errors"]) for grade in effective),
        "ambiguous_cases": sum(grade["ambiguous"] for grade in effective),
        "unsupported_extras": sum(len(grade["unsupported_extras"]) for grade in effective),
        "citation_failure_cases": sum(not grade["compliance"]["full_urls"] or any(check["status"] != "missing" and check["citation_status"] != "entailing" for check in grade["checks"]) for grade in effective),
        "tasks": dict(collections.Counter(grade["task_id"] for grade in effective)),
        "uncertainty": dict(collections.Counter(grade["uncertainty"]["status"] for grade in effective)),
    }
    require(counts == receipt["counts"], "Receipt counts mismatch")
    print(json.dumps({"passed": True, **counts, "source_quote_checks": source_checks, "actual_fetched_citation_proofs": fetched_proofs, "public_only": True, "semantic_judgments": "independent AI source-read; not generated by this validator"}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Read-only public shard-A coverage, schema, quote and citation-proof validator; does not adjudicate semantics.")
    parser.add_argument("--verify", action="store_true", help="Verify shard-A review against allowed saved public inputs, without writing files or accessing network.")
    args = parser.parse_args()
    if not args.verify:
        parser.error("--verify is required")
    verify()


if __name__ == "__main__":
    main()
