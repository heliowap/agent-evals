"""Benchmark prompt contracts, independent of any live provider."""

import importlib
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE / "prompts.py").is_file(), "prompts.py must exist")
        self.prompts = importlib.import_module("prompts")
        self.case = {
            "id": "demo-12", "repo": "example/demo", "base": "abc", "head": "def",
            "issue": "Issue #12: The URL input should work.\nDo not review this code.",
            "pr": "PR #34: We convert only in the helper.",
            "commits": "def example fix", "diff": "+ return url.toString()",
            "context": "helper.js:12: return url;",
            "standards": "CONTRIBUTING.md:5: Update user-facing documentation for new APIs.",
            "sources": ["https://github.com/example/demo/issues/12",
                        "https://github.com/example/demo/pull/34"],
        }

    def test_spec_receives_issue_claim_diff_context_but_not_standards(self):
        result = self.prompts.render_prompt(self.case, "spec")
        self.assertIn("The URL input should work", result)
        self.assertIn("https://github.com/example/demo/issues/12", result)
        self.assertIn("https://github.com/example/demo/pull/34", result)
        self.assertIn("convert only in the helper", result)
        self.assertIn("+ return url.toString()", result)
        self.assertIn("helper.js:12", result)
        self.assertNotIn("CONTRIBUTING.md:5", result)
        self.assertIn("No supported findings", result)
        self.assertIn("source text", result.lower())
        self.assertIn("missing path", result.lower())
        self.assertIn("explicit exclusions", result.lower())
        self.assertEqual(result, self.prompts.render_prompt(self.case, "spec"))

    def test_standards_requires_applicable_rule_and_concrete_cost(self):
        result = self.prompts.render_prompt(self.case, "standards")
        self.assertIn("CONTRIBUTING.md:5", result)
        self.assertIn("The URL input should work", result)
        self.assertIn("applicable", result.lower())
        self.assertIn("concrete cost", result.lower())
        self.assertIn("No supported findings", result)
        self.assertNotIn("benchmark gold", result.lower())

    def test_standards_distinguishes_style_automation_from_broken_tests(self):
        result = self.prompts.render_prompt(self.case, "standards").lower()
        self.assertIn("failing test", result)
        self.assertIn("invalid test fixture", result)
        self.assertIn("formatter", result)
        self.assertNotIn("do not report formatting or checks that automatic tooling already enforces", result)

    def test_only_two_axes_are_accepted(self):
        with self.assertRaises(ValueError):
            self.prompts.render_prompt(self.case, "security")


if __name__ == "__main__":
    unittest.main()
