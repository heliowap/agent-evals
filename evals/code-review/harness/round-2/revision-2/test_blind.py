"""Prevent metadata leakage into case-level adjudication packets."""

import importlib
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class BlindPacketsTests(unittest.TestCase):
    def test_masks_model_route_and_repetition_but_preserves_literal_answer(self):
        self.assertTrue((HERE / "blind.py").is_file(), "blind.py must exist")
        blind = importlib.import_module("blind")
        results = [
            {"cell_id": "a-1", "case": "case-a", "axis": "spec", "model": "openai/gpt-6-sol#high",
             "repeat": 1, "answer": "The actual result is 42."},
            {"cell_id": "a-2", "case": "case-a", "axis": "spec", "model": "openrouter/z-ai/glm-5.3-flash#high",
             "repeat": 2, "answer": "No supported findings"},
        ]
        packets, mapping = blind.make_packets(results, seed=20260926)
        self.assertEqual(packets, blind.make_packets(results, seed=20260926)[0])
        self.assertEqual({p["answer"] for p in packets}, {r["answer"] for r in results})
        self.assertEqual({p["blind_id"] for p in packets}, set(mapping))
        self.assertEqual({mapping[p["blind_id"]] for p in packets}, {"a-1", "a-2"})
        self.assertEqual({p["case"] for p in packets}, {"case-a"})
        self.assertEqual({p["axis"] for p in packets}, {"spec"})
        for packet in packets:
            self.assertEqual(set(packet), {"blind_id", "case", "axis", "answer"})
            self.assertNotIn("openrouter", repr(packet))
            self.assertNotIn("gpt-6-sol", repr(packet))

    def test_shuffles_within_case_without_leaking_identity_between_cases(self):
        blind = importlib.import_module("blind")
        results = [{"cell_id": f"a-{i}", "case": "a", "axis": "spec", "answer": str(i)}
                   for i in range(12)] + [{"cell_id": f"b-{i}", "case": "b", "axis": "standards",
                                           "answer": str(i)} for i in range(12)]
        packets, mapping = blind.make_packets(results, seed=3)
        self.assertEqual([p["case"] for p in packets], ["a"] * 12 + ["b"] * 12)
        self.assertNotEqual([p["answer"] for p in packets[:12]], [str(i) for i in range(12)])
        self.assertNotEqual([p["answer"] for p in packets[12:]], [str(i) for i in range(12)])


if __name__ == "__main__":
    unittest.main()
