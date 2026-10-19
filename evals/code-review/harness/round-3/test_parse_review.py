import unittest

from parse_review import parse_review


class ParseTest(unittest.TestCase):
    def test_contract(self):
        r = parse_review("BLOCKING\n- src/a.py:10 — breaks X\n\nWARNING\n(none)\n\nNIT\n- b.go:3 — name\n\nSUMMARY: 1 BLOCKING, 0 WARNING, 1 NIT")
        self.assertTrue(r["format_ok"])
        self.assertEqual([(f["severity"], f["path"], f["line"]) for f in r["findings"]], [("BLOCKING","src/a.py",10),("NIT","b.go",3)])
    def test_markdown_headers_and_ranges(self):
        r = parse_review("## BLOCKING\n* `src/a.py:10-14` breaks\n## WARNING\n- none\n## NIT\n(none)\nSUMMARY: 1 BLOCKING, 0 WARNING, 0 NIT")
        self.assertEqual(r["findings"][0]["line"], 10)
    def test_missing_summary_and_path(self):
        r = parse_review("BLOCKING\n- the loop never ends\n")
        self.assertFalse(r["format_ok"]); self.assertEqual(r["findings"][0]["path"], None)
        self.assertIn("missing SUMMARY", r["problems"]); self.assertIn("finding without path:line", r["problems"])
    def test_summary_mismatch(self):
        r = parse_review("BLOCKING\n(none)\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 2 BLOCKING, 0 WARNING, 0 NIT")
        self.assertFalse(r["format_ok"]); self.assertIn("SUMMARY count mismatch", r["problems"])
    def test_multiline_finding(self):
        r = parse_review("BLOCKING\n- a.rs:5 — first line\n  continues here\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 1 BLOCKING, 0 WARNING, 0 NIT")
        self.assertIn("continues here", r["findings"][0]["text"])

    # extra tests
    def test_preamble_ignored(self):
        r = parse_review("I reviewed the diff.\nHere is my report:\n\nBLOCKING\n- a.py:1 — bad\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 1 BLOCKING, 0 WARNING, 0 NIT")
        self.assertTrue(r["format_ok"], r["problems"])
        self.assertEqual([(f["severity"], f["path"], f["line"]) for f in r["findings"]], [("BLOCKING", "a.py", 1)])

    def test_none_variants(self):
        for v in ["(none)", "none", "- none", "_None_", "* (None)", "None."]:
            with self.subTest(v=v):
                r = parse_review(f"BLOCKING\n{v}\nWARNING\n{v}\nNIT\n{v}\nSUMMARY: 0 BLOCKING, 0 WARNING, 0 NIT")
                self.assertEqual(r["findings"], [])
                self.assertTrue(r["format_ok"], r["problems"])

    def test_extensionless_paths(self):
        r = parse_review("BLOCKING\n- Makefile:3 — bad target\nWARNING\n- docker/Dockerfile:10 — root user\nNIT\n(none)\nSUMMARY: 1 BLOCKING, 1 WARNING, 0 NIT")
        self.assertTrue(r["format_ok"], r["problems"])
        self.assertEqual([(f["path"], f["line"]) for f in r["findings"]], [("Makefile", 3), ("docker/Dockerfile", 10)])

    def test_never_crashes(self):
        for t in ["", "   \n", None, "SUMMARY: x", "BLOCKING", "- a.py:1", "\x00\ufeff##"]:
            with self.subTest(t=t):
                r = parse_review(t)
                self.assertFalse(r["format_ok"])

    def test_unbulleted_blocking_not_dropped(self):
        r = parse_review("BLOCKING\nsrc/a.py:4 breaks auth\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 1 BLOCKING, 0 WARNING, 0 NIT")
        self.assertEqual(r["findings"][0]["severity"], "BLOCKING")
        self.assertEqual(r["findings"][0]["path"], "src/a.py")
        self.assertFalse(r["format_ok"])

    def test_summary_not_last(self):
        r = parse_review("BLOCKING\n(none)\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 0 BLOCKING, 0 WARNING, 0 NIT\nthanks!")
        self.assertFalse(r["format_ok"])
        self.assertEqual(r["summary"], {"BLOCKING": 0, "WARNING": 0, "NIT": 0})

    # fix round 1 regressions
    def test_summary_word_inside_section(self):
        r = parse_review("BLOCKING\nSummary: this breaks auth\n- a.py:2 — later\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 2 BLOCKING, 0 WARNING, 0 NIT")
        self.assertEqual([f["severity"] for f in r["findings"]], ["BLOCKING", "BLOCKING"])
        self.assertEqual(r["findings"][1]["path"], "a.py")
        self.assertNotIn("SUMMARY count mismatch", r["problems"])

    def test_inline_headers(self):
        r = parse_review("BLOCKING: - a.py:1 bug\nWARNING:\n- b.py:2 — w\nNIT: (none)\nSUMMARY: 1 BLOCKING, 1 WARNING, 0 NIT")
        self.assertTrue(r["format_ok"], r["problems"])
        self.assertEqual([(f["severity"], f["path"]) for f in r["findings"]], [("BLOCKING", "a.py"), ("WARNING", "b.py")])

    def test_indented_bullet_without_path_is_new_finding(self):
        r = parse_review("BLOCKING\n- a.py:1 — x\n  - loop never ends\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 2 BLOCKING, 0 WARNING, 0 NIT")
        self.assertEqual(len(r["findings"]), 2)
        self.assertIsNone(r["findings"][1]["path"])

    def test_backticked_path_and_urls(self):
        r = parse_review("BLOCKING\n- `a.py`:10 — x\n- see http://host:8080 then b.py:3\nWARNING\n(none)\nNIT\n(none)\nSUMMARY: 2 BLOCKING, 0 WARNING, 0 NIT")
        self.assertEqual([(f["path"], f["line"]) for f in r["findings"]], [("a.py", 10), ("b.py", 3)])

    # fix round 2
    def test_prose_starting_with_severity_word_stays_in_section(self):
        r = parse_review("BLOCKING\n- a.py:1 — x\nNit-picky but real: b.py:2 leaks\nWarning: c.py:3 also bad\n")
        self.assertEqual([(f["severity"], f["path"]) for f in r["findings"]],
                         [("BLOCKING", "a.py"), ("BLOCKING", "b.py"), ("BLOCKING", "c.py")])

    def test_uppercase_inline_header_with_dash(self):
        r = parse_review("BLOCKING\n(none)\nWARNING — c.py:3 bad\nNIT: (none)\nSUMMARY: 0 BLOCKING, 1 WARNING, 0 NIT")
        self.assertEqual(r["findings"][0]["severity"], "WARNING")


if __name__ == "__main__":
    unittest.main()
