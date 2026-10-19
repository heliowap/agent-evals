"""Blind grading must be complete and auditable before model identities join it."""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module("summarize")
        self.packets = [
            {"blind_id": "b0001", "case": "example", "axis": "spec",
             "answer": "The branch returns URL before conversion, breaking baseURL. Typings still reject URL."},
            {"blind_id": "b0002", "case": "example", "axis": "spec",
             "answer": "No supported findings"},
        ]
        self.decisions = {"case": "example", "axis": "spec", "decisions": [
            {"blind_id": "b0001", "target_hit": True,
             "target_quote": "breaking baseURL", "target_reason": "Cites path, mechanism, effect",
             "additional_claims": [{"quote": "Typings still reject URL", "category": "valid_extra",
                                    "evidence": "example/index.d.ts:13 requires string"}]},
            {"blind_id": "b0002", "target_hit": False,
             "target_quote": None, "target_reason": "No finding",
             "additional_claims": []},
        ]}

    def test_rejects_missing_duplicate_and_unanchored_blind_decisions(self):
        decisions = self.module.validate_group(self.packets, self.decisions)
        self.assertEqual(set(decisions), {"b0001", "b0002"})
        bad = {**self.decisions, "decisions": [self.decisions["decisions"][0]]}
        with self.assertRaisesRegex(ValueError, "missing"):
            self.module.validate_group(self.packets, bad)
        bad = {**self.decisions, "decisions": [self.decisions["decisions"][0]] * 2}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.module.validate_group(self.packets, bad)
        wrong = dict(self.decisions["decisions"][0], target_quote="hallucinated quote")
        bad = {**self.decisions, "decisions": [wrong, self.decisions["decisions"][1]]}
        with self.assertRaisesRegex(ValueError, "quote"):
            self.module.validate_group(self.packets, bad)

    def test_requires_evidence_before_a_refuted_claim_can_be_counted(self):
        wrong = {**self.decisions["decisions"][0], "additional_claims": [
            {"quote": "Typings still reject URL", "category": "refuted", "evidence": ""}]}
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.module.validate_group(self.packets, {**self.decisions,
                                                       "decisions": [wrong, self.decisions["decisions"][1]]})

    def test_does_not_silently_drop_or_double_count_additional_claims(self):
        omitted = {key: value for key, value in self.decisions["decisions"][0].items()
                   if key != "additional_claims"}
        with self.assertRaisesRegex(ValueError, "claim"):
            self.module.validate_group(self.packets, {**self.decisions,
                                                       "decisions": [omitted, self.decisions["decisions"][1]]})
        repeated = {**self.decisions["decisions"][0], "additional_claims":
                    self.decisions["decisions"][0]["additional_claims"] * 2}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.module.validate_group(self.packets, {**self.decisions,
                                                       "decisions": [repeated, self.decisions["decisions"][1]]})

    def test_joins_identities_only_after_complete_blind_validation(self):
        decisions = self.module.validate_group(self.packets, self.decisions)
        mapping = {"b0001": "cell-a", "b0002": "cell-b"}
        cells = [{"id": "cell-a", "case": "example", "axis": "spec", "repeat": 1, "model": "route/a"},
                 {"id": "cell-b", "case": "example", "axis": "spec", "repeat": 2, "model": "route/a"}]
        results = {"cell-a": {"session": "ses_a", "elapsed_seconds": 10, "cost_usd": 0,
                              "model": "route/a", "case": "example", "axis": "spec", "repeat": 1},
                   "cell-b": {"session": "ses_b", "elapsed_seconds": 30, "cost_usd": 0,
                              "model": "route/a", "case": "example", "axis": "spec", "repeat": 2}}
        results["cell-a"]["answer"] = self.packets[0]["answer"]
        results["cell-b"]["answer"] = self.packets[1]["answer"]
        joined = self.module.join_validated(decisions, mapping, cells, results, self.packets)
        self.assertEqual(len(joined), 2)
        summary = self.module.summarize_models(joined)
        self.assertEqual(summary["route/a"]["spec_hits"], 1)
        self.assertEqual(summary["route/a"]["median_seconds"], 20)
        self.assertEqual(summary["route/a"]["valid_extras"], 1)
        self.assertEqual(summary["route/a"]["refuted_claims"], 0)
        with self.assertRaisesRegex(ValueError, "missing"):
            self.module.join_validated(decisions, {"b0001": "cell-a"}, cells, results, self.packets)

    def test_refuses_packet_mapped_to_a_different_answer_or_axis(self):
        decisions = self.module.validate_group(self.packets, self.decisions)
        cells = [{"id": "cell-a", "case": "example", "axis": "spec", "repeat": 1, "model": "route/a"},
                 {"id": "cell-b", "case": "example", "axis": "spec", "repeat": 2, "model": "route/a"}]
        results = {cell["id"]: {**cell, "answer": answer, "session": cell["id"],
                                "elapsed_seconds": 1, "cost_usd": 0}
                   for cell, answer in zip(cells, (p["answer"] for p in self.packets))}
        with self.assertRaisesRegex(ValueError, "answer|packet"):
            self.module.join_validated(decisions, {"b0001": "cell-b", "b0002": "cell-a"},
                                       cells, results, self.packets)
        altered = [{**self.packets[0], "axis": "standards"}, self.packets[1]]
        with self.assertRaisesRegex(ValueError, "axis|packet"):
            self.module.join_validated(decisions, {"b0001": "cell-a", "b0002": "cell-b"},
                                       cells, results, altered)

    def test_blind_seal_freezes_decisions_before_identity_join(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "blind-groups").mkdir()
            (root / "adjudication-groups").mkdir()
            (root / "blind-answers.json").write_text(json.dumps({"partial": False, "answers": self.packets}))
            name = "example-spec.json"
            (root / "blind-groups" / name).write_text(json.dumps(self.packets))
            decision_path = root / "adjudication-groups" / name
            decision_path.write_text(json.dumps(self.decisions))
            self.module.freeze_blind_grades(root)
            self.module.verify_blind_seal(root)
            decision_path.write_text(json.dumps({**self.decisions, "decisions": list(reversed(self.decisions["decisions"]))}))
            with self.assertRaisesRegex(ValueError, "seal"):
                self.module.verify_blind_seal(root)
            decision_path.write_text(json.dumps(self.decisions))
            (root / "blind-groups" / name).write_text(json.dumps(list(reversed(self.packets))))
            with self.assertRaisesRegex(ValueError, "seal"):
                self.module.verify_blind_seal(root)

    def test_report_distinguishes_complete_coverage_from_provider_cost(self):
        models = {"route/a": {"standards_hits": 1, "spec_hits": 0,
                              "refuted_claims": 0, "valid_extras": 0, "inconclusive": 1,
                              "median_seconds": 10, "iqr_seconds": [8, 12],
                              "reported_valid_cost_usd": 0}}
        joined = [{"case": "example", "axis": "standards", "target_hit": True,
                   "additional_claims": [{"category": "inconclusive"}]}]
        report = self.module.render_report(joined, models, {"models": ["route/a"]}, 0.12,
                                           [{"status": "succeeded"}],
                                           {"breaches": 0, "over_400": 0, "maximum": 4, "by_model": {}})
        self.assertIn("0 células faltantes", report)
        self.assertIn("US$ 0,12000 informados pelo OpenRouter", report)
        self.assertIn("não demonstra custo real nulo", report)

    def test_under_400_word_requirement_counts_the_boundary_as_a_breach(self):
        rows = [{"model": "route/a", "answer": "word " * n} for n in (399, 400, 401)]
        rows += [{"model": "route/b", "answer": "word " * 401}]
        self.assertEqual(self.module.word_limit_stats(rows),
                         {"breaches": 3, "over_400": 2, "maximum": 401,
                          "by_model": {"route/a": 2, "route/b": 1}})


if __name__ == "__main__":
    unittest.main()
