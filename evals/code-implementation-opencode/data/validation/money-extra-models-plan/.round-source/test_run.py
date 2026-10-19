import argparse
from contextlib import redirect_stdout
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
spec = importlib.util.spec_from_file_location("money_extra_round", ROUND / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class MoneyExtraRoundTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="money-extra-models-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

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
                              capture_output=True, text=True, timeout=60)

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

    def test_cli_plan_fixes_three_three_nine_with_exact_routes_and_image(self):
        out = self.root / "plan"
        completed = self.cli("plan", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        frozen = runner.read_json(out / "round-freeze.json")
        self.assertEqual([len(phase["schedule"]) for phase in frozen["phases"]], [3, 3, 9])
        self.assertEqual(runner.read_json(out / "round-summary.json")["model_calls"], 0)
        candidates = frozen["candidates"]
        self.assertEqual([(item["id"], item["selection"], item["effort"], item["fast"], item["protocol"], item["auth_type"]) for item in candidates],
                         [("sol-fast-low", "openai/gpt-6.1-sol-fast#low", "low", True, "responses", "oauth"),
                          ("glm-flash-high", "opencode-go/glm-5.3-flash#high", "high", False, "chat", "key"),
                          ("glm-flash-max", "opencode-go/glm-5.3-flash#max", "max", False, "chat", "key")])
        self.assertEqual([item["upstream"] for item in candidates],
                         ["https://chatgpt.com/backend-api/codex", "https://opencode.ai/zen/go/v1", "https://opencode.ai/zen/go/v1"])
        for phase in frozen["phases"]:
            spec = runner.read_json(out / phase["phase"] / "freeze.json")
            self.assertEqual(spec["image_spec"]["tag"], frozen["image_id"])
            self.assertEqual(spec["source_hashes"]["contract.py"], frozen["provenance"]["source_hashes"]["contract.py"])
            self.assertEqual(spec["budget"], {"seconds": 20 if phase["phase"] == "budget" else 1200,
                                            "calls": 2 if phase["phase"] == "budget" else 60, "grace": 15})

    def test_task_spec_is_integrally_equal_to_previous_corrected_runner(self):
        previous_spec = importlib.util.spec_from_file_location("original_corrected_money", PACKAGE / "rounds/money-contract-v2/run.py")
        previous = importlib.util.module_from_spec(previous_spec)
        previous_spec.loader.exec_module(previous)
        previous_task = runner.normalized(asdict(previous.load_context().task))
        context = runner.load_context()
        self.assertEqual(context.phases["screening"]["tasks"], [previous_task])
        with runner.harness_modules(context.round_dir / "harness") as (bench, _):
            self.assertEqual(bench.tasks.REQUEST, (PACKAGE / "rounds/money-contract-v2/request.txt").read_text().strip())

    def test_cli_validate_runs_real_baseline_and_reference_with_zero_models(self):
        out = self.root / "validate"
        completed = self.cli("validate", out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        validation = runner.read_json(out / "screening/validation.json")
        self.assertEqual(validation["model_calls"], 0)
        money = validation["tasks"][0]
        self.assertTrue(money["baseline"]["compilation"]["passed"])
        self.assertTrue(money["baseline"]["regression"]["passed"])
        self.assertFalse(money["baseline"]["acceptance"]["passed"])
        self.assertTrue(all(item["passed"] for item in money["reference"].values()))

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
        self.assertEqual(summary["planned"], 15)
        self.assertEqual(summary["model_calls"], 15)
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
        self.assertEqual(summary["phases"][1]["summary"]["started"], 2)
        self.assertIsNone(summary["phases"][2]["summary"])

    def test_incomplete_screening_is_an_error_despite_zero_process_exit(self):
        context = self.fixture()
        process, _ = self.phase_process(context, incomplete="screening")
        self.assertEqual(self.execute(self.args(), context, process), 1)
        summary = runner.read_json(self.root / "output/round-summary.json")
        self.assertEqual(summary["phases"][2]["summary"]["started"], 8)

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
