"""Synthetic evidence only. Every write is under the caller's TemporaryDirectory."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import random

from verify import CONFIGS, SEED, TASKS, digest, visible_words, mapping_digest, VISIBLE_WORD_RULE

T0 = datetime(2026, 10, 7, 10, tzinfo=timezone.utc)
RUNTIME = "/private/tmp/opencode/researcher-eval-20261007T093207Z"


def stamp(seconds=0):
    return (T0+timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def write(root, name, data):
    p = Path(root)/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2)+"\n" if not isinstance(data, str) else data)
    return name


def read(root, name):
    return json.loads((Path(root)/name).read_text())


def edit(root, name, mutate):
    data = read(root, name)
    mutate(data)
    write(root, name, data)


def usage(raws):
    rows = []
    for raw in raws:
        r = raw or {}
        details = r.get("prompt_tokens_details") or {}
        prompt, completion = r.get("prompt_tokens"), r.get("completion_tokens")
        cached = details.get("cached_tokens", r.get("prompt_cache_hit_tokens"))
        written = details.get("cache_write_tokens", r.get("cache_creation_input_tokens"))
        reasoning = (r.get("completion_tokens_details") or {}).get("reasoning_tokens")
        uncached = prompt-cached-written if all(v is not None for v in (prompt, cached, written)) else None
        miss = r.get("prompt_cache_miss_tokens")
        if all(v is not None for v in (prompt, cached, miss)) and prompt == cached+miss:
            uncached = miss
        rows.append({"prompt_tokens": prompt, "completion_tokens": completion, "reasoning_tokens": reasoning,
                     "cache_read_tokens": cached, "cache_write_tokens": written, "uncached_input_tokens": uncached,
                     "non_reasoning_output_tokens": completion-reasoning if all(v is not None for v in (completion, reasoning)) else None,
                     "reported_cost": r.get("cost")})
    fields = ("prompt_tokens", "completion_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens",
              "uncached_input_tokens", "non_reasoning_output_tokens", "reported_cost")
    totals = {k: sum(r[k] for r in rows) if rows and all(r[k] is not None for r in rows) else None for k in fields}
    return {"complete": bool(rows) and all(totals[k] is not None for k in fields[:-1]), "raw_steps": raws, **totals}


def frozen(root, task_urls=None):
    root = Path(root)
    write(root, "scope.json", {"models": ["deepseek-v4.1-flash", "glm-5.3-flash"], "price_in_decision": False,
                               "planned_research_runs": 72, "runtime_root": RUNTIME, "prior_results_in_ranking": False})
    for name in ("plan.md", "contracts.md"):
        write(root, name, "Offline synthetic fixture, not production evidence.\n")
    write(root, "restart.json", {"authorized_by_user": True, "new_planned_cases": 72,
                                 "prior_cases_in_new_ranking": False, "runtime_root": RUNTIME})
    # Real auditor/analysis source is included in fixture freeze; candidate mock is inert.
    for name in ("verify.py", "analysis.py"):
        write(root, name, (Path(__file__).resolve().parents[2]/name).read_text())
    for name in ("runner.py", "webfetch.py", "dataset.py"):
        write(root, name, '"""Inert offline fixture."""\n')
    scope = {t: [("docs.example.test", f"/{t}/.*")] for t in TASKS}
    write(root, "webfetch.py", "# Inert, literal frozen scope fixture.\nALLOWLIST = " + repr(scope) + "\n")
    write(root, "tests/audit/mock_fixed.py", "# frozen synthetic fixed test\n")
    write(root, "api-evidence/contract.json", {"created_utc": stamp(-30), "contract": "offline mock"})
    write(root, "system.txt", "Identical research instructions.")
    write(root, "tools.json", [{"type": "function", "function": {"name": "webfetch", "parameters": {"type": "object"}}}])
    write(root, "protocol.json", {"version": 1, "endpoint": "https://opencode.ai/zen/go/v1/chat/completions",
                                 "models": ["deepseek-v4.1-flash", "glm-5.3-flash"], "efforts": ["low", "high", "max"],
                                 "limits": {"inference_steps": 8, "tool_steps": 7, "wall_s": 180, "visible_words": 400,
                                            "max_tokens": 16384, "fetch_attempts": 32},
                                 "schedule_seed": SEED, "statistics_seed": SEED+1,
                                 "blind_seed": 20261007093207,
                                 "effort_field": "reasoning_effort",
                                 "retries": {"client": 0, "auxiliary_inference": 0, "upstream": "unknown"},
                                 "source_drift": {"required_main_text_mismatch": "halt current case and all remaining cases"},
                                 "access_gate": {"counted": True}, "compatibility_gate": {"counted": True},
                                 "security": {"auth_post_redirects": False},
                                 "grading": {"checks": 6, "supported": 1, "contradicted": -1, "missing": 0, "unverifiable": 0,
                                             "extra_penalty": .5, "extra_cap": 2, "floor": -6},
                                 "qualification": {"operational_complete": True, "supported_grounded_checks": 6, "uncertainty": "pass",
                                                   "minimum_distinct_sources": 2, "critical_errors": 0, "unsupported_extras": 0},
                                 "eligibility": {"qualified_min": 10, "planned_per_config": 12, "every_task_qualified": True,
                                                 "required_contradictions": 0, "critical_errors": 0},
                                 "recommendation": {"speed_median_margin": .10, "paired_median_corroboration": True,
                                                    "paired_min_blocks": 6, "paired_min_tasks": 4, "p90_max_worse": .10,
                                                    "leave_one_task_out_direction": True, "price": False},
                                 "bootstrap_draws": 10000, "bootstrap_unit": "whole task, retaining repetitions and configurations",
                                 "visible_word_rule": VISIBLE_WORD_RULE,
                                 "audit_rules": {"caller_retries": 0, "source_drift": "stop_on_required_normalized_change",
                                                 "access_gate": "first_case_once_only", "step8": "tools_none",
                                                 "grading": "six_checks_plus_uncertainty", "eligibility_qualified_min": 10,
                                                 "recommendation": "quality_first_no_price", "bootstrap_draws": 10000,
                                                 "bootstrap_cluster": "whole_task", "word_count": "markdown_whitespace_without_urls"}})
    configurations = [{"id": c, "model": model, "effort": effort} for c, (model, effort) in CONFIGS.items()]
    config_ids = list(CONFIGS)
    cases, blocks = [], []
    for repetition in (1, 2):
        for t in range(6):
            block_id = f"B{len(blocks)+1:02}"
            subset = []
            for position in range(6):
                config = config_ids[(t+position) % 6]
                model, effort = CONFIGS[config]
                case = {"id": f"C{len(cases)+1:03}", "index": len(cases)+1, "block_id": block_id,
                        "position": position+1, "task_id": f"T{t+1}", "repetition": repetition,
                        "configuration_id": config, "model": model, "effort": effort}
                cases.append(case)
                subset.append(case["id"])
            blocks.append({"id": block_id, "task_id": f"T{t+1}", "repetition": repetition, "case_ids": subset})
    counts = {c: {str(p): 2 for p in range(1, 7)} for c in CONFIGS}
    write(root, "schedule.json", {"seed": SEED, "algorithm": "seeded cyclic Latin fixture", "configurations": configurations,
                                 "blocks": blocks, "cases": cases, "position_counts": counts})
    tasks, gold, sources = [], {}, []
    source_text = "Official documented claim. A separate supported limitation. High contention may occur."
    for task in sorted(TASKS):
        urls = task_urls[task] if task_urls else [f"https://docs.example.test/{task}/p{i}" for i in (1, 2)]
        tasks.append({"id": task, "slug": task.lower(), "title": f"Decision {task}", "prompt": f"Research decision {task}.",
                      "starting_urls": urls[:1], "allowed_url_patterns": [f"https://docs.example.test/{task}/.*"],
                      "required_source_urls": urls, "discovery_chain": []})
        for i, url in enumerate(urls, 1):
            page_text = source_text + f" Content page {i}."
            raw_path = write(root, f"dataset/archive/{task}-{i}.raw", page_text)
            text_path = write(root, f"dataset/archive/{task}-{i}.txt", page_text)
            sources.append({"id": f"{task}-{i}", "url": url, "final_url": url, "canonical_url": url, "status": 200,
                            "content_type": "text/plain", "raw_path": raw_path, "text_path": text_path,
                            "raw_sha256": digest(root/raw_path), "text_sha256": digest(root/text_path),
                            "anchors": [], "links": [], "retrieved_utc": stamp(-60)})
        ev = {"url": urls[0], "quote": "Official documented claim.", "archive_path": f"dataset/archive/{task}-1.txt"}
        gold[task] = {"checks": [{"id": f"C{i}", "requirement": f"Required claim {i}", "accepted": [], "contradicted": [],
                                  "source_evidence": [ev]} for i in range(1, 7)],
                      "uncertainty": {"pass": "Bounded limitation", "omit": "Absent", "fail": "Unsupported guarantee", "evidence": [ev]},
                      "critical_errors": [], "source_rules": {}}
    write(root, "dataset/tasks.json", tasks)
    write(root, "dataset/gold.json", {"version": 1, "tasks": gold})
    write(root, "dataset/sources.json", sources)
    write(root, "preflight/workflow.json", {"owner": "parent", "created_utc": stamp(-10), "candidate_post_starts": 0,
                                           "credential_provisioning": "parent_owned", "external_secret_paths_imported": False,
                                           "runtime_root": RUNTIME, "worker_bounds_verified": True,
                                           "protocol_reviewed": True, "api_evidence_reviewed": True})
    reseal(root)
    return cases


def reseal(root):
    root = Path(root)
    files = {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file() and
             str(p.relative_to(root)).split("/")[0] not in {"freeze.json", "execution", "blind", "private", "grades",
                                                          "adjudication", "analysis", "final-review", "report.md",
                                                          "grades-seal.json", "audit.json"}}
    write(root, "freeze.json", {"version": 1, "created_utc": stamp(), "files": files,
                               "schedule_sha256": digest(Path(root)/"schedule.json"), "no_candidate_calls_before_seal": True})


def cleanup(root):
    write(root, "execution/cleanup/processes.json", {"owned_only": True, "remaining": [], "runtime_root": RUNTIME})
    write(root, "execution/cleanup/credentials.json", {"redacted_before_persistence": True, "secret_matches": 0,
                                                       "scanned_paths": ["execution"], "external_secret_paths_read": False})
    return {"owned_processes_remaining": 0, "owned_process_check_path": "execution/cleanup/processes.json",
            "credential_scan_path": "execution/cleanup/credentials.json", "external_state_unchanged": True}


def provisioning(root):
    """Synthetic schema receipt: no credential was read, supplied or scanned."""
    write(root, "execution/parent-provisioning.json", {
        "started_utc": stamp(1), "finished_utc": stamp(3000),
        "credential_source": "parent read-only selected opencode-go integration credential",
        "fixture_only": True, "synthetic": True,
        "credential_store_copied": False, "worker_credential_store_access": False,
        "ephemeral_environment_only": True, "secret_matches": 0, "scanned_file_count": 100,
        "caller_retries": 0, "runner_returncode": 0})


def collected(root, status="completed", steps=2):
    root = Path(root)
    cases = read(root, "schedule.json")["cases"]
    paths, ledger = [], []
    clean = cleanup(root)
    for i, c in enumerate(cases):
        prefix = f"execution/cases/{c['id']}"
        unrun = status != "completed" and i > 0
        blocked = status == "access_blocked" and i == 0
        failed = status == "incomplete" and i == 0
        case_steps = 1 if blocked or failed else steps
        start, end = 10+i*30, 30+i*30
        record = {k: c[k] for k in ("block_id", "task_id", "repetition", "configuration_id", "model", "effort")}
        record.update({"case_id": c["id"], "schedule_index": c["index"],
                       "status": "not_run_access_gate" if unrun and status == "access_blocked" else "not_run_stop" if unrun else
                                 "access_gate_error" if blocked else "harness_error" if failed else "completed",
                       "operational_complete": not (unrun or blocked or failed), "start_utc": None if unrun else stamp(start),
                       "end_utc": None if unrun else stamp(end), "monotonic_start": None if unrun else start,
                       "monotonic_end": None if unrun else end, "wall_s": None if unrun else 20,
                       "assistant_span_s": None if unrun else 10, "inference_steps": 0 if unrun else case_steps,
                       "requests": [], "fetches": [], "answer_path": None, "visible_words": 0,
                       "usage": usage([]), "errors": ["Global regions required"] if blocked else ["interrupted"] if failed else [],
                       "cleanup": clean, "source_drift": [], "history_path": None})
        raw = None if blocked or failed else {"prompt_tokens": 100, "completion_tokens": 40,
                                            "completion_tokens_details": {"reasoning_tokens": 10},
                                            "prompt_tokens_details": {"cached_tokens": 20, "cache_write_tokens": 0}, "cost": .01}
        if not unrun:
            messages = [{"role": "system", "content": (root/"system.txt").read_text()},
                        {"role": "user", "content": f"Research decision {c['task_id']}."}]
            urls = next(t["required_source_urls"] for t in read(root, "dataset/tasks.json") if t["id"] == c["task_id"])
            answer = "Official documented claim. A separate supported limitation. " + urls[0]
            full_history = messages[:]
            source_text = (root/f"dataset/archive/{c['task_id']}-1.txt").read_text()
            for step in range(1, case_steps+1):
                body = {"model": c["model"], "reasoning_effort": c["effort"], "max_tokens": 16384,
                        "messages": full_history[:], "stream": False,
                        "tools": read(root, "tools.json") if step < 8 else [], "tool_choice": "auto" if step < 8 else "none"}
                if step == 8:
                    body.pop("tools"); body.pop("tool_choice")
                req_path = write(root, f"{prefix}/requests/{step}-body.json", body)
                native_message = {"role": "assistant", "content": answer if step == case_steps else "", "reasoning_content": "Native reasoning retained."}
                if step == 1 and not (blocked or failed):
                    native_message["tool_calls"] = [{"id": f"tool{j}", "type": "function", "function": {"name": "webfetch",
                                                       "arguments": json.dumps({"url": urls[j-1]})}} for j in (1, 2)]
                resp_path = write(root, f"{prefix}/requests/{step}-response.json", {"error": {"message": "Global regions required" if blocked else "Internal server error"}, "usage": raw} if blocked or failed else
                                  {"choices": [{"message": native_message, "finish_reason": "stop" if step == case_steps else "tool_calls"}], "usage": raw})
                req_start, req_end = stamp(start+step), stamp(start+step+.5)
                record["requests"].append({"step": step, "started_utc": req_start, "ended_utc": req_end, "elapsed_s": .5,
                                            "request_path": req_path, "response_path": resp_path, "http_status": 400 if blocked else 500 if failed else 200,
                                            "error": "denied" if blocked else "interrupted" if failed else None, "usage": raw,
                                            "intent_logged": True, "client_post_starts": 1, "client_post_started_utc": req_start})
                ledger.append({"case_id": c["id"], "step": step, "request_path": req_path, "started_utc": req_start})
                if not (blocked or failed):
                    full_history.append(native_message)
                    if step == 1:
                        full_history.extend({"role": "tool", "tool_call_id": f"tool{j}", "content": json.dumps({"status": "ok",
                                             "url": urls[j-1], "http_status": 200,
                                             "truncated": False, "error": None, "text": (root/f"dataset/archive/{c['task_id']}-{j}.txt").read_text()})} for j in (1, 2))
            record["history_path"] = write(root, f"{prefix}/history.json", full_history)
            record["usage"] = usage([raw]*case_steps)
            if not (blocked or failed):
                record["answer_path"] = write(root, f"{prefix}/answer.txt", answer)
                record["visible_words"] = visible_words(answer)
                for j in (1, 2):
                    source = next(s for s in read(root, "dataset/sources.json") if s["id"] == f"{c['task_id']}-{j}")
                    text = (root/source["text_path"]).read_text()
                    fp = f"{prefix}/fetches/f{j}"
                    raw_path = write(root, fp+".raw", text)
                    text_path = write(root, fp+".txt", text)
                    shown_path = write(root, fp+"-shown.txt", text)
                    record["fetches"].append({"id": f"F{j}", "tool_call_id": f"tool{j}", "requested_url": source["url"], "final_url": source["url"], "status": "ok", "http_status": 200,
                                               "redirects": [], "started_utc": stamp(start+12+j), "ended_utc": stamp(start+12+j+.1),
                                               "elapsed_s": .1, "raw_path": raw_path, "text_path": text_path, "model_text_path": shown_path,
                                               "raw_sha256": digest(root/raw_path), "text_sha256": digest(root/text_path), "model_text_sha256": digest(root/shown_path),
                                               "raw_bytes": len(text.encode()), "text_bytes": len(text.encode()), "truncated": False,
                                               "error": None, "frozen_source_match": {"raw": True, "text": True}})
        paths.append(write(root, f"{prefix}/record.json", record))
    write(root, "execution/post-starts.jsonl", "".join(json.dumps(row)+"\n" for row in ledger))
    write(root, "execution/index.json", {"study_status": status, "gate_case_id": cases[0]["id"],
                                        "gate_status": "access_blocked" if status == "access_blocked" else "incomplete" if status == "incomplete" else "passed",
                                        "compatibility_gates": {c["configuration_id"]: {"case_id": c["id"], "status":
                                            "passed" if status == "completed" else "not_run" if c["index"] > 1 else
                                            "access_blocked" if status == "access_blocked" else "incomplete"} for c in cases[:6]},
                                        "stop": None if status == "completed" else {"case_id": cases[0]["id"], "schedule_index": 1,
                                            "reason": "access_gate_error" if status == "access_blocked" else "harness_error",
                                            "http_status": 400 if status == "access_blocked" else 500,
                                            "response_path": f"execution/cases/{cases[0]['id']}/requests/1-response.json"},
                                       "planned_cases": 72, "attempted_cases": 72 if status == "completed" else 1,
                                        "terminal_cases": 72, "cases": paths, "cleanup": clean})
    provisioning(root)


def blinded(root):
    root = Path(root)
    records = [read(root, p) for p in read(root, "execution/index.json")["cases"]]
    random.Random(read(root, "protocol.json").get("blind_seed", 20261007093207)).shuffle(records)
    mapping, files, ids = {}, {}, []
    for i, r in enumerate(records):
        blind = f"opaque{i:03}"
        ids.append(blind)
        mapping[blind] = r["case_id"]
        row = {"blind_id": blind, "task_id": r["task_id"], "prompt": f"Research decision {r['task_id']}.",
               "answer": (root/r["answer_path"]).read_text() if r["answer_path"] else "", "sources": [],
               "rubric": read(root, "dataset/gold.json")["tasks"][r["task_id"]],
               "mechanical": {"word_cap": True, "fetched_two_sources": bool(r["fetches"]), "source_rules": True, "tool_rules": True}}
        for j in (1, 2):
            src = next(s for s in read(root, "dataset/sources.json") if s["id"] == f"{r['task_id']}-{j}")
            path = write(root, f"blind/cases/{blind}/source-{j}.txt", (root/src["text_path"]).read_text())
            row["sources"].append({"url": src["url"], "source_path": path, "status": "fetched" if r["fetches"] else "frozen_reference",
                                   "frozen": not bool(r["fetches"])})
            if r["fetches"]:
                row["sources"][-1]["candidate_visible_path"] = path
            files[path] = digest(root/path)
        name = write(root, f"blind/cases/{blind}/case.json", row)
        files[name] = digest(root/name)
    write(root, "blind/index.json", {"shards": {"a": ids[:36], "b": ids[36:]}, "cases": ids})
    write(root, "private/unblind.json", {"mapping": mapping, "sealed_hashes": files})


def grades(root):
    root = Path(root)
    index = read(root, "blind/index.json")
    for shard, ids in index["shards"].items():
        for blind in ids:
            row = read(root, f"blind/cases/{blind}/case.json")
            if not row["answer"]:
                continue
            ev = {"url": row["sources"][0]["url"], "source_path": row["sources"][0]["source_path"], "quote": "Official documented claim."}
            grade = {"blind_id": blind, "task_id": row["task_id"],
                     "checks": [{"id": f"C{i}", "status": "supported", "answer_quote": "Official documented claim.",
                                 "evidence": [ev], "rationale": "The official text entails the stated synthetic claim.", "citation_status": "entailing"} for i in range(1, 7)],
                     "uncertainty": {"status": "pass", "answer_quote": "A separate supported limitation.", "rationale": "Explicit bounded limitation.", "evidence": [ev]},
                     "citations": [{"answer_quote": "Official documented claim.", "url": ev["url"], "support": "entailing", "anchor_compliance": True,
                                    "rationale": "Attached official citation supports the claim.", "evidence": [ev]}],
                     "critical_errors": [], "unsupported_extras": [],
                     "compliance": {"full_urls": True, "word_cap": True, "english": True, "fetched_two_sources": True,
                                    "source_rules": True, "tool_rules": True, "discovery_chain": "complete"},
                     "ambiguous": False, "notes": "Synthetic offline judgment, not a real benchmark."}
            write(root, f"grades/shard-{shard}/{blind}.json", grade)
    grade_seal(root)


def runner_blind_style(root):
    """Actual export shapes, without importing/executing the runner."""
    index = read(root, "blind/index.json")
    mapping = read(root, "private/unblind.json")
    for blind in index["cases"]:
        name = f"blind/cases/{blind}/case.json"
        row = read(root, name)
        fetched = {s["url"]: s["source_path"] for s in row["sources"] if s["status"] == "fetched"}
        for j in (1, 2):
            url = next(t["required_source_urls"] for t in read(root, "dataset/tasks.json") if t["id"] == row["task_id"])[j-1]
            path = write(root, f"blind/cases/{blind}/sources/frozen-{j}.txt", (Path(root)/f"dataset/archive/{row['task_id']}-{j}.txt").read_text())
            row["sources"].append({"url": url, "source_path": path, "status": "frozen_reference", "frozen": True})
            mapping["sealed_hashes"][path] = digest(Path(root)/path)
        source_paths = {s["url"]: s["source_path"] for s in row["sources"]}
        source_paths.update(fetched)  # Fetched evidence remains preferred over same-URL gold references.
        def transform(value):
            if isinstance(value, dict):
                obj = {k: transform(v) for k, v in value.items() if k not in {"archive_path", "raw_path", "text_path"}}
                if "url" in obj and obj["url"].split("#")[0] in source_paths:
                    obj["source_path"] = source_paths[obj["url"].split("#")[0]]
                return obj
            if isinstance(value, list):
                return [transform(v) for v in value]
            return value
        row["rubric"] = transform(row["rubric"])
        r = read(root, f"execution/cases/{mapping['mapping'][blind]}/record.json")
        row["mechanical"].update(attempted=not r["status"].startswith("not_run"), operational_complete=r["operational_complete"],
                                 visible_words=r["visible_words"], distinct_fetched_pages=2 if r["fetches"] else 0,
                                 fetch_attempts=len(r["fetches"]), truncated_fetches=sum(f["truncated"] for f in r["fetches"]))
        write(root, name, row)
        mapping["sealed_hashes"][name] = digest(Path(root)/name)
    index["cases"] = [f"blind/cases/{b}/case.json" for b in index["cases"]]
    write(root, "blind/index.json", index)
    write(root, "private/unblind.json", mapping)


def grade_seal(root, overrides=None):
    root = Path(root)
    review = write(root, "grades/review/blind-review.json", {"blind_review": True, "reviewer_type": "offline_fixture", "passed": True})
    effective = {p.stem: str(p.relative_to(root)) for p in root.glob("grades/shard-*/*.json")}
    effective.update(overrides or {})
    files = {str(p.relative_to(root)): digest(p) for pat in ("grades/**/*.json", "adjudication/*.json") for p in root.glob(pat)}
    write(root, "grades-seal.json", {"created_utc": stamp(3000), "files": files, "effective_grades": effective, "blind_review_paths": [review],
                                    "mapping_sha256": mapping_digest(read(root, "private/unblind.json"))})
    edit(root, "private/unblind.json", lambda d: d.update(unblinded_utc=stamp(3001)))


def complete(root):
    frozen(root)
    collected(root)
    blinded(root)
    grades(root)


def final_review(root):
    root = Path(root)
    write(root, "report.md", "Offline fixture report: quality and qualified latency only. Not real results.\n")
    paths = ["report.md", "freeze.json", "execution/index.json"]
    if (root/"analysis/results.json").exists():
        paths += ["analysis/results.json", "grades-seal.json"]
    if (root/"analysis/block-report.json").exists():
        paths += ["analysis/block-report.json"]
    if (root/"execution/parent-provisioning.json").exists():
        paths += ["execution/parent-provisioning.json"]
    write(root, "final-review/index.json", {"saved_only": True, "passed": True, "files": {p: digest(root/p) for p in paths}})
