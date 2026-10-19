import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

# Shared artificial artifacts live entirely inside the owned grading test tree.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grading"))
from fixtures import inputs, study, assembled

from analysis import analyze, render_report, write_artifacts, audit_artifacts
from grading import select_review_ids, pack_jobs
from grading.common import digest, load, save


class AnalysisTests(unittest.TestCase):
    def test_complete_full_matrix_10000_clusters_contrasts_and_recommendation(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study(full=True)
        result = analyze(records, sealed, schedule, tasks)
        self.assertFalse(result["incomplete"])
        self.assertEqual(648, result["n_attempted"])
        self.assertEqual(10000, result["bootstrap_draws"])
        for suite, clusters in (("web", 4), ("code", 6)):
            data = result["suites"][suite]
            self.assertEqual(clusters, data["bootstrap"]["n_independent_clusters"])
            self.assertEqual(36, len(data["bootstrap"]["pairwise_contrasts"]))
            self.assertEqual(9, len(data["bootstrap"]["within_family_effort_contrasts"]))
            self.assertEqual("gemini-low", data["recommendation"]["preferred"])
            for config in data["configurations"].values():
                self.assertEqual((36, 36, 36), (config["n_scheduled"], config["n_attempted"], config["n_semantic"]))
                self.assertEqual(1, config["effective_coverage_task_macro_scheduled"])
                self.assertEqual(1, config["success_scheduled"])
                self.assertEqual(0, config["n_critical_instances"])
        report = render_report(result)
        self.assertIn("not human calibration", report)
        self.assertIn("No formal superiority", report)

    def test_stopped_unrun_denominators_and_no_qualified_winner(self):
        records, tasks, gold, schedule = inputs()
        selected = select_review_ids(schedule, 1)
        records = [r for r in records if r["id"] != selected[0]]
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule)
        result = analyze(records, sealed, schedule, tasks, draws=10000)
        self.assertTrue(result["incomplete"])
        self.assertEqual((24, 23, 1), (result["n_scheduled"], result["n_attempted"], result["n_unrun"]))
        self.assertEqual(1, len(result["review_accounting"]["unresolved_unrun"]))
        for suite in result["suites"].values():
            self.assertIsNone(suite["recommendation"]["preferred"])
            self.assertEqual([], suite["recommendation"]["qualified"])
        s = next(s for d in result["suites"].values() for s in d["configurations"].values() if s["n_unrun"])
        self.assertEqual(5 / 6, s["completion_scheduled"])
        self.assertEqual(1, s["completion_attempted"])
        self.assertEqual(5, s["n_semantic"])
        self.assertEqual(1, s["mean_grounded_coverage_completed"])
        self.assertAlmostEqual(5 / 6, s["effective_coverage_task_macro_scheduled"])
        self.assertIn("INCOMPLETE STUDY — NO QUALIFIED WINNER", render_report(result))

    def test_nonanswer_semantic_null_zero_effective_and_failure_not_fast(self):
        records, tasks, gold, schedule = inputs()
        trial = next(t for t in schedule["trials"] if t["suite"] == "web" and t["configuration_id"] == "gemini-low")
        failed = next(r for r in records if r["id"] == trial["id"])
        failed.update(status="timeout", completed=False, final_answer="partial", wall_seconds=1)
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule)
        result = analyze(records, sealed, schedule, tasks, draws=200)
        s = result["suites"]["web"]["configurations"]["gemini-low"]
        self.assertEqual(5, s["n_semantic"])
        self.assertEqual(1, s["mean_grounded_coverage_completed"])
        self.assertAlmostEqual(5 / 6, s["effective_coverage_task_macro_scheduled"])
        self.assertEqual((20, 5), (s["success_wall_seconds"]["median"], s["success_wall_seconds"]["n"]))
        self.assertEqual("gemini-medium", result["suites"]["web"]["recommendation"]["preferred"])
        self.assertEqual(5, s["auxiliary"]["citation_coverage"]["n_missing"])
        self.assertEqual(0, s["auxiliary"]["citation_coverage"]["n_observed"])

    def test_cluster_pairing_keeps_all_repeats_and_configurations(self):
        records, tasks, gold, schedule = inputs()
        def edit(grades, bundle):
            for identity, grade in grades.items():
                # Both configs share the same difficult repository; paired differences remain exactly zero.
                trialid = bundle["private_mapping"][identity]["trial_id"]
                if trialid.startswith("code-0"):
                    for unit in grade["units"]:
                        unit["correct"] = False
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, grade_edit=edit)
        result = analyze(records, sealed, schedule, tasks)
        bootstrap = result["suites"]["code"]["bootstrap"]
        self.assertEqual(2, bootstrap["n_independent_clusters"])
        self.assertEqual([0, 0], bootstrap["pairwise_contrasts"][0]["descriptive_95_percent_interval"])
        self.assertEqual([0, 1], bootstrap["coverage_intervals"]["gemini-low"])
        self.assertEqual(.5, result["suites"]["code"]["configurations"]["gemini-low"]["effective_coverage_task_macro_scheduled"])
        self.assertEqual([], result["suites"]["code"]["recommendation"]["qualified"])

    def test_critical_disqualifies_and_missing_latency_does_not_invent_preference(self):
        records, tasks, gold, schedule = inputs()
        for record in records:
            record.pop("wall_seconds")
        def edit(grades, bundle):
            for identity, grade in grades.items():
                if "gemini-low" in bundle["private_mapping"][identity]["trial_id"]:
                    grade["critical_errors"] = ["Artificial decisive wrong conclusion"]
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, grade_edit=edit)
        result = analyze(records, sealed, schedule, tasks, draws=100)
        for data in result["suites"].values():
            self.assertEqual(["gemini-medium"], data["recommendation"]["qualified"])
            self.assertIsNone(data["recommendation"]["preferred"])
            low = data["configurations"]["gemini-low"]
            self.assertEqual(6, low["n_critical_instances"])
            self.assertEqual(0, low["n_success"])
            medium = data["configurations"]["gemini-medium"]
            self.assertEqual({"n": 0, "missing": 6, "median": None, "p90": None}, medium["success_wall_seconds"])

    def test_saved_hashes_reproduce_tables_and_detect_breaches(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = write_artifacts(root, records, sealed, schedule, tasks, draws=10000)
            self.assertEqual(manifest, audit_artifacts(root))
            audited = subprocess.run([sys.executable, "-B", "-m", "analysis.audit", "--final", str(root / "final.json")], capture_output=True, text=True)
            self.assertEqual(0, audited.returncode, audited.stderr)
            original = (root / "report.md").read_text()
            (root / "report.md").write_text(original + "hash breach\n")
            with self.assertRaisesRegex(ValueError, "hash breach"):
                audit_artifacts(root)
            (root / "report.md").write_text(original)
            metrics = load(root / "metrics.json")
            metrics["n_unrun"] = 1
            save(root / "metrics.json", metrics)
            with self.assertRaisesRegex(ValueError, "hash breach"):
                audit_artifacts(root)

    def test_duplicate_and_record_task_schedule_hash_breach(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            analyze(records + [records[0]], sealed, schedule, tasks, draws=10)
        changed = deepcopy(records)
        changed[0]["wall_seconds"] = 100
        with self.assertRaisesRegex(ValueError, "record hash breach"):
            analyze(changed, sealed, schedule, tasks, draws=10)
        changed_tasks = deepcopy(tasks)
        changed_tasks[0]["cluster_id"] = "post-selected"
        with self.assertRaisesRegex(ValueError, "tasks hash breach"):
            analyze(records, sealed, schedule, changed_tasks, draws=10)
        changed_schedule = deepcopy(schedule)
        changed_schedule["seed"] = 99
        with self.assertRaisesRegex(ValueError, "schedule/tasks hash breach"):
            analyze(records, sealed, changed_schedule, tasks, draws=10)

    def test_mandatory_fault_on_648th_attempt_blocks_both_suite_winners(self):
        for status in ("auth_error", "quota_error", "protocol_error", "search_outage", "harness_error",
                       "supervisor_cleanup_failure", "credential_hygiene_failure"):
            with self.subTest(status=status):
                records, tasks, gold, schedule = inputs(full=True)
                records[-1].update(status=status, completed=False, final_answer="")
                # No explicit study fields: direct API callers still get mandatory-stop protection.
                bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
                result = analyze(records, sealed, schedule, tasks, draws=100)
                self.assertEqual((648, 648, 0), (result["n_scheduled"], result["n_attempted"], result["n_unrun"]))
                self.assertTrue(result["incomplete"])
                self.assertIn({"source": "record.terminal_status", "reason": status, "detail": None,
                               "trial_ids": [records[-1]["id"]]}, result["study_stop_reasons"])
                for suite in result["suites"].values():
                    self.assertEqual(9, len(suite["configurations"]))
                    self.assertEqual([], suite["recommendation"]["qualified"])
                    self.assertIsNone(suite["recommendation"]["preferred"])
                report = render_report(result)
                self.assertIn("NO QUALIFIED WINNER in either suite", report)
                self.assertLess(report.index(status), report.index("## Code suite"))

    def test_execution_flags_override_completed_last_trial_and_hygiene_stop(self):
        for flag, stop, propagate in (
                (True, None, False),
                (True, {"reason": "supervisor_cleanup_failure", "trial_id": "last"}, False),
                (False, {"reason": "credential_hygiene_failure", "after_terminal": True}, False),
                (True, {"reason": "credential_hygiene_failure", "after_terminal": True}, True),
                (False, {}, False)):
            with self.subTest(flag=flag, stop=stop, propagate=propagate):
                records, tasks, gold, schedule = inputs(full=True)
                for record in records:
                    record.update(study_incomplete=False, study_stop=None)
                affected = records if propagate else records[-1:]
                for record in affected:
                    record.update(study_incomplete=flag, study_stop=deepcopy(stop))
                bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
                result = analyze(records, sealed, schedule, tasks, draws=100)
                self.assertTrue(result["incomplete"])
                self.assertEqual(648, result["n_attempted"])
                self.assertEqual(648, sum(s["n_semantic"] for d in result["suites"].values() for s in d["configurations"].values()))
                sources = {r["source"] for r in result["study_stop_reasons"]}
                self.assertEqual(flag, "record.study_incomplete" in sources)
                self.assertEqual(stop is not None, "record.study_stop" in sources)
                self.assertTrue(all(len(r["trial_ids"]) == len(affected) for r in result["study_stop_reasons"]))
                for suite in result["suites"].values():
                    self.assertEqual([], suite["recommendation"]["qualified"])
                    self.assertIsNone(suite["recommendation"]["preferred"])
                    self.assertTrue(all(s["success_scheduled"] == 1 for s in suite["configurations"].values()))
                # Execution-level state is covered by record hashes, not exposed to blind graders.
                public = json.dumps([j for job in pack_jobs(bundle) for j in job["jobs"]])
                self.assertNotIn("study_incomplete", public)
                self.assertNotIn("study_stop", public)

    def test_all_attempted_ordinary_failures_do_not_automatically_stop_study(self):
        for status in ("provider_error", "incomplete", "timeout"):
            with self.subTest(status=status):
                records, tasks, gold, schedule = inputs(full=True)
                for record in records:
                    record.update(study_incomplete=False, study_stop=None)
                records[-1].update(status=status, completed=False, final_answer="")
                bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
                result = analyze(records, sealed, schedule, tasks, draws=100)
                self.assertFalse(result["incomplete"])
                self.assertEqual([], result["study_stop_reasons"])
                self.assertEqual(648, result["n_attempted"])
                self.assertTrue(all(d["recommendation"]["preferred"] is not None for d in result["suites"].values()))
        records, tasks, gold, schedule = inputs(full=True)
        for record in records:
            record.update(status="timeout", completed=False, final_answer="", study_incomplete=False, study_stop=None)
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
        result = analyze(records, sealed, schedule, tasks, draws=100)
        self.assertFalse(result["incomplete"])
        self.assertEqual(648, result["n_attempted"])
        self.assertTrue(all(d["recommendation"]["status"] == "No qualified candidate" for d in result["suites"].values()))

    def test_execution_stop_saved_report_reproduces_and_state_is_hash_bound(self):
        records, tasks, gold, schedule = inputs(full=True)
        for record in records:
            record.update(study_incomplete=True, study_stop={"reason": "supervisor_cleanup_failure",
                                                           "trial_id": records[-1]["id"], "after_terminal": True})
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = write_artifacts(root, records, sealed, schedule, tasks)
            self.assertEqual(manifest, audit_artifacts(root))
            saved = load(root / "metrics.json")
            self.assertTrue(saved["study_state"]["incomplete"])
            self.assertEqual(648, saved["n_attempted"])
            self.assertIn("supervisor_cleanup_failure", (root / "report.md").read_text())
            self.assertEqual(records[-1]["study_stop"], load(root / "inputs.json")["records"][-1]["study_stop"])
        for field, replacement in (("study_incomplete", False), ("study_stop", None)):
            changed = deepcopy(records)
            changed[-1][field] = replacement
            with self.assertRaisesRegex(ValueError, "execution record hash breach"):
                analyze(changed, sealed, schedule, tasks, draws=10)


if __name__ == "__main__":
    unittest.main()
