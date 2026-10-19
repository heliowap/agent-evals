import argparse

from .common import load
from .sealing import validate_sealed


def main():
    parser = argparse.ArgumentParser(description="Validate grade seals/history/support eligibility, not semantic truth.")
    parser.add_argument("--sealed", nargs="?", const="fixture", required=True,
                        help="sealed JSON; omit path for explicitly artificial fixture audit")
    args = parser.parse_args()
    if args.sealed == "fixture":
        from .verify import main as verify
        verify()
        print("PASS: sealed fixture audit ONLY — no real study artifact audited")
    else:
        document = validate_sealed(load(args.sealed))
        print("PASS: sealed artifact " + document["sha256"])
        print("Review accounting: " + str(document["review_accounting"]))


if __name__ == "__main__":
    main()
