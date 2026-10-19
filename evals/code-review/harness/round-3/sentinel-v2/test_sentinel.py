# round-3/sentinel-v2/test_sentinel.py
# Canonical command (from round-3/):
#   uv run --with lizard==1.24.0 python3 -m unittest discover -s sentinel-v2 -v
# Tests that need lizard are skipped when it is not importable.
# The live Jev test runs only with SENTINEL_LIVE=1 (and OPENROUTER_API_KEY set).
import json, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import jev  # noqa: E402
import sentinel  # noqa: E402
from sentinel import changed_functions, changed_functions_report, jev_questions, rank, hotspots, QUESTIONS  # noqa: E402

try:
    import lizard
except ImportError:
    lizard = None
NEED_LIZARD = unittest.skipIf(
    lizard is None,
    "lizard not installed; run: uv run --with lizard==1.24.0 python3 -m unittest discover -s sentinel-v2 -v")


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def mktmp(tc):
    d = Path(tempfile.mkdtemp()); tc.addCleanup(shutil.rmtree, d, ignore_errors=True)
    return d


PY_BASE = """\
def untouched(x):
    return x + 1


def guarded(items, i):
    if items is None:
        return None
    if i < 0 or i >= len(items):
        raise IndexError(i)
    return items[i]


def cosmetic(a):
    return a * 2
"""

PY_HEAD = """\
def untouched(x):
    return x + 1


def guarded(items, i):
    if items is None:
        return None
    return items[i]


def cosmetic(value):
    return value * 2
"""

TS_BASE = """\
export function pick(a: any): number {
  return a.b.c;
}

export function stable(): number {
  return 1;
}
"""

TS_HEAD = """\
export function pick(a: any): number {
  const v = a?.b?.c?.d;
  if (v) {
    return v;
  }
  return 0;
}

export function stable(): number {
  return 1;
}
"""


def make_fixture(tc):
    repo = mktmp(tc)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
    (repo / "src").mkdir()
    (repo / "src/mod.py").write_text(PY_BASE)
    (repo / "src/util.ts").write_text(TS_BASE)
    (repo / "gone.py").write_text("def bye():\n    return 0\n")
    (repo / "README.md").write_text("hello\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "pr")
    (repo / "src/mod.py").write_text(PY_HEAD)
    (repo / "src/util.ts").write_text(TS_HEAD)
    (repo / "gone.py").unlink()
    (repo / "README.md").write_text("hello world\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "head")
    return repo, base


@NEED_LIZARD
class ChangedFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.repo, self.base = make_fixture(self)
        self.fns = changed_functions(self.repo, self.base)
        self.by = {(f["file"], f["function"]): f for f in self.fns}

    def test_selects_changed_functions_only(self):
        self.assertEqual(set(self.by), {("src/mod.py", "guarded"), ("src/mod.py", "cosmetic"),
                                        ("src/util.ts", "pick")})

    def test_fields(self):
        for f in self.fns:
            self.assertTrue({"file", "function", "start", "end", "ccn", "added_lines", "removed_lines"} <= set(f))
        g = self.by[("src/mod.py", "guarded")]
        self.assertEqual((g["start"], g["end"]), (5, 8))
        self.assertEqual(g["added_lines"], 0)
        self.assertEqual(g["removed_lines"], 2)   # pure deletion inside the body still counts
        c = self.by[("src/mod.py", "cosmetic")]
        self.assertEqual((c["added_lines"], c["removed_lines"]), (2, 2))

    def test_ccn_matches_lizard_for_optional_chaining(self):
        ref = {f.name: f.cyclomatic_complexity
               for f in lizard.analyze_file.analyze_source_code("src/util.ts", TS_HEAD).function_list}
        p = self.by[("src/util.ts", "pick")]
        self.assertEqual(p["ccn"], ref["pick"])
        self.assertEqual(p["ccn"], 2)   # one `if`; `?.` must not inflate it

    def test_ccn_python(self):
        self.assertEqual(self.by[("src/mod.py", "guarded")]["ccn"], 2)

    def test_diff_attached_per_function(self):
        g = self.by[("src/mod.py", "guarded")]
        self.assertIn("-    if i < 0 or i >= len(items):", g["diff"])
        self.assertNotIn("cosmetic", g["diff"])


@NEED_LIZARD
class DeletionEdgeTest(unittest.TestCase):
    def _run(self, name, before, after):
        repo = mktmp(self)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
        (repo / name).write_text(before)
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "b")
        base = git(repo, "rev-parse", "HEAD")
        (repo / name).write_text(after)
        git(repo, "commit", "-qam", "h")
        return {f["function"] for f in changed_functions(repo, base)}

    def test_python_trailing_deletion_counts(self):
        before = "def f(x):\n    y = x\n    log(y)\n    audit(y)\n\n\ndef g():\n    return 0\n"
        after = "def f(x):\n    y = x\n\n\ndef g():\n    return 0\n"
        self.assertEqual(self._run("m.py", before, after), {"f"})

    def test_brace_deletion_after_closing_brace_not_attributed(self):
        before = "function f() {\n  return 1;\n}\nconst junk = 1;\nfunction g() {\n  return 2;\n}\n"
        after = "function f() {\n  return 1;\n}\nfunction g() {\n  return 2;\n}\n"
        self.assertEqual(self._run("m.js", before, after), set())


@NEED_LIZARD
class GitRobustnessTest(unittest.TestCase):
    def _repo(self, files_base, files_head, config=()):
        repo = mktmp(self)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
        for k, v in config:
            git(repo, "config", k, v)
        for name, text in files_base.items():
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_text(text)
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "b")
        base = git(repo, "rev-parse", "HEAD")
        for name, text in files_head.items():
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_text(text)
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "h")
        return repo, base

    B = "def f(x):\n    return x\n"
    H = "def f(x):\n    if x:\n        return 1\n    return x\n"

    def test_user_prefix_config_ignored(self):
        cfg = [("diff.dstPrefix", "x/"), ("diff.srcPrefix", "y/"), ("diff.mnemonicPrefix", "true"),
               ("diff.renames", "copies"), ("color.diff", "always")]
        repo, base = self._repo({"src/m.py": self.B}, {"src/m.py": self.H}, cfg)
        self.assertEqual([(f["file"], f["function"]) for f in changed_functions(repo, base)],
                         [("src/m.py", "f")])

    def test_noprefix_config_ignored(self):
        repo, base = self._repo({"m.py": self.B}, {"m.py": self.H}, [("diff.noprefix", "true")])
        self.assertEqual([f["file"] for f in changed_functions(repo, base)], ["m.py"])

    def test_space_quote_and_unicode_paths(self):
        names = ["dir with space/a b.py", 'q"t.py', "caf\u00e9.py"]
        repo, base = self._repo({n: self.B for n in names}, {n: self.H for n in names})
        self.assertEqual(sorted(f["file"] for f in changed_functions(repo, base)), sorted(names))

    def test_unsupported_files_reported_as_skipped(self):
        repo, base = self._repo({"m.py": self.B, "README.md": "a\n", "c.json": "{}\n", "old.md": "x\n"},
                                {"m.py": self.H, "README.md": "b\n", "c.json": "{\"a\": 1}\n"})
        (repo / "old.md").unlink(); git(repo, "commit", "-qam", "rm")
        fns, skipped = changed_functions_report(repo, base)
        self.assertEqual(sorted(skipped), ["README.md", "c.json"])   # deleted files are not listed
        self.assertEqual([f["file"] for f in fns], ["m.py"])

    def test_unreadable_head_file_raises(self):
        repo, base = self._repo({"m.py": self.B}, {"m.py": self.H})
        real = sentinel._git
        def flaky(cwd, *args):
            if args[:1] == ("show",):
                raise subprocess.CalledProcessError(128, "git show", stderr="fatal: boom")
            return real(cwd, *args)
        with mock.patch.object(sentinel, "_git", flaky):
            with self.assertRaises(RuntimeError):
                changed_functions(repo, base)


@NEED_LIZARD
class NestedFunctionTest(unittest.TestCase):
    BASE = ("def outer(x):\n"
            "    y = 1\n"
            "    def inner(z):\n"
            "        return z + 1\n"
            "    return inner(y)\n")

    def _run(self, head):
        repo = mktmp(self)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
        (repo / "n.py").write_text(self.BASE)
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "b")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "n.py").write_text(head)
        git(repo, "commit", "-qam", "h")
        return {f["function"]: f for f in changed_functions(repo, base)}

    def test_change_inside_inner_only_attributed_to_inner(self):
        out = self._run(self.BASE.replace("z + 1", "z + 2"))
        self.assertEqual(set(out), {"outer.inner"})
        self.assertEqual(out["outer.inner"]["added_lines"], 1)

    def test_outer_kept_when_it_has_own_changes(self):
        out = self._run(self.BASE.replace("z + 1", "z + 2").replace("y = 1", "y = 3"))
        self.assertEqual(set(out), {"outer", "outer.inner"})
        self.assertEqual(out["outer"]["added_lines"], 1)
        self.assertNotIn("z + 2", out["outer"]["diff"])


class JevQuestionsTest(unittest.TestCase):
    FN = {"file": "src/mod.py", "function": "guarded", "start": 5, "end": 8, "ccn": 7,
          "added_lines": 3, "removed_lines": 9}

    def test_questions_exact(self):
        p = jev_questions(self.FN, "@@\n-    if x:\n+    pass\n")
        self.assertEqual(p["questions"], {k: {"type": "noul", "instructions": v} for k, v in QUESTIONS.items()})
        self.assertEqual(QUESTIONS["removes_guard"],
                         "The change removes or weakens a validation, null check, bounds check, or fallback")
        self.assertEqual(set(QUESTIONS), {"changes_public_contract", "removes_guard", "changes_error_handling",
                                          "changes_state_mutation", "is_cosmetic"})
        self.assertEqual(p["model"], "typesafe/jev-1.13")

    def test_state_is_text_only(self):
        diff = "@@ -5,6 +5,4 @@\n-    if i < 0 or i >= len(items):\n-        raise IndexError(i)\n"
        p = jev_questions(self.FN, diff)
        st = p["state"]
        self.assertEqual(set(st), {"file", "function", "diff"})
        self.assertTrue(all(isinstance(v, str) for v in st.values()))
        self.assertNotRegex(st["file"] + st["function"], r"\d")
        self.assertNotRegex(json.dumps({k: v for k, v in st.items() if k != "diff"}), r"\d")
        self.assertNotIn("@@ -5,6 +5,4 @@", st["diff"])   # hunk line numbers are stripped
        self.assertIn("raise IndexError(i)", st["diff"])

    def test_diff_capped(self):
        p = jev_questions(self.FN, "+" + "x" * 10000)
        self.assertLessEqual(len(p["state"]["diff"]), 3000)


def fn(name, ccn=3, added=1, file="a.py"):
    return {"file": file, "function": name, "start": 1, "end": 5, "ccn": ccn, "added_lines": added, "removed_lines": 0}


def ans(contract=0.0, guard=0.0, error=0.0, state=0.0, cosmetic=0.0):
    return {"changes_public_contract": contract, "removes_guard": guard, "changes_error_handling": error,
            "changes_state_mutation": state, "is_cosmetic": cosmetic}


class RankTest(unittest.TestCase):
    def test_guard_removal_above_cosmetic(self):
        fns = [fn("cosmetic"), fn("guard")]
        out = rank(fns, [ans(contract=0.2, cosmetic=0.95), ans(guard=0.97, cosmetic=0.05)])
        self.assertEqual([o["function"] for o in out], ["guard", "cosmetic"])
        self.assertAlmostEqual(out[0]["priority"], 0.97 * 0.95)
        self.assertAlmostEqual(out[1]["priority"], 0.2 * 0.05)
        self.assertEqual(out[0]["jev"], "ok")
        self.assertEqual(out[0]["signals"]["removes_guard"], 0.97)

    def test_uncertain_nouls_do_not_raise_priority(self):
        out = rank([fn("unsure"), fn("sure")], [ans(contract=0.6, guard=0.5), ans(error=0.3)])
        self.assertEqual(out[0]["function"], "sure")
        self.assertAlmostEqual(out[1]["priority"], 0.0)

    def test_ties_by_ccn_then_added(self):
        fns = [fn("a", ccn=2, added=9), fn("b", ccn=5, added=1), fn("c", ccn=5, added=4)]
        out = rank(fns, [ans(guard=0.9)] * 3)
        self.assertEqual([o["function"] for o in out], ["c", "b", "a"])

    def test_failure_path_structural_and_top5(self):
        fns = [fn(f"f{i}", ccn=i * 4) for i in range(8)]
        answers = [None] * 7 + [ans(guard=0.99)]
        out = rank(fns, answers)
        self.assertLessEqual(len(out), 5)
        self.assertEqual(len(out), 5)
        un = [o for o in out if o["jev"] == "unavailable"]
        self.assertTrue(un)
        for o in un:
            self.assertEqual(o["priority"], min(1, o["ccn"] / 20))
        # f7 (jev ok, 0.99) outranks f6/f5 (structural 1.0 is > 0.99, so structural ones come first)
        self.assertEqual([o["function"] for o in out[:3]], ["f6", "f5", "f7"])
        self.assertEqual(out[2]["jev"], "ok")

    def test_does_not_mutate_input(self):
        fns = [fn("a")]
        rank(fns, [ans()])
        self.assertNotIn("priority", fns[0])


class FakeResp:
    def __init__(self, body): self.body = json.dumps(body).encode()
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *a): return False


class JevClientTest(unittest.TestCase):
    def setUp(self):
        self.spend = mktmp(self) / "jev_spend.json"
        self.payload = jev_questions(fn("g"), "-x\n")

    def _ask(self, body):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}), \
             mock.patch("urllib.request.urlopen", return_value=FakeResp(body)) as m:
            out = jev.ask(self.payload, case="c1", function="a.py:g", spend_path=self.spend)
        return out, m

    def test_parses_answers_and_records_spend(self):
        body = {"model": "typesafe/jev-1.13-20260917", "id": "gen-dec-1",
                "answers": {k: {"type": "noul", "noul": 0.1} for k in QUESTIONS},
                "usage": {"input_tokens": 1, "output_tokens": 1, "cost": 0.00001}}
        out, m = self._ask(body)
        self.assertEqual(out, {k: 0.1 for k in QUESTIONS})
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "https://openrouter.ai/api/alpha/decisions")
        self.assertEqual(req.get_header("Authorization"), "Bearer k")
        self.assertEqual(json.loads(req.data)["model"], "typesafe/jev-1.13")
        self.assertEqual(json.loads(self.spend.read_text()),
                         [{"id": "gen-dec-1", "case": "c1", "function": "a.py:g", "cost": 0.00001}])

    def test_missing_cost_raises_unknown_cost(self):
        body = {"id": "gen-dec-2", "answers": {k: {"type": "noul", "noul": 0.1} for k in QUESTIONS},
                "usage": {"input_tokens": 1}}
        with self.assertRaises(jev.JevUnknownCost):
            self._ask(body)
        self.assertFalse(issubclass(jev.JevUnknownCost, jev.JevError))

    def test_missing_answer_is_jev_error(self):
        body = {"id": "gen-dec-3", "answers": {"removes_guard": {"type": "noul", "noul": 0.9}},
                "usage": {"cost": 0.0}}
        with self.assertRaises(jev.JevError):
            self._ask(body)
        self.assertEqual(len(json.loads(self.spend.read_text())), 1)  # still paid, still recorded

    def _http_error(self, code):
        import io, urllib.error
        return urllib.error.HTTPError(jev.URL, code, "err", {}, io.BytesIO(b"x"))

    def test_retries_429_and_5xx_then_succeeds(self):
        body = {"id": "gen-dec-4", "answers": {k: {"type": "noul", "noul": 0.2} for k in QUESTIONS},
                "usage": {"cost": 0.0001}}
        side = [self._http_error(429), self._http_error(503), FakeResp(body)]
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}), \
             mock.patch("urllib.request.urlopen", side_effect=side) as m, \
             mock.patch("time.sleep") as sleep:
            out = jev.ask(self.payload, case="c", function="f", spend_path=self.spend)
        self.assertEqual(m.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 3])
        self.assertEqual(out["removes_guard"], 0.2)

    def test_gives_up_after_two_retries(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}), \
             mock.patch("urllib.request.urlopen", side_effect=[self._http_error(500) for _ in range(3)]) as m, \
             mock.patch("time.sleep"):
            with self.assertRaises(jev.JevError):
                jev.ask(self.payload, case="c", function="f", spend_path=self.spend)
        self.assertEqual(m.call_count, 3)

    def test_no_retry_on_400(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}), \
             mock.patch("urllib.request.urlopen", side_effect=[self._http_error(400)]) as m, \
             mock.patch("time.sleep") as sleep:
            with self.assertRaises(jev.JevError):
                jev.ask(self.payload, case="c", function="f", spend_path=self.spend)
        self.assertEqual(m.call_count, 1)
        sleep.assert_not_called()

    def test_no_key_is_not_silently_unavailable(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as cm:
                jev.ask(self.payload, case="c", function="f", spend_path=self.spend)
        self.assertNotIsInstance(cm.exception, jev.JevError)


@NEED_LIZARD
class HotspotsTest(unittest.TestCase):
    def setUp(self):
        self.repo, self.base = make_fixture(self)
        self.case_dir = mktmp(self) / "case-x"
        self.case_dir.mkdir()
        (self.case_dir / "case.json").write_text(json.dumps({"id": "case-x", "base": self.base}))
        self.calls = []

    def fake_jev(self, payload, *, case, function):
        self.calls.append((payload, case, function))
        if payload["state"]["function"] == "pick":
            raise jev.JevError("boom")
        if payload["state"]["function"] == "guarded":
            return ans(guard=0.97)
        return ans(cosmetic=0.99, contract=0.3)

    def test_partial_not_cached_by_default(self):
        out = hotspots(self.case_dir, self.repo, jev=self.fake_jev)
        self.assertIn("unavailable", {o["jev"] for o in out})
        self.assertFalse((self.case_dir / "hotspots.json").exists())

    def test_complete_result_cached_without_flag(self):
        out = hotspots(self.case_dir, self.repo, jev=lambda p, *, case, function: ans(guard=0.9))
        self.assertEqual(json.loads((self.case_dir / "hotspots.json").read_text()), out)

    def test_writes_hotspots_json(self):
        out = hotspots(self.case_dir, self.repo, jev=self.fake_jev, allow_partial=True)
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(all(c[1] == "case-x" for c in self.calls))
        for payload, _, _ in self.calls:
            self.assertEqual(set(payload["state"]), {"file", "function", "diff"})
        saved = json.loads((self.case_dir / "hotspots.json").read_text())
        self.assertEqual(saved, out)
        self.assertEqual(out[0]["function"], "guarded")
        for item in out:
            self.assertEqual(set(item), {"file", "function", "start", "end", "ccn", "priority", "signals", "jev"})
        pick = next(o for o in out if o["function"] == "pick")
        self.assertEqual(pick["jev"], "unavailable")
        self.assertEqual(pick["priority"], min(1, pick["ccn"] / 20))

    def test_cached(self):
        hotspots(self.case_dir, self.repo, jev=self.fake_jev, allow_partial=True)
        n = len(self.calls)
        hotspots(self.case_dir, self.repo, jev=self.fake_jev, allow_partial=True)
        self.assertEqual(len(self.calls), n)

    def test_unknown_cost_propagates(self):
        def bad(payload, *, case, function):
            raise jev.JevUnknownCost("no cost")
        with self.assertRaises(jev.JevUnknownCost):
            hotspots(self.case_dir, self.repo, jev=bad)
        self.assertFalse((self.case_dir / "hotspots.json").exists())


@unittest.skipUnless(os.environ.get("SENTINEL_LIVE") == "1" and os.environ.get("OPENROUTER_API_KEY"),
                     "live Jev call; set SENTINEL_LIVE=1 and OPENROUTER_API_KEY")
class LiveJevTest(unittest.TestCase):
    def test_live_call(self):
        spend = mktmp(self) / "jev_spend.json"
        payload = jev_questions(fn("guarded"), "@@\n-    if items is None:\n-        return None\n")
        out = jev.ask(payload, case="live-test", function="a.py:guarded", spend_path=spend)
        self.assertEqual(set(out), set(QUESTIONS))
        self.assertTrue(all(0.0 <= v <= 1.0 for v in out.values()))


if __name__ == "__main__":
    unittest.main()
