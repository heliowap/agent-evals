"""Exercise the data verifier through its public API, never snapshot execution."""

from copy import deepcopy
import unittest

from tasks.code.verify import load, verify


class CodeTaskAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks, cls.gold, cls.navigation = load()

    def audit(self, *, tasks=None, gold=None, navigation=None):
        return verify(tasks=self.tasks if tasks is None else tasks,
                      gold=self.gold if gold is None else gold,
                      navigation=self.navigation if navigation is None else navigation)

    def test_authored_artifacts_pass(self):
        counts = self.audit()
        self.assertEqual(counts["tasks"], 12)
        self.assertEqual(counts["repositories"], 6)
        self.assertEqual(counts["fixtures"], 72)
        self.assertGreater(counts["quotes"], counts["units"])

    def test_changed_quote_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][0]["evidence"][0]["quote"] += "invented"
        with self.assertRaisesRegex(ValueError, "quote mismatch"):
            self.audit(gold=gold)

    def test_manifest_hash_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["manifest"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "manifest hash mismatch"):
            self.audit(gold=gold)

    def test_source_hash_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["source_hashes"]["src/click/core.py"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "gold source hash mismatch"):
            self.audit(gold=gold)

    def test_invalid_span_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][0]["evidence"][0]["end_line"] = 10**9
        with self.assertRaisesRegex(ValueError, "invalid span"):
            self.audit(gold=gold)

    def test_unmanifested_source_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][0]["evidence"][0]["path"] = "invented.py"
        with self.assertRaisesRegex(ValueError, "source missing from manifest"):
            self.audit(gold=gold)

    def test_path_escape_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][0]["evidence"][0]["path"] = "../gold.json"
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            self.audit(gold=gold)

    def test_repository_balance_rejected(self):
        tasks = deepcopy(self.tasks)
        tasks[0]["snapshot_id"] = "httpx"
        with self.assertRaisesRegex(ValueError, "two tasks per repository"):
            self.audit(tasks=tasks)

    def test_wrong_type_mix_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["task_type"] = "semanticlocation"
        with self.assertRaisesRegex(ValueError, "task-type counts"):
            self.audit(gold=gold)

    def test_duplicate_unit_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][1]["id"] = gold["C01"]["units"][0]["id"]
        with self.assertRaisesRegex(ValueError, "unit IDs/order"):
            self.audit(gold=gold)

    def test_nonboolean_essential_rejected(self):
        gold = deepcopy(self.gold)
        gold["C01"]["units"][0]["essential"] = 1
        with self.assertRaisesRegex(ValueError, "essential flag not boolean"):
            self.audit(gold=gold)

    def test_negative_requires_closed_branch(self):
        gold = deepcopy(self.gold)
        del gold["C04"]["closed_branch_evidence"]
        with self.assertRaisesRegex(ValueError, "negative lacks closed-branch"):
            self.audit(gold=gold)

    def test_unsupported_fixture_cannot_claim_supported(self):
        gold = deepcopy(self.gold)
        gold["C01"]["fixtures"]["unsupported"]["expected_unit_labels"][0] = "correct_supported"
        with self.assertRaisesRegex(ValueError, "fixture label expectation"):
            self.audit(gold=gold)

    def test_fixture_omission_has_no_assigned_evidence(self):
        gold = deepcopy(self.gold)
        gold["C01"]["fixtures"]["omitted"]["evidence_units"].append("C01.U4")
        with self.assertRaisesRegex(ValueError, "fixture evidence assignment"):
            self.audit(gold=gold)

    def test_alternativevalid_contract(self):
        # This inspects declared author-reviewed expectations, not NLP truth.
        # The public audit also verifies each fixture's evidence references.
        counts = self.audit()
        self.assertEqual(counts["fixtures"], 72)
        for item in self.gold.values():
            self.assertNotEqual(item["fixtures"]["alternativevalid"]["answer"],
                                item["fixtures"]["correct"]["answer"])

    def test_navigation_cannot_execute_source(self):
        navigation = deepcopy(self.navigation)
        navigation["C01"][0]["tool"] = "shell"
        with self.assertRaisesRegex(ValueError, "prohibited navigation tool"):
            self.audit(navigation=navigation)

    def test_navigation_must_cover_evidence(self):
        navigation = deepcopy(self.navigation)
        navigation["C01"][1]["start_line"] = 2690
        with self.assertRaisesRegex(ValueError, "navigation omits evidence"):
            self.audit(navigation=navigation)

    def test_navigation_enforces_step_budget(self):
        navigation = deepcopy(self.navigation)
        navigation["C01"] *= 3
        with self.assertRaisesRegex(ValueError, "navigation exceeds tool/step caps"):
            self.audit(navigation=navigation)
