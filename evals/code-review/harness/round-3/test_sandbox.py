# round-3/test_sandbox.py
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from sandbox import make_snapshot, install_fake_gh

def mktmp(tc):
    d = Path(tempfile.mkdtemp()); tc.addCleanup(shutil.rmtree, d, ignore_errors=True)
    return d

def git(cwd, *a): return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = mktmp(self); src = self.tmp / "src"; src.mkdir()
        git(src, "init", "-q", "-b", "main")
        for i, msg in enumerate(["base", "pr-change", "fix: regression introduced in #1"]):
            (src / "f.txt").write_text(str(i)); git(src, "add", "."); git(src, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)
            if i == 0: self.base = git(src, "rev-parse", "HEAD")
            if i == 1: self.head = git(src, "rev-parse", "HEAD")
        git(src, "tag", "v9")
        self.src = src

    def test_future_commit_unreachable(self):
        snap = make_snapshot(self.src, self.base, self.head, self.tmp / "snap")
        log = git(snap, "log", "--all", "--format=%s")
        self.assertNotIn("regression introduced", log)
        self.assertEqual(git(snap, "rev-parse", "HEAD"), self.head)
        self.assertEqual(git(snap, "tag"), "")
        objs = subprocess.run(["git", "cat-file", "--batch-all-objects", "--batch-check"], cwd=snap, capture_output=True, text=True).stdout
        fix = git(self.src, "rev-parse", "main")
        self.assertNotIn(fix, objs)

    def test_merge_base_works(self):
        snap = make_snapshot(self.src, self.base, self.head, self.tmp / "snap")
        self.assertEqual(git(snap, "merge-base", "origin/main", "HEAD"), self.base)

    def test_no_source_path_in_git_dir(self):
        snap = make_snapshot(self.src, self.base, self.head, self.tmp / "snap")
        self.assertFalse((snap / ".git" / "FETCH_HEAD").exists())
        needles = {str(self.src).encode(), str(self.src.resolve()).encode()}
        pack = snap / ".git" / "objects" / "pack"
        for f in (snap / ".git").rglob("*"):
            if f.is_file() and pack not in f.parents:
                data = f.read_bytes()
                for n in needles:
                    self.assertNotIn(n, data, f"source path leaked in {f}")
        self.assertFalse((snap / ".git" / "logs").exists())
        for cmd in (["reflog", "--all"], ["log", "--all", "--format=%s%n%b"]):
            out = git(snap, *cmd)
            for n in needles:
                self.assertNotIn(n.decode(), out)

class FakeGhTest(unittest.TestCase):
    def test_answers_frozen_and_refuses_rest(self):
        d = mktmp(self)
        case = {"pr": {"number": 7, "title": "T", "body": "B", "baseRefName": "main"}, "diff": "diff --git a/x b/x\n", "issues": {"3": {"title": "I", "body": "IB"}}}
        gh = install_fake_gh(d, case)
        out = json.loads(subprocess.run([gh, "pr", "view", "--json", "title,body"], capture_output=True, text=True).stdout)
        self.assertEqual(out, {"title": "T", "body": "B"})
        self.assertEqual(subprocess.run([gh, "pr", "diff"], capture_output=True, text=True).stdout, case["diff"])
        self.assertIn("IB", subprocess.run([gh, "issue", "view", "3"], capture_output=True, text=True).stdout)
        r = subprocess.run([gh, "api", "repos/x/y/pulls/8"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn("unsupported in benchmark", r.stderr)
        r = subprocess.run([gh, "pr", "view", "8", "--comments"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


DIFF = ("diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1,2 +1,2 @@\n-x = 1\n+x = 2\n+y = 3\n"
        "diff --git a/b.txt b/b.txt\n--- a/b.txt\n+++ b/b.txt\n@@ -1 +0,0 @@\n-gone\n")


class FakeGhCompatTest(unittest.TestCase):
    def setUp(self):
        self.dest = mktmp(self) / "snap"
        self.dest.mkdir()
        self.case = {"repo": "acme/widgets", "head": "abc123",
                     "pr": {"number": 7, "title": "Fix widgets", "body": "Closes #3", "baseRefName": "main",
                            "headRefName": "fix-w", "author": {"login": "dev"}, "state": "OPEN"},
                     "diff": DIFF, "issues": {"3": {"title": "I", "body": "IB"}},
                     "target": {"mechanism": "SECRET-TARGET"}}
        self.gh = install_fake_gh(self.dest, self.case)

    def run_gh(self, *a):
        return subprocess.run([self.gh, *a], capture_output=True, text=True)

    def json_gh(self, *a):
        r = self.run_gh(*a); self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_grading_data_not_under_dest(self):
        for f in self.dest.rglob("*"):
            if f.is_file():
                self.assertNotIn(b"SECRET-TARGET", f.read_bytes(), f"grading key leaked in {f}")
        case_path = Path(self.gh.read_text().split('"')[3]).resolve()
        self.assertTrue(case_path.is_file())
        self.assertNotIn(self.dest.resolve(), case_path.parents)
        self.assertNotIn("target", json.loads(case_path.read_text()))

    def test_repo_flag(self):
        for flag in (["-R", "acme/widgets"], ["--repo", "acme/widgets"], ["--repo=acme/widgets"]):
            self.assertEqual(self.json_gh("pr", "view", "7", *flag, "--json", "title"), {"title": "Fix widgets"})
            self.assertEqual(self.run_gh("pr", "diff", *flag).stdout, DIFF)
            self.assertIn("IB", self.run_gh("issue", "view", "3", *flag).stdout)
        for cmd in (["pr", "view"], ["pr", "diff"], ["issue", "view", "3"]):
            r = self.run_gh(*cmd, "-R", "other/repo")
            self.assertNotEqual(r.returncode, 0); self.assertIn("unsupported in benchmark", r.stderr)

    def test_pr_number_optional(self):
        for ref in ([], ["7"], ["#7"], ["https://github.com/acme/widgets/pull/7"]):
            self.assertEqual(self.json_gh("pr", "view", *ref, "--json", "number"), {"number": 7})
            self.assertEqual(self.run_gh("pr", "diff", *ref).stdout, DIFF)
        self.assertNotEqual(self.run_gh("pr", "diff", "8").returncode, 0)
        self.assertNotEqual(self.run_gh("issue", "view", "4").returncode, 0)

    def test_json_fields(self):
        out = self.json_gh("pr", "view", "--json",
                           "number,title,body,baseRefName,headRefName,headRefOid,url,author,files,additions,deletions,state")
        self.assertEqual(out["headRefOid"], "abc123")
        self.assertEqual(out["headRefName"], "fix-w")
        self.assertEqual(out["url"], "https://github.com/acme/widgets/pull/7")
        self.assertEqual(out["author"], {"login": "dev"})
        self.assertEqual(out["state"], "OPEN")
        self.assertEqual(out["files"], [{"path": "src/a.py", "additions": 2, "deletions": 1},
                                        {"path": "b.txt", "additions": 0, "deletions": 1}])
        self.assertEqual((out["additions"], out["deletions"]), (2, 2))

    def test_unknown_json_field_is_null(self):
        self.assertEqual(self.json_gh("pr", "view", "--json", "title,mergeable"), {"title": "Fix widgets", "mergeable": None})
        self.assertEqual(self.json_gh("issue", "view", "3", "--json", "title,labels"), {"title": "I", "labels": None})

    def test_human_readable_view(self):
        r = self.run_gh("pr", "view")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Fix widgets", r.stdout); self.assertIn("Closes #3", r.stdout)

    def test_still_refuses(self):
        for cmd in (["pr", "view", "--comments"], ["pr", "view", "7", "--comments"], ["pr", "view", "8"],
                    ["pr", "list"], ["api", "repos/acme/widgets/pulls"], ["issue", "list"], ["pr", "checkout", "7"]):
            r = self.run_gh(*cmd)
            self.assertNotEqual(r.returncode, 0, cmd); self.assertIn("unsupported in benchmark", r.stderr)

if __name__ == "__main__": unittest.main()
