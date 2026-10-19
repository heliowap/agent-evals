"""P4 B1--B4 regressions: read-only real inputs, all generated evidence temporary.

Runner calls here use public offline seams with injected transports/fetchers and
an empty key; no native POST, credential access, subprocess or auth occurs.
"""
import copy
from datetime import datetime, timedelta
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from verify import Auditor, AuditError, audit, digest, normalized, frozen_tool_scope
import fixtures as f

ACTUAL = Path(__file__).resolve().parents[2]


def real_runner():
    spec = importlib.util.spec_from_file_location("offline_review_runner", ACTUAL/"runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence_entries():
    gold = f.read(ACTUAL, "dataset/gold.json")
    return [e for task in gold["tasks"].values() for bundle in task["checks"] + [task["uncertainty"]]
            for e in bundle["source_evidence"]]


def wire_root(root, runner):
    tasks = f.read(ACTUAL, "dataset/tasks.json")
    urls = {t["id"]: [t["required_source_urls"][0].rstrip("/")+"/mock/p1",
                      t["required_source_urls"][0].rstrip("/")+"/mock/p2"] for t in tasks}
    # Version-pinned file allowlists need a permitted documentation path, not a
    # child of a fixed raw file. These are only opaque synthetic source paths.
    urls["T2"] = ["https://nodejs.org/download/release/v24.21.0/docs/api/mock/p1",
                  "https://nodejs.org/download/release/v24.21.0/docs/api/mock/p2"]
    f.frozen(root, task_urls=urls)
    for name in ("runner.py", "webfetch.py"):
        f.write(root, name, (ACTUAL/name).read_text())
    public = f.read(root, "dataset/tasks.json")
    for row, actual in zip(public, tasks):
        row["allowed_url_patterns"] = actual["allowed_url_patterns"]
    f.write(root, "dataset/tasks.json", public)
    f.reseal(root)
    f.write(root, "private/freeze-receipt.json", {"freeze_sha256": digest(root/"freeze.json")})
    f.collected(root)


def native_call(ident, url, name="webfetch", args=None, kind="function"):
    return {"id": ident, "type": kind, "function": {"name": name,
            "arguments": json.dumps({"url": url}) if args is None else args}}


def replace_case_offline(root, runner, scenario):
    """Use actual run_case then rebase only synthetic clocks to the fixture block.

    Durations and all relative timing are retained. This is not real inference
    evidence; rebasing lets the 71 independent fixture rows remain sequential.
    """
    case = f.read(root, "schedule.json")["cases"][-1]
    task = next(t for t in f.read(root, "dataset/tasks.json") if t["id"] == case["task_id"])
    urls = task["required_source_urls"]
    directory = root/"execution/cases"/case["id"]
    shutil.rmtree(directory)
    ledger_path = root/"offline-case-ledger.jsonl"
    batches = []
    extra = None
    if scenario == "preview":
        extra = urls[1].rsplit("/", 1)[0]+"/extra"
        batches = [[native_call("t1", urls[0]), native_call("t2", extra)]]
    elif scenario == "overflow":
        batches = [[native_call(f"t{i}", urls[i % 2]) for i in range(32)], [native_call("t32", urls[0])]]
    elif scenario == "excessive_batch":
        batches = [[native_call(f"t{i}", urls[0]) for i in range(33)]]
    elif scenario == "step8":
        batches = [[native_call(f"t{i}", urls[i % 2])] for i in range(8)]
    else:
        bad_url = urls[1]
        name, args, kind = "webfetch", None, "function"
        if scenario == "shell":
            name = "shell"
        elif scenario == "malformed":
            args = "{invalid"
        elif scenario == "extra_args":
            args = json.dumps({"url": bad_url, "execute": True})
        elif scenario == "wrong_type":
            kind = "shell"
        elif scenario == "foreign":
            bad_url = "https://evil.test/secret"
        elif scenario == "broad_scope":
            # The last case is T6 in the mock Latin schedule; archive patterns
            # allow go.dev/, while tool scope allows only /doc/toolchain/modules.
            bad_url = "https://go.dev/blog/outside-tool-scope"
        batches = [[native_call("t1", urls[0]), native_call("t2", bad_url, name, args, kind)]]
    answer = "Official documented claim. A separate supported limitation. " + urls[0]
    calls = iter(batches)
    def transport(body, key, session, deadline, mark_started):
        mark_started()
        batch = next(calls, None)
        message = {"role": "assistant", "content": "" if batch else answer, "reasoning_content": "Saved native reasoning."}
        if batch:
            message["tool_calls"] = batch
            if body.get("tools") is None:  # Unexpected native step-eight output, never executed.
                message["content"] = answer
        return 200, json.dumps({"choices": [{"message": message, "finish_reason": "tool_calls" if batch else "stop"}]}).encode()
    def fetcher(url, task_id, deadline):
        if scenario in {"foreign", "broad_scope"} and url not in urls:
            return {"status": "rejected", "final_url": None, "redirects": [], "truncated": False,
                    "error": "outside frozen tool scope", "http_status": None, "raw": None, "text": None, "model_text": None}
        if scenario == "redirect" and url == urls[1]:
            return {"status": "rejected", "final_url": url, "redirects": [{"from": url, "to": "https://evil.test/secret", "status": 302}],
                    "truncated": False, "error": "redirect outside frozen tool scope", "http_status": 302,
                    "raw": None, "text": None, "model_text": None}
        source = next((s for s in f.read(root, "dataset/sources.json") if s["url"] == url), None)
        text = (root/source["text_path"]).read_text() if source else "Official documented claim. " + "whole documentation "*16000
        marker = "\n[TRUNCATED: whole-document text exceeded 256 KiB]\n"
        preview = text.encode()[:262144-len(marker)].decode()+marker if len(text.encode()) > 262144 else text
        return {"status": "ok", "final_url": url, "redirects": [], "truncated": preview != text,
                "error": None, "http_status": 200, "content_type": "text/plain", "raw": text.encode(), "text": text, "model_text": preview}
    record = runner.run_case({"case": case, "task": task, "protocol": f.read(root, "protocol.json"),
                              "tools": f.read(root, "tools.json"), "system": (root/"system.txt").read_text(),
                              "sources": f.read(root, "dataset/sources.json"), "directory": str(directory),
                              "ledger_path": str(ledger_path)}, "", transport=transport, fetcher=fetcher)
    old_start = datetime.fromisoformat(record["start_utc"])
    base = datetime.fromisoformat(f.stamp(10+(case["index"]-1)*30).replace("Z", "+00:00"))
    delta = base-old_start
    def times(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.endswith("_utc") and v:
                    obj[k] = (datetime.fromisoformat(v.replace("Z", "+00:00"))+delta).isoformat()
                else:
                    times(v)
        elif isinstance(obj, list):
            for item in obj:
                times(item)
    times(record)
    mono_delta = 10+(case["index"]-1)*30-record["monotonic_start"]
    record["monotonic_start"] += mono_delta; record["monotonic_end"] += mono_delta
    record["cleanup"] = f.cleanup(root)
    f.write(root, f"execution/cases/{case['id']}/record.json", record)
    index = f.read(root, "execution/index.json")
    if record["status"] == "harness_error":
        index["study_status"] = "incomplete"
        f.write(root, "execution/index.json", index)
    ledger = []
    for path in index["cases"]:
        r = f.read(root, path)
        ledger.extend({"case_id": r["case_id"], "step": req["step"], "request_path": req["request_path"],
                       "started_utc": req["client_post_started_utc"]} for req in r["requests"] if req["client_post_starts"])
    f.write(root, "execution/post-starts.jsonl", "".join(json.dumps(r)+"\n" for r in ledger))
    ledger_path.unlink()
    return record, task


class ReviewRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = real_runner()

    def test_B1_all_53_real_factual_and_uncertainty_quotes(self):
        entries = evidence_entries()
        missing = [e["archive_path"] for e in entries if not (ACTUAL/e["archive_path"]).is_file()]
        if missing:
            self.skipTest("P1 fresh source archives pending; parent must rerun full suite after archive finalization")
        self.assertEqual(len(entries), 53)
        for entry in entries:
            with self.subTest(source=entry["source_id"], quote=entry["quote"]):
                body = (ACTUAL/entry["archive_path"]).read_text()
                self.assertIn(normalized(entry["quote"]), normalized(body))
                self.assertNotIn(normalized("NOT "+entry["quote"]), normalized(body))
                self.assertNotIn(normalized("FABRICATED_VERSION_999 "+entry["quote"]), normalized(body))
        self.assertEqual(normalized("x[go](https://example.test/a(b))()"), "xgo()")
        self.assertEqual(normalized(r"**Do not** use `/srv/jobs/*.js` or `a != b`; \* is literal; ‘1.21.9’"),
                         "Do not use /srv/jobs/*.js or a != b; * is literal; '1.21.9'")
        self.assertNotEqual(normalized("Use *.js"), normalized("Use .js"))
        self.assertNotEqual(normalized("a != b"), normalized("a == b"))
        self.assertNotIn(normalized("Workers do not inherit restrictions."), normalized("Workers inherit restrictions."))

    def test_B1_actual_finalized_dataset_frozen_only_in_temporary_copy(self):
        if not (ACTUAL/"dataset/archive-state.json").is_file() or not f.read(ACTUAL, "dataset/archive-state.json").get("shared_extraction_finalized"):
            self.skipTest("P1 fresh finalized archive pending; parent must rerun full suite")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            f.frozen(root)
            shutil.rmtree(root/"dataset")
            shutil.copytree(ACTUAL/"dataset", root/"dataset", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            f.write(root, "webfetch.py", (ACTUAL/"webfetch.py").read_text())
            f.reseal(root)
            # Saved retrieval dates precede this synthetic seal; real root stays unsealed.
            latest = max(datetime.fromisoformat(s["retrieved_utc"].replace("Z", "+00:00")) for s in f.read(root, "dataset/sources.json"))
            f.edit(root, "freeze.json", lambda d: d.update(created_utc=(latest+timedelta(days=1)).isoformat()))
            self.assertTrue(f.read(root, "dataset/archive-state.json")["shared_extraction_finalized"])
            self.assertTrue(audit(root, "frozen")["ok"])

    def test_B2_actual_runner_export_full_and_linked_truncated_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); wire_root(root, self.runner)
            r, _ = replace_case_offline(root, self.runner, "preview")
            self.assertTrue(audit(root, "collected")["ok"])
            self.runner.blind_export(root)
            a = Auditor(root).frozen().collected().blind()
            row = next(v for b, v in a.blinds.items() if a.mapping[b] == r["case_id"])
            truncated = next(s for s in row["sources"] if s.get("candidate_visible_path") and s["candidate_visible_path"] != s["source_path"])
            equal = next(s for s in row["sources"] if s.get("candidate_visible_path") == s["source_path"])
            self.assertEqual((root/equal["source_path"]).read_bytes(), (root/equal["candidate_visible_path"]).read_bytes())
            self.assertGreater(len((root/truncated["source_path"]).read_bytes()), 262144)
            self.assertEqual((root/truncated["candidate_visible_path"]).read_bytes(), (root/r["fetches"][1]["model_text_path"]).read_bytes())
            blind = row["blind_id"]; name = f"blind/cases/{blind}/case.json"
            private_original = f.read(root, "private/unblind.json")
            original = f.read(root, name)
            preview = truncated["candidate_visible_path"]
            original_preview = (root/preview).read_bytes()
            def must_fail(pattern):
                with self.assertRaisesRegex(AuditError, pattern):
                    Auditor(root).frozen().collected().blind()
            (root/preview).write_text("Wrong preview")
            must_fail("changed hash")
            private = copy.deepcopy(private_original); private["sealed_hashes"][preview] = digest(root/preview)
            f.write(root, "private/unblind.json", private)
            must_fail("preview differs")
            (root/preview).write_bytes(original_preview); f.write(root, "private/unblind.json", private_original)
            private = copy.deepcopy(private_original); private["sealed_hashes"].pop(preview)
            f.write(root, "private/unblind.json", private)
            must_fail("preview lacks sealed hash")
            (root/preview).write_text("This preview is by DeepSeek.")
            private = copy.deepcopy(private_original); private["sealed_hashes"][preview] = digest(root/preview)
            f.write(root, "private/unblind.json", private)
            must_fail("blind identity/path leak")
            (root/preview).write_bytes(original_preview); f.write(root, "private/unblind.json", private_original)
            altered = copy.deepcopy(original)
            next(s for s in altered["sources"] if s["source_path"] == truncated["source_path"])["candidate_visible_path"] = "blind/cases/other/source.txt"
            f.write(root, name, altered)
            private = copy.deepcopy(private_original); private["sealed_hashes"][name] = digest(root/name)
            f.write(root, "private/unblind.json", private)
            must_fail("preview must be linked inside")
            f.write(root, name, original); f.write(root, "private/unblind.json", private_original)
            f.write(root, f"blind/cases/{blind}/unlinked.txt", "unlinked preview")
            must_fail("extra grader input")

    def test_B3_actual_runner_rejections_overflow_and_mechanical_tampering(self):
        scenarios = {"shell": (False, False), "malformed": (False, False), "extra_args": (False, False),
                     "wrong_type": (False, False), "foreign": (False, True), "broad_scope": (False, True),
                     "redirect": (False, True), "overflow": (True, False), "step8": (True, False),
                     "excessive_batch": (True, False)}
        for scenario, expected in scenarios.items():
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); wire_root(root, self.runner)
                r, task = replace_case_offline(root, self.runner, scenario)
                self.assertTrue(audit(root, "collected")["ok"])
                self.runner.blind_export(root)
                a = Auditor(root).frozen().collected().blind()
                independent = a.mechanical_compliance(r)
                reference = self.runner.mechanical_compliance(root, r, task, f.read(root, "dataset/sources.json"))
                self.assertEqual(independent, reference)
                self.assertEqual((independent["source_rules"], independent["tool_rules"]), expected)
                row = next(v for b, v in a.blinds.items() if a.mapping[b] == r["case_id"])
                key = "source_rules" if not expected[0] else "tool_rules"
                name = f"blind/cases/{row['blind_id']}/case.json"
                f.edit(root, name, lambda d: d["mechanical"].update({key: True}))
                f.edit(root, "private/unblind.json", lambda d: d["sealed_hashes"].update({name: digest(root/name)}))
                with self.assertRaisesRegex(AuditError, "fabricated mechanical "+key):
                    Auditor(root).frozen().collected().blind()

    def test_B3_real_task_scope_and_identical_content_deduplication(self):
        task = f.read(ACTUAL, "dataset/tasks.json")[0]
        a = Auditor(ACTUAL); a.tasks = {"T1": task}; a.sources = f.read(ACTUAL, "dataset/sources.json")
        a.tool_scope = frozen_tool_scope((ACTUAL/"webfetch.py").read_text())
        self.assertFalse(a.allowed_url("https://docs.github.com/en/rest", "T1"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); wire_root(root, self.runner)
            # Two differently addressed frozen pages legitimately have the same
            # extracted content. Change only this temporary pre-freeze fixture.
            sources = f.read(root, "dataset/sources.json")
            pair = [s for s in sources if s["id"].startswith("T1-")]
            for kind in ("raw", "text"):
                (root/pair[1][kind+"_path"]).write_bytes((root/pair[0][kind+"_path"]).read_bytes())
                pair[1][kind+"_sha256"] = pair[0][kind+"_sha256"]
            f.write(root, "dataset/sources.json", sources); f.reseal(root)
            f.write(root, "private/freeze-receipt.json", {"freeze_sha256": digest(root/"freeze.json")})
            f.collected(root); self.runner.blind_export(root)
            a = Auditor(root).frozen().collected().blind()
            r = a.records[0]
            independent = a.mechanical_compliance(r)
            self.assertEqual(independent, self.runner.mechanical_compliance(root, r, a.tasks["T1"], sources))
            self.assertEqual(independent["distinct_fetched_pages"], 1)
            self.assertFalse(independent["fetched_two_sources"])
            blind = next(b for b, c in a.mapping.items() if c == r["case_id"])
            name = f"blind/cases/{blind}/case.json"
            f.edit(root, name, lambda d: d["mechanical"].update(requested_tool_calls=999))
            f.edit(root, "private/unblind.json", lambda d: d["sealed_hashes"].update({name: digest(root/name)}))
            with self.assertRaisesRegex(AuditError, "fabricated mechanical requested_tool_calls"):
                Auditor(root).frozen().collected().blind()

    def test_B4_native_gate_denials_and_ordinary_interruptions(self):
        positives = [(401, "Invalid API key"), (403, "Forbidden"), (400, "A Go subscription is required"),
                     (402, "Entitlement unavailable"), (429, "Workspace privacy settings require Global regions"),
                     (500, "Authentication failed")]
        negatives = [(400, "Malformed request"), (500, "Internal server error"), (429, "Rate limit exceeded")]
        for status, message in positives+negatives:
            with self.subTest(status=status, message=message), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); f.frozen(root); f.collected(root, "access_blocked")
                index = f.read(root, "execution/index.json"); path = index["cases"][0]; r = f.read(root, path)
                req = r["requests"][0]; req["http_status"] = status; req["error"] = {"message": message}
                native = {"error": {"message": message}}
                f.write(root, req["response_path"], native); f.write(root, path, r)
                index["stop"].update(http_status=status)
                f.write(root, "execution/index.json", index)
                is_access = self.runner.access_denial(status, native)
                self.assertEqual(is_access, (status, message) in positives)
                if is_access:
                    self.assertEqual(audit(root, "collected")["study_status"], "access_blocked")
                else:
                    with self.assertRaisesRegex(AuditError, "missing native denial evidence"):
                        audit(root, "collected")
                    r["status"] = "provider_error"; f.write(root, path, r)
                    index.update(study_status="incomplete", gate_status="incomplete")
                    index["compatibility_gates"][r["configuration_id"]]["status"] = "incomplete"
                    index["stop"]["reason"] = "provider_error"
                    f.write(root, "execution/index.json", index)
                    for skipped in index["cases"][1:]:
                        f.edit(root, skipped, lambda d: d.update(status="not_run_first_failure"))
                    self.assertEqual(audit(root, "collected")["study_status"], "incomplete")
                    with self.assertRaisesRegex(AuditError, "incomplete.*missing"):
                        audit(root)


if __name__ == "__main__":
    unittest.main()
