"""Frozen stand-in for `gh`: answers PR/issue reads from case.json, refuses everything else.

Usage (via the wrapper written by sandbox.install_fake_gh): fake_gh.py <case.json> <gh args...>
"""
import json
import sys


def refuse(msg="unsupported in benchmark"):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def parse(args, allowed_flags):
    """Split args into positionals and flags; any flag outside allowed_flags is refused."""
    pos, flags = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("-"):
            name, eq, val = a.partition("=")
            if name not in allowed_flags:
                refuse()
            if allowed_flags[name]:
                if not eq:
                    i += 1
                    if i >= len(args):
                        refuse()
                    val = args[i]
                flags[name] = val
            else:
                flags[name] = True
        else:
            pos.append(a)
        i += 1
    if "-R" in flags:
        flags["--repo"] = flags.pop("-R")
    return pos, flags


def diff_stats(diff):
    files, cur = [], None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            cur = {"path": line.split(" b/", 1)[-1], "additions": 0, "deletions": 0}
            files.append(cur)
        elif cur is None or line.startswith(("+++", "---")):
            continue
        elif line.startswith("+"):
            cur["additions"] += 1
        elif line.startswith("-"):
            cur["deletions"] += 1
    return files


def pr_data(case):
    pr = dict(case["pr"])
    files = diff_stats(case.get("diff", ""))
    pr.setdefault("files", files)
    pr.setdefault("additions", sum(f["additions"] for f in files))
    pr.setdefault("deletions", sum(f["deletions"] for f in files))
    if "headRefOid" not in pr and case.get("head"):
        pr["headRefOid"] = case["head"]
    if "url" not in pr and case.get("repo"):
        pr["url"] = f"https://github.com/{case['repo']}/pull/{pr['number']}"
    return pr


def select(obj, fields):
    return {f: obj.get(f) for f in (x.strip() for x in fields.split(",")) if f}


def check_repo(case, flags):
    if "--repo" in flags and flags["--repo"] != case.get("repo"):
        refuse()


def check_pr_ref(case, pos):
    if len(pos) > 1:
        refuse()
    if pos:
        ref = pos[0].lstrip("#")
        url = f"https://github.com/{case.get('repo')}/pull/{case['pr']['number']}"
        if ref != str(case["pr"]["number"]) and pos[0] != url:
            refuse()


def main(argv):
    case = json.load(open(argv[0]))
    args = argv[1:]
    issues = case.get("issues", {})
    if args[:2] == ["pr", "view"]:
        pos, flags = parse(args[2:], {"--json": True, "--repo": True, "-R": True})
        check_repo(case, flags)
        check_pr_ref(case, pos)
        pr = pr_data(case)
        if "--json" in flags:
            print(json.dumps(select(pr, flags["--json"])))
        else:
            print(f"{pr.get('title', '')} #{pr['number']}\n"
                  f"base: {pr.get('baseRefName', '')}  head: {pr.get('headRefName', '')}\n"
                  f"+{pr['additions']} -{pr['deletions']}\n\n{pr.get('body', '')}")
        return 0
    if args[:2] == ["pr", "diff"]:
        pos, flags = parse(args[2:], {"--repo": True, "-R": True})
        check_repo(case, flags)
        check_pr_ref(case, pos)
        sys.stdout.write(case["diff"])
        return 0
    if args[:2] == ["issue", "view"]:
        pos, flags = parse(args[2:], {"--json": True, "--repo": True, "-R": True})
        check_repo(case, flags)
        if len(pos) != 1:
            refuse()
        num = pos[0].lstrip("#")
        issue = issues.get(num)
        if issue is None:
            refuse()
        if "--json" in flags:
            print(json.dumps(select({"number": int(num), **issue}, flags["--json"])))
        else:
            print(f"{issue.get('title', '')} #{num}\n\n{issue.get('body', '')}")
        return 0
    refuse()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
