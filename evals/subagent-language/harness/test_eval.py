import argparse
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from cases import CASES, build, grade
import run
import runtime
import telemetry


def usage(n):
    return {"input_tokens": n, "cached_input_tokens": n // 2, "output_tokens": 10,
            "reasoning_output_tokens": 3, "total_tokens": n + 10}


def event(kind, payload):
    return {"type": kind, "payload": payload}


def trace(tid, n, parent=None, fork=None):
    source = {"subagent": {"thread_spawn": {"parent_thread_id": parent, "agent_path": "/root/" + tid}}} if parent else "exec"
    u = usage(n)
    result = [event("session_meta", {"id": tid, "source": source, "forked_from_id": fork}),
              event("turn_context", {"model": "model", "effort": "high"}),
              event("event_msg", {"type": "task_started", "turn_id": tid + "-turn"}),
              event("token_usage_record", {"thread_id": tid, "response_id": tid + "-response",
                                           "usage": u, "thread_token_usage": u}),
              event("event_msg", {"type": "token_count", "info": {"total_token_usage": u}}),
              event("event_msg", {"type": "token_count", "info": {"total_token_usage": u}}),
              event("event_msg", {"type": "task_complete", "turn_id": tid + "-turn", "last_agent_message": "Análise concluída."})]
    if not parent:
        result += [event("response_item", {"type": "function_call", "name": "spawn_agent", "call_id": child,
                                            "arguments": json.dumps({"fork_turns": "none", "message": "Analise os dados.", "task_name": child})})
                   for child in ("a", "b")]
    return result


class EvalTests(unittest.TestCase):
    def collect(self, traces, cli=None):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for i, events in enumerate(traces):
                path = Path(temp) / f"{i}.jsonl"
                path.write_text("\n".join(map(json.dumps, events)))
                paths.append(path)
            return telemetry.collect(paths, "root", "model", "high", cli or usage(100))

    def test_ledger_sums_team_once_and_keeps_subsets_separate(self):
        root = trace("root", 100)
        root.insert(4, root[3])  # Duplicate response persisted twice, not another request.
        result = self.collect([root, trace("a", 200, "root"), trace("b", 300, "root")])
        self.assertTrue(result["measurement_valid"], result["issues"])
        self.assertTrue(result["protocol_pass"])
        self.assertEqual(result["usage"], {"input_tokens": 600, "cached_input_tokens": 300,
                                         "output_tokens": 30, "reasoning_output_tokens": 9, "total_tokens": 630})
        self.assertEqual(result["subagent_usage"]["total_tokens"], 520)
        self.assertEqual(result["cli_usage_scope"], "root")
        self.assertEqual(result["response_count"], 3)

    def test_encrypted_communication_is_not_exported_as_reviewable_prose(self):
        root = trace("root", 100)
        root[-1]["payload"]["arguments"] = json.dumps({"fork_turns": "none", "message": "opaque-ciphertext"})
        child = trace("b", 300, "root")
        child.append(event("response_item", {"type": "agent_message", "content": [
            {"type": "input_text", "text": "Payload:"},
            {"type": "encrypted_content", "encrypted_content": "opaque-ciphertext"}]}))
        result = self.collect([root, trace("a", 200, "root"), child])
        self.assertTrue(result["measurement_valid"])
        self.assertFalse(result["language_audit_complete"])
        self.assertEqual(result["communication_observability"], {"readable": 3, "encrypted": 1})
        hidden = [m for m in result["communications"] if m.get("observability") == "encrypted"]
        self.assertEqual(len(hidden), 1)
        self.assertIsNone(hidden[0]["text"])
        self.assertEqual(hidden[0]["language"], "unobservable")

    def test_cli_team_counter_is_never_added_again(self):
        result = self.collect([trace("root", 100), trace("a", 200, "root"), trace("b", 300, "root")],
                              {"input_tokens": 600, "output_tokens": 30})
        self.assertTrue(result["measurement_valid"], result["issues"])
        self.assertEqual(result["cli_usage_scope"], "team")
        self.assertEqual(result["usage"]["total_tokens"], 630)

    def test_missing_child_usage_is_not_zero(self):
        child = [e for e in trace("a", 200, "root") if e["type"] != "token_usage_record"]
        result = self.collect([trace("root", 100), child, trace("b", 300, "root")])
        self.assertFalse(result["measurement_valid"])
        self.assertIn("missing_usage:a", result["issues"])

    def test_opaque_message_without_delivery_record_remains_unobservable(self):
        root = trace("root", 100)
        root[-1]["payload"]["arguments"] = json.dumps({"fork_turns": "none", "message": "gAAAA" + "x" * 100})
        result = self.collect([root, trace("a", 200, "root"), trace("b", 300, "root")])
        self.assertEqual(result["communication_observability"], {"readable": 3, "encrypted": 1})
        self.assertFalse(result["language_audit_complete"])

    def test_unfinished_subagent_invalidates_measurement(self):
        result = self.collect([trace("root", 100), trace("a", 200, "root")[:-1], trace("b", 300, "root")])
        self.assertIn("unfinished_turns:a", result["issues"])

    def test_cumulative_counters_are_reconciled(self):
        child = trace("a", 200, "root")
        child[3]["payload"]["thread_token_usage"] = usage(400)
        result = self.collect([trace("root", 100), child, trace("b", 300, "root")])
        self.assertIn("response_sum_differs_from_thread_counter:a", result["issues"])

    def test_fork_or_other_model_is_rejected(self):
        child = trace("a", 200, "root", fork="root")
        child[1]["payload"]["model"] = "other"
        result = self.collect([trace("root", 100), child, trace("b", 300, "root")])
        self.assertFalse(result["protocol_pass"])
        self.assertIn("model_or_effort_mismatch:a", result["issues"])
        self.assertIn("unexpected_parent_or_fork:a", result["issues"])

    def test_no_delegation_is_a_protocol_failure(self):
        root = [e for e in trace("root", 100) if e["type"] != "response_item"]
        result = self.collect([root])
        self.assertTrue(result["measurement_valid"])
        self.assertFalse(result["protocol_pass"])

    def test_schedule_pairs_all_conditions_with_balanced_orders(self):
        rows = run.schedule(list(CASES), 5, 20261011)
        self.assertEqual(len(rows), 60)
        self.assertEqual(rows, run.schedule(list(CASES), 5, 20261011))
        for i in range(0, len(rows), 3):
            block = rows[i:i + 3]
            self.assertEqual({(r["case"], r["rep"]) for r in block}, {(block[0]["case"], block[0]["rep"])})
            self.assertEqual({r["variant"] for r in block}, {"default", "pt", "en"})
        permutations = [tuple(r["variant"] for r in rows[i:i + 3]) for i in range(0, 60, 3)]
        self.assertEqual(len(set(permutations)), 6)
        self.assertLessEqual(max(permutations.count(p) for p in permutations) - min(permutations.count(p) for p in permutations), 1)

    def test_graders_reject_wrong_missing_and_input_mutations(self):
        for name, case in CASES.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp:
                work = Path(temp)
                build(name, work)
                self.assertFalse(grade(name, work)["automatic_pass"])
                (work / "answer.json").write_text(json.dumps(case["expected"]))
                (work / "report.md").write_text("Justificativa a revisar.")
                self.assertTrue(grade(name, work)["automatic_pass"])
                (work / "answer.json").write_text("{}")
                self.assertFalse(grade(name, work)["automatic_pass"])
                (work / "answer.json").write_text(json.dumps(case["expected"]))
                (work / next(iter(case["files"]))).write_text("alterado")
                self.assertFalse(grade(name, work)["automatic_pass"])

    def test_independent_reconciliation_of_money_fixture(self):
        events = json.loads(CASES["conciliacao"]["files"]["eventos.json"])
        unique = {e["event_id"]: e for e in events}.values()
        payments = [e for e in unique if e["tipo"] == "pago" and e["moeda"] == "BRL"
                    and "2026-10-10T00:00:00Z" <= e["em"] < "2026-10-11T00:00:00Z"]
        by_channel = {"loja": 0, "web": 0}
        for payment in payments:
            refunds = sum(e["valor"] for e in unique if e["tipo"] == "estorno_confirmado"
                          and e["pedido"] == payment["pedido"] and e["em"] < "2026-10-11T00:00:00Z")
            by_channel[payment["canal"]] += payment["valor"] - refunds
        self.assertEqual(by_channel, {"loja": 25000, "web": 13000})

    def test_fornecedor_uses_portuguese_alphabetical_order(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            build("fornecedor", work)
            (work / "report.md").write_text("Gama vence pelo prazo de implantação.")
            answer = {"escolhido": "Gama", "elegiveis": ["Alfa", "Épsilon", "Gama"],
                      "custo_12_meses_centavos": 3180000, "excluidos": {"Beta": ["R1"], "Delta": ["R2"]}}
            (work / "answer.json").write_text(json.dumps(answer))
            self.assertTrue(grade("fornecedor", work)["automatic_pass"])
            answer["elegiveis"] = ["Alfa", "Gama", "Épsilon"]
            (work / "answer.json").write_text(json.dumps(answer))
            self.assertFalse(grade("fornecedor", work)["automatic_pass"])

    def test_timeout_kills_actual_child_process(self):
        with tempfile.TemporaryDirectory() as temp:
            result = runtime.command([sys.executable, "-c", "import time; time.sleep(5)"],
                                     Path(temp), os.environ.copy(), 0.05)
            self.assertTrue(result["timeout"])
            self.assertNotEqual(result["exit_code"], 0)

    def test_offline_end_to_end_collect_grade_and_report(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            args = argparse.Namespace(binary="codex", auth_file=None, model="model", effort="high", timeout=2)
            row = {"id": "trial-0001", "case": "incidente", "rep": 1, "variant": "en"}

            def prepare(base, work, raw, *unused):
                state = base / "codex-state"
                (state / "sessions").mkdir(parents=True)
                (state / "AGENTS.md").write_bytes(raw)
                for tid, n, parent in [("root", 100, None), ("a", 200, "root"), ("b", 300, "root")]:
                    (state / "sessions" / f"{tid}.jsonl").write_text("\n".join(map(json.dumps, trace(tid, n, parent))))
                return {}, {}

            def command(argv, work, env, timeout):
                (work / "answer.json").write_text(json.dumps(CASES["incidente"]["expected"]))
                (work / "report.md").write_text("Relatório em português para revisão.")
                events = [{"type": "thread.started", "thread_id": "root"},
                          {"type": "item.completed", "item": {"type": "agent_message", "text": "Concluído."}},
                          {"type": "turn.completed", "usage": usage(100)}]
                return {"wall_s": 1.5, "stdout": "\n".join(map(json.dumps, events)), "stderr": "", "exit_code": 0, "timeout": False}

            with patch.object(runtime, "prepare", prepare), patch.object(runtime, "command", command):
                result = run.run_trial(row, out, args)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["usage"]["total_tokens"], 630)
            self.assertTrue(result["grade"]["automatic_pass"])
            self.assertEqual(len(list((out / row["id"] / "rollouts").glob("*.jsonl"))), 3)
            self.assertFalse(list(out.rglob("auth.json")))
            schedule = [{**row, "id": f"trial-{i:04}", "variant": v} for i, v in enumerate(("en", "pt", "default"), 1)]
            run.save(out / "freeze.json", {"schedule": schedule, "cases": CASES})
            run.report(out)
            run.blind(out)
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual([r["status"] for r in summary["rows"]], ["completed", "not_run", "not_run"])
            self.assertEqual(summary["comparisons"][0]["pairs"], [])
            self.assertEqual(len(json.loads((out / "blind-review/ratings.json").read_text())), 1)

    def test_report_separates_assigned_conditions_from_quality_filter(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            rows = [{"id": v, "variant": v, "case": "incidente", "rep": 1} for v in ("default", "pt", "en")]
            run.save(out / "freeze.json", {"schedule": rows})
            for row in rows:
                (out / row["id"]).mkdir()
                english = row["variant"] == "en"
                run.save(out / row["id"] / "result.json", {
                    **row, "status": "completed", "wall_s": 8 if english else 10,
                    "protocol_pass": True, "grade": {"automatic_pass": not english},
                    "usage": {"input_tokens": 70 if english else 90, "output_tokens": 10,
                              "cached_input_tokens": 0, "reasoning_output_tokens": 0,
                              "total_tokens": 80 if english else 100}})
            run.report(out)
            comparisons = json.loads((out / "summary.json").read_text())["comparisons"]
            all_runs = next(c for c in comparisons if c["baseline"] == "default" and c["subset"] == "completas")
            passed = next(c for c in comparisons if c["baseline"] == "default" and c["subset"] == "acerto+protocolo")
            self.assertAlmostEqual(all_runs["pairs"][0]["tokens_pct"], -20)
            self.assertAlmostEqual(all_runs["pairs"][0]["time_pct"], -20)
            self.assertEqual(passed["pairs"], [])


if __name__ == "__main__":
    unittest.main()
