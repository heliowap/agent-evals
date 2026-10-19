"""Print compact run metrics or the saved answers; no re-grading by keyword."""

import argparse
import json
from pathlib import Path

from benchmark import LUNA_MODELS, MODELS, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--luna", action="store_true", help="Read the OpenAI OAuth Luna cohort")
    args = parser.parse_args()
    models = LUNA_MODELS if args.luna else MODELS
    expected = len(models) * 2 * 2
    runs = [json.loads(path.read_text()) for path in (ROOT / ("results-luna" if args.luna else "results")).glob("*/*.json")]
    if args.check:
        assert len(runs) == expected, f"Expected {expected} runs; found {len(runs)}"
        assert len({(r["case"], r["model"], r["axis"]) for r in runs}) == expected
        assert all(r.get("status") == "succeeded" and r.get("answer") and not r.get("tool_events") for r in runs), [
            (r["case"], r["model"], r["axis"], r.get("status")) for r in runs
            if r.get("status") != "succeeded" or not r.get("answer") or r.get("tool_events")
        ]
        print(f"{expected}/{expected} responses succeeded, with text and no tool calls")
        return
    if args.answers:
        for case in ("click-3773", "click-3868"):
            for axis in ("standards", "spec"):
                print(f"\n{'=' * 16} {case} {axis} {'=' * 16}")
                for model in models:
                    run = next((r for r in runs if (r["case"], r["model"], r["axis"]) == (case, model, axis)), None)
                    print(f"\n### {model}\n{run.get('answer', '[missing]') if run else '[missing]'}")
        return
    print("model | successful / total | time s | cost USD | output tokens | reasoning tokens")
    for model in models:
        selected = [r for r in runs if r["model"] == model]
        print(" | ".join(map(str, (
            model,
            f"{sum(r.get('status') == 'succeeded' for r in selected)}/{len(selected)}",
            round(sum(r.get("elapsed_seconds", 0) for r in selected), 1),
            round(sum(r.get("cost_usd") or 0 for r in selected), 5),
            sum((r.get("tokens") or {}).get("output", 0) for r in selected),
            sum((r.get("tokens") or {}).get("reasoning", 0) for r in selected),
        ))))


if __name__ == "__main__":
    main()
