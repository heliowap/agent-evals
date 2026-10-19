from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROUND = Path(__file__).resolve().parent
PACKAGE = ROUND.parents[1]
spec = importlib.util.spec_from_file_location("money_contract_rerun", ROUND / "run.py")
rerun = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rerun)


def hashes(folder):
    return {path.relative_to(folder).as_posix(): rerun.digest(path)
            for path in folder.rglob("*") if path.is_file()}


class MoneyContractRerunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="money-contract-rerun-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self, package_name="package"):
        package = self.root / package_name
        round_dir = package / "rounds/money-contract-v2"
        shutil.copytree(ROUND / "harness", round_dir / "harness")
        for name in rerun.REVISION_FILES:
            shutil.copyfile(ROUND / name, round_dir / name)
        baseline = package / "results/screening"
        baseline.mkdir(parents=True)
        for name in ("freeze.json", "models.json"):
            shutil.copyfile(PACKAGE / "results/screening" / name, baseline / name)
        shutil.copytree(PACKAGE / "results/screening/.frozen-source", baseline / ".frozen-source")
        for phase in ("budget-r4", "smoke"):
            source = PACKAGE / "results" / phase
            target = package / "results" / phase
            target.mkdir()
            shutil.copyfile(source / "freeze.json", target / "freeze.json")
            gate = rerun.read_json(source / "freeze.json")
            for row in gate["schedule"]:
                destination = target / "trials" / row["id"]
                destination.mkdir(parents=True)
                shutil.copyfile(source / "trials" / row["id"] / "result.json", destination / "result.json")
        provenance = rerun.read_json(round_dir / "provenance.json")
        provenance["baseline_path"] = str(baseline)
        (round_dir / "provenance.json").write_text(json.dumps(provenance))
        return rerun.load_context(round_dir)

    def passed_preflight(self, context, hook=None):
        def preflight(out, args, tasks, candidates):
            frozen = rerun.read_json(out / "freeze.json")
            frozen["image_spec"] = context.baseline["image_spec"]
            context.bench.runtime.save(out / "freeze.json", frozen)
            if hook:
                hook(out)
            return {"status": "passed", "model_calls": 0}
        return preflight

    def completed_trial(self, context, status="completed", hook=None):
        def trial(row, out, *args):
            result = {**row, "status": status, "accepted": status == "completed", "patch_correct": status == "completed",
                      "session_completed": status == "completed", "task_wall_s": 1.0, "request_count": 1}
            destination = out / "trials" / row["id"]
            destination.mkdir(parents=True)
            context.bench.runtime.save(destination / "result.json", result)
            if hook:
                hook(out)
            return result
        return trial

    def execute(self, context, command="run", out=None):
        args = rerun.fixed_args(command, out or self.root / "output", context)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return rerun.execute(args, context)

    def test_cli_plan_has_only_revised_case_and_three_runs_per_original_candidate(self):
        context = rerun.load_context()
        before = {name: hashes(PACKAGE / "results" / name) for name in ("budget-r4", "smoke")}
        out = self.root / "plan"
        completed = subprocess.run([sys.executable, "-B", str(ROUND / "run.py"), "plan", "--out", str(out)],
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("zero model calls", completed.stdout)
        frozen = rerun.read_json(out / "freeze.json")
        self.assertEqual(len(frozen["schedule"]), 18)
        self.assertEqual({row["task"] for row in frozen["schedule"]}, {"py-money-contract-v2"})
        self.assertEqual(frozen["candidates"], context.baseline["candidates"])
        for candidate in frozen["candidates"]:
            self.assertEqual(sorted(row["rep"] for row in frozen["schedule"] if row["candidate"] == candidate["id"]), [1, 2, 3])
        revised = frozen["tasks"][0]
        original = next(task for task in context.baseline["tasks"] if task["id"] == "py-money-contract")
        self.assertEqual(revised["reference"], original["reference"])
        self.assertEqual(revised["acceptance"], original["acceptance"])
        self.assertEqual(revised["allowed"], original["allowed"])
        self.assertEqual(revised["structural"], original["structural"])
        self.assertEqual({name: value for name, value in revised["files"].items() if name != "README.md"},
                         {name: value for name, value in original["files"].items() if name != "README.md"})
        self.assertNotIn(original["request"], revised["files"]["README.md"])
        self.assertIn(revised["request"], revised["files"]["README.md"])
        self.assertEqual(before, {name: hashes(PACKAGE / "results" / name) for name in before})

    def test_cli_validate_runs_real_baseline_and_reference_without_models(self):
        out = self.root / "validate"
        completed = subprocess.run([sys.executable, "-B", str(ROUND / "run.py"), "validate", "--out", str(out)],
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("zero model calls", completed.stdout)
        validation = rerun.read_json(out / "validation.json")
        self.assertEqual(validation["model_calls"], 0)
        proof = validation["tasks"][0]
        self.assertTrue(proof["baseline"]["compilation"]["passed"])
        self.assertTrue(proof["baseline"]["regression"]["passed"])
        self.assertFalse(proof["baseline"]["acceptance"]["passed"])
        self.assertTrue(all(check["passed"] for check in proof["reference"].values()))

    def test_mocked_run_keeps_baseline_and_gate_files_unchanged_and_rechecks_oauth(self):
        context = self.fixture()
        before = hashes(context.package / "results")
        with patch.object(context.bench, "preflight", self.passed_preflight(context)), \
             patch.object(context.bench.runtime, "validate_oauth_window") as oauth, \
             patch.object(context.bench, "run_trial", self.completed_trial(context)):
            self.assertEqual(self.execute(context), 0)
        self.assertEqual(oauth.call_count, 3)
        summary = rerun.read_json(self.root / "output/summary.json")
        self.assertEqual((summary["started"], summary["accepted"]), (18, 18))
        self.assertEqual(before, hashes(context.package / "results"))
        gates = rerun.read_json(self.root / "output/gates.json")
        self.assertTrue(all("gate-proofs" in gate["path"] for gate in gates))
        provenance = rerun.read_json(self.root / "output/gate-provenance.json")
        for gate in provenance:
            for name, expected in gate["source_hashes"].items():
                self.assertEqual(rerun.digest(Path(gate["copy"]) / name), expected)

    def test_mutated_contract_is_rejected_before_first_model_call(self):
        context = self.fixture()
        def mutate(_):
            with (context.round_dir / "request.txt").open("a") as stream:
                stream.write("\nChanged after freeze.\n")
        with patch.object(context.bench, "preflight", self.passed_preflight(context, mutate)), \
             patch.object(context.bench, "run_trial") as trial:
            with self.assertRaisesRegex(ValueError, "changed after freezing"):
                self.execute(context)
            trial.assert_not_called()

    def test_mutated_provenance_stops_before_next_model_call(self):
        context = self.fixture()
        def mutate(_):
            with (context.round_dir / "provenance.json").open("a") as stream:
                stream.write("\n")
        with patch.object(context.bench, "preflight", self.passed_preflight(context)), \
             patch.object(context.bench.runtime, "validate_oauth_window"), \
             patch.object(context.bench, "run_trial", side_effect=self.completed_trial(context, hook=mutate)) as trial:
            with self.assertRaisesRegex(ValueError, "changed after freezing"):
                self.execute(context)
            self.assertEqual(trial.call_count, 1)
        self.assertEqual(rerun.read_json(self.root / "output/summary.json")["started"], 1)

    def test_frozen_task_and_revision_snapshot_are_checked_before_inference(self):
        for target in ("task", "snapshot"):
            with self.subTest(target=target):
                context = self.fixture(target)
                def mutate(out):
                    if target == "task":
                        frozen = rerun.read_json(out / "freeze.json")
                        frozen["tasks"][0]["request"] = "Ignore the revised contract."
                        context.bench.runtime.save(out / "freeze.json", frozen)
                    else:
                        (out / ".rerun-source/request.txt").write_text("Altered evidence.")
                with patch.object(context.bench, "preflight", self.passed_preflight(context, mutate)), \
                     patch.object(context.bench, "run_trial") as trial:
                    with self.assertRaisesRegex(ValueError, "Frozen (task|rerun source)"):
                        self.execute(context, out=self.root / (target + "-output"))
                    trial.assert_not_called()

    def test_changed_agenda_or_budget_is_rejected_before_inference(self):
        for target in ("schedule", "budget", "reps", "seed", "candidates", "global_seconds"):
            with self.subTest(target=target):
                context = self.fixture(target)
                def mutate(out):
                    frozen = rerun.read_json(out / "freeze.json")
                    if target == "schedule":
                        frozen["schedule"][0]["rep"] = 4
                    elif target == "budget":
                        frozen["budget"]["calls"] = 10
                    elif target == "candidates":
                        frozen["candidates"][0]["variant"] = "low"
                    else:
                        frozen[target] += 1
                    context.bench.runtime.save(out / "freeze.json", frozen)
                with patch.object(context.bench, "preflight", self.passed_preflight(context, mutate)), \
                     patch.object(context.bench, "run_trial") as trial:
                    with self.assertRaisesRegex(ValueError, "agenda, cohort or budget differs"):
                        self.execute(context, out=self.root / (target + "-output"))
                    trial.assert_not_called()

    def test_original_task_cannot_be_redefined_even_with_updated_provenance_digest(self):
        context = self.fixture()
        baseline = context.baseline_path / "freeze.json"
        frozen = rerun.read_json(baseline)
        next(task for task in frozen["tasks"] if task["id"] == "py-money-contract")["acceptance"] = "assert True\n"
        baseline.write_text(json.dumps(frozen))
        provenance_path = context.round_dir / "provenance.json"
        provenance = rerun.read_json(provenance_path)
        provenance["baseline_freeze_sha256"] = rerun.digest(baseline)
        provenance_path.write_text(json.dumps(provenance))
        with self.assertRaisesRegex(ValueError, "Original money task differs"):
            rerun.load_context(context.round_dir)

    def test_extra_harness_source_is_rejected_before_loading_it(self):
        context = self.fixture()
        (context.round_dir / "harness/override.py").write_text("raise RuntimeError('must not execute')\n")
        with self.assertRaisesRegex(ValueError, "file set differs"):
            rerun.load_context(context.round_dir)

    def test_failed_gate_still_blocks_model_calls(self):
        context = self.fixture()
        gate = context.package / "results/smoke"
        frozen = rerun.read_json(gate / "freeze.json")
        result_path = gate / "trials" / frozen["schedule"][0]["id"] / "result.json"
        result = rerun.read_json(result_path)
        result["accepted"] = False
        result_path.write_text(json.dumps(result))
        before = hashes(context.package / "results")
        with patch.object(context.bench, "preflight", self.passed_preflight(context)), \
             patch.object(context.bench, "run_trial") as trial:
            with self.assertRaisesRegex(ValueError, "smoke gate did not pass"):
                self.execute(context)
            trial.assert_not_called()
        self.assertEqual(before, hashes(context.package / "results"))

    def test_gate_cohort_compatibility_is_not_bypassed(self):
        context = self.fixture()
        gate_path = context.package / "results/budget-r4/freeze.json"
        gate = rerun.read_json(gate_path)
        gate["candidates"][0]["variant"] = "low"
        gate_path.write_text(json.dumps(gate))
        with patch.object(context.bench, "preflight", self.passed_preflight(context)), \
             patch.object(context.bench, "run_trial") as trial:
            with self.assertRaisesRegex(ValueError, "configuration differs"):
                self.execute(context)
            trial.assert_not_called()

    def test_infrastructure_failure_stops_and_reports_remaining_trials(self):
        context = self.fixture()
        with patch.object(context.bench, "preflight", self.passed_preflight(context)), \
             patch.object(context.bench.runtime, "validate_oauth_window"), \
             patch.object(context.bench, "run_trial", side_effect=self.completed_trial(context, "infra_error")) as trial:
            self.assertEqual(self.execute(context), 1)
            self.assertEqual(trial.call_count, 1)
        summary = rerun.read_json(self.root / "output/summary.json")
        self.assertEqual((summary["planned"], summary["started"], summary["accepted"]), (18, 1, 0))

    def test_existing_output_is_never_overwritten(self):
        context = self.fixture()
        self.assertEqual(self.execute(context, "plan"), 0)
        before = hashes(self.root / "output")
        with self.assertRaisesRegex(ValueError, "Output must be new"):
            self.execute(context, "plan")
        self.assertEqual(before, hashes(self.root / "output"))


if __name__ == "__main__":
    unittest.main()
