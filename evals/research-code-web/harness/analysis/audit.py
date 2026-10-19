import argparse

from .report import audit_artifacts


def main():
    parser = argparse.ArgumentParser(description="Reproduce saved tables from joined sealed inputs, verifying hashes.")
    parser.add_argument("--final", nargs="?", const="fixture", required=True,
                        help="artifact directory/final.json; omit path for explicitly artificial fixture audit")
    args = parser.parse_args()
    if args.final == "fixture":
        from .verify import main as verify
        verify()
        print("PASS: final fixture audit ONLY — no real study artifact audited")
    else:
        final = audit_artifacts(args.final)
        print("PASS: saved hashes and reproduced JSON/Markdown tables " + final["sha256"])


if __name__ == "__main__":
    main()
