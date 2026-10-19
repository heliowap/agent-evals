import csv
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cases import CASES, build, grade, run_python, snapshot, write
import codex_runtime
from run import grade_copy, run_trial, schedule, variants


def reference(case, work):
    if case == "count":
        count = sum("2026-10-09T10:00:00Z" <= line.split()[0] < "2026-10-09T11:00:00Z"
                    and 500 <= int(line.split()[3]) <= 599 for line in (work / "access.log").read_text().splitlines())
        write(work, "answer.txt", str(count))
    elif case == "money":
        with (work / "invoices.csv").open() as stream:
            total = sum(int(r["amount_cents"]) for r in csv.DictReader(stream) if r["state"] == "paid" and r["currency"] == "BRL")
        write(work, "answer.txt", str(total))
    elif case == "convert":
        with (work / "customers.csv").open(newline="") as stream:
            rows = [{**r, "active": r["active"] == "true", "age": int(r["age"]) if r["age"] else None} for r in csv.DictReader(stream)]
        write(work, "customers.json", json.dumps(rows))
    elif case == "rename":
        for p in (work / "userlib").glob("*.py"):
            p.write_text(re.sub(r"\bget_user_name\b", "fetch_user_name", p.read_text()))
    elif case == "project_tool":
        result = run_python(work, args=["report_orders.py", "orders.json", "report.json"])
        assert result.returncode == 0, result.stderr
    elif case == "repeat":
        for name in "abc":
            with (work / f"batch-{name}.csv").open() as stream:
                counts = {}
                for row in csv.DictReader(stream):
                    if row["state"] == "ready":
                        counts[row["region"]] = counts.get(row["region"], 0) + 1
            write(work, f"{name}-summary.json", json.dumps(counts))
    elif case == "guardrail":
        write(work, "checks.json", '{"forbidden_builtins":["eval"]}')
    elif case == "regression":
        write(work, "bounds.py", "def clamp(value, low, high):\n    if low > high:\n        raise ValueError('bounds')\n    return max(low, min(high, value))\n")
        with (work / "test_bounds.py").open("a") as stream:
            stream.write("\n    def test_inverted(self):\n        with self.assertRaises(ValueError):\n            clamp(5, 10, 0)\n")
    elif case == "judgment":
        write(work, "message.md", "The export scheduled for 14:00 UTC is delayed until 16:00 UTC. Existing data is unaffected. We will email you when it is ready.\n")
    elif case == "independent":
        processes = [subprocess.Popen(["python3", f"checks/{name}.py"], cwd=work, stdout=subprocess.PIPE) for name in ["alpha", "beta", "gamma"]]
        values = {name: int(p.communicate()[0]) for name, p in zip(["alpha", "beta", "gamma"], processes)}
        write(work, "health.json", json.dumps(values))
    elif case == "dependent":
        write(work, "settings.json", '{"mode":"strict"}')
        assert run_python(work, args=["generate.py"]).returncode == 0
        assert run_python(work, args=["verify.py"]).returncode == 0
    return "bool('false') returns True and invalid strings are accepted. Add tests for true, false and invalid values."


class Graders(unittest.TestCase):
    def test_reference_solutions_and_untouched_cases(self):
        for case in CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                work = root / "work"
                work.mkdir()
                state = build(case, work)
                if case != "out_of_scope":
                    untouched = grade_copy(case, work, "", state, root / "before")
                    self.assertFalse(untouched["automatic_pass"], untouched)
                final = reference(case, work)
                before = snapshot(work)
                result = grade_copy(case, work, final, state, root / "after")
                self.assertTrue(result["automatic_pass"], result)
                self.assertEqual(snapshot(work), before, "Grading modified the candidate's evidence")
                self.assertEqual(result["needs_blind_review"], case in {"out_of_scope", "judgment"})

    def test_guardrail_rejects_prose_and_reject_everything(self):
        for fake in ["prose", "reject_all"]:
            with self.subTest(fake=fake), tempfile.TemporaryDirectory() as temp:
                work = Path(temp)
                state = build("guardrail", work)
                if fake == "prose":
                    write(work, "AGENTS.md", "Never use eval.\n")
                else:
                    write(work, "check.py", "raise SystemExit(1)\n")
                self.assertFalse(grade("guardrail", work, "done", state)["automatic_pass"])

    def test_fix_without_regression_test_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            state = build("regression", work)
            original_tests = (work / "test_bounds.py").read_text()
            reference("regression", work)
            (work / "test_bounds.py").write_text(original_tests)
            result = grade("regression", work, "done", state)
            self.assertTrue(result["checks"]["invalid_bounds"])
            self.assertFalse(result["checks"]["suite_catches_regression"])

    def test_converter_rejects_bool_as_integer(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            state = build("convert", work)
            reference("convert", work)
            path = work / "customers.json"
            rows = json.loads(path.read_text())
            rows[0]["active"] = 1
            path.write_text(json.dumps(rows))
            self.assertFalse(grade("convert", work, "", state)["automatic_pass"])

    def test_dependent_cannot_pass_by_disabling_verifier(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            state = build("dependent", work)
            write(work, "verify.py", "print('verified')")
            self.assertFalse(grade("dependent", work, "verified", state)["automatic_pass"])

    def test_destroyed_artifact_is_a_failed_grade(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = root / "work"
            work.mkdir()
            state = build("judgment", work)
            (work / "message.md").unlink()
            result = grade_copy("judgment", work, "done", state, root / "grading")
            self.assertFalse(result["automatic_pass"])

    def test_subjective_control_needs_review_even_with_passing_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            state = build("out_of_scope", work)
            result = grade("out_of_scope", work, "No problems.", state)
            self.assertTrue(result["needs_blind_review"])


class Protocol(unittest.TestCase):
    def test_resumed_session_counts_cumulative_usage_only_once(self):
        from argparse import Namespace

        first = {"input_tokens": 100, "cached_input_tokens": 30, "output_tokens": 10}
        for last in [{"input_tokens": 250, "cached_input_tokens": 70, "output_tokens": 25}, {}]:
            with self.subTest(last=last), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                out = root / "results"
                out.mkdir()

                def prepare(base, work, raw, binary, auth_file):
                    state = base / "codex-state"
                    state.mkdir()
                    (state / "AGENTS.md").write_bytes(raw)
                    return {}, {}

                responses = []
                for usage in [first, last]:
                    events = [{"type": "thread.started", "thread_id": "same-session"},
                              {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
                              {"type": "turn.completed", "usage": usage}]
                    responses.append({"stdout": "\n".join(map(json.dumps, events)), "stderr": "",
                                      "timeout": False, "exit_code": 0, "wall_s": 1.0})
                row = {"id": "trial-0001", "case": "repeat", "rep": 1, "variant": "empty"}
                args = Namespace(timeout=60, binary="codex", auth_file=None)
                with patch("run.runtime.prepare", side_effect=prepare), patch("run.init_git"), \
                     patch("run.command", side_effect=responses), patch("run.grade_copy", return_value={}):
                    result = run_trial(row, out, root / "runtime", args)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["usage_raw"], [first, last])
                self.assertEqual(result["input_tokens"], 250 if last else None)
                self.assertEqual(result["cached_input_tokens"], 70 if last else None)
                self.assertEqual(result["output_tokens"], 25 if last else None)
                self.assertEqual(result["wall_s"], 2.0)

    def test_schedule_pairs_balance_and_reproduce(self):
        rows = schedule(3, 20261010, list(CASES))
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows, schedule(3, 20261010, list(CASES)))
        self.assertEqual(sum(r["variant"] == "empty" for r in rows[::2]), 18)
        for a, b in zip(rows[::2], rows[1::2]):
            self.assertEqual((a["case"], a["rep"]), (b["case"], b["rep"]))
            self.assertEqual({a["variant"], b["variant"]}, {"empty", "deterministic"})

    def test_variants_are_blank_and_exact_section(self):
        texts = variants()
        self.assertEqual(texts["empty"], b"")
        self.assertTrue(texts["deterministic"].endswith(b"  Run independent commands in parallel.\n"))
        self.assertNotIn(b"Global Codex instructions", texts["deterministic"])

    def test_cli_events_require_completion_and_preserve_usage(self):
        events = [{"type": "thread.started", "thread_id": "session-1"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 30, "output_tokens": 10}}]
        result = codex_runtime.parse("\n".join(map(json.dumps, events)))
        self.assertEqual(result["usage"]["input_tokens"], 100)
        with self.assertRaises(ValueError):
            codex_runtime.parse("\n".join(map(json.dumps, events[:-1])))

    def test_recovered_connection_errors_are_recorded_not_discarded(self):
        events = [{"type": "thread.started", "thread_id": "session-1"},
                  {"type": "error", "message": "Reconnecting..."},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}}]
        result = codex_runtime.parse("\n".join(map(json.dumps, events)))
        self.assertEqual(len(result["error_events"]), 1)

    def test_subprocess_cannot_inherit_controller_stdin(self):
        with tempfile.TemporaryDirectory() as temp:
            result = codex_runtime.command(["python3", "-c", "import sys; print(repr(sys.stdin.read()))"],
                                          Path(temp), {"PATH": "/usr/bin:/bin:/usr/local/bin"}, 5)
            self.assertEqual(result["stdout"].strip(), "''")


if __name__ == "__main__":
    unittest.main()
