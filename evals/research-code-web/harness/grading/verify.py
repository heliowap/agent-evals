"""Run public-interface offline fixtures; no inference."""

import unittest
from pathlib import Path


def main():
    directory = Path(__file__).resolve().parent.parent / "tests" / "grading"
    suite = unittest.defaultTestLoader.discover(str(directory), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: grading public-interface fixtures (artificial data; no inference)")


if __name__ == "__main__":
    main()
