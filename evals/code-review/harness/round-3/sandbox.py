"""Isolated review environment: repo snapshot, frozen `gh`, and an OpenCode env with no user plugins/skills."""
import copy
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

from reviewer_config import REVIEWER_AGENT

HERE = Path(__file__).resolve().parent
USER_GLOBAL_JSONC = Path.home() / ".config/opencode/opencode.jsonc"


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_snapshot(repo_dir: Path, base: str, head: str, dest: Path, base_branch: str = "main") -> Path:
    """Clone only what is reachable from base/head: branch `pr` at head, origin/<base_branch> at base."""
    repo_dir, dest = Path(repo_dir).resolve(), Path(dest)
    dest.mkdir(parents=True, exist_ok=False)
    _git(dest, "init", "-q", "--template=")
    # -c propagates to the local upload-pack via GIT_CONFIG_PARAMETERS, so the source repo config is untouched.
    _git(dest, "-c", "uploadpack.allowAnySHA1InWant=true", "-c", "core.logAllRefUpdates=false", "fetch", "-q", "--no-tags", str(repo_dir),
         f"{head}:refs/heads/pr", f"{base}:refs/remotes/origin/{base_branch}")
    _git(dest, "-c", "core.logAllRefUpdates=false", "checkout", "-q", "pr")
    shutil.rmtree(dest / ".git" / "logs", ignore_errors=True)  # reflogs record the source repo path
    _git(dest, "gc", "--prune=now", "-q")
    (dest / ".git" / "FETCH_HEAD").unlink(missing_ok=True)  # records the source repo path
    return dest


GH_FIELDS = ("pr", "diff", "issues", "repo", "head")


def install_fake_gh(dest: Path, case: dict) -> Path:
    """Write `dest/.bin/gh`; the frozen data it serves lives outside dest, in `<dest>.gh/case.json`."""
    dest = Path(dest).resolve()
    bindir = dest / ".bin"
    bindir.mkdir(parents=True, exist_ok=True)
    data_dir = dest.parent / f"{dest.name}.gh"
    data_dir.mkdir(parents=True, exist_ok=True)
    case_path = data_dir / "case.json"
    case_path.write_text(json.dumps({k: case[k] for k in GH_FIELDS if k in case}))
    gh = bindir / "gh"
    gh.write_text(f'#!/bin/sh\nexec python3 "{HERE / "fake_gh.py"}" "{case_path}" "$@"\n')
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH | stat.S_IRGRP | stat.S_IROTH)
    return gh


def _load_jsonc(path: Path) -> dict:
    text = re.sub(r"^\s*//.*$", "", path.read_text(), flags=re.M)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def _fake_home(workdir: Path) -> Path:
    """Home outside the workdir holding only a global config with the user's provider definitions.

    OPENCODE_TEST_HOME redirects `~` (so ~/.claude/skills, ~/.agents/skills are not found) and
    XDG_CONFIG_HOME redirects the global config dir (so ~/.config/opencode plugins and skills are
    not loaded). The data dir (auth.json, session DB) stays the real one, so credentials and
    `opencode session export` keep working.
    """
    home = workdir.parent / f".{workdir.name}-ochome"
    cfg_dir = home / ".config" / "opencode"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    user = _load_jsonc(USER_GLOBAL_JSONC) if USER_GLOBAL_JSONC.exists() else {}
    cfg = {"$schema": "https://opencode.ai/config.json"}
    for key in ("provider", "disabled_providers"):
        if key in user:
            cfg[key] = user[key]
    (cfg_dir / "opencode.json").write_text(json.dumps(cfg, indent=2))
    return home


def _exclude_from_git(workdir: Path, patterns):
    info = workdir / ".git" / "info"
    if not info.is_dir():
        return
    exclude = info / "exclude"
    existing = exclude.read_text().splitlines() if exclude.exists() else []
    missing = [p for p in patterns if p not in existing]
    if missing:
        exclude.write_text("\n".join(existing + missing) + "\n")


def build_env(workdir: Path, skill_text: str) -> dict:
    workdir = Path(workdir).resolve()
    skill = workdir / ".opencode" / "skills" / "code-review" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(skill_text)
    _exclude_from_git(workdir, ["/.opencode/", "/.bin/"])

    agent = copy.deepcopy(REVIEWER_AGENT)
    agent.pop("model", None)  # the runner picks the model per cell with --model
    content = {"plugin": [], "default_agent": "reviewer", "permission": {"edit": "deny"},
               "agent": {"reviewer": agent}}

    home = _fake_home(workdir)
    # Drop every inherited OPENCODE_* (an OPENCODE_CONFIG_CONTENT rerouting providers through a local
    # gateway; an OPENCODE_API_KEY that overrides the opencode-go key in auth.json and has no funds).
    env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
    env.update({
        "OPENCODE_CONFIG_CONTENT": json.dumps(content),
        "OPENCODE_TEST_HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        # opencode resolves the session location from $PWD, not the process cwd
        "PWD": str(workdir),
        "PATH": f"{workdir / '.bin'}{os.pathsep}{os.environ.get('PATH', '')}",
    })
    return env
