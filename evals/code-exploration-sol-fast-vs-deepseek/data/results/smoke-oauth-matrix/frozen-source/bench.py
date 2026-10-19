import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import random
import shutil
import sqlite3
import statistics
import tempfile
import time

import cases
import runtime


ROOT = Path(__file__).resolve().parent


def schedule(selected, reps, seed, candidates=None):
    candidates = tuple(runtime.CANDIDATES if candidates is None else candidates)
    if not candidates or len({c.id for c in candidates}) != len(candidates):
        raise ValueError("Candidate list must be nonempty and unique")
    rng = random.Random(seed)
    blocks = [(case, rep) for rep in range(1, reps + 1) for case in selected]
    rng.shuffle(blocks)
    offsets = [i % len(candidates) for i in range(len(blocks))]
    rng.shuffle(offsets)
    base = list(candidates)
    rng.shuffle(base)
    rows = []
    for pair, ((case, rep), offset) in enumerate(zip(blocks, offsets), 1):
        ordered = base[offset:] + base[:offset]
        for position, candidate in enumerate(ordered):
            rows.append({"id": f"trial-{len(rows) + 1:04d}", "pair": pair, "case": case,
                         "rep": rep, "position": position, "candidate": candidate.id})
    return rows


def manifest(selected, reps, seed, timeout, budget, cache, candidates=None):
    candidates = tuple(runtime.CANDIDATES if candidates is None else candidates)
    return {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runtime_version": runtime.VERSION, "role": "standalone explorer",
            "candidates": [runtime.public_candidate(c) for c in candidates],
            "seed": seed, "repetitions": reps, "timeout_s": timeout, "budget_s": budget,
            "schedule": schedule(selected, reps, seed, candidates),
            "cases": {case: {"definition": cases.CASES[case], "prompt": cases.prompt(case)} for case in selected},
            "fixture_sha256": {name: hashlib.sha256(text.encode()).hexdigest()
                               for name, text in cases.FILES.items()},
            "source_sha256": {p.name: runtime.source_hash(p) for p in sorted([*ROOT.glob("*.py"), *ROOT.glob("observer.js")])},
            "protocol_sha256": runtime.source_hash(ROOT / "README.md"),
            "catalog_sha256": runtime.source_hash(cache),
            "settings": {"steps": 25, "shell": False, "web": False, "skills": False,
                         "native_delegation": False, "automatic_cross_model_fallback": False,
                         "automatic_harness_retries": 0, "cold_session_per_trial": True,
                         "observation_mode": "passive_native_provider",
                         "candidate_order": "randomized blocks, cyclic rotations balanced across all positions",
                         "measured_region": "opencode run process including boot, tools, and internal retries",
                         "time_excluded": "fixture creation, auth import, discovery audit, export, grading",
                         "fast_requirement": "low + priority forwarded; served tier separately confirmed",
                         "conclusion": "descriptive pilot, not general qualification"}}


def check_freeze(frozen, cache):
    for name, expected in frozen["source_sha256"].items():
        if runtime.source_hash(ROOT / name) != expected:
            raise ValueError(f"Source changed after freeze: {name}")
    if runtime.source_hash(ROOT / "README.md") != frozen["protocol_sha256"]:
        raise ValueError("Protocol changed after freeze")
    if runtime.source_hash(cache) != frozen["catalog_sha256"]:
        raise ValueError("Model catalog changed after freeze")


def redact(text, secret):
    secrets = [secret] if isinstance(secret, str) else secret or []
    for value in sorted((s for s in secrets if s), key=len, reverse=True):
        text = text.replace(value, "<REDACTED>")
    return text


def run_trial(row, out, private_root, args):
    candidate = next(c for c in runtime.CANDIDATES if c.id == row["candidate"])
    artifacts = out / row["id"]
    artifacts.mkdir()
    root = (private_root / row["id"]).resolve()
    work = root / "orders-service"
    work.mkdir(parents=True)
    initial = cases.build(work)
    runtime.save(artifacts / "initial-files.json", initial)
    result = {**row, "status": "running", "passed": False, "wall_s": None,
              "requested": runtime.public_candidate(candidate)}
    runtime.save(artifacts / "result.json", result)
    requests = []
    secret = None
    started = time.monotonic()
    try:
        secret = runtime.credential_secrets(runtime.credential(candidate, args.database)["value"])
        env, config = runtime.prepare(root, work, candidate, args.binary, args.database, args.cache)
        runtime.save(artifacts / "config.json", config)
        discovery = runtime.audit(root, work, args.binary, env, config, candidate=candidate)
        runtime.save(artifacts / "discovery.json", discovery)
        result["preparation_s"] = time.monotonic() - started
        prompt = cases.prompt(row["case"])
        (artifacts / "prompt.txt").write_text(prompt)
        invoked = runtime.command([args.binary, "run", "--standalone", "--auto", "--format", "json",
                                   "--agent", runtime.AGENT, "--model", candidate.selection,
                                   "--title", "Navigation", prompt], work, env, args.timeout)
        result["wall_s"] = invoked["wall_s"]
        requests = runtime.read_requests(root / "observations.jsonl")
        (artifacts / "events.jsonl").write_text(redact(invoked["stdout"], secret))
        (artifacts / "stderr.txt").write_text(redact(invoked["stderr"], secret))
        if invoked["timeout"]:
            result["status"] = "timeout"
            raise TimeoutError("Task exceeded its deadline")
        if invoked["exit_code"]:
            raise runtime.TaskFailure("OpenCode task failed; see sanitized stderr and events")
        events = [json.loads(line) for line in invoked["stdout"].splitlines() if line.startswith("{")]
        sessions = {event["sessionID"] for event in events if event.get("sessionID")}
        if len(sessions) != 1:
            raise ValueError("Expected exactly one task session")
        session = sessions.pop()
        exported = runtime.command([args.binary, "session", "export", "--standalone", session], work, env, 45)
        (artifacts / "export.stderr").write_text(redact(exported["stderr"], secret))
        if exported["timeout"] or exported["exit_code"]:
            raise ValueError("Could not export task session")
        clean_export = redact(exported["stdout"], secret)
        (artifacts / "session.json").write_text(clean_export)
        parsed = runtime.parse_session(json.loads(clean_export), candidate, work)
        transport = runtime.verify_requests(candidate, requests, parsed["session_id"])
        (artifacts / "answer.json.txt").write_text(parsed["final"])
        runtime.save(artifacts / "tool-events.json", parsed["tools"])
        graded = cases.grade(row["case"], work, parsed["final"])
        result.update(status="completed", passed=graded["passed"], grade=graded, transport=transport,
                      session_id=parsed["session_id"], observed_identity=parsed["observed_identity"],
                      usage=parsed["usage"], reported_cost_usd=parsed["reported_cost_usd"],
                      tool_calls=len(parsed["tools"]), error_events=parsed["error_events"])
    except KeyboardInterrupt:
        result.update(status="interrupted", error="Stopped by operator")
        raise
    except TimeoutError as exc:
        result.update(status="timeout", error=str(exc))
    except runtime.TaskFailure as exc:
        result.update(status="task_error", error=redact(str(exc), secret))
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        result.update(status="infra_error", error=redact(str(exc), secret))
    finally:
        try:
            requests = runtime.read_requests(root / "observations.jsonl")
        except (OSError, ValueError) as exc:
            result.update(status="infra_error", passed=False, error=redact(str(exc), secret))
        runtime.save(artifacts / "requests.json", requests)
        if requests and "transport" not in result:
            try:
                result["transport"] = runtime.verify_requests(candidate, requests)
            except ValueError as exc:
                result.update(status="infra_error", passed=False, error=str(exc))
        if (root / "discovery.json").exists():
            shutil.copyfile(root / "discovery.json", artifacts / "discovery-probe.json")
        if (root / "effective-config.json").exists():
            shutil.copyfile(root / "effective-config.json", artifacts / "effective-config.json")
        result["fixture_unchanged"] = cases.snapshot(work) == initial
        if not result["fixture_unchanged"]:
            result.update(status="scope_violation", passed=False, error="Project source was modified")
        result["total_trial_s"] = time.monotonic() - started
        shutil.rmtree(root / "data", ignore_errors=True)
        (root / "auth.json").unlink(missing_ok=True)
        runtime.save(artifacts / "result.json", result)
    return result


def preflight(out, args):
    report = {"status": "running", "model_inference_calls": 0, "candidates": []}
    try:
        runtime.validate_oauth_window(args.selected_candidates, args.database, args.budget_seconds + args.timeout)
        with tempfile.TemporaryDirectory(prefix="project-", dir="/private/tmp") as folder:
            for candidate in args.selected_candidates:
                root = (Path(folder) / candidate.id).resolve()
                work = root / "orders-service"
                work.mkdir(parents=True)
                env, config = runtime.prepare(root, work, candidate, args.binary, args.database, args.cache)
                discovery = runtime.audit(root, work, args.binary, env, config, candidate=candidate)
                if runtime.read_requests(root / "observations.jsonl"):
                    raise ValueError("Preflight unexpectedly made model requests")
                report["candidates"].append({"candidate": candidate.id, "configuration": config,
                                             "discovery": discovery, "status": "passed"})
                shutil.rmtree(root / "data", ignore_errors=True)
        report["status"] = "passed"
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        report.update(status="blocked", error=str(exc))
    runtime.save(out / "preflight.json", report)
    return report


def records(out, frozen):
    return [json.loads(path.read_text()) if (path := out / row["id"] / "result.json").exists()
            else {**row, "status": "not_run", "passed": False} for row in frozen["schedule"]]


def candidate_inventory(frozen):
    inventory = frozen.get("candidates")
    if inventory is None:
        inventory = [{"id": name, "fast": name == "sol-fast-low"}
                     for name in dict.fromkeys(row["candidate"] for row in frozen["schedule"])]
    ids = [candidate["id"] for candidate in inventory]
    if len(ids) != len(set(ids)) or not set(row["candidate"] for row in frozen["schedule"]).issubset(ids):
        raise ValueError("Frozen candidate inventory does not match the schedule")
    return inventory


def pair_detail(left, right, rows):
    blocks = {}
    for row in rows:
        blocks.setdefault((row["case"], row["rep"]), {})[row["candidate"]] = row
    comparisons = []
    for (case, rep), block in blocks.items():
        a, b = block.get(left), block.get(right)
        if not a or not b or any(r["status"] != "completed" or not r.get("passed") for r in (a, b)):
            continue
        if any(r.get("wall_s") is None or r["wall_s"] <= 0 for r in (a, b)):
            continue
        comparisons.append({"case": case, "rep": rep, "a_over_b": a["wall_s"] / b["wall_s"],
                            "a_s": a["wall_s"], "b_s": b["wall_s"],
                            "faster": left if a["wall_s"] < b["wall_s"] else right if b["wall_s"] < a["wall_s"] else None})
    ratios = [row["a_over_b"] for row in comparisons]
    return {"a": left, "b": right, "paired_success_count": len(comparisons),
            "median_a_over_b": statistics.median(ratios) if ratios else None,
            "faster_counts": {left: sum(r["faster"] == left for r in comparisons),
                              right: sum(r["faster"] == right for r in comparisons),
                              "ties": sum(r["faster"] is None for r in comparisons)},
            "observations": comparisons}


def report(out):
    frozen = json.loads((out / "freeze.json").read_text())
    inventory = candidate_inventory(frozen)
    ids = [candidate["id"] for candidate in inventory]
    rows = records(out, frozen)
    completed = [r for r in rows if r["status"] == "completed"]
    fast_ids = {candidate["id"] for candidate in inventory if candidate.get("fast")}
    fast = [r for r in completed if r["candidate"] in fast_ids]
    fast_confirmed = bool(fast) and all(r.get("transport", {}).get("fast_served") == "confirmed" for r in fast)
    coverage = len(completed) == len(rows)
    observation_mode = frozen.get("settings", {}).get("observation_mode", "forwarding_proxy")
    summary = {"planned": len(rows), "completed": len(completed), "statuses": dict(Counter(r["status"] for r in rows)),
               "candidates": inventory, "observation_mode": observation_mode,
               "fast_served_confirmed": fast_confirmed, "all_tasks_completed": coverage,
               "verdict": "inconclusive", "by_candidate": {}, "by_case": {}, "pairwise": [], "paired_passed": []}
    lines = ["# Comparação de exploradores no OpenCode", "", "Veredito inconclusivo. Piloto descritivo de exploração individual.", "",
             f"Planejadas {len(rows)}. Concluídas {len(completed)}. Fast servido confirmado {'sim' if fast_confirmed else 'não'}.", "",
             "Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.", "",
             "| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for candidate_id in ids:
        subset = [r for r in rows if r["candidate"] == candidate_id]
        done = [r for r in subset if r["status"] == "completed"]
        times = [r["wall_s"] for r in done if r.get("wall_s") is not None]
        passed = sum(r.get("passed", False) for r in done)
        detail = {"planned": len(subset), "completed": len(done), "passed": passed,
                  "incorrect": len(done) - passed,
                  "errors": sum(r["status"] not in {"completed", "not_run"} for r in subset),
                  "missing": sum(r["status"] == "not_run" for r in subset),
                  "median_s": statistics.median(times) if times else None,
                  "min_s": min(times) if times else None, "max_s": max(times) if times else None,
                  "statuses": dict(Counter(r["status"] for r in subset))}
        summary["by_candidate"][candidate_id] = detail
        values = ["n/d" if detail[key] is None else f"{detail[key]:.2f}" for key in ["median_s", "min_s", "max_s"]]
        lines.append(f"| {candidate_id} | {len(subset)} | {len(done)} | {passed} | {detail['incorrect']} | {detail['errors']} | {detail['missing']} | {' | '.join(values)} |")
    lines += ["", "A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.", "",
              "| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |",
              "|---|---|---|---:|---:|---:|---:|---:|"]
    for left, right in combinations(ids, 2):
        summary["pairwise"].append(pair_detail(left, right, rows))
    for case in frozen["cases"]:
        subset = [r for r in rows if r["case"] == case]
        counts = {candidate_id: sum(r.get("passed", False) and r["status"] == "completed"
                                   for r in subset if r["candidate"] == candidate_id) for candidate_id in ids}
        pairs = [pair_detail(left, right, subset) for left, right in combinations(ids, 2)]
        case_detail = {"passed": counts, "pairwise": pairs}
        for pair in pairs:
            ratio = pair["median_a_over_b"]
            ratio_text = "n/d" if ratio is None else f"{ratio:.3f}"
            faster = pair["faster_counts"]
            lines.append(f"| {case} | {pair['a']} | {pair['b']} | {pair['paired_success_count']} | {ratio_text} | {faster[pair['a']]} | {faster[pair['b']]} | {faster['ties']} |")
        if "sol-fast-low" in ids and "deepseek-max" in ids:
            legacy = pair_detail("sol-fast-low", "deepseek-max", subset)
            case_detail.update(paired_success_count=legacy["paired_success_count"],
                               median_sol_over_deepseek=legacy["median_a_over_b"])
            summary["paired_passed"].extend({"case": r["case"], "rep": r["rep"], "sol_over_deepseek": r["a_over_b"]}
                                             for r in legacy["observations"])
        summary["by_case"][case] = case_detail
    lines += ["", "Uma razão A/B abaixo de 1 indica menor tempo observado para A. As contagens descrevem observações e não declaram vencedor.", "",
              "## Limites", "",
              "- Fast solicitado precisa de confirmação do serviço. Ausência de metadados não confirma atendimento na classe Fast.",
              "- A observação passiva registra parâmetros e metadados selecionados sem redirecionar as chamadas dos provedores."
              if observation_mode == "passive_native_provider" else
              "- O proxy observador encaminhou as chamadas e registrou parâmetros e metadados selecionados nesta execução histórica.",
              "- Repetições do mesmo caso não são tarefas independentes. A suíte sintética não qualifica o modelo para todo repositório.",
              "- Não mede delegação nativa, nem o efeito causal de Fast. Modelo, rota e esforço variam juntos.",
              "- A identidade da sessão e da requisição não atesta qual modelo foi executado a montante.",
              "- Cache remoto pode persistir entre repetições. Contadores nativos de cache ficam nos resultados.",
              "- Custo informado zero não significa gratuidade. Não estima consumo real das assinaturas.",
              "- Isolamento de descoberta e permissões não equivale a sandbox do sistema operacional.",
              "- O relatório não declara vencedor automaticamente. Falhas, variabilidade, qualidade e confirmação de Fast exigem revisão.", ""]
    runtime.save(out / "summary.json", summary)
    (out / "report.md").write_text("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description="OpenCode explorer comparison")
    parser.add_argument("command", choices=["plan", "preflight", "run", "report"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", default=",".join(cases.CASES))
    parser.add_argument("--candidates", default=",".join(c.id for c in runtime.CANDIDATES))
    parser.add_argument("--reps", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--budget-seconds", type=float, default=21600)
    parser.add_argument("--binary", default="opencode")
    parser.add_argument("--database", type=Path, default=Path.home() / ".local/share/opencode/opencode.db")
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/opencode/models.json")
    args = parser.parse_args()
    selected = args.cases.split(",")
    candidate_ids = args.candidates.split(",")
    available = {candidate.id: candidate for candidate in runtime.CANDIDATES}
    if args.reps < 1 or args.timeout <= 0 or args.budget_seconds <= 0 or len(set(selected)) != len(selected) or any(c not in cases.CASES for c in selected):
        parser.error("Invalid cases, repetitions, or time budget")
    if len(set(candidate_ids)) != len(candidate_ids) or any(c not in available for c in candidate_ids):
        parser.error("Invalid candidate list")
    args.selected_candidates = tuple(available[c] for c in candidate_ids)
    out = args.out.resolve()
    if args.command == "report":
        print(json.dumps(report(out), ensure_ascii=False, indent=2))
        return
    if out.exists():
        parser.error("Output directory must be new; prior evidence is never overwritten")
    out.mkdir(parents=True)
    frozen = manifest(selected, args.reps, args.seed, args.timeout, args.budget_seconds, args.cache, args.selected_candidates)
    runtime.save(out / "freeze.json", frozen)
    if args.command == "plan":
        print(f"Frozen {len(frozen['schedule'])} executions in {out}; no model calls")
        report(out)
        return
    checked = preflight(out, args)
    if checked["status"] != "passed":
        report(out)
        parser.exit(1, f"Preflight blocked: {checked['error']}. Evidence: {out / 'preflight.json'}\n")
    if args.command == "preflight":
        print(f"Preflight passed; no model calls. Evidence: {out / 'preflight.json'}")
        return
    started = time.monotonic()
    runtime.save(out / "machine.json", {"load_average": os.getloadavg(), "cpu_count": os.cpu_count()})
    try:
        with tempfile.TemporaryDirectory(prefix="project-", dir="/private/tmp") as folder:
            for row in frozen["schedule"]:
                check_freeze(frozen, args.cache)
                if time.monotonic() - started >= args.budget_seconds:
                    break
                rec = run_trial(row, out, Path(folder), args)
                print(f"{row['id']} {row['candidate']} {row['case']} {rec['status']} passed={rec['passed']}", flush=True)
                report(out)
                if rec["status"] in {"infra_error", "scope_violation"}:
                    print("Stopped after infrastructure or scope failure; remaining trials stay visible", flush=True)
                    break
    finally:
        report(out)


if __name__ == "__main__":
    main()
