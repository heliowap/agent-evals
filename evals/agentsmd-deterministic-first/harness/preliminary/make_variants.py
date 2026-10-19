"""Build per-variant XDG config homes that differ only in opencode/AGENTS.md.

A = current AGENTS.md; B = AGENTS.md without the "## Deterministic first" section.
Every other entry of ~/.config and ~/.config/opencode is symlinked, so git, gh
and plugins keep reading the real config.
"""

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

REAL_XDG = Path.home() / ".config"
REAL_OC = REAL_XDG / "opencode"
SECTION = "## Deterministic first"


def strip_section(text: str) -> str:
    parts = re.split(r"(?m)^(?=## )", text)
    kept = [p for p in parts if not p.startswith(SECTION + "\n")]
    if len(kept) != len(parts) - 1:
        sys.exit(f"expected exactly one '{SECTION}' section")
    return "".join(kept)


def build(root: Path, name: str, agents_md: str) -> Path:
    xdg = root / f"xdg-{name}"
    if xdg.exists():
        shutil.rmtree(xdg)
    oc = xdg / "opencode"
    oc.mkdir(parents=True)
    for entry in REAL_XDG.iterdir():
        if entry.name != "opencode":
            (xdg / entry.name).symlink_to(entry)
    for entry in REAL_OC.iterdir():
        if entry.name != "AGENTS.md":
            (oc / entry.name).symlink_to(entry)
    (oc / "AGENTS.md").write_text(agents_md)
    return xdg


def main() -> None:
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    current = (REAL_OC / "AGENTS.md").read_text()
    variants = {"A": current, "B": strip_section(current)}
    manifest = {}
    for name, text in variants.items():
        xdg = build(root, name, text)
        manifest[name] = {
            "xdg_config_home": str(xdg),
            "agents_md_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "agents_md_bytes": len(text.encode()),
            "has_deterministic_first": SECTION in text,
        }
    (root / "variants.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
