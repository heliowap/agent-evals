import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from grading import export, pack_jobs, select_review_ids, validate_grade, derive_metrics, seal_base, seal_final, validate_sealed
from grading.common import digest, save, load
from grading.sealing import unblind
from grading.schema import AUXILIARY, GRADER
from fixtures import inputs, study, assembled, base_grades, reviews_for


class GradingTests(unittest.TestCase):
    def test_blinding_exact_visible_evidence_and_loader(self):
        records, tasks, gold, schedule = inputs()
        visible = records[0]["tool_evidence"][1].pop("visible_text")
        records[0]["tool_evidence"][1].update(visible_path="visible.txt", visible_sha256=hashlib.sha256(visible.encode()).hexdigest(),
                                            raw_text="RAW_PRIVATE")
        bundle = export(records, tasks, gold, lambda path: visible, schedule, review_per_group=1)
        public = json.dumps(pack_jobs(bundle))
        for hidden in ("CANDIDATE_PRIVATE", "EFFORT_PRIVATE", "LATENCY_PRIVATE", "NATIVE_PRIVATE", "CONTROLLER_PRIVATE", "RAW_PRIVATE", records[0]["id"]):
            self.assertNotIn(hidden, public)
        identity = next(i for i, m in bundle["private_mapping"].items() if m["trial_id"] == records[0]["id"])
        packet = bundle["packets"][identity]
        self.assertEqual(visible, packet["candidate_evidence"][1]["text"])
        self.assertFalse(packet["units"][0]["reference_evidence"][0]["support_eligible"])
        with self.assertRaisesRegex(ValueError, "hash breach"):
            export(records, tasks, gold, lambda path: "different", schedule, review_per_group=1)

    def test_planned_sample_162_and_batches(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study(full=True)
        selected = select_review_ids(schedule)
        self.assertEqual(162, len(selected))
        self.assertEqual(selected, bundle["review_plan"]["trial_ids"])
        for suite in ("web", "code"):
            for config in schedule["configurations"]:
                self.assertEqual(9, sum(t["id"] in selected and t["suite"] == suite and t["configuration_id"] == config for t in schedule["trials"]))
        self.assertTrue(all(len(job["jobs"]) <= 4 for job in pack_jobs(bundle)))
        self.assertEqual(162, sum(len(j["jobs"]) for j in pack_jobs(bundle, review=True, base_grades=base["grades"])))
        self.assertEqual(sealed, validate_sealed(sealed))
        with self.assertRaises(ValueError):
            pack_jobs(bundle, batch_size=5)

    def test_no_other_units_vacuous_and_actual_research(self):
        *_, bundle, base, reviews, sealed = study(no_other=True)
        identity = next(iter(base["grades"]))
        packet, grade = bundle["packets"][identity], base["grades"][identity]
        self.assertTrue(derive_metrics(packet, grade)["practical_success"])
        absent = deepcopy(packet)
        absent["candidate_evidence"] = [e for e in absent["candidate_evidence"] if e["tool"] != "websearch"]
        # Use a web packet: code only requires a file read.
        webid = next(i for i, p in bundle["packets"].items() if p["suite"] == "web")
        web = deepcopy(bundle["packets"][webid])
        web["candidate_evidence"] = [e for e in web["candidate_evidence"] if e["tool"] != "websearch"]
        self.assertFalse(derive_metrics(web, base["grades"][webid])["practical_success"])

    def test_explicit_frozen_sample_authoritative_through_plan_export_and_seal(self):
        records, tasks, gold, schedule = inputs(full=True)
        fallback = select_review_ids(schedule)
        grouped = {}
        for trial in schedule["trials"]:
            grouped.setdefault((trial["suite"], trial["configuration_id"]), []).append(trial["id"])
        frozen = [identity for group in sorted(grouped) for identity in sorted(grouped[group])[:9]]
        schedule["review_sample_ids"] = list(reversed(frozen))
        expected = sorted(frozen)
        self.assertNotEqual(fallback, expected)
        self.assertEqual(expected, select_review_ids(schedule))
        self.assertEqual(list(reversed(frozen)), schedule["review_sample_ids"])
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule, full=True)
        self.assertEqual(expected, bundle["review_plan"]["trial_ids"])
        reviewed_ids = sorted(bundle["private_mapping"][r["blind_id"]]["trial_id"] for r in sealed["reviews"])
        self.assertEqual(expected, reviewed_ids)
        self.assertEqual(162, sealed["review_accounting"]["planned_sample"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / "schedule.json", schedule)
            planned = subprocess.run([sys.executable, "-B", "-m", "grading.cli", "plan-reviews",
                                      "--schedule", str(root / "schedule.json"),
                                      "--output", str(root / "planned.json")], capture_output=True, text=True)
            self.assertEqual(0, planned.returncode, planned.stderr)
            self.assertEqual(expected, load(root / "planned.json")["trial_ids"])
            self.assertEqual(bundle["review_plan"]["blind_ids"], load(root / "planned.json")["blind_ids"])

    def test_invalid_explicit_samples_rejected_without_fallback(self):
        records, tasks, gold, schedule = inputs()
        valid = select_review_ids(schedule, per_group=1)
        schedule["review_sample_ids"] = list(reversed(valid))
        self.assertEqual(valid, select_review_ids(schedule, per_group=1))
        trial_map = {t["id"]: t for t in schedule["trials"]}
        first = trial_map[valid[0]]
        same_group_other = next(t["id"] for t in schedule["trials"]
                                if t["suite"] == first["suite"] and t["configuration_id"] == first["configuration_id"]
                                and t["id"] != valid[0])
        malformed = {
            "duplicate": [valid[0], valid[0], *valid[2:]],
            "unknown": ["not-in-planned-schedule", *valid[1:]],
            "unbalanced": [valid[0], same_group_other, *valid[2:]],
            "missing": valid[:-1],
            "extra": [*valid, same_group_other],
            "null": None,
            "not_array": "invalid",
        }
        for name, sample in malformed.items():
            with self.subTest(sample=name):
                invalid = dict(schedule, review_sample_ids=sample)
                with self.assertRaises(ValueError):
                    select_review_ids(invalid, per_group=1)
                with self.assertRaises(ValueError):
                    export(records, tasks, gold, None, invalid, review_per_group=1)

    def test_support_eligible_and_exact_units(self):
        *_, bundle, base, reviews, sealed = study()
        identity = next(iter(base["grades"]))
        packet, good = bundle["packets"][identity], base["grades"][identity]
        for mutate in (lambda g: g["units"].pop(),
                       lambda g: g["units"].append(deepcopy(g["units"][0])),
                       lambda g: g["units"][0]["evidence"].clear(),
                       lambda g: g["units"][0]["evidence"][0].update(source_id="gold-reference"),
                       lambda g: g["units"][0]["evidence"][0].update(quote="raw beyond visible")):
            bad = deepcopy(good)
            mutate(bad)
            with self.assertRaises(ValueError):
                validate_grade(bad, packet)
        unsupported = deepcopy(good)
        unsupported["units"][0].update(supported=False, evidence=[])
        metrics = derive_metrics(packet, unsupported)
        self.assertEqual(1, metrics["correctness"])
        self.assertEqual(.5, metrics["grounded_coverage"])
        self.assertFalse(metrics["practical_success"])
        self.assertEqual(set(AUXILIARY), set(validate_grade(good, packet)["auxiliary"]))
        self.assertTrue(all(v is None for v in validate_grade(good, packet)["auxiliary"].values()))

    def test_nonanswer_operational_review_and_unrun_not_replaced(self):
        records, tasks, gold, schedule = inputs()
        selected = select_review_ids(schedule, 1)
        failed = next(r for r in records if r["id"] == selected[0])
        failed.update(status="timeout", completed=False, final_answer="partial diagnostic")
        records = [r for r in records if r["id"] != selected[1]]
        bundle, base, reviews, sealed = assembled(records, tasks, gold, schedule)
        identities = {m["trial_id"]: i for i, m in bundle["private_mapping"].items()}
        self.assertEqual(selected, bundle["review_plan"]["trial_ids"])
        self.assertIsNone(sealed["final_grades"][identities[selected[0]]])
        self.assertIsNone(sealed["metrics"][identities[selected[0]]]["correctness"])
        self.assertEqual(0, sealed["metrics"][identities[selected[0]]]["effective_coverage"])
        self.assertEqual(1, sealed["review_accounting"]["operational_reviewed"])
        self.assertEqual([identities[selected[1]]], sealed["review_accounting"]["unresolved_unrun"])
        with self.assertRaises(ValueError):
            validate_grade(next(iter(base["grades"].values())), bundle["packets"][identities[selected[0]]])

    def test_critical_uncertain_extra_missing_review_and_adjudication(self):
        records, tasks, gold, schedule = inputs()
        bundle = export(records, tasks, gold, None, schedule, review_per_group=1)
        grades = base_grades(bundle)
        extras = [i for i in grades if i not in bundle["review_plan"]["blind_ids"]][:2]
        grades[extras[0]]["critical_errors"] = [{"instance": "Artificial critical error"}]
        grades[extras[1]]["uncertain"] = True
        base = seal_base(bundle, grades)
        reviews = reviews_for(bundle, base)
        self.assertEqual(6, len(reviews))
        with self.assertRaisesRegex(ValueError, "review obligation"):
            seal_final(bundle, base, reviews[:-1])
        reviews[0]["grade"]["units"][0].update(correct=False)
        with self.assertRaisesRegex(ValueError, "adjudication"):
            seal_final(bundle, base, reviews)
        identity = reviews[0]["blind_id"]
        event = {"blind_id": identity, "grade": deepcopy(reviews[0]["grade"]), "rationale": "Artificial label correction",
                 "grader": GRADER, "base_grade_hash": digest(base["grades"][identity]), "review_hash": digest(reviews[0])}
        sealed = seal_final(bundle, base, reviews, [event])
        self.assertTrue(sealed["base_seal"]["grades"][identity]["units"][0]["correct"])
        self.assertFalse(sealed["final_grades"][identity]["units"][0]["correct"])
        self.assertEqual(1, len(sealed["review_accounting"]["disagreements"]))

    def test_duplicate_ledger_and_hash_breach(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            export(records + [records[0]], tasks, gold, None, schedule, review_per_group=1)
        corrupted = deepcopy(sealed)
        corrupted["base_seal"]["grades"][next(iter(base["grades"]))]["uncertain"] = True
        with self.assertRaisesRegex(ValueError, "hash breach"):
            validate_sealed(corrupted)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            seal_final(bundle, base, reviews + [reviews[0]])
        self.assertEqual(len(schedule["trials"]), len(unblind(sealed)))

    def test_import_cli_immutable_original_and_seal_audit(self):
        records, tasks, gold, schedule, bundle, base, reviews, sealed = study()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / "bundle.json", bundle)
            save(root / "incoming.json", list(base["grades"].values()))
            command = [sys.executable, "-B", "-m", "grading.cli", "import-base", "--bundle", str(root / "bundle.json"),
                       "--input", str(root / "incoming.json"), "--store", str(root)]
            imported = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, imported.returncode, imported.stderr)
            duplicate = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, duplicate.returncode)
            seal_command = [sys.executable, "-B", "-m", "grading.cli", "seal-base", "--bundle", str(root / "bundle.json"),
                            "--store", str(root), "--output", str(root / "base-seal.json")]
            run = subprocess.run(seal_command, capture_output=True, text=True)
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertEqual(base, load(root / "base-seal.json"))
            save(root / "sealed.json", sealed, immutable=True)
            audit = subprocess.run([sys.executable, "-B", "-m", "grading.audit", "--sealed", str(root / "sealed.json")], capture_output=True, text=True)
            self.assertEqual(0, audit.returncode, audit.stderr)
            with self.assertRaises(FileExistsError):
                save(root / "sealed.json", {}, immutable=True)


if __name__ == "__main__":
    unittest.main()
