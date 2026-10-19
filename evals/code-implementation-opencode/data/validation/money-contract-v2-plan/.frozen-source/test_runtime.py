from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import bench
import controller
from domain import Budget, CANDIDATES
import grader
import runtime
import tasks


class HarnessTests(unittest.TestCase):
    def test_schedules_balanced_and_distinct(self):
        for phase, reps, count in (("budget", 1, 6), ("smoke", 1, 6), ("screening", 3, 216), ("confirmation", 5, 80)):
            candidates = CANDIDATES[:2] if phase == "confirmation" else CANDIDATES
            rows = bench.schedule(tasks.inventory(phase), candidates, reps, 42)
            self.assertEqual(len(rows), count)
            keys = {(r["task"], r["rep"], r["candidate"]) for r in rows}
            self.assertEqual(len(keys), count)
            for block in {r["block"] for r in rows}:
                self.assertEqual({r["candidate"] for r in rows if r["block"] == block}, {c.id for c in candidates})
        self.assertFalse({t.id for t in tasks.inventory("screening")} & {t.id for t in tasks.inventory("confirmation")})

    def test_private_config_removes_native_step_limit_and_host_permissions(self):
        for candidate in CANDIDATES:
            config = runtime.configuration(candidate, Path("/private/observer"), Path("/private/terminal"))
            self.assertNotIn("steps", config["agents"]["implementer"])
            self.assertEqual([r["action"] for r in config["permissions"] if r["effect"] == "allow"], ["terminal"])
            self.assertEqual(config["model"], candidate.selection)
            self.assertEqual(config["mcp"], {})
            self.assertEqual(config["skills"], [])

    def test_native_agent_audit_refuses_effective_steps_even_if_config_omits_them(self):
        candidate = CANDIDATES[0]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            work = root / "project"
            work.mkdir()
            expected = runtime.configuration(candidate, root / "observer", root / "terminal")
            runtime.save(root / "config.json", expected)
            (root / "observations.jsonl").write_text('{"event":"ready"}\n')
            (root / "terminal.jsonl").write_text('{"event":"ready","tools":[{"id":"terminal","name":"terminal"}]}\n')
            agent = {"id": "implementer"}
            @contextmanager
            def server(*_):
                yield {}
            def api(binary, work, server, operation, params=None, data=None, timeout=45):
                if operation == "config.get":
                    return [{"type": "document", "path": str(root / "config/opencode/opencode.json"), "info": expected}]
                if operation == "plugin.list":
                    return {"data": [{"id": identity, "source": {"type": "local", "path": str(root / directory / "server.js")}, "state": {"status": "active"}}
                                     for identity, directory in (("implementation-observer", "observer"), ("workspace-terminal", "terminal"))]}
                if operation == "model.list":
                    return {"data": [{"id": candidate.model, "providerID": candidate.provider, "modelID": candidate.wire_model,
                                      "variants": [{"id": candidate.variant, "settings": {"effort": candidate.effort}}]}]}
                if operation == "agent.get":
                    self.assertEqual(params, {"agentID": "implementer"})
                    return {"data": agent}
                if operation == "session.create":
                    return {"data": {"id": "probe"}}
                if operation == "experimental.session.export":
                    self.assertEqual(params, {"sessionID": "probe"})
                    return {"data": {"info": {"id": "probe"}, "messages": []}}
                return {"data": []}
            with patch.object(runtime, "local_server", server), patch.object(runtime, "api", api):
                result = runtime.audit(root, work, "opencode", {}, expected, candidate)
                self.assertTrue(result["agent"]["native_steps_unlimited"])
                for value in (25, None):
                    agent["steps"] = value
                    with self.assertRaisesRegex(ValueError, "step limit"):
                        runtime.audit(root, work, "opencode", {}, expected, candidate)

    def test_scope_rejects_symlink_and_restores_original_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            work, clean = root / "project", root / "clean"
            grader.materialize(tasks.SMOKE, work)
            outside = root / "private.txt"
            outside.write_text("private")
            (work / "src/escape.py").symlink_to(outside)
            (work / "checks/public.py").write_text("raise SystemExit(0)\n")
            (work / "README.md").write_text("changed configuration")
            collected = grader.collect_patch(tasks.SMOKE, work)
            self.assertFalse(collected["scope_correct"])
            self.assertEqual({v["reason"] for v in collected["violations"]}, {"symlink", "outside_scope"})
            grader.apply_patch(tasks.SMOKE, clean, collected["files"])
            self.assertEqual((clean / "checks/public.py").read_text(), tasks.SMOKE.files["checks/public.py"])
            self.assertFalse((clean / "src/escape.py").exists())
            self.assertEqual(outside.read_text(), "private")

    def test_generated_binary_is_ignored_but_generated_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            grader.materialize(tasks.SMOKE, work)
            (work / "src/__pycache__").mkdir()
            (work / "src/__pycache__/x.pyc").write_bytes(b"\xff\xfe")
            self.assertTrue(grader.collect_patch(tasks.SMOKE, work)["scope_correct"])
            (work / ".build").symlink_to("/tmp", target_is_directory=True)
            self.assertFalse(grader.collect_patch(tasks.SMOKE, work)["scope_correct"])

    def test_trusted_smoke_reference_passes_baseline_fails_new_behavior(self):
        result = grader.validate_task(tasks.SMOKE)
        self.assertTrue(result["valid"])
        self.assertTrue(result["baseline"]["regression"]["passed"])
        self.assertFalse(result["baseline"]["acceptance"]["passed"])
        self.assertTrue(result["reference"]["acceptance"]["passed"])

    def test_early_exit_zero_does_not_pass_a_check_in_either_language(self):
        exiting = replace(tasks.SMOKE, reference={"src/numbers.py": "import os\nos._exit(0)\n"})
        result = grader.validate_task(exiting)
        self.assertFalse(result["valid"])
        self.assertFalse(result["reference"]["regression"]["check_completed"])
        self.assertFalse(result["reference"]["acceptance"]["passed"])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for body in ("process.exit(0);\n", "module.exports = new Promise(resolve => setTimeout(() => process.exit(0), 10));\n", "module.exports = new Promise(() => {});\n"):
                (root / "check.cjs").write_text(body)
                argv, marker = grader.check_runner(["node", "check.cjs"], root, "typescript", "acceptance")
                checked = grader.require_completion(grader.run_local(argv, root), marker)
                self.assertFalse(checked["passed"])
                self.assertFalse(checked["check_completed"])
            (root / "check.cjs").write_text("module.exports = new Promise(resolve => setTimeout(() => { require('node:assert/strict').equal(2+2, 4); resolve(); }, 10));\n")
            argv, marker = grader.check_runner(["node", "check.cjs"], root, "typescript", "acceptance")
            self.assertTrue(grader.require_completion(grader.run_local(argv, root), marker)["passed"])

    def test_oauth_reservation_covers_last_full_block_and_short_budget_phase(self):
        self.assertEqual(bench.oauth_window(21600, 6, Budget(1200, 60), 216), 39690)
        self.assertEqual(bench.oauth_window(21600, 6, Budget(20, 2), 6), 11010)

    def test_non_200_and_incomplete_are_not_accepted(self):
        control = {"reason": None, "exit_code": 0}
        parsed = {"session_completed": True, "error_events": []}
        grade = {"scope": {"scope_correct": True}}
        observation = {"non_200_requests": 0, "incomplete_requests": 0}
        self.assertEqual(bench.operational_status(control, parsed, observation, grade, []), "completed")
        self.assertEqual(bench.operational_status(control, parsed, {**observation, "non_200_requests": 1}, grade, []), "integration_error")
        self.assertEqual(bench.operational_status(control, parsed, {**observation, "incomplete_requests": 1}, grade, []), "integration_error")
        self.assertEqual(bench.operational_status({**control, "reason": "calls"}, parsed, observation, grade, [{"code": "stream_cancelled"}]), "budget_exceeded")

    def test_error_codes_survive_observation_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "observation.jsonl"
            common = {"call_id": "call-1", "session_id": "session-1", "identity": CANDIDATES[0].identity,
                      "transport": "http", "url": "http://127.0.0.1:8317/v1/messages", "agent": "implementer", "kind": "primary"}
            events = [{**common, "event": "request", "at_ms": 10, "request": {"model": CANDIDATES[0].wire_model}},
                      {**common, "event": "error", "at_ms": 20, "error": "provider_failure", "provider_code": "invalid_request_error", "provider_type": "request_error", "status": 400},
                      {**common, "event": "error", "at_ms": 21, "error": "stream_cancelled", "status": 400},
                      {**common, "event": "end", "at_ms": 22, "status": 400}]
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            result = runtime.read_requests(path)[0]
            self.assertEqual(result["errors"][0]["provider_code"], "invalid_request_error")
            self.assertEqual(result["errors"][1]["code"], "stream_cancelled")

    def test_fast_selection_does_not_confirm_default_tier(self):
        candidate = next(c for c in CANDIDATES if c.id == "sol-fast-medium")
        request = {"session_id": "session-1", "request": {"model": candidate.wire_model, "reasoning_effort": candidate.effort, "service_tier": "priority"},
                   "identity": candidate.identity, "agent": "implementer", "kind": "primary", "url": candidate.upstream + "/responses", "transport": "websocket", "status": 200,
                   "complete": True, "responses": [{"event_type": "response.completed", "service_tier": "default"}]}
        observed = runtime.verify_requests(candidate, [request], "session-1")
        self.assertEqual(observed["fast_served"], "not_confirmed")
        self.assertEqual(observed["terminal_served_tiers"], ["default"])

    def test_partial_json_line_is_not_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "log"
            path.write_text('{"event":"request"}\n{"event":"reque')
            self.assertEqual(controller.complete_lines(path), [{"event": "request"}])

    def test_budget_calls_and_time_trigger_external_interrupt(self):
        self.assertEqual(controller.limit_reason(5, 2, Budget(20, 2)), "calls")
        self.assertEqual(controller.limit_reason(20, 0, Budget(20, 2)), "time")
        self.assertIsNone(controller.limit_reason(19, 1, Budget(20, 2)))
        candidate = CANDIDATES[0]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            work = root / "project"
            work.mkdir()
            (root / "request.txt").write_text("Read the project.")
            (root / "observations.jsonl").write_text(json.dumps({"event": "request", "session_id": "session-1"}) + "\n")
            @contextmanager
            def server(*_):
                yield {"url": "http://127.0.0.1:1", "env": {}}
            calls = []
            def api(binary, work, server, operation, params=None, data=None, timeout=45):
                calls.append((operation, params, data))
                if operation == "session.create":
                    return {"data": {"id": "session-1"}}
                if operation == "session.interrupt":
                    return {"interrupted": True}
                if operation == "experimental.session.export":
                    return {"data": {"info": {}, "messages": []}}
                raise ValueError(f"OpenCode {operation} failed: Operation not found")
            process = Mock()
            process.poll.side_effect = [None, 0]
            process.returncode = 0
            container = Mock()
            with patch.object(runtime, "local_server", server), patch.object(runtime, "api", api), patch.object(controller.subprocess, "Popen", return_value=process):
                result, _ = controller.invoke(candidate, work, root, "opencode", {}, container, Budget(20, 1))
            self.assertEqual([c[0] for c in calls], ["session.create", "session.interrupt", "experimental.session.export"])
            self.assertEqual(calls[1][1], {"sessionID": "session-1"})
            self.assertEqual(calls[0][2]["model"], candidate.identity)
            self.assertEqual(result["reason"], "calls")
            self.assertTrue(result["interrupt"]["interrupted"])
            self.assertEqual(json.loads((root / "control.json").read_text())["interrupt"], {"interrupted": True})
            container.stop.assert_called_once()
            process.wait.assert_called_once_with(timeout=15)

    def test_completed_process_cannot_bypass_final_time_or_call_budget(self):
        candidate = CANDIDATES[0]
        for elapsed, count, expected in ((21, 1, "time"), (1, 3, "calls")):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as folder:
                root = Path(folder).resolve()
                work = root / "project"
                work.mkdir()
                (root / "request.txt").write_text("Read the project.")
                (root / "observations.jsonl").write_text((json.dumps({"event": "request", "session_id": "session-1"}) + "\n") * count)
                @contextmanager
                def server(*_):
                    yield {"url": "http://127.0.0.1:1", "env": {}}
                def api(binary, work, server, operation, params=None, data=None, timeout=45):
                    return {"data": {"id": "session-1"}} if operation == "session.create" else {"data": {"info": {}, "messages": []}}
                process = Mock()
                process.poll.return_value = 0
                process.returncode = 0
                with patch.object(runtime, "local_server", server), patch.object(runtime, "api", api), patch.object(controller.subprocess, "Popen", return_value=process), patch.object(controller.time, "monotonic", side_effect=[0, elapsed, elapsed]):
                    result, _ = controller.invoke(candidate, work, root, "opencode", {}, Mock(), Budget(20, 2))
                self.assertEqual(result["reason"], expected)
                self.assertTrue(result["late_limit_detected"])
                self.assertIsNone(result["interrupt"])

    def test_failed_export_keeps_interrupt_control_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            work = root / "project"
            work.mkdir()
            (root / "request.txt").write_text("Read the project.")
            (root / "observations.jsonl").write_text('{"event":"request","session_id":"session-1"}\n')
            @contextmanager
            def server(*_):
                yield {"url": "http://127.0.0.1:1", "env": {}}
            def api(binary, work, server, operation, params=None, data=None, timeout=45):
                if operation == "session.create":
                    return {"data": {"id": "session-1"}}
                if operation == "session.interrupt":
                    return {"interrupted": True}
                self.assertEqual(operation, "experimental.session.export")
                raise ValueError("export failed")
            process = Mock()
            process.poll.side_effect = [None, 0]
            process.returncode = 0
            with patch.object(runtime, "local_server", server), patch.object(runtime, "api", api), patch.object(controller.subprocess, "Popen", return_value=process):
                with self.assertRaisesRegex(ValueError, "export failed"):
                    controller.invoke(CANDIDATES[0], work, root, "opencode", {}, Mock(), Budget(20, 1))
            saved = json.loads((root / "control.json").read_text())
            self.assertEqual(saved["reason"], "calls")
            self.assertEqual(saved["interrupt"], {"interrupted": True})
            self.assertTrue(saved["container_stopped"])

    def test_api_failure_reports_stderr_without_private_password(self):
        outcome = {"timeout": False, "exit_code": 1, "stdout": "", "stderr": "Operation not found: session.export private-password"}
        with patch.object(runtime, "command", return_value=outcome):
            with self.assertRaises(ValueError) as raised:
                runtime.api("opencode", Path("/project"), {"url": "http://127.0.0.1:1", "env": {"OPENCODE_PASSWORD": "private-password"}}, "session.export")
        self.assertIn("Operation not found", str(raised.exception))
        self.assertNotIn("private-password", str(raised.exception))

    def test_frozen_inventory_drives_historical_report_and_gate_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            frozen = {"phase": "smoke", "tool_surface": "isolated_terminal_only", "candidates": [runtime.public_candidate(CANDIDATES[0])],
                      "tasks": [{"id": "smoke"}], "schedule": [{"id": "trial-0001", "candidate": CANDIDATES[0].id, "task": "smoke", "rep": 1}],
                      "source_hashes": {}, "catalog_sha256": "hash", "image_spec": {"image_id": "sha256:image"}}
            runtime.save(root / "freeze.json", frozen)
            (root / "trials/trial-0001").mkdir(parents=True)
            runtime.save(root / "trials/trial-0001/result.json", {**frozen["schedule"][0], "accepted": True, "status": "completed", "session_completed": True, "patch_correct": True, "task_wall_s": 3, "request_count": 4})
            with patch.object(bench, "CANDIDATES", ()):
                observed = bench.report(root)
            self.assertEqual(observed["by_candidate"][CANDIDATES[0].id]["accepted"], 1)
            self.assertEqual(observed["model_calls"], 4)
            self.assertTrue(observed["gate_passed"])
            self.assertIsNone(observed["automatic_winner"])
            bench.require_gate(root, "smoke", frozen)
            with self.assertRaisesRegex(ValueError, "image"):
                bench.require_gate(root, "smoke", {**frozen, "image_spec": {"image_id": "sha256:other"}})


if __name__ == "__main__":
    unittest.main()
