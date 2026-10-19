import argparse
import ast
from contextlib import contextmanager, redirect_stdout
from dataclasses import asdict
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROUND = Path(__file__).resolve().parent
PACKAGE = ROUND.parents[1]
spec = importlib.util.spec_from_file_location("haiku_55_round", ROUND / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class HaikuRoundTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="haiku-55-models-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def fixture(self):
        round_dir = self.root / "round"
        shutil.copytree(ROUND, round_dir, ignore=shutil.ignore_patterns("__pycache__"))
        return runner.load_context(round_dir)

    def args(self, out=None, command="run", phase="all"):
        return argparse.Namespace(command=command, out=out or self.root / "output", phase=phase,
                                  binary="opencode", docker="docker")

    def execute(self, args, context, process=None):
        with redirect_stdout(io.StringIO()):
            return runner.execute(args, context, process)

    def cli(self, command, out):
        return subprocess.run([sys.executable, "-B", str(ROUND / "run.py"), command, "--out", str(out)],
                              capture_output=True, text=True, timeout=120)

    def phase_process(self, context, failed=None, incomplete=None, status=None, mutate=None):
        calls = []
        def process(command, **kwargs):
            phase = command[command.index("--phase") + 1]
            calls.append(phase)
            plan = command.copy()
            plan[3] = "plan"
            completed = subprocess.run(plan, capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            out = Path(command[command.index("--out") + 1])
            frozen = runner.read_json(out / "freeze.json")
            frozen["image_spec"]["image_id"] = context.baseline["image_spec"]["image_id"]
            runner.save(out / "freeze.json", frozen)
            rows = frozen["schedule"][:-1] if phase == incomplete else frozen["schedule"]
            for index, row in enumerate(rows):
                good = not (phase == failed and index == 0)
                result = {**row, "status": status if index == 0 and status else "budget_exceeded" if phase == "budget" else "completed",
                          "accepted": good and phase != "budget", "proof_passed": good and phase == "budget",
                          "session_completed": phase != "budget", "patch_correct": good and phase != "budget",
                          "task_wall_s": 1.0, "request_count": 1}
                destination = out / "trials" / row["id"]
                destination.mkdir(parents=True)
                runner.save(destination / "result.json", result)
            if mutate:
                mutate(phase, out)
            return SimpleNamespace(returncode=0)
        return process, calls

    def test_cli_plan_fixes_five_five_180_with_exact_routes_and_image(self):
        out = self.root / "plan"
        completed = self.cli("plan", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        frozen = runner.read_json(out / "round-freeze.json")
        self.assertEqual([len(phase["schedule"]) for phase in frozen["phases"]], [5, 5, 180])
        self.assertEqual(runner.read_json(out / "round-summary.json")["model_calls"], 0)
        candidates = frozen["candidates"]
        self.assertEqual([(item["id"], item["selection"], item["wire_model"], item["effort"], item["fast"],
                           item["protocol"], item["auth_type"], item["credential_provider"], item["upstream"])
                          for item in candidates],
                         [(f"haiku-{effort}", f"cli_proxy/cpa-claude-haiku-5-5#{effort}", "claude-haiku-5-5", effort,
                           False, "messages", "key", "cli_proxy", "http://127.0.0.1:8317/v1")
                          for effort in ("low", "medium", "high", "xhigh", "max")])
        for phase in frozen["phases"]:
            spec = runner.read_json(out / phase["phase"] / "freeze.json")
            report = (out / phase["phase"] / "report.md").read_text()
            self.assertIn("As 5 configurações usam somente o terminal isolado.", report)
            self.assertNotIn("As seis configurações", report)
            self.assertEqual(spec["image_spec"]["tag"], frozen["image_id"])
            self.assertEqual(spec["source_hashes"], frozen["provenance"]["source_hashes"])
            self.assertEqual(spec["budget"], {"seconds": 20 if phase["phase"] == "budget" else 1200,
                                            "calls": 2 if phase["phase"] == "budget" else 60, "grace": 15})
            self.assertEqual(spec["seed"], 20261010)
            self.assertEqual(spec["global_seconds"], 21600)
            schedule = spec["schedule"]
            self.assertEqual(len({(row["task"], row["rep"], row["candidate"]) for row in schedule}), len(schedule))
            for block in {row["block"] for row in schedule}:
                self.assertEqual({row["candidate"] for row in schedule if row["block"] == block},
                                 {item["id"] for item in candidates})
        screening = runner.read_json(out / "screening/freeze.json")
        self.assertEqual({row["rep"] for row in screening["schedule"]}, {1, 2, 3})
        for candidate in candidates:
            self.assertEqual(sum(row["candidate"] == candidate["id"] for row in screening["schedule"]), 36)

    def test_full_task_specs_equal_original_eleven_and_corrected_money(self):
        context = runner.load_context()
        corrected = runner.read_json(PACKAGE / "results/money-contract-v2/freeze.json")["tasks"][0]
        expected = [corrected if task["id"] == "py-money-contract" else task
                    for task in context.baseline["tasks"]]
        self.assertEqual(context.phases["screening"]["tasks"], expected)
        self.assertEqual(len(expected), 12)
        self.assertIn("ts-money-consolidation", {task["id"] for task in expected})
        self.assertIn("py-money-contract-v2", {task["id"] for task in expected})
        self.assertNotIn("py-money-contract", {task["id"] for task in expected})
        with runner.harness_modules(context.round_dir / "harness") as (bench, _):
            monetary = next(task for task in bench.tasks.inventory("screening") if task.id == "py-money-contract-v2")
            self.assertEqual(runner.normalized(asdict(monetary)), corrected)
            self.assertEqual(bench.tasks.REQUEST, (PACKAGE / "rounds/money-contract-v2/request.txt").read_text().strip())

    def test_cli_report_retains_full_plan_with_zero_model_calls(self):
        out = self.root / "planned-report"
        completed = self.cli("plan", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        completed = self.cli("report", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["planned"], 190)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual([item["summary"]["planned"] for item in report["phases"]], [5, 5, 180])

    def test_cli_validate_runs_real_twelve_baselines_and_references_with_zero_models(self):
        out = self.root / "validate"
        completed = self.cli("validate", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        validation = runner.read_json(out / "screening/validation.json")
        self.assertEqual(validation["model_calls"], 0)
        self.assertEqual(len(validation["tasks"]), 12)
        self.assertTrue(all(item["valid"] for item in validation["tasks"]))
        for task in validation["tasks"]:
            self.assertTrue(task["baseline"]["compilation"]["passed"])
            self.assertTrue(task["baseline"]["regression"]["passed"])
            self.assertFalse(task["baseline"]["acceptance"]["passed"] and task["baseline"]["structural"]["passed"])
            self.assertTrue(all(item["passed"] for item in task["reference"].values()))

    def test_tampered_contract_and_core_are_blocked_before_launch(self):
        for name in ("contract.py", "runtime.py"):
            with self.subTest(name=name):
                context = self.fixture()
                path = context.round_dir / "harness" / name
                path.write_text(path.read_text() + "\nraise RuntimeError('must not execute')\n")
                with patch.object(runner.subprocess, "run") as process:
                    with self.assertRaisesRegex(ValueError, "harness source"):
                        self.execute(self.args(out=self.root / name), context)
                    process.assert_not_called()
                shutil.rmtree(context.round_dir)

    def test_runtime_changes_only_the_explicit_five_variants(self):
        context = runner.load_context()
        original = ast.parse((context.baseline_path / ".frozen-source/runtime.py").read_text())
        current = ast.parse((context.round_dir / "harness/runtime.py").read_text())
        before = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == "configuration")
        original.body.remove(before)
        current.body.remove(next(node for node in current.body if isinstance(node, ast.FunctionDef) and node.name == "configuration"))
        self.assertEqual(ast.dump(current), ast.dump(original))
        with runner.harness_modules(context.round_dir / "harness") as (bench, domain):
            namespace = {"AGENT": bench.runtime.AGENT, "SYSTEM": bench.runtime.SYSTEM}
            exec(compile(ast.Module(body=[before], type_ignores=[]), "baseline-configuration", "exec"), namespace)
            for candidate in domain.CANDIDATES:
                expected = namespace["configuration"](candidate, Path("/private/observer"), Path("/private/terminal"))
                observed = bench.runtime.configuration(candidate, Path("/private/observer"), Path("/private/terminal"))
                model = observed["providers"][candidate.provider]["models"][candidate.model]
                self.assertEqual(model.pop("variants"),
                                 [{"id": effort, "settings": {"effort": effort}}
                                  for effort in ("low", "medium", "high", "xhigh", "max")])
                self.assertEqual(observed, expected)

    def test_resealed_runtime_controller_changes_are_still_rejected(self):
        context = self.fixture()
        path = context.round_dir / "harness/runtime.py"
        path.write_text(path.read_text().replace('requested.get("thinking_type") != "adaptive"', "False"))
        provenance = runner.read_json(context.round_dir / "provenance.json")
        provenance["source_hashes"]["runtime.py"] = runner.digest(path)
        runner.save(context.round_dir / "provenance.json", provenance)
        with self.assertRaisesRegex(ValueError, "variant registration"):
            runner.load_context(context.round_dir)

    def test_native_audit_requires_each_selected_effort_and_wire_model(self):
        context = runner.load_context()
        with runner.harness_modules(context.round_dir / "harness") as (bench, domain):
            runtime = bench.runtime
            for candidate in domain.CANDIDATES:
                with self.subTest(effort=candidate.effort):
                    root = self.root / candidate.id
                    root.mkdir()
                    work = root / "project"
                    work.mkdir()
                    expected = runtime.configuration(candidate, root / "observer", root / "terminal")
                    (root / "observations.jsonl").write_text('{"event":"ready"}\n')
                    (root / "terminal.jsonl").write_text('{"event":"ready","tools":[{"id":"terminal","name":"terminal"}]}\n')
                    model = {"id": candidate.model, "providerID": candidate.provider, "modelID": candidate.wire_model,
                             "variants": [{"id": effort, "settings": {"effort": effort}}
                                          for effort in ("low", "medium", "high", "xhigh", "max")]}
                    @contextmanager
                    def server(*_):
                        yield {}
                    def api(binary, work, server, operation, params=None, data=None, timeout=45):
                        if operation == "config.get":
                            return [{"type": "document", "path": str(root / "config/opencode/opencode.json"), "info": expected}]
                        if operation == "plugin.list":
                            return {"data": [{"id": identity, "source": {"type": "local", "path": str(root / directory / "server.js")},
                                              "state": {"status": "active"}}
                                             for identity, directory in (("implementation-observer", "observer"), ("workspace-terminal", "terminal"))]}
                        if operation == "model.list":
                            return {"data": [model]}
                        if operation == "agent.get":
                            return {"data": {"id": "implementer"}}
                        if operation == "session.create":
                            return {"data": {"id": "probe"}}
                        if operation == "experimental.session.export":
                            return {"data": {"info": {"id": "probe"}, "messages": []}}
                        return {"data": []}
                    with patch.object(runtime, "local_server", server), patch.object(runtime, "api", api):
                        observed = runtime.audit(root, work, "opencode", {}, expected, candidate)
                        self.assertEqual(observed["model"],
                                         {"id": candidate.model, "providerID": "cli_proxy", "modelID": "claude-haiku-5-5",
                                          "variant": candidate.variant, "effort": candidate.effort, "fast": False, "auth_type": "key"})
                        variants = model["variants"]
                        model["variants"] = [item for item in variants if item["id"] != candidate.variant]
                        with self.assertRaisesRegex(ValueError, "effort variant"):
                            runtime.audit(root, work, "opencode", {}, expected, candidate)
                        model["variants"] = variants
                        model["modelID"] = "claude-sonnet-5-5"
                        with self.assertRaisesRegex(ValueError, "effort variant"):
                            runtime.audit(root, work, "opencode", {}, expected, candidate)
                        model["modelID"] = candidate.wire_model
                        selected = next(item for item in variants if item["id"] == candidate.variant)
                        selected["settings"]["effort"] = "other"
                        with self.assertRaisesRegex(ValueError, "effort or Fast mode"):
                            runtime.audit(root, work, "opencode", {}, expected, candidate)

    def test_observed_messages_reject_wrong_model_effort_thinking_route_and_session(self):
        context = runner.load_context()
        with runner.harness_modules(context.round_dir / "harness") as (bench, domain):
            for candidate in domain.CANDIDATES:
                record = {"session_id": "session-1", "request": {"model": "claude-haiku-5-5", "reasoning_effort": candidate.effort,
                                                                  "thinking_type": "adaptive"},
                          "identity": candidate.identity, "agent": "implementer", "kind": "primary",
                          "url": "http://127.0.0.1:8317/v1/messages", "status": 200,
                          "responses": [], "complete": True, "transport": "fetch"}
                observed = bench.runtime.verify_requests(candidate, [record], "session-1")
                self.assertTrue(observed["request_settings_verified"])
                self.assertEqual(observed["request_count"], 1)
                for field, value, message in (("model", "claude-sonnet-5-5", "model or reasoning effort"),
                                               ("reasoning_effort", "other", "model or reasoning effort"),
                                               ("thinking_type", "enabled", "adaptive thinking")):
                    altered = runner.normalized(record)
                    altered["request"][field] = value
                    with self.assertRaisesRegex(ValueError, message):
                        bench.runtime.verify_requests(candidate, [altered], "session-1")
                for field, value, message in (("url", "http://127.0.0.1:8317/v1/chat/completions", "provider route"),
                                               ("session_id", "another-session", "single task session"),
                                               ("identity", {**candidate.identity, "variant": "other"}, "session identity")):
                    altered = runner.normalized(record)
                    altered[field] = value
                    with self.assertRaisesRegex(ValueError, message):
                        bench.runtime.verify_requests(candidate, [altered], "session-1")

    def test_wrapper_and_provenance_drift_block_before_any_phase(self):
        for name in ("run.py", "README.md", "test_run.py", "provenance.json"):
            with self.subTest(name=name):
                context = self.fixture()
                path = context.round_dir / name
                if name == "provenance.json":
                    value = runner.read_json(path)
                    value["candidates"][0]["effort"] = "other"
                    runner.save(path, value)
                else:
                    path.write_text(path.read_text() + "\n")
                with patch.object(runner.subprocess, "run") as process:
                    with self.assertRaises(ValueError):
                        self.execute(self.args(out=self.root / name), context)
                    process.assert_not_called()
                shutil.rmtree(context.round_dir)

    def test_round_agenda_drift_stops_before_the_next_phase(self):
        context = self.fixture()
        def mutate(phase, out):
            if phase == "budget":
                path = out.parent / "round-freeze.json"
                value = runner.read_json(path)
                value["phases"][2]["schedule"][0]["candidate"] = "haiku-other"
                runner.save(path, value)
        process, calls = self.phase_process(context, mutate=mutate)
        with self.assertRaisesRegex(ValueError, "agenda or evidence"):
            self.execute(self.args(), context, process)
        self.assertEqual(calls, ["budget"])

    def test_core_freeze_rejects_source_drift_used_before_each_trial(self):
        context = self.fixture()
        out = self.root / "planned"
        self.assertEqual(self.execute(self.args(out, "plan"), context), 0)
        with runner.harness_modules(context.round_dir / "harness") as (bench, _):
            bench.check_freeze(out / "screening")
            path = context.round_dir / "harness/controller.py"
            path.write_text(path.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "source differs"):
                bench.check_freeze(out / "screening")

    def test_original_gates_are_rejected_by_real_core_guard(self):
        context = runner.load_context()
        out = self.root / "planned"
        self.assertEqual(self.execute(self.args(out, "plan"), context), 0)
        frozen = runner.read_json(out / "screening/freeze.json")
        frozen["image_spec"]["image_id"] = context.baseline["image_spec"]["image_id"]
        for phase, directory in (("budget", "budget-r4"), ("smoke", "smoke")):
            original = PACKAGE / "results" / directory
            copied = self.root / directory
            copied.mkdir()
            shutil.copyfile(original / "freeze.json", copied / "freeze.json")
            gate = runner.read_json(copied / "freeze.json")
            for row in gate["schedule"]:
                destination = copied / "trials" / row["id"]
                destination.mkdir(parents=True)
                shutil.copyfile(original / "trials" / row["id"] / "result.json", destination / "result.json")
            with runner.harness_modules(context.round_dir / "harness") as (bench, _):
                with self.assertRaisesRegex(ValueError, "configuration differs"):
                    bench.require_gate(copied, phase, frozen)

    def test_run_accepts_expected_budget_interruptions_and_finishes_all_phases(self):
        context = self.fixture()
        process, calls = self.phase_process(context)
        self.assertEqual(self.execute(self.args(), context, process), 0)
        self.assertEqual(calls, ["budget", "smoke", "screening"])
        summary = runner.read_json(self.root / "output/round-summary.json")
        self.assertEqual(summary["planned"], 190)
        self.assertEqual(summary["model_calls"], 190)
        self.assertTrue(summary["phases"][0]["summary"]["gate_passed"])

    def test_failed_budget_or_smoke_stops_despite_zero_process_exit(self):
        for phase, expected in (("budget", ["budget"]), ("smoke", ["budget", "smoke"])):
            with self.subTest(phase=phase):
                context = self.fixture()
                process, calls = self.phase_process(context, failed=phase)
                with self.assertRaisesRegex(ValueError, f"{phase} gate did not pass"):
                    self.execute(self.args(out=self.root / phase), context, process)
                self.assertEqual(calls, expected)
                shutil.rmtree(context.round_dir)

    def test_incomplete_phase_stops_despite_zero_process_exit(self):
        context = self.fixture()
        process, calls = self.phase_process(context, incomplete="smoke")
        with self.assertRaisesRegex(ValueError, "smoke gate did not pass"):
            self.execute(self.args(), context, process)
        self.assertEqual(calls, ["budget", "smoke"])
        summary = runner.read_json(self.root / "output/round-summary.json")
        self.assertEqual(summary["phases"][1]["summary"]["started"], 4)
        self.assertIsNone(summary["phases"][2]["summary"])

    def test_incomplete_screening_is_an_error_despite_zero_process_exit(self):
        context = self.fixture()
        process, _ = self.phase_process(context, incomplete="screening")
        self.assertEqual(self.execute(self.args(), context, process), 1)
        summary = runner.read_json(self.root / "output/round-summary.json")
        self.assertEqual(summary["phases"][2]["summary"]["started"], 179)

    def test_infrastructure_status_stops_even_with_zero_process_exit(self):
        context = self.fixture()
        process, calls = self.phase_process(context, status="infra_error")
        self.assertEqual(self.execute(self.args(), context, process), 1)
        self.assertEqual(calls, ["budget"])

    def test_changed_source_between_phases_blocks_next_launch(self):
        context = self.fixture()
        def mutate(phase, _):
            if phase == "budget":
                path = context.round_dir / "harness/runtime.py"
                path.write_text(path.read_text() + "\n")
        process, calls = self.phase_process(context, mutate=mutate)
        with self.assertRaisesRegex(ValueError, "harness source"):
            self.execute(self.args(), context, process)
        self.assertEqual(calls, ["budget"])

    def test_existing_output_is_never_overwritten(self):
        context = runner.load_context()
        out = self.root / "existing"
        out.mkdir()
        marker = out / "evidence.txt"
        marker.write_text("preserve me")
        with self.assertRaisesRegex(ValueError, "Output must be new"):
            self.execute(self.args(out), context)
        self.assertEqual(marker.read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()
