import unittest
from bounds import clamp

class BoundsTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-2, 0, 10), 0)
        self.assertEqual(clamp(12, 0, 10), 10)
