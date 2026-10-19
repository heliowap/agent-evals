import csv
import contextlib
import io
from contextlib import closing
import json
import copy
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import sys
import sqlite3
from unittest.mock import patch

from cases import CASES, build, grade, run_python, snapshot, write
import opencode_runtime as runtime
import run as runner
from run import grade_copy, schedule, variants, verify_suite_parity


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

    def test_suite_is_identical_to_codex(self):
        verify_suite_parity()

    def test_subprocess_cannot_inherit_controller_stdin(self):
        with tempfile.TemporaryDirectory() as temp:
            result = runtime.command(["python3", "-c", "import sys; print(repr(sys.stdin.read()))"],
                                     Path(temp), {"PATH": "/usr/bin:/bin:/usr/local/bin"}, 5)
            self.assertEqual(result["stdout"].strip(), "''")


def exported(work, turns=1):
    messages = []
    for turn in range(turns):
        messages += [{"type": "user"},
                     {"type": "assistant", "id": f"msg_{turn}", "model": runtime.MODEL_REF, "agent": "build",
                      "tokens": {"input": 10, "output": 4, "reasoning": 2, "cache": {"read": 3, "write": 0}},
                      "content": [{"type": "text", "text": f"done {turn}"}, {"type": "tool", "name": "shell"}]},
                     {"type": "idle", "outcome": "succeeded"}]
    return {"info": {"id": "ses_test", "model": runtime.MODEL_REF, "location": {"directory": str(work)},
                     "cost": 0}, "messages": messages}


class OpenCodeRuntime(unittest.TestCase):
    def test_default_target_is_cpa_opus_medium_without_config_credentials(self):
        self.assertEqual(runtime.SELECTION, "cli_proxy/cpa-claude-opus-5-5#medium")
        self.assertEqual(runtime.MODEL_REF,
                         {"providerID": "cli_proxy", "id": "cpa-claude-opus-5-5", "variant": "medium"})
        config = runtime.config()
        self.assertEqual(set(config["providers"]), {"cli_proxy"})
        provider = config["providers"]["cli_proxy"]
        self.assertEqual(provider["canonical"], "anthropic")
        self.assertEqual(provider["settings"], {"baseURL": "http://127.0.0.1:8317/v1"})
        self.assertEqual(set(provider["models"]), {"cpa-claude-opus-5-5"})
        model = provider["models"]["cpa-claude-opus-5-5"]
        self.assertEqual(model["modelID"], "claude-opus-5-5")
        self.assertEqual(model["settings"], {"effort": "medium"})
        self.assertEqual(model["variants"], [{"id": "medium", "settings": {"effort": "medium"}}])
        self.assertNotIn("apiKey", json.dumps(config))

    def test_cpa_environment_credential_stays_out_of_config(self):
        with patch.dict(os.environ, {"CLIPROXY_API_KEY": "TEST_ONLY_CPA"}):
            entry = runtime.load_credential()
        self.assertEqual(entry["integrationID"], "cli_proxy")
        self.assertEqual(entry["value"], {"type": "key", "key": "TEST_ONLY_CPA"})
        self.assertNotIn("TEST_ONLY_CPA", json.dumps(runtime.config()))

    def test_preflight_failure_is_visible_in_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results"
            error = "Expected only the built-in OpenCode plugins"
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["run.py", "run", "--out", str(out)]), \
                    patch.object(runtime, "audit_pair", side_effect=ValueError(error)), \
                    contextlib.redirect_stdout(stdout):
                code = runner.main()
            self.assertEqual(code, 1)
            self.assertIn(error, stdout.getvalue())

    def test_cumulative_export_is_consumed_once(self):
        result = runtime.parse_export(exported(Path('/tmp'), 2), "ses_test", Path('/tmp'), 2)
        self.assertEqual(result["input_tokens"], 20)
        self.assertEqual(result["reasoning_tokens"], 4)
        self.assertEqual(len(result["tools"]), 2)
        self.assertEqual(result["final"], "done 1")

    def test_refuses_wrong_model_effort_agent_session_or_directory(self):
        for field, value in [("id", "ses_other"), ("model", {**runtime.MODEL_REF, "variant": "high"}),
                             ("model", {**runtime.MODEL_REF, "id": "claude-opus-4-6"}),
                             ("model", {**runtime.MODEL_REF, "providerID": "anthropic"}),
                             ("location", {"directory": "/other"})]:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(exported(Path('/tmp')))
                data["info"][field] = value
                with self.assertRaises(ValueError):
                    runtime.parse_export(data, "ses_test", Path('/tmp'), 1)
        data = copy.deepcopy(exported(Path('/tmp')))
        data["messages"][1]["model"]["variant"] = "high"
        with self.assertRaises(ValueError):
            runtime.parse_export(data, "ses_test", Path('/tmp'), 1)

    def test_latest_turn_must_complete_and_have_a_new_response(self):
        for failure in ["failed", "interrupted", "no_answer", "old_idle", "extra_turn"]:
            data = exported(Path('/tmp'), 2)
            if failure in ("failed", "interrupted"):
                data["messages"][-1]["outcome"] = failure
            elif failure == "no_answer":
                data["messages"][-2]["content"] = []
            elif failure == "old_idle":
                data["messages"].pop()
            else:
                data["messages"].append({"type": "user"})
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                runtime.parse_export(data, "ses_test", Path('/tmp'), 2)

    def test_missing_tokens_stay_unknown(self):
        data = exported(Path('/tmp'), 2)
        del data["messages"][1]["tokens"]["input"]
        result = runtime.parse_export(data, "ses_test", Path('/tmp'), 2)
        self.assertIsNone(result["input_tokens"])
        self.assertEqual(result["output_tokens"], 8)

    def test_event_session_identity(self):
        self.assertEqual(runtime.session_id('{"type":"text","sessionID":"ses_test"}'), "ses_test")
        with self.assertRaises(ValueError):
            runtime.session_id('{"sessionID":"ses_a"}\n{"sessionID":"ses_b"}')

    def test_prepare_drops_ambient_config_and_copies_only_cpa(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = root / "work"
            work.mkdir()
            auth = root / "source.json"
            auth.write_text(json.dumps({"cli_proxy": {"type": "api", "key": "TEST_ONLY"},
                                       "openai": {"type": "api", "key": "MUST_NOT_COPY"}}))
            with patch.dict(os.environ, {"OPENCODE_CONFIG_CONTENT": '{"instructions":["leak"]}',
                                         "OPENAI_BASE_URL": "https://unexpected.invalid"}), \
                    patch.object(runtime, "command", return_value={"exit_code": 0, "timeout": False, "stdout": f"opencode v{runtime.VERSION}"}):
                env, audit = runtime.prepare(root, work, b"", auth_file=auth)
            self.assertNotIn("OPENCODE_CONFIG_CONTENT", env)
            self.assertNotIn("OPENAI_BASE_URL", env)
            self.assertNotIn("CLIPROXY_API_KEY", env)
            self.assertEqual(env["OPENCODE_CONFIG_PROJECT_DISABLE"], "1")
            self.assertEqual([e["integrationID"] for e in json.loads(runtime.auth_path(root).read_text())], ["cli_proxy"])
            self.assertNotIn("MUST_NOT_COPY", runtime.auth_path(root).read_text())
            self.assertNotIn("TEST_ONLY", json.dumps(audit))
            self.assertEqual(runtime.auth_path(root).stat().st_mode & 0o777, 0o600)
            self.assertEqual(audit["agents_bytes"], 0)

    def test_auth_uses_active_v2_credential_and_preserves_refresh(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "opencode/opencode.db"
            database.parent.mkdir()
            with closing(sqlite3.connect(database)) as db, db:
                db.execute('CREATE TABLE credential (id TEXT, integration_id TEXT, label TEXT, value TEXT, active INT, time_created INT)')
                for name, active, created in [("selected", 1, 1), ("unselected", 0, 2)]:
                    db.execute('INSERT INTO credential VALUES (?, ?, ?, ?, ?, ?)',
                               (name, 'cli_proxy', name, json.dumps({'type': 'key', 'key': name}), active, created))
            before = database.read_bytes()
            with patch.dict(os.environ, {"XDG_DATA_HOME": str(root), "CLIPROXY_API_KEY": ""}):
                entry = runtime.load_credential()
            self.assertEqual(entry["id"], "selected")
            self.assertEqual(before, database.read_bytes())
            destination = root / "private.json"
            entry["value"]["key"] = "refreshed"
            runtime.save_credential(entry, destination)
            self.assertEqual(runtime.load_credential(destination)["value"]["key"], "refreshed")

    def test_auth_file_without_cpa_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            auth = Path(temp) / "auth.json"
            for data in [{"openai": {"type": "api", "key": "TEST_ONLY"}},
                         [{"integrationID": "openai", "value": {"type": "key", "key": "TEST_ONLY"}}]]:
                auth.write_text(json.dumps(data))
                with self.subTest(data_type=type(data).__name__), self.assertRaisesRegex(ValueError, "No cli_proxy credential"):
                    runtime.load_credential(auth)

    def test_audit_rejects_contaminated_skills_plugins_and_configs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = root / "work"
            valid = [{"type": "document", "path": str(root / "config/opencode/opencode.json"),
                      "info": runtime.config()}]
            plugin = {"id": "opencode.config.instruction", "source": {"type": "builtin"}, "state": {"status": "active"}}
            for mode in ["valid", "skill", "plugin", "config"]:
                entries = valid if mode != "config" else valid + [{"type": "directory", "path": "/outside"}]
                skills = {"data": [{"id": "contaminated"}] if mode == "skill" else []}
                plugins = {"data": [plugin] if mode != "plugin" else [{"source": {"type": "local"}}]}
                with patch.object(runtime, "local_server", return_value=contextlib.nullcontext({})), \
                        patch.object(runtime, "api", side_effect=[{}, entries, skills, plugins]):
                    if mode == "valid":
                        self.assertEqual(runtime.live_audit(root, work, {}, "opencode")["skills"], [])
                    else:
                        with self.subTest(mode=mode), self.assertRaises(ValueError):
                            runtime.live_audit(root, work, {}, "opencode")

    def test_runner_with_fake_cli_preserves_continuation_and_auth_cleanup(self):
        # Contract test only. No model inference and no claim about real OpenCode behavior.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "fake-opencode"
            fake.write_text(f"#!{sys.executable}\n" + FAKE_CLI)
            fake.chmod(0o700)
            auth = root / "auth.json"
            auth.write_text('{"cli_proxy":{"type":"api","key":"TEST_ONLY"}}')
            original_auth = auth.read_bytes()
            output = root / "results"
            result = subprocess.run([sys.executable, "run.py", "run", "--out", str(output), "--reps", "1",
                                     "--cases", "repeat", "--binary", str(fake), "--auth-file", str(auth),
                                     "--timeout", "30", "--budget-seconds", "300"],
                                    cwd=Path(__file__).parent, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for p in output.glob("trial-*/result.json"):
                row = json.loads(p.read_text())
                self.assertEqual(row["status"], "completed")
                self.assertEqual(row["input_tokens"], 20)
            self.assertEqual(len(list(output.glob("trial-*/result.json"))), 2)
            self.assertEqual(auth.read_bytes(), original_auth)
            runtime_root = Path((output / "runtime-path.txt").read_text().strip())
            self.assertFalse(list(runtime_root.rglob("auth*.json")))
            self.assertFalse(list(runtime_root.rglob("fake-server.json")), "Audit server outlived its ownership scope")
            import shutil
            shutil.rmtree(runtime_root)


FAKE_CLI = r'''
import json, os, sys, sqlite3
from contextlib import closing
from pathlib import Path
a=sys.argv[1:]
def emit(data): print(json.dumps(data))
config=Path(os.environ['XDG_CONFIG_HOME'])/'opencode/opencode.json'
server_state=Path(os.environ['XDG_STATE_HOME'])/'fake-server.json'
activated=Path(os.environ['XDG_STATE_HOME'])/'activated'
if a == ['--version']:
    print('opencode v2.0.25')
elif a[0] == 'serve':
    assert a == ['serve','--stdio','--port','0']
    activated.unlink(missing_ok=True)
    server_state.write_text(json.dumps({'pid':os.getpid(),'password':os.environ['OPENCODE_PASSWORD']}))
    emit({'url':'http://127.0.0.1:34567'})
    sys.stdout.flush()
    try: sys.stdin.read()
    finally: server_state.unlink(missing_ok=True)
elif a[0] == 'api':
    if '--standalone' in a:
        op=a[2]
        settled=False
    else:
        assert a[1:3]==['--server','http://127.0.0.1:34567']
        state=json.loads(server_state.read_text())
        assert state['password']==os.environ['OPENCODE_PASSWORD']
        op=a[3]
        settled=activated.exists()
    if op == 'config.get': emit([{'type':'document','path':str(config),'info':json.loads(config.read_text())}])
    elif op == 'skill.list':
        disabled='-opencode.skill' in json.loads(config.read_text())['plugins']
        emit({'data':[{'id':'opencode'},{'id':'report'}] if settled and not disabled else []})
    elif op == 'integration.list':
        activated.touch()
        emit({'data':[]})
    elif op == 'plugin.list': emit({'data':[{'id':'opencode.config.instruction','source':{'type':'builtin'},'state':{'status':'active'}}] if settled else []})
    else: raise SystemExit(2)
elif a[:2] == ['auth','import']:
    assert a[2]=='--standalone' and len(a)==4
    entry=json.loads(Path(a[3]).read_text())[0]
    assert entry['integrationID']=='cli_proxy'
    database=Path(os.environ['XDG_DATA_HOME'])/'opencode/opencode.db'
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE credential (id TEXT, integration_id TEXT, label TEXT, value TEXT, active INT, time_created INT)')
        db.execute('INSERT INTO credential VALUES (?, ?, ?, ?, ?, ?)',
          (entry['id'],entry['integrationID'],entry['label'],json.dumps(entry['value']),1,1))
else:
    path=Path(os.environ['XDG_DATA_HOME'])/'export.json'
    model={'providerID':'cli_proxy','id':'cpa-claude-opus-5-5','variant':'medium'}
    if a[0] == 'run':
        assert a[a.index('--model')+1] == 'cli_proxy/cpa-claude-opus-5-5#medium'
        if path.exists():
            assert '--session' in a and a[a.index('--session')+1]=='ses_fake'
            data=json.loads(path.read_text())
        else:
            assert '--session' not in a
            data={'info':{'id':'ses_fake','model':model,'location':{'directory':os.getcwd()},'cost':0},'messages':[]}
        data['messages'] += [{'type':'user'},{'type':'assistant','agent':'build','model':model,
          'content':[{'type':'text','text':'done'}],
          'tokens':{'input':10,'output':4,'reasoning':2,'cache':{'read':3,'write':0}}},
          {'type':'idle','outcome':'succeeded'}]
        path.write_text(json.dumps(data))
        emit({'type':'text','sessionID':'ses_fake','part':{'text':'done'}})
    else:
        assert a==['session','export','--standalone','ses_fake']
        emit(json.loads(path.read_text()))
'''


if __name__ == "__main__":
    unittest.main()
