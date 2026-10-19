import argparse
from contextlib import nullcontext, redirect_stdout
from copy import deepcopy
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
spec = importlib.util.spec_from_file_location("implementer_rest_tests", ROUND / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RemainingScreeningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="implementer-rest-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.context = runner.load_context()

    def args(self, command="run", origin=None, out=None):
        return argparse.Namespace(command=command, money_run=origin or self.root / "money",
                                  out=out or self.root / "out", binary="opencode", docker="docker")

    def origin(self, incomplete=False, rejected=False):
        context = self.context.money_context
        origin = self.root / "money"
        origin.mkdir()
        names = (*self.context.money.WRAPPER_FILES, "provenance.json")
        snapshot = origin / ".round-source"
        snapshot.mkdir()
        for name in names:
            shutil.copyfile(context.round_dir / name, snapshot / name)
        frozen = {"schema": 1, "round": "money-sol-low-glm-flash", "command": "run",
                  "source_hashes": {name: runner.digest(context.round_dir / name) for name in names},
                  "provenance": context.provenance, "candidates": context.candidates,
                  "phases": [context.phases[phase] for phase in self.context.money.PHASES],
                  "commands": {}}
        runner.save(origin / "round-freeze.json", frozen)
        with self.context.money.harness_modules(context.round_dir / "harness") as (bench, domain):
            for phase in self.context.money.PHASES:
                folder = origin / phase
                folder.mkdir()
                options = runner.core_args(self.args(), self.context)
                definition = context.phases[phase]
                options.phase, options.reps = phase, definition["reps"]
                budget = domain.Budget(**definition["budget"])
                phase_freeze = bench.freeze(folder, options, bench.tasks.inventory(phase), domain.CANDIDATES, budget)
                phase_freeze["image_spec"].update(image_id=self.context.baseline["image_spec"]["image_id"], engine_endpoint="fixture")
                runner.save(folder / "freeze.json", phase_freeze)
                runner.save(folder / "preflight.json", {"status": "passed", "namespace_validated": True})
                rows = phase_freeze["schedule"][:-1] if phase == "screening" and incomplete else phase_freeze["schedule"]
                for index, row in enumerate(rows):
                    good = not (rejected and phase == "screening" and index == 0)
                    result = {**row, "status": "budget_exceeded" if phase == "budget" else "completed",
                              "proof_passed": phase == "budget", "accepted": phase != "budget" and good,
                              "session_completed": phase != "budget", "patch_correct": phase != "budget" and good,
                              "request_count": 1, "task_wall_s": 1.0}
                    destination = folder / "trials" / row["id"]
                    destination.mkdir(parents=True)
                    runner.save(destination / "result.json", result)
        return origin

    def file_hashes(self, path):
        return {str(file.relative_to(path)): runner.digest(file) for file in path.rglob("*") if file.is_file()}

    def execute(self, args):
        with redirect_stdout(io.StringIO()):
            return runner.execute(args, self.context)

    def planned(self):
        origin = self.origin(rejected=True)
        args = self.args("plan", origin)
        self.assertEqual(self.execute(args), 0)
        frozen = runner.read_json(args.out / "freeze.json")
        options = runner.core_args(args, self.context)
        options.out, options.money_run, options.command = args.out, origin, "run"
        extension = runner.read_json(args.out / "round-freeze.json")
        extension["money_origin_hashes"] = runner.inspect_origin(origin, self.context, complete=True)
        runner.save(args.out / "round-freeze.json", extension)
        runner.copy_gates(options, self.context, extension)
        frozen["image_spec"].update(image_id=self.context.baseline["image_spec"]["image_id"], engine_endpoint="fixture")
        runner.save(args.out / "freeze.json", frozen)
        return options, frozen, extension

    def test_real_cli_plan_is_99_exact_cases_routes_and_no_money(self):
        origin = PACKAGE / "results/money-sol-low-glm-flash"
        out = self.root / "cli-plan"
        result = subprocess.run([sys.executable, "-B", str(ROUND / "run.py"), "plan",
                                 "--money-run", str(origin), "--out", str(out)], capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        frozen = runner.read_json(out / "freeze.json")
        self.assertEqual(len(frozen["schedule"]), 99)
        self.assertEqual(len(frozen["tasks"]), 11)
        self.assertEqual(frozen["tasks"], self.context.tasks)
        self.assertNotIn("py-money-contract", {row["task"] for row in frozen["schedule"]})
        self.assertIn("ts-money-consolidation", {row["task"] for row in frozen["schedule"]})
        self.assertEqual([(row["id"], row["selection"]) for row in frozen["candidates"]],
                         [("sol-fast-low", "openai/gpt-6.1-sol-fast#low"),
                          ("glm-flash-high", "opencode-go/glm-5.3-flash#high"),
                          ("glm-flash-max", "opencode-go/glm-5.3-flash#max")])
        self.assertEqual(frozen["source_hashes"], self.context.money_context.provenance["source_hashes"])
        self.assertEqual(frozen["budget"], {"seconds": 1200, "calls": 60, "grace": 15})
        self.assertEqual(runner.read_json(out / "summary.json")["model_calls"], 0)

    def test_real_cli_validate_all_baselines_and_references_without_models(self):
        origin = PACKAGE / "results/money-sol-low-glm-flash"
        out = self.root / "cli-validate"
        result = subprocess.run([sys.executable, "-B", str(ROUND / "run.py"), "validate",
                                 "--money-run", str(origin), "--out", str(out)], capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        validated = runner.read_json(out / "validation.json")
        self.assertEqual(validated["status"], "passed")
        self.assertEqual(validated["model_calls"], 0)
        self.assertEqual(len(validated["tasks"]), 11)
        self.assertTrue(all(row["valid"] for row in validated["tasks"]))

    def test_run_blocks_incomplete_origin_before_output_or_calls(self):
        origin = self.origin(incomplete=True)
        args = self.args(origin=origin)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.execute(args)
        self.assertFalse(args.out.exists())

    def test_complete_but_rejected_money_is_valid(self):
        origin = self.origin(rejected=True)
        hashes = runner.inspect_origin(origin, self.context, complete=True)
        self.assertEqual(sum(key.startswith("screening/trials/") for key in hashes), 9)

    def test_origin_image_catalog_source_cohort_and_gates_fail_closed(self):
        for label, file, mutate, message in (
                ("image", "smoke/freeze.json", lambda value: value["image_spec"].update(image_id="different"), "image"),
                ("catalog", "smoke/freeze.json", lambda value: value.update(catalog_sha256="different"), "catalog"),
                ("source", "smoke/freeze.json", lambda value: value["source_hashes"].update(**{"runtime.py": "different"}), "source"),
                ("cohort", "smoke/freeze.json", lambda value: value["candidates"][0].update(effort="high"), "cohort"),
                ("budget", "budget/trials/trial-0001/result.json", lambda value: value.update(proof_passed=False), "budget gate"),
                ("smoke", "smoke/trials/trial-0001/result.json", lambda value: value.update(accepted=False), "smoke gate"),
                ("infra", "screening/trials/trial-0001/result.json", lambda value: value.update(status="infra_error"), "infrastructure")):
            with self.subTest(label=label):
                origin = self.origin()
                path = origin / file
                value = runner.read_json(path)
                mutate(value)
                runner.save(path, value)
                with self.assertRaisesRegex(ValueError, message):
                    runner.inspect_origin(origin, self.context, complete=True)
                shutil.rmtree(origin)

    def test_real_require_gate_only_writes_copies_and_source_unchanged(self):
        args, frozen, extension = self.planned()
        before = self.file_hashes(args.money_run)
        with self.context.money.harness_modules(self.context.money_context.round_dir / "harness") as (bench, _):
            for phase in ("budget", "smoke"):
                bench.require_gate(args.out / "gate-proofs" / phase, phase, frozen)
        self.assertEqual(before, self.file_hashes(args.money_run))
        runner.guard(args, self.context, extension)
        for key in ("source_hashes", "catalog_sha256", "candidates"):
            changed = deepcopy(frozen)
            changed[key] = {} if key == "source_hashes" else "wrong" if key == "catalog_sha256" else [{**frozen["candidates"][0], "effort": "high"}]
            with self.context.money.harness_modules(self.context.money_context.round_dir / "harness") as (bench, _):
                with self.assertRaises(ValueError):
                    bench.require_gate(args.out / "gate-proofs/budget", "budget", changed)

    def test_guard_blocks_origin_copy_and_agenda_drift(self):
        args, frozen, extension = self.planned()
        for path, message in ((args.money_run / "screening/trials/trial-0001/result.json", "origin evidence"),
                              (args.out / "gate-proofs/budget/trials/trial-0001/result.json", "Private gate"),
                              (args.out / "round-freeze.json", "freeze changed")):
            original = path.read_bytes()
            if path.name == "round-freeze.json":
                changed = runner.read_json(path)
                changed["reps"] = 4
                runner.save(path, changed)
            else:
                path.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ValueError, message):
                runner.guard(args, self.context, extension)
            path.write_bytes(original)

    def test_preflight_blocks_with_zero_calls_and_preserves_origin(self):
        origin = self.origin(rejected=True)
        before = self.file_hashes(origin)
        with self.context.money.harness_modules(self.context.money_context.round_dir / "harness") as (bench, domain):
            with patch.object(self.context.money, "harness_modules", return_value=nullcontext((bench, domain))), \
                    patch.object(bench, "preflight", return_value={"status": "blocked", "error": "fixture isolation failure"}), \
                    patch.object(bench, "run_trial") as model:
                self.assertEqual(self.execute(self.args(origin=origin)), 1)
                model.assert_not_called()
        self.assertEqual(before, self.file_hashes(origin))
        self.assertEqual(runner.read_json(self.root / "out/summary.json")["started"], 0)

    def test_preflight_cannot_change_limits_before_first_model_call(self):
        origin = self.origin()
        def changed(out, options, selected, candidates):
            frozen = runner.read_json(out / "freeze.json")
            frozen["budget"]["calls"] = 61
            frozen["image_spec"]["image_id"] = self.context.baseline["image_spec"]["image_id"]
            runner.save(out / "freeze.json", frozen)
            return {"status": "passed"}
        with self.context.money.harness_modules(self.context.money_context.round_dir / "harness") as (bench, domain):
            with patch.object(self.context.money, "harness_modules", return_value=nullcontext((bench, domain))), \
                    patch.object(bench, "preflight", side_effect=changed), \
                    patch.object(bench, "run_trial") as model:
                with self.assertRaisesRegex(ValueError, "limits changed"):
                    self.execute(self.args(origin=origin))
                model.assert_not_called()
        self.assertEqual(runner.read_json(self.root / "out/summary.json")["started"], 0)

    def test_adapter_source_seal_rejects_drift(self):
        copied = self.root / "round"
        copied.mkdir()
        for name in (*runner.WRAPPER_FILES, "provenance.json"):
            shutil.copyfile(ROUND / name, copied / name)
        context = runner.load_context(copied)
        path = copied / "run.py"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "source differs"):
            runner.load_context(context.round_dir)

    def fake_loop(self, stop=None, drift=False, ticks=None, oauth_error=False):
        args, frozen, extension = self.planned()
        with self.context.money.harness_modules(self.context.money_context.round_dir / "harness") as (bench, domain):
            python = importlib.import_module("tasks_python")
            typescript = importlib.import_module("tasks_typescript")
            selected = tuple(task for task in (*python.TASKS, *typescript.TASKS)
                             if task.phase == "screening" and task.id != "py-money-contract")
            calls = []
            reports = []
            real_report = runner.report
            def trial(row, out, options, core_freeze, candidate, task, budget):
                calls.append(row)
                self.assertEqual(core_freeze, frozen)
                self.assertEqual(budget, domain.Budget(1200, 60, 15))
                value = {**row, "status": stop or "completed", "accepted": not stop,
                         "session_completed": not stop, "patch_correct": not stop,
                         "request_count": 1, "task_wall_s": 1.0}
                path = out / "trials" / row["id"]
                path.mkdir(parents=True)
                runner.save(path / "result.json", value)
                if drift:
                    source = args.money_run / "screening/trials/trial-0001/result.json"
                    source.write_text(source.read_text() + "\n")
                return value
            def counted_report(core, out):
                reports.append(len(calls))
                return real_report(core, out)
            with patch.object(bench, "run_trial", side_effect=trial), \
                    patch.object(bench.runtime, "validate_oauth_window", side_effect=ValueError("OAuth expired") if oauth_error else None) as oauth, \
                    patch.object(runner, "report", side_effect=counted_report), \
                    patch.object(runner.time, "monotonic", side_effect=ticks) if ticks else patch.object(runner.time, "monotonic", return_value=0), \
                    redirect_stdout(io.StringIO()):
                try:
                    result = runner.run_schedule(bench, args, self.context, frozen, extension,
                                                 domain.CANDIDATES, selected, domain.Budget())
                except ValueError as error:
                    result = error
                return result, calls, reports, oauth.call_args_list, runner.read_json(args.out / "summary.json")

    def test_loop_is_99_with_per_block_oauth_and_incremental_final_reports(self):
        result, calls, reports, oauth, summary = self.fake_loop()
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 99)
        self.assertEqual(len(oauth), 33)
        self.assertEqual(oauth[0].args[2], 3 * (1200 + 15 + 1200))
        self.assertEqual(reports, [*range(1, 100), 99])
        self.assertEqual(summary["started"], 99)

    def test_loop_stops_on_infrastructure_and_scope_with_not_run_visible(self):
        for status in ("infra_error", "scope_violation"):
            with self.subTest(status=status):
                result, calls, reports, _, summary = self.fake_loop(stop=status)
                self.assertEqual(result, 1)
                self.assertEqual(len(calls), 1)
                self.assertEqual(reports, [1, 1])
                self.assertEqual(summary["started"], 1)
                shutil.rmtree(self.root / "money")
                shutil.rmtree(self.root / "out")

    def test_global_stop_and_oauth_failure_have_no_calls_and_final_report(self):
        result, calls, reports, oauth, summary = self.fake_loop(ticks=[0, 21600])
        self.assertEqual(result, 1)
        self.assertFalse(calls)
        self.assertFalse(oauth)
        self.assertEqual(reports, [0])
        self.assertEqual(summary["started"], 0)
        shutil.rmtree(self.root / "money")
        shutil.rmtree(self.root / "out")
        result, calls, reports, _, _ = self.fake_loop(oauth_error=True)
        self.assertIsInstance(result, ValueError)
        self.assertFalse(calls)
        self.assertEqual(reports, [0])

    def test_drift_between_trials_prevents_next_call_and_still_reports(self):
        result, calls, reports, _, summary = self.fake_loop(drift=True)
        self.assertIsInstance(result, ValueError)
        self.assertEqual(len(calls), 1)
        self.assertEqual(reports, [1, 1])
        self.assertEqual(summary["started"], 1)

    def test_output_must_be_new_and_outside_origin(self):
        origin = self.origin()
        out = self.root / "out"
        out.mkdir()
        marker = out / "marker"
        marker.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "Output must be new"):
            self.execute(self.args(origin=origin))
        self.assertEqual(marker.read_text(), "preserve")
        for overlap in (origin, origin / "nested", origin.parent):
            with self.assertRaisesRegex(ValueError, "outside"):
                self.execute(self.args(origin=origin, out=overlap))


if __name__ == "__main__":
    unittest.main()
