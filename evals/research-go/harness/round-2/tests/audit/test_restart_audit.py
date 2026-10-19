"""Restart behavior through saved audit/analysis interfaces, entirely offline."""
import copy
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import analysis
from verify import audit, AuditError, digest, PUBLIC_CANONICAL
import fixtures as f


def refresh_index(root):
    index = f.read(root, "execution/index.json")
    records = [f.read(root, name) for name in index["cases"]]
    index["attempted_cases"] = sum(not r["status"].startswith("not_run") for r in records)
    for config, gate in index["compatibility_gates"].items():
        first = next(r for r in records if r["configuration_id"] == config)
        gate["status"] = ("not_run" if first["status"].startswith("not_run") else
                          "passed" if first["operational_complete"] else
                          "access_blocked" if first["status"] == "access_gate_error" else
                          "compatibility_blocked" if first["status"] == "compatibility_error" else "incomplete")
    index["gate_status"] = index["compatibility_gates"][records[0]["configuration_id"]]["status"]
    f.write(root, "execution/index.json", index)
    ledger = [{"case_id": r["case_id"], "step": req["step"], "request_path": req["request_path"],
               "started_utc": req["client_post_started_utc"]}
              for r in records for req in r["requests"] if req["client_post_starts"]]
    f.write(root, "execution/post-starts.jsonl", "".join(json.dumps(row)+"\n" for row in ledger))


def save_failure(root, position, step, study_status, payload, http_status=400, halt=True):
    """Mutate synthetic terminal evidence; no production record ever enters here."""
    index = f.read(root, "execution/index.json")
    name = index["cases"][position-1]
    r = f.read(root, name)
    for req in r["requests"][step:]:
        (root/req["request_path"]).unlink(); (root/req["response_path"]).unlink()
    r["requests"] = r["requests"][:step]
    req = r["requests"][-1]
    req.update(http_status=http_status, error={"message": "saved native HTTP error"}, usage=None)
    if step > 1:
        start = 10+(position-1)*30
        req.update(started_utc=f.stamp(start+19), ended_utc=f.stamp(start+19.5),
                   client_post_started_utc=f.stamp(start+19))
    f.write(root, req["response_path"], payload)
    history = f.read(root, req["request_path"])["messages"]
    f.write(root, r["history_path"], history)
    if r["answer_path"]:
        (root/r["answer_path"]).unlink()
    if step == 1:
        for fetch in r["fetches"]:
            for kind in ("raw", "text", "model_text"):
                (root/fetch[kind+"_path"]).unlink()
        r["fetches"] = []
    r.update(status="access_gate_error" if study_status == "access_blocked" else
             "compatibility_error" if study_status == "compatibility_blocked" else "provider_error",
             operational_complete=False, inference_steps=step, answer_path=None, visible_words=0,
             errors=["native error; no replay"], usage=f.usage([q["usage"] for q in r["requests"]]))
    f.write(root, name, r)
    if halt:
        index.update(study_status=study_status, stop={"case_id": r["case_id"], "schedule_index": position,
                     "reason": r["status"], "http_status": http_status, "response_path": req["response_path"]})
        suffix = ("not_run_access_gate" if study_status == "access_blocked" else
                  "not_run_compatibility_block" if study_status == "compatibility_blocked" else "not_run_first_failure")
        for skipped in index["cases"][position:]:
            row = f.read(root, skipped)
            shutil.rmtree((root/skipped).parent)
            row.update(status=suffix, operational_complete=False, start_utc=None, end_utc=None,
                       monotonic_start=None, monotonic_end=None, wall_s=None, assistant_span_s=None,
                       inference_steps=0, requests=[], fetches=[], answer_path=None, visible_words=0,
                       usage=f.usage([]), errors=[], source_drift=[], history_path=None)
            f.write(root, skipped, row)
    f.write(root, "execution/index.json", index)
    refresh_index(root)
    return name


def public_fixture(root, text='Official documented claim. Public example {"Authorization": "documented field"}.'):
    f.frozen(root)
    sources = f.read(root, "dataset/sources.json")
    source = sources[0]
    source.update(url=PUBLIC_CANONICAL, final_url=PUBLIC_CANONICAL, canonical_url=PUBLIC_CANONICAL)
    for kind in ("raw", "text"):
        f.write(root, source[kind+"_path"], text)
        source[kind+"_sha256"] = digest(root/source[kind+"_path"])
    f.write(root, "dataset/sources.json", sources)
    tasks = f.read(root, "dataset/tasks.json")
    tasks[0]["required_source_urls"][0] = PUBLIC_CANONICAL
    tasks[0]["starting_urls"] = [PUBLIC_CANONICAL]
    tasks[0]["allowed_url_patterns"].append(r"https://developers\.cloudflare\.com/d1/best-practices/read-replication/(?:index\.md)?")
    f.write(root, "dataset/tasks.json", tasks)
    scope = {t: [("docs.example.test", f"/{t}/.*")] for t in f.TASKS}
    scope["T1"].append(("developers.cloudflare.com", r"/d1/best-practices/read-replication/(?:index\.md)?"))
    f.write(root, "webfetch.py", "ALLOWLIST = "+repr(scope)+"\n")
    f.reseal(root)
    f.collected(root)


def native_failure_fixture(root, position, step, status, raw, http_status):
    """Actual run_case with injected bytes/empty key; rebase fixture clocks only."""
    f.frozen(root); f.collected(root)
    name = save_failure(root, position, step, status, {"error": {"message": raw.decode()}}, http_status)
    case = f.read(root, "schedule.json")["cases"][position-1]
    task = next(t for t in f.read(root, "dataset/tasks.json") if t["id"] == case["task_id"])
    directory = (root/name).parent
    shutil.rmtree(directory)
    spec = importlib.util.spec_from_file_location("offline_native_error_runner", Path(__file__).resolve().parents[2]/"runner.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    calls = []
    def transport(body, key, session, deadline, mark_started):
        mark_started(); calls.append(body)
        if len(calls) == step:
            return http_status, raw
        message = {"role": "assistant", "content": "", "tool_calls": [
            {"id": "invalid-offline-call", "type": "function", "function": {"name": "webfetch", "arguments": "{invalid"}}]}
        return 200, json.dumps({"choices": [{"message": message, "finish_reason": "tool_calls"}]}).encode()
    def never_fetch(*args):
        raise AssertionError("invalid offline arguments must not invoke fetcher")
    temporary_ledger = root/"offline-native-ledger.jsonl"
    r = runner.run_case({"case": case, "task": task, "protocol": f.read(root, "protocol.json"),
                         "tools": f.read(root, "tools.json"), "system": (root/"system.txt").read_text(),
                         "sources": f.read(root, "dataset/sources.json"), "directory": str(directory),
                         "ledger_path": str(temporary_ledger)}, "", transport=transport, fetcher=never_fetch)
    base_seconds = 10+(position-1)*30
    base = datetime.fromisoformat(f.stamp(base_seconds).replace("Z", "+00:00"))
    delta = base-datetime.fromisoformat(r["start_utc"])
    def rebase(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.endswith("_utc") and item:
                    value[key] = (datetime.fromisoformat(item.replace("Z", "+00:00"))+delta).isoformat()
                else:
                    rebase(item)
        elif isinstance(value, list):
            for item in value:
                rebase(item)
    rebase(r)
    mono_delta = base_seconds-r["monotonic_start"]
    r["monotonic_start"] += mono_delta; r["monotonic_end"] += mono_delta
    r["cleanup"] = f.cleanup(root)
    f.write(root, name, r)
    f.edit(root, "execution/index.json", lambda d: d["stop"].update(reason=r["status"]))
    refresh_index(root)
    temporary_ledger.unlink()
    return r, calls


class RestartAuditTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def prepare(self):
        f.frozen(self.root); f.collected(self.root)

    def rejects(self, pattern):
        with self.assertRaisesRegex(AuditError, pattern):
            audit(self.root, "collected")

    def test_thinking_absence_on_protocol_and_every_configuration_and_step(self):
        self.prepare()
        self.assertTrue(audit(self.root, "collected")["ok"])
        index = f.read(self.root, "execution/index.json")
        for name in index["cases"][:6]:
            r = f.read(self.root, name)
            body_path = r["requests"][-1]["request_path"]
            for value in (None, {"type": "enabled"}):
                f.edit(self.root, body_path, lambda d: d.update(thinking=value))
                self.rejects("actual model/reasoning_effort/thinking")
                f.edit(self.root, body_path, lambda d: d.pop("thinking"))
        f.edit(self.root, "protocol.json", lambda d: d.update(thinking=None))
        f.reseal(self.root)
        with self.assertRaisesRegex(AuditError, "effort/thinking contract"):
            audit(self.root, "frozen")

    def test_late_native_block_keeps_actual_prefix_and_every_post(self):
        for status, payload in (("compatibility_blocked", {"error": {"message": "Unknown field: thinking"}}),
                                ("access_blocked", {"error": {"message": "Entitlement unavailable"}})):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); f.frozen(root); f.collected(root)
                save_failure(root, 39, 2, status, payload)
                self.assertEqual(audit(root, "collected")["study_status"], status)
                report = analysis.analyze(root)
                self.assertEqual(report["attempted_cases"], 39)
                self.assertEqual(report["client_post_starts"], 78)
                self.assertEqual(sum(report["status_counts"].values()), 72)
                self.assertIsNone(report["winner"]); self.assertIsNone(report["qualified_latency"])
                self.assertFalse(report["completed_comparison"])
                self.assertEqual(analysis.tables(report), {})
                f.write(root, "analysis/block-report.json", report); f.final_review(root)
                self.assertFalse(audit(root)["completed_comparison"])
                report["client_post_starts"] = 39
                f.write(root, "analysis/block-report.json", report); f.final_review(root)
                with self.assertRaisesRegex(AuditError, "fabricated native-block comparison"):
                    audit(root)

    def test_specific_native_types_and_nested_string_not_generic_400(self):
        positives = [{"error": {"type": "unknown_field", "message": "thinking"}},
                     {"error": {"code": "unsupported_parameter", "message": "reasoning_effort"}},
                     {"error": {"message": json.dumps({"error": {"type": "unknown_field", "message": "thinking"}})}},
                     {"error": {"message": "Parameter 'thinking' is not supported"}},
                     {"error": {"message": "Unknown request parameter: thinking"}},
                     {"error": {"message": "reasoning_effort is not supported"}},
                     {"error": {"message": "Unrecognised request parameter: reasoning_effort"}},
                     json.dumps("unknown field thinking")]
        for payload in positives:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); f.frozen(root); f.collected(root)
                save_failure(root, 4, 1, "compatibility_blocked", payload)
                self.assertEqual(audit(root, "collected")["study_status"], "compatibility_blocked")
        self.prepare()
        save_failure(self.root, 1, 1, "compatibility_blocked", {"error": {"type": "invalid_request_error", "message": "Malformed request"}})
        self.rejects("missing native denial evidence")

    def test_generic_first_failure_is_incomplete_later_error_continues(self):
        for position, halt in ((1, True), (4, False)):
            with self.subTest(position=position), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); f.frozen(root); f.collected(root)
                save_failure(root, position, 1, "incomplete", {"error": {"message": "Malformed request", "type": "invalid_request_error"}}, halt=halt)
                result = audit(root, "collected")
                self.assertEqual(result["study_status"], "incomplete" if halt else "completed")
                if halt:
                    with self.assertRaisesRegex(AuditError, "final audit incomplete"):
                        audit(root)
                else:
                    gate = f.read(root, "execution/index.json")["compatibility_gates"]["glm-low"]
                    self.assertEqual(gate, {"case_id": "C004", "status": "incomplete"})

    def test_any_later_block_cannot_be_hidden_as_ordinary_error(self):
        self.prepare()
        save_failure(self.root, 10, 2, "incomplete", {"error": {"message": "Unsupported parameter thinking"}}, halt=False)
        self.rejects("native block classification/status mismatch")

    def test_request_and_case_after_block_are_rejected(self):
        self.prepare()
        first = f.read(self.root, f.read(self.root, "execution/index.json")["cases"][0])
        f.write(self.root, first["requests"][0]["response_path"], {"error": {"message": "Unknown field thinking"}})
        first["requests"][0].update(http_status=400, error="native rejection", usage=None)
        first.update(status="compatibility_error", operational_complete=False)
        f.write(self.root, "execution/cases/C001/record.json", first)
        self.rejects("request after native parameter/access block")
        f.collected(self.root)
        save_failure(self.root, 7, 2, "compatibility_blocked", {"error": {"message": "Unknown field thinking"}}, halt=False)
        f.edit(self.root, "execution/index.json", lambda d: d.update(study_status="compatibility_blocked"))
        self.rejects("candidate attempt after native parameter/access block")

    def test_block_counts_stop_suffix_gates_and_hidden_retries(self):
        self.prepare()
        save_failure(self.root, 3, 2, "compatibility_blocked", {"error": {"message": "Unsupported parameter thinking"}})
        original = f.read(self.root, "execution/index.json")
        for mutate, pattern in ((lambda d: d.update(attempted_cases=2), "count mismatch"),
                                (lambda d: d["stop"].update(schedule_index=2), "stop does not match"),
                                (lambda d: d["compatibility_gates"]["deepseek-max"].update(status="passed"), "fabricated compatibility gate")):
            with self.subTest(pattern=pattern):
                changed = copy.deepcopy(original); mutate(changed)
                f.write(self.root, "execution/index.json", changed)
                self.rejects(pattern)
        f.write(self.root, "execution/index.json", original)
        skipped = original["cases"][3]
        f.edit(self.root, skipped, lambda d: d.update(status="not_run_access_gate"))
        self.rejects("invalid native block prefix/stop/suffix")
        f.edit(self.root, skipped, lambda d: d.update(status="not_run_compatibility_block"))
        ledger = (self.root/"execution/post-starts.jsonl").read_text()
        f.write(self.root, "execution/post-starts.jsonl", ledger+ledger.splitlines()[-1]+"\n")
        self.rejects("hidden extra")

    def test_gate_pass_requires_operational_case_and_skips_need_reason(self):
        self.prepare()
        save_failure(self.root, 2, 1, "incomplete", {"error": {"message": "Internal server error"}}, halt=False)
        f.edit(self.root, "execution/index.json", lambda d: d["compatibility_gates"]["deepseek-high"].update(status="passed"))
        self.rejects("fabricated compatibility gate")
        shutil.rmtree(self.root/"execution")
        f.collected(self.root, "incomplete")
        f.edit(self.root, "execution/index.json", lambda d: d.update(stop=None))
        self.rejects("fabricated ordinary stop/skips")

    def test_linked_exact_public_document_is_allowed_with_key_proof(self):
        public_fixture(self.root)
        self.assertTrue(audit(self.root, "collected")["ok"])
        f.edit(self.root, "execution/parent-provisioning.json", lambda d: d.update(secret_matches=1))
        self.rejects("exact selected-Go-key hygiene proof")

    def test_unknown_field_bearer_and_sk_cannot_ride_on_public_match(self):
        additions = [' "authorization": "unknown"', ' Bearer mock_secret_12345678', ' sk-mock_secret_12345678']
        for addition in additions:
            with self.subTest(addition=addition), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                public_fixture(root, 'Official documented claim. {"Authorization": "public"}'+addition)
                with self.assertRaisesRegex(AuditError, "persisted credential material"):
                    audit(root, "collected")

    def test_unlinked_copy_request_header_and_unknown_json_never_exempt(self):
        public_fixture(self.root)
        text = (self.root/"dataset/archive/T1-1.txt").read_text()
        for name, content in (("execution/unlinked.txt", text),
                              ("execution/headers.json", '{"Authorization": "example"}'),
                              ("execution/unknown.json", '{"Authorization": "public"}')):
            with self.subTest(name=name):
                f.write(self.root, name, content)
                self.rejects("persisted credential material")
                (self.root/name).unlink()

    def test_modified_text_and_frozen_provenance_cannot_get_exception(self):
        public_fixture(self.root)
        name = f.read(self.root, "execution/index.json")["cases"][0]
        r = f.read(self.root, name); fetch = r["fetches"][0]
        f.write(self.root, fetch["text_path"], 'changed {"Authorization": "public"}')
        self.rejects("changed hash")
        public_fixture(self.root)
        f.edit(self.root, "dataset/sources.json", lambda d: d[0].update(status=500))
        self.rejects("changed hash")

    def test_public_exception_does_not_exempt_truncated_or_noncanonical_fetch(self):
        public_fixture(self.root)
        name = f.read(self.root, "execution/index.json")["cases"][0]
        r = f.read(self.root, name); fetch = r["fetches"][0]
        full = (self.root/fetch["text_path"]).read_text()
        preview = full[:-1]
        f.write(self.root, fetch["model_text_path"], preview)
        fetch.update(model_text_sha256=digest(self.root/fetch["model_text_path"]), truncated=True)
        history = f.read(self.root, r["history_path"])
        tool = next(m for m in history if m.get("tool_call_id") == "tool1")
        content = json.loads(tool["content"]); content.update(text=preview, truncated=True)
        tool["content"] = json.dumps(content)
        f.write(self.root, r["history_path"], history)
        f.edit(self.root, r["requests"][1]["request_path"], lambda d: d.update(messages=history[:-1]))
        f.write(self.root, name, r)
        self.rejects("persisted credential material")
        public_fixture(self.root)
        # The same bytes from an unknown URL cannot borrow the public archive's identity.
        sources = f.read(self.root, "dataset/sources.json")
        sources[0]["canonical_url"] = "https://docs.example.test/T1/public-copy"
        f.write(self.root, "dataset/sources.json", sources); f.reseal(self.root)
        self.rejects("persisted credential material")

    def test_native_markdown_public_document_and_unfrozen_copy(self):
        public_fixture(self.root)
        sources = f.read(self.root, "dataset/sources.json")
        sources[0].update(url=PUBLIC_CANONICAL+"index.md", final_url=PUBLIC_CANONICAL+"index.md")
        f.write(self.root, "dataset/sources.json", sources)
        f.edit(self.root, "dataset/tasks.json", lambda d: d[0].update(
            starting_urls=[PUBLIC_CANONICAL+"index.md"],
            required_source_urls=[PUBLIC_CANONICAL+"index.md", d[0]["required_source_urls"][1]]))
        f.reseal(self.root); f.collected(self.root)
        self.assertTrue(audit(self.root, "collected")["ok"])
        # Public exception never bypasses the frozen source hashes.
        (self.root/"dataset/archive/T1-1.txt").write_text('modified {"Authorization": "field"}')
        self.rejects("changed hash")

    def test_complete_quality_and_statistics_still_need_all_grade_evidence(self):
        f.complete(self.root)
        result = analysis.analyze(self.root)
        self.assertEqual(result["bootstrap"]["seed"], 20261007021015)
        self.assertEqual(result["bootstrap"]["draws"], 10000)
        self.assertEqual(result["configurations"]["deepseek-low"]["qualified"], 12)
        self.assertEqual(result["configurations"]["deepseek-low"]["qualified_latency"]["median_s"], 20)
        self.assertIsNone(result["recommendation"]["winner"])
        next(self.root.glob("grades/shard-a/*.json")).unlink()
        with self.assertRaisesRegex(AuditError, "missing grades stage artifact"):
            analysis.analyze(self.root)

    def test_R2_actual_non_json_native_blocks_early_late_case_and_step(self):
        for status, http_status, raw in (("compatibility_blocked", 400, b"unknown field thinking"),
                                         ("access_blocked", 403, b"Forbidden")):
            for position, step in ((1, 1), (7, 1), (39, 2)):
                with self.subTest(status=status, position=position, step=step), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    r, calls = native_failure_fixture(root, position, step, status, raw, http_status)
                    self.assertEqual(len(calls), step)
                    response_path = root/r["requests"][-1]["response_path"]
                    self.assertEqual(response_path.read_bytes(), raw)
                    self.assertEqual(audit(root, "collected")["study_status"], status)
                    report = analysis.analyze(root)
                    self.assertEqual(report["attempted_cases"], position)
                    self.assertEqual(report["client_post_starts"], 2*(position-1)+step)
                    self.assertIsNone(r["usage"]["completion_tokens"])
                    self.assertIsNone(r["requests"][-1]["native_usage"])
                    self.assertFalse(r["usage"]["complete"])
                    f.write(root, "analysis/block-report.json", report); f.final_review(root)
                    self.assertFalse(audit(root)["completed_comparison"])
                    self.assertEqual(response_path.read_bytes(), raw)

    def test_R2_non_json_ordinary_error_is_not_a_comparison_or_native_block(self):
        r, _ = native_failure_fixture(self.root, 1, 1, "incomplete", b"Malformed request", 400)
        self.assertEqual(r["status"], "provider_error")
        self.assertEqual(audit(self.root, "collected")["study_status"], "incomplete")
        with self.assertRaisesRegex(AuditError, "final audit incomplete"):
            audit(self.root)
        with self.assertRaisesRegex(AuditError, "incomplete study"):
            analysis.analyze(self.root)

    def test_R2_successful_inference_still_requires_json_and_unknown_usage(self):
        self.prepare()
        name = f.read(self.root, "execution/index.json")["cases"][0]
        r = f.read(self.root, name)
        (self.root/r["requests"][-1]["response_path"]).write_bytes(b"not JSON")
        self.rejects("invalid JSON.*native response")
        shutil.rmtree(self.root/"execution")
        r, _ = native_failure_fixture(self.root, 3, 1, "compatibility_blocked", b"unknown field thinking", 400)
        r["usage"]["completion_tokens"] = 0
        f.write(self.root, "execution/cases/C003/record.json", r)
        self.rejects("unknown must stay null")

    def test_R3_receipt_required_collected_and_final_with_and_without_public_docs(self):
        for public in (False, True):
            with self.subTest(public=public), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                if public:
                    public_fixture(root)
                    save_failure(root, 3, 1, "compatibility_blocked", {"error": {"message": "unknown field thinking"}})
                    f.write(root, "analysis/block-report.json", analysis.analyze(root))
                else:
                    f.complete(root)
                    f.write(root, "analysis/results.json", analysis.analyze(root))
                f.final_review(root)
                self.assertTrue(audit(root)["ok"])
                receipt = root/"execution/parent-provisioning.json"
                original = receipt.read_bytes()
                receipt.unlink()
                for stage in ("collected", None):
                    with self.subTest(stage=stage), self.assertRaisesRegex(AuditError, "parent-provisioning"):
                        audit(root, stage)
                receipt.write_bytes(original)
                f.edit(root, "execution/parent-provisioning.json", lambda d: d.update(secret_matches=1))
                for stage in ("collected", None):
                    with self.subTest(stage=stage), self.assertRaisesRegex(AuditError, "selected-Go-key hygiene proof"):
                        audit(root, stage)
                receipt.write_bytes(original)
                f.edit(root, "execution/parent-provisioning.json", lambda d: d.update(
                    credential_source="Different provider, no selected Go credential"))
                f.final_review(root)
                for stage in ("collected", None):
                    with self.subTest(stage=stage, different_provider=True), self.assertRaisesRegex(
                            AuditError, "selected-Go-key hygiene proof"):
                        audit(root, stage)
                receipt.write_bytes(original)
                f.final_review(root)
                f.edit(root, "final-review/index.json", lambda d: d["files"].pop("execution/parent-provisioning.json"))
                with self.assertRaisesRegex(AuditError, "selected-Go-key proof not sealed"):
                    audit(root)
                f.final_review(root)
                f.edit(root, "execution/parent-provisioning.json", lambda d: d.update(scanned_file_count=101))
                self.assertTrue(audit(root, "collected")["ok"])
                with self.assertRaisesRegex(AuditError, "changed hash: execution/parent-provisioning"):
                    audit(root)

    def test_R3_receipt_schema_rejects_false_or_missing_evidence(self):
        self.prepare()
        name = "execution/parent-provisioning.json"
        original = f.read(self.root, name)
        invalid = {"credential_source": "", "credential_store_copied": True,
                   "worker_credential_store_access": True, "ephemeral_environment_only": False,
                   "secret_matches": 1, "caller_retries": 1, "scanned_file_count": 0,
                   "runner_returncode": None, "started_utc": f.stamp(-1), "finished_utc": f.stamp(-2)}
        for field, value in invalid.items():
            with self.subTest(field=field):
                changed = copy.deepcopy(original); changed[field] = value
                f.write(self.root, name, changed)
                self.rejects("provisioning|selected-Go-key hygiene proof")
        f.write(self.root, name, original)


if __name__ == "__main__":
    unittest.main()
