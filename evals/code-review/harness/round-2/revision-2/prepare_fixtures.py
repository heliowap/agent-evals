"""Collect immutable PR diffs and verbatim issue/rule excerpts from GitHub."""

import json
import subprocess
import urllib.request

from benchmark import ROOT, atomic_new, validate_fixtures


# All excerpts below are literal source ranges, not interpretations or gold labels.
SPECS = [
    {
        "id": "axios-10852", "repo": "axios/axios",
        "base": "05436fd562027a9d10531d58d13dd33d7f222c0c",
        "head": "7b51e6d70b383f308cb97dfb1abc59daae187e61",
        "issue_number": 6546, "pr_number": 10852,
        "issue_slice": ["### Describe the bug", "### To Reproduce"],
        "pr_slice": ["## Bug Fix Summary", "<!-- This is an auto-generated description by cubic. -->"],
        "context": [
            ["lib/core/Axios.js", 233, 250],
            ["lib/helpers/resolveConfig.js", 38, 61],
            ["lib/core/buildFullPath.js", 1, 22],
            ["lib/helpers/isAbsoluteURL.js", 10, 19],
            ["lib/helpers/combineURLs.js", 11, 15],
            ["index.d.ts", 609, 628],
        ],
        "standards": [["CONTRIBUTING.md", 7, 24]],
    },
    {
        "id": "rust-161834", "repo": "rust-lang/rust",
        "base": "ac7f9ec7da74d37fd28667c86bf117a39ba5b02a",
        "head": "152379d7dd1615ef8b951ee7a579c5b3706130b9",
        "issue_number": 161735, "pr_number": 161834,
        "issue_slice": ["# Code", None],
        "pr_slice": ["Fixes rust-lang/rust#161735", None],
        "context": [
            ["src/librustdoc/html/static/js/search.js", 310, 329],
            ["src/librustdoc/html/static/js/search.js", 635, 651],
            ["src/librustdoc/html/render/search_index.rs", 2172, 2186],
            ["tests/rustdoc-js/alias-sort.js", 1, 10],
        ],
        "standards": [
            ["src/doc/rustc-dev-guide/src/rustdoc-internals/search.md", 426, 455],
            ["src/tools/rustdoc-js/tester.js", 363, 404],
        ],
    },
    {
        "id": "requests-6991", "repo": "psf/requests",
        "base": "91a3eabd3dcc4d7f36dd8249e4777a90ef9b4305",
        "head": "1688e65119a0de5e9434702fb3805fc7cfeb8a41",
        "issue_number": 6990, "pr_number": 6991,
        "issue_slice": ["When there is a semicolon (`;`)", "## System Information"],
        # The PR title is the author's literal English claim; its body is in Chinese.
        "pr_title_only": True,
        "context": [
            ["src/requests/models.py", 84, 104],
            ["src/requests/auth.py", 120, 145],
            ["src/requests/auth.py", 220, 236],
        ],
        "standards": [
            ["docs/dev/contributing.rst", 65, 79],
            ["pyproject.toml", 6, 10],
        ],
        "external_standards": [{
            "url": "https://docs.pytest.org/en/8.4.x/explanation/goodpractices.html#conventions-for-python-test-discovery",
            "quote": "In those directories, search for `test_*.py` or `*_test.py` files",
        }],
    },
]


def fetch_text(url):
    if url.startswith("https://api.github.com/"):
        return subprocess.run(["gh", "api", url.removeprefix("https://api.github.com/")],
                              check=True, text=True, capture_output=True, timeout=60).stdout
    request = urllib.request.Request(url, headers={"User-Agent": "code-review-eval-v2", "Accept": "application/vnd.github.raw+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def excerpt(text, start, end):
    lines = text.splitlines()
    if start < 1 or end > len(lines) or start > end:
        raise ValueError(f"missing pinned source lines {start}-{end}; source has {len(lines)} lines")
    return "\n".join(f"{index}: {lines[index - 1]}" for index in range(start, end + 1))


def body_slice(body, markers):
    body = body.replace("\r\n", "\n")
    start_marker, end_marker = markers
    start = body.index(start_marker)
    end = body.index(end_marker, start + len(start_marker)) if end_marker else len(body)
    return body[start:end]


def assemble(spec, fetch=fetch_text):
    repo, base, head = spec["repo"], spec["base"], spec["head"]
    api = f"https://api.github.com/repos/{repo}"
    compare_url = f"{api}/compare/{base}...{head}"
    comparison = json.loads(fetch(compare_url))
    if (comparison["base_commit"]["sha"] != base or comparison["merge_base_commit"]["sha"] != base or
            not comparison["commits"] or comparison["commits"][-1]["sha"] != head):
        raise ValueError(f"{repo}: base/head comparison does not match the pinned commits")
    diff_url = f"https://github.com/{repo}/compare/{base}...{head}.diff"
    diff = fetch(diff_url)
    if not diff.startswith("diff --git "):
        raise ValueError(f"{repo}: unavailable full pinned diff")
    issue_url = f"{api}/issues/{spec['issue_number']}"
    pr_url = f"{api}/pulls/{spec['pr_number']}"
    issue = body_slice(json.loads(fetch(issue_url))["body"], spec["issue_slice"])
    pr_data = json.loads(fetch(pr_url))
    pr = pr_data["title"] if spec.get("pr_title_only") else body_slice(pr_data["body"], spec["pr_slice"])
    sources = [f"https://github.com/{repo}/issues/{spec['issue_number']}",
               f"https://github.com/{repo}/pull/{spec['pr_number']}",
               diff_url]

    def gather(ranges):
        blocks = []
        for path, start, end in ranges:
            raw = fetch(f"https://raw.githubusercontent.com/{repo}/{head}/{path}")
            blocks.append(f"{path} (lines {start}-{end}):\n{excerpt(raw, start, end)}")
            sources.append(f"https://github.com/{repo}/blob/{head}/{path}#L{start}-L{end}")
        return "\n\n".join(blocks)

    context = gather(spec["context"])
    standards = gather(spec["standards"])
    for source in spec.get("external_standards", []):
        standards += f'\n\n{source["url"]}:\n{source["quote"]}'
        sources.append(source["url"])

    return {
        "id": spec["id"], "repo": repo, "base": base, "head": head,
        "diff_command": f"git diff {base}..{head}",
        "commits": "\n".join(f'{item["sha"]} {item["commit"]["message"].splitlines()[0]}'
                             for item in comparison["commits"]),
        "issue": issue, "pr": pr, "diff": diff,
        "context": context, "standards": standards,
        "sources": sources,
    }


def main():
    if len(SPECS) != 3:
        raise SystemExit("Three qualified cases required; do not freeze a partial fixture")
    cases = [assemble(spec) for spec in SPECS]
    validate_fixtures(cases)
    atomic_new(ROOT / "fixtures.json", cases)
    print("Saved three pinned cases:", ", ".join(case["id"] for case in cases))


if __name__ == "__main__":
    main()
