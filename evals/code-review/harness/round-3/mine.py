"""Case mining helpers: regression-link detection, case schema validation, and case/bundle I/O."""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

KINDS = ("tracked", "clean", "mutation", "injection")
REPRO_KINDS = ("test", "script", "code")
# Served to the reviewer by the fake gh (sandbox.GH_FIELDS) vs. used only for grading.
GRADING_FIELDS = ("target", "fix_ref", "maintainer_comments")
REQUIRED_KEYS = ("id", "kind", "repo", "language", "pr", "base", "head", "diff", "issues",
                 "target", "fix_ref", "maintainer_comments")
PR_KEYS = ("number", "title", "body", "baseRefName", "merged_at", "url")
TARGET_KEYS = ("file", "lines", "mechanism", "consequence", "equivalents", "repro")
REPRO_KEYS = ("kind", "path", "command", "expected")
COMMENT_KEYS = ("author", "body", "url")
MIN_DIFF_LINES, MAX_DIFF_LINES = 20, 800
EXCLUDED_OWNERS = ("<user>",)

_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")

_REF = r"(?:(?:[\w.-]+/[\w.-]+)?#(\d+)|https?://github\.com/[\w.-]+/[\w.-]+/(?:pull|issues)/(\d+))"
_PR = r"\s+(?:(?:pr|pull\s+request)\s+)?"
# "reverts #N" is always a link; the weak verbs only count when the sentence talks about a regression/bug.
_STRONG = re.compile(r"\breverts" + _PR + _REF, re.IGNORECASE)
_WEAK = re.compile(r"\b(?:(?:introduced|caused|broke|broken)\s+(?:in|by)|from)" + _PR + _REF, re.IGNORECASE)
_KEYWORD = re.compile(r"\b(?:regression|regressed|broke|broken|bug|bugs|revert\w*)\b", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n")
_REVERTED = re.compile(r"\bThis reverts commit ([0-9a-fA-F]{7,40})\b")


def find_fix_links(text: str) -> list[int]:
    """PR numbers a fix/revert message blames, in order of appearance, deduplicated."""
    out = []
    for sentence in _SENTENCE_END.split(text or ""):
        matches = list(_STRONG.finditer(sentence))
        if _KEYWORD.search(sentence):
            matches += _WEAK.finditer(sentence)
        for m in sorted(matches, key=lambda m: m.start()):
            n = int(m.group(1) or m.group(2))
            if n not in out:
                out.append(n)
    return out


def find_reverted_shas(text: str) -> list[str]:
    out = []
    for m in _REVERTED.finditer(text or ""):
        sha = m.group(1).lower()
        if sha not in out:
            out.append(sha)
    return out


def count_diff_lines(diff: str) -> int:
    n = 0
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            n += 1
    return n


def case_sha256(case: dict) -> str:
    body = {k: v for k, v in case.items() if k != "sha256"}
    canon = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _need_str(value, name, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ValueError(f"{name} must be a {'' if allow_empty else 'non-empty '}string")


def _validate_target(t):
    if not isinstance(t, dict):
        raise ValueError("target must be an object for tracked/mutation cases")
    for k in TARGET_KEYS:
        if k not in t:
            raise ValueError(f"target missing key: {k}")
    _need_str(t["file"], "target.file")
    lines = t["lines"]
    if (not isinstance(lines, list) or len(lines) != 2 or not all(type(x) is int for x in lines)
            or not 1 <= lines[0] <= lines[1]):
        raise ValueError("target.lines must be [a, b] with 1 <= a <= b")
    _need_str(t["mechanism"], "target.mechanism")
    _need_str(t["consequence"], "target.consequence")
    if not isinstance(t["equivalents"], list) or not all(isinstance(e, str) for e in t["equivalents"]):
        raise ValueError("target.equivalents must be a list of strings")
    r = t["repro"]
    if not isinstance(r, dict):
        raise ValueError("target.repro must be an object")
    for k in REPRO_KEYS:
        if k not in r:
            raise ValueError(f"target.repro missing key: {k}")
    if r["kind"] not in REPRO_KINDS:
        raise ValueError(f"target.repro.kind must be one of {REPRO_KINDS}")
    for k in ("path", "command", "expected"):
        _need_str(r[k], f"target.repro.{k}")


def validate_case(case: dict) -> None:
    """Raise ValueError describing the first schema violation."""
    if not isinstance(case, dict):
        raise ValueError("case must be an object")
    for k in REQUIRED_KEYS:
        if k not in case:
            raise ValueError(f"case missing key: {k}")
    if not isinstance(case["id"], str) or not _ID.fullmatch(case["id"]):
        raise ValueError(f"id must match {_ID.pattern}")
    kind = case["kind"]
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    repo = case["repo"]
    if not isinstance(repo, str) or not _REPO.fullmatch(repo):
        raise ValueError("repo must be 'owner/name'")
    if repo.split("/")[0].lower() in EXCLUDED_OWNERS:
        raise ValueError(f"repo owner excluded (<user>): {repo}")
    _need_str(case["language"], "language")

    pr = case["pr"]
    if not isinstance(pr, dict):
        raise ValueError("pr must be an object")
    for k in PR_KEYS:
        if k not in pr:
            raise ValueError(f"pr missing key: {k}")
    if type(pr["number"]) is not int or pr["number"] <= 0:
        raise ValueError("pr.number must be a positive int")
    _need_str(pr["title"], "pr.title")
    _need_str(pr["body"], "pr.body", allow_empty=True)
    _need_str(pr["baseRefName"], "pr.baseRefName")
    if pr["merged_at"] is not None:
        _need_str(pr["merged_at"], "pr.merged_at")
    _need_str(pr["url"], "pr.url")

    for field in ("base", "head"):
        if not isinstance(case[field], str) or not _SHA40.fullmatch(case[field]):
            raise ValueError(f"{field} must be a 40-char lowercase hex sha")
    if case["base"] == case["head"]:
        raise ValueError("base and head must differ")

    if not isinstance(case["diff"], str):
        raise ValueError("diff must be a string")
    n = count_diff_lines(case["diff"])
    if not MIN_DIFF_LINES <= n <= MAX_DIFF_LINES:
        raise ValueError(f"diff has {n} changed lines, need {MIN_DIFF_LINES}..{MAX_DIFF_LINES}")

    issues = case["issues"]
    if not isinstance(issues, dict):
        raise ValueError("issues must be an object")
    for num, iss in issues.items():
        if not str(num).isdigit() or not isinstance(iss, dict) or "title" not in iss or "body" not in iss:
            raise ValueError(f"issues[{num!r}] must be {{title, body}} keyed by number")

    if kind in ("tracked", "mutation"):
        if case["target"] is None:
            raise ValueError(f"{kind} case requires a target with repro")
        _validate_target(case["target"])
    elif case["target"] is not None:
        raise ValueError(f"{kind} case requires target to be null")

    if case["fix_ref"] is not None:
        _need_str(case["fix_ref"], "fix_ref")
    if kind == "tracked" and case["fix_ref"] is None:
        raise ValueError("tracked case requires fix_ref")

    mc = case["maintainer_comments"]
    if not isinstance(mc, list):
        raise ValueError("maintainer_comments must be a list")
    for c in mc:
        if not isinstance(c, dict) or any(k not in c for k in COMMENT_KEYS):
            raise ValueError(f"maintainer_comments entries need {COMMENT_KEYS}")

    if "sha256" in case and (not isinstance(case["sha256"], str) or not _SHA256.fullmatch(case["sha256"])):
        raise ValueError("sha256 must be 64 lowercase hex chars")


def load_case(path) -> dict:
    """Load case.json (or <dir>/case.json) and verify its sha256."""
    path = Path(path)
    if path.is_dir():
        path = path / "case.json"
    case = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(case, dict) or not case.get("sha256"):
        raise ValueError(f"{path}: missing sha256")
    actual = case_sha256(case)
    if actual != case["sha256"]:
        raise ValueError(f"{path}: sha256 mismatch (stored {case['sha256']}, actual {actual})")
    validate_case(case)
    return case


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _rev(cwd, ref):
    r = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{ref}^{{commit}}"], cwd=cwd,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def write_case(case: dict, snapshot: Path, out_dir: Path) -> Path:
    """Validate, fill sha256, write out_dir/<id>/case.json and repo.bundle (pr + origin/<base>)."""
    case = {k: v for k, v in case.items() if k != "sha256"}
    validate_case(case)
    snapshot = Path(snapshot).resolve()
    base_ref = f"refs/remotes/origin/{case['pr']['baseRefName']}"
    if _rev(snapshot, "refs/heads/pr") != case["head"]:
        raise ValueError(f"snapshot branch pr is not at head {case['head']}")
    if _rev(snapshot, base_ref) != case["base"]:
        raise ValueError(f"snapshot {base_ref} is not at base {case['base']}")
    case["sha256"] = case_sha256(case)

    out_dir = Path(out_dir).resolve()
    final = out_dir / case["id"]
    if final.exists():
        raise FileExistsError(final)
    out_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{case['id']}-", dir=out_dir))
    try:
        _git(snapshot, "bundle", "create", "-q", str(staging / "repo.bundle"), "pr", base_ref)
        (staging / "case.json").write_text(
            json.dumps(case, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        staging.rename(final)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return final


def restore_snapshot(case_dir: Path, dest: Path) -> Path:
    """Recreate the snapshot from repo.bundle: branch `pr` at head (checked out), origin/<base> at base."""
    case_dir = Path(case_dir).resolve()
    case = load_case(case_dir / "case.json")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=False)
    base_ref = f"refs/remotes/origin/{case['pr']['baseRefName']}"
    _git(dest, "init", "-q", "--template=")
    _git(dest, "-c", "core.logAllRefUpdates=false", "fetch", "-q", "--no-tags", str(case_dir / "repo.bundle"),
         "refs/heads/pr:refs/heads/pr", f"{base_ref}:{base_ref}")
    if _rev(dest, "refs/heads/pr") != case["head"]:
        raise ValueError(f"bundle pr ref does not match head {case['head']}")
    if _rev(dest, base_ref) != case["base"]:
        raise ValueError(f"bundle {base_ref} does not match base {case['base']}")
    _git(dest, "-c", "core.logAllRefUpdates=false", "checkout", "-q", "pr")
    # FETCH_HEAD and reflogs record the bundle path, which leads to case.json's grading fields.
    (dest / ".git" / "FETCH_HEAD").unlink(missing_ok=True)
    shutil.rmtree(dest / ".git" / "logs", ignore_errors=True)
    return dest
