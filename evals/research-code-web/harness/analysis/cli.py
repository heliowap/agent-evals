import argparse

from grading.common import load
from .report import write_artifacts


def main():
    parser = argparse.ArgumentParser(description="Analyze sealed trial outcomes; no inference.")
    for name in ("records", "sealed", "schedule", "tasks", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    final = write_artifacts(args.output, load(args.records), load(args.sealed), load(args.schedule), load(args.tasks))
    print("OK: reproducible analysis, final hash " + final["sha256"])


if __name__ == "__main__":
    main()
