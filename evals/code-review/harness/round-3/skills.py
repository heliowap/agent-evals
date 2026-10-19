from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def render_hotspots(items) -> str:
    lines = [
        "## Review priority hints",
        "",
        "Automated triage suggests reading these changed functions first. "
        "Hints are not findings: report only what you verify in the code.",
        "",
    ]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. `{it['file']}::{it['function']}` (lines {it['start']}\u2013{it['end']})")
    return "\n".join(lines) + "\n"


def _read(variant: str) -> str:
    return (SKILLS_DIR / variant / "SKILL.md").read_bytes().decode()


def _append(base: str, items) -> str:
    return base.rstrip("\n") + "\n\n" + render_hotspots(items)


def skill_text(variant: str, hotspots=None, placebo=None) -> str:
    if variant in ("A", "B"):
        return _read(variant)
    if variant == "C":
        if hotspots is None:
            raise ValueError("variant C requires hotspots")
        return _append(_read("B"), hotspots)
    if variant == "D":
        if placebo is None:
            raise ValueError("variant D requires placebo")
        if hotspots is not None and len(placebo) != len(hotspots):
            raise ValueError("variant D placebo length must equal hotspots length")
        return _append(_read("B"), placebo)
    raise ValueError(f"unknown variant: {variant!r}")
