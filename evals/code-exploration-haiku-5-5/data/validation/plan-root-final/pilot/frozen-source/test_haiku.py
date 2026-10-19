from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bench
import cases
import haiku
import runtime
from test_cases import reference


def request(candidate):
    return {"request": {"model": candidate.wire_model, "reasoning_effort": candidate.effort,
                        "thinking_type": "adaptive", "max_tokens": 128000},
            "identity": candidate.identity, "agent": "navigator", "kind": "primary",
            "url": "http://127.0.0.1:8317/v1/messages", "session_id": "ses_test",
            "status": 200, "complete": True, "responses": [], "transport": "http"}


def session(candidate, work, finish="stop", raw="end_turn", text="{}"):
    return {"info": {"id": "ses_test", "model": candidate.identity, "location": {"directory": str(work)}},
            "messages": [{"type": "user"},
                         {"type": "assistant", "id": "msg_a", "model": candidate.identity, "agent": "navigator",
                          "finish": finish, "rawFinish": raw, "content": [{"type": "text", "text": text}],
                          "tokens": {"input": 20, "output": 0, "reasoning": 128000, "cache": {"read": 0, "write": 0}}},
                         {"type": "idle", "outcome": "succeeded"}]}


class CampaignProof(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.candidate = runtime.CANDIDATES[0]

    def test_schedule_full_matrix_balanced_and_smoke(self):
        rows = bench.schedule(list(cases.CASES), 5, 20261010)
        self.assertEqual(len(rows), 150)
        self.assertEqual(len(bench.schedule(["route"], 1, 20261010)), 5)
        self.assertEqual(rows, bench.schedule(list(cases.CASES), 5, 20261010))
        self.assertEqual(Counter((r["case"], r["rep"]) for r in rows), Counter({(c, r): 5 for c in cases.CASES for r in range(1, 6)}))
        for candidate in runtime.CANDIDATES:
            self.assertEqual(Counter(r["position"] for r in rows if r["candidate"] == candidate.id), Counter({i: 6 for i in range(5)}))

    def test_configuration_identity_cap_permissions_and_variants(self):
        for candidate in runtime.CANDIDATES:
            config = runtime.configuration(candidate, self.root / "observer")
            model = config["providers"]["cli_proxy"]["models"][candidate.model]
            self.assertEqual(model["limit"], {"context": 272000, "output": 128000})
            self.assertEqual(model["variants"], [{"id": e, "settings": {"effort": e}} for e in ["low", "medium", "high", "xhigh", "max"]])
            self.assertEqual({p["action"] for p in config["permissions"] if p["effect"] == "allow"}, {"read", "glob", "grep", "list"})
            self.assertEqual((config["skills"], config["mcp"], config["instructions"], config["agents"]["navigator"]["steps"]), ([], {}, [], 25))
            self.assertFalse(candidate.fast)

    def test_all_requests_must_preserve_route_identity_effort_and_cap(self):
        for candidate in runtime.CANDIDATES:
            valid = request(candidate)
            self.assertTrue(runtime.verify_requests(candidate, [valid], "ses_test")["request_settings_verified"])
            for field, values in [("max_tokens", [None, True, 128000.0, 32768]),
                                  ("model", ["other"]), ("reasoning_effort", ["other"]), ("thinking_type", ["enabled"])]:
                for value in values:
                    bad = copy.deepcopy(valid)
                    bad["request"][field] = value
                    with self.assertRaises(ValueError):
                        runtime.verify_requests(candidate, [valid, bad], "ses_test")
            for field, value in [("session_id", "other"), ("url", "http://127.0.0.1:8317/v1/chat/completions"),
                                 ("agent", "build"), ("kind", "summary"), ("identity", {})]:
                bad = copy.deepcopy(valid)
                bad[field] = value
                with self.assertRaises(ValueError):
                    runtime.verify_requests(candidate, [valid, bad], "ses_test")

    def test_terminal_limit_empty_text_preserves_diagnostics(self):
        data = session(self.candidate, self.root, "length", "max_tokens", "")
        parsed = runtime.parse_session(data, self.candidate, self.root)
        self.assertEqual((parsed["delivery"], parsed["terminal_output_limit"], parsed["usage"]["reasoning_tokens"]), ("output_limit_reached", True, 128000))
        self.assertEqual(parsed["finishes"], [{"id": "msg_a", "finish": "length", "rawFinish": "max_tokens"}])

    def test_intermediate_limit_recovered_and_no_token_inference(self):
        data = session(self.candidate, self.root)
        limited = copy.deepcopy(data["messages"][1])
        limited.update(id="first", finish="length", rawFinish="max_tokens")
        data["messages"].insert(1, limited)
        parsed = runtime.parse_session(data, self.candidate, self.root)
        self.assertEqual((parsed["delivery"], parsed["intermediate_output_limits"], parsed["recovered_output_limit"]), ("completed", 1, True))
        self.assertEqual(runtime.parse_session(session(self.candidate, self.root), self.candidate, self.root)["delivery"], "completed")

    def test_missing_final_task_error_and_forbidden_tool_infra(self):
        self.assertEqual(runtime.parse_session(session(self.candidate, self.root, text=""), self.candidate, self.root)["delivery"], "task_error")
        data = session(self.candidate, self.root)
        data["messages"][1]["content"].append({"type": "tool", "name": "bash"})
        with self.assertRaises(ValueError):
            runtime.parse_session(data, self.candidate, self.root)

    def fake_binary(self, body):
        binary = self.root / "opencode"
        binary.write_text("#!/usr/bin/env python3\n" + body)
        binary.chmod(0o700)
        return str(binary)

    def test_export_regular_file_large_complete_json(self):
        binary = self.fake_binary("import os,stat,json\nassert stat.S_ISREG(os.fstat(1).st_mode)\nos.write(1,json.dumps({'payload':'x'*1000000}).encode())\n")
        artifacts = self.root / "artifacts"
        artifacts.mkdir()
        result = runtime.export_session(binary, "ses", self.root, dict(os.environ), artifacts)
        self.assertEqual(len(result["payload"]), 1000000)
        raw = (artifacts / "session.json").read_bytes()
        receipt = json.loads((artifacts / "export.json").read_text())
        self.assertEqual((receipt["preserved_bytes"], receipt["preserved_sha256"]), (len(raw), hashlib.sha256(raw).hexdigest()))
        self.assertGreater(len(raw), 1000000)
        self.assertEqual((artifacts / "session.json").stat().st_mode & 0o777, 0o600)
        self.assertFalse((artifacts / ".export-raw").exists())

    def test_invalid_json_preserved_before_parse_and_redacted(self):
        secret = 'sêc"ret\\value'
        raw = b'{"token":' + json.dumps(secret).encode() + b',"payload":"unfinished'
        binary = self.fake_binary(f"import os\nos.write(1,{raw!r})\nos.write(2,{secret.encode()!r})\n")
        with self.assertRaises(ValueError):
            runtime.export_session(binary, "ses", self.root, dict(os.environ), self.root, [secret])
        expected = raw.replace(json.dumps(secret)[1:-1].encode(), b"<REDACTED>")
        self.assertEqual((self.root / "session.json").read_bytes(), expected)
        self.assertEqual((self.root / "export.stderr").read_bytes(), b"<REDACTED>")
        receipt = json.loads((self.root / "export.json").read_text())
        self.assertEqual(receipt["raw_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIsInstance(receipt["json_error"]["byte_offset"], int)

    def test_utf8_failure_nonzero_and_timeout_preserve_bytes(self):
        for mode, body in [("utf8", "import os\nos.write(1,b'\\xff')\n"),
                           ("exit", "import os\nos.write(1,b'{}')\nraise SystemExit(9)\n"),
                           ("timeout", "import os,time\nos.write(1,b'{')\ntime.sleep(10)\n")]:
            folder = self.root / mode
            folder.mkdir()
            binary = self.fake_binary(body)
            with self.assertRaises(ValueError):
                runtime.export_session(binary, "ses", self.root, dict(os.environ), folder, timeout=0.5 if mode == "timeout" else 5)
            self.assertTrue((folder / "session.json").exists())
            receipt = json.loads((folder / "export.json").read_text())
            self.assertEqual(receipt["timeout"], mode == "timeout")
            self.assertFalse((folder / ".export-raw").exists())

    def build_smoke(self):
        smoke = self.root / "smoke"
        smoke.mkdir()
        frozen = bench.manifest(["route"], 1, 20261010, 300, 21600, haiku.ROOT / "models.json")
        runtime.save(smoke / "freeze.json", frozen)
        runtime.save(smoke / "phase.json", {"planned": 5, "attempted": 5, "stop_reason": "schedule_exhausted", "exit_code": 0})
        for row in frozen["schedule"]:
            folder = smoke / row["id"]
            folder.mkdir()
            runtime.save(folder / "result.json", {**row, "status": "completed", "passed": True, "fixture_unchanged": True, "session_id": "ses_test"})
            candidate = next(c for c in runtime.CANDIDATES if c.id == row["candidate"])
            runtime.save(folder / "requests.json", [request(candidate)])
            (folder / "answer.json.txt").write_text(json.dumps(reference("route")))
        return smoke

    def test_fresh_smoke_gate_regrades_answers_and_checks_every_request(self):
        smoke = self.build_smoke()
        self.assertTrue(haiku.smoke_passed(smoke))
        answer = smoke / "trial-0005/answer.json.txt"
        answer.write_text('{}')
        self.assertFalse(haiku.smoke_passed(smoke))
        answer.write_text(json.dumps(reference("route")))
        path = smoke / "trial-0005/requests.json"
        records = json.loads(path.read_text())
        records[0]["request"]["max_tokens"] = 32768
        runtime.save(path, records)
        with self.assertRaises(ValueError):
            haiku.smoke_passed(smoke)

    def test_smoke_gate_rejects_observer_error_after_complete_http_200(self):
        smoke = self.build_smoke()
        self.assertTrue(haiku.smoke_passed(smoke))
        path = smoke / "trial-0005/requests.json"
        records = json.loads(path.read_text())
        records[0]["error"] = "Observed provider or transport failure"
        runtime.save(path, records)
        self.assertFalse(haiku.smoke_passed(smoke))
        candidate = next(c for c in runtime.CANDIDATES if c.identity == records[0]["identity"])
        self.assertEqual(runtime.verify_requests(candidate, records, "ses_test")["observed_error_requests"], 1)
        self.assertEqual(json.loads(path.read_text()), records)

    def test_failed_smoke_never_starts_pilot(self):
        locations = SimpleNamespace(binary="opencode", cache=haiku.ROOT / "models.json", database=self.root / "db")
        with patch.object(haiku, "phase_envelope") as envelope, patch.object(haiku, "original_inventory", return_value={}), patch.object(bench, "main", return_value=1) as core:
            envelope.return_value.__enter__.return_value = None
            self.assertEqual(haiku.run_campaign(self.root, locations), 1)
        self.assertEqual(core.call_count, 1)
        self.assertEqual(json.loads((self.root / "summary.json").read_text())["phases"]["pilot"]["statuses"], {"not_run": 150})

    def test_final_envelope_guard_detects_change(self):
        locations = SimpleNamespace(binary="opencode", cache=haiku.ROOT / "models.json")
        with patch.object(haiku, "provenance_check"), patch.object(haiku, "external_inventory", side_effect=[{"source": "a"}, {"source": "b"}]):
            with self.assertRaises(ValueError):
                with haiku.phase_envelope("pilot", self.root, locations):
                    pass
        self.assertFalse(json.loads((self.root / "envelopes/pilot.json").read_text())["integrity_passed"])

    def test_budget_incomplete_and_complete_output_limits_exit(self):
        for limit_budget in [True, False]:
            out = self.root / str(limit_budget)
            argv = ["run", "--out", str(out), "--cases", "route", "--reps", "1", "--cache", str(haiku.ROOT / "models.json")]
            def synthetic(row, output, private, args):
                folder = output / row["id"]
                folder.mkdir()
                rec = {**row, "status": "output_limit_reached", "passed": False}
                runtime.save(folder / "result.json", rec)
                return rec
            clock = iter([0, 22000]) if limit_budget else None
            with patch.object(bench, "preflight", return_value={"status": "passed"}), patch.object(bench, "run_trial", side_effect=synthetic), patch.object(bench.time, "monotonic", side_effect=(lambda: next(clock)) if limit_budget else (lambda: 0)):
                code = bench.main(argv)
            phase = json.loads((out / "phase.json").read_text())
            self.assertEqual((code, phase["attempted"], phase["stop_reason"]), (1, 0, "budget_exhausted") if limit_budget else (0, 5, "schedule_exhausted"))
            summary = json.loads((out / "summary.json").read_text())
            for detail in summary["by_candidate"].values():
                self.assertEqual((detail["incorrect"], detail["errors"]), (0, 0))

    def test_original_contract_and_private_environment(self):
        self.assertEqual(len(cases.FILES), 23)
        haiku.provenance_check()
        env = runtime.private_env(self.root / "private", self.root)
        self.assertEqual((env["OPENCODE_CONFIG_PROJECT_DISABLE"], env["OPENCODE_DISABLE_MODELS_FETCH"]), ("1", "1"))
        self.assertNotIn("CLIPROXY_API_KEY", env)
        self.assertNotIn("HOME", env)

    def test_core_guard_checks_source_after_final_trial(self):
        source = self.root / "source"
        source.mkdir()
        (source / "README.md").write_text("protocol")
        (source / "provenance.json").write_text("{}")
        target = source / "runner.py"
        target.write_text("initial")
        out = self.root / "run"

        def synthetic(row, output, private, args):
            folder = output / row["id"]
            folder.mkdir()
            result = {**row, "status": "completed", "passed": True, "wall_s": 1}
            runtime.save(folder / "result.json", result)
            target.write_text("changed after the final task")
            return result

        argv = ["run", "--out", str(out), "--cases", "route", "--reps", "1", "--candidates", "haiku-low", "--cache", str(haiku.ROOT / "models.json")]
        with patch.object(bench, "ROOT", source), patch.object(bench, "preflight", return_value={"status": "passed"}), patch.object(bench, "run_trial", side_effect=synthetic):
            self.assertEqual(bench.main(argv), 1)
        self.assertEqual(json.loads((out / "phase.json").read_text())["stop_reason"], "integrity_failure")


if __name__ == "__main__":
    unittest.main()
