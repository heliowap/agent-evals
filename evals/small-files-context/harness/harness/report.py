"""Aggregate trials and apply the pre-registered decision rule.

Usage: python3 -B harness/report.py RESULTS_DIR [RESULTS_DIR ...] --out DIR

Pass several directories to pool stages (stage 2 decisions use all five
repetitions). Trials whose session configuration fails validation are excluded
and listed; flagged trials stay in.
"""
import argparse
import json
import math
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ARMS, TASK_IDS  # noqa: E402

BOOTSTRAP = 10_000
SEED = 20261018


def load(dirs):
    trials, excluded = [], []
    for d in dirs:
        for tdir in sorted((pathlib.Path(d) / "trials").iterdir()):
            if not (tdir / "trial.json").exists() or tdir.name.startswith("smoke"):
                continue
            t = json.loads((tdir / "trial.json").read_text())
            t["metrics"] = json.loads((tdir / "metrics.json").read_text())
            t["grade"] = json.loads((tdir / "grade.json").read_text())
            (trials if t["metrics"]["validity"]["ok"] else excluded).append(t)
    return trials, excluded


def ratio(peaks):
    """Geometric mean over tasks of median(B) / median(A)."""
    logs = [math.log(statistics.median(peaks[t]["b"]) / statistics.median(peaks[t]["a"]))
            for t in peaks if peaks[t]["a"] and peaks[t]["b"]]
    return math.exp(sum(logs) / len(logs)) if logs else None


def bootstrap(peaks):
    rng = random.Random(SEED)
    values = []
    for _ in range(BOOTSTRAP):
        sample = {t: {arm: [rng.choice(v) for _ in v] for arm, v in arms.items()} for t, arms in peaks.items()}
        values.append(ratio(sample))
    values.sort()
    return values[int(0.025 * BOOTSTRAP)], values[int(0.975 * BOOTSTRAP) - 1]


def decide(pa, pb, r, lo, hi):
    # Rows are checked in this order; the first match decides.
    if pb < pa - 1 or (r > 1.0 and lo > 1.0):
        return "refuted", "stop"
    if pb >= pa - 1 and r <= 0.80 and hi < 1.0:
        return "supported", "run arm C"
    if pb >= pa + 2 and r <= 1.0:
        return "supported on quality", "run arm C"
    if pb >= pa - 1 and lo > 0.80:
        return "reduction below 20%", "stop"
    return "inconclusive", "run stage 2 (if stage 1), else report as inconclusive"


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def fmt(x, digits=0):
    if x is None:
        return "–"
    return f"{x:,.{digits}f}" if isinstance(x, float) or digits else f"{x:,}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    trials, excluded = load(args.dirs)
    by = lambda task, arm: [t for t in trials if t["task"] == task and t["arm"] == arm]

    peaks = {task: {arm: [t["metrics"]["peak_context"] for t in by(task, arm)] for arm in ARMS}
             for task in TASK_IDS}
    passes = {arm: sum(t["pass"] for t in trials if t["arm"] == arm) for arm in ARMS}
    n = {arm: sum(1 for t in trials if t["arm"] == arm) for arm in ARMS}
    r = ratio(peaks)
    lo, hi = bootstrap(peaks)
    verdict, action = decide(passes["a"], passes["b"], r, lo, hi)

    passing = {task: {arm: [t["metrics"]["peak_context"] for t in by(task, arm) if t["pass"]] for arm in ARMS}
               for task in TASK_IDS}
    passing = {k: v for k, v in passing.items() if v["a"] and v["b"]}
    r_passing = ratio(passing) if passing else None

    secondary = ["peak_context", "fresh_input_tokens", "cache_read_tokens", "cache_creation_tokens",
                 "output_tokens", "num_turns", "api_calls", "cost_usd", "file_exposure_tokens",
                 "largest_exposure_tokens", "exposures_over_5k", "read_calls"]
    rows = []
    for task in TASK_IDS:
        for arm in ARMS:
            ts = by(task, arm)
            row = {"task": task, "arm": arm, "n": len(ts), "pass": sum(t["pass"] for t in ts),
                   "timeouts": sum(t["timed_out"] for t in ts),
                   "turn_cap": sum(t["metrics"]["result_subtype"] == "error_max_turns" for t in ts),
                   "wall_s": med([t["wall_s"] for t in ts])}
            for k in secondary:
                row[k] = med([t["metrics"][k] for t in ts])
            row["chunked_reads"] = sum(bool(t["metrics"]["chunked_reads"]) for t in ts)
            rows.append(row)

    flags = [{"id": t["id"], **{k: v for k, v in t["metrics"]["flags"].items() if v}}
             for t in trials if any(t["metrics"]["flags"].values())]
    summary = {"trials": len(trials), "excluded": [t["id"] for t in excluded], "passes": passes, "n": n,
               "ratio": r, "ci95": [lo, hi], "ratio_passing_only": r_passing,
               "verdict": verdict, "action": action, "rows": rows, "flags": flags}

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    md = [f"# Small files A/B: report ({', '.join(pathlib.Path(d).name for d in args.dirs)})", "",
          f"**Verdict: {verdict}.** Next step: {action}.", "",
          "| | A | B |", "|---|---|---|",
          f"| Trials | {n['a']} | {n['b']} |",
          f"| Passed | {passes['a']} | {passes['b']} |", "",
          f"Peak-context ratio B/A (geometric mean over tasks of median ratios): **{r:.3f}**, "
          f"95% bootstrap interval [{lo:.3f}, {hi:.3f}].",
          f"Passing trials only (sensitivity): {fmt(r_passing, 3) if r_passing else 'n/a'}.", "",
          f"Excluded for invalid session configuration: {summary['excluded'] or 'none'}.", "",
          "## Per task and arm (medians)", "",
          "| Task | Arm | Pass | Peak ctx | Fresh in | Cache read | Cache create | Output | API calls | Turns | "
          "Cost $ | File exposure | Largest exposure | Exposures >5k | Reads | Chunked | Timeouts | Turn cap |",
          "|" + "---|" * 18]
    for row in rows:
        md.append(f"| {row['task']} | {row['arm'].upper()} | {row['pass']}/{row['n']} | {fmt(row['peak_context'])} | "
                  f"{fmt(row['fresh_input_tokens'])} | {fmt(row['cache_read_tokens'])} | "
                  f"{fmt(row['cache_creation_tokens'])} | {fmt(row['output_tokens'])} | {fmt(row['api_calls'])} | {fmt(row['num_turns'])} | "
                  f"{fmt(row['cost_usd'], 3)} | {fmt(row['file_exposure_tokens'])} | "
                  f"{fmt(row['largest_exposure_tokens'])} | {fmt(row['exposures_over_5k'])} | "
                  f"{fmt(row['read_calls'])} | {row['chunked_reads']} | {row['timeouts']} | {row['turn_cap']} |")
    md += ["", "## Flags", ""]
    md += [f"- `{f['id']}`: {json.dumps({k: v for k, v in f.items() if k != 'id'})}" for f in flags] or ["None."]
    md += ["", "Limitations: directional pilot; N per task is small; one interim look if stage 2 runs; "
           "bottle is in training data; token exposure for Bash file prints is matched by command name."]
    (out / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
