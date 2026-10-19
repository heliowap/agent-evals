"""Behavioral checks for the frozen, resumable review run."""

import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def sample_case(n):
    return {
        "id": f"repo-{n}", "repo": f"example/repo-{n}", "base": "aaa", "head": "bbb",
        "issue": "Fix observed behavior", "pr": "This change fixes it",
        "commits": "bbb fix", "diff": "+ fix", "context": "file:1: context",
        "standards": "CONTRIBUTING.md:1: Add a focused test",
        "sources": [f"https://github.com/example/repo-{n}/issues/1",
                    f"https://github.com/example/repo-{n}/pull/2"],
    }


def sample_export(prompt, model="openai/gpt-6-sol#high", cost=0):
    provider, variant = model.split("#") if "#" in model else (model, "default")
    provider, model_id = provider.split("/", 1)
    identity = {"providerID": provider, "id": model_id, "variant": variant}
    return {
        "info": {"id": "ses_example", "outcome": "succeeded", "model": identity,
                 "agent": "benchmark-review", "cost": cost, "tokens": {"input": 123, "output": 12}},
        "messages": [
            {"type": "agent-switched", "agent": "benchmark-review", "previous": "benchmark-review"},
            {"type": "user", "text": json.dumps(prompt).replace("\\n", "\n")},
            {"type": "assistant", "agent": "benchmark-review", "model": identity, "finish": "stop",
             "content": [{"type": "reasoning", "text": "private"},
                         {"type": "text", "text": "No supported findings"}]},
            {"type": "idle", "outcome": "succeeded"},
        ],
    }


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE / "benchmark.py").is_file(), "benchmark.py must exist")
        self.benchmark = importlib.import_module("benchmark")
        self.cases = [sample_case(n) for n in range(3)]

    def test_manifest_has_300_distinct_cells_and_two_identical_prompts_per_axis(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cells = manifest["cells"]
        self.assertEqual(len(self.benchmark.MODELS), 25)
        self.assertEqual(len(set(self.benchmark.MODELS)), 25)
        self.assertEqual(self.benchmark.MODELS[-1], "openrouter/xiaomi/mimo-v2.6-flash#none")
        self.assertEqual(len(cells), 300)
        self.assertEqual(len({cell["id"] for cell in cells}), 300)
        self.assertEqual({cell["repeat"] for cell in cells}, {1, 2})
        self.assertEqual(len(manifest["prompt_hashes"]), 6)
        self.assertEqual(manifest.get("route_prices_usd_per_million"), {
            "openrouter/z-ai/glm-5.3-flash": {"input": 0.04, "output": 0.5},
            "openrouter/deepseek/deepseek-v4.1-flash": {"input": 0.3, "output": 1.2},
            "openrouter/xiaomi/mimo-v2.6-flash": {"input": 0.14, "output": 0.28},
        })
        self.assertEqual([cell["id"] for cell in cells],
                         [cell["id"] for cell in self.benchmark.build_manifest(self.cases, 20260926)["cells"]])
        self.assertNotEqual([cell["id"] for cell in cells],
                            [cell["id"] for cell in self.benchmark.build_manifest(self.cases, 4)["cells"]])

    def test_freeze_rejects_incomplete_or_unpinned_source_material(self):
        cases = [
            {**case, "base": "a" * 40, "head": "b" * 40,
             "diff": "diff --git a/file b/file\n+ fix", "sources": ["https://github.com/example/issues/1"]}
            for case in self.cases
        ]
        self.benchmark.validate_fixtures(cases)
        cases[2]["sources"].append("https://docs.pytest.org/en/8.4.x/explanation/goodpractices.html")
        self.benchmark.validate_fixtures(cases)
        cases[0]["standards"] = ""
        with self.assertRaisesRegex(ValueError, "standards"):
            self.benchmark.validate_fixtures(cases)
        cases[0]["standards"] = "CONTRIBUTING.md:1: Add a focused test"
        cases[1]["head"] = "short"
        with self.assertRaisesRegex(ValueError, "head"):
            self.benchmark.validate_fixtures(cases)

    def test_freeze_refuses_draft_or_missing_case_rubric(self):
        cases = [{**case, "head": char * 40} for case, char in zip(self.cases, "abc")]
        rubric = "# Gabarito — RASCUNHO\n" + "\n".join(
            f"## {case['id']} {case['head']}\n*Spec* target\n*Standards* target"
            for case in cases)
        with self.assertRaisesRegex(ValueError, "draft"):
            self.benchmark.validate_rubric(cases, rubric)
        rubric = rubric.replace("RASCUNHO", "Congelado")
        self.benchmark.validate_rubric(cases, rubric)
        with self.assertRaisesRegex(ValueError, "missing"):
            self.benchmark.validate_rubric(cases, rubric.replace(cases[2]["head"], "wrong"))

    def test_manifest_input_hashes_include_runner_and_blind_adjudication(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("fixtures.json", "prompts.py", "grading-rubric.md", "benchmark.py",
                         "blind.py", "prepare_fixtures.py"):
                (root / name).write_text(name)
            hashes = self.benchmark.inputs(root)
            self.assertEqual(set(hashes), {"fixtures.json", "prompts.py", "grading-rubric.md",
                                           "benchmark.py", "blind.py", "prepare_fixtures.py"})
            self.assertEqual(len(set(hashes.values())), 6)

    def test_validator_checks_actual_user_prompt_and_identity(self):
        prompt = 'Review this\nquote "literal" and backslash \\.'
        result = self.benchmark.validate_export(sample_export(prompt), prompt,
                                                 "openai/gpt-6-sol#high")
        self.assertEqual(result["answer"], "No supported findings")
        self.assertEqual(result["session"], "ses_example")
        bad = sample_export(prompt)
        bad["messages"][1]["text"] = json.dumps(prompt + "\nUNWANTED STDIN")
        with self.assertRaisesRegex(ValueError, "prompt"):
            self.benchmark.validate_export(bad, prompt, "openai/gpt-6-sol#high")
        with self.assertRaisesRegex(ValueError, "model"):
            self.benchmark.validate_export(sample_export(prompt), prompt,
                                           "openai/gpt-6-sol#max")
        wrong_agent = sample_export(prompt)
        wrong_agent["info"]["agent"] = "build"
        with self.assertRaisesRegex(ValueError, "agent"):
            self.benchmark.validate_export(wrong_agent, prompt, "openai/gpt-6-sol#high")

    def test_validator_rejects_tool_empty_truncated_and_failed_sessions(self):
        prompt = "Review"
        for change in (lambda d: d["messages"][2]["content"].append({"type": "tool", "name": "read"}),
                       lambda d: d["messages"].insert(1, {"type": "tool", "name": "read"}),
                       lambda d: d["messages"][2]["content"].__setitem__(1, {"type": "text", "text": ""}),
                       lambda d: d["messages"][2].__setitem__("finish", "length"),
                       lambda d: d["info"].__setitem__("outcome", "error"),
                       lambda d: d["messages"][2].__setitem__("model", {"id": "gpt-6-sol", "providerID": "openai", "variant": "max"})):
            with self.subTest(change=change):
                data = sample_export(prompt)
                change(data)
                with self.assertRaises(ValueError):
                    self.benchmark.validate_export(data, prompt, "openai/gpt-6-sol#high")

    def test_agent_switch_event_is_allowed_only_for_the_frozen_reviewer(self):
        prompt = "Review"
        self.assertEqual(self.benchmark.validate_export(sample_export(prompt), prompt,
                                                         "openai/gpt-6-sol#high")["answer"],
                         "No supported findings")
        bad = sample_export(prompt)
        bad["messages"][0]["agent"] = "build"
        with self.assertRaisesRegex(ValueError, "agent"):
            self.benchmark.validate_export(bad, prompt, "openai/gpt-6-sol#high")

    def test_retry_resume_and_budget_include_rejected_attempts(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        first = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            (root / "attempts").mkdir()
            self.assertIn(first, self.benchmark.pending_cells(manifest, root))
            (root / "attempts" / f'{first["id"]}-1.json').write_text(json.dumps(
                {"cell_id": first["id"], "cost_usd": 0.2, "status": "excluded", "model": "openrouter/z-ai/glm-5.3-flash#high"}))
            self.assertIn(first, self.benchmark.pending_cells(manifest, root))
            (root / "attempts" / f'{first["id"]}-2.json').write_text(json.dumps(
                {"cell_id": first["id"], "cost_usd": 0, "status": "excluded", "model": "openrouter/z-ai/glm-5.3-flash#high"}))
            self.assertNotIn(first, self.benchmark.pending_cells(manifest, root))
            self.assertEqual(self.benchmark.openrouter_spend(root), 0.2)
            (root / "attempts" / "unknown-1.json").write_text(json.dumps(
                {"cell_id": "unknown", "cost_usd": None, "status": "excluded", "model": "openrouter/z-ai/glm-5.3-flash#high"}))
            with self.assertRaisesRegex(ValueError, "unknown"):
                self.benchmark.openrouter_spend(root)

    def test_missing_result_with_successful_attempt_is_an_integrity_error(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "attempts" / f'{cell["id"]}-1.json').write_text(json.dumps({
                "cell_id": cell["id"], "status": "succeeded", "session": "ses_orphan",
                "cost_usd": 0, "model": cell["model"]}))
            with self.assertRaisesRegex(ValueError, "successful attempt"):
                self.benchmark.pending_cells(manifest, root)

    def test_result_skips_only_when_its_cell_and_hash_match(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            (root / "attempts").mkdir()
            record = {"cell_id": cell["id"], "model": cell["model"], "case": cell["case"],
                      "axis": cell["axis"], "repeat": cell["repeat"],
                      "prompt_sha256": manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'],
                      "status": "succeeded", "session": "ses_example", "answer": "No supported findings",
                      "used_model": self.benchmark.expected_identity(cell["model"])}
            (root / "results" / f'{cell["id"]}.json').write_text(json.dumps(record))
            self.assertNotIn(cell, self.benchmark.pending_cells(manifest, root))
            record["prompt_sha256"] = "tampered"
            (root / "results" / f'{cell["id"]}.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "mismatch"):
                self.benchmark.pending_cells(manifest, root)

    def test_result_cannot_claim_the_wrong_axis_or_repetition(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            record = {"cell_id": cell["id"], "model": cell["model"], "case": cell["case"],
                      "axis": "spec" if cell["axis"] == "standards" else "standards",
                      "repeat": cell["repeat"],
                      "prompt_sha256": manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'],
                      "status": "succeeded", "session": "ses_example", "answer": "No supported findings",
                      "used_model": self.benchmark.expected_identity(cell["model"])}
            (root / "results" / f'{cell["id"]}.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "mismatch"):
                self.benchmark.pending_cells(manifest, root)

    def test_result_without_answer_or_actual_route_cannot_be_skipped(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            (root / "attempts").mkdir()
            record = {"cell_id": cell["id"], "model": cell["model"],
                      "prompt_sha256": manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'],
                      "status": "succeeded", "session": "ses_example", "answer": ""}
            (root / "results" / f'{cell["id"]}.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "mismatch"):
                self.benchmark.pending_cells(manifest, root)

    def test_stray_result_file_cannot_inflate_completion_count(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            (root / "attempts").mkdir()
            (root / "results" / "not-a-manifest-cell.json").write_text(json.dumps({
                "cell_id": "not-a-manifest-cell", "answer": "No supported findings"}))
            with self.assertRaisesRegex(ValueError, "unexpected result"):
                self.benchmark.pending_cells(manifest, root)

    def test_repetitions_cannot_share_an_exported_session(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cells = manifest["cells"][:2]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results").mkdir()
            (root / "attempts").mkdir()
            for cell in cells:
                record = {"cell_id": cell["id"], "model": cell["model"], "case": cell["case"],
                          "axis": cell["axis"], "repeat": cell["repeat"],
                          "prompt_sha256": manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'],
                          "status": "succeeded", "session": "ses_shared", "answer": "No supported findings",
                          "used_model": self.benchmark.expected_identity(cell["model"])}
                (root / "results" / f'{cell["id"]}.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "session"):
                self.benchmark.pending_cells(manifest, root)

    def test_live_review_reusing_a_previous_session_is_excluded(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "attempts" / "previous-1.json").write_text(json.dumps({
                "cell_id": "previous", "model": "openai/gpt-6-sol#high",
                "status": "succeeded", "session": "ses_shared", "cost_usd": 0}))
            review = {"session": "ses_shared", "answer": "No supported findings",
                      "used_model": self.benchmark.expected_identity(cell["model"]), "cost_usd": 0}
            with patch.object(self.benchmark, "run_review", return_value=review):
                self.benchmark.run_cell(cell, self.cases[int(cell["case"].rsplit("-", 1)[1])], manifest, root)
            self.assertFalse((root / "results" / f'{cell["id"]}.json').exists())
            self.assertEqual(json.loads((root / "attempts" / f'{cell["id"]}-1.json').read_text())["status"],
                             "excluded")

    def test_external_cli_receives_closed_stdin_and_export_is_verified(self):
        prompt = "Review\nDo not read stdin."
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            if argv[1] == "run":
                self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
                self.assertEqual(argv[-1], prompt)
                self.assertEqual(argv[argv.index("--agent") + 1], "benchmark-review")
                policy = json.loads((Path(kwargs["cwd"]) / ".opencode" / "opencode.json").read_text())
                deny = [{"action": "*", "resource": "*", "effect": "deny"}]
                self.assertEqual(policy["permissions"], deny)
                self.assertEqual(policy["agents"]["benchmark-review"]["permissions"], deny)
                self.assertEqual(policy["agents"]["benchmark-review"]["mode"], "primary")
                self.assertNotIn("permission", policy)
                self.assertNotIn("tools", policy)
                runtime = json.loads(kwargs["env"]["OPENCODE_CONFIG_CONTENT"])
                self.assertEqual(runtime["providers"]["example"]["models"], {"sample": {}})
                self.assertEqual(runtime["permissions"], deny)
                self.assertEqual(runtime["agents"]["benchmark-review"]["permissions"], deny)
                return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({
                    "type": "text", "sessionID": "ses_example",
                    "part": {"type": "text", "text": "No supported findings"}}) + "\n", stderr="")
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(sample_export(prompt)), stderr="")

        inherited = {"providers": {"example": {"models": {"sample": {}}}},
                     "permissions": [{"action": "*", "resource": "*", "effect": "allow"}]}
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"OPENCODE_CONFIG_CONTENT": json.dumps(inherited)}), patch.object(subprocess, "run", side_effect=fake_run):
            result = self.benchmark.run_review(prompt, "openai/gpt-6-sol#high", td, 30)
        self.assertEqual(result["answer"], "No supported findings")
        self.assertEqual(len(calls), 2)
        self.assertIn("--standalone", calls[1][0])

    def test_restart_after_crash_is_not_blocked_by_stale_lock_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".run.lock").write_text("pid=999999999\n")
            with self.benchmark.run_lock(root):
                self.assertTrue((root / ".run.lock").exists())

    def test_export_timeout_preserves_known_session_for_audit(self):
        def fake_run(argv, **kwargs):
            if argv[1] == "run":
                return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({
                    "type": "text", "sessionID": "ses_known",
                    "part": {"type": "text", "text": "No supported findings"}}), stderr="")
            raise subprocess.TimeoutExpired(argv, 30)

        with tempfile.TemporaryDirectory() as td, patch.object(subprocess, "run", side_effect=fake_run):
            with self.assertRaises(self.benchmark.RejectedReview) as caught:
                self.benchmark.run_review("Review", "openai/gpt-6-sol#high", td, 30)
        self.assertEqual(caught.exception.session, "ses_known")

    def test_exported_session_must_match_event_session_id(self):
        def fake_run(argv, **kwargs):
            if argv[1] == "run":
                return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({
                    "type": "text", "sessionID": "ses_expected",
                    "part": {"type": "text", "text": "No supported findings"}}), stderr="")
            export = sample_export("Review")
            export["info"]["id"] = "ses_other"
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(export), stderr="")

        with tempfile.TemporaryDirectory() as td, patch.object(subprocess, "run", side_effect=fake_run):
            with self.assertRaisesRegex(self.benchmark.RejectedReview, "session"):
                self.benchmark.run_review("Review", "openai/gpt-6-sol#high", td, 30)

    def test_cli_events_must_belong_to_one_session(self):
        prompt = "Review"
        events = [
            {"type": "text", "sessionID": "ses_expected", "part": {"type": "text", "text": "No supported findings"}},
            {"type": "text", "sessionID": "ses_other", "part": {"type": "text", "text": "No supported findings"}},
        ]
        def fake_run(argv, **kwargs):
            if argv[1] == "run":
                return subprocess.CompletedProcess(argv, 0, stdout="\n".join(json.dumps(e) for e in events), stderr="")
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(sample_export(prompt)), stderr="")
        with tempfile.TemporaryDirectory() as td, patch.object(subprocess, "run", side_effect=fake_run):
            with self.assertRaisesRegex(self.benchmark.RejectedReview, "multiple sessions"):
                self.benchmark.run_review(prompt, "openai/gpt-6-sol#high", td, 30)

    def test_interrupted_openrouter_call_records_unknown_charge_before_resume(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            marker = root / "attempts" / "repo-0-spec-m20-r1-1.started"
            marker.write_text(json.dumps({"cell_id": "repo-0-spec-m20-r1",
                                           "model": "openrouter/z-ai/glm-5.3-flash#high"}))
            self.benchmark.recover_interrupted(root)
            self.assertFalse(marker.exists())
            recovered = json.loads((root / "attempts" / "repo-0-spec-m20-r1-1.json").read_text())
            self.assertEqual(recovered["status"], "excluded")
            self.assertIsNone(recovered["cost_usd"])
            with self.assertRaisesRegex(ValueError, "unknown"):
                self.benchmark.openrouter_spend(root)

    def test_recovery_reconstructs_successful_second_attempt_result(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "results").mkdir()
            attempt = {"cell_id": cell["id"], "case": cell["case"], "axis": cell["axis"],
                       "repeat": cell["repeat"], "model": cell["model"], "number": 2,
                       "prompt_sha256": manifest["prompt_hashes"][f'{cell["case"]}:{cell["axis"]}'],
                       "status": "succeeded", "session": "ses_second", "answer": "No supported findings",
                       "used_model": self.benchmark.expected_identity(cell["model"]), "cost_usd": 0}
            (root / "attempts" / f'{cell["id"]}-1.json').write_text(json.dumps(
                {"cell_id": cell["id"], "model": cell["model"], "status": "excluded", "cost_usd": 0}))
            (root / "attempts" / f'{cell["id"]}-2.json').write_text(json.dumps(attempt))
            (root / "attempts" / f'{cell["id"]}-2.started').write_text(json.dumps(
                {"cell_id": cell["id"], "model": cell["model"]}))
            self.benchmark.recover_interrupted(root)
            self.assertEqual(json.loads((root / "results" / f'{cell["id"]}.json').read_text()), attempt)
            self.assertNotIn(cell, self.benchmark.pending_cells(manifest, root))

    def test_success_attempt_preserves_answer_for_interruption_recovery(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = manifest["cells"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            review = {"session": "ses_unique", "answer": "No supported findings",
                      "used_model": self.benchmark.expected_identity(cell["model"]), "cost_usd": 0}
            with patch.object(self.benchmark, "run_review", return_value=review):
                self.benchmark.run_cell(cell, self.cases[int(cell["case"].rsplit("-", 1)[1])], manifest, root)
            attempt = json.loads((root / "attempts" / f'{cell["id"]}-1.json').read_text())
            self.assertEqual(attempt.get("answer"), "No supported findings")
            self.assertEqual(attempt.get("used_model"), review["used_model"])
            self.assertEqual(attempt.get("case"), cell["case"])

    def test_openrouter_reserves_model_specific_maximum_before_dispatch(self):
        manifest = self.benchmark.build_manifest(self.cases, 20260926)
        cell = next(c for c in manifest["cells"] if c["model"] == "openrouter/deepseek/deepseek-v4.1-flash#high")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "attempts").mkdir()
            (root / "attempts" / "previous-1.json").write_text(json.dumps({
                "model": cell["model"], "cost_usd": 8.99, "status": "succeeded"}))
            with patch.object(self.benchmark, "run_review", side_effect=AssertionError("dispatch must pause")):
                outcome = self.benchmark.run_cell(cell, self.cases[int(cell["case"].rsplit("-", 1)[1])], manifest, root)
            self.assertEqual(outcome, "paused")


if __name__ == "__main__":
    unittest.main()
