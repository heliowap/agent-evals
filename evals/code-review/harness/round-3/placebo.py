import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "sentinel-v2"))
import sentinel  # noqa: E402


def _key(f):
    return (f["file"], f["function"], f["start"])


def changed_pool(snapshot: Path, base: str) -> list[dict]:
    seen = {}
    for f in sentinel.changed_functions(Path(snapshot), base):
        seen.setdefault(_key(f), {"file": f["file"], "function": f["function"],
                                  "start": f["start"], "end": f["end"]})
    return sorted(seen.values(), key=lambda f: (f["file"], f["start"], f["function"]))


def placebo_hotspots(snapshot: Path, base: str, k: int, seed: str) -> list[dict]:
    pool = changed_pool(snapshot, base)
    return random.Random(seed).sample(pool, min(k, len(pool)))


def placebo_overlap(hotspots, placebo) -> float:
    a = {_key(x) for x in hotspots}
    b = {_key(x) for x in placebo}
    return len(a & b) / len(a | b) if a | b else 0.0
