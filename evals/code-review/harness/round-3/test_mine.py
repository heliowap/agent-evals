# round-3/test_mine.py
import copy, json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from mine import (find_fix_links, find_reverted_shas, validate_case, load_case, write_case,
                  restore_snapshot, case_sha256, count_diff_lines)
from sandbox import make_snapshot


def git(cwd, *a): return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def mktmp(tc):
    d = Path(tempfile.mkdtemp()); tc.addCleanup(shutil.rmtree, d, ignore_errors=True)
    return d


def assert_no_path_leak(tc, dest, needles):
    needles = {str(n) for n in needles} | {str(Path(n).resolve()) for n in needles}
    objects = dest / ".git" / "objects"
    for f in (dest / ".git").rglob("*"):
        if f.is_file() and objects not in f.parents:
            data = f.read_bytes()
            for n in needles:
                tc.assertNotIn(n.encode(), data, f"path leaked in {f}")
    for cmd in (["reflog", "--all"], ["log", "--all", "--format=%s%n%b"]):
        out = subprocess.run(["git", *cmd], cwd=dest, capture_output=True, text=True).stdout
        for n in needles:
            tc.assertNotIn(n, out, f"path leaked in git {' '.join(cmd)}")


def make_diff(n_added, n_removed=0):
    lines = ["diff --git a/f.py b/f.py", "--- a/f.py", "+++ b/f.py", f"@@ -1,{n_removed} +1,{n_added} @@"]
    lines += [f"-old{i}" for i in range(n_removed)] + [f"+new{i}" for i in range(n_added)]
    return "\n".join(lines) + "\n"


REPRO = {"kind": "test", "path": "repro/test_x.py", "command": "python -m pytest repro/test_x.py", "expected": "fail at head"}
TARGET = {"file": "f.py", "lines": [3, 5], "mechanism": "off-by-one", "consequence": "drops last item",
          "equivalents": ["boundary error"], "repro": REPRO}


def base_case(kind="tracked"):
    return {
        "id": "py-requests-1", "kind": kind, "repo": "psf/requests", "language": "python",
        "pr": {"number": 1, "title": "T", "body": "B", "baseRefName": "main",
               "merged_at": "2026-04-01T00:00:00Z", "url": "https://github.com/psf/requests/pull/1"},
        "base": "a" * 40, "head": "b" * 40, "diff": make_diff(30), "issues": {},
        "target": copy.deepcopy(TARGET) if kind in ("tracked", "mutation") else None,
        "fix_ref": "https://github.com/psf/requests/pull/2" if kind == "tracked" else None,
        "maintainer_comments": [],
    }


class FindFixLinksTest(unittest.TestCase):
    def test_patterns(self):
        self.assertEqual(find_fix_links("Fix regression introduced in #123"), [123])
        self.assertEqual(find_fix_links("Reverts owner/repo#45"), [45])
        self.assertEqual(find_fix_links("caused by #9 and broke in #10"), [9, 10])
        self.assertEqual(find_fix_links("Fixes #88"), [])  # plain issue fix is not a regression link

    def test_more_patterns(self):
        self.assertEqual(find_fix_links("regression caused by #7"), [7])
        self.assertEqual(find_fix_links("Regression Introduced By #8"), [8])
        self.assertEqual(find_fix_links("Reverts #3"), [3])
        self.assertEqual(find_fix_links("This fixes bug from #55."), [55])
        self.assertEqual(find_fix_links("broke in https://github.com/o/r/pull/77"), [77])

    def test_order_and_dedup(self):
        self.assertEqual(find_fix_links("broke in #10; regression introduced in #9; reverts #10"), [10, 9])

    def test_revert_commit_not_a_pr_link(self):
        msg = "Revert \"x\"\n\nThis reverts commit 0123456789abcdef0123456789abcdef01234567."
        self.assertEqual(find_fix_links(msg), [])
        self.assertEqual(find_reverted_shas(msg), ["0123456789abcdef0123456789abcdef01234567"])
        self.assertEqual(find_reverted_shas("This reverts commit abc1234"), ["abc1234"])
        self.assertEqual(find_reverted_shas("This reverts commit abc12"), [])
        self.assertEqual(find_reverted_shas("nothing here"), [])

    def test_strict_weak_verbs(self):
        self.assertEqual(find_fix_links("feature introduced in #5"), [])
        self.assertEqual(find_fix_links("Port code from #6"), [])
        self.assertEqual(find_fix_links("fixes a bug introduced in #5"), [5])
        self.assertEqual(find_fix_links("Handle the bug from #6"), [6])
        self.assertEqual(find_fix_links("Feature introduced in #5. This regressed perf."), [])
        self.assertEqual(find_fix_links("Regressed perf. Caused by #5"), [])  # keyword in another sentence
        self.assertEqual(find_fix_links("Perf regressed, caused by #5"), [5])

    def test_unrelated_mentions(self):
        self.assertEqual(find_fix_links("See #12, related to #13, closes #14"), [])


class ValidateCaseTest(unittest.TestCase):
    def assertInvalid(self, case, needle):
        with self.assertRaises(ValueError) as cm:
            validate_case(case)
        self.assertIn(needle, str(cm.exception))

    def test_valid_kinds(self):
        for kind in ("tracked", "clean", "mutation", "injection"):
            validate_case(base_case(kind))

    def test_tracked_mutation_need_repro(self):
        for kind in ("tracked", "mutation"):
            c = base_case(kind); c["target"] = None
            self.assertInvalid(c, "target")
            c = base_case(kind); del c["target"]["repro"]
            self.assertInvalid(c, "repro")
            c = base_case(kind); c["target"]["repro"]["kind"] = "vibes"
            self.assertInvalid(c, "repro")

    def test_clean_injection_need_null_target(self):
        for kind in ("clean", "injection"):
            c = base_case(kind); c["target"] = copy.deepcopy(TARGET)
            self.assertInvalid(c, "target")

    def test_bad_kind(self):
        c = base_case(); c["kind"] = "other"
        self.assertInvalid(c, "kind")

    def test_diff_size_bounds(self):
        c = base_case(); c["diff"] = make_diff(10, 10); validate_case(c)  # 20 ok
        c["diff"] = make_diff(400, 400); validate_case(c)  # 800 ok
        c["diff"] = make_diff(10, 9); self.assertInvalid(c, "diff")
        c["diff"] = make_diff(401, 400); self.assertInvalid(c, "diff")

    def test_count_ignores_headers(self):
        self.assertEqual(count_diff_lines(make_diff(3, 2)), 5)

    def test_sha_format(self):
        for field, val in (("base", "a" * 39), ("head", "B" * 40), ("head", "g" * 40), ("base", None)):
            c = base_case(); c[field] = val
            self.assertInvalid(c, field)

    def test_owner_rejected(self):
        for repo in ("<user>/thing", "<user>/thing"):
            c = base_case(); c["repo"] = repo
            self.assertInvalid(c, "<user>")
        c = base_case(); c["repo"] = "notarepo"
        self.assertInvalid(c, "repo")

    def test_sha256_format(self):
        c = base_case(); c["sha256"] = case_sha256(c); validate_case(c)
        for bad in ("A" * 64, "a" * 63, "", None, 5):
            c = base_case(); c["sha256"] = bad
            self.assertInvalid(c, "sha256")

    def test_missing_key(self):
        c = base_case(); del c["maintainer_comments"]
        self.assertInvalid(c, "maintainer_comments")

    def test_bad_id(self):
        c = base_case(); c["id"] = "../escape"
        self.assertInvalid(c, "id")


class LoadCaseTest(unittest.TestCase):
    def test_hash_roundtrip_and_mismatch(self):
        d = mktmp(self)
        c = base_case(); c["sha256"] = case_sha256(c)
        p = d / "case.json"; p.write_text(json.dumps(c))
        self.assertEqual(load_case(p), c)
        self.assertEqual(load_case(d), c)  # directory form
        c["pr"]["title"] = "tampered"; p.write_text(json.dumps(c))
        with self.assertRaises(ValueError):
            load_case(p)

    def test_missing_hash_raises(self):
        d = mktmp(self); p = d / "case.json"
        p.write_text(json.dumps(base_case()))
        with self.assertRaises(ValueError):
            load_case(p)

    def test_invalid_case_with_valid_hash_raises(self):
        d = mktmp(self); p = d / "case.json"
        c = base_case(); c["repo"] = "<user>/x"; c["sha256"] = case_sha256(c)
        p.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError, "<user>"):
            load_case(p)

    def test_hash_is_canonical(self):
        c = base_case()
        shuffled = dict(reversed(list(c.items())))
        self.assertEqual(case_sha256(c), case_sha256(shuffled))
        self.assertEqual(case_sha256(c), case_sha256({**c, "sha256": "whatever"}))


class WriteRestoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = mktmp(self); src = self.tmp / "src"; src.mkdir()
        git(src, "init", "-q", "-b", "main")
        for i, msg in enumerate(["base", "pr-change", "fix: regression introduced in #1"]):
            (src / "f.txt").write_text(str(i)); git(src, "add", "."); git(src, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)
            if i == 0: self.base = git(src, "rev-parse", "HEAD")
            if i == 1: self.head = git(src, "rev-parse", "HEAD")
        self.fix = git(src, "rev-parse", "HEAD")
        self.snap = make_snapshot(src, self.base, self.head, self.tmp / "snap")
        self.case = base_case(); self.case["base"] = self.base; self.case["head"] = self.head

    def test_write_then_restore(self):
        out = self.tmp / "cases"
        cdir = write_case(self.case, self.snap, out)
        self.assertEqual(cdir, (out / self.case["id"]).resolve())
        self.assertTrue((cdir / "repo.bundle").is_file())
        loaded = load_case(cdir / "case.json")
        self.assertEqual(loaded["sha256"], case_sha256(loaded))
        self.assertNotIn("sha256", self.case)  # caller's dict not mutated

        dest = restore_snapshot(cdir, self.tmp / "restored")
        self.assertEqual(git(dest, "rev-parse", "HEAD"), self.head)
        self.assertEqual(git(dest, "rev-parse", "--abbrev-ref", "HEAD"), "pr")
        self.assertEqual(git(dest, "rev-parse", "refs/remotes/origin/main"), self.base)
        self.assertEqual(git(dest, "merge-base", "origin/main", "HEAD"), self.base)
        self.assertEqual(sorted(git(dest, "rev-list", "--all").split()), sorted([self.base, self.head]))
        self.assertNotIn("regression introduced", git(dest, "log", "--all", "--format=%s"))
        self.assertEqual(git(dest, "tag"), "")
        self.assertEqual(git(dest, "remote"), "")  # no pointer back to the bundle path
        self.assertFalse((dest / ".git" / "FETCH_HEAD").exists())
        self.assertFalse((dest / ".git" / "logs").exists())
        assert_no_path_leak(self, dest, [cdir, cdir / "repo.bundle", out, self.tmp / "src"])

    def test_snapshot_no_path_leak(self):
        self.assertFalse((self.snap / ".git" / "logs").exists())
        assert_no_path_leak(self, self.snap, [self.tmp / "src"])
        self.assertFalse((self.snap / ".git" / "hooks").exists())  # --template=

    def test_write_rejects_invalid(self):
        self.case["repo"] = "<user>/x"
        with self.assertRaises(ValueError):
            write_case(self.case, self.snap, self.tmp / "cases")
        self.assertFalse((self.tmp / "cases" / self.case["id"]).exists())

    def test_write_rejects_snapshot_mismatch(self):
        self.case["head"] = self.fix
        with self.assertRaises(ValueError):
            write_case(self.case, self.snap, self.tmp / "cases")

    def test_restore_detects_tampered_case(self):
        cdir = write_case(self.case, self.snap, self.tmp / "cases")
        data = json.loads((cdir / "case.json").read_text()); data["head"] = self.base
        (cdir / "case.json").write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            restore_snapshot(cdir, self.tmp / "restored")


if __name__ == "__main__":
    unittest.main()
