"""A frozen revision imports verified responses without changing its predecessor."""

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


class RevisionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [sample_case(i) for i in range(3)]
        self.manifest = benchmark.build_manifest(self.cases)
        self.cell = self.manifest["cells"][0]
        self.prompt = prompts.render_prompt(
            next(c for c in self.cases if c["id"] == self.cell["case"]), self.cell["axis"])

    def prepare(self, source, target):
        fixture_bytes = json.dumps(self.cases).encode()
        old = {**self.manifest, "inputs": {"fixtures.json": benchmark.digest(fixture_bytes),
                                            "benchmark.py": benchmark.digest(b"prior-runner")}}
        target_manifest = {**self.manifest, "inputs": {"fixtures.json": benchmark.digest(fixture_bytes),
                                                        "benchmark.py": benchmark.digest(b"new-runner")}}
        (source / "fixtures.json").write_bytes(fixture_bytes)
        (source / "benchmark.py").write_text("prior-runner")
        (source / "manifest.json").write_text(json.dumps(old))
        (target / "cost-resolution.json").write_text(json.dumps({
            "source_manifest_sha256": benchmark.digest((source / "manifest.json").read_bytes()),
            "items": {}}))
        (source / "attempts").mkdir()
        (source / "results").mkdir()
        (target / "attempts").mkdir()
        (target / "results").mkdir()
        export = sample_export(self.prompt, self.cell["model"], 0)
        export["info"]["id"] = "ses_verified"
        result = {"cell_id": self.cell["id"], "case": self.cell["case"],
                  "axis": self.cell["axis"], "repeat": self.cell["repeat"],
                  "model": self.cell["model"], "number": 1,
                  "session": "ses_verified", "status": "succeeded", "cost_usd": 0,
                  "used_model": benchmark.expected_identity(self.cell["model"]),
                  "tokens": export["info"]["tokens"],
                  "prompt": self.prompt, "answer": "No supported findings",
                  "prompt_sha256": self.manifest["prompt_hashes"][
                      f'{self.cell["case"]}:{self.cell["axis"]}']}
        data = json.dumps(result).encode()
        (source / "attempts" / f'{self.cell["id"]}-1.json').write_bytes(data)
        (source / "results" / f'{self.cell["id"]}.json').write_bytes(data)
        return old, target_manifest, export, data

    def test_verifies_session_and_copies_prior_bytes_once(self):
        migration = importlib.import_module("migrate_revision")
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            source, target = Path(src), Path(dst)
            old, new, export, data = self.prepare(source, target)
            summary = migration.migrate_revision(source, target, self.cases, new,
                                                 lambda _: export)
            self.assertEqual(summary["valid_results"], 1)
            self.assertEqual(summary["attempts"], 1)
            self.assertEqual((target / "results" / f'{self.cell["id"]}.json').read_bytes(), data)
            self.assertEqual((target / "attempts" / f'{self.cell["id"]}-1.json').read_bytes(), data)
            self.assertNotIn(self.cell, benchmark.pending_cells(new, target))
            with self.assertRaises(FileExistsError):
                migration.migrate_revision(source, target, self.cases, new, lambda _: export)

    def test_refuses_inflight_source_or_changed_prompt_before_writing(self):
        migration = importlib.import_module("migrate_revision")
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            source, target = Path(src), Path(dst)
            old, new, export, _ = self.prepare(source, target)
            marker = source / "attempts" / f'{self.cell["id"]}-2.started'
            marker.write_text("in flight")
            with self.assertRaisesRegex(ValueError, "running|in-flight"):
                migration.migrate_revision(source, target, self.cases, new, lambda _: export)
            marker.unlink()
            new["prompt_hashes"] = {**new["prompt_hashes"],
                                    f'{self.cell["case"]}:{self.cell["axis"]}': "changed"}
            with self.assertRaisesRegex(ValueError, "source|lineage|prompt"):
                migration.migrate_revision(source, target, self.cases, new, lambda _: export)
            self.assertFalse((target / "migration.json").exists())
            self.assertEqual(list((target / "results").glob("*.json")), [])

    def test_refuses_cost_resolution_for_a_different_source_manifest(self):
        migration = importlib.import_module("migrate_revision")
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            source, target = Path(src), Path(dst)
            _, new, export, _ = self.prepare(source, target)
            (target / "cost-resolution.json").write_text(json.dumps({
                "source_manifest_sha256": "different-run", "items": {}}))
            with self.assertRaisesRegex(ValueError, "resolution|lineage"):
                migration.migrate_revision(source, target, self.cases, new, lambda _: export)
            self.assertFalse((target / "migration.json").exists())


if __name__ == "__main__":
    unittest.main()
