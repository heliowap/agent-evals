import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from harness.core.audit import audit_execution
from harness.core.runner import run_trial
from harness.core.supervisor import supervise_trial


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = json.loads((ROOT / "contracts/runtime.json").read_text())
SECRET = "fixture-ephemeral-secret-DO-NOT-PERSIST"


def schema(name, field):
    return {"type": "function", "function": {"name": name, "description": "fixture tool",
            "parameters": {"type": "object", "required": [field], "additionalProperties": False,
                           "properties": {field: {"type": "string"}}}}}


def call(identifier, name="read", arguments=None):
    return {"id": identifier, "type": "function", "function": {
        "name": name, "arguments": json.dumps(arguments if arguments is not None else {"path": "file"})},
        "native_call_signature": {"bytes": "opaque-call-signature"}}


def response(content="finished", calls=None, finish=None, **extra):
    assistant = {"role": "assistant", "content": content}
    if calls is not None:
        assistant["tool_calls"] = calls
    assistant.update(extra)
    return {"id": "native-id", "model": "actual-version-20261007", "system_fingerprint": "native-fingerprint",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                      "completion_tokens_details": {"reasoning_tokens": 3}, "future_counter": 7},
            "choices": [{"index": 0, "finish_reason": finish or ("tool_calls" if calls else "stop"),
                         "message": assistant, "future_choice": [1, 2]}]}


class Transcript:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.sessions = []

    def __call__(self, body, credentials, session, deadline, start):
        start()
        self.requests.append(copy.deepcopy(body))
        self.sessions.append(session)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, tuple) else (200, json.dumps(value).encode())


class Dispatch:
    def __init__(self, text="actual evidence", status="ok", metadata=None):
        self.requests = []
        self.text, self.status, self.metadata = text, status, metadata or {}

    def dispatch(self, name, arguments, context, deadline):
        self.requests.append((name, arguments, context, deadline))
        return {"status": self.status, "text": self.text, "archives": {"source.txt": self.text},
                "metadata": self.metadata}


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="core-fixture-")
        self.root = Path(self.temp.name).resolve()
        self.counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def spec(self, suite="code", gemini=False):
        self.counter += 1
        config = copy.deepcopy(RUNTIME["configurations"][0 if gemini else 3])
        return {"trial": {"id": "fixture-" + str(self.counter), "index": self.counter},
                "task": {"id": "public-task", "suite": suite, "prompt": "Research the public task."},
                "configuration": config, "runtime": copy.deepcopy(RUNTIME),
                "tools": [schema("websearch", "query"), schema("webfetch", "url")] if suite == "web"
                         else [schema("read", "path"), schema("list", "path")],
                "tool_context": {"snapshot_root": "assigned-public-snapshot"} if suite == "code" else
                                {"search_contract": {"engine": "fixture"}},
                "directory": str(self.root / ("trial-" + str(self.counter))),
                "ledger_path": str(self.root / "ledger.jsonl")}

    def run_fixture(self, spec, responses, dispatcher=None, credentials=None):
        transport = Transcript(responses)
        record = run_trial(spec, credentials or {"api_key": SECRET}, transport, dispatcher or Dispatch())
        return record, transport

    def assert_audit(self, runtime=None):
        report = audit_execution(self.root, runtime or RUNTIME)
        self.assertEqual(report["status"], "passed", report)

    def test_native_history_parallel_batch_gemini_and_final_separation(self):
        spec = self.spec(gemini=True)
        native = response("Intermediate diagnostic only.", [call("a"), call("b", "list")],
                          reasoning_content="native reasoning", reasoning={"signature": "opaque", "data": [1]},
                          signature="native-signature", future_native={"unknown": [1, {"x": True}]})
        dispatcher = Dispatch()
        record, transport = self.run_fixture(spec, [native, response("Final answer only.")], dispatcher)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["final_answer"], "Final answer only.")
        self.assertEqual(record["intermediate_text"], ["Intermediate diagnostic only."])
        continuation = transport.requests[1]["messages"]
        self.assertEqual([m for m in continuation if m["role"] == "assistant"], [native["choices"][0]["message"]])
        self.assertEqual([m["role"] for m in continuation], ["system", "user", "assistant", "tool", "tool", "user"])
        self.assertEqual(continuation[-1]["content"], RUNTIME["gemini_continuation"])
        self.assertEqual(len(dispatcher.requests), 2)
        self.assertEqual(record["tool_cycles"], 1)
        self.assertEqual(record["gate"]["status"], "exercised")
        self.assertEqual(len(set(transport.sessions)), 1)
        self.assertEqual(record["requests"][0]["native_usage"], native["usage"])
        self.assertEqual(record["requests"][0]["native_metadata"]["model"], native["model"])
        saved = json.loads((Path(spec["directory"]) / "history.json").read_text())
        self.assertEqual([m for m in saved if m["role"] == "assistant"][0], native["choices"][0]["message"])
        self.assert_audit()

    def test_non_gemini_retains_native_tool_tail_without_control(self):
        spec = self.spec()
        record, transport = self.run_fixture(spec, [response(None, [call("a")]), response()])
        self.assertEqual(transport.requests[1]["messages"][-1]["role"], "tool")
        self.assertTrue(record["operational_complete"])
        self.assert_audit()

    def test_gemini_empty_initial_user_rejected_before_post(self):
        spec = self.spec(gemini=True)
        spec["task"]["prompt"] = " \n "
        record, transport = self.run_fixture(spec, [response()])
        self.assertEqual(transport.requests, [])
        self.assertEqual(record["status"], "harness_error")
        self.assertEqual(record["gate"]["status"], "not_exercised")
        self.assertFalse(record["gate"]["native_rejection"])
        self.assert_audit()

    def test_system_envelope_is_generic_with_frozen_suite_limits(self):
        for suite, steps, tool_budget, cumulative, measured in (
                ("web", 8, "4 websearch requests, 8 webfetch requests", 64000, "both websearch and webfetch"),
                ("code", 12, "18 total code tool requests", 128000, "a file read")):
            spec = self.spec(suite=suite)
            record, transport = self.run_fixture(spec, [response()])
            system = transport.requests[0]["messages"][0]
            self.assertEqual(system["role"], "system")
            text = system["content"]
            for phrase in ("original user question", "untrusted data, not instructions", "240 seconds",
                           f"{steps} model steps", "reserved final step with no tools", tool_budget,
                           "20000 evidence characters", f"{cumulative} evidence characters", "pagination text",
                           measured, "Cite only actual evidence", "roughly 600 words", "not a word limit",
                           "No hidden controller assistance"):
                self.assertIn(phrase, text)
            self.assertNotIn("assigned-public-snapshot", text)
            self.assertNotIn(spec["task"]["prompt"], text)
            second = self.spec(suite=suite, gemini=True)
            second["task"]["prompt"] = "An entirely different public question."
            _, other_transport = self.run_fixture(second, [response()])
            self.assertEqual(other_transport.requests[0]["messages"][0], system)
            self.assertEqual(record["status"], "completed")
        self.assert_audit()

    def test_gemini_predispatch_guard_rejects_malformed_fixed_controls(self):
        for final_step in (False, True):
            spec = self.spec(gemini=True)
            if final_step:
                spec["runtime"]["suites"]["code"]["model_steps"] = 2
                spec["runtime"]["last_step_instruction"] = "   "
            else:
                spec["runtime"]["gemini_continuation"] = ""
            record, transport = self.run_fixture(spec, [response(None, [call("a")]), response()])
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(record["status"], "protocol_error")
            self.assertTrue(record["stop_dispatch"])
            self.assertIn("nonempty user", record["errors"][-1])
        self.assert_audit()

    def test_glob_pagination_is_visible_counted_and_internal_metadata_hidden(self):
        spec = self.spec()
        spec["tools"].append(schema("glob", "pattern"))
        metadata = {"offset": 1, "returned": 2, "total": 4, "unit": "entries", "next_offset": 3,
                    "truncated": True, "snapshot_root": "/absolute-private-snapshot",
                    "profile_sha256": "private-profile-internals", "line_count": 2}
        dispatcher = Dispatch(text="first.py\nsecond.py", metadata=metadata)
        record, transport = self.run_fixture(spec, [response(None, [call("g", "glob", {"pattern": "**/*.py"})]),
                                                  response()], dispatcher)
        message = next(m["content"] for m in transport.requests[1]["messages"] if m["role"] == "tool")
        candidate = json.loads(message.split("\n", 1)[1].rsplit("\n", 1)[0])
        for field in ('"next_offset": 3', '"returned": 2', '"total": 4', '"unit": "entries"', '"line_count": 2'):
            self.assertIn(field, candidate["text"])
        self.assertTrue(candidate["source_truncated"])
        self.assertFalse(candidate["core_budget_truncated"])
        self.assertNotIn("absolute-private-snapshot", message)
        self.assertNotIn("private-profile-internals", message)
        self.assertEqual(record["evidence_characters"], len(candidate["text"]))
        self.assertGreater(record["evidence_characters"], len(dispatcher.text))
        visible_path = Path(spec["directory"]) / record["tool_calls"][0]["visible_path"]
        self.assertEqual(json.loads(visible_path.read_text())["message"], message)
        self.assert_audit()

    def test_core_cut_invalidates_whole_page_cursor_with_explicit_warning(self):
        spec = self.spec()
        spec["runtime"]["limits"]["result_characters"] = 500
        metadata = {"offset": 1, "returned": 100, "total": 1000, "unit": "lines", "next_offset": 101,
                    "truncated": True}
        dispatcher = Dispatch(text="source.py:1: " + "x" * 2000, metadata=metadata)
        record, transport = self.run_fixture(spec, [response(None, [call("a")]), response()], dispatcher)
        message = next(m["content"] for m in transport.requests[1]["messages"] if m["role"] == "tool")
        candidate = json.loads(message.split("\n", 1)[1].rsplit("\n", 1)[0])
        self.assertTrue(candidate["source_truncated"])
        self.assertTrue(candidate["core_budget_truncated"])
        self.assertTrue(candidate["unsafe_next_offset"])
        self.assertIn('"next_offset": null', candidate["text"])
        self.assertNotIn('"next_offset": 101', candidate["text"])
        self.assertIn("unseen text has not been read", candidate["text"])
        self.assertIn("last visible location", candidate["text"])
        self.assertEqual(record["evidence_characters"], 500)
        self.assertEqual(len(candidate["text"]), 500)
        original = json.loads((Path(spec["directory"]) / record["tool_calls"][0]["original_path"]).read_text())
        self.assertEqual(original["metadata"]["next_offset"], 101)
        self.assertEqual(original["text"], dispatcher.text)
        self.assert_audit(spec["runtime"])

    def test_no_retry_for_400_429_401_403_and_prefill_rejection(self):
        fixtures = [(400, "plain bad request", "provider_error"),
                    (400, "assistant prefill is not supported", "protocol_error"),
                    (400, "Requests ending with a model turn are not supported.", "protocol_error"),
                    (400, "This model does not support assistant message prefill. The conversation must end with a user message.", "protocol_error"),
                    (400, "unsupported parameter reasoning_effort", "protocol_error"),
                    (429, "quota exceeded", "quota_error"), (401, "unauthorized", "auth_error"),
                    (403, "forbidden", "auth_error")]
        for status, error, expected in fixtures:
            with self.subTest(status=status, error=error):
                spec = self.spec()
                record, transport = self.run_fixture(spec, [(status, json.dumps({"error": error}).encode()), response()])
                self.assertEqual(record["status"], expected)
                self.assertEqual(len(transport.requests), 1)
                self.assertFalse(record["operational_complete"])
                self.assertEqual(record["final_answer"], "")
                self.assertEqual(record["stop_dispatch"], expected in RUNTIME["stopping_statuses"])
        self.assert_audit()

    def test_provider_prose_is_not_a_protocol_rejection(self):
        record, _ = self.run_fixture(self.spec(), [response("The documentation mentions unsupported prefill.")])
        self.assertEqual(record["status"], "completed")

    def test_lease_and_ledger_prevent_replay_even_different_directory(self):
        spec = self.spec()
        self.run_fixture(spec, [response()])
        transport = Transcript([response()])
        with self.assertRaises(FileExistsError):
            run_trial(spec, {}, transport, Dispatch())
        spec["directory"] = str(self.root / "another-directory")
        with self.assertRaises(FileExistsError):
            run_trial(spec, {}, transport, Dispatch())
        self.assertEqual(transport.requests, [])
        self.assert_audit()

    def test_interrupted_send_is_not_replayed(self):
        spec = self.spec()
        record, transport = self.run_fixture(spec, [TimeoutError("uncertain in-flight POST"), response()])
        self.assertEqual(record["status"], "timeout")
        self.assertEqual(len(transport.requests), 1)
        with self.assertRaises(FileExistsError):
            run_trial(spec, {}, transport, Dispatch())
        self.assert_audit()

    def test_final_step_nonempty_user_no_tools_and_no_postcap_send(self):
        for gemini in (True, False):
            spec = self.spec(gemini=gemini)
            spec["runtime"]["suites"]["code"]["model_steps"] = 2
            dispatcher = Dispatch()
            record, transport = self.run_fixture(spec, [response("not final", [call("a")]), response("final")], dispatcher)
            last = transport.requests[-1]
            self.assertNotIn("tools", last)
            self.assertEqual(last["messages"][-1], {"role": "user", "content": RUNTIME["last_step_instruction"]})
            self.assertEqual(record["status"], "completed")
        # A tool returned on the final step is recorded/rejected, never dispatched.
        spec = self.spec()
        spec["runtime"]["suites"]["code"]["model_steps"] = 1
        dispatcher = Dispatch()
        record, transport = self.run_fixture(spec, [response(None, [call("forbidden")]), response()], dispatcher)
        self.assertEqual(record["status"], "step_limit")
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(dispatcher.requests, [])
        self.assertEqual(record["tool_calls"][0]["rejection"], "final_step")

    def test_bad_arguments_duplicates_and_failures_count_requested_dispatches(self):
        spec = self.spec()
        spec["runtime"]["suites"]["code"]["tool_calls"] = 4
        batch = [call("bad", arguments={"wrong": "field"}), call("ok"), call("ok"), call("badjson"), call("over")]
        batch[3]["function"]["arguments"] = "{broken"
        dispatcher = Dispatch(status="error", text="tool failure, not evidence")
        record, _ = self.run_fixture(spec, [response(None, batch), response("answer after cap")], dispatcher)
        self.assertEqual(len(dispatcher.requests), 1)
        self.assertEqual(len(record["tool_calls"]), 5)
        self.assertEqual([r.get("rejection") for r in record["tool_calls"]],
                         ["bad_arguments", None, "duplicate_call_id", "bad_arguments", "tool_cap"])
        self.assertEqual(record["status"], "tool_limit")
        self.assertFalse(record["operational_complete"])
        self.assertEqual(record["final_answer"], "")
        self.assert_audit(spec["runtime"])

    def test_web_per_tool_budget_parallel_batch(self):
        spec = self.spec(suite="web", gemini=True)
        batch = [call("s" + str(i), "websearch", {"query": "query"}) for i in range(5)]
        batch += [call("f", "webfetch", {"url": "https://fixture.invalid"})]
        dispatcher = Dispatch()
        record, _ = self.run_fixture(spec, [response(None, batch), response()], dispatcher)
        self.assertEqual(len(dispatcher.requests), 5)
        self.assertEqual(record["tool_calls"][4]["rejection"], "tool_cap")
        self.assertTrue(record["tool_calls"][5]["dispatched"])
        self.assertEqual(record["status"], "tool_limit")
        self.assert_audit()

    def test_evidence_truncation_originals_archived_exact_visible_caps(self):
        for suite, size in (("web", 64000), ("code", 128000)):
            spec = self.spec(suite=suite)
            name, args = ("webfetch", {"url": "https://fixture.invalid"}) if suite == "web" else ("read", {"path": "file"})
            batch = [call(str(i), name, args) for i in range(8)]
            dispatcher = Dispatch(text="e" * 30000)
            record, _ = self.run_fixture(spec, [response(None, batch), response()], dispatcher)
            self.assertEqual(record["evidence_characters"], size)
            for row in record["tool_calls"]:
                self.assertLessEqual(row["visible_characters"], 20000)
                self.assertTrue(row["truncated"])
                original = json.loads((Path(spec["directory"]) / row["original_path"]).read_text())
                self.assertEqual(original["text"], dispatcher.text)
                visible = json.loads((Path(spec["directory"]) / row["visible_path"]).read_text())
                self.assertEqual(len(visible["text"]), row["visible_characters"])
                self.assertIn('"truncated": true', visible["message"])
            self.assert_audit()

    def test_tool_outage_stops_batch_and_model_continuation(self):
        spec = self.spec(suite="web")
        dispatcher = Dispatch(status="error", text="shared search unavailable", metadata={"stop_reason": "search_outage"})
        record, transport = self.run_fixture(spec, [response(None, [call("a", "websearch", {"query": "q"}),
                                                    call("b", "websearch", {"query": "q"})]), response()], dispatcher)
        self.assertEqual(record["status"], "search_outage")
        self.assertTrue(record["stop_dispatch"])
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(len(dispatcher.requests), 1)
        self.assertEqual(len(record["tool_calls"]), 2)
        self.assertEqual(record["tool_calls"][1]["rejection"], "trial_stopped")
        self.assert_audit()

    def test_unknown_native_secrets_and_headers_are_sanitized_without_dropping_fields(self):
        spec = self.spec()
        native = response("answer", future_native={"secret_echo": SECRET, "headers": {"Authorization": "Bearer OTHER"},
                                                    "retained": {"signature": "opaque"}})
        record, _ = self.run_fixture(spec, [native])
        self.assertEqual(record["requests"][0]["assistant"]["future_native"]["retained"], {"signature": "opaque"})
        self.assertNotIn(SECRET, json.dumps(record))
        self.assertNotIn("Bearer OTHER", json.dumps(record))
        for path in self.root.rglob("*"):
            if path.is_file():
                raw = path.read_bytes()
                self.assertNotIn(SECRET.encode(), raw, str(path))
                self.assertNotIn(b"Bearer OTHER", raw, str(path))
        self.assert_audit()

    def test_nonanswers_are_not_completed_or_final(self):
        for native in (response("partial answer", finish="length"), response("   "), response(None)):
            spec = self.spec()
            record, _ = self.run_fixture(spec, [native])
            self.assertEqual(record["status"], "incomplete")
            self.assertFalse(record["operational_complete"])
            self.assertEqual(record["final_answer"], "")
            self.assertFalse((Path(spec["directory"]) / "final-answer.txt").exists())
        self.assert_audit()

    def test_archive_path_escape_and_dispatch_schema_are_harness_errors(self):
        def dispatcher(name, arguments, context, deadline):
            return {"status": "ok", "text": "text", "archives": {"../../../../escape": "forbidden"}, "metadata": {}}
        record, transport = self.run_fixture(self.spec(), [response(None, [call("a")]), response()], dispatcher)
        self.assertEqual(record["status"], "harness_error")
        self.assertEqual(len(transport.requests), 1)
        self.assertFalse((self.root / "escape").exists())
        self.assert_audit()

    def test_malformed_native_schema_stops_without_retry(self):
        for native in ([], {"choices": [None]}, {"choices": []}, {"choices": [{"message": {"role": "user"}}]}):
            record, transport = self.run_fixture(self.spec(), [native, response()])
            self.assertEqual(record["status"], "protocol_error")
            self.assertTrue(record["stop_dispatch"])
            self.assertEqual(len(transport.requests), 1)
        self.assert_audit()

    def test_symlink_directory_refused_before_send(self):
        spec = self.spec()
        target = self.root / "outside"
        target.mkdir()
        Path(spec["directory"]).symlink_to(target, target_is_directory=True)
        transport = Transcript([response()])
        with self.assertRaises(ValueError):
            run_trial(spec, {}, transport, Dispatch())
        self.assertFalse(transport.requests)

    def test_direct_transport_own_user_agent_stable_session_once_without_real_network(self):
        spec = self.spec()
        spec["configuration"]["endpoint"] = "http://offline.fixture.invalid/v1/chat/completions"
        sent = []

        class Connection:
            def __init__(self, host, port, timeout):
                self.host = host

            def request(self, method, path, body, headers):
                sent.append((method, path, json.loads(body), headers))

            def getresponse(self):
                class Reply:
                    status = 429

                    def read(self):
                        return b'{"error":"fixture quota"}'
                return Reply()

            def close(self):
                pass

        with patch("harness.core.transport.http.client.HTTPConnection", Connection):
            record = run_trial(spec, {"api_key": SECRET})
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][3]["x-opencode-session"], record["session_id"])
        self.assertTrue(sent[0][3]["User-Agent"].startswith("research-eval/"))
        self.assertEqual(record["status"], "quota_error")
        self.assertNotIn("headers", record["requests"][0])
        self.assert_audit()

    def test_supervisor_deadline_includes_startup_terminal_without_sends(self):
        spec = self.spec()
        spec["runtime"]["limits"]["wall_seconds"] = 0
        record = supervise_trial(spec, {"api_key": SECRET})
        self.assertEqual(record["status"], "timeout")
        self.assertFalse(record["requests"])
        receipt = json.loads((Path(spec["directory"]) / "supervisor-receipt.json").read_text())
        self.assertTrue(receipt["cleanup"]["not_spawned"])
        self.assertEqual(receipt["worker_shutdown_reason"], "timeout")
        self.assert_audit()

    def test_supervisor_terminates_only_owned_group_and_drains(self):
        spec = self.spec()
        spec["runtime"]["limits"]["wall_seconds"] = 0.25
        original_popen = subprocess.Popen
        workers = []

        def fixture_popen(command, **kwargs):
            # Real child process, but no model/network/credentials/config-store access.
            child = original_popen([sys.executable, "-B", "-c",
                                    "import sys,time; sys.stdin.read(); time.sleep(30)"], **kwargs)
            workers.append(child)
            return child

        unrelated = original_popen([sys.executable, "-B", "-c", "import time; time.sleep(30)"], start_new_session=True)
        try:
            before = time.monotonic()
            with patch("harness.core.supervisor.subprocess.Popen", fixture_popen):
                record = supervise_trial(spec, {"api_key": SECRET})
            self.assertEqual(record["status"], "timeout")
            self.assertTrue(record["cleanup"]["terminated"])
            self.assertTrue(record["cleanup"]["drained"])
            self.assertIsNotNone(workers[0].poll())
            self.assertIsNone(unrelated.poll())
            receipt = json.loads((Path(spec["directory"]) / "supervisor-receipt.json").read_text())
            self.assertTrue(receipt["cleanup"]["group_absent"])
            self.assertTrue(receipt["cleanup"]["waited"])
            self.assertEqual(receipt["cleanup"]["returncode"], workers[0].returncode)
            self.assertIn("no deadline grace", receipt["latency_scope"])
            self.assertLess(time.monotonic() - before, 3)
            self.assert_audit()
        finally:
            unrelated.terminate()
            unrelated.wait()

    def test_audit_not_executed_and_detects_duplicate_start(self):
        self.assertEqual(audit_execution(self.root, RUNTIME)["status"], "not_executed")
        spec = self.spec()
        self.run_fixture(spec, [response()])
        path = Path(spec["ledger_path"])
        rows = path.read_text().splitlines()
        start = next(line for line in rows if json.loads(line)["event"] == "start")
        with path.open("a") as stream:
            stream.write(start + "\n")
        report = audit_execution(self.root, RUNTIME)
        self.assertEqual(report["status"], "failed")
        self.assertIn("duplicate start", report["errors"])

    def test_supervisor_inflight_send_has_terminal_and_cannot_replay(self):
        spec = self.spec()
        spec["runtime"]["limits"]["wall_seconds"] = 0.4
        original_popen = subprocess.Popen

        def fixture_popen(command, **kwargs):
            program = ("import json,sys,time; from harness.core.runner import _run_reserved; "
                       "e=json.load(sys.stdin); "
                       "exec('def transport(body, credentials, session, deadline, start):\\n"
                       " start()\\n time.sleep(30)\\n'); "
                       "_run_reserved(e['spec'],e['credentials'],e['record'],transport)")
            return original_popen([sys.executable, "-B", "-c", program], **kwargs)

        with patch("harness.core.supervisor.subprocess.Popen", fixture_popen):
            record = supervise_trial(spec, {"api_key": SECRET})
        self.assertEqual(record["status"], "timeout")
        self.assertEqual(len(record["requests"]), 1)
        self.assertEqual(record["requests"][0]["starts"], 1)
        self.assertTrue(record["requests"][0]["ambiguous_in_flight"])
        self.assertTrue(record["cleanup"]["drained"])
        with self.assertRaises(FileExistsError):
            run_trial(spec, {}, Transcript([response()]), Dispatch())
        self.assert_audit()

    def test_completed_supervisor_receipt_waits_drains_without_mutating_terminal(self):
        for abnormal_exit in (False, True):
            spec = self.spec()
            original_popen = subprocess.Popen
            workers = []

            def fixture_popen(command, **kwargs):
                program = ("import json,sys; from harness.core.runner import _run_reserved; "
                           "e=json.load(sys.stdin); "
                           "exec('def transport(body, credentials, session, deadline, start):\\n"
                           " start()\\n return 200, {\\\"choices\\\":[{\\\"finish_reason\\\":\\\"stop\\\","
                           "\\\"message\\\":{\\\"role\\\":\\\"assistant\\\",\\\"content\\\":\\\"final\\\"}}]}\\n'); "
                           "_run_reserved(e['spec'],e['credentials'],e['record'],transport); "
                           f"sys.exit({7 if abnormal_exit else 0})")
                child = original_popen([sys.executable, "-B", "-c", program], **kwargs)
                workers.append(child)
                return child

            with patch("harness.core.supervisor.subprocess.Popen", fixture_popen):
                record = supervise_trial(spec, {"api_key": SECRET})
            self.assertEqual(record["status"], "completed")
            self.assertEqual(record["final_answer"], "final")
            persisted = json.loads((Path(spec["directory"]) / "record.json").read_text())
            self.assertEqual(record, persisted)
            self.assertNotIn("cleanup", persisted)
            receipt = json.loads((Path(spec["directory"]) / "supervisor-receipt.json").read_text())
            self.assertTrue(receipt["cleanup"]["waited"])
            self.assertTrue(receipt["cleanup"]["drained"])
            self.assertTrue(receipt["cleanup"]["group_absent"])
            self.assertEqual(receipt["cleanup"]["returncode"], 7 if abnormal_exit else 0)
            self.assertEqual(workers[0].poll(), receipt["cleanup"]["returncode"])
            self.assertEqual(receipt["stop_dispatch"], abnormal_exit)
            self.assertEqual(receipt["status"], "warning" if abnormal_exit else "passed")
            self.assertGreaterEqual(receipt["supervisor_wall_seconds"], record["wall_seconds"])
            self.assert_audit()


if __name__ == "__main__":
    unittest.main()
