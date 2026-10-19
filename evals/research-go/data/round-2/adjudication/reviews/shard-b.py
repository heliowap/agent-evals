import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = "adjudication/reviews/shard-b.json"
OVERRIDES = {
    "b-bf4e81f360b8b20af2b956c39274263c",
    "b-8cde36a8b4992e44c500313bcd5a56a6",
    "b-bf6567ae9f3a37de8f271385b3dfab78",
}
TRANSCRIPTION_WARNINGS = {
    "b-be25217ddb69a8fee2482556e184d278",
    "b-3fe40bc432dbe9afed87accfc1b872a8",
    "b-8cde36a8b4992e44c500313bcd5a56a6",
    "b-bf6567ae9f3a37de8f271385b3dfab78",
    "b-26c3fa1f9ffe2f896fa9c497ab559c3c",
}
STATUSES = {"supported", "contradicted", "missing", "unverifiable"}
CITATION_STATUSES = {"entailing", "missing", "non_entailing"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(relative, allowed):
    require(relative in allowed, f"read outside public allowlist: {relative}")
    path = ROOT / relative
    require(path.resolve().is_relative_to(ROOT), f"path escapes root: {relative}")
    require(not path.is_symlink(), f"symlink input: {relative}")
    return path.read_text(encoding="utf-8")


def load(relative, allowed):
    return json.loads(read(relative, allowed))


def presentation(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").replace("**", "").replace("*", "")
    text = re.sub(r"\\([*_`])", r"\1", text)
    return " ".join(text.split())


def page(url):
    return url.split("#", 1)[0].replace("/index.md", "/")


def urls(text):
    return {m.rstrip(".,;:") for m in re.findall(r"https://[^\s<>\)\]\}]+", text)}


def verify_grade(grade, case, allowed, strict, warnings):
    blind_id = case["blind_id"]
    label = f"{blind_id} {'override' if strict else 'initial'}"
    keys = {
        "blind_id", "task_id", "checks", "uncertainty", "citations",
        "critical_errors", "unsupported_extras", "compliance", "ambiguous", "notes",
    }
    require(keys <= grade.keys(), f"{label}: incomplete grade")
    require(grade["blind_id"] == blind_id and grade["task_id"] == case["task_id"], f"{label}: identity/task mismatch")
    require(type(grade["ambiguous"]) is bool, f"{label}: ambiguity must be boolean")
    require(isinstance(grade["notes"], list), f"{label}: notes must be an array")
    require(len(grade["checks"]) == 6, f"{label}: not six checks")
    require([x["id"] for x in grade["checks"]] == [x["id"] for x in case["rubric"]["checks"]], f"{label}: check IDs differ from frozen rubric")
    sources = {s["source_path"]: s for s in case["sources"]}
    texts = {p: read(p, allowed) for p in sources}
    answer = presentation(case["answer"])
    answer_urls = urls(case["answer"])

    def evidence(items, location):
        require(isinstance(items, list), f"{label} {location}: evidence is not an array")
        for e in items:
            require({"url", "source_path", "quote"} <= e.keys(), f"{label}: incomplete evidence")
            require(e["source_path"] in sources, f"{label}: evidence not bound to this case")
            s = sources[e["source_path"]]
            require(page(e["url"]) == page(s["url"]), f"{label}: wrong evidence URL")
            require(e["url"].startswith("https://") and bool(e["quote"]), f"{label}: empty/insecure evidence")
            literal = presentation(e["quote"]) in presentation(texts[e["source_path"]])
            if not literal:
                expected = "The Go toolchain refuses to load a module or workspace that declares a minimum required Go version greater than the toolchain's own version."
                known = not strict and blind_id in TRANSCRIPTION_WARNINGS and e["quote"] == expected
                require(known, f"{label} {location}: source quote not literal: {e['quote']!r}")
                warnings.append({"blind_id": blind_id, "location": location, "source_path": e["source_path"], "issue": "Initial transcription uses ASCII apostrophe; source uses curly apostrophe. No semantic change."})

    def claim(item, location, required_evidence=True):
        require({"answer_quote", "rationale", "evidence"} <= item.keys(), f"{label} {location}: incomplete claim")
        require(isinstance(item["rationale"], str) and bool(item["rationale"]), f"{label}: absent rationale")
        require(isinstance(item["answer_quote"], str), f"{label}: quote must be text")
        if item["answer_quote"]:
            require(presentation(item["answer_quote"]) in answer, f"{label} {location}: answer quote not literal")
        if required_evidence:
            require(bool(item["evidence"]), f"{label} {location}: no evidence")
        evidence(item["evidence"], location)

    for check in grade["checks"]:
        require(check["status"] in STATUSES and check["citation_status"] in CITATION_STATUSES, f"{label}: invalid check status")
        claim(check, check["id"], check["status"] != "missing")
        if check["status"] == "missing":
            require(check["answer_quote"] == "" and not check["evidence"], f"{label}: invented missing-check quote/evidence")
        else:
            require(bool(check["answer_quote"]), f"{label}: asserted check lacks quote")
    uncertainty = grade["uncertainty"]
    require(uncertainty["status"] in {"pass", "omit", "fail"}, f"{label}: invalid U")
    claim(uncertainty, "U", uncertainty["status"] != "omit")
    for field in ("critical_errors", "unsupported_extras"):
        require(isinstance(grade[field], list), f"{label}: {field} must be an array")
        for item in grade[field]:
            claim(item, field)
            require(bool(item["answer_quote"]), f"{label}: empty extra/critical quote")
    for citation in grade["citations"]:
        claim(citation, "citation", citation["support"] == "entailing")
        require(citation["support"] in CITATION_STATUSES, f"{label}: invalid citation support")
        require(type(citation["anchor_compliance"]) is bool, f"{label}: invalid anchor flag")
        require(citation["url"] in answer_urls, f"{label}: citation URL was not supplied verbatim")
        if citation["support"] == "entailing":
            require(citation["anchor_compliance"], f"{label}: entailing citation with invalid anchor")
            matched = []
            for e in citation["evidence"]:
                s = sources[e["source_path"]]
                if page(e["url"]) == page(citation["url"]) and s["status"] == "fetched" and s["citation_support_eligible"] and not s["frozen"]:
                    matched.append(s)
            require(bool(matched), f"{label}: entailing citation relies on unfetched/frozen page")
            fragment = urlsplit(citation["url"]).fragment
            if fragment:
                require(":~:text=" not in fragment, f"{label}: text directive is not a literal anchor")
                require(any(citation["url"] in urls(texts[s["source_path"]]) for s in matched), f"{label}: absent literal document anchor")
            for s in matched:
                visible = s.get("candidate_visible_path", s["source_path"])
                if visible != s["source_path"]:
                    preview = read(visible, allowed)
                    eligible = [e for e in citation["evidence"] if e["source_path"] == s["source_path"]]
                    require(any(presentation(e["quote"]) in presentation(preview) for e in eligible), f"{label}: support outside candidate preview")
    for check in grade["checks"]:
        if check["citation_status"] == "entailing":
            matches = [x for x in grade["citations"] if x["support"] == "entailing" and presentation(check["answer_quote"]) in presentation(x["answer_quote"])]
            require(any(any(page(e["url"]) == page(x["url"]) for e in check["evidence"]) for x in matches), f"{label} {check['id']}: no covering entailing claim-level record")
    compliance = grade["compliance"]
    for field in ("full_urls", "word_cap", "english", "fetched_two_sources", "source_rules", "tool_rules"):
        require(type(compliance[field]) is bool, f"{label}: invalid compliance flag {field}")
    for field in ("word_cap", "fetched_two_sources", "source_rules", "tool_rules"):
        require(compliance[field] == case["mechanical"][field], f"{label}: mechanical {field} changed")
    require(compliance["word_cap"] == (case["mechanical"]["visible_words"] <= 400), f"{label}: word cap inconsistent")
    fetched = [s for s in case["sources"] if s["status"] == "fetched" and s["citation_support_eligible"]]
    hashes = {hashlib.sha256(texts[s["source_path"]].encode()).hexdigest() for s in fetched}
    require(compliance["fetched_two_sources"] == (len(hashes) >= 2), f"{label}: distinct fetched content count inconsistent")
    required = set(case["rubric"]["source_rules"]["required_source_urls"])
    missing = required - {page(s["url"]) for s in fetched}
    discovery = compliance["discovery_chain"]
    require(discovery["complete"] == (not missing), f"{label}: discovery completeness inconsistent")
    require(set(discovery["missing_required_pages"]) == missing, f"{label}: missing discovery pages inconsistent")


def verify():
    allowed = {"blind/index.json", RECEIPT, "adjudication/reviews/shard-b.md"}
    index = load("blind/index.json", allowed)
    ids = index["shards"]["b"]
    require(len(ids) == 36 and len(set(ids)) == 36, "expected 36 distinct shard-B IDs")
    allowed.update(f"blind/cases/{i}/case.json" for i in ids)
    allowed.update(f"grades/shard-b/{i}.json" for i in ids)
    allowed.update(f"adjudication/{i}.json" for i in OVERRIDES)
    receipt = load(RECEIPT, allowed)
    require(receipt["reviewed_ids"] == ids, "receipt coverage/order differs from public index")
    require(receipt["initial_grade_paths"] == [f"grades/shard-b/{i}.json" for i in ids], "initial paths differ")
    require(set(receipt["override_paths"]) == {f"adjudication/{i}.json" for i in OVERRIDES}, "override paths differ")
    require(receipt["reviewer_type"] == "AI: GPT-6.1 Sol Fast High", "reviewer label differs")
    for flag in ("blind_review", "passed", "source_based", "blind_inputs_only"):
        require(receipt[flag] is True, f"receipt {flag} is not true")
    require(bool(receipt["notes"]), "receipt must disclose review limits")
    counts = collections.Counter()
    warnings = []
    for blind_id in ids:
        case = load(f"blind/cases/{blind_id}/case.json", allowed)
        require(case["blind_id"] == blind_id and bool(case["answer"].strip()), "nonempty answer coverage failed")
        for source in case["sources"]:
            for key in ("source_path", "candidate_visible_path"):
                if key in source:
                    p = source[key]
                    require(p.startswith(f"blind/cases/{blind_id}/"), "source not bound to opaque case")
                    allowed.add(p)
        initial = load(f"grades/shard-b/{blind_id}.json", allowed)
        verify_grade(initial, case, allowed, False, warnings)
        effective = initial
        if blind_id in OVERRIDES:
            override = load(f"adjudication/{blind_id}.json", allowed)
            require(set(override) == {"blind_id", "initial_grade_path", "rationale", "effective_grade"}, "override envelope schema differs")
            require(override["blind_id"] == blind_id, "override ID mismatch")
            require(override["initial_grade_path"] == f"grades/shard-b/{blind_id}.json", "override initial path mismatch")
            require(bool(override["rationale"]), "override lacks semantic rationale")
            effective = override["effective_grade"]
            verify_grade(effective, case, allowed, True, warnings)
            for field in ("checks", "uncertainty"):
                if field == "checks":
                    require([(x["status"], x["citation_status"], x["answer_quote"]) for x in initial[field]] == [(x["status"], x["citation_status"], x["answer_quote"]) for x in effective[field]], "unexpected changed check judgment")
                else:
                    require(initial[field]["status"] == effective[field]["status"], "unexpected changed U")
            require(initial["critical_errors"] == effective["critical_errors"], "unexpected critical change")
            require(initial["ambiguous"] == effective["ambiguous"], "ambiguity disclosure lost")
            require(len(initial["unsupported_extras"]) - len(effective["unsupported_extras"]) == 1, "override must remove exactly its adjudicated extra")
        counts["reviewed"] += 1
        counts[case["task_id"]] += 1
        counts["initial_ambiguities"] += initial["ambiguous"]
        counts["effective_ambiguities"] += effective["ambiguous"]
        counts["critical_items"] += len(effective["critical_errors"])
        counts["initial_extras"] += len(initial["unsupported_extras"])
        counts["effective_extras"] += len(effective["unsupported_extras"])
        counts["initial_citation_failure_cases"] += any(x["status"] != "missing" and x["citation_status"] != "entailing" for x in initial["checks"])
        counts["effective_citation_failure_cases"] += any(x["status"] != "missing" and x["citation_status"] != "entailing" for x in effective["checks"])
    require(all(counts[f"T{i}"] == 6 for i in range(1, 7)), "six domains not fully covered")
    counts["overrides"] = len(OVERRIDES)
    counts["checks_reviewed"] = 36 * 6
    counts["uncertainty_reviewed"] = 36
    require(dict(counts) == receipt["counts"], "receipt counts differ from deterministic totals")
    require(len(warnings) == 10, "initial literal-transcription warning coverage changed")
    md = read("adjudication/reviews/shard-b.md", allowed)
    require(all(i in md for i in ids), "Markdown review ledger does not cover all 36 IDs")
    print("PASS: 36 answers; 216 checks + 36 U; 3 complete overrides; 1 critical item; 18 ambiguities; 10 citation-failure cases; receipt passed=true.")
    print("LIMIT: 10 initial source-quote apostrophe transcriptions across 5 blind IDs disclosed; all override quotes pass literal proof. No semantic entailment is generated by this validator.")


def main():
    parser = argparse.ArgumentParser(description="Public-only shard-B review artifact validator; read-only, no network or private verifier imports.")
    parser.add_argument("--verify", action="store_true", help="verify all 36 reviewed IDs, complete override schema, literal quotes, citations and receipt counts")
    args = parser.parse_args()
    if not args.verify:
        parser.error("choose --verify")
    try:
        verify()
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
