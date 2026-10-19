"""Offline verification entrypoint; no broker, candidate inference or live fetch."""
from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parents[3]
    suite = unittest.defaultTestLoader.discover(str(root / "tests" / "webtools"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    sys.exit(main())
