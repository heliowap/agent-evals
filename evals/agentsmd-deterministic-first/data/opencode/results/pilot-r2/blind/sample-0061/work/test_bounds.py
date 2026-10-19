import unittest
from bounds import clamp

class BoundsTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-2, 0, 10), 0)
        self.assertEqual(clamp(12, 0, 10), 10)
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)

    def test_equal_bounds(self):
        for value in (-2, 5, 12):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 5, 5), 5)

    def test_reversed_bounds(self):
        for value in (-2, 5, 12):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 10, 0)
