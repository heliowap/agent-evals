"""A corrected validator can reuse prior sessions only with full revalidation."""

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


class PreflightImportTests(unittest.TestCase):
    def test_revalidates_sessions_promotes_only_first_and_preserves_duplicate_cost(self):
        migration = importlib.import_module("import_preflight")
        cases = [sample_case(i) for i in range(3)]
        manifest = benchmark.build_manifest(cases)
        manifest["inputs"] = {"fixtures.json": "same", "prompts.py": "same",
                              "grading-rubric.md": "same", "benchmark.py": "new"}
        old = json.loads(json.dumps(manifest))
        old["inputs"]["benchmark.py"] = "old"
        cell = manifest["cells"][0]
        prompt = prompts.render_prompt(next(c for c in cases if c["id"] == cell["case"]), cell["axis"])
        phash = manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}']
        sessions = {"ses_first": sample_export(prompt, cell["model"], 0),
                    "ses_surplus": sample_export(prompt, cell["model"], 0)}
        for sid, export in sessions.items():
            export["info"]["id"] = sid
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            source, target = Path(source), Path(target)
            (source / "attempts").mkdir()
            (source / "results").mkdir()
            (source / "manifest.json").write_text(json.dumps(old))
            for number, sid in enumerate(sessions, 1):
                (source / "attempts" / f'{cell["id"]}-{number}.json').write_text(json.dumps({
                    "cell_id": cell["id"], "model": cell["model"], "number": number,
                    "session": sid, "cost_usd": 0, "elapsed_seconds": 4,
                    "status": "excluded", "error": "exported prompt cannot be decoded",
                    "prompt_sha256": phash}))
            record = migration.import_preflight(source, target, cases, manifest, sessions.__getitem__)
            self.assertEqual(record["promoted"], [cell["id"]])
            self.assertEqual(record["duplicates"], ["ses_surplus"])
            result = json.loads((target / "results" / f'{cell["id"]}.json').read_text())
            self.assertEqual(result["session"], "ses_first")
            self.assertEqual(result["prompt"], prompt)
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["source_original_status"], "excluded")
            duplicate = json.loads((target / "attempts" / f'{cell["id"]}-2.json').read_text())
            self.assertEqual(duplicate["status"], "excluded")
            self.assertEqual(duplicate["session"], "ses_surplus")
            self.assertEqual(duplicate["cost_usd"], 0)
            self.assertNotIn(cell, benchmark.pending_cells(manifest, target))
            with self.assertRaisesRegex(FileExistsError, "File exists"):
                migration.import_preflight(source, target, cases, manifest, sessions.__getitem__)

    def test_refuses_changed_prompt_before_importing_any_result(self):
        migration = importlib.import_module("import_preflight")
        cases = [sample_case(i) for i in range(3)]
        manifest = benchmark.build_manifest(cases)
        manifest["inputs"] = {"fixtures.json": "same", "prompts.py": "new", "benchmark.py": "new"}
        old = json.loads(json.dumps(manifest))
        old["inputs"]["prompts.py"] = "old"
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            source, target = Path(source), Path(target)
            (source / "manifest.json").write_text(json.dumps(old))
            with self.assertRaisesRegex(ValueError, "source|prompt|lineage"):
                migration.import_preflight(source, target, cases, manifest,
                                           lambda _: self.fail("must not export any session"))
            self.assertFalse((target / "results").exists())


if __name__ == "__main__":
    unittest.main()
