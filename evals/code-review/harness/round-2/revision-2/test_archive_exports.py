"""Saved evidence can replay export validation without saving private reasoning."""

import importlib
import json
import sys
import unittest
from pathlib import Path

from test_benchmark import sample_export


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
benchmark = importlib.import_module("benchmark")


class ArchiveExportsTests(unittest.TestCase):
    def test_replays_exact_session_without_reasoning_text(self):
        archiver = importlib.import_module("archive_exports")
        prompt = "Review pinned patch only"
        export = sample_export(prompt)
        result = {"cell_id": "example-spec-m01-r1", "prompt": prompt,
                  "model": "openai/gpt-6-sol#high", "session": "ses_example",
                  "answer": "No supported findings", "used_model": export["info"]["model"],
                  "tokens": export["info"]["tokens"], "cost_usd": 0}
        records = archiver.archive_valid_results([result], lambda _: export)
        self.assertEqual(set(records), {result["cell_id"]})
        transcript = records[result["cell_id"]]["transcript"]
        self.assertNotIn("private", json.dumps(records))
        self.assertEqual([p["type"] for p in transcript["messages"][2]["content"]], ["reasoning", "text"])
        self.assertEqual(benchmark.validate_export(transcript, prompt, result["model"])["answer"], result["answer"])
        self.assertEqual(records[result["cell_id"]]["source_export_sha256"],
                         benchmark.digest(json.dumps(export, sort_keys=True, ensure_ascii=False).encode()))

    def test_rejects_mismatch_and_preserves_unexpected_part_type(self):
        archiver = importlib.import_module("archive_exports")
        export = sample_export("same prompt")
        result = {"cell_id": "example", "prompt": "same prompt", "model": "openai/gpt-6-sol#high",
                  "session": "ses_example", "answer": "different answer", "used_model": export["info"]["model"],
                  "tokens": export["info"]["tokens"], "cost_usd": 0}
        with self.assertRaisesRegex(ValueError, "result|answer"):
            archiver.archive_valid_results([result], lambda _: export)
        export["messages"][2]["content"].append({"type": "tool", "name": "read", "secret": "opaque"})
        result["answer"] = "No supported findings"
        with self.assertRaisesRegex(ValueError, "tool"):
            archiver.archive_valid_results([result], lambda _: export)


if __name__ == "__main__":
    unittest.main()
