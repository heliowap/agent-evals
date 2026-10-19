import json
import tempfile
import unittest
from pathlib import Path

from summarize_pilot import summarize


class SummaryTest(unittest.TestCase):
    def test_incomplete_score_is_not_reported_and_missing_cost_is_preserved(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp/opencode") as directory:
            job = Path(directory)
            for index, error in enumerate((None, {"exception_type": "VerifierError"})):
                trial = job / str(index)
                trial.mkdir()
                (trial / "result.json").write_text(json.dumps({
                    "task_name": "fixture", "started_at": "2026-10-06T00:00:00+00:00",
                    "finished_at": "2026-10-06T00:01:00+00:00",
                    "config": {"agent": {"model_name": "opencode-go/glm-5.3-flash", "kwargs": {"variant": "high"}}},
                    "verifier_result": {"rewards": {"reward": 1}}, "exception_info": error,
                    "agent_result": {"cost_usd": None},
                }))
            result = summarize(job)
            glm = result["models"][0]
            self.assertEqual(glm["finished"], 2)
            self.assertEqual(glm["passed"], 1)
            self.assertEqual(glm["errors"], 1)
            self.assertIsNone(glm["accuracy"])
            self.assertIsNone(glm["reported_cost_usd"])
            self.assertEqual(glm["cost_coverage"], 0)
            self.assertTrue((job / "comparison.md").exists())


if __name__ == "__main__":
    unittest.main()
