import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import bench
import cases
import runtime


ROOT = Path(__file__).resolve().parent
LAB = ROOT.parents[1]
CONTROLS = {"seed": 20261010, "repetitions": 5, "timeout_s": 300,
            "budget_s": 21600, "steps": 25, "output_limit": runtime.OUTPUT_LIMIT}


def package_inventory():
    paths = [*ROOT.glob("*.py"), *ROOT.glob("*.mjs"), ROOT / "observer.js", ROOT / "README.md",
             ROOT / "provenance.json", ROOT / "models.json"]
    return {p.name: runtime.source_hash(p) for p in sorted(paths)}


def original_inventory():
    baseline = LAB / "exploracao/sol-fast-vs-deepseek"
    return {str(p.relative_to(LAB)): runtime.source_hash(p)
            for p in sorted(baseline.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def provenance_check():
    origin = json.loads((ROOT / "provenance.json").read_text())
    if runtime.source_hash(Path(origin["baseline_freeze"])) != origin["baseline_freeze_sha256"]:
        raise ValueError("Historical freeze changed")
    base = Path(origin["baseline"])
    for name, expected in origin["baseline_sha256"].items():
        if runtime.source_hash(base / name) != expected:
            raise ValueError(f"Historical baseline changed: {name}")
    for name in origin["unchanged"]:
        if runtime.source_hash(ROOT / name) != origin["baseline_sha256"][name]:
            raise ValueError(f"Inherited contract changed: {name}")
    if runtime.source_hash(ROOT / "models.json") != origin["catalog_sha256"]:
        raise ValueError("Bundled catalog changed")
    return origin


def external_inventory(locations):
    binary = shutil.which(locations.binary)
    if binary is None:
        raise ValueError("OpenCode executable unavailable")
    return {"package": package_inventory(), "original": original_inventory(),
            "catalog": runtime.source_hash(locations.cache),
            "binary": {"path": str(Path(binary).resolve()), "sha256": runtime.source_hash(Path(binary))}}


@contextmanager
def phase_envelope(name, campaign, locations):
    provenance_check()
    before = external_inventory(locations)
    receipt = {"phase": name, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "before": before, "integrity_passed": False}
    folder = campaign / "envelopes"
    folder.mkdir(exist_ok=True)
    runtime.save(folder / f"{name}.json", receipt)
    try:
        yield
    finally:
        try:
            provenance_check()
            after = external_inventory(locations)
            receipt.update(after=after, integrity_passed=before == after)
        except (OSError, ValueError) as exc:
            receipt["error"] = str(exc)
        runtime.save(folder / f"{name}.json", receipt)
        if not receipt["integrity_passed"]:
            raise ValueError(f"Integrity changed during {name}; see envelope")


def phase_args(command, name, campaign, locations):
    return [command, "--out", str(campaign / name), "--cases", "route" if name == "smoke" else ",".join(cases.CASES),
            "--reps", "1" if name == "smoke" else "5", "--seed", str(CONTROLS["seed"]),
            "--timeout", str(CONTROLS["timeout_s"]), "--budget-seconds", str(CONTROLS["budget_s"]),
            "--binary", locations.binary, "--database", str(locations.database), "--cache", str(locations.cache)]


def smoke_passed(smoke_out):
    frozen = json.loads((smoke_out / "freeze.json").read_text())
    expected = bench.schedule(["route"], 1, CONTROLS["seed"])
    if frozen["schedule"] != expected or frozen["settings"]["output_limit"] != runtime.OUTPUT_LIMIT:
        return False
    if frozen["candidates"] != [runtime.public_candidate(c) for c in runtime.CANDIDATES]:
        return False
    phase = json.loads((smoke_out / "phase.json").read_text())
    if phase != {"planned": 5, "attempted": 5, "stop_reason": "schedule_exhausted", "exit_code": 0}:
        return False
    for row in expected:
        artifacts = smoke_out / row["id"]
        result = json.loads((artifacts / "result.json").read_text())
        if any(result.get(key) != value for key, value in row.items()):
            return False
        candidate = next(c for c in runtime.CANDIDATES if c.id == row["candidate"])
        if result.get("status") != "completed" or not result.get("passed") or not result.get("fixture_unchanged"):
            return False
        records = json.loads((artifacts / "requests.json").read_text())
        transport = runtime.verify_requests(candidate, records, result["session_id"])
        if transport["non_200_requests"] or transport["incomplete_requests"] or transport["observed_error_requests"]:
            return False
        with tempfile.TemporaryDirectory(prefix="haiku-gate-", dir="/private/tmp") as folder:
            work = Path(folder)
            cases.build(work)
            grade = cases.grade("route", work, (artifacts / "answer.json.txt").read_text())
            if not grade["passed"]:
                return False
    return True


def report_campaign(out):
    campaign = json.loads((out / "campaign.json").read_text())
    phases = {}
    for name, planned in [("smoke", 5), ("pilot", 150)]:
        source = out / name / "freeze.json"
        if source.exists():
            phases[name] = bench.report(out / name)
        else:
            phases[name] = {"planned": planned, "attempted": 0, "completed": 0,
                            "statuses": {"not_run": planned}, "stop_reason": "not_started", "exit_code": None}
    summary = {"controls": campaign["controls"], "planned": 155,
               "attempted": sum(p["attempted"] for p in phases.values()),
               "phases": phases, "exit_code": campaign.get("exit_code"), "stop_reason": campaign.get("stop_reason"),
               "model_calls": sum(json.loads(p.read_text()).get("transport", {}).get("request_count", 0)
                                  for name in phases for p in (out / name).glob("trial-*/result.json"))}
    runtime.save(out / "summary.json", summary)
    lines = ["# Haiku 5.5: leitura e exploração", "", f"Previstos 155 trials: smoke 5, comparação 150. Tentados {summary['attempted']}.", "",
             f"Parada: {summary['stop_reason']}. Exit: {summary['exit_code']}.", "",
             "| Fase | Previstas | Tentadas | Concluídas | Parada |", "|---|---:|---:|---:|---|"]
    for name, p in phases.items():
        lines.append(f"| {name} | {p['planned']} | {p['attempted']} | {p['completed']} | {p['stop_reason']} |")
    lines += ["", "As tabelas por esforço, caso e pares ficam em smoke/report.md e pilot/report.md.",
              "Não há vencedor automático. Seis casos sintéticos e repetições não comprovam confiabilidade geral.", ""]
    (out / "report.md").write_text("\n".join(lines))
    return summary


def run_campaign(out, locations):
    campaign = {"controls": CONTROLS, "candidates": [runtime.public_candidate(c) for c in runtime.CANDIDATES],
                "cases": list(cases.CASES), "exit_code": 1, "stop_reason": "smoke_not_completed"}
    runtime.save(out / "campaign.json", campaign)
    original = original_inventory()
    runtime.save(out / "preserved-before.json", original)
    try:
        for name in ["smoke", "pilot"]:
            with phase_envelope(name, out, locations):
                exit_code = bench.main(phase_args("run", name, out, locations))
            if name == "smoke":
                passed = exit_code == 0 and smoke_passed(out / "smoke")
                runtime.save(out / "smoke-gate.json", {"passed": passed, "required": 5, "fresh_smoke": True})
                if not passed:
                    campaign["stop_reason"] = "smoke_gate_failed"
                    break
            else:
                campaign.update(exit_code=exit_code, stop_reason="complete" if exit_code == 0 else "pilot_incomplete")
    except (OSError, ValueError, KeyError) as exc:
        campaign.update(stop_reason="blocked", error=str(exc))
    except KeyboardInterrupt:
        campaign.update(stop_reason="interrupted", exit_code=130)
        raise
    finally:
        after = original_inventory()
        runtime.save(out / "preserved-after.json", after)
        if original != after:
            campaign.update(exit_code=1, stop_reason="historical_integrity_failure")
        runtime.save(out / "campaign.json", campaign)
        report_campaign(out)
    return campaign["exit_code"]


def validate_offline(out):
    provenance_check()
    checked = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT), "-p", "test_*.py", "-v"],
                             capture_output=True, text=True)
    (out / "tests.txt").write_text(checked.stdout + checked.stderr)
    node_binary = shutil.which("node")
    observed = subprocess.run([node_binary, "--test", str(ROOT / "test_observer.mjs")], capture_output=True, text=True) if node_binary else None
    (out / "observer-tests.txt").write_text(observed.stdout + observed.stderr if observed else "Node unavailable; observer tests not run\n")
    exit_code = max(checked.returncode, observed.returncode if observed else 1)
    receipt = {"exit_code": exit_code, "python_exit_code": checked.returncode, "observer_exit_code": observed.returncode if observed else None, "model_calls": 0,
               "planned_smoke": len(bench.schedule(["route"], 1, CONTROLS["seed"])),
               "planned_pilot": len(bench.schedule(list(cases.CASES), 5, CONTROLS["seed"])),
               "package_sha256": package_inventory()}
    runtime.save(out / "validation.json", receipt)
    return exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Haiku 5.5 exploration campaign; fixed five efforts")
    parser.add_argument("command", choices=["plan", "validate-offline", "preflight", "run", "report"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--database", type=Path, default=Path.home() / ".local/share/opencode/opencode.db")
    parser.add_argument("--cache", type=Path, default=ROOT / "models.json")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if not out.is_relative_to(ROOT):
        parser.error("Output must be inside this experiment package")
    if args.command == "report":
        summary = report_campaign(out)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary.get("exit_code") if summary.get("exit_code") is not None else 1
    if out.exists():
        parser.error("Output must be new; prior evidence is never overwritten")
    out.mkdir(parents=True)
    if args.command == "validate-offline":
        return validate_offline(out)
    provenance_check()
    if args.command == "run":
        return run_campaign(out, args)
    if args.command == "preflight":
        with phase_envelope("preflight", out, args):
            return bench.main(phase_args("preflight", "smoke", out, args))
    runtime.save(out / "campaign.json", {"controls": CONTROLS, "exit_code": 0, "stop_reason": "plan_only"})
    for name in ["smoke", "pilot"]:
        bench.main(phase_args("plan", name, out, args))
    report_campaign(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
