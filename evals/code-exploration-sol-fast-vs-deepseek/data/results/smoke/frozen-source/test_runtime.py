import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import bench
import runtime


def session(candidate, work):
    return {"info": {"id": "s1", "model": candidate.identity, "location": {"directory": str(work)}, "cost": 0},
            "messages": [{"type": "user"}, {"type": "assistant", "agent": "navigator", "model": candidate.identity,
                          "content": [{"type": "tool", "name": "read"}, {"type": "text", "text": '{"answer":{}}'}],
                          "tokens": {"input": 10, "output": 5, "reasoning": 2, "cache": {"read": 3, "write": 0}}},
                         {"type": "idle", "outcome": "succeeded"}]}


def call(candidate, tier=None):
    return {"request": {"model": candidate.model, "reasoning_effort": candidate.effort,
                        "service_tier": "priority" if candidate.fast else None},
            "status": 200, "responses": [{"service_tier": tier}] if tier else []}


class EvidenceChecks(unittest.TestCase):
    def test_fast_configuration_contains_effort_and_priority(self):
        config = runtime.configuration(runtime.CANDIDATES[0], "http://127.0.0.1:1/v1")
        variant = config["providers"]["cli_proxy_openai"]["models"]["gpt-6.1-sol"]["variants"][0]
        self.assertEqual(variant, {"id": "fast-low", "settings": {"reasoningEffort": "low"},
                                   "body": {"reasoning_effort": "low", "service_tier": "priority"}})

    def test_deepseek_configuration_preserves_max_and_its_route(self):
        config = runtime.configuration(runtime.CANDIDATES[1], "http://127.0.0.1:1/v1")
        self.assertEqual(config["model"], "opencode-go/deepseek-v4.1-flash#max")
        variant = config["providers"]["opencode-go"]["models"]["deepseek-v4.1-flash"]["variants"][0]
        self.assertEqual(variant["body"], {"reasoning_effort": "max"})

    def test_forwarded_fast_without_served_tier_is_unknown(self):
        candidate = runtime.CANDIDATES[0]
        checked = runtime.verify_requests(candidate, [call(candidate)])
        self.assertEqual((checked["fast_forwarded"], checked["fast_served"]), (True, "unknown"))

    def test_all_successful_requests_must_confirm_fast(self):
        candidate = runtime.CANDIDATES[0]
        self.assertEqual(runtime.verify_requests(candidate, [call(candidate, "priority")])["fast_served"], "confirmed")
        self.assertEqual(runtime.verify_requests(candidate, [call(candidate, "priority"), call(candidate)])["fast_served"], "not_confirmed")
        self.assertEqual(runtime.verify_requests(candidate, [call(candidate, "default")])["fast_served"], "not_confirmed")

    def test_missing_priority_or_changed_effort_fails(self):
        candidate = runtime.CANDIDATES[0]
        for field, value in [("service_tier", None), ("reasoning_effort", "high"), ("model", "another-model")]:
            with self.subTest(field=field):
                recorded = call(candidate)
                recorded["request"][field] = value
                with self.assertRaises(ValueError):
                    runtime.verify_requests(candidate, [recorded])
        with self.assertRaises(ValueError):
            runtime.verify_requests(candidate, [])

    def test_conflicting_served_tiers_cannot_confirm_fast(self):
        candidate = runtime.CANDIDATES[0]
        recorded = call(candidate, "priority")
        recorded["responses"].append({"service_tier": "default"})
        result = runtime.verify_requests(candidate, [recorded])
        self.assertEqual(result["fast_served"], "not_confirmed")
        self.assertEqual(result["served_tiers"], ["default", "priority"])

    def test_request_capture_excludes_prompt_and_credentials(self):
        metadata = runtime.request_metadata({"model": "gpt-6.1-sol", "reasoning_effort": "low",
                                             "service_tier": "priority", "messages": ["private"], "api_key": "private"})
        self.assertEqual(metadata, {"model": "gpt-6.1-sol", "reasoning_effort": "low", "service_tier": "priority",
                                    "stream": None, "max_tokens": None})
        self.assertNotIn("private", json.dumps(metadata))

    def test_session_identity_tools_and_usage_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            parsed = runtime.parse_session(session(runtime.CANDIDATES[0], work), runtime.CANDIDATES[0], work)
            self.assertEqual(parsed["usage"], {"input_tokens": 10, "output_tokens": 5, "reasoning_tokens": 2,
                                               "cached_input_tokens": 3, "cache_write_tokens": 0})
            self.assertEqual(parsed["final"], '{"answer":{}}')

    def test_session_rejects_silent_fallback_or_forbidden_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            original = session(runtime.CANDIDATES[0], work)
            for change in ["assistant_model", "session_model", "agent", "tool", "outcome"]:
                with self.subTest(change=change):
                    data = copy.deepcopy(original)
                    if change == "assistant_model":
                        data["messages"][1]["model"] = runtime.CANDIDATES[1].identity
                    elif change == "session_model":
                        data["info"]["model"] = runtime.CANDIDATES[1].identity
                    elif change == "agent":
                        data["messages"][1]["agent"] = "build"
                    elif change == "tool":
                        data["messages"][1]["content"][0]["name"] = "shell"
                    else:
                        data["messages"][-1]["outcome"] = "failed"
                    with self.assertRaises(ValueError):
                        runtime.parse_session(data, runtime.CANDIDATES[0], work)

    def test_unknown_token_counts_remain_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            data = session(runtime.CANDIDATES[0], work)
            del data["messages"][1]["tokens"]["reasoning"]
            self.assertIsNone(runtime.parse_session(data, runtime.CANDIDATES[0], work)["usage"]["reasoning_tokens"])

    def test_private_environment_discards_inherited_routing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = runtime.private_env(root, root / "orders-service")
            self.assertNotIn("OPENCODE_CONFIG_CONTENT", env)
            self.assertNotIn("OPENCODE_API_KEY", env)
            self.assertNotIn("HOME", env)
            self.assertEqual(env["OPENCODE_CONFIG_PROJECT_DISABLE"], "1")
            self.assertEqual(env["XDG_DATA_HOME"], str(root / "data"))


class PairedReports(unittest.TestCase):
    def test_schedule_covers_sixty_trials_and_balances_first_position(self):
        rows = bench.schedule(["route", "config", "retry", "permission", "feature", "absence"], 5, 20261010)
        self.assertEqual(len(rows), 60)
        self.assertEqual(sum(r["position"] == 0 and r["candidate"] == "sol-fast-low" for r in rows), 15)
        self.assertEqual(len({(r["case"], r["rep"], r["candidate"]) for r in rows}), 60)
        for left, right in zip(rows[::2], rows[1::2]):
            self.assertEqual((left["pair"], left["case"], left["rep"]), (right["pair"], right["case"], right["rep"]))
            self.assertNotEqual(left["candidate"], right["candidate"])

    def test_missing_failed_and_incorrect_tasks_do_not_create_successful_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            rows = bench.schedule(["route"], 3, 20261010)
            runtime.save(out / "freeze.json", {"schedule": rows, "cases": {"route": {}}, "repetitions": 3})
            for row in rows:
                if row["rep"] == 3:
                    continue
                target = out / row["id"]
                target.mkdir()
                runtime.save(target / "result.json", {**row, "status": "completed", "passed": row["rep"] == 1,
                                                       "wall_s": 10 if row["candidate"] == "sol-fast-low" else 20,
                                                       "transport": {"fast_served": "unknown"}})
            summary = bench.report(out)
            self.assertEqual(summary["statuses"], {"completed": 4, "not_run": 2})
            self.assertEqual(summary["by_case"]["route"]["paired_success_count"], 1)
            self.assertEqual(summary["by_case"]["route"]["median_sol_over_deepseek"], 0.5)
            self.assertFalse(summary["fast_served_confirmed"])
            self.assertEqual(summary["verdict"], "inconclusive")

    def test_redaction_removes_selected_key(self):
        self.assertEqual(bench.redact('header secret-key message secret-key', 'secret-key'),
                         'header <REDACTED> message <REDACTED>')


if __name__ == "__main__":
    unittest.main()
