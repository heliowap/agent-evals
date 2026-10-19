#!/usr/bin/env python3
"""Saved-only evidence audit. See tests/audit/README.md for evidence extensions.

Quote membership is an integrity check, never a semantic entailment judgment.
This module does not import the runner, webfetch, or any candidate code.
"""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, unquote, urlunsplit

SEED = 20261007021014
MODELS = {"deepseek": "deepseek-v4.1-flash", "glm": "glm-5.3-flash"}
CONFIGS = {f"{family}-{effort}": (model, effort)
           for family, model in MODELS.items() for effort in ("low", "high", "max")}
TASKS = {f"T{i}" for i in range(1, 7)}
UNRUN = {"not_run_access_gate", "not_run", "not_run_stop", "not_run_source_drift",
          "not_run_first_failure", "not_run_access_denial", "not_run_harness_failure",
          "not_run_compatibility_block"}
TERMINAL = {"completed", "timeout", "provider_error", "access_gate_error", "tool_error",
             "harness_error", "step_limit", "incomplete", "retry_stopped", "source_drift", "compatibility_error"}
BLOCKED = {"access_blocked", "compatibility_blocked"}
CREDENTIAL_PATTERN = r'(?i)bearer\s+[A-Za-z0-9._-]{8,}|sk-[A-Za-z0-9_-]{12,}|"(?:api_key|authorization)"\s*:'
PUBLIC_FIELD_SHA256 = "81d54facb40f6897ee428462a51dbaa0fde638e5b023f15811d05d66923b4e19"
PUBLIC_CANONICAL = "https://developers.cloudflare.com/d1/best-practices/read-replication/"
PUBLIC_URLS = {PUBLIC_CANONICAL, PUBLIC_CANONICAL + "index.md"}
VISIBLE_WORD_RULE = ("all assistant content turns; remove Markdown link destinations and bare HTTPS URLs, "
                     "remove Markdown marker characters; whitespace-delimited visible tokens; do not exclude "
                     "code or commentary; reasoning/tool text excluded")
USAGE_FIELDS = ("prompt_tokens", "completion_tokens", "reasoning_tokens", "cache_read_tokens",
                "cache_write_tokens", "uncached_input_tokens", "non_reasoning_output_tokens",
                "reported_cost")


class AuditError(ValueError):
    """An explicit missing stage, invalid schema, or contradictory saved evidence."""


def require(condition, message):
    if not condition:
        raise AuditError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_digest(mapping):
    """Seal the private identity join without the later unblinding timestamp."""
    return hashlib.sha256(json.dumps({"mapping": mapping["mapping"], "sealed_hashes": mapping["sealed_hashes"]},
                                    sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def normalized(text):
    """Evidence presentation only; never applied to saved bodies or hashes.

    Preserve code/globs/operators and escaped punctuation before removing paired
    Markdown presentation. Link labels keep their original character adjacency.
    Words, case, negation, versions and literal code are not rewritten.
    """
    text = html.unescape(text)
    literals = []
    def stash(value):
        literals.append(value)
        return f"\x00LITERAL{len(literals)-1}\x00"
    text = re.sub(r"(`+)(.*?)\1", lambda m: stash(m[2]), text, flags=re.S)
    text = re.sub(r"\\([*_`\[\]<>])", lambda m: stash(m[1]), text)
    text = re.sub(r"!?\[([^\]]*)\]\((?:[^()\s]|\([^()\n]*\))*(?:\s+\"[^\"]*\")?\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?<!\w)(\*\*|__)(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", text)
    text = re.sub(r"(?<![\w/*_])([*_])(?=[^\s*/_.])(.+?)(?<![\s/])\1(?![\w/*_])", r"\2", text)
    text = re.sub(r"\x00LITERAL(\d+)\x00", lambda m: literals[int(m[1])], text)
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return " ".join(text.split())


def utc(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None, "UTC timestamp has no timezone")
        require(result.utcoffset().total_seconds() == 0, "timestamp must be UTC")
        return result
    except (TypeError, AttributeError, ValueError) as exc:
        raise AuditError(f"invalid UTC timestamp: {value!r}") from exc


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def visible_words(text):
    """Independent implementation of the frozen Markdown visible-word definition."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https://\S+", "", text)
    text = re.sub(r"[`*_#>|~]", "", text)
    return len(text.split())


def frozen_tool_scope(source):
    """Read the literal frozen catalog policy without executing candidate code."""
    tree = ast.parse(source)
    assignments = [n.value for n in tree.body if isinstance(n, ast.Assign) and
                   any(isinstance(t, ast.Name) and t.id == "ALLOWLIST" for t in n.targets)]
    require(len(assignments) == 1, "frozen: missing/ambiguous literal webfetch ALLOWLIST")
    try:
        scope = ast.literal_eval(assignments[0])
    except (ValueError, TypeError) as exc:
        raise AuditError("frozen: webfetch ALLOWLIST is not literal") from exc
    require(isinstance(scope, dict) and set(scope) == TASKS, "frozen: webfetch scope must cover six tasks")
    for entries in scope.values():
        require(isinstance(entries, list) and entries, "frozen: missing tool host/path scope")
        for entry in entries:
            require(isinstance(entry, (tuple, list)) and len(entry) == 2 and all(isinstance(v, str) for v in entry),
                    "frozen: invalid tool host/path scope")
            re.compile(entry[1])
    return scope


def official_url(url, task, scope):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or
            parsed.password is not None or parsed.query or "\\" in url or any(ord(c) < 33 for c in url)):
        return False
    try:
        if parsed.port not in (None, 443):
            return False
    except ValueError:
        return False
    decoded = unquote(parsed.path)
    if "%" in decoded or "\\" in decoded or any(s in {".", ".."} for s in decoded.split("/")):
        return False
    clean = urlunsplit(("https", parsed.hostname, parsed.path or "/", "", ""))
    return (any(parsed.hostname == host and re.fullmatch(pattern, decoded) for host, pattern in scope[task["id"]]) and
            any(re.fullmatch(pattern, clean) for pattern in task["allowed_url_patterns"]))


def saved_access_denial(status, payload):
    """Independent saved HTTP/native-payload access classification, no probe."""
    if not isinstance(status, int) or isinstance(status, bool):
        return False
    if status in (401, 403):
        return True
    error = payload.get("error", payload) if isinstance(payload, dict) else payload
    text = json.dumps(error).lower()
    return status >= 400 and any(term in text for term in
        ("global regions", "privacy settings", "region", "entitlement", "unauthorized",
          "invalid api key", "subscription", "authentication"))


def saved_parameter_denial(status, payload):
    """Specific native parameter errors, including JSON embedded in error strings.

    A generic invalid_request_error or HTTP 400 alone is not compatibility proof.
    No runner classification/exception text is used as evidence.
    """
    if not isinstance(status, int) or isinstance(status, bool) or status < 400:
        return False
    def parts(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from parts(item)
        elif isinstance(value, list):
            for item in value:
                yield from parts(item)
        elif isinstance(value, str):
            yield value.lower()
            try:
                embedded = json.loads(value)
            except ValueError:
                return
            if isinstance(embedded, (dict, list)):
                yield from parts(embedded)
    error = payload.get("error", payload) if isinstance(payload, dict) else payload
    for text in parts(error):
        if re.search(r'\b(?:unknown|unsupported|unrecognized|unexpected|unrecognised)[_ -]+(?:request[_ -]+)?(?:field|parameter|param|argument)(?:[_ -]+error)?\b', text):
            return True
        if re.search(r'\b(?:field|parameter|param|argument)\b.{0,100}\b(?:not supported|unsupported|unknown|unrecognized|unrecognised|not permitted|not allowed)\b', text):
            return True
        if re.search(r'\binvalid[_ -]+request[_ -]+(?:parameter|param|field|argument)\b', text):
            return True
        if re.search(r'\b(?:thinking|reasoning_effort)\b.{0,80}\b(?:not supported|unsupported|unknown|not allowed)\b', text):
            return True
    return False


def public_matches(text):
    matches = list(re.finditer(CREDENTIAL_PATTERN, text))
    return bool(matches) and all(hashlib.sha256(m[0].encode()).hexdigest() == PUBLIC_FIELD_SHA256 for m in matches)


class Auditor:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.stage = "frozen"
        self.records = []
        self.effective = {}

    def path(self, name):
        require(isinstance(name, str) and name and not Path(name).is_absolute(),
                f"{self.stage}: artifact path must be relative: {name!r}")
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root), f"{self.stage}: artifact escapes root: {name}")
        return path

    def read(self, name):
        path = self.path(name)
        require(path.is_file(), f"missing {self.stage} stage artifact: {name}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise AuditError(f"{self.stage}: invalid JSON schema: {name}: {exc}") from exc

    def text(self, name):
        path = self.path(name)
        require(path.is_file(), f"missing {self.stage} stage artifact: {name}")
        return path.read_text(encoding="utf-8")

    def native_response(self, request):
        """Read actual bytes; non-JSON HTTP errors get a local classification view.

        Never persist the wrapper or add usage. Successful inference must still
        supply valid native JSON. Root JSON values are retained as-is.
        """
        name = request["response_path"]
        path = self.path(name)
        require(path.is_file(), f"missing {self.stage} stage artifact: {name}")
        raw = path.read_bytes()
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            status = request["http_status"]
            if isinstance(status, int) and not isinstance(status, bool) and status >= 400:
                return {"error": {"message": raw.decode("utf-8", errors="replace")}}
            raise AuditError(f"{self.stage}: invalid JSON native response: {name}: {exc}") from exc

    def keys(self, obj, names, label):
        require(isinstance(obj, dict), f"{self.stage}: {label} must be an object")
        require(set(names) <= obj.keys(), f"{self.stage}: {label} missing fields {sorted(set(names)-obj.keys())}")

    def hashed(self, name, expected):
        path = self.path(name)
        require(path.is_file(), f"missing {self.stage} stage artifact: {name}")
        require(digest(path) == expected, f"{self.stage}: changed hash: {name}")

    def ledger(self):
        name = "execution/post-starts.jsonl"
        path = self.path(name)
        if not path.exists():
            return []
        try:
            rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        except ValueError as exc:
            raise AuditError("collected: malformed POST-start ledger") from exc
        for row in rows:
            self.keys(row, ("case_id", "step", "request_path", "started_utc"), "POST start")
        return rows

    def request_artifacts(self):
        """Identify outbound bodies by saved schema, never an incidental filename."""
        result = set()
        for path in self.root.glob("execution/**/*.json"):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError):
                continue  # Linked response/body validation handles malformed required artifacts.
            if isinstance(obj, dict) and "messages" in obj and ("model" in obj or "reasoning_effort" in obj):
                result.add(str(path.relative_to(self.root)))
        return result

    def canonical(self, url):
        base = url.split("#")[0]
        return next((s["canonical_url"].split("#")[0] for s in self.sources
                     if base in (s["url"].split("#")[0], s["final_url"].split("#")[0], s["canonical_url"].split("#")[0])), base)

    def allowed_url(self, url, task_id):
        return official_url(url, self.tasks[task_id], self.tool_scope)

    def fetched_pages(self, record):
        return {self.canonical(f["final_url"]) for f in record["fetches"]
                if f["status"] in {"ok", 200} and not f["error"] and f["text_path"] and f["model_text_path"] and
                self.allowed_url(f["final_url"], record["task_id"])}

    def mechanical_compliance(self, record):
        """Reconstruct judgments from native calls and ALL fetches, including denials."""
        history = self.read(record["history_path"]) if record["history_path"] else []
        calls = []
        tool_rules = len(record["fetches"]) <= 32 and record["inference_steps"] <= 8
        for message in history:
            if message.get("role") != "assistant":
                continue
            batch = message.get("tool_calls") or []
            if not isinstance(batch, list):
                tool_rules = False
                continue
            calls.extend(batch)
        tool_rules = tool_rules and len(calls) <= 32
        for call in calls:
            try:
                args = json.loads(call["function"]["arguments"])
                valid = (call.get("type") == "function" and call["function"]["name"] == "webfetch" and
                         isinstance(args, dict) and set(args) == {"url"} and isinstance(args["url"], str))
            except (ValueError, KeyError, TypeError, AttributeError):
                valid = False
            tool_rules = tool_rules and valid
        if record["inference_steps"] == 8 and record["requests"]:
            request = record["requests"][-1]
            path = request["response_path"]
            if path:
                native = self.native_response(request)
                choices = native.get("choices", []) if isinstance(native, dict) else []
                tool_rules = tool_rules and not any(c.get("message", {}).get("tool_calls") for c in choices)
        source_rules = True
        groups = []
        for fetch in record["fetches"]:
            urls = [fetch["requested_url"]]
            if fetch["final_url"]:
                urls.append(fetch["final_url"])
            for redirect in fetch["redirects"]:
                urls.extend([redirect["from"], redirect["to"]] if isinstance(redirect, dict) else [redirect])
            source_rules = source_rules and all(self.allowed_url(u, record["task_id"]) for u in urls)
            if (fetch["status"] in {"ok", 200} and not fetch["error"] and fetch["text_path"] and
                    fetch["model_text_path"] and self.allowed_url(fetch["final_url"], record["task_id"])):
                identities = {("url", self.canonical(fetch["final_url"])), ("text", fetch["text_sha256"])}
                # Union transitively on canonical aliases OR identical full extracted content.
                touching = [g for g in groups if g & identities]
                groups = [g for g in groups if not g & identities]
                groups.append(identities.union(*touching))
        return {"word_cap": record["visible_words"] <= 400, "source_rules": bool(source_rules),
                "tool_rules": bool(tool_rules), "fetched_two_sources": len(groups) >= 2,
                "distinct_fetched_pages": len(groups), "requested_tool_calls": len(calls)}

    def anchor_exists(self, url, record):
        anchor = unquote(urlsplit(url).fragment)
        if not anchor:
            return True
        canonical = self.canonical(url)
        for fetch in record["fetches"]:
            if fetch["final_url"] and self.canonical(fetch["final_url"]) == canonical and fetch["status"] in {"ok", 200}:
                for name in ("text_path", "raw_path"):
                    if fetch[name]:
                        text = self.path(fetch[name]).read_bytes().decode("utf-8", errors="replace")
                        if (re.search(r"(?:id|name)=[\"']" + re.escape(anchor) + r"[\"']", text) or
                                re.search(r"\]\([^\s)]*#" + re.escape(anchor) + r"\)", text)):
                            return True
        return any(self.canonical(s["url"]) == canonical and anchor in s["anchors"] for s in self.sources)

    def frozen(self):
        self.stage = "frozen"
        self.scope = self.read("scope.json")
        require(self.scope.get("models") == list(MODELS.values()) and
                self.scope.get("price_in_decision") is False and
                self.scope.get("planned_research_runs") == 72 and self.scope.get("prior_results_in_ranking") is False,
                "frozen: wrong study scope")
        restart = self.read("restart.json")
        require(restart.get("authorized_by_user") is True and restart.get("new_planned_cases") == 72 and
                restart.get("prior_cases_in_new_ranking") is False and
                restart.get("runtime_root") == self.scope["runtime_root"], "frozen: wrong restart scope")
        self.freeze = self.read("freeze.json")
        self.keys(self.freeze, ("version", "created_utc", "files", "schedule_sha256",
                                "no_candidate_calls_before_seal"), "freeze")
        seal_time = utc(self.freeze["created_utc"])
        require(self.freeze["no_candidate_calls_before_seal"] is True,
                "frozen: pre-seal calls not excluded")
        files = self.freeze["files"]
        require(isinstance(files, dict), "frozen: files must be a hash map")
        required = {"scope.json", "plan.md", "contracts.md", "restart.json", "dataset.py", "runner.py", "webfetch.py",
                    "verify.py", "analysis.py", "protocol.json", "system.txt", "tools.json", "schedule.json",
                    "dataset/tasks.json", "dataset/gold.json", "dataset/sources.json", "preflight/workflow.json"}
        # Discover local code/tests and frozen source/API archives, not generated results.
        for pattern in ("*.py", "tests/**/*.py", "dataset/**/*", "api-evidence/**/*"):
            required.update(str(p.relative_to(self.root)) for p in self.root.glob(pattern)
                            if p.is_file() and "__pycache__" not in p.parts)
        require(required <= files.keys(), f"frozen: uncovered immutable files: {sorted(required-files.keys())}")
        require(any(p.startswith("api-evidence/") for p in files), "frozen: missing API evidence")
        for name, sha in files.items():
            require(not name.startswith(("execution/", "grades/", "analysis/", "private/", "blind/")),
                    f"frozen: generated output cannot be immutable input: {name}")
            self.hashed(name, sha)
        self.hashed("schedule.json", self.freeze["schedule_sha256"])
        self.protocol = self.read("protocol.json")
        self.keys(self.protocol, ("version", "endpoint", "models", "efforts", "limits", "schedule_seed",
                                  "statistics_seed"), "protocol")
        require(self.protocol["endpoint"] == "https://opencode.ai/zen/go/v1/chat/completions",
                "frozen: only the Go chat/completions endpoint is allowed")
        require(set(self.protocol["models"]) == set(MODELS.values()) and
                set(self.protocol["efforts"]) == {"low", "high", "max"}, "frozen: model/effort schema")
        require(self.protocol["schedule_seed"] == SEED and self.protocol["statistics_seed"] == SEED + 1,
                "frozen: seeds must be documented before case 1 (analysis seed = schedule seed + 1)")
        require("blind_seed" not in self.protocol or self.protocol["blind_seed"] == 20261007093207,
                "frozen: wrong optional restart blind seed")
        limits = self.protocol["limits"]
        for key, value in {"inference_steps": 8, "wall_s": 180, "visible_words": 400,
                           "max_tokens": 16384, "fetch_attempts": 32}.items():
            require(limits.get(key) == value, f"frozen: protocol limits.{key} must be {value}")
        self.keys(self.protocol, ("effort_field", "retries", "grading", "qualification", "eligibility",
                                  "recommendation", "bootstrap_draws", "bootstrap_unit", "visible_word_rule",
                                  "source_drift", "access_gate", "compatibility_gate", "security"), "semantic protocol")
        require(self.protocol["effort_field"] == "reasoning_effort" and "thinking" not in self.protocol,
                "frozen: actual effort/thinking contract changed")
        require(self.protocol["visible_word_rule"] == VISIBLE_WORD_RULE, "frozen: unsupported visible word rule")
        require(self.protocol["retries"].get("client") == 0 and
                self.protocol["retries"].get("auxiliary_inference") == 0 and
                self.protocol["security"].get("auth_post_redirects") is False,
                "frozen: retries/auxiliary POSTs/auth redirects forbidden")
        semantics = {"grading": {"checks": 6, "supported": 1, "contradicted": -1, "missing": 0, "unverifiable": 0,
                                 "extra_penalty": .5, "extra_cap": 2, "floor": -6},
                     "qualification": {"operational_complete": True, "supported_grounded_checks": 6,
                                       "uncertainty": "pass", "minimum_distinct_sources": 2, "critical_errors": 0,
                                       "unsupported_extras": 0},
                     "eligibility": {"qualified_min": 10, "planned_per_config": 12, "every_task_qualified": True,
                                     "required_contradictions": 0, "critical_errors": 0},
                     "recommendation": {"speed_median_margin": .10, "paired_median_corroboration": True,
                                        "paired_min_blocks": 6, "paired_min_tasks": 4, "p90_max_worse": .10,
                                        "leave_one_task_out_direction": True, "price": False}}
        for section, expected in semantics.items():
            require(all(self.protocol[section].get(k) == v for k, v in expected.items()),
                    f"frozen: incompatible {section} semantics")
        require(self.protocol["bootstrap_draws"] == 10000 and self.protocol["bootstrap_unit"] ==
                "whole task, retaining repetitions and configurations", "frozen: whole-task bootstrap contract")
        require(self.protocol["source_drift"].get("required_main_text_mismatch") and
                self.protocol["access_gate"].get("counted") is True and
                self.protocol["compatibility_gate"].get("counted") is True, "frozen: missing drift/native gate stop policies")
        tools = self.read("tools.json")
        require(isinstance(tools, list) and len(tools) == 1 and tools[0].get("type") == "function" and
                tools[0].get("function", {}).get("name") == "webfetch", "frozen: only webfetch may be exposed")
        self.schedule = self.read("schedule.json")
        self.keys(self.schedule, ("seed", "algorithm", "configurations", "blocks", "cases", "position_counts"), "schedule")
        require(self.schedule["seed"] == SEED and "latin" in self.schedule["algorithm"].lower(),
                "frozen: seeded Latin schedule required")
        configurations = self.schedule["configurations"]
        require(len(configurations) == 6 and {c["id"] for c in configurations} == set(CONFIGS),
                "frozen: six exact configurations required")
        for c in configurations:
            require((c["model"], c["effort"]) == CONFIGS[c["id"]], "frozen: invalid configuration model/effort")
        cases = self.schedule["cases"]
        require(len(cases) == 72 and len({c["id"] for c in cases}) == 72, "frozen: 72 unique cases required")
        counts = {c: Counter() for c in CONFIGS}
        for index, c in enumerate(cases, 1):
            self.keys(c, ("id", "index", "block_id", "position", "task_id", "repetition",
                          "configuration_id", "model", "effort"), "scheduled case")
            require(c["index"] == index and c["task_id"] in TASKS and c["repetition"] == (1 if index <= 36 else 2),
                    "frozen: case index/task/repetition mismatch")
            require(c["configuration_id"] in CONFIGS and (c["model"], c["effort"]) == CONFIGS[c["configuration_id"]],
                    "frozen: case model/effort mismatch")
            require(c["position"] == (index-1) % 6 + 1, "frozen: blocks must run contiguously")
            require(not any(token in c["id"].lower() for token in ("deepseek", "glm", "low", "high", "max")),
                    "frozen: identity-bearing case ID")
            counts[c["configuration_id"]][c["position"]] += 1
        require(cases[0]["configuration_id"] == "deepseek-low", "frozen: first case must be DeepSeek LOW")
        for config, positions in counts.items():
            require(dict(positions) == {i: 2 for i in range(1, 7)}, "frozen: unbalanced Latin positions")
            declared = self.schedule["position_counts"].get(config, {})
            require({int(k): v for k, v in declared.items()} == dict(positions), "frozen: false position_counts")
        blocks = self.schedule["blocks"]
        require(len(blocks) == 12 and len({b["id"] for b in blocks}) == 12 and
                {(b["task_id"], b["repetition"]) for b in blocks} == {(t, r) for t in TASKS for r in (1, 2)},
                "frozen: twelve task/repetition blocks required")
        for i, block in enumerate(blocks):
            subset = cases[i*6:(i+1)*6]
            require(block["case_ids"] == [c["id"] for c in subset] and
                    {c["configuration_id"] for c in subset} == set(CONFIGS) and
                    all((c["block_id"], c["task_id"], c["repetition"]) ==
                        (block["id"], block["task_id"], block["repetition"]) for c in subset),
                    "frozen: block/schedule mismatch")
        tasks = self.read("dataset/tasks.json")
        gold = self.read("dataset/gold.json")
        self.gold = gold["tasks"]
        require(len(tasks) == 6 and {t["id"] for t in tasks} == TASKS and set(self.gold) == TASKS,
                "frozen: exact six tasks required")
        self.tasks = {t["id"]: t for t in tasks}
        self.tool_scope = frozen_tool_scope(self.text("webfetch.py"))
        for task, rubric in self.gold.items():
            require(len(rubric["checks"]) == 6 and {c["id"] for c in rubric["checks"]} == {f"C{i}" for i in range(1, 7)},
                    "frozen: six gold checks required")
            for check in rubric["checks"] + [rubric["uncertainty"]]:
                for evidence in check.get("source_evidence", check.get("evidence", [])):
                    require(normalized(evidence["quote"]) in normalized(self.text(evidence["archive_path"])) and
                            bool(evidence["quote"]), "frozen: gold quote absent from archive")
        self.sources = self.read("dataset/sources.json")
        require(bool(self.sources), "frozen: source archive missing")
        for source in self.sources:
            for kind in ("raw", "text"):
                require(source[f"{kind}_path"] in files, "frozen: unhashed source")
                self.hashed(source[f"{kind}_path"], source[f"{kind}_sha256"])
            require(utc(source["retrieved_utc"]) <= seal_time, "frozen: source retrieved after freeze")
        # Parent creates this proof, not the candidate. No secret paths or values are imported.
        workflow = self.read("preflight/workflow.json")
        self.keys(workflow, ("owner", "created_utc", "candidate_post_starts", "credential_provisioning",
                             "external_secret_paths_imported", "runtime_root", "worker_bounds_verified",
                             "protocol_reviewed", "api_evidence_reviewed"), "parent workflow")
        require(workflow["owner"] == "parent" and workflow["candidate_post_starts"] == 0 and
                workflow["external_secret_paths_imported"] is False and
                workflow["credential_provisioning"] == "parent_owned" and
                workflow["worker_bounds_verified"] is True and workflow["protocol_reviewed"] is True and
                workflow["api_evidence_reviewed"] is True and
                workflow["runtime_root"] == self.scope["runtime_root"] and utc(workflow["created_utc"]) <= seal_time,
                "frozen: parent workflow/worker/credential proof missing or false")
        for name in ("runner.py", "webfetch.py"):
            source = self.text(name)
            tree = ast.parse(source)
            require(not any(isinstance(n, ast.ImportFrom) and n.module and
                            n.module.split(".")[0] in {"auth", "keyring", "sqlite3"} for n in ast.walk(tree)),
                    "frozen: external credential store import")
            require(not re.search(r"(?:~/|/Users/[^/]+/)(?:\.config|\.opencode|\.local)|auth\.json", source),
                    "frozen: candidate code imports external secret paths")
        self.seal_time = seal_time
        for row in self.ledger():
            require(utc(row["started_utc"]) >= seal_time, "frozen: POST started before seal")
        return self

    def usage(self, usage, raw_steps, label):
        self.keys(usage, ("complete", "raw_steps", *USAGE_FIELDS), label)
        require(usage["raw_steps"] == raw_steps, f"collected: {label} discarded native usage")
        rows = []
        def known(v):
            return number(v) and v >= 0
        for raw in raw_steps:
            r = raw if isinstance(raw, dict) else {}
            details = r.get("prompt_tokens_details") or {}
            outputs = r.get("completion_tokens_details") or {}
            require(isinstance(details, dict) and isinstance(outputs, dict), "collected: malformed native usage details")
            prompt, completion = r.get("prompt_tokens"), r.get("completion_tokens")
            cached = details.get("cached_tokens", r.get("prompt_cache_hit_tokens"))
            written = details.get("cache_write_tokens", r.get("cache_creation_input_tokens"))
            reasoning = outputs.get("reasoning_tokens")
            def subtract(total, *subsets):
                return total-sum(subsets) if all(known(v) for v in (total, *subsets)) and total >= sum(subsets) else None
            uncached = subtract(prompt, cached, written)
            miss = r.get("prompt_cache_miss_tokens")
            if known(miss) and known(prompt) and known(cached) and prompt == cached+miss:
                uncached = miss
            values = (prompt, completion, reasoning, cached, written, uncached, subtract(completion, reasoning), r.get("cost"))
            rows.append(dict(zip(USAGE_FIELDS, (v if known(v) else None for v in values))))
        expected = {f: sum(row[f] for row in rows) if rows and all(row[f] is not None for row in rows) else None
                    for f in USAGE_FIELDS}
        complete = bool(rows) and all(expected[f] is not None for f in USAGE_FIELDS[:-1])
        require(usage["complete"] is complete, f"collected: {label} false usage completeness")
        for field in USAGE_FIELDS:
            value = usage[field]
            require(value is None or (number(value) and value >= 0), f"collected: invalid {field}")
            require(value == expected[field], f"collected: {label} {field}: unknown must stay null; native completion is inclusive")

    def cleanup(self, data, label):
        self.keys(data, ("owned_process_check_path", "credential_scan_path", "external_state_unchanged"), label)
        require(data["external_state_unchanged"] is True and
                (data.get("owned_processes_remaining") == 0 or data.get("owned_group_absent") is True or
                 data.get("all_owned_groups_absent") is True), f"collected: {label} cleanup failed")
        process = self.read(data["owned_process_check_path"])
        scan = self.read(data["credential_scan_path"])
        proof = process.get("owned_only") is True and process.get("remaining") == []
        if "owned_pgid" in process:
            proof = (isinstance(process["owned_pgid"], int) and process["owned_pgid"] > 0 and
                     process.get("owned_group_absent") is True and process.get("worker_awaited") is True and
                     process.get("output_drained") is True and process.get("owned_only") is True)
        require(proof and process.get("runtime_root") == self.scope["runtime_root"], "collected: missing owned process proof")
        require(scan.get("redacted_before_persistence") is True and scan.get("secret_matches") == 0 and
                scan.get("scanned_paths") and scan.get("external_secret_paths_read") is False,
                "collected: missing credential hygiene proof")

    def public_document_paths(self):
        """Narrow pre-freeze correction, tied to THIS freeze, not old body hashes.

        Only linked full/model .txt bytes from the two exact public URLs qualify.
        All other credential matches (including a second unknown match) fail.
        """
        archives = {}
        for source in self.sources:
            if (source["url"] not in PUBLIC_URLS or source["final_url"] != source["url"] or
                    source["canonical_url"] != PUBLIC_CANONICAL or source["status"] != 200 or source.get("error")):
                continue
            for kind in ("raw", "text"):
                name, sha = source[kind+"_path"], source[kind+"_sha256"]
                require(self.freeze["files"].get(name) == sha, "collected: public archive not frozen")
                self.hashed(name, sha)
            if public_matches(self.text(source["text_path"])):
                require(source["url"] not in archives, "collected: ambiguous public archive provenance")
                archives[source["url"]] = source
        proven = set()
        non_document_paths = {name for r in self.records for name in (r["history_path"], r["answer_path"]) if name}
        non_document_paths.update(name for r in self.records for req in r["requests"]
                                  for name in (req["request_path"], req["response_path"]) if name)
        non_document_paths.update(name for r in self.records for fetch in r["fetches"]
                                  for name in (fetch["raw_path"], fetch.get("tool_result_path")) if name)
        for record in self.records:
            for fetch in record["fetches"]:
                source = archives.get(fetch["requested_url"])
                if (not source or fetch["final_url"] != source["url"] or fetch["status"] not in {"ok", 200} or
                        fetch["error"] or fetch["truncated"] is not False):
                    continue
                expected = source["text_sha256"]
                if fetch["text_sha256"] != expected or fetch["model_text_sha256"] != expected:
                    continue
                for kind in ("text", "model_text"):
                    name = fetch[kind+"_path"]
                    if not isinstance(name, str) or name in non_document_paths:
                        continue
                    path = self.path(name)
                    prefix = f"execution/cases/{record['case_id']}/fetches/"
                    if (not name.startswith(prefix) or not path.is_relative_to(self.path(prefix)) or
                            path.suffix != ".txt" or (self.root/name).is_symlink()):
                        continue
                    raw = path.read_bytes()
                    if (digest(path) == expected and raw == self.path(source["text_path"]).read_bytes() and
                            public_matches(raw.decode("utf-8"))):
                        proven.add(name)
        self.public_paths = proven
        return proven

    def provisioning(self):
        """Validate the parent's saved receipt, not the credential or scan itself."""
        proof = self.read("execution/parent-provisioning.json")
        self.keys(proof, ("started_utc", "finished_utc", "credential_source", "credential_store_copied",
                          "worker_credential_store_access", "ephemeral_environment_only", "secret_matches",
                          "scanned_file_count", "runner_returncode", "caller_retries"), "parent provisioning")
        def integer(value):
            return isinstance(value, int) and not isinstance(value, bool)
        require(proof["credential_source"] == "parent read-only selected opencode-go integration credential" and
                proof["credential_store_copied"] is False and proof["worker_credential_store_access"] is False and
                proof["ephemeral_environment_only"] is True and integer(proof["secret_matches"]) and
                proof["secret_matches"] == 0 and integer(proof["scanned_file_count"]) and proof["scanned_file_count"] > 0 and
                integer(proof["caller_retries"]) and proof["caller_retries"] == 0 and integer(proof["runner_returncode"]),
                "collected: missing exact selected-Go-key hygiene proof")
        require(self.seal_time <= utc(proof["started_utc"]) <= utc(proof["finished_utc"]),
                "collected: invalid parent provisioning provenance")

    def collected(self):
        self.stage = "collected"
        index = self.read("execution/index.json")
        self.index = index
        self.keys(index, ("study_status", "gate_case_id", "gate_status", "planned_cases", "attempted_cases",
                          "terminal_cases", "cases", "cleanup", "compatibility_gates", "stop"), "execution index")
        self.provisioning()
        require(index["planned_cases"] == 72 and index["gate_case_id"] == self.schedule["cases"][0]["id"] and
                len(index["cases"]) == 72 and len(set(index["cases"])) == 72, "collected: preserve all 72 case rows")
        previous_end = None
        previous_monotonic_end = None
        unrun_seen = False
        drift_seen = False
        native_stop = None
        post_rows = []
        attempted = terminal = 0
        for case, path in zip(self.schedule["cases"], index["cases"]):
            r = self.read(path)
            self.keys(r, ("case_id", "schedule_index", "block_id", "task_id", "repetition", "configuration_id",
                          "model", "effort", "status", "operational_complete", "start_utc", "end_utc",
                          "monotonic_start", "monotonic_end", "wall_s", "assistant_span_s", "inference_steps",
                          "requests", "fetches", "answer_path", "visible_words", "usage", "errors", "cleanup",
                          "source_drift", "history_path"), "case record")
            for name in ("block_id", "task_id", "repetition", "configuration_id", "model", "effort"):
                require(r[name] == case[name], f"collected: case {case['id']} changed {name}")
            require(r["case_id"] == case["id"] and r["schedule_index"] == case["index"], "collected: case/order mismatch")
            self.records.append(r)
            terminal += 1  # Runner terminal_cases counts saved terminal rows, including honest skips.
            if r["status"] in UNRUN:
                unrun_seen = True
                require(all(r[k] is None for k in ("start_utc", "end_utc", "monotonic_start", "monotonic_end",
                                                   "wall_s", "assistant_span_s", "answer_path", "history_path")) and
                        r["requests"] == [] and r["fetches"] == [] and r["inference_steps"] == 0 and
                        r["operational_complete"] is False and r["visible_words"] == 0 and
                        r["errors"] == [] and not r["source_drift"], "collected: fabricated unrun record")
                self.usage(r["usage"], [], "unrun usage")
                continue
            require(not unrun_seen, "collected: candidate attempt after an unrun schedule gap")
            require(not drift_seen, "collected: candidate attempt after required-source drift stop")
            require(native_stop is None, "collected: candidate attempt after native parameter/access block")
            require(not self.records[:-1] or self.records[0]["operational_complete"],
                    "collected: candidate attempt after ordinary first overall failure")
            require(r["status"] in TERMINAL, f"collected: unknown case status {r['status']}")
            attempted += 1
            start, end = utc(r["start_utc"]), utc(r["end_utc"])
            require(self.seal_time <= start <= end and (previous_end is None or start >= previous_end),
                    "collected: prefreeze case or sequential overlap")
            previous_end = end
            require(number(r["monotonic_start"]) and number(r["monotonic_end"]) and number(r["wall_s"]) and
                    0 <= r["wall_s"] and abs(r["wall_s"]-(r["monotonic_end"]-r["monotonic_start"])) < .001,
                    "collected: case wall/deadline evidence inconsistent")
            require(previous_monotonic_end is None or r["monotonic_start"] >= previous_monotonic_end,
                    "collected: monotonic candidate overlap")
            previous_monotonic_end = r["monotonic_end"]
            require(abs((end-start).total_seconds()-r["wall_s"]) < 1,
                    "collected: launch/exit UTC and monotonic wall mismatch")
            require(r["assistant_span_s"] is None or (number(r["assistant_span_s"]) and
                    0 <= r["assistant_span_s"] <= r["wall_s"]), "collected: invalid assistant span")
            require(r["inference_steps"] == len(r["requests"]) and 1 <= len(r["requests"]) <= 8,
                    "collected: inference/request step limit")
            require(len(r["fetches"]) <= 32, "collected: fetch attempt limit")
            history = self.read(r["history_path"])
            require(isinstance(history, list) and history, "collected: missing full assistant/tool history")
            require(history[:2] == [{"role": "system", "content": self.text("system.txt")},
                                    {"role": "user", "content": self.tasks[case["task_id"]]["prompt"]}],
                    "collected: full history does not start fresh")
            assistant_texts = [m.get("content", "") for m in history if m.get("role") == "assistant" and
                               isinstance(m.get("content"), str) and m["content"].strip()]
            require(r["visible_words"] == sum(visible_words(t) for t in assistant_texts),
                    "collected: visible word count does not reproduce full assistant text")
            raw_steps = []
            native_messages = []
            request_end = start
            case_block = None
            for step, request in enumerate(r["requests"], 1):
                require(case_block is None, "collected: request after native parameter/access block")
                self.keys(request, ("step", "started_utc", "ended_utc", "elapsed_s", "request_path",
                                    "response_path", "http_status", "error", "usage"), "request")
                require(request["step"] == step, "collected: repeated/skipped request step")
                rs = utc(request["started_utc"])
                interrupted = request["ended_utc"] is None
                require(not interrupted or (r["status"] == "timeout" and request["error"] and
                        step == len(r["requests"]) and request["elapsed_s"] is None),
                        "collected: unfinished request without saved supervisory interruption")
                re_ = end if interrupted else utc(request["ended_utc"])
                require(request_end <= rs <= re_ <= end and (interrupted or (number(request["elapsed_s"]) and
                        0 <= request["elapsed_s"] <= r["wall_s"])), "collected: overlapping/out-of-case request")
                request_end = re_
                body = self.read(request["request_path"])
                require(body.get("model") == case["model"] and body.get("reasoning_effort") == case["effort"] and
                        body.get("max_tokens") == 16384 and "thinking" not in body and
                        body.get("stream") is False, "collected: actual model/reasoning_effort/thinking/budget mismatch")
                require(not set(body).intersection({"temperature", "top_p", "api_key", "authorization"}),
                        "collected: sampler override or persisted credential")
                require(body.get("messages") and body["messages"][0] == {"role": "system", "content": self.text("system.txt")},
                        "collected: changed system/history")
                require(len(body["messages"]) >= 2 and body["messages"][1] ==
                        {"role": "user", "content": self.tasks[case["task_id"]]["prompt"]}, "collected: changed task input")
                require(body["messages"] == history[:len(body["messages"])], "collected: request history changed native reasoning/tool messages")
                if step == 1:
                    require(len(body["messages"]) == 2, "collected: case not fresh")
                tools = self.read("tools.json")
                require((body.get("tools", []) == tools if step < 8 else body.get("tools", []) == []),
                        "collected: changed tools or step 8 tools not removed")
                if step == 8:
                    require(body.get("tool_choice") in (None, "none"), "collected: step 8 tool exposure is forbidden")
                if request["response_path"] is None:
                    require(request["error"] and request["http_status"] is None, "collected: missing native response without transmission error")
                    response = {}
                else:
                    response = self.native_response(request)
                if saved_access_denial(request["http_status"], response):
                    case_block = "access_blocked"
                elif saved_parameter_denial(request["http_status"], response):
                    case_block = "compatibility_blocked"
                if case_block:
                    require(request["error"] and not r["operational_complete"],
                            "collected: native block hidden as success")
                    native_stop = {"case_id": case["id"], "schedule_index": case["index"],
                                   "http_status": request["http_status"], "response_path": request["response_path"]}
                if request["error"] is None:
                    require(request["http_status"] == 200 and isinstance(response, dict) and
                            isinstance(response.get("choices"), list) and response["choices"],
                            "collected: successful request lacks native choice")
                    message = response["choices"][0].get("message")
                    require(isinstance(message, dict) and message in history,
                            "collected: native assistant response absent from full history")
                    native_messages.append(message)
                    if step == 8:
                        returned_calls = message.get("tool_calls") or []
                        if returned_calls:
                            require(r["status"] == "step_limit" and not r["operational_complete"] and
                                    not any(f.get("tool_call_id") in {c["id"] for c in returned_calls} for f in r["fetches"]),
                                    "collected: native step 8 forbidden tools must be retained but never executed")
                else:
                    require(not r["operational_complete"], "collected: request error hidden by successful case")
                    # A post-response harness error (e.g. excessive native call batch)
                    # still preserves the native assistant already appended by runner.
                    choices = response.get("choices") if isinstance(response, dict) else None
                    if isinstance(choices, list) and len(choices) == 1:
                        message = choices[0].get("message")
                        if isinstance(message, dict) and message in history:
                            native_messages.append(message)
                raw = response.get("usage") if isinstance(response, dict) else None
                if "native_usage" in request:
                    require(request["native_usage"] == raw, "collected: request discarded/changed raw native usage")
                if isinstance(request["usage"], dict) and {"complete", "raw_steps"} <= request["usage"].keys():
                    self.usage(request["usage"], [raw], "request usage")
                else:
                    require(request["usage"] == raw, "collected: request discarded/changed raw native usage")
                raw_steps.append(raw)
                self.keys(request, ("intent_logged", "client_post_starts", "client_post_started_utc"), "request POST proof")
                require(request["intent_logged"] is True and request["client_post_starts"] in (0, 1),
                        "collected: request intent absent or replayed POST")
                if request["client_post_starts"] == 1:
                    require(rs <= utc(request["client_post_started_utc"]) <= re_, "collected: POST start outside request")
                    post_rows.append({"case_id": r["case_id"], "step": step,
                                      "request_path": request["request_path"], "started_utc": request["client_post_started_utc"]})
                else:
                    require(request["client_post_started_utc"] is None and request["response_path"] is None and
                            request["error"], "collected: native response without recorded client POST")
            self.usage(r["usage"], raw_steps, "case usage")
            expected_status = {"access_blocked": "access_gate_error", "compatibility_blocked": "compatibility_error"}
            if case_block:
                require(r["status"] == expected_status[case_block] and index["study_status"] == case_block,
                        "collected: native block classification/status mismatch")
            elif r["status"] in expected_status.values():
                raise AuditError("collected: block missing native denial evidence")
            require(native_messages == [m for m in history if m.get("role") == "assistant"],
                    "collected: full native assistant history missing/extra/out of order")
            calls_by_id = {}
            for message in native_messages:
                batch = message.get("tool_calls") or []
                if isinstance(batch, list):
                    for call in batch:
                        if isinstance(call, dict) and call.get("id"):
                            require(call["id"] not in calls_by_id, "collected: duplicate native tool call ID")
                            calls_by_id[call["id"]] = call
            for fetch in r["fetches"]:
                self.keys(fetch, ("id", "requested_url", "final_url", "status", "redirects", "started_utc",
                                  "ended_utc", "elapsed_s", "raw_path", "text_path", "model_text_path",
                                  "raw_sha256", "text_sha256", "model_text_sha256", "raw_bytes", "text_bytes",
                                  "truncated", "error", "frozen_source_match"), "fetch")
                if fetch.get("tool_call_id"):
                    require(fetch["tool_call_id"] in calls_by_id, "collected: fetch has no native assistant call")
                    call = calls_by_id[fetch["tool_call_id"]]
                    function = call.get("function") or {}
                    try:
                        args = json.loads(function.get("arguments", "null"))
                    except (ValueError, TypeError):
                        args = None
                    valid = (call.get("type") == "function" and function.get("name") == "webfetch" and
                             isinstance(args, dict) and set(args) == {"url"} and isinstance(args["url"], str))
                    require(fetch["requested_url"] == (args["url"] if valid else None),
                            "collected: fetch request differs from native arguments")
                    if "tool_name" in fetch:
                        require(fetch["tool_name"] == function.get("name"), "collected: changed native tool name")
                    if "arguments_valid" in fetch:
                        require(fetch["arguments_valid"] is valid, "collected: changed native argument-schema evidence")
                if fetch.get("tool_result_path"):
                    self.hashed(fetch["tool_result_path"], fetch["tool_result_sha256"])
                    require(any(m.get("role") == "tool" and m.get("tool_call_id") == fetch.get("tool_call_id") and
                                m.get("content") == self.text(fetch["tool_result_path"]) for m in history),
                            "collected: full tool result absent from history")
                require(fetch["ended_utc"] is not None or (r["status"] == "timeout" and fetch["error"]),
                        "collected: unfinished fetch without supervisory interruption")
                require(start <= utc(fetch["started_utc"]) <= (utc(fetch["ended_utc"]) if fetch["ended_utc"] else end) <= end,
                        "collected: fetch outside case")
                require(isinstance(fetch["truncated"], bool), "collected: missing truncation evidence")
                require(fetch["status"] in {"ok", "http_error", "rejected", "fetch_error", "interrupted", 200},
                        "collected: unknown fetch terminal schema")
                require(isinstance(fetch["redirects"], list), "collected: redirect evidence must be an array")
                redirect_urls = []
                previous_url = fetch["requested_url"].split("#")[0] if fetch["requested_url"] else None
                for hop in fetch["redirects"]:
                    if isinstance(hop, str):
                        redirect_urls.append(hop)
                        previous_url = hop
                    else:
                        self.keys(hop, ("from", "to", "status"), "documentation redirect")
                        require(hop["from"] == previous_url and hop["status"] in {301, 302, 303, 307, 308},
                                "collected: malformed redirect chain/status")
                        redirect_urls.extend((hop["from"], hop["to"]))
                        previous_url = hop["to"]
                if not fetch["error"]:
                    require(all(self.allowed_url(u, case["task_id"]) for u in
                                [fetch["requested_url"], fetch["final_url"], *redirect_urls]) and
                            (not fetch["redirects"] or previous_url == fetch["final_url"]),
                            "collected: fetch/redirect outside official frozen URL rules")
                for kind in ("raw", "text", "model_text"):
                    if fetch[f"{kind}_path"] is not None:
                        self.hashed(fetch[f"{kind}_path"], fetch[f"{kind}_sha256"])
                    else:
                        require(fetch["error"] and fetch[f"{kind}_sha256"] is None,
                                "collected: successful fetch missing full source/model text")
                if fetch["raw_path"]:
                    require(self.path(fetch["raw_path"]).stat().st_size == fetch["raw_bytes"] <= 2*1024*1024,
                            "collected: invalid full raw body size")
                if fetch["text_path"]:
                    require(fetch["model_text_path"] and self.path(fetch["text_path"]).stat().st_size == fetch["text_bytes"],
                            "collected: invalid full text size")
                    text, shown = self.text(fetch["text_path"]), self.text(fetch["model_text_path"])
                    require((text != shown) == fetch["truncated"], "collected: false truncation flag")
                    require(len(shown.encode()) <= 256*1024, "collected: model text cap")
                    tool_contents = [m for m in history if m.get("role") == "tool" and
                                     (not fetch.get("tool_call_id") or m.get("tool_call_id") == fetch["tool_call_id"])]
                    def contains_shown(m):
                        if m.get("content") == shown:
                            return True
                        try:
                            payload = json.loads(m.get("content", ""))
                        except (ValueError, TypeError):
                            return False
                        return (isinstance(payload, dict) and payload.get("text") == shown and
                                payload.get("status") == fetch["status"] and payload.get("url") == fetch["final_url"] and
                                payload.get("truncated") is fetch["truncated"])
                    require(any(contains_shown(m) for m in tool_contents),
                            "collected: exact fetched model text absent from full tool history")
                    frozen = next((s for s in self.sources if fetch["requested_url"].split("#")[0] == s["url"]), None)
                    frozen = frozen or next((s for s in self.sources if fetch["final_url"] == s["url"]), None)
                    match = fetch["text_sha256"] == frozen["text_sha256"] if frozen else None
                    proof = fetch["frozen_source_match"]
                    expected = {"raw": fetch["raw_sha256"] == frozen["raw_sha256"], "text": match} if frozen else None
                    require(proof == expected if isinstance(proof, dict) else proof is match, "collected: source drift match false")
                    if match is False and self.canonical(fetch["final_url"]) in self.tasks[case["task_id"]]["required_source_urls"]:
                        require(r["source_drift"], "collected: unrecorded normalized source drift")
                        drift_seen = True
            if r["operational_complete"]:
                require(r["status"] == "completed" and r["answer_path"] and self.text(r["answer_path"]).strip() and
                        not r["errors"] and not r["source_drift"], "collected: falsely operationally complete")
                require(assistant_texts and self.text(r["answer_path"]) == "\n\n".join(assistant_texts),
                        "collected: answer omits/fabricates visible assistant text")
                last_response = self.native_response(r["requests"][-1])
                require(last_response["choices"][0].get("finish_reason") == "stop" and
                        not last_response["choices"][0]["message"].get("tool_calls"),
                        "collected: completed record lacks terminal native answer")
            elif r["status"] == "completed":
                raise AuditError("collected: completed status without operational completion")
            if r["status"] in {"provider_error", "access_gate_error", "compatibility_error", "timeout", "harness_error", "tool_error"}:
                require(r["errors"] or any(req["error"] for req in r["requests"]) or
                        (r["status"] == "timeout" and r["cleanup"].get("kill_sent") is True),
                        "collected: failed terminal record missing error evidence")
            self.cleanup(r["cleanup"], "case cleanup")
        require(index["attempted_cases"] == attempted and index["terminal_cases"] == terminal,
                "collected: attempted/terminal count mismatch")
        ledger_path = self.path("execution/post-starts.jsonl")
        require(ledger_path.is_file(), "missing collected stage artifact: execution/post-starts.jsonl")
        require(self.ledger() == post_rows and len({r["request_path"] for r in post_rows}) == len(post_rows),
                "collected: duplicate, hidden extra, or missing real POST starts; upstream attempts remain unknown")
        linked = {r["request_path"] for r in post_rows}
        intended = {req["request_path"] for r in self.records for req in r["requests"]}
        require(len(intended) == sum(len(r["requests"]) for r in self.records) and
                self.request_artifacts() == intended, "collected: unledgered/reused request body artifact")
        public_paths = self.public_document_paths()
        for path in self.root.glob("execution/**/*"):
            if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".md"}:
                text = path.read_text(encoding="utf-8")
                require(not re.search(CREDENTIAL_PATTERN, text) or
                        (str(path.relative_to(self.root)) in public_paths and public_matches(text)),
                        "collected: persisted credential material")
        self.cleanup(index["cleanup"], "study cleanup")
        status = index["study_status"]
        require(status in {"completed", "incomplete", *BLOCKED}, "collected: unknown study status")
        require(status == "completed" or index.get("completed_comparison") is not True,
                "collected: native blocked/incomplete study is not a completed comparison")
        gates = index["compatibility_gates"]
        require(isinstance(gates, dict) and set(gates) == set(CONFIGS), "collected: six compatibility gates required")
        for config in CONFIGS:
            first = next(r for r in self.records if r["configuration_id"] == config)
            expected = ("not_run" if first["status"] in UNRUN else "passed" if first["operational_complete"] else
                        "access_blocked" if first["status"] == "access_gate_error" else
                        "compatibility_blocked" if first["status"] == "compatibility_error" else "incomplete")
            require(gates[config] == {"case_id": first["case_id"], "status": expected},
                    "collected: fabricated compatibility gate/pass")
        first = self.records[0]
        first_gate = gates[first["configuration_id"]]["status"]
        require(index["gate_status"] == first_gate, "collected: fabricated first gate status")
        stop = index["stop"]
        if stop is not None:
            self.keys(stop, ("case_id", "schedule_index", "reason", "http_status", "response_path"), "study stop")
            require(isinstance(stop["reason"], str) and stop["reason"].strip() and attempted,
                    "collected: stop reason/attempt missing")
            last = self.records[attempted-1]
            require(stop["case_id"] == last["case_id"] and stop["schedule_index"] == last["schedule_index"],
                    "collected: stop does not match attempted prefix")
            request = last["requests"][-1] if last["requests"] else {}
            require(stop["reason"] == last["status"] and stop["http_status"] == request.get("http_status") and
                    stop["response_path"] == request.get("response_path"), "collected: stop contradicts saved terminal evidence")
        if status == "completed":
            require(attempted == terminal == 72 and index["gate_status"] == "passed" and
                    first["status"] == "completed" and first["operational_complete"] and stop is None,
                    "collected: incomplete 72-case comparison")
        elif status in BLOCKED:
            suffix = "not_run_access_gate" if status == "access_blocked" else "not_run_compatibility_block"
            require(native_stop is not None and stop is not None and
                    all(stop[k] == v for k, v in native_stop.items()) and
                    all(r["status"] == suffix for r in self.records[attempted:]),
                    "collected: invalid native block prefix/stop/suffix")
        else:
            require(native_stop is None, "collected: native block mislabeled incomplete")
            require(attempted and any(not r["operational_complete"] for r in self.records[:attempted]),
                    "collected: fabricated incomplete/skipped study")
            if attempted < 72:
                last = self.records[attempted-1]
                require(stop is not None and not last["operational_complete"] and
                        all(r["status"] not in {"not_run_access_gate", "not_run_compatibility_block"}
                            for r in self.records[attempted:]), "collected: fabricated ordinary stop/skips")
        return self

    def blind(self):
        self.stage = "grades"
        index = self.read("blind/index.json")
        mapping = self.read("private/unblind.json")
        self.keys(mapping, ("mapping", "sealed_hashes"), "private mapping")
        self.mapping = mapping["mapping"]
        self.keys(index, ("shards", "cases"), "blind index")
        case_ids = []
        for item in index["cases"]:
            if isinstance(item, str) and item.startswith("blind/cases/") and item.endswith("/case.json"):
                blind_id = item.split("/")[2]
                require(item == f"blind/cases/{blind_id}/case.json", "grades: invalid blind case path")
                case_ids.append(blind_id)
            else:
                case_ids.append(item)
        self.blind_index = {**index, "cases": case_ids}
        a, b = index["shards"].get("a", []), index["shards"].get("b", [])
        require(len(a) == len(b) == 36 and not set(a)&set(b) and len(set(a+b)) == 72 and
                set(a+b) == set(case_ids) == set(self.mapping), "grades: disjoint 36/36 blind shards required")
        require(set(self.mapping.values()) == {c["id"] for c in self.schedule["cases"]}, "grades: mapping not a 72-case bijection")
        require([self.mapping[b] for b in case_ids] != [c["id"] for c in self.schedule["cases"]],
                "grades: blind order must be shuffled")
        self.blinds = {}
        record_map = {r["case_id"]: r for r in self.records}
        prohibited = re.compile(r"(?i)deepseek|glm[-_ ]?(?:5|low|high|max)|reasoning_effort|opencode-go|(?:effort|configuration)\s*[:=]\s*(?:low|high|max)|/Users/|/private/|execution/cases/|researcher-poc")
        forbidden_keys = {"model", "effort", "configuration_id", "schedule_index", "index", "wall_s", "latency",
                          "start_utc", "end_utc", "usage", "tokens", "cost", "response_path", "backend", "monotonic_start",
                          "position", "repetition", "block_id", "model_id", "provider", "provider_id", "backend_id",
                          "elapsed_s", "started_utc", "ended_utc", "monotonic_end", "assistant_span_s", "prompt_tokens",
                          "completion_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens", "reported_cost",
                          "raw_response", "raw_path", "http_status", "created_utc", "schedule", "request_path"}
        def leak(obj):
            if isinstance(obj, dict):
                require(not set(obj)&forbidden_keys, "grades: blind metadata leak")
                for value in obj.values():
                    leak(value)
            elif isinstance(obj, list):
                for value in obj:
                    leak(value)
            elif isinstance(obj, str):
                require(not prohibited.search(obj), "grades: blind identity/path leak")
        def rubric_semantics(value):
            if isinstance(value, dict):
                return {k: rubric_semantics(v) for k, v in value.items()
                        if k not in {"archive_path", "raw_path", "text_path", "source_path"}}
            if isinstance(value, list):
                return [rubric_semantics(v) for v in value]
            return value
        def redacted(original, blind_id, kind, source_path=None):
            path = self.path("private/redactions.json")
            if not path.exists():
                return original
            entries = self.read("private/redactions.json").get(blind_id, [])
            if isinstance(entries, dict):
                entries = entries.get(kind, [])
            elif kind != "answer":
                entries = []
            require(isinstance(entries, list), "grades: redaction operations must be an array")
            for edit in entries:
                self.keys(edit, ("original", "replacement", "reason"), "private redaction operation")
                if source_path and edit.get("source_path") not in (None, source_path):
                    continue
                require(edit["reason"] == "self_identification" and edit["original"], "grades: undocumented redaction")
                if edit["original"] in original:
                    original = original.replace(edit["original"], edit["replacement"])
            return original
        for blind_id in case_ids:
            require(re.fullmatch(r"[A-Za-z0-9_-]+", blind_id) and blind_id not in self.mapping.values(),
                    "grades: blind IDs must be opaque and different from case IDs")
            name = f"blind/cases/{blind_id}/case.json"
            require(name in mapping["sealed_hashes"], "grades: blind export lacks private hash")
            self.hashed(name, mapping["sealed_hashes"][name])
            row = self.read(name)
            self.keys(row, ("blind_id", "task_id", "prompt", "answer", "sources", "rubric", "mechanical"), "blind case")
            leak(row)
            r = record_map[self.mapping[blind_id]]
            require(row["blind_id"] == blind_id and row["task_id"] == r["task_id"] and
                    row["prompt"] == self.tasks[r["task_id"]]["prompt"] and
                    rubric_semantics(row["rubric"]) == rubric_semantics(self.gold[r["task_id"]]),
                    "grades: changed blind task/rubric")
            original = self.text(r["answer_path"]) if r["answer_path"] else ""
            require(redacted(original, blind_id, "answer") == row["answer"], "grades: fabricated blind answer or undocumented redaction")
            for source in row["sources"]:
                self.keys(source, ("url", "source_path", "status", "frozen"), "blind source")
                require(source["status"] in {"fetched", "frozen_reference"} and
                        source["frozen"] is (source["status"] == "frozen_reference"), "grades: blind source provenance schema")
                require(source["source_path"].startswith(f"blind/cases/{blind_id}/") and
                        self.path(source["source_path"]).is_relative_to(self.path(f"blind/cases/{blind_id}")),
                        "grades: identity-bearing source path")
                require(source["source_path"] in mapping["sealed_hashes"], "grades: blind source lacks sealed hash")
                self.hashed(source["source_path"], mapping["sealed_hashes"][source["source_path"]])
                source_text = self.text(source["source_path"])
                leak(source_text)
                if "citation_support_eligible" in source:
                    require(source["citation_support_eligible"] is (source["status"] == "fetched"),
                            "grades: fabricated source citation eligibility")
                if source["status"] == "fetched":
                    candidates = [f for f in r["fetches"] if f["text_path"] and f["model_text_path"] and
                              f["status"] in {"ok", 200} and not f["error"] and
                              self.canonical(f["final_url"]) == self.canonical(source["url"]) and
                              (not source.get("fetched_url") or f["final_url"] == source["fetched_url"])]
                    candidates = [f for f in candidates if
                                  redacted(self.text(f["text_path"]), blind_id, "source", source["source_path"]) == source_text]
                    require(candidates, "grades: blind source not frozen/fetched evidence")
                    preview_path = source.get("candidate_visible_path")
                    require(preview_path and preview_path.startswith(f"blind/cases/{blind_id}/") and
                            self.path(preview_path).is_relative_to(self.path(f"blind/cases/{blind_id}")),
                            "grades: candidate preview must be linked inside its opaque case")
                    require(preview_path in mapping["sealed_hashes"], "grades: candidate preview lacks sealed hash")
                    self.hashed(preview_path, mapping["sealed_hashes"][preview_path])
                    preview_text = self.text(preview_path)
                    leak(preview_text)
                    require(any(redacted(self.text(f["model_text_path"]), blind_id, "source", preview_path) == preview_text
                                for f in candidates), "grades: candidate preview differs from corresponding fetch model text")
                else:
                    paths = [s["text_path"] for s in self.sources if self.canonical(s["url"]) == self.canonical(source["url"])]
                    require(not source.get("candidate_visible_path"), "grades: frozen reference cannot claim a candidate preview")
                    require(any(redacted(self.text(p), blind_id, "source", source["source_path"]) == source_text for p in paths),
                            "grades: blind source not frozen/fetched evidence")
            mechanical = row["mechanical"]
            reconstructed = self.mechanical_compliance(r)
            for key in ("word_cap", "fetched_two_sources", "source_rules", "tool_rules"):
                actual = reconstructed[key]
                require(mechanical.get(key) is actual, f"grades: fabricated mechanical {key}")
            for key in ("distinct_fetched_pages", "requested_tool_calls"):
                if key in mechanical:
                    require(mechanical[key] == reconstructed[key], f"grades: fabricated mechanical {key}")
            for key, actual in {"attempted": r["status"] not in UNRUN, "operational_complete": r["operational_complete"],
                                "visible_words": r["visible_words"], "fetch_attempts": len(r["fetches"]),
                                "truncated_fetches": sum(bool(f["truncated"]) for f in r["fetches"])}.items():
                if key in mechanical:
                    require(mechanical[key] == actual, f"grades: fabricated mechanical {key}")
            self.blinds[blind_id] = row
        allowed = {"blind/index.json"} | {f"blind/cases/{b}/case.json" for b in self.blinds} | {
            s["source_path"] for row in self.blinds.values() for s in row["sources"]}
        allowed.update(s["candidate_visible_path"] for row in self.blinds.values() for s in row["sources"]
                       if s.get("candidate_visible_path"))
        actual = {str(p.relative_to(self.root)) for p in self.root.glob("blind/**/*") if p.is_file()}
        require(actual == allowed, "grades: unreviewed extra grader input artifact (possible identity leak)")
        return self

    def grade(self, g, blind_id):
        row = self.blinds[blind_id]
        record = next(r for r in self.records if r["case_id"] == self.mapping[blind_id])
        self.keys(g, ("blind_id", "task_id", "checks", "uncertainty", "citations", "critical_errors",
                      "unsupported_extras", "compliance", "ambiguous", "notes"), "grade")
        require(g["blind_id"] == blind_id and g["task_id"] == row["task_id"], "grades: grade identity mismatch")
        require(bool(row["answer"].strip()), "grades: empty unrun row must receive no semantic grade")
        require(len(g["checks"]) == 6 and {c["id"] for c in g["checks"]} == {f"C{i}" for i in range(1, 7)},
                "grades: six unique checks per attempted answer required")
        sources = {s["source_path"]: s["url"] for s in row["sources"]}
        fetched_sources = {s["source_path"]: s for s in row["sources"] if s["status"] == "fetched"}
        def answer_quote(obj, missing=False):
            self.keys(obj, ("answer_quote", "rationale"), "judgment")
            quote = obj["answer_quote"]
            require(isinstance(quote, str) and isinstance(obj["rationale"], str) and obj["rationale"].strip(),
                    "grades: semantic rationale required")
            require((quote == "" if missing else bool(quote) and normalized(quote) in normalized(row["answer"])),
                    "grades: fabricated answer quote or missing judgment without empty quote")
        def evidence(items, required=False):
            require(isinstance(items, list) and (bool(items) or not required), "grades: missing source rationale/evidence")
            for item in items:
                self.keys(item, ("url", "source_path", "quote"), "grade evidence")
                path = item["source_path"]
                if path.startswith("dataset/"):
                    allowed = {s["text_path"]: s["canonical_url"] for s in self.sources}
                else:
                    allowed = sources
                require(path in allowed and self.canonical(item["url"]) == self.canonical(allowed[path]),
                        "grades: evidence outside blind/frozen first-party sources")
                require(bool(item["quote"]) and normalized(item["quote"]) in normalized(self.text(path)),
                        "grades: fabricated source quote")
        for check in g["checks"]:
            self.keys(check, ("id", "status", "answer_quote", "evidence", "rationale", "citation_status"), "check")
            require(check["status"] in {"supported", "contradicted", "missing", "unverifiable"} and
                    check["citation_status"] in {"entailing", "missing", "non_entailing"}, "grades: unknown judgment schema")
            answer_quote(check, check["status"] == "missing")
            evidence(check["evidence"], check["status"] in {"supported", "contradicted"})
            require(check["citation_status"] != "entailing" or bool(check["evidence"]),
                    "grades: entailing citation without source quote")
            if check["citation_status"] == "entailing":
                require(any(c.get("support") == "entailing" and normalized(check["answer_quote"]) in
                            normalized(c.get("answer_quote", "")) and
                            self.canonical(c.get("url", "")) in {self.canonical(e["url"]) for e in check["evidence"]}
                            for c in g["citations"]),
                        "grades: entailing check lacks linked claim-level citation")
        uncertainty = g["uncertainty"]
        require(uncertainty.get("status") in {"pass", "omit", "fail"}, "grades: uncertainty status")
        answer_quote(uncertainty, uncertainty["status"] == "omit")
        evidence(uncertainty.get("evidence"), uncertainty["status"] == "pass")
        for item in g["critical_errors"] + g["unsupported_extras"]:
            answer_quote(item)
            evidence(item.get("evidence"), True)
        for citation in g["citations"]:
            self.keys(citation, ("answer_quote", "url", "support", "anchor_compliance", "rationale", "evidence"), "citation")
            answer_quote(citation)
            require(citation["support"] in {"entailing", "missing", "non_entailing"} and
                    isinstance(citation["anchor_compliance"], bool), "grades: invalid citation judgment")
            evidence(citation["evidence"], citation["support"] == "entailing")
            if citation["support"] == "entailing":
                require(self.canonical(citation["url"]) in self.fetched_pages(record),
                        "grades: entailing citation page was never actually fetched")
                require(any(e["source_path"] in fetched_sources and self.canonical(e["url"]) == self.canonical(citation["url"])
                            for e in citation["evidence"]),
                        "grades: grounding must use fetched evidence, not a frozen-only reference bibliography")
            if citation["anchor_compliance"]:
                require(self.anchor_exists(citation["url"], record), "grades: supplied citation anchor does not exist")
            if g["compliance"].get("full_urls"):
                require(citation["url"] in row["answer"] and
                        self.canonical(citation["url"]) in {self.canonical(s["url"]) for s in row["sources"]},
                        "grades: full URL citation absent from answer or official source export")
        compliance = g["compliance"]
        for key in ("full_urls", "word_cap", "english", "fetched_two_sources", "source_rules", "tool_rules"):
            require(isinstance(compliance.get(key), bool), f"grades: compliance.{key} must be boolean")
        require("discovery_chain" in compliance, "grades: separate discovery-chain judgment required")
        # Mechanical evidence is separate from semantic reviewer judgments.
        mechanical = row["mechanical"]
        for key in ("word_cap", "fetched_two_sources", "source_rules", "tool_rules"):
            require(isinstance(mechanical.get(key), bool) and not (compliance[key] and not mechanical[key]),
                    f"grades: compliance contradicts mechanical {key}")
        if compliance["full_urls"]:
            require(all(c["url"].startswith("https://") and c["anchor_compliance"] for c in g["citations"]),
                    "grades: full URL compliance contradicts citations")
        require(not all(c["citation_status"] == "entailing" for c in g["checks"]) or bool(g["citations"]),
                "grades: grounded checks without claim-level citation records")
        return g

    def grades(self, shard=None):
        for s in ([shard] if shard else ["a", "b"]):
            expected = set()
            for blind_id in self.blind_index["shards"][s]:
                row = self.blinds[blind_id]
                name = f"grades/shard-{s}/{blind_id}.json"
                if not row["answer"].strip():
                    require(not self.path(name).exists(), "grades: fabricated semantic grade for empty answer")
                    continue
                expected.add(name)
                grade = self.grade(self.read(name), blind_id)
                self.effective[blind_id] = grade
            actual = {str(p.relative_to(self.root)) for p in self.root.glob(f"grades/shard-{s}/*.json")}
            require(actual == expected, "grades: unexpected/duplicate grade artifact")
        return self

    def graded(self):
        self.stage = "graded"
        seal = self.read("grades-seal.json")
        self.keys(seal, ("created_utc", "files", "effective_grades", "blind_review_paths", "mapping_sha256"), "grade seal")
        mapping = self.read("private/unblind.json")
        require(seal["mapping_sha256"] == mapping_digest(mapping), "graded: private identity mapping changed after grade seal")
        require("unblinded_utc" in mapping and utc(seal["created_utc"]) < utc(mapping["unblinded_utc"]),
                "graded: grades must be sealed before unblinding")
        if self.records:
            ends = [utc(r["end_utc"]) for r in self.records if r["end_utc"]]
            require(not ends or utc(seal["created_utc"]) >= max(ends), "graded: grade seal precedes collection")
        initial = {str(p.relative_to(self.root)) for p in self.root.glob("grades/**/*.json")}
        overrides = {str(p.relative_to(self.root)) for p in self.root.glob("adjudication/*.json")}
        require(initial | overrides | set(seal["blind_review_paths"]) <= seal["files"].keys() and
                seal["blind_review_paths"], "graded: initial/override/blind reviews not sealed")
        for path, sha in seal["files"].items():
            self.hashed(path, sha)
        for path in seal["blind_review_paths"]:
            review = self.read(path)
            self.keys(review, ("blind_review", "reviewer_type", "passed"), "blind review")
            require(review["blind_review"] is True and review["passed"] is True and review["reviewer_type"],
                    "graded: missing disclosed blind review evidence")
        require(set(seal["effective_grades"]) == set(self.effective), "graded: effective grade coverage mismatch")
        for blind_id, name in seal["effective_grades"].items():
            require(name in seal["files"], "graded: unsealed effective grade")
            if name.startswith("adjudication/"):
                override = self.read(name)
                self.keys(override, ("blind_id", "initial_grade_path", "rationale", "effective_grade"), "adjudication")
                require(override["blind_id"] == blind_id and override["rationale"].strip() and
                        override["initial_grade_path"] in initial and
                        self.read(override["initial_grade_path"])["blind_id"] == blind_id,
                        "graded: override must preserve matching initial judgment")
                self.effective[blind_id] = self.grade(override["effective_grade"], blind_id)
            else:
                require(name in initial and self.read(name) == self.effective[blind_id], "graded: invalid effective grade link")
        return self


def audit(root, stage=None, shard=None, write=False):
    """Audit only saved public artifacts; raise AuditError rather than infer missing data."""
    require(stage in {None, "frozen", "collected", "grades", "graded"}, "unknown audit stage")
    require(shard in {None, "a", "b"} and (shard is None or stage == "grades"), "--shard applies only to grades")
    a = Auditor(root).frozen()
    if stage == "frozen":
        require(a.ledger() == [], "frozen: stage requires zero POST starts")
        require(not a.request_artifacts(), "frozen: hidden request artifacts before execution")
        result = {"ok": True, "stage": "frozen", "candidate_post_starts": 0}
    else:
        a.collected()
        if stage == "collected":
            result = {"ok": True, "stage": "collected", "study_status": a.index["study_status"]}
        elif stage == "grades":
            a.blind().grades(shard)
            result = {"ok": True, "stage": "grades", "shard": shard}
        elif stage == "graded":
            a.blind().grades().graded()
            result = {"ok": True, "stage": "graded"}
        else:
            require(a.index["study_status"] != "incomplete", "final audit incomplete: missing completed/blocked stage; preserve rows and resolve interruption")
            if a.index["study_status"] in BLOCKED:
                require(a.text("report.md").strip(), "final: missing honest native-block report")
                block = a.read("analysis/block-report.json")
                from analysis import block_report
                require(block == block_report(a), "final: fabricated native-block comparison")
                completion = "honest_access_block" if a.index["study_status"] == "access_blocked" else "honest_compatibility_block"
                result = {"ok": True, "stage": "final", "completion": completion, "completed_comparison": False}
            else:
                a.blind().grades().graded()
                from analysis import analyze_saved
                expected = analyze_saved(a)
                require(a.read("analysis/results.json") == expected, "final: analysis does not reproduce sealed saved evidence")
                require(a.text("report.md").strip(), "final: report missing")
                result = {"ok": True, "stage": "final", "completion": "completed_comparison", "completed_comparison": True}
            review = a.read("final-review/index.json")
            require(review.get("saved_only") is True and review.get("passed") is True and review.get("files"),
                    "final: missing independent saved-evidence review seal")
            for path, sha in review["files"].items():
                a.hashed(path, sha)
            require("report.md" in review["files"], "final: report not sealed by final review")
            analysis_path = "analysis/block-report.json" if a.index["study_status"] in BLOCKED else "analysis/results.json"
            require({"freeze.json", "execution/index.json", analysis_path} <= review["files"].keys(),
                    "final: final review must seal freeze, execution and analysis evidence")
            if a.index["study_status"] == "completed":
                require("grades-seal.json" in review["files"], "final: final review must seal grades")
            require("execution/parent-provisioning.json" in review["files"],
                    "final: exact selected-Go-key proof not sealed by final review")
    result["semantic_truth_proven_by_audit"] = False
    if write:
        a.path("audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline saved-evidence audit; no execution, credentials or network.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent, help="saved artifact root")
    parser.add_argument("--stage", choices=("frozen", "collected", "grades", "graded"), help="default: complete final comparison or honest native access/compatibility block")
    parser.add_argument("--shard", choices=("a", "b"), help="audit one blind grades shard only")
    args = parser.parse_args(argv)
    try:
        result = audit(args.root, args.stage, args.shard, write=args.stage is None)
    except (AuditError, KeyError, TypeError, OSError, SyntaxError) as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
