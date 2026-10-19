"""Produce model-masked answer packets; keep the identity map separate."""

import argparse
import json
import random

from benchmark import ROOT, SEED, atomic_new, frozen_manifest, pending_cells


def make_packets(results, seed=SEED):
    shuffled = []
    for case in sorted({result["case"] for result in results}):
        group = [result for result in results if result["case"] == case]
        random.Random(f"{seed}:{case}").shuffle(group)
        shuffled.extend(group)
    packets = []
    mapping = {}
    for index, result in enumerate(shuffled, 1):
        blind_id = f"b{index:04}"
        packets.append({"blind_id": blind_id, "case": result["case"],
                        "axis": result["axis"], "answer": result["answer"]})
        mapping[blind_id] = result["cell_id"]
    return packets, mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    _, manifest = frozen_manifest(ROOT)
    pending_cells(manifest, ROOT)
    results = [json.loads(path.read_text()) for path in (ROOT / "results").glob("*.json")]
    if len(results) != len(manifest["cells"]) and not args.allow_partial:
        raise SystemExit(f"Only {len(results)}/300 valid; use --allow-partial to label a partial adjudication")
    packets, mapping = make_packets(results)
    atomic_new(ROOT / "blind-answers.json", {"partial": len(results) != 300, "answers": packets})
    atomic_new(ROOT / "blind-map.json", mapping)
    print(f"{len(packets)} masked answers; only pass blind-answers.json to an adjudicator")


if __name__ == "__main__":
    main()
