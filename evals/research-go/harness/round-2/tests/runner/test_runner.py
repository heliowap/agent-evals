"""Offline public-interface behavior tests. No candidate, credentials or network."""
import collections
import copy
import json
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, Mock

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(A))
import runner
import webfetch

KEY = "offline-test-secret-never-real"
URL = "https://docs.github.com/en/webhooks"
PROTOCOL = runner.read_json(A / "protocol.json")
TOOLS = runner.read_json(A / "tools.json")


def completion(content="Decision.", calls=None, reasoning="private reasoning", usage=None, finish=None):
    assistant = {"role": "assistant", "content": content, "reasoning_content": reasoning}
    if calls:
        assistant["tool_calls"] = calls
    return {"choices": [{"message": assistant, "finish_reason": finish or ("tool_calls" if calls else "stop")}], "usage": usage}


def tool(url=URL, name="webfetch", id="call-1"):
    return {"id": id, "type": "function", "function": {"name": name, "arguments": json.dumps({"url": url})}}


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="offline-runner-", dir="/private/tmp/opencode")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Unexpected live network always fails the test. Subprocess tests run -I
        # with a fixed sleep-only program, never the actual model worker.
        guard = patch.object(socket, "create_connection", side_effect=AssertionError("live network forbidden"))
        guard.start()
        self.addCleanup(guard.stop)
        dns = patch.object(socket, "getaddrinfo", side_effect=AssertionError("live DNS forbidden"))
        dns.start()
        self.addCleanup(dns.stop)

    def spec(self, configuration=None, directory=None):
        case = copy.deepcopy(runner.make_schedule()["cases"][0])
        case["task_id"] = "T1"
        if configuration:
            case.update(model=configuration["model"], effort=configuration["effort"], configuration_id=configuration["id"])
        return {"case": case, "task": {"id": "T1", "prompt": "Public task only.", "required_source_urls": [URL]},
                "directory": str(directory or (self.root / "case")), "sources": [],
                "ledger_path": str(self.root / "post-starts.jsonl"),
                "protocol": copy.deepcopy(PROTOCOL), "tools": copy.deepcopy(TOOLS), "system": "Fixed public system."}

    def responses(self, values, bodies=None):
        queue = iter(values)
        def transport(body, key, session, deadline, mark_started):
            mark_started()
            if bodies is not None:
                bodies.append((copy.deepcopy(body), session))
            value = next(queue)
            if isinstance(value, Exception):
                raise value
            status, response = value if isinstance(value, tuple) else (200, value)
            return status, json.dumps(response).encode()
        return transport

    def frozen_fixture(self, seal_now=True):
        # All fixtures live within the runner-owned test directory and are deleted.
        for name in ("runner.py", "webfetch.py", "dataset.py", "verify.py", "analysis.py", "scope.json", "plan.md", "contracts.md", "restart.json"):
            (self.root / name).write_text("offline fixture\n")
        runner.save_json(self.root / "schedule.json", runner.make_schedule())
        runner.save_json(self.root / "protocol.json", PROTOCOL)
        runner.save_json(self.root / "tools.json", TOOLS)
        (self.root / "system.txt").write_text("fixed")
        tasks = [{"id": "T" + str(i), "prompt": "Official public engineering task " + str(i), "required_source_urls": [],
                  "allowed_url_patterns": []} for i in range(1, 7)]
        runner.save_json(self.root / "dataset/tasks.json", tasks)
        runner.save_json(self.root / "dataset/gold.json", {"version": 1, "tasks": {t["id"]: {"checks": [], "uncertainty": {}, "source_rules": {}, "critical_errors": []} for t in tasks}})
        runner.save_json(self.root / "dataset/sources.json", [])
        (self.root / "api-evidence").mkdir()
        (self.root / "api-evidence/contract.txt").write_text("primary fixture")
        runner.save_json(self.root / "preflight/workflow.json", {
            "owner": "parent", "candidate_post_starts": 0, "credential_provisioning": "parent_owned",
            "external_secret_paths_imported": False, "runtime_root": str(runner.RUNTIME),
            "worker_bounds_verified": True, "protocol_reviewed": True, "api_evidence_reviewed": True,
            "created_utc": runner.utc(), "synthetic_fixture": True})
        if seal_now:
            runner.seal(self.root)

    def launch_record(self, status="completed"):
        def launch(case, directory):
            record = runner.new_record(case, status)
            record.update(operational_complete=status == "completed", cleanup={"owned_group_absent": True})
            if status == "source_drift":
                record["source_drift"] = [{"kind": "required_main_content"}]
            return record
        return launch


class RunnerBehavior(OfflineCase):
    def test_six_native_requests_and_max_serialization(self):
        self.assertNotIn("thinking", PROTOCOL)
        for config in runner.CONFIGURATIONS:
            with self.subTest(config=config["id"]):
                bodies = []
                spec = self.spec(config, self.root / config["id"])
                rows = [completion(None, [tool(id="call-" + str(i))]) for i in range(7)] + [completion()]
                fetcher = Mock(return_value={"status": "http_error", "http_status": 404, "error": "HTTP 404"})
                observed = runner.run_case(spec, KEY, self.responses(rows, bodies), fetcher)
                body, session = bodies[0]
                self.assertEqual(config["effort"], json.loads(json.dumps(body))["reasoning_effort"])
                self.assertEqual(config["model"], body["model"])
                self.assertEqual(16384, body["max_tokens"])
                self.assertEqual(["webfetch"], [t["function"]["name"] for t in body["tools"]])
                self.assertEqual(2, len(body["messages"]))
                self.assertNotIn("temperature", body)
                self.assertNotIn("top_p", body)
                self.assertEqual("completed", observed["status"])
                self.assertEqual(1, observed["requests"][0]["client_post_starts"])
                self.assertEqual(session, observed["session_id"])
                self.assertEqual(8, len(bodies))
                self.assertEqual(7, fetcher.call_count)
                for step, (wire, step_session) in enumerate(bodies, 1):
                    self.assertEqual(config["effort"], wire["reasoning_effort"])
                    self.assertEqual(config["model"], wire["model"])
                    self.assertEqual(16384, wire["max_tokens"])
                    self.assertNotIn("thinking", wire)
                    self.assertEqual(step < 8, "tools" in wire)
                    self.assertNotIn("tool_choice", wire)
                    self.assertEqual(session, step_session)
                    saved = runner.read_json(Path(spec["directory"]) / ("requests/" + str(step) + "-body.json"))
                    self.assertEqual(wire, saved)

    def test_native_reasoning_and_tool_turns_preserved(self):
        first = completion(None, [tool()], "full native private analysis\nsecond line")
        bodies = []
        def fetched(url, task_id, deadline):
            return webfetch.fetch_document(url, task_id, deadline, lambda u, timeout: (200, {"content-type": "text/plain"}, b"Whole document."))
        observed = runner.run_case(self.spec(), KEY, self.responses([first, completion()], bodies), fetched)
        self.assertEqual(first["choices"][0]["message"], bodies[1][0]["messages"][2])
        self.assertEqual("tool", bodies[1][0]["messages"][3]["role"])
        self.assertEqual("call-1", bodies[1][0]["messages"][3]["tool_call_id"])
        self.assertEqual("Whole document.\n", json.loads(bodies[1][0]["messages"][3]["content"])["text"])
        self.assertEqual(bodies[0][1], bodies[1][1])
        self.assertEqual(2, observed["inference_steps"])
        self.assertEqual(1, len(observed["fetches"]))

    def test_intent_saved_before_http_and_once_only_worker(self):
        spec = self.spec()
        def transport(body, key, session, deadline, mark_started):
            record = runner.read_json(Path(spec["directory"]) / "record.json")
            self.assertEqual(1, record["inference_steps"])
            self.assertTrue(record["requests"][0]["intent_logged"])
            self.assertEqual(0, record["requests"][0]["client_post_starts"])
            self.assertTrue((Path(spec["directory"]) / "requests/1-body.json").exists())
            mark_started()
            rows = [json.loads(line) for line in Path(spec["ledger_path"]).read_text().splitlines()]
            self.assertEqual(1, len(rows))
            self.assertEqual(spec["case"]["id"], rows[0]["case_id"])
            self.assertEqual(record["requests"][0]["request_path"], rows[0]["request_path"])
            persisted = runner.read_json(Path(spec["directory"]) / "record.json")
            self.assertEqual(rows[0]["started_utc"], persisted["requests"][0]["started_utc"])
            self.assertNotIn(KEY, Path(spec["ledger_path"]).read_text())
            raise ConnectionResetError("ambiguous transport failure")
        observed = runner.run_case(spec, KEY, transport)
        self.assertEqual("harness_error", observed["status"])
        self.assertEqual(1, observed["inference_steps"])
        replay = Mock(side_effect=AssertionError("must not replay"))
        with self.assertRaises(FileExistsError):
            runner.run_case(spec, KEY, replay)
        replay.assert_not_called()

    def test_step_eight_has_no_tools_and_never_follows_terminal_calls(self):
        bodies, fetches = [], []
        def fetched(url, task_id, deadline):
            fetches.append(url)
            return {"status": "http_error", "http_status": 404, "error": "HTTP 404"}
        rows = [completion(None, [tool(id="call-" + str(i))]) for i in range(8)]
        observed = runner.run_case(self.spec(), KEY, self.responses(rows, bodies), fetched)
        self.assertEqual(8, observed["inference_steps"])
        self.assertEqual(7, len(fetches))
        self.assertTrue(all("tools" in body for body, session in bodies[:7]))
        self.assertNotIn("tools", bodies[7][0])
        self.assertNotIn("tool_choice", bodies[7][0])
        self.assertEqual("step_limit", observed["status"])
        self.assertFalse(observed["operational_complete"])

    def test_secret_scrub_and_no_auth_redirect_follow(self):
        response = Mock(status=302)
        response.read.return_value = json.dumps({"error": {"message": KEY}}).encode()
        conn = Mock()
        conn.getresponse.return_value = response
        starts = []
        with patch.object(runner.http.client, "HTTPSConnection", return_value=conn):
            status, raw = runner.post_go({"model": "deepseek-v4.1-flash"}, KEY, "opaque-session", time.monotonic() + 10, lambda: starts.append(1))
        self.assertEqual(302, status)
        self.assertEqual(1, conn.request.call_count)
        headers = conn.request.call_args.kwargs["headers"]
        self.assertEqual("Bearer " + KEY, headers["Authorization"])
        self.assertEqual("opaque-session", headers["x-opencode-session"])
        self.assertTrue(headers["User-Agent"].startswith("researcher-eval/"))
        observed = runner.run_case(self.spec(), KEY, self.responses([(400, {"error": {"message": KEY}})]))
        for path in Path(self.spec()["directory"]).rglob("*"):
            if path.is_file():
                self.assertNotIn(KEY.encode(), path.read_bytes())
        self.assertIn("REDACTED_AUTH", json.dumps(observed))

    def test_tool_rejection_and_real_preview_retained(self):
        fetcher = Mock(side_effect=AssertionError("unknown tool cannot fetch"))
        bodies = []
        observed = runner.run_case(self.spec(), KEY, self.responses([completion(None, [tool(name="shell")]), completion()], bodies), fetcher)
        fetcher.assert_not_called()
        self.assertEqual("rejected", observed["fetches"][0]["status"])
        self.assertEqual("rejected", json.loads(bodies[1][0]["messages"][-1]["content"])["status"])

    def test_fetch_cap_32_no_extra_network(self):
        calls = [tool(id=str(i)) for i in range(32)]
        fetched = Mock(return_value={"status": "http_error", "error": "HTTP 404", "http_status": 404})
        bodies = []
        observed = runner.run_case(self.spec(), KEY, self.responses([completion(None, calls), completion(None, [tool()]), completion()], bodies), fetched)
        self.assertEqual(32, fetched.call_count)
        self.assertEqual(32, len(observed["fetches"]))
        self.assertEqual("rejected", json.loads(bodies[2][0]["messages"][-1]["content"])["status"])

    def test_usage_unknown_and_inclusive_subsets(self):
        native = {"prompt_tokens": 100, "completion_tokens": 80,
                  "prompt_tokens_details": {"cached_tokens": 30, "cache_write_tokens": 10},
                  "prompt_cache_hit_tokens": 30, "completion_tokens_details": {"reasoning_tokens": 50}, "vendor": "retained"}
        observed = runner.run_case(self.spec(), KEY, self.responses([completion(usage=native)]))
        usage = observed["usage"]
        self.assertEqual(80, usage["completion_tokens"])
        self.assertEqual(30, usage["non_reasoning_output_tokens"])
        self.assertEqual(30, usage["cache_read_tokens"])
        self.assertEqual(60, usage["uncached_input_tokens"])
        self.assertEqual([native], usage["raw_steps"])
        self.assertEqual(usage, observed["requests"][0]["usage"])
        self.assertEqual(native, observed["requests"][0]["native_usage"])
        self.assertTrue(usage["complete"])
        self.assertIsNone(usage["reported_cost"])
        unknown = runner.run_case(self.spec(directory=self.root / "unknown"), KEY, self.responses([completion()]))["usage"]
        self.assertFalse(unknown["complete"])
        self.assertIsNone(unknown["prompt_tokens"])
        mixed = runner.usage_summary([native, None])
        self.assertIsNone(mixed["completion_tokens"])
        alias = runner.usage_summary([{ "prompt_tokens": 100, "completion_tokens": 10, "prompt_cache_hit_tokens": 30, "prompt_cache_miss_tokens": 70}])
        self.assertEqual(30, alias["cache_read_tokens"])
        self.assertEqual(70, alias["uncached_input_tokens"])
        self.assertIsNone(alias["reasoning_tokens"])

    def test_counted_gate_halts_71_and_study_cannot_replay(self):
        self.frozen_fixture()
        calls = []
        def launch(case, directory):
            calls.append(case)
            spec = self.spec(directory=directory)
            spec["case"] = case
            record = runner.run_case(spec, KEY, self.responses([(400, {"error": {"message": "This Go model requires Global regions. Select Global in Privacy settings."}})]))
            record["cleanup"] = {"owned_group_absent": True}
            return record
        index = runner.run_study(self.root, launch)
        self.assertEqual("access_blocked", index["study_status"])
        self.assertEqual(1, index["attempted_cases"])
        self.assertEqual(72, index["terminal_cases"])
        self.assertEqual(1, index["attempted_terminal_cases"])
        self.assertEqual(72, index["terminal_records"])
        self.assertEqual("deepseek-low", calls[0]["configuration_id"])
        self.assertEqual(1, len(calls))
        for name in index["cases"][1:]:
            record = runner.read_json(self.root / name)
            self.assertEqual("not_run_access_gate", record["status"])
            self.assertIsNone(record["wall_s"])
            self.assertEqual([], record["requests"])
        with self.assertRaises(FileExistsError):
            runner.run_study(self.root, launch)

    def test_other_first_failure_stops_incomplete(self):
        self.frozen_fixture()
        launch = Mock(side_effect=self.launch_record("provider_error"))
        index = runner.run_study(self.root, launch)
        self.assertEqual("incomplete", index["study_status"])
        self.assertEqual(1, launch.call_count)
        self.assertEqual("not_run_first_failure", runner.read_json(self.root / index["cases"][1])["status"])
        self.assertEqual("incomplete", index["gate_status"])
        self.assertEqual("provider_error", index["stop"]["reason"])

    def test_parameter_errors_require_native_explicit_http_diagnostic(self):
        rows = [
            (400, {"error": {"message": "unknown field 'thinking'"}}, "compatibility_error"),
            (422, {"error": {"code": "unsupported_parameter", "param": "reasoning_effort"}}, "compatibility_error"),
            (400, {"error": {"message": "Parameter reasoning_effort is not supported"}}, "compatibility_error"),
            (400, {"error": {"message": "reasoning_effort is not supported"}}, "compatibility_error"),
            (400, {"error": {"message": "Unrecognised request parameter: reasoning_effort"}}, "compatibility_error"),
            (400, {"error": {"message": "thinking is not supported"}}, "compatibility_error"),
            (400, {"error": {"message": "invalid request parameter: max_tokens"}}, "compatibility_error"),
            (400, {"error": {"message": "Malformed JSON request"}}, "provider_error"),
            (400, {"error": {"code": "invalid_request_error", "message": "Context length exceeded"}}, "provider_error"),
            (400, {"error": {"message": "max_tokens must be an integer"}}, "provider_error"),
            (400, {"error": {"code": "invalid_request_error", "message": "reasoning_effort must be a string"}}, "provider_error"),
            (200, completion("The documentation describes an unsupported parameter."), "completed"),
            (200, completion("reasoning_effort is not supported"), "completed"),
            (200, {"error": {"message": "unknown field 'thinking'"}}, "provider_error"),
            (401, {"error": {"message": "unknown field 'thinking'"}}, "access_gate_error"),
            (403, {"error": {"message": "unsupported parameter"}}, "access_gate_error"),
            (400, {"error": {"message": "entitlement denied; unsupported parameter"}}, "access_gate_error"),
        ]
        for i, (status, native, expected) in enumerate(rows):
            with self.subTest(status=status, native=native):
                spec = self.spec(directory=self.root / str(i))
                transport = Mock(side_effect=self.responses([(status, native)]))
                record = runner.run_case(spec, KEY, transport)
                self.assertEqual(expected, record["status"])
                self.assertEqual(1, transport.call_count)
                self.assertEqual(1, record["inference_steps"])

    def test_non_json_native_parameter_and_access_errors_keep_response(self):
        for status, message, expected in [(400, b"unknown field thinking", "compatibility_error"),
                                          (403, b"Forbidden", "access_gate_error"),
                                          (400, b"Bad JSON", "provider_error")]:
            with self.subTest(status=status, message=message):
                spec = self.spec(directory=self.root / expected)
                def transport(body, key, session, deadline, mark_started):
                    mark_started()
                    return status, message
                record = runner.run_case(spec, KEY, transport)
                self.assertEqual(expected, record["status"])
                self.assertEqual(message, (Path(spec["directory"]) / "requests/1-response.json").read_bytes())

    def test_first_six_are_once_counted_gates_ordinary_error_not_replaced(self):
        self.frozen_fixture()
        schedule = runner.read_json(self.root / "schedule.json")
        first = {c["configuration_id"]: c["id"] for c in schedule["cases"][:6]}
        self.assertEqual(6, len(first))
        calls = []
        def launch(case, directory):
            current = runner.read_json(self.root / "execution/index.json")
            if not calls:
                self.assertEqual(first, {k: v["case_id"] for k, v in current["compatibility_gates"].items()})
                self.assertEqual({"pending"}, {v["status"] for v in current["compatibility_gates"].values()})
            calls.append(case["id"])
            return self.launch_record("provider_error" if case["index"] == 2 else "completed")(case, directory)
        index = runner.run_study(self.root, launch)
        self.assertEqual([c["id"] for c in schedule["cases"]], calls)
        self.assertEqual(72, len(set(calls)))
        self.assertEqual(72, index["planned_cases"])
        self.assertEqual(72, index["attempted_cases"])
        self.assertEqual(72, index["attempted_terminal_cases"])
        self.assertEqual("completed", index["study_status"])
        self.assertIsNone(index["stop"])
        failed_config = schedule["cases"][1]["configuration_id"]
        for config, gate in index["compatibility_gates"].items():
            self.assertEqual(first[config], gate["case_id"])
            self.assertEqual("incomplete" if config == failed_config else "passed", gate["status"])
        self.assertEqual("passed", index["gate_status"])
        with self.assertRaises(FileExistsError):
            runner.run_study(self.root, Mock(side_effect=AssertionError("no reruns")))

    def test_gate_requires_operational_completion_not_status_alone(self):
        self.frozen_fixture()
        def launch(case, directory):
            record = self.launch_record()(case, directory)
            record["operational_complete"] = False
            return record
        index = runner.run_study(self.root, launch)
        self.assertEqual(1, index["attempted_cases"])
        self.assertEqual("incomplete", index["gate_status"])
        self.assertEqual("incomplete", index["study_status"])

    def test_native_rejection_any_case_any_step_stops_without_replay(self):
        scenarios = [(1, 1, 400, "unknown field thinking", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (3, 8, 422, "unsupported parameter reasoning_effort", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (7, 1, 400, "reasoning_effort is not supported", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (7, 7, 400, "reasoning_effort is not supported", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (7, 1, 400, "Unrecognised request parameter: reasoning_effort", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (7, 7, 400, "Unrecognised request parameter: reasoning_effort", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (37, 3, 400, "unknown field thinking", "compatibility_blocked", "compatibility_error", "not_run_compatibility_block"),
                     (37, 3, 403, "unsupported parameter reasoning_effort", "access_blocked", "access_gate_error", "not_run_access_gate")]
        original_root = self.root
        for scenario, (failure_case, failure_step, http_status, message, study_status, case_status, suffix) in enumerate(scenarios):
            with self.subTest(case=failure_case, step=failure_step, study=study_status):
                self.root = original_root / str(scenario)
                self.root.mkdir()
                self.frozen_fixture()
                calls, bodies = [], []
                schedule = runner.read_json(self.root / "schedule.json")
                failed = schedule["cases"][failure_case - 1]
                def launch(case, directory):
                    calls.append(case["id"])
                    spec = self.spec(directory=directory)
                    spec.update(case=case, ledger_path=str(self.root / "execution/post-starts.jsonl"))
                    rows = [completion()]
                    if case["index"] == failure_case:
                        rows = [completion(None, [tool(id=str(i))]) for i in range(failure_step - 1)]
                        rows.append((http_status, {"error": {"message": message}}))
                    fetcher = Mock(return_value={"status": "http_error", "http_status": 404, "error": "HTTP 404"})
                    record = runner.run_case(spec, KEY, self.responses(rows, bodies), fetcher)
                    record["cleanup"] = {"owned_group_absent": True}
                    return record
                index = runner.run_study(self.root, launch)
                self.assertEqual(study_status, index["study_status"])
                self.assertEqual(failure_case, index["attempted_cases"])
                self.assertEqual(failure_case, index["attempted_terminal_cases"])
                self.assertEqual(72, index["planned_cases"])
                self.assertEqual(72, index["terminal_cases"])
                self.assertEqual([c["id"] for c in schedule["cases"][:failure_case]], calls)
                failed_record = runner.read_json(self.root / index["cases"][failure_case - 1])
                self.assertEqual(case_status, failed_record["status"])
                self.assertEqual(failure_step, failed_record["inference_steps"])
                self.assertEqual({"case_id": failed["id"], "schedule_index": failure_case,
                                  "reason": case_status, "http_status": http_status,
                                  "response_path": failed_record["requests"][-1]["response_path"]}, index["stop"])
                self.assertTrue((self.root / index["stop"]["response_path"]).is_file())
                for name in index["cases"][failure_case:]:
                    record = runner.read_json(self.root / name)
                    self.assertEqual(suffix, record["status"])
                    self.assertIsNone(record["wall_s"])
                    self.assertIsNone(record["start_utc"])
                    self.assertEqual([], record["requests"])
                for c in schedule["cases"][:6]:
                    gate = index["compatibility_gates"][c["configuration_id"]]
                    expected = study_status if c["index"] == failure_case else "passed" if c["index"] < failure_case else "not_run"
                    self.assertEqual({"case_id": c["id"], "status": expected}, gate)
                self.assertEqual(study_status if failure_case == 1 else "passed", index["gate_status"])
                self.assertEqual(schedule["cases"][0]["id"], index["gate_case_id"])
                ledger = [json.loads(line) for line in (self.root / "execution/post-starts.jsonl").read_text().splitlines()]
                self.assertEqual(failure_case - 1 + failure_step, len(ledger))
                self.assertEqual(len(ledger), len({(r["case_id"], r["step"]) for r in ledger}))
                self.assertEqual(len(ledger), len(bodies))
                with self.assertRaises(FileExistsError):
                    runner.run_study(self.root, Mock(side_effect=AssertionError("no replay")))
        self.root = original_root

    def test_source_drift_stops_current_and_further_cases(self):
        spec = self.spec()
        original = b"Original substantive page."
        spec["sources"] = [{"url": URL, "canonical_url": URL, "raw_sha256": runner.sha(original), "text_sha256": webfetch.document_hash("Original substantive page.\n")}]
        fetched = lambda url, task, deadline: webfetch.fetch_document(url, task, deadline, lambda u, timeout: (200, {"content-type": "text/plain"}, b"Changed substantive page."))
        transport = Mock(side_effect=self.responses([completion(None, [tool()])]))
        record = runner.run_case(spec, KEY, transport, fetched)
        self.assertEqual("source_drift", record["status"])
        self.assertEqual(1, transport.call_count)
        self.assertFalse(record["fetches"][0]["frozen_source_match"]["text"])
        self.frozen_fixture()
        launch = Mock(side_effect=self.launch_record("source_drift"))
        index = runner.run_study(self.root, launch)
        self.assertEqual(1, launch.call_count)
        self.assertEqual("incomplete", index["study_status"])
        self.assertEqual("not_run_source_drift", runner.read_json(self.root / index["cases"][1])["status"])

    def test_supervisory_timeout_kills_awaits_and_drains(self):
        command = [sys.executable, "-I", "-c", "import time; print('owned-output', flush=True); time.sleep(60)"]
        result = runner.supervise(command, b"", {"PATH": "/usr/bin:/bin"}, self.root, 0.3)
        self.assertTrue(result["timeout"])
        self.assertLess(result["wall_s"], 3)
        self.assertIn(b"owned-output", result["stdout"])
        self.assertTrue(result["cleanup"]["owned_group_absent"])
        self.assertTrue(result["cleanup"]["worker_awaited"])
        self.assertTrue(result["cleanup"]["output_drained"])

    def test_schedule_realized_72_latin_counts(self):
        schedule = runner.read_json(A / "schedule.json")
        self.assertEqual(runner.make_schedule(), schedule)
        self.assertEqual(72, len({c["id"] for c in schedule["cases"]}))
        self.assertEqual("deepseek-low", schedule["cases"][0]["configuration_id"])
        self.assertEqual([1] * 36 + [2] * 36, [c["repetition"] for c in schedule["cases"]])
        counts = collections.Counter((c["configuration_id"], c["position"]) for c in schedule["cases"])
        self.assertEqual({2}, set(counts.values()))
        factorial = collections.Counter((c["task_id"], c["repetition"], c["configuration_id"]) for c in schedule["cases"])
        self.assertEqual(72, len(factorial))
        self.assertEqual({1}, set(factorial.values()))
        for block in schedule["blocks"]:
            self.assertEqual(6, len(block["case_ids"]))

    def test_seal_rejects_modified_inputs_manifest_and_resealing(self):
        self.frozen_fixture()
        runner.check_seal(self.root)
        with self.assertRaises(ValueError):
            runner.seal(self.root)
        (self.root / "system.txt").write_text("changed")
        with self.assertRaisesRegex(ValueError, "modified"):
            runner.check_seal(self.root)
        (self.root / "system.txt").write_text("fixed")
        freeze = runner.read_json(self.root / "freeze.json")
        freeze["created_utc"] = "altered"
        runner.save_json(self.root / "freeze.json", freeze)
        with self.assertRaisesRegex(ValueError, "modified freeze manifest"):
            runner.check_seal(self.root)

    def test_seal_hashes_parent_workflow_and_saved_review_records(self):
        self.frozen_fixture(seal_now=False)
        (self.root / "research").mkdir()
        (self.root / "research/harness.md").write_text("Read-only research provenance fixture.")
        runner.save_json(self.root / "preflight/bootstrap.json", {"synthetic_fixture": True})
        runner.seal(self.root)
        freeze = runner.read_json(self.root / "freeze.json")
        self.assertIn("preflight/workflow.json", freeze["files"])
        self.assertIn("preflight/bootstrap.json", freeze["files"])
        self.assertIn("restart.json", freeze["files"])
        self.assertIn("research/harness.md", freeze["files"])
        (self.root / "preflight/late-review.json").write_text('{"synthetic_fixture":true}')
        with self.assertRaisesRegex(ValueError, "modified"):
            runner.check_seal(self.root)

    def test_cleanup_actual_owned_group_probe_and_supplied_key_scan(self):
        self.frozen_fixture()
        (self.root / "execution").mkdir()
        (self.root / "execution/redacted.txt").write_text("No credentials persisted.")
        outcome = runner.supervise([sys.executable, "-I", "-c", "print('offline child')"], b"", {"PATH": "/usr/bin:/bin"}, self.root, 2)
        proof = runner.save_cleanup(self.root, "execution/cleanup", KEY, [outcome["cleanup"]["owned_pgid"]])
        processes = runner.read_json(self.root / proof["owned_process_check_path"])
        scan = runner.read_json(self.root / proof["credential_scan_path"])
        self.assertEqual(0, proof["owned_processes_remaining"])
        self.assertEqual([], processes["remaining"])
        self.assertEqual([outcome["cleanup"]["owned_pgid"]], [p["pgid"] for p in processes["probes"]])
        self.assertTrue(processes["probes"][0]["absent"])
        self.assertTrue(scan["redacted_before_persistence"])
        self.assertFalse(scan["external_secret_paths_read"])
        self.assertEqual(0, scan["secret_matches"])
        self.assertIn("execution/redacted.txt", scan["scanned_paths"])
        self.assertTrue(proof["external_state_unchanged"])
        # Inject a dummy credential into this test fixture only; the scanner
        # reports counts/paths but never includes credential values in its proof.
        (self.root / "execution/leak.txt").write_text(KEY)
        failed = runner.save_cleanup(self.root, "execution/cleanup", KEY, [])
        scan = runner.read_json(self.root / failed["credential_scan_path"])
        self.assertEqual(1, scan["secret_matches"])
        self.assertFalse(failed["credential_artifacts_clean"])
        self.assertNotIn(KEY, json.dumps(scan))

    def test_mechanical_scope_names_and_distinct_content_not_mirrors(self):
        spec = self.spec()
        spec["case"]["task_id"] = "T4"
        spec["task"] = {"id": "T4", "prompt": "Public D1 documentation question.",
                        "required_source_urls": [], "allowed_url_patterns": [r"https://developers\.cloudflare\.com/d1/.*"]}
        canonical = "https://developers.cloudflare.com/d1/best-practices/read-replication/"
        mirror = canonical + "index.md"
        sources = [{"url": canonical, "final_url": canonical, "canonical_url": canonical},
                   {"url": mirror, "final_url": mirror, "canonical_url": canonical}]
        def fetcher(url, task, deadline):
            raw = ("Whole HTML content." if url == canonical else "Whole native Markdown content.").encode()
            return webfetch.fetch_document(url, task, deadline, lambda u, timeout: (200, {"content-type": "text/plain"}, raw))
        record = runner.run_case(spec, KEY, self.responses([completion(None, [tool(canonical, id="a"), tool(mirror, id="b")]), completion()]), fetcher)
        for f in record["fetches"]:
            for name in ("raw_path", "text_path", "model_text_path"):
                # run_case fixture directory is intentionally not execution/cases;
                # copy into its returned public artifact layout for saved-only checks.
                path = self.root / f[name]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((Path(spec["directory"]) / "fetches" / Path(f[name]).name).read_bytes())
        path = self.root / record["history_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((Path(spec["directory"]) / "history.json").read_bytes())
        mechanical = runner.mechanical_compliance(self.root, record, spec["task"], sources)
        self.assertEqual(1, mechanical["distinct_fetched_pages"])
        self.assertFalse(mechanical["fetched_two_sources"])
        self.assertTrue(mechanical["source_rules"])
        self.assertTrue(mechanical["tool_rules"])
        history = runner.read_json(path)
        history[2]["tool_calls"][0]["function"]["name"] = "shell"
        runner.save_json(path, history)
        self.assertFalse(runner.mechanical_compliance(self.root, record, spec["task"], sources)["tool_rules"])
        record["fetches"][0]["redirects"] = [{"from": canonical, "to": "https://evil.test/", "status": 302}]
        self.assertFalse(runner.mechanical_compliance(self.root, record, spec["task"], sources)["source_rules"])

    def test_blind_shards_balanced_redacted_and_failed_truthful(self):
        self.frozen_fixture()
        def launch(case, directory):
            record = self.launch_record()(case, directory)
            if case["index"] == 2:
                record.update(status="provider_error", operational_complete=False)
            else:
                path = "execution/cases/" + case["id"] + "/answer.txt"
                (self.root / path).write_text("I am DeepSeek using max effort. Use secure comparison.")
                record.update(answer_path=path, visible_words=12)
            return record
        runner.run_study(self.root, launch)
        exported = runner.blind_export(self.root)
        self.assertEqual(20261007093207, PROTOCOL["blind_seed"])
        mapping = runner.read_json(self.root / "private/unblind.json")
        case_by_id = {c["id"]: c for c in runner.make_schedule()["cases"]}
        for shard, ids in exported["shards"].items():
            self.assertEqual(36, len(ids))
            counts = collections.Counter((case_by_id[mapping["mapping"][bid]]["configuration_id"],
                                          case_by_id[mapping["mapping"][bid]]["task_id"]) for bid in ids)
            self.assertEqual(36, len(counts))
            self.assertEqual({1}, set(counts.values()))
        failed = []
        for bid in exported["cases"]:
            path = "blind/cases/" + bid + "/case.json"
            payload = runner.read_json(self.root / path)
            self.assertEqual(runner.sha((self.root / path).read_bytes()), mapping["sealed_hashes"][path])
            serialized = json.dumps(payload)
            for forbidden in ("deepseek", "glm-5", "reasoning_effort", "wall_s", "prompt_tokens", "configuration_id", "execution/cases", "schedule_index"):
                self.assertNotIn(forbidden, serialized.lower())
            if not payload["mechanical"]["operational_complete"]:
                failed.append(payload)
                self.assertEqual("", payload["answer"])
                self.assertTrue(payload["mechanical"]["attempted"])
            else:
                self.assertIn("self-identification redacted", payload["answer"])
        self.assertEqual(1, len(failed))
        redactions = runner.read_json(self.root / "private/redactions.json")
        self.assertTrue(any(v for v in redactions.values()))
        self.assertNotIn("unblinded_utc", mapping)
        for operations in redactions.values():
            for operation in operations:
                self.assertEqual("self_identification", operation["reason"])
                self.assertEqual({"original", "replacement", "reason"}, set(operation))

    def test_blind_fetched_reference_coexistence_and_stable_gold_path(self):
        self.frozen_fixture(seal_now=False)
        body = "A complete factual note.\n"
        source_path = "dataset/archive/note.txt"
        (self.root / source_path).parent.mkdir(parents=True)
        (self.root / source_path).write_text(body)
        sources = [{"url": URL, "final_url": URL, "canonical_url": URL, "text_path": source_path,
                    "raw_sha256": runner.sha(body.encode()), "text_sha256": runner.sha(body.encode())},
                   {"url": URL + ".md", "final_url": URL + ".md", "canonical_url": URL, "text_path": source_path,
                    "raw_sha256": runner.sha(body.encode()), "text_sha256": runner.sha(body.encode())}]
        runner.save_json(self.root / "dataset/sources.json", sources)
        tasks = runner.read_json(self.root / "dataset/tasks.json")
        for task in tasks:
            if task["id"] == "T1":
                task.update(required_source_urls=[URL], allowed_url_patterns=[r"https://docs\.github\.com/en/webhooks(?:/.*)?"])
        runner.save_json(self.root / "dataset/tasks.json", tasks)
        gold = runner.read_json(self.root / "dataset/gold.json")
        gold["tasks"]["T1"]["checks"] = [{"id": "C1", "source_evidence": [{"url": URL, "quote": "A complete factual note.", "archive_path": source_path}]}]
        runner.save_json(self.root / "dataset/gold.json", gold)
        runner.seal(self.root)
        def launch(case, directory):
            task = next(t for t in tasks if t["id"] == case["task_id"])
            spec = self.spec(directory=directory)
            spec.update(case=case, task=task, sources=sources if task["id"] == "T1" else [],
                        ledger_path=str(self.root / "execution/post-starts.jsonl"), system="fixed")
            rows = [completion()]
            if task["id"] == "T1":
                rows = [completion(None, [tool(id="first"), tool(id="repeat")]), completion("A complete factual note. " + URL)]
            def fetcher(url, task_id, deadline):
                return webfetch.fetch_document(url, task_id, deadline, lambda u, timeout: (200, {"content-type": "text/plain"}, body.encode()))
            record = runner.run_case(spec, KEY, self.responses(rows), fetcher)
            record["cleanup"] = {"owned_group_absent": True}
            return record
        runner.run_study(self.root, launch)
        index = runner.blind_export(self.root)
        for bid in index["cases"]:
            payload = runner.read_json(self.root / ("blind/cases/" + bid + "/case.json"))
            if payload["task_id"] != "T1":
                continue
            fetched = [s for s in payload["sources"] if s["status"] == "fetched"]
            references = [s for s in payload["sources"] if s["status"] == "frozen_reference"]
            self.assertEqual(2, len(fetched))
            self.assertEqual(2, len(references))
            self.assertTrue(all(s["citation_support_eligible"] for s in fetched))
            self.assertTrue(all(not s["citation_support_eligible"] for s in references))
            self.assertEqual(fetched[0]["source_path"], payload["rubric"]["checks"][0]["source_evidence"][0]["source_path"])
            self.assertEqual(1, payload["mechanical"]["distinct_fetched_pages"])
            self.assertFalse(payload["mechanical"]["fetched_two_sources"])
            self.assertTrue(payload["mechanical"]["source_rules"])
            self.assertTrue(payload["mechanical"]["tool_rules"])

    def test_independent_saved_only_auditor_on_runner_gate_and_complete_fixtures(self):
        import verify as independent_verify
        fixture_spec = importlib.util.spec_from_file_location("readonly_p3_fixtures", A / "tests/audit/fixtures.py")
        fixtures = importlib.util.module_from_spec(fixture_spec)
        fixture_spec.loader.exec_module(fixtures)  # Module import has no fixture writes.
        for status in ("access_blocked", "completed"):
            with self.subTest(study=status):
                root = self.root / status
                root.mkdir()
                fixtures.frozen(root)  # Synthetic artifacts only inside runner-owned tests.
                for name in ("runner.py", "webfetch.py", "protocol.json", "system.txt", "tools.json", "schedule.json", "restart.json"):
                    (root / name).write_bytes((A / name).read_bytes())
                scope = runner.read_json(root / "scope.json")
                scope["runtime_root"] = str(runner.RUNTIME)
                runner.save_json(root / "scope.json", scope)
                workflow = runner.read_json(root / "preflight/workflow.json")
                workflow.update(runtime_root=str(runner.RUNTIME), created_utc=runner.utc(), synthetic_fixture=True,
                                review_paths=["preflight/review.json"])
                runner.save_json(root / "preflight/review.json", {"synthetic_fixture": True, "purpose": "offline audit integration, not parent approval"})
                runner.save_json(root / "preflight/workflow.json", workflow)
                sources = runner.read_json(root / "dataset/sources.json")
                for source in sources:
                    source["retrieved_utc"] = runner.utc()
                runner.save_json(root / "dataset/sources.json", sources)
                (root / "freeze.json").unlink()  # Replace the fixture seal before any mocked attempt.
                runner.seal(root)
                self.assertTrue(independent_verify.audit(root, stage="frozen")["ok"])
                self.assertIn("preflight/review.json", runner.read_json(root / "freeze.json")["files"])
                tasks = {t["id"]: t for t in runner.read_json(root / "dataset/tasks.json")}
                system = (root / "system.txt").read_text()
                def launch(case, directory):
                    spec = self.spec(directory=directory)
                    spec.update(case=case, task=tasks[case["task_id"]], system=system,
                                ledger_path=str(root / "execution/post-starts.jsonl"))
                    raw_usage = {"prompt_tokens": 100, "completion_tokens": 50,
                                 "prompt_tokens_details": {"cached_tokens": 20, "cache_write_tokens": 10},
                                 "completion_tokens_details": {"reasoning_tokens": 30}}
                    row = (400, {"error": {"message": "Global regions required"}}) if status == "access_blocked" else completion(usage=raw_usage)
                    record = runner.run_case(spec, KEY, self.responses([row]))
                    record["cleanup"] = runner.save_cleanup(root, "execution/cases/" + case["id"] + "/cleanup", KEY, [])
                    return record
                started = runner.utc()
                index = runner.run_study(root, launch, lambda i: runner.save_cleanup(root, "execution/cleanup", KEY, []))
                # Synthetic existing-schema receipt for injected offline transports;
                # no real credential was selected or parent provisioning invoked.
                runner.save_json(root / "execution/parent-provisioning.json", {
                    "synthetic_fixture": True,
                    "started_utc": started, "finished_utc": runner.utc(),
                    "credential_source": "parent read-only selected opencode-go integration credential",
                    "credential_store_copied": False, "worker_credential_store_access": False,
                    "ephemeral_environment_only": True, "secret_matches": 0,
                    "scanned_file_count": sum(path.is_file() for path in root.rglob("*")),
                    "runner_returncode": 0, "caller_retries": 0})
                audited = independent_verify.audit(root, stage="collected")
                self.assertTrue(audited["ok"])
                self.assertEqual(status, audited["study_status"])
                self.assertEqual(1 if status == "access_blocked" else 72, index["attempted_cases"])
                self.assertEqual(72, index["terminal_records"])
                runner.blind_export(root)
                checked = independent_verify.Auditor(root).frozen().collected().blind()
                self.assertEqual(72, len(checked.blinds))
                self.assertTrue(all(not b["mechanical"]["fetched_two_sources"] for b in checked.blinds.values()))
                self.assertFalse((root / "grades").exists())

    def test_visible_words_count_commentary_but_not_link_destinations(self):
        self.assertEqual(5, runner.visible_words("## Decision\nUse [secure comparison](https://example.org/a-long/path) now."))


class FetchBehavior(OfflineCase):
    def test_substantive_note_alert_and_admonition_retained_not_sidebar(self):
        raw = b'''<main><p>Overview.</p>
          <aside role="note" class="starlight-aside starlight-aside--note"><p>Writes are forwarded to the primary database.</p><a href="#contract">Read contract</a></aside>
          <aside role="alert"><p>Failures roll back the transaction.</p></aside>
          <aside class="admonition warning"><p>Do not weaken verification.</p></aside>
          <aside class="callout tip"><p>Carry prior request context.</p></aside>
          <aside class="sidebar"><p>Sidebar navigation noise.</p></aside>
          <aside role="navigation" class="note"><p>Navigation wins over note styling.</p></aside>
          <aside><p>Unmarked sidebar noise.</p></aside></main>'''
        text = webfetch.extract_document(raw, "text/html", "https://developers.cloudflare.com/d1/")
        for fact in ("Writes are forwarded to the primary database.", "Failures roll back the transaction.",
                     "Do not weaken verification.", "Carry prior request context.", "https://developers.cloudflare.com/d1/#contract"):
            self.assertIn(fact, text)
        for noise in ("Sidebar navigation", "Navigation wins", "Unmarked sidebar"):
            self.assertNotIn(noise, text)

    def test_extractor_inline_adjacency_links_anchors_whole_main_and_nav_noise(self):
        a = b'<nav>noise A</nav><main><h2 id="rules">Rules</h2><p>per<strong>mission</strong> is <code>not</code> a boundary.</p><p>Other substantive content <a href="/en/webhooks/using-webhooks/page#x">next</a>.</p></main>'
        b = a.replace(b"noise A", b"noise B completely different")
        extracted = webfetch.extract_document(a, "text/html", URL)
        self.assertIn("permission is not a boundary.", extracted)
        self.assertIn("Other substantive content", extracted)
        self.assertIn(URL + "#rules", extracted)
        self.assertIn("https://docs.github.com/en/webhooks/using-webhooks/page#x", extracted)
        self.assertNotIn("noise", extracted)
        self.assertEqual(extracted, webfetch.extract_document(b, "text/html", URL))
        markdown = "# Native\n\n[link](https://go.dev/doc/toolchain#select)\nBody words."
        self.assertEqual(markdown + "\n", webfetch.extract_document(markdown.encode(), "text/markdown", "https://go.dev/doc/toolchain"))
        self.assertEqual("a b c", webfetch.normalize_text("a\n  b\t c"))

    def test_url_denials_and_each_redirect_validation(self):
        for url in ("http://docs.github.com/en/webhooks", "https://u:p@docs.github.com/en/webhooks",
                    "https://docs.github.com:444/en/webhooks", "https://docs.github.com.evil.test/en/webhooks",
                    "https://127.0.0.1/en/webhooks", "https://docs.github.com/en/webhooks/../secret",
                    "https://docs.github.com/en/webhooks/%2e%2e/secret", "https://docs.github.com/en/webhooks?token=x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                webfetch.validate_url(url, "T1")
        seen = []
        def redirect(url, timeout):
            seen.append(url)
            return 302, {"location": "https://evil.test/secret"}, b""
        result = webfetch.fetch_document(URL, "T1", time.monotonic() + 5, redirect)
        self.assertEqual([URL], seen)
        self.assertEqual("rejected", result["status"])
        self.assertIsNone(result["model_text"])
        self.assertEqual(1, len(result["redirects"]))

    def test_public_dns_rejects_mixed_private_answers_and_pins_tls(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
                   (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=records), self.assertRaises(webfetch.Rejected):
            webfetch.public_addresses("docs.github.com")
        with patch.object(socket, "getaddrinfo", return_value=records[:1]):
            self.assertEqual(["93.184.216.34"], webfetch.public_addresses("docs.github.com"))
        sock = Mock()
        with patch.object(socket, "create_connection", return_value=sock) as connect:
            connection = webfetch._PinnedHTTPS("docs.github.com", "93.184.216.34", 3)
            with patch.object(connection._context, "wrap_socket", return_value=Mock()) as wrap:
                connection.connect()
                connect.assert_called_once_with(("93.184.216.34", 443), 3)
                wrap.assert_called_once_with(sock, server_hostname="docs.github.com")

    def test_fetch_404_is_error_not_content_and_timeout_clipped(self):
        captured = []
        def transport(url, timeout):
            captured.append(timeout)
            return 404, {"content-type": "text/html"}, b"Not found should never be model content"
        result = webfetch.fetch_document(URL, "T1", time.monotonic() + 2, transport)
        self.assertEqual("http_error", result["status"])
        self.assertEqual(404, result["http_status"])
        self.assertIsNone(result["text"])
        self.assertLessEqual(captured[0], 2)
        self.assertGreater(captured[0], 0)

    def test_truncation_records_full_extraction_and_explicit_preview(self):
        raw = ("Entire unselected page content\n" * 12000).encode()
        result = webfetch.fetch_document(URL, "T1", time.monotonic() + 10, lambda url, timeout: (200, {"content-type": "text/plain"}, raw))
        self.assertEqual("ok", result["status"])
        self.assertEqual(raw, result["raw"])
        self.assertGreater(len(result["text"].encode()), webfetch.TEXT_LIMIT)
        self.assertLessEqual(len(result["model_text"].encode()), webfetch.TEXT_LIMIT)
        self.assertIn("TRUNCATED", result["model_text"])
        self.assertTrue(result["truncated"])
        too_big = webfetch.fetch_document(URL, "T1", time.monotonic() + 10, lambda url, timeout: (200, {"content-type": "text/plain"}, b"x" * (webfetch.RAW_LIMIT + 1)))
        self.assertEqual("rejected", too_big["status"])
        self.assertEqual(webfetch.RAW_LIMIT, len(too_big["raw"]))
        self.assertTrue(too_big["truncated"])
        self.assertIsNone(too_big["model_text"])

    def test_actual_preview_paths_and_hashes_are_retained(self):
        raw = b"Full generic page\n" * 25000
        def fetcher(url, task, deadline):
            return webfetch.fetch_document(url, task, deadline, lambda u, timeout: (200, {"content-type": "text/plain"}, raw))
        bodies = []
        record = runner.run_case(self.spec(), KEY, self.responses([completion(None, [tool()]), completion()], bodies), fetcher)
        f = record["fetches"][0]
        model_path = Path(self.spec()["directory"]) / "fetches/f1-model_text.txt"
        self.assertEqual(runner.sha(model_path.read_bytes()), f["model_text_sha256"])
        self.assertEqual(model_path.read_text(), json.loads(bodies[1][0]["messages"][-1]["content"])["text"])
        self.assertEqual(runner.sha(raw), f["raw_sha256"])
        self.assertNotEqual(f["text_sha256"], f["model_text_sha256"])


if __name__ == "__main__":
    unittest.main()
