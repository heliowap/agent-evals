from collections import Counter
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import bench
import runtime


IDS = ("sol-fast-low", "deepseek-max", "sonnet-low", "sonnet-medium", "sonnet-high", "opus-low", "opus-medium")
CANDIDATES = tuple(SimpleNamespace(id=name) for name in IDS)


def freeze(out, selected, reps, candidates):
    rows = bench.schedule(selected, reps, 20261010, candidates)
    runtime.save(out / "freeze.json", {"schedule": rows, "cases": {case: {} for case in selected},
                                       "repetitions": reps,
                                       "candidates": [{"id": c.id, "fast": c.id == "sol-fast-low"} for c in candidates],
                                       "settings": {"observation_mode": "passive_native_provider"}})
    return rows


def completed(out, row, passed, seconds, tier="unknown"):
    target = out / row["id"]
    target.mkdir()
    runtime.save(target / "result.json", {**row, "status": "completed", "passed": passed,
                                          "wall_s": seconds, "transport": {"fast_served": tier}})


class MatrixSchedule(unittest.TestCase):
    def test_default_cohort_keeps_original_seven_and_210_trials(self):
        self.assertEqual(tuple(c.id for c in runtime.DEFAULT_CANDIDATES), IDS)
        rows = bench.schedule(["route", "config", "retry", "permission", "feature", "absence"], 5, 20261010)
        self.assertEqual(len(rows), 210)
        self.assertEqual({r["candidate"] for r in rows}, set(IDS))

    def test_requested_four_configs_cover_120_trials(self):
        ids = ("sonnet-xhigh", "sol-fast-medium", "gemini-medium", "gemini-high")
        selected = tuple(next(c for c in runtime.CANDIDATES if c.id == name) for name in ids)
        self.assertEqual(len({c.id for c in runtime.CANDIDATES}), 11)
        self.assertEqual(tuple(c.selection for c in selected), (
            "cli_proxy/cpa-claude-sonnet-5-5#xhigh", "openai/gpt-6.1-sol-fast#medium",
            "cli_proxy_google/gemini-3.8-flash#medium", "cli_proxy_google/gemini-3.8-flash#high"))
        rows = bench.schedule(["route", "config", "retry", "permission", "feature", "absence"], 5, 20261010, selected)
        self.assertEqual(len(rows), 120)
        self.assertEqual(len({(r["case"], r["rep"], r["candidate"]) for r in rows}), 120)
        for offset in range(0, len(rows), 4):
            block = rows[offset:offset + 4]
            self.assertEqual(len({(r["pair"], r["case"], r["rep"]) for r in block}), 1)
            self.assertEqual({r["candidate"] for r in block}, set(ids))
        for position in range(4):
            counts = Counter(r["candidate"] for r in rows if r["position"] == position)
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_seven_candidates_cover_210_trials_and_every_block(self):
        cases = ["route", "config", "retry", "permission", "feature", "absence"]
        rows = bench.schedule(cases, 5, 20261010, CANDIDATES)
        self.assertEqual(len(rows), 210)
        self.assertEqual(len({(r["case"], r["rep"], r["candidate"]) for r in rows}), 210)
        self.assertEqual([r["id"] for r in rows], [f"trial-{i:04d}" for i in range(1, 211)])
        for offset in range(0, len(rows), 7):
            block = rows[offset:offset + 7]
            self.assertEqual(len({(r["pair"], r["case"], r["rep"]) for r in block}), 1)
            self.assertEqual({r["candidate"] for r in block}, set(IDS))
            self.assertEqual([r["position"] for r in block], list(range(7)))
        for position in range(7):
            counts = Counter(r["candidate"] for r in rows if r["position"] == position)
            self.assertEqual(set(counts), set(IDS))
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_seed_is_reproducible_and_subset_remains_balanced(self):
        selected = CANDIDATES[2:5]
        first = bench.schedule(["route", "retry"], 4, 17, selected)
        self.assertEqual(first, bench.schedule(["route", "retry"], 4, 17, selected))
        self.assertNotEqual(first, bench.schedule(["route", "retry"], 4, 18, selected))
        self.assertEqual(len(first), 24)
        for position in range(3):
            counts = Counter(r["candidate"] for r in first if r["position"] == position)
            self.assertEqual(sorted(counts.values()), [2, 3, 3])

    def test_empty_and_duplicate_candidates_are_rejected(self):
        for candidates in [(), (CANDIDATES[0], CANDIDATES[0])]:
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                bench.schedule(["route"], 1, 17, candidates)


class MatrixReports(unittest.TestCase):
    def test_pairwise_comparison_needs_only_the_two_selected_correct_results(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            rows = freeze(out, ["route"], 2, CANDIDATES)
            for row in rows:
                if row["candidate"] == "sonnet-low":
                    completed(out, row, True, 10)
                elif row["candidate"] == "opus-low":
                    completed(out, row, row["rep"] == 1, 20)
                elif row["candidate"] == "deepseek-max":
                    target = out / row["id"]
                    target.mkdir()
                    runtime.save(target / "result.json", {**row, "status": "timeout", "passed": False, "wall_s": 300})
            summary = bench.report(out)
            self.assertEqual(len(summary["pairwise"]), 21)
            chosen = next(p for p in summary["pairwise"] if (p["a"], p["b"]) == ("sonnet-low", "opus-low"))
            self.assertEqual(chosen["paired_success_count"], 1)
            self.assertEqual(chosen["median_a_over_b"], 0.5)
            self.assertEqual(chosen["faster_counts"], {"sonnet-low": 1, "opus-low": 0, "ties": 0})
            self.assertEqual(summary["by_candidate"]["opus-low"]["incorrect"], 1)
            self.assertEqual(summary["by_candidate"]["deepseek-max"]["errors"], 2)
            self.assertEqual(summary["by_candidate"]["sol-fast-low"]["missing"], 2)
            self.assertEqual(summary["verdict"], "inconclusive")
            self.assertEqual(summary["statuses"], {"completed": 4, "not_run": 8, "timeout": 2})

    def test_report_uses_only_frozen_inventory_even_if_live_registry_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            rows = freeze(out, ["route"], 1, CANDIDATES[2:4])
            for row in rows:
                completed(out, row, True, 10)
            with mock.patch.object(runtime, "CANDIDATES", CANDIDATES):
                summary = bench.report(out)
            self.assertEqual(list(summary["by_candidate"]), ["sonnet-low", "sonnet-medium"])
            self.assertEqual(len(summary["pairwise"]), 1)
            self.assertEqual(summary["pairwise"][0]["faster_counts"], {"sonnet-low": 0, "sonnet-medium": 0, "ties": 1})
            self.assertFalse(summary["fast_served_confirmed"])
            self.assertTrue(summary["all_tasks_completed"])

    def test_historical_two_model_smoke_keeps_legacy_metrics_without_extra_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            rows = bench.schedule(["route"], 1, 17, CANDIDATES[:2])
            runtime.save(out / "freeze.json", {"schedule": rows, "cases": {"route": {}}, "repetitions": 1})
            for row in rows:
                completed(out, row, True, 10 if row["candidate"] == "sol-fast-low" else 20)
            with mock.patch.object(runtime, "CANDIDATES", CANDIDATES):
                summary = bench.report(out)
            self.assertEqual(set(summary["by_candidate"]), set(IDS[:2]))
            self.assertEqual(summary["by_case"]["route"]["median_sol_over_deepseek"], 0.5)
            self.assertEqual(summary["paired_passed"], [{"case": "route", "rep": 1, "sol_over_deepseek": 0.5}])
            self.assertEqual(summary["observation_mode"], "forwarding_proxy")
            self.assertNotIn("sem redirecionar", (out / "report.md").read_text())

    def test_mixed_fast_metadata_never_confirms_all_tasks(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            rows = freeze(out, ["route"], 2, CANDIDATES[:2])
            for row in rows:
                completed(out, row, True, 10, "confirmed" if row["rep"] == 1 else "unknown")
            self.assertFalse(bench.report(out)["fast_served_confirmed"])

    def test_frozen_inventory_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            bench.candidate_inventory({"candidates": [{"id": "sol-fast-low"}], "schedule": [{"candidate": "sonnet-low"}]})

    def test_redaction_removes_all_oauth_secrets_with_overlapping_values(self):
        self.assertEqual(bench.redact("token-long token refresh", ["token", "token-long", "refresh"]),
                         "<REDACTED> <REDACTED> <REDACTED>")
        self.assertEqual(bench.redact("unchanged", None), "unchanged")


if __name__ == "__main__":
    unittest.main()
