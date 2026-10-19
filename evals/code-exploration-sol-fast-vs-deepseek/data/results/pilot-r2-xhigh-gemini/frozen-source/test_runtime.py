import copy
import json
import os
import sqlite3
import time
from unittest.mock import patch
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
    return {"request": {"model": candidate.wire_model, "reasoning_effort": candidate.effort,
                        "service_tier": "priority" if candidate.fast else None},
            "status": 200, "responses": [{"event_type": "response.completed", "service_tier": tier}] if tier else [],
            "complete": True, "identity": candidate.identity, "session_id": "s1", "agent": "navigator", "kind": "primary",
            "transport": "websocket" if candidate.fast else "http",
            "url": candidate.upstream + {"responses": "/responses", "messages": "/messages", "chat": "/chat/completions"}[candidate.protocol]}


class EvidenceChecks(unittest.TestCase):
    def test_fast_configuration_uses_native_oauth_model_and_variants(self):
        for candidate in (c for c in runtime.CANDIDATES if c.fast):
            with self.subTest(candidate=candidate.id):
                config = runtime.configuration(candidate, Path("/private/tmp/observer"))
                self.assertEqual(config["model"], f"openai/gpt-6.1-sol-fast#{candidate.effort}")
                provider = config["providers"]["openai"]
                self.assertEqual(list(provider), ["models"])
                model = provider["models"]["gpt-6.1-sol-fast"]
                self.assertNotIn("variants", model)
                self.assertNotIn("body", model)
                self.assertEqual((candidate.auth_type, candidate.wire_model), ("oauth", "gpt-6.1-sol"))

    def test_deepseek_configuration_keeps_builtin_go_and_max(self):
        config = runtime.configuration(runtime.CANDIDATES[1], Path("/private/tmp/observer"))
        self.assertEqual(config["model"], "opencode-go/deepseek-v4.1-flash#max")
        self.assertNotIn("settings", config["providers"]["opencode-go"])

    def test_anthropic_configurations_keep_protocol_and_native_efforts(self):
        for candidate in (c for c in runtime.CANDIDATES if c.protocol == "messages"):
            with self.subTest(candidate=candidate.id):
                provider = runtime.configuration(candidate, Path("/private/tmp/observer"))["providers"]["cli_proxy"]
                self.assertEqual(provider["canonical"], "anthropic")
                self.assertEqual(provider["package"], "@opencode/ai/providers/anthropic")
                self.assertEqual(provider["models"][candidate.model]["modelID"], candidate.wire_model)
                self.assertNotIn("variants", provider["models"][candidate.model])

    def test_gemini_configurations_use_local_compatibility_route_and_selected_effort(self):
        for candidate in (c for c in runtime.CANDIDATES if c.provider == "cli_proxy_google"):
            with self.subTest(candidate=candidate.id):
                config = runtime.configuration(candidate, Path("/private/tmp/observer"))
                self.assertEqual(config["model"], f"cli_proxy_google/gemini-3.8-flash#{candidate.effort}")
                provider = config["providers"]["cli_proxy_google"]
                self.assertEqual(provider["canonical"], "google")
                self.assertEqual(provider["package"], "@opencode/ai/providers/openai-compatible")
                self.assertEqual(provider["settings"], {"baseURL": "http://127.0.0.1:8317/v1"})
                model = provider["models"]["gemini-3.8-flash"]
                self.assertEqual(model["modelID"], "gemini-3.8-flash")
                self.assertEqual(model["variants"], [{"id": candidate.effort, "settings": {"reasoningEffort": candidate.effort}}])
                self.assertNotIn("body", model)

    def test_gemini_wire_effort_and_route_are_verified(self):
        for candidate in (c for c in runtime.CANDIDATES if c.provider == "cli_proxy_google"):
            with self.subTest(candidate=candidate.id):
                recorded = call(candidate)
                self.assertTrue(runtime.verify_requests(candidate, [recorded])["request_settings_verified"])
                self.assertEqual(recorded["url"], "http://127.0.0.1:8317/v1/chat/completions")
                bad_effort = copy.deepcopy(recorded)
                bad_effort["request"]["reasoning_effort"] = "low"
                with self.assertRaises(ValueError):
                    runtime.verify_requests(candidate, [bad_effort])
                with self.assertRaises(ValueError):
                    runtime.verify_requests(candidate, [{**recorded, "url": "https://generativelanguage.googleapis.com/v1/chat/completions"}])

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
        for candidate in (c for c in runtime.CANDIDATES if c.fast):
            with self.subTest(candidate=candidate.id):
                self.assertTrue(runtime.verify_requests(candidate, [call(candidate, "priority")])["fast_forwarded"])
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
        recorded["responses"].append({"event_type": "response.completed", "service_tier": "default"})
        result = runtime.verify_requests(candidate, [recorded])
        self.assertEqual(result["fast_served"], "not_confirmed")
        self.assertEqual(result["served_tiers"], ["default", "priority"])

    def test_created_tier_does_not_override_terminal_service_class(self):
        candidate = runtime.CANDIDATES[0]
        recorded = call(candidate, "priority")
        recorded["responses"].insert(0, {"event_type": "response.created", "service_tier": "auto"})
        result = runtime.verify_requests(candidate, [recorded])
        self.assertEqual(result["fast_served"], "confirmed")
        self.assertEqual(result["terminal_served_tiers"], ["priority"])

    def test_native_route_and_anthropic_thinking_are_verified(self):
        candidate = runtime.CANDIDATES[2]
        recorded = call(candidate)
        recorded["request"]["thinking_type"] = "adaptive"
        self.assertTrue(runtime.verify_requests(candidate, [recorded])["request_settings_verified"])
        for field, value in [("url", "https://another.example/v1/messages"), ("identity", runtime.CANDIDATES[3].identity), ("kind", "title")]:
            bad = {**recorded, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                runtime.verify_requests(candidate, [bad])
        recorded["request"]["thinking_type"] = "enabled"
        with self.assertRaises(ValueError):
            runtime.verify_requests(candidate, [recorded])

    def test_incomplete_websocket_does_not_confirm_fast(self):
        recorded = call(runtime.CANDIDATES[0], "priority")
        recorded["complete"] = False
        self.assertEqual(runtime.verify_requests(runtime.CANDIDATES[0], [recorded])["fast_served"], "not_confirmed")

    def test_requests_must_belong_to_the_exported_task_session(self):
        candidate = runtime.CANDIDATES[0]
        recorded = call(candidate, "priority")
        self.assertEqual(runtime.verify_requests(candidate, [recorded], "s1")["request_count"], 1)
        with self.assertRaises(ValueError):
            runtime.verify_requests(candidate, [recorded], "another-session")
        with self.assertRaises(ValueError):
            runtime.verify_requests(candidate, [recorded, {**recorded, "session_id": "another-session"}])

    def test_log_replay_preserves_request_identity_status_and_timing(self):
        candidate = runtime.CANDIDATES[0]
        shared = {"call_id": "1", "session_id": "s1", "identity": candidate.identity, "kind": "primary", "agent": "navigator"}
        events = [{"event": "ready"}, {**shared, "event": "request", "transport": "websocket", "url": candidate.upstream + "/responses", "at_ms": 1000, "request": call(candidate)["request"]},
                  {**shared, "event": "response", "at_ms": 2000, "response": {"event_type": "response.completed", "service_tier": "priority"}},
                  {**shared, "event": "end", "at_ms": 2100, "status": 200}]
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "observations.jsonl"
            log.write_text("".join(json.dumps(e) + "\n" for e in events))
            records = runtime.read_requests(log)
            self.assertEqual((records[0]["wall_s"], records[0]["first_event_s"]), (1.1, 1.0))
            self.assertEqual(runtime.verify_requests(candidate, records)["fast_served"], "confirmed")
            log.write_text(json.dumps(events[2]) + "\n")
            with self.assertRaises(ValueError):
                runtime.read_requests(log)

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


class PrivateCredentials(unittest.TestCase):
    def test_gemini_remaps_existing_proxy_key_to_google_integration(self):
        candidate = next(c for c in runtime.CANDIDATES if c.id == "gemini-medium")
        value = {"type": "key", "key": "test-proxy-key"}
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            database = Path(folder) / "credentials.db"
            with sqlite3.connect(database) as connection:
                connection.execute("create table credential(id text,integration_id text,value text,time_created integer)")
                connection.execute("insert into credential values(?,?,?,?)", ("k", "cli_proxy", json.dumps(value), 1))
            imported = runtime.credential(candidate, database)
            self.assertEqual(imported["integrationID"], "cli_proxy_google")
            self.assertEqual(imported["value"], value)
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("select integration_id from credential").fetchone()[0], "cli_proxy")
            with patch.dict(os.environ, {"CLIPROXY_API_KEY": "test-override-key"}):
                self.assertEqual(runtime.credential(candidate, database)["value"], {"type": "key", "key": "test-override-key"})

    def test_oauth_is_importable_intact_without_key_conversion(self):
        candidate = runtime.CANDIDATES[0]
        value = {"type": "oauth", "methodID": "chatgpt-browser", "access": "private-access", "refresh": "private-refresh",
                 "expires": int((time.time() + 100000) * 1000), "metadata": {"accountID": "private-account"}}
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "credentials.db"
            with sqlite3.connect(database) as connection:
                connection.execute("create table credential(id text, integration_id text, value text, active integer, time_created integer)")
                connection.execute("insert into credential values(?,?,?,?,?)", ("original", "openai", json.dumps(value), 1, 1))
            imported = runtime.credential(candidate, database)
            self.assertEqual(imported["value"], value)
            self.assertEqual(imported["integrationID"], "openai")
            self.assertEqual(runtime.credential_secrets(value), ["private-access", "private-refresh"])
            runtime.validate_oauth_window([candidate], database, 21600)
            with self.assertRaises(ValueError):
                runtime.validate_oauth_window([candidate], database, 200000)
            with sqlite3.connect(database) as connection:
                self.assertEqual(json.loads(connection.execute("select value from credential").fetchone()[0]), value)

    def test_oauth_cannot_be_replaced_by_key_environment_override(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"CLIPROXY_API_KEY": "private", "OPENAI_API_KEY": "private"}):
            database = Path(folder) / "credentials.db"
            with sqlite3.connect(database) as connection:
                connection.execute("create table credential(id text,integration_id text,value text,time_created integer)")
                connection.execute("insert into credential values(?,?,?,?)", ("k", "openai", '{"type":"key","key":"private"}', 1))
            with self.assertRaises(ValueError):
                runtime.credential(runtime.CANDIDATES[0], database)


if __name__ == "__main__":
    unittest.main()
