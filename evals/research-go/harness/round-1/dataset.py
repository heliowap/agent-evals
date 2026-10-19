#!/usr/bin/env python3
"""Prepare primary-source archives; verify saved evidence without network access.

prepare is a read-only public HTTP operation. finalize never fetches: it applies
the runner-owned extract_document/normalize_text contract to retained raw bodies.
No candidate inference, credentials, services, or freeze files are used here.
"""

import argparse
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset"
RESEARCH = ROOT / "research/tasks.md"
VERSION = 1
MAX_BODY = 2 * 1024 * 1024

# These are anchored regular expressions, also consumed by the runner. The
# narrow raw.githubusercontent rule deliberately does not permit floating main.
PATTERNS = {
    "T1": [r"https://docs\.github\.com/[^?#]*"],
    "T2": [r"https://nodejs\.org/download/release/v24\.21\.0/docs/api/[^?#]*",
           r"https://raw\.githubusercontent\.com/nodejs/node/v24\.21\.0/SECURITY\.md",
           r"https://github\.com/nodejs/node/(?:blob|tree)/v24\.21\.0(?:/[^?#]*)?"],
    "T3": [r"https://www\.postgresql\.org/docs/18/[^?#]*"],
    "T4": [r"https://developers\.cloudflare\.com/d1(?:/[^?#]*)?"],
    "T5": [r"https://docs\.docker\.com/[^?#]*",
           r"https://github\.com/docker/compose/releases(?:/[^?#]*)?"],
    "T6": [r"https://go\.dev/[^?#]*"],
}

MIRRORS = [
    ("DC-G-MD", "https://docs.docker.com/compose/how-tos/startup-order.md", "DC-G"),
    ("DC-S-MD", "https://docs.docker.com/reference/compose-file/services.md", "DC-S"),
    ("D1-R-MD", "https://developers.cloudflare.com/d1/best-practices/read-replication/index.md", "D1-R"),
    ("D1-D-MD", "https://developers.cloudflare.com/d1/worker-api/d1-database/index.md", "D1-D"),
]

CHAIN_SPECS = {
    "T1": [("GH-I", "GH-V"), ("GH-I", "GH-B"), ("GH-I", "GH-F")],
    "T2": [("N-P", "https://github.com/nodejs/node/blob/main/SECURITY.md")],
    "T3": [("PG-I", "PG-T"), ("PG-I", "PG-R")],
    "T4": [("D1-I", "D1-L"), ("D1-L", "D1-R"), ("D1-L", "D1-D")],
    "T5": [("DC-G", "DC-S")],
    "T6": [("GO-M", "GO-D")],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class BodyParser(HTMLParser):
    """Temporary whole-body extraction, preserving adjacent inline tokens.

    Delimit *block* elements, never every handle_data token. Inserting spaces at
    inline boundaries changes strings such as withSession() and broke the
    research audit. Links/anchors are collected independently from quote text.
    """

    BLOCKS = set("address article aside blockquote br dd div dl dt footer h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section table td th tr ul".split())
    HIDDEN = {"script", "style", "noscript", "svg"}

    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.parts = []
        self.anchors = set()
        self.links = set()
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("id", "name"):
            if attrs.get(key):
                self.anchors.add(attrs[key])
        if tag in {"a", "link"} and attrs.get("href"):
            self.links.add(urllib.parse.urljoin(self.url, attrs["href"]))
        if tag in self.HIDDEN:
            self.hidden += 1
        if not self.hidden and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.HIDDEN:
            self.hidden = max(0, self.hidden - 1)
        if not self.hidden and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def placeholder_normalize(text):
    text = html.unescape(text)
    # Retain link label adjacency, not the URL inserted into the middle of prose.
    text = re.sub(r"!?\[([^\]]*)\]\([^\s)]*(?:\s+\"[^\"]*\")?\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = text.replace("`", "").replace("**", "").replace("__", "")
    text = re.sub(r"\\([*_`\[\]<>])", r"\1", text)
    return " ".join(text.split())


def parse_body(raw, content_type, url):
    body = raw.decode("utf-8", errors="replace")
    if "html" in content_type:
        parser = BodyParser(url)
        parser.feed(body)
        return "".join(parser.parts), sorted(parser.anchors), sorted(parser.links)
    links = set(urllib.parse.urljoin(url, value) for value in
                re.findall(r"\]\((https?://[^\s)]+|/[^\s)]+)\)", body))
    links.update(re.findall(r"https://[^\s<>\"\)]+", body))
    # Markdown heading IDs are not substitutes for verified HTML fragment IDs.
    return body, [], sorted(links)


def placeholder_extract(raw, content_type, url):
    body, _, links = parse_body(raw, content_type, url)
    return body.strip() + ("\n\nLinks:\n" + "\n".join(links) if links else "")


def quote_normalize(text, normalize):
    """Match visible evidence, without changing whole-document/hash text.

    The shared normalizer is intentionally whitespace-only. Remove Markdown
    presentation before calling it, so linked labels remain adjacent to their
    surrounding characters. Protect code and escaped punctuation first: a
    literal glob or operator is content, not an emphasis delimiter.
    """
    text = html.unescape(text)
    literals = []

    def protect(value):
        literals.append(value)
        return f"\x00CODE{len(literals) - 1}\x00"

    text = re.sub(r"(`+)(.*?)\1", lambda match: protect(match.group(2)), text, flags=re.S)
    text = re.sub(r"\\([*_`\[\]<>])", lambda match: protect(match.group(1)), text)
    # A destination may contain parenthesized URL components; never insert a
    # separator or keep the destination inside the quoted prose.
    text = re.sub(r"!?\[([^\]]*)\]\((?:[^()\s]|\([^()\n]*\))*(?:\s+\"[^\"]*\")?\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?<!\w)(\*\*|__)(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", text)
    # Exclude path/glob boundaries and *.suffix from single-star emphasis.
    text = re.sub(r"(?<![\w/*_])([*_])(?=[^\s*/_.])(.+?)(?<![\s/])\1(?![\w/*_])", r"\2", text)
    text = re.sub(r"\x00CODE(\d+)\x00", lambda match: literals[int(match.group(1))], text)
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return normalize(text)


def shared_interfaces():
    path = ROOT / "webfetch.py"
    if not path.is_file():
        raise ValueError("Shared extraction unavailable: parent must run dataset.py finalize after P2.")
    spec = importlib.util.spec_from_file_location("dataset_shared_webfetch", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    old_bytecode = sys.dont_write_bytecode
    try:
        # P1 owns no root __pycache__ or runner files.
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old_bytecode
    extract = getattr(module, "extract_document", None)
    normalize = getattr(module, "normalize_text", None)
    if not callable(extract) or not callable(normalize):
        raise ValueError("webfetch.py lacks the contracted extract_document/normalize_text interfaces")
    return extract, normalize, sha(path.read_bytes())


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def source_plan(research):
    rows = re.findall(r"^\| ([A-Z0-9-]+) \| (T[1-6]) \| (https://[^ ]+) \|", research, re.M)
    if len(rows) != 18:
        raise ValueError("Research manifest must contain exactly 18 canonical bodies")
    result = [{"id": ident, "task_id": task, "url": url, "canonical_url": url,
               "kind": "canonical"} for ident, task, url in rows]
    by_id = {row["id"]: row for row in result}
    result += [{"id": ident, "task_id": by_id[parent]["task_id"], "url": url,
                "canonical_url": by_id[parent]["url"], "kind": "native_markdown"}
               for ident, url, parent in MIRRORS]
    return result


def quotations(text, sources):
    by_url = {row["url"]: row for row in sources if row["kind"] == "canonical"}
    pairs = re.findall(r"Source: (https://\S+)\n> ([^\n]+)", text)
    result = []
    for url, quote in pairs:
        base, fragment = urllib.parse.urldefrag(url)
        row = by_url[base]
        result.append({"url": url, "quote": quote, "archive_path": row.get("text_path"),
                       "source_id": row["id"], "anchor": fragment or None})
    return result


def task_artifacts(research, sources):
    common = section(research, "```text\n", "\n```")
    tasks, gold = [], {}
    by_id = {row["id"]: row for row in sources}
    blocks = re.split(r"(?m)^## (T[1-6]) — `([^`]+)`\n", research)[1:]
    if len(blocks) != 18:
        raise ValueError("Six stable task sections are required")
    for index in range(0, len(blocks), 3):
        ident, slug, block = blocks[index:index + 3]
        block = block.split("\n## Source manifest", 1)[0]
        decision = section(block, "### Exact decision prompt\n\n```text\n", "\n```")
        starts_text = section(block, "### Starting URLs\n", "### Six atomic scored checks")
        starts = re.findall(r"^- (https://\S+)", starts_text, re.M)
        title = re.search(r"\*\*Title/domain:\*\* ([^\n]+)", block).group(1)
        required = [row["url"] for row in sources if row["task_id"] == ident and row["kind"] == "canonical"]
        description = section(block, "**Required discovery/synthesis chain:** ", "\n\n**Archive/allowlist:")
        edges = []
        for parent, child in CHAIN_SPECS[ident]:
            edges.append({"from": by_id[parent]["url"],
                          "to": by_id[child]["url"] if child in by_id else child,
                          "relation": "documentation_link"})
        if ident == "T2":
            edges[0]["note"] = "Floating policy link is discovery evidence only; fetch the supplied v24.21.0 tag instead."
        tasks.append({"id": ident, "slug": slug, "title": title,
                      "prompt": common + "\n\n" + decision + "\n\nStarting URLs\n" + "\n".join("- " + url for url in starts),
                      "starting_urls": starts, "allowed_url_patterns": PATTERNS[ident],
                      "required_source_urls": required,
                      "discovery_chain": {"description": description, "edges": edges,
                                          "minimum_distinct_sources": len(required)}})
        factual = section(block, "### Six atomic scored checks\n", "### U —")
        checks = []
        pieces = re.split(r"(?m)^\*\*(C[1-6]) — ([^\n]+?)\.\*\* ", factual)[1:]
        if len(pieces) != 18:
            raise ValueError(f"{ident}: six atomic C1..C6 checks required")
        for pos in range(0, len(pieces), 3):
            check_id, requirement, body = pieces[pos:pos + 3]
            variants = body.split("\n\nSource:", 1)[0].strip()
            # Keep all wording, including permissible alternatives and omissions;
            # do not expand these six checks into extra factual bundles.
            accepted = re.search(r"(?:^| )S: (.*?)(?= X:|$)", variants).group(1)
            rejected = re.search(r"(?:^| )X: (.*)", variants)
            checks.append({"id": check_id, "requirement": requirement,
                           "accepted": [accepted], "contradicted": [rejected.group(1)] if rejected else [],
                           "rubric_text": variants, "source_evidence": quotations(body, sources)})
        uncertainty_text = section(block, "### U —", "**Critical mistakes:**")
        uncertainty_title, criteria = uncertainty_text.split("\n\n", 1)
        pass_text = section(criteria, "Pass: ", "\n\nSource:")
        fail_match = re.search(r"(?m)^Fail: (.*)", criteria)
        omit = "Absent, generic uncertainty without the task-specific limiting reason and useful next evidence target."
        fail = "Assert the unsupported guarantee that the pass criterion explicitly declines."
        if fail_match:
            split = fail_match.group(1).split(" Omit: ", 1)
            fail = split[0]
            if len(split) == 2:
                omit = split[1]
        critical = section(block, "**Critical mistakes:** ", "\n\n**Required discovery/synthesis chain:")
        source_rules = section(block, "**Archive/allowlist:** ", "\n\n") if "\n\n" in block.split("**Archive/allowlist:** ", 1)[1] else block.split("**Archive/allowlist:** ", 1)[1].strip()
        gold[ident] = {"checks": checks,
                       "uncertainty": {"id": "U", "requirement": uncertainty_title,
                                       "pass": pass_text, "omit": omit, "fail": fail,
                                       "source_evidence": quotations(criteria, sources)},
                       "critical_errors": [part.strip() for part in critical.split("; ")],
                       "critical_errors_text": critical,
                       "source_rules": {"description": source_rules,
                                        "allowed_url_patterns": PATTERNS[ident],
                                        "required_source_urls": required,
                                        "minimum_distinct_sources": len(required),
                                        "minimum_answer_bearing_sources": [3, 2, 2, 2, 2, 3][int(ident[1]) - 1],
                                        "discovery_chain": tasks[-1]["discovery_chain"]}}
    all_quotes = [e for task in gold.values() for check in task["checks"] for e in check["source_evidence"]]
    all_quotes += [e for task in gold.values() for e in task["uncertainty"]["source_evidence"]]
    if len(all_quotes) != 53:
        raise ValueError(f"Expected 53 exact research quotations, got {len(all_quotes)}")
    return tasks, {"version": VERSION, "tasks": gold}


def allowed(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443):
        return False
    clean = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return any(re.fullmatch(pattern, clean) for patterns in PATTERNS.values() for pattern in patterns)


class ArchiveRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.redirects = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError(f"Archive redirect outside official families: {newurl}")
        self.redirects.append({"from": req.full_url, "to": newurl, "status": code})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_source(plan):
    row = dict(plan)
    row.update({"final_url": None, "status": None, "content_type": None,
                "raw_path": None, "text_path": None, "raw_sha256": None, "text_sha256": None,
                "raw_bytes": None, "text_bytes": None, "anchors": [], "links": [],
                "retrieved_utc": utc(), "redirects": [], "error": None})
    redirects = ArchiveRedirects()
    try:
        if not allowed(row["url"]):
            raise ValueError("Archive URL is outside official families")
        opener = urllib.request.build_opener(redirects)
        req = urllib.request.Request(row["url"], headers={"User-Agent": "researcher-eval-source-archive/1", "Accept": "*/*", "Accept-Encoding": "identity"})
        with opener.open(req, timeout=20) as response:
            row.update({"status": response.status, "final_url": response.geturl(),
                        "content_type": response.headers.get("Content-Type", "")})
            raw = response.read(MAX_BODY + 1)
        if row["status"] != 200:
            raise ValueError(f"Non-page HTTP status {row['status']}")
        if len(raw) > MAX_BODY:
            raise ValueError("Raw body exceeds 2 MiB archive bound")
        content_type = row["content_type"]
        suffix = ".html" if "html" in content_type else ".md" if ("markdown" in content_type or row["url"].endswith(".md")) else ".txt"
        raw_path = DATA / "sources" / (row["id"] + suffix)
        text_path = DATA / "sources" / (row["id"] + ".extracted.txt")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(raw)
        text = placeholder_extract(raw, content_type, row["final_url"])
        encoded = text.encode("utf-8")
        text_path.write_bytes(encoded)
        _, anchors, links = parse_body(raw, content_type, row["final_url"])
        row.update({"raw_path": raw_path.relative_to(ROOT).as_posix(),
                    "text_path": text_path.relative_to(ROOT).as_posix(),
                    "raw_sha256": sha(raw), "text_sha256": sha(encoded),
                    "raw_bytes": len(raw), "text_bytes": len(encoded), "anchors": anchors, "links": links,
                    "normalized_sha256": sha(placeholder_normalize(text).encode("utf-8")),
                    "extraction": "temporary-whole-body-v1"})
    except urllib.error.HTTPError as exc:
        row.update({"status": exc.code, "final_url": exc.geturl(),
                    "content_type": exc.headers.get("Content-Type", ""), "error": str(exc)})
        # Preserve status/failure, never archive an HTTP error as a source page.
    except (OSError, ValueError) as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["redirects"] = redirects.redirects
    row["ended_utc"] = utc()
    return row


def prepare():
    research = RESEARCH.read_text(encoding="utf-8")
    plan = source_plan(research)
    manifest_path = DATA / "sources.json"
    previous = read_json(manifest_path) if manifest_path.exists() else []
    rows = {row["id"]: row for row in previous}
    # Incremental recovery is source fetching, not candidate retries. Every
    # failed attempt remains in the append-only source-attempts log.
    DATA.mkdir(parents=True, exist_ok=True)
    for source in plan:
        if source["id"] in rows and not rows[source["id"]].get("error"):
            continue
        result = fetch_source(source)
        rows[source["id"]] = result
        with (DATA / "source-attempts.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(result, ensure_ascii=False) + "\n")
        write_json(manifest_path, [rows.get(item["id"], item) for item in plan])
        print(f"{result['id']}: {result['status']} {result.get('raw_bytes')} bytes" + (f" ERROR {result['error']}" if result["error"] else ""))
    sources = [rows[item["id"]] for item in plan]
    tasks, gold = task_artifacts(research, sources)
    write_json(DATA / "tasks.json", tasks)
    write_json(DATA / "gold.json", gold)
    write_json(DATA / "archive-state.json", {"version": VERSION, "research_sha256": sha(RESEARCH.read_bytes()),
               "extraction": "temporary-whole-body-v1", "shared_extraction_finalized": False,
               "finalize_command": f"python3 {ROOT / 'dataset.py'} finalize",
               "created_utc": utc()})
    return verify(save_report=True)


def all_evidence(gold):
    return [e for task in gold["tasks"].values()
            for bundle in task["checks"] + [task["uncertainty"]]
            for e in bundle["source_evidence"]]


def match_link(links, target, source_by_url):
    target, _ = urllib.parse.urldefrag(target)
    for link in links:
        base, _ = urllib.parse.urldefrag(link)
        if base == target:
            return link
        row = source_by_url.get(base)
        if row and row["canonical_url"] == target:
            return link
    return None


def checks_saved(require_finalized=False):
    research = RESEARCH.read_text(encoding="utf-8")
    sources = read_json(DATA / "sources.json")
    tasks = read_json(DATA / "tasks.json")
    gold = read_json(DATA / "gold.json")
    state = read_json(DATA / "archive-state.json")
    expected_plan = source_plan(research)
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(state["research_sha256"] == sha(RESEARCH.read_bytes()), "Research changed since archive preparation")
    check(len(sources) == 22 and len({r['id'] for r in sources}) == 22, "Expected 18 canonical bodies and four distinct native mirrors")
    check([{k: row.get(k) for k in ("id", "task_id", "url", "canonical_url", "kind")} for row in sources] == expected_plan, "Source plan differs from exact research manifest")
    expected_tasks, expected_gold = task_artifacts(research, sources)
    check(tasks == expected_tasks, "Six exact public common+decision+starting-URL tasks differ from research")
    check(gold == expected_gold, "Separate 36-check/six-uncertainty gold differs from research")
    check([t["id"] for t in tasks] == [f"T{i}" for i in range(1, 7)], "Stable task IDs/order differ")
    check([len(t["required_source_urls"]) for t in tasks] == [4, 2, 3, 4, 2, 3], "Required-source cardinalities differ")
    check("v24.21.0" in tasks[1]["prompt"] and "PostgreSQL 18" in tasks[2]["prompt"], "Fixed Node/PostgreSQL version premise changed")
    for task in tasks:
        check("at most 8 inference steps" in task["prompt"] and "at most 400 visible words" in task["prompt"], f"{task['id']}: instruction caps missing")
        check("source_evidence" not in task and "checks" not in task and "uncertainty" not in task, f"{task['id']}: gold leaked into public object")
    finalized = state.get("shared_extraction_finalized", False)
    extract, normalize = placeholder_extract, placeholder_normalize
    if finalized:
        extract, normalize, shared_hash = shared_interfaces()
        check(state.get("webfetch_sha256") == shared_hash, "Shared extractor changed: run finalize again before freeze")
    if require_finalized:
        check(finalized, "Shared-extraction finalization is pending")
    texts, parsings = {}, {}
    attempts = [json.loads(line) for line in (DATA / "source-attempts.jsonl").read_text(encoding="utf-8").splitlines()]
    latest_attempts = {attempt["id"]: attempt for attempt in attempts}
    for row in sources:
        ident = row["id"]
        attempt = latest_attempts.get(ident, {})
        for field in ("url", "canonical_url", "final_url", "status", "content_type", "raw_path",
                      "raw_sha256", "raw_bytes", "anchors", "links", "retrieved_utc", "redirects", "error"):
            check(row.get(field) == attempt.get(field), f"{ident}: HTTP archive metadata differs from retained attempt: {field}")
        check(row.get("status") == 200 and not row.get("error"), f"{ident}: archive fetch failed: {row.get('error')}")
        check(bool(row.get("raw_path") and row.get("text_path")), f"{ident}: missing body paths")
        if not row.get("raw_path") or not row.get("text_path"):
            continue
        raw_path, text_path = ROOT / row["raw_path"], ROOT / row["text_path"]
        if not (raw_path.resolve().is_relative_to((DATA / 'sources').resolve()) and text_path.resolve().is_relative_to((DATA / 'sources').resolve())):
            raise ValueError(f"{ident}: source path outside owned archive")
        raw, encoded = raw_path.read_bytes(), text_path.read_bytes()
        check(len(raw) == row["raw_bytes"] and sha(raw) == row["raw_sha256"], f"{ident}: raw size/hash mismatch")
        check(len(encoded) == row["text_bytes"] and sha(encoded) == row["text_sha256"], f"{ident}: extracted size/hash mismatch")
        expected = extract(raw, row["content_type"], row["final_url"])
        check(expected.encode("utf-8") == encoded, f"{ident}: extracted body is not reproducible")
        text = encoded.decode("utf-8")
        check(sha(normalize(text).encode("utf-8")) == row.get("normalized_sha256"), f"{ident}: normalized main-content hash mismatch")
        parsed = parse_body(raw, row["content_type"], row["final_url"])
        parsings[ident] = parsed
        check(row["anchors"] == parsed[1] and row["links"] == parsed[2], f"{ident}: anchors/links not reproducible from raw body")
        check(allowed(row["url"]) and allowed(row["final_url"]), f"{ident}: URL outside official families")
        for redirect in row["redirects"]:
            check(allowed(redirect["from"]) and allowed(redirect["to"]), f"{ident}: unofficial redirect")
        check(bool(row["retrieved_utc"]) and bool(row["content_type"]), f"{ident}: missing HTTP metadata")
        texts[ident] = quote_normalize(text, normalize)
    by_id = {row["id"]: row for row in sources}
    by_url = {row["url"]: row for row in sources}
    evidence = all_evidence(gold)
    check(len(evidence) == 53, "Expected 53 research source quotations")
    anchor_count = 0
    for entry in evidence:
        ident = entry["source_id"]
        check(quote_normalize(entry["quote"], normalize) in texts.get(ident, ""), f"{ident}: unmatched quote: {entry['quote']}")
        check(entry["archive_path"] == by_id[ident]["text_path"], f"{ident}: incorrect evidence archive path")
        if entry["anchor"]:
            anchor_count += 1
            check(entry["anchor"] in by_id[ident]["anchors"], f"{ident}: missing HTML anchor {entry['anchor']}")
    chain_records = []
    for task in tasks:
        for edge in task["discovery_chain"]["edges"]:
            parent = by_url[edge["from"]]
            link = match_link(parent["links"], edge["to"], by_url)
            check(bool(link), f"{task['id']}: actual discovery link missing: {edge['from']} -> {edge['to']}")
            chain_records.append({"task_id": task["id"], **edge, "actual_link": link})
    # Short version quote is ambiguous globally: prove it occurs in the
    # depends_on required bullet's complete paragraph, not env_file.required.
    compose = parsings.get("DC-S", ("", [], []))[0]
    marker = re.search(r"(?:^|\n)\s*required\s*:\s*", compose)
    context = ""
    if marker:
        tail = compose[marker.start():]
        context = tail.split("\n\n", 1)[0].strip()
        # HTML block boundaries can surround inline version badges; keep the
        # entire required bullet up to the next configuration block.
        if "2.20.0" not in context:
            context = tail.split("\n\n", 3)[0:3]
            context = "\n\n".join(context).strip()
    check("required" in context and "2.20.0" in context and "warns" in context,
          "Compose required:false 2.20.0 full paragraph context not verified")
    check("The model does not inherit to a worker thread." in texts.get("N-P", "") and
          "Workers inherit the permission restrictions of their parent process." in texts.get("N-S", ""),
          "Pinned opposing Node worker statements not both archived")
    check("v24.21.0" in parsings.get("N-P", ("", [], []))[0], "Node HTML version header missing")
    mirrors = []
    for row in sources:
        if row["kind"] != "native_markdown":
            continue
        canonical = by_url[row["canonical_url"]]
        canonical_quotes = [e for e in evidence if e["source_id"] == canonical["id"]]
        for entry in canonical_quotes:
            check(quote_normalize(entry["quote"], normalize) in texts.get(row["id"], ""), f"{row['id']}: mirror quote mismatch: {entry['quote']}")
        # Whole generic bodies are compared honestly, not claimed byte-equal.
        mirrors.append({"id": row["id"], "canonical_id": canonical["id"],
                        "raw_byte_equal": row.get("raw_sha256") == canonical.get("raw_sha256"),
                        "normalized_whole_body_equal": row.get("normalized_sha256") == canonical.get("normalized_sha256"),
                        "mirror_normalized_sha256": row.get("normalized_sha256"),
                        "canonical_normalized_sha256": canonical.get("normalized_sha256"),
                        "verified_quote_count": len(canonical_quotes),
                        "equivalence_scope": "Canonical mapping and all task evidence quotes; not a claim of identical whole bodies."})
    return {"version": VERSION, "verified_utc": utc(), "structurally_verified": not errors,
            "shared_extraction_finalized": finalized, "canonical_bodies": 18, "native_markdown_mirrors": 4,
            "tasks": 6, "atomic_checks": 36, "uncertainty_keys": 6, "source_quotations": len(evidence),
            "html_anchor_references": anchor_count, "discovery_links": chain_records,
            "compose_required_context": {"url": by_id['DC-S']['url'] + "#depends_on", "paragraph": context},
            "mirror_comparisons": mirrors, "errors": errors,
            "pending_finalize_command": None if finalized else f"python3 {ROOT / 'dataset.py'} finalize"}


def verify(require_finalized=False, save_report=False):
    report = checks_saved(require_finalized)
    # CLI verification is genuinely saved-only and does not mutate the source
    # package after freeze. prepare/finalize retain their diagnostic snapshot.
    if save_report:
        write_json(DATA / "verification.json", report)
    for error in report["errors"]:
        print("FAIL:", error)
    if report["errors"]:
        print(f"FAIL: {len(report['errors'])} saved-evidence errors")
        return 1
    print("PASS: 6 exact tasks; 36 atomic checks; 6 uncertainty keys")
    print(f"PASS: 18 canonical bodies + 4 native Markdown mirrors; 53 quotes; {report['html_anchor_references']} HTML anchor references; {len(report['discovery_links'])} actual discovery links")
    print("PASS: Compose required:false 2.20.0 full paragraph; opposing fixed-version Node worker statements")
    if report["shared_extraction_finalized"]:
        print("PASS: shared webfetch.extract_document/normalize_text finalization")
    else:
        print("STRUCTURAL PASS ONLY: shared-extraction finalization PENDING before freeze/inference")
        print("Pending:", report["pending_finalize_command"])
    return 0


def finalize():
    extract, normalize, shared_hash = shared_interfaces()
    sources = read_json(DATA / "sources.json")
    for row in sources:
        if row.get("error") or row.get("status") != 200:
            raise ValueError(f"Cannot finalize unsuccessful archive row {row['id']}")
        raw = (ROOT / row["raw_path"]).read_bytes()
        if sha(raw) != row["raw_sha256"]:
            raise ValueError(f"Raw archive changed: {row['id']}")
        text = extract(raw, row["content_type"], row["final_url"])
        encoded = text.encode("utf-8")
        (ROOT / row["text_path"]).write_bytes(encoded)
        row.update({"text_sha256": sha(encoded), "text_bytes": len(encoded),
                    "normalized_sha256": sha(normalize(text).encode("utf-8")),
                    "extraction": "webfetch.extract_document"})
    write_json(DATA / "sources.json", sources)
    state = read_json(DATA / "archive-state.json")
    state.update({"shared_extraction_finalized": True, "extraction": "webfetch.extract_document",
                  "webfetch_sha256": shared_hash, "finalized_utc": utc()})
    write_json(DATA / "archive-state.json", state)
    return verify(require_finalized=True, save_report=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="Archive the exact public official bodies; retain failed attempts; create public tasks and private gold")
    sub.add_parser("finalize", help="Offline: apply shared runner extraction to retained bodies, then verify; required before freeze")
    verify_parser = sub.add_parser("verify", help="Offline: verify exact tasks, sources, all quotes, anchors and discovery links; report finalization separately")
    verify_parser.add_argument("--require-finalized", action="store_true", help="Also fail if shared runner extraction is not finalized")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            return prepare()
        if args.command == "finalize":
            return finalize()
        return verify(args.require_finalized)
    except (ValueError, OSError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
