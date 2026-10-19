"""A session-exported charge can unblock only its exact excluded attempt."""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from test_benchmark import sample_case, sample_export


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
benchmark = importlib.import_module("benchmark")
prompts = importlib.import_module("prompts")


class CostReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [sample_case(i) for i in range(3)]
        self.manifest = benchmark.build_manifest(self.cases)
        self.cell = next(c for c in self.manifest["cells"] if c["model"].startswith("openrouter/"))
        self.prompt = prompts.render_prompt(
            next(c for c in self.cases if c["id"] == self.cell["case"]), self.cell["axis"])
        self.attempt_name = f'{self.cell["id"]}-1.json'

    def test_exact_exported_charge_is_counted_but_unverified_or_changed_charge_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "fixtures.json").write_text(json.dumps(self.cases))
            (root / "manifest.json").write_text(json.dumps(self.manifest))
            attempt_path = root / "attempts" / self.attempt_name
            attempt_path.write_text(json.dumps({"cell_id": self.cell["id"],
                                                "model": self.cell["model"], "number": 1,
                                                "status": "excluded", "session": None,
                                                "cost_usd": None,
                                                "prompt_sha256": self.manifest["prompt_hashes"][
                                                    f'{self.cell["case"]}:{self.cell["axis"]}']}))
            with self.assertRaisesRegex(ValueError, "unknown"):
                benchmark.openrouter_spend(root)
            evidence = sample_export(self.prompt, self.cell["model"], 0.00106231)
            evidence["info"]["id"] = "ses_recovered"
            evidence["messages"][2]["content"] = []  # Finished without a review answer.
            evidence_path = root / "cost-evidence.json"
            evidence_path.write_text(json.dumps(evidence))
            resolution_path = root / "cost-resolution.json"
            resolution = {"items": {self.attempt_name: {
                "attempt_sha256": benchmark.digest(attempt_path.read_bytes()),
                "export_sha256": benchmark.digest(evidence_path.read_bytes()),
                "session_id": "ses_recovered", "cost_usd": 0.00106231}}}
            resolution_path.write_text(json.dumps(resolution))
            self.assertAlmostEqual(benchmark.openrouter_spend(root), 0.00106231)
            for edit in (lambda: attempt_path.write_text(attempt_path.read_text() + "\n"),
                         lambda: resolution_path.write_text(resolution_path.read_text().replace("0.00106231", "0.00001")),
                         lambda: evidence_path.write_text(evidence_path.read_text().replace("benchmark-review", "build"))):
                with self.subTest(edit=edit):
                    original = [p.read_bytes() for p in (attempt_path, resolution_path, evidence_path)]
                    edit()
                    with self.assertRaisesRegex(ValueError, "unknown|resolution|evidence"):
                        benchmark.openrouter_spend(root)
                    for p, data in zip((attempt_path, resolution_path, evidence_path), original):
                        p.write_bytes(data)

    def test_evidence_from_wrong_prompt_or_tool_using_session_never_releases_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "fixtures.json").write_text(json.dumps(self.cases))
            (root / "manifest.json").write_text(json.dumps(self.manifest))
            attempt_path = root / "attempts" / self.attempt_name
            attempt_path.write_text(json.dumps({"cell_id": self.cell["id"],
                                                "model": self.cell["model"], "number": 1,
                                                "status": "excluded", "session": None, "cost_usd": None,
                                                "prompt_sha256": self.manifest["prompt_hashes"][
                                                    f'{self.cell["case"]}:{self.cell["axis"]}']}))
            for contaminator in (lambda x: x["messages"][1].__setitem__("text", json.dumps("wrong prompt")),
                                  lambda x: x["messages"][2]["content"].append({"type": "tool", "name": "read"})):
                with self.subTest(contaminator=contaminator):
                    evidence = sample_export(self.prompt, self.cell["model"], 0.00106231)
                    evidence["info"]["id"] = "ses_recovered"
                    evidence["messages"][2]["content"] = []
                    contaminator(evidence)
                    evidence_path = root / "cost-evidence.json"
                    evidence_path.write_text(json.dumps(evidence))
                    (root / "cost-resolution.json").write_text(json.dumps({"items": {self.attempt_name: {
                        "attempt_sha256": benchmark.digest(attempt_path.read_bytes()),
                        "export_sha256": benchmark.digest(evidence_path.read_bytes()),
                        "session_id": "ses_recovered", "cost_usd": 0.00106231}}}))
                    with self.assertRaisesRegex(ValueError, "evidence|prompt|tool"):
                        benchmark.openrouter_spend(root)


if __name__ == "__main__":
    unittest.main()
