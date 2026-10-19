from pathlib import Path
import sys
import unittest


def main():
    root=Path(__file__).resolve().parent.parent
    suite=unittest.TestLoader().discover(str(root/'tests/integration'),pattern='test_*.py')
    outcome=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if outcome.wasSuccessful() else 1


if __name__=='__main__':
    sys.exit(main())
