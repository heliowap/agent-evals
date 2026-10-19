import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

import placebo
import skills

HERE = Path(__file__).resolve().parent
A_SHA256 = "f757bfeb6bf7b7a4e3d5511410b76c9067cc7e8a64391ce3cdf7d3a41e917f82"  # gh-agents aac254a


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def output_contract(text):
    return text[text.index("## Output contract"):]


HOT = [
    {"file": "a.py", "function": "f", "start": 40, "end": 72, "ccn": 3, "priority": 1.0},
    {"file": "b/c.py", "function": "g", "start": 1, "end": 9},
]


class TestSkillText(unittest.TestCase):
    def test_a_byte_identical(self):
        data = (HERE / "skills/A/SKILL.md").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), A_SHA256)
        self.assertEqual(skills.skill_text("A"), data.decode())

    def test_b_keeps_output_contract(self):
        a = skills.skill_text("A")
        b = skills.skill_text("B")
        self.assertNotEqual(a, b)
        self.assertIn(output_contract(a), b)
        self.assertTrue(b.endswith(output_contract(a)))

    def test_render(self):
        r = skills.render_hotspots(HOT)
        self.assertEqual(r, (
            "## Review priority hints\n\n"
            "Automated triage suggests reading these changed functions first. "
            "Hints are not findings: report only what you verify in the code.\n\n"
            "1. `a.py::f` (lines 40\u201372)\n"
            "2. `b/c.py::g` (lines 1\u20139)\n"))

    def test_c_and_d_append_only(self):
        b = skills.skill_text("B")
        c = skills.skill_text("C", hotspots=HOT)
        d = skills.skill_text("D", placebo=HOT[1:])
        self.assertTrue(c.startswith(b))
        self.assertTrue(d.startswith(b))
        self.assertEqual(c[len(b):].lstrip("\n"), skills.render_hotspots(HOT))
        self.assertEqual(d[len(b):].lstrip("\n"), skills.render_hotspots(HOT[1:]))

    def test_errors(self):
        for kw in [("C", {}), ("D", {}), ("E", {})]:
            with self.assertRaises(ValueError):
                skills.skill_text(kw[0], **kw[1])

    def test_d_length_must_match_hotspots(self):
        with self.assertRaises(ValueError):
            skills.skill_text("D", hotspots=HOT, placebo=HOT[1:])
        self.assertEqual(skills.skill_text("D", hotspots=HOT, placebo=HOT[::-1]),
                         skills.skill_text("D", placebo=HOT[::-1]))


class TestPlacebo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        repo = Path(cls.tmp.name)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
        n = 12
        (repo / "m.py").write_text("".join(f"def f{i}(x):\n    return x\n\n\n" for i in range(n)))
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "base")
        cls.base = git(repo, "rev-parse", "HEAD")
        (repo / "m.py").write_text("".join(f"def f{i}(x):\n    return x + {i}\n\n\n" for i in range(n)))
        git(repo, "commit", "-qam", "head")
        cls.repo = repo
        cls.n = n

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_k_and_keys(self):
        p = placebo.placebo_hotspots(self.repo, self.base, 3, "s1")
        self.assertEqual(len(p), 3)
        self.assertEqual(len({(x["file"], x["function"]) for x in p}), 3)
        for x in p:
            self.assertEqual(set(x), {"file", "function", "start", "end"})

    def test_deterministic(self):
        a = placebo.placebo_hotspots(self.repo, self.base, 4, "seed")
        b = placebo.placebo_hotspots(self.repo, self.base, 4, "seed")
        self.assertEqual(a, b)

    def test_seeds_differ(self):
        outs = {tuple(x["function"] for x in placebo.placebo_hotspots(self.repo, self.base, 3, f"s{i}"))
                for i in range(10)}
        self.assertGreater(len(outs), 1)

    def test_k_larger_than_pool(self):
        pool = placebo.changed_pool(self.repo, self.base)
        key = lambda x: (x["file"], x["function"], x["start"])
        orders = set()
        for i in range(5):
            p = placebo.placebo_hotspots(self.repo, self.base, 100, f"x{i}")
            self.assertEqual(p, placebo.placebo_hotspots(self.repo, self.base, 100, f"x{i}"))
            self.assertEqual(len(p), self.n)
            self.assertEqual({key(x) for x in p}, {key(x) for x in pool})
            orders.add(tuple(map(key, p)))
        self.assertTrue(any(o != tuple(map(key, pool)) for o in orders))

    def test_pool_deduped(self):
        pool = placebo.changed_pool(self.repo, self.base)
        keys = [(x["file"], x["function"], x["start"]) for x in pool]
        self.assertEqual(len(keys), len(set(keys)))

    def test_overlap(self):
        a = [{"file": "a", "function": "f", "start": 1, "end": 2},
             {"file": "a", "function": "g", "start": 5, "end": 6}]
        b = [{"file": "a", "function": "f", "start": 1, "end": 9},
             {"file": "a", "function": "h", "start": 8, "end": 9}]
        self.assertAlmostEqual(placebo.placebo_overlap(a, b), 1 / 3)
        self.assertEqual(placebo.placebo_overlap(a, a), 1.0)
        self.assertEqual(placebo.placebo_overlap([], []), 0.0)


if __name__ == "__main__":
    unittest.main()
