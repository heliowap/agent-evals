"""Exploratory (post hoc, not pre-registered) analyses of a results directory.

Usage: python3 -B analysis/exploratory.py RESULTS_DIR --out DIR

Writes per-trial behavior measures and paired A/B comparisons to
DIR/exploratory.json and DIR/exploratory.md. Nothing here feeds the
pre-registered decision rule (harness/report.py).
"""
import argparse
import json
import math
import pathlib
import re
import statistics

PART = re.compile(r"bottle/\d\d_[a-z_]+\.py")
SOURCE = re.compile(r"\bbottle\.py\b|bottle/\d\d_[a-z_]+\.py|bottle/__init__\.py")
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\n")
SEARCH = re.compile(r"(^|[|;&(]\s*|\s)(grep|rg|find)\s")


def tokens_of(text):
    return len(text.encode("utf-8")) / 4


def result_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


def whole_file_views(command):
    """Source files printed in full by `cat` segments that are not piped into a filter."""
    files = []
    for seg in SEGMENT_SPLIT.split(command):
        seg = seg.strip()
        if seg.startswith("cat ") and "|" not in seg and "<<" not in seg:
            files += SOURCE.findall(seg)
    return files


def trial_behavior(tdir):
    uses, results = {}, {}
    usage, order = {}, []
    for line in open(tdir / "stream.jsonl", encoding="utf-8"):
        ev = json.loads(line)
        if ev.get("type") == "assistant":
            msg = ev["message"]
            if msg["id"] not in usage:
                order.append(msg["id"])
            usage[msg["id"]] = msg.get("usage", {})
            for b in msg.get("content", []):
                if b.get("type") == "tool_use":
                    uses[b["id"]] = b
        elif ev.get("type") == "user":
            content = ev.get("message", {}).get("content")
            for b in content if isinstance(content, list) else []:
                if b.get("type") == "tool_result":
                    results[b.get("tool_use_id")] = tokens_of(result_text(b.get("content")))
    ctx = [usage[m].get("input_tokens", 0) + usage[m].get("cache_read_input_tokens", 0)
           + usage[m].get("cache_creation_input_tokens", 0) for m in order]

    reads_full, reads_sliced, whole, searches, bash = 0, 0, [], 0, 0
    parts_seen, result_tokens = set(), 0.0
    for uid, b in uses.items():
        inp = b.get("input", {})
        result_tokens += results.get(uid, 0)
        if b["name"] == "Read":
            path = inp.get("file_path", "")
            if SOURCE.search(path):
                if "offset" in inp or "limit" in inp:
                    reads_sliced += 1
                else:
                    reads_full += 1
                    whole.append(SOURCE.search(path).group(0))
            parts_seen.update(PART.findall(path))
        elif b["name"] == "Bash":
            bash += 1
            cmd = inp.get("command", "")
            whole += whole_file_views(cmd)
            searches += bool(SEARCH.search(" " + cmd))
            parts_seen.update(PART.findall(cmd))
    return {
        "first_call_context": ctx[0] if ctx else None,
        "final_call_context": ctx[-1] if ctx else None,
        "peak_is_final": bool(ctx) and max(ctx) == ctx[-1],
        "tool_result_tokens": round(result_tokens),
        "bash_calls": bash,
        "search_commands": searches,
        "source_reads_sliced": reads_sliced,
        "source_reads_full": reads_full,
        "whole_file_views": len(whole),
        "distinct_parts_referenced": len(parts_seen),
    }


def diff_stats(path):
    files, added, removed, test_removed = set(), 0, 0, 0
    current = None
    for line in path.read_text().splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[1]
            files.add(current)
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
            test_removed += bool(line[1:].strip()) and current is not None and current.startswith("test/")
    tests = sorted(f for f in files if f.startswith("test/"))
    return {"files_changed": len(files), "lines_added": added, "lines_removed": removed,
            "test_files_changed": tests, "test_lines_removed": test_removed}


def sign_test_two_sided(k, n):
    """Exact binomial sign test, p = P(|X - n/2| >= |k - n/2|) under Binomial(n, 1/2)."""
    dev = abs(k - n / 2)
    return sum(math.comb(n, i) for i in range(n + 1) if abs(i - n / 2) >= dev) / 2 ** n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = []
    for tdir in sorted((pathlib.Path(args.results) / "trials").iterdir()):
        if not (tdir / "trial.json").exists():
            continue
        t = json.loads((tdir / "trial.json").read_text())
        m = json.loads((tdir / "metrics.json").read_text())
        rows.append({"id": t["id"], "task": t["task"], "arm": t["arm"], "rep": t["rep"], "pass": t["pass"],
                     "peak_context": m["peak_context"], "api_calls": m["api_calls"],
                     "file_exposure_tokens": m["file_exposure_tokens"],
                     "largest_exposure_tokens": m["largest_exposure_tokens"], "cost_usd": m["cost_usd"],
                     "wall_s": t["wall_s"], **trial_behavior(tdir), **diff_stats(tdir / "diff.patch")})

    pairs = []
    for a in (r for r in rows if r["arm"] == "a"):
        b = next(r for r in rows if r["arm"] == "b" and r["task"] == a["task"] and r["rep"] == a["rep"])
        pairs.append({"task": a["task"], "rep": a["rep"], "peak_a": a["peak_context"], "peak_b": b["peak_context"],
                      "log_ratio": math.log(b["peak_context"] / a["peak_context"])})
    k = sum(p["peak_b"] > p["peak_a"] for p in pairs)
    lr = [p["log_ratio"] for p in pairs]
    by_arm = lambda key: {arm: statistics.median(r[key] for r in rows if r["arm"] == arm) for arm in "ab"}
    keys = ["first_call_context", "tool_result_tokens", "bash_calls", "search_commands", "source_reads_sliced",
            "source_reads_full", "whole_file_views", "distinct_parts_referenced", "files_changed", "lines_added"]
    summary = {
        "pairs": pairs,
        "pairs_b_higher": k, "pairs_total": len(pairs),
        "sign_test_p_two_sided": sign_test_two_sided(k, len(pairs)),
        "mean_log_ratio": statistics.mean(lr), "sd_log_ratio": statistics.stdev(lr),
        "pooled_ratio_geomean": math.exp(statistics.mean(lr)),
        "peak_is_final_share": sum(r["peak_is_final"] for r in rows) / len(rows),
        "medians_by_arm": {key: by_arm(key) for key in keys},
        "trials_modifying_existing_tests": [r["id"] for r in rows if r["test_lines_removed"]],
        "rows": rows,
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "exploratory.json").write_text(json.dumps(summary, indent=2) + "\n")

    md = ["# Exploratory analyses (post hoc, not pre-registered)", "",
          f"Paired by task and repetition: B had the higher peak context in {k} of {len(pairs)} pairs "
          f"(exact two-sided sign test p = {summary['sign_test_p_two_sided']:.3f}). "
          f"Mean log ratio {summary['mean_log_ratio']:.3f} (SD {summary['sd_log_ratio']:.3f}), "
          f"pooled geometric-mean ratio {summary['pooled_ratio_geomean']:.3f}.", "",
          f"Peak context was reached on the final API call in {summary['peak_is_final_share']:.0%} of trials.", "",
          "| Measure (median per trial) | A | B |", "|---|---|---|"]
    md += [f"| {key} | {v['a']:,} | {v['b']:,} |" for key, v in summary["medians_by_arm"].items()]
    md += ["", "| Trial | Pass | Peak | API calls | Tool-result tok | Whole-file views | Sliced reads | Searches | "
           "Parts referenced | Files changed |", "|" + "---|" * 10]
    md += [f"| {r['id']} | {r['pass']} | {r['peak_context']:,} | {r['api_calls']} | {r['tool_result_tokens']:,} | "
           f"{r['whole_file_views']} | {r['source_reads_sliced']} | {r['search_commands']} | "
           f"{r['distinct_parts_referenced']} | {r['files_changed']} |" for r in rows]
    md += ["", f"Trials that removed non-blank lines from existing test files: "
           f"{summary['trials_modifying_existing_tests'] or 'none'}."]
    (out / "exploratory.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:20]))


if __name__ == "__main__":
    main()
