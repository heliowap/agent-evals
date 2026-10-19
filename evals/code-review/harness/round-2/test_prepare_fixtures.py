"""Fixture assembly must preserve pinned, neutral primary-source excerpts."""

import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class FixturePreparationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE / "prepare_fixtures.py").is_file(), "prepare_fixtures.py must exist")
        self.module = importlib.import_module("prepare_fixtures")

    def test_excerpt_numbers_exact_pinned_source_lines(self):
        self.assertEqual(self.module.excerpt("alpha\nbeta\ngamma\n", 2, 3), "2: beta\n3: gamma")
        with self.assertRaises(ValueError):
            self.module.excerpt("alpha\n", 2, 3)

    def test_github_api_fetch_uses_authenticated_cli(self):
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
                ["gh"], 0, stdout='{"sha":"pinned"}', stderr="")) as call:
            self.assertEqual(self.module.fetch_text("https://api.github.com/repos/example/demo/compare/a...b"),
                             '{"sha":"pinned"}')
        args, kwargs = call.call_args
        self.assertEqual(args[0][:2], ["gh", "api"])
        self.assertEqual(args[0][2], "repos/example/demo/compare/a...b")
        self.assertTrue(kwargs.get("check"))

    def test_assemble_uses_verbatim_issue_pr_diff_and_head_context(self):
        base, head = "a" * 40, "b" * 40
        spec = {"id": "demo", "repo": "example/demo", "base": base, "head": head,
                "issue_number": 5, "pr_number": 7,
                "issue_slice": ["### Problem", "### Metadata"],
                "pr_slice": ["## Goal", "## Internal"],
                "context": [["src/file.js", 2, 3]],
                "standards": [["CONTRIBUTING.md", 1, 2]]}
        compare = {"base_commit": {"sha": base}, "merge_base_commit": {"sha": base},
                   "commits": [{"sha": head, "commit": {"message": "Fix issue"}}]}
        root = "https://api.github.com/repos/example/demo"
        urls = {
            f"{root}/compare/{base}...{head}": json.dumps(compare),
            f"{root}/issues/5": json.dumps({"body": "### Problem\nA URL breaks\n### Metadata\nother"}),
            f"{root}/pulls/7": json.dumps({"body": "## Goal\nHandle the URL\n## Internal\nother"}),
            f"https://github.com/example/demo/compare/{base}...{head}.diff": "diff --git a/src/file.js b/src/file.js\n+ fix\n",
            f"https://raw.githubusercontent.com/example/demo/{head}/src/file.js": "one\ntwo\nthree\n",
            f"https://raw.githubusercontent.com/example/demo/{head}/CONTRIBUTING.md": "rule\nmore rule\n",
        }
        case = self.module.assemble(spec, urls.__getitem__)
        self.assertEqual(case["issue"], "### Problem\nA URL breaks\n")
        self.assertEqual(case["pr"], "## Goal\nHandle the URL\n")
        self.assertEqual(case["diff"], urls[f"https://github.com/example/demo/compare/{base}...{head}.diff"])
        self.assertIn("src/file.js (lines 2-3):\n2: two\n3: three", case["context"])
        self.assertIn("CONTRIBUTING.md (lines 1-2):\n1: rule\n2: more rule", case["standards"])
        self.assertIn("Fix issue", case["commits"])
        self.assertTrue(all(u.startswith("https://github.com/") for u in case["sources"]))
        bad = dict(urls)
        bad[f"{root}/compare/{base}...{head}"] = json.dumps({**compare, "merge_base_commit": {"sha": "wrong"}})
        with self.assertRaisesRegex(ValueError, "base"):
            self.module.assemble(spec, bad.__getitem__)

    def test_author_title_can_be_the_only_pr_claim_for_non_english_body(self):
        base, head = "a" * 40, "b" * 40
        spec = {"id": "demo", "repo": "example/demo", "base": base, "head": head,
                "issue_number": 5, "pr_number": 7,
                "issue_slice": ["Issue goal", None], "pr_title_only": True,
                "context": [["code.py", 1, 1]], "standards": [["rules.rst", 1, 1]],
                "external_standards": [{"url": "https://docs.pytest.org/en/8.4.x/explanation/goodpractices.html",
                                        "quote": "search for `test_*.py` or `*_test.py` files"}]}
        api = f"https://api.github.com/repos/{spec['repo']}"
        fetch = {
            f"{api}/compare/{base}...{head}": json.dumps({"base_commit": {"sha": base},
                "merge_base_commit": {"sha": base},
                "commits": [{"sha": head, "commit": {"message": "Fix"}}]}),
            f"{api}/issues/5": json.dumps({"body": "Issue goal"}),
            f"{api}/pulls/7": json.dumps({"title": "Preserve digest URI", "body": "非英语原文"}),
            f"https://github.com/example/demo/compare/{base}...{head}.diff": "diff --git a/code.py b/code.py\n+line",
            f"https://raw.githubusercontent.com/example/demo/{head}/code.py": "line",
            f"https://raw.githubusercontent.com/example/demo/{head}/rules.rst": "rule",
        }
        result = self.module.assemble(spec, fetch.__getitem__)
        self.assertEqual(result["pr"], "Preserve digest URI")
        self.assertIn("search for `test_*.py` or `*_test.py` files", result["standards"])
        self.assertIn("https://docs.pytest.org/en/8.4.x/explanation/goodpractices.html", result["sources"])


if __name__ == "__main__":
    unittest.main()
