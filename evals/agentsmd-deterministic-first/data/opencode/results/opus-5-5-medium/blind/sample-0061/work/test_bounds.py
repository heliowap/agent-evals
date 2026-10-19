import unittest
from bounds import clamp

class BoundsTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-2, 0, 10), 0)
        self.assertEqual(clamp(12, 0, 10), 10)

    def test_equal_bounds(self):
        self.assertEqual(clamp(5, 3, 3), 3)
        self.assertEqual(clamp(1, 3, 3), 3)

    def test_low_greater_than_high_raises(self):
        with self.assertRaises(ValueError):
            clamp(5, 10, 0)
        with self.assertRaises(ValueError):
            clamp(5, 1, 0)

