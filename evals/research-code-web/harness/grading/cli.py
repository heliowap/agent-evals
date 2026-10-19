"""Artifact CLI; no controller inference or automatic semantic labeling."""

import argparse
from pathlib import Path

from .common import load, save, verify_signed, digest, signed
from .packets import export, pack_jobs, select_review_ids, blind_id
from .schema import validate_grade
from .sealing import seal_base, seal_final, unblind


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan-reviews")
    plan.add_argument("--schedule", required=True)
    plan.add_argument("--output", required=True)
    plan.add_argument("--review-per-group", type=int, default=9)
    exporter = commands.add_parser("export")
    for name in ("records", "tasks", "gold", "schedule", "output"):
        exporter.add_argument("--" + name, required=True)
    exporter.add_argument("--evidence-root", required=True)
    exporter.add_argument("--review-per-group", type=int, default=9)
    for name in ("import-base", "import-review", "import-adjudication"):
        command = commands.add_parser(name)
        command.add_argument("--bundle", required=True)
        command.add_argument("--input", required=True)
        command.add_argument("--store", required=True)
    jobs = commands.add_parser("jobs")
    jobs.add_argument("--bundle", required=True)
    jobs.add_argument("--output", required=True)
    jobs.add_argument("--review", action="store_true")
    jobs.add_argument("--base-seal")
    for name in ("seal-base", "seal-final"):
        command = commands.add_parser(name)
        command.add_argument("--bundle", required=True)
        command.add_argument("--store", required=True)
        command.add_argument("--output", required=True)
        if name == "seal-final":
            command.add_argument("--base-seal", required=True)
    reveal = commands.add_parser("unblind")
    reveal.add_argument("--sealed", required=True)
    reveal.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "plan-reviews":
        schedule = load(args.schedule)
        selected = select_review_ids(schedule, args.review_per_group)
        save(args.output, signed({"schedule_hash": digest(schedule), "seed": schedule["seed"],
                                 "per_group": args.review_per_group, "trial_ids": selected,
                                 "blind_ids": sorted(blind_id(schedule["seed"], i) for i in selected)}), immutable=True)
    elif args.command == "export":
        root = Path(args.evidence_root).resolve()
        def loader(name):
            path = (root / name).resolve()
            if not path.is_relative_to(root):
                raise ValueError("evidence loader path escapes archive root")
            return path.read_text(encoding="utf-8")
        bundle = export(load(args.records), load(args.tasks), load(args.gold), loader,
                        load(args.schedule), review_per_group=args.review_per_group)
        save(args.output, bundle, immutable=True)
    elif args.command == "unblind":
        save(args.output, unblind(load(args.sealed)), immutable=True)
    else:
        bundle = load(args.bundle)
        verify_signed(bundle)
        if args.command.startswith("import-"):
            category = args.command.removeprefix("import-")
            incoming = load(args.input)
            if not isinstance(incoming, list):
                raise ValueError("import expects a JSON array of grades/envelopes")
            identities = set()
            prepared = []
            for item in incoming:
                identity = item["blind_id"]
                if identity in identities or identity not in bundle["packets"]:
                    raise ValueError("duplicate/unknown imported identity")
                identities.add(identity)
                normalized = (validate_grade(item, bundle["packets"][identity]) if category == "base"
                              else dict(item, grade=validate_grade(item.get("grade"), bundle["packets"][identity])))
                target = Path(args.store) / category / (identity + ".json")
                if target.exists():
                    raise ValueError("immutable original/history already exists")
                prepared.append((target, normalized))
            for target, normalized in prepared:
                save(target, normalized, immutable=True)
        elif args.command == "jobs":
            base = load(args.base_seal)["grades"] if args.base_seal else None
            if args.review and base is None:
                raise ValueError("review job packing requires sealed original grades")
            save(args.output, pack_jobs(bundle, review=args.review, base_grades=base), immutable=True)
        else:
            store = Path(args.store)
            def events(category):
                return [load(path) for path in sorted((store / category).glob("*.json"))]
            if args.command == "seal-base":
                grades = events("base")
                from .common import indexed
                document = seal_base(bundle, indexed(grades, "blind_id"))
            else:
                document = seal_final(bundle, load(args.base_seal), events("review"), events("adjudication"))
            save(args.output, document, immutable=True)
    print("OK: " + args.command)


if __name__ == "__main__":
    main()
