#!/usr/bin/env python3
"""Paired language-policy pilot using native Codex subagents; Python stdlib only."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import sys
import tempfile
import time

from cases import CASES, COMMON, build, grade
import runtime
import telemetry

ROOT = Path(__file__).resolve().parent
VARIANTS = {
    "default": "Comunique-se com o usuário em português.\n",
    "pt": "Comunique-se com o usuário em português.\nNas delegações, mensagens e respostas entre agentes, use português e instrua os subagentes a fazer o mesmo. Preserve citações, identificadores e conteúdos que precisem permanecer no idioma original.\n",
    "en": "Comunique-se com o usuário em português.\nNas delegações, mensagens e respostas entre agentes, use inglês e instrua os subagentes a fazer o mesmo. Preserve citações, identificadores e conteúdos que precisem permanecer no idioma original.\n",
}


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def schedule(cases, reps, seed):
    rng = random.Random(seed)
    blocks = list(itertools.product(cases, range(1, reps + 1)))
    rng.shuffle(blocks)
    permutations = list(itertools.permutations(VARIANTS))
    rng.shuffle(permutations)
    return [{"id": f"trial-{i * 3 + j + 1:04}", "case": case, "rep": rep, "variant": variant}
            for i, (case, rep) in enumerate(blocks)
            for j, variant in enumerate(permutations[i % len(permutations)])]


def freeze(args, out):
    sources = sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("*.md"))
    frozen = out / "frozen-source"
    frozen.mkdir()
    for path in sources:
        shutil.copyfile(path, frozen / path.name)
    data = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": args.model, "effort": args.effort, "cli_version": runtime.VERSION,
            "seed": args.seed, "repetitions": args.reps, "timeout_s": args.timeout,
            "budget_s": args.budget_seconds, "conditions": VARIANTS,
            "common_prompt": COMMON, "cases": {c: CASES[c] for c in args.cases},
            "schedule": schedule(args.cases, args.reps, args.seed),
            "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "cpu_count": os.cpu_count(), "load_average": os.getloadavg()}}
    save(out / "freeze.json", data)
    return data


def preflight(args, out):
    audits = {}
    with tempfile.TemporaryDirectory(prefix="language-eval-preflight-") as temp:
        for variant, raw in VARIANTS.items():
            base = Path(temp) / variant
            work = base / "work"
            work.mkdir(parents=True)
            _, audit = runtime.prepare(base, work, raw.encode(), args.binary,
                                       model=args.model, effort=args.effort)
            audits[variant] = audit
    contexts = [runtime.normalized_context(a) for a in audits.values()]
    if any(c != contexts[0] for c in contexts[1:]):
        raise ValueError("Context differs beyond language treatment and temporary paths")
    save(out / "preflight.json", {"equal_except_treatment": True, "conditions": audits})


def run_trial(row, out, args):
    target = out / row["id"]
    target.mkdir()
    result = {**row, "status": "running", "wall_s": None, "grade": None}
    save(target / "result.json", result)
    with tempfile.TemporaryDirectory(prefix="language-eval-trial-") as temp:
        base = Path(temp)
        work = base / "work"
        work.mkdir()
        prompt = build(row["case"], work)
        (target / "prompt.txt").write_text(prompt)
        state = base / "codex-state"
        try:
            env, audit = runtime.prepare(base, work, VARIANTS[row["variant"]].encode(), args.binary,
                                         args.auth_file, args.model, args.effort)
            save(target / "isolation.json", audit)
            response = runtime.command(runtime.argv(args.binary, work, target / "final.txt", prompt,
                                                     args.model, args.effort), work, env, args.timeout)
            result["wall_s"] = response["wall_s"]
            (target / "events.jsonl").write_text(response["stdout"])
            (target / "stderr.txt").write_text(response["stderr"])
            result["exit_code"] = response["exit_code"]
            if response["timeout"]:
                raise TimeoutError("Trial exceeded timeout; process group terminated")
            if response["exit_code"]:
                raise ValueError("Codex exited with an error; inspect stderr.txt")
            parsed = runtime.parse(response["stdout"])
            result["cli_usage_raw"] = parsed["usage"]
            result["session_id"] = parsed["session_id"]
            result["cli_error_events"] = parsed["error_events"]
            data = telemetry.collect(sorted((state / "sessions").rglob("*.jsonl")), parsed["session_id"],
                                     args.model, args.effort, parsed["usage"] or {})
            save(target / "telemetry.json", data)
            save(target / "language-review.json", data["communications"])
            result.update({k: v for k, v in data.items() if k not in {"threads", "communications"}})
            result["grade"] = grade(row["case"], work)
            result["status"] = "completed" if data["measurement_valid"] else "measurement_error"
            if parsed["error_events"]:
                result["status"] = "infra_error"
            if (state / "AGENTS.md").read_text() != VARIANTS[row["variant"]]:
                raise ValueError("Treatment file changed during execution")
        except TimeoutError as exc:
            result.update(status="timeout", error=str(exc))
        except (ValueError, KeyError, OSError) as exc:
            result.update(status="infra_error", error=str(exc))
        except KeyboardInterrupt:
            result.update(status="interrupted", error="Interrupted by operator")
            raise
        finally:
            (state / "auth.json").unlink(missing_ok=True)
            # Retain partial rollouts even for errors; never copy auth/config state wholesale.
            traces = target / "rollouts"
            traces.mkdir(exist_ok=True)
            for trace in (state / "sessions").rglob("*.jsonl"):
                shutil.copyfile(trace, traces / trace.name)
            shutil.copytree(work, target / "work", symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            save(target / "result.json", result)
    return result


def load_rows(out):
    frozen = json.loads((out / "freeze.json").read_text())
    return [{**r, **(json.loads((out / r["id"] / "result.json").read_text())
                    if (out / r["id"] / "result.json").is_file() else {"status": "not_run"})}
            for r in frozen["schedule"]]


def spread(values):
    if not values:
        return "sem dados"
    return f"{statistics.median(values):.1f} [{min(values):.1f}; {max(values):.1f}]"


def report(out):
    rows = load_rows(out)
    lines = ["# Piloto de idioma entre subagentes", "",
             "Veredito de adoção: inconclusivo. Revisão humana de qualidade e idioma pendente.", "",
             "Medianas [mínimo; máximo]. Tokens incluem todos os agentes; cache e raciocínio são parcelas, não acréscimos.", "",
             "| Condição | Planejadas | Concluídas e mensuráveis | Passes factuais | Protocolo correto | Erros/timeouts | Não iniciadas |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for variant in VARIANTS:
        group = [r for r in rows if r["variant"] == variant]
        ok = [r for r in group if r["status"] == "completed"]
        lines.append(f"| {variant} | {len(group)} | {len(ok)} | {sum(bool((r.get('grade') or {}).get('automatic_pass')) for r in group)} | {sum(bool(r.get('protocol_pass')) for r in group)} | {sum(r['status'] not in {'completed', 'not_run'} for r in group)} | {sum(r['status'] == 'not_run' for r in group)} |")
    lines += ["", "## Diferenças pareadas por tarefa", "",
              "Valores negativos favorecem en. Cada par usa a mesma tarefa e repetição.",
              "Todas as execuções completas e mensuráveis entram na primeira linha, inclusive erros factuais e desvios do protocolo.",
              "A segunda linha é análise condicionada a acerto factual e protocolo em ambos os lados; pode ter viés de seleção.", "",
              "| Caso | Comparação | Amostra | Pares | Δ tokens % | Δ tempo % |",
              "|---|---|---|---:|---|---|"]
    comparisons = []
    for case in dict.fromkeys(r["case"] for r in rows):
        for baseline in ("default", "pt"):
            for subset in ("completas", "acerto+protocolo"):
                pairs = []
                for rep in sorted({r["rep"] for r in rows if r["case"] == case}):
                    group = {r["variant"]: r for r in rows if r["case"] == case and r["rep"] == rep}
                    a, b = group[baseline], group["en"]
                    if a["status"] != "completed" or b["status"] != "completed":
                        continue
                    if subset == "acerto+protocolo" and not all(r["protocol_pass"] and r["grade"]["automatic_pass"] for r in (a, b)):
                        continue
                    if a["usage"]["total_tokens"] <= 0 or a["wall_s"] <= 0:
                        continue
                    pairs.append({"rep": rep, "tokens_pct": 100 * (b["usage"]["total_tokens"] / a["usage"]["total_tokens"] - 1),
                                  "time_pct": 100 * (b["wall_s"] / a["wall_s"] - 1)})
                comparisons.append({"case": case, "baseline": baseline, "subset": subset, "pairs": pairs})
                lines.append(f"| {case} | en / {baseline} | {subset} | {len(pairs)} | {spread([p['tokens_pct'] for p in pairs])} | {spread([p['time_pct'] for p in pairs])} |")
    lines += ["", "## Medidas absolutas por condição", "",
              "Somente execuções completas e mensuráveis. Não interpretar falhas rápidas como economia.", "",
              "| Condição | Tokens de entrada | Tokens de saída | Entrada em cache | Raciocínio | Tempo total s |",
              "|---|---|---|---|---|---|"]
    for variant in VARIANTS:
        ok = [r for r in rows if r["variant"] == variant and r["status"] == "completed"]
        fields = [spread([r["usage"][k] for r in ok if r["usage"][k] is not None])
                  for k in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens")]
        lines.append("| " + " | ".join([variant, *fields, spread([r["wall_s"] for r in ok])]) + " |")
    lines += ["", "Rodadas interrompidas preservam registros brutos, mas o consumo de chamadas que falharam pode não ser informado pelo provedor.",
              "O CLI pode cifrar delegações e mensagens intermediárias nos registros. protocol_pass verifica a estrutura de delegação, não adesão ao idioma.",
              "Consulte communication_observability em cada resultado. Mensagens cifradas ficam unobservable na revisão; respostas finais legíveis não provam adesão integral.",
              "Quatro tarefas sintéticas não sustentam generalização. Não há conversão de tokens em custo monetário nem estimativa de idioma do raciocínio interno.",
              "Use REVIEW.md e os pacotes de revisão antes de interpretar eficiência com qualidade preservada.", ""]
    (out / "report.md").write_text("\n".join(lines))
    save(out / "summary.json", {"verdict": "inconclusive", "rows": rows, "comparisons": comparisons})


def blind(out):
    rows = [r for r in load_rows(out) if (out / r["id"] / "work/report.md").is_file()]
    random.Random(7831).shuffle(rows)
    destination = out / "blind-review"
    destination.mkdir(exist_ok=True)
    mapping, template = {}, []
    for i, row in enumerate(rows, 1):
        label = f"sample-{i:03}"
        mapping[label] = row["id"]
        folder = destination / label
        folder.mkdir(exist_ok=True)
        for name in ("answer.json", "report.md"):
            source = out / row["id"] / "work" / name
            if source.is_file():
                shutil.copyfile(source, folder / name)
        frozen = json.loads((out / "freeze.json").read_text())
        case = frozen["cases"][row["case"]]
        save(folder / "reference.json", {k: case[k] for k in ("prompt", "files", "expected", "rubric")})
        template.append({"sample": label, "portuguese": None, "factual_explanation": None,
                         "complete": None, "unsupported_claims": None, "notes": ""})
    save(out / "blind-key.json", mapping)
    # A refreshed report must not erase reviewer annotations.
    if not (destination / "ratings.json").exists():
        save(destination / "ratings.json", template)


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use an integer greater than zero")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "preflight", "run", "report"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", default=runtime.MODEL)
    parser.add_argument("--effort", choices=("low", "medium", "high", "xhigh"), default=runtime.EFFORT)
    parser.add_argument("--reps", type=positive, default=5)
    parser.add_argument("--cases", nargs="+", choices=tuple(CASES), default=list(CASES))
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--timeout", type=positive, default=300)
    parser.add_argument("--budget-seconds", type=positive, default=21600)
    parser.add_argument("--binary", default="codex")
    parser.add_argument("--auth-file", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "auth.json")
    args = parser.parse_args()
    if len(set(args.cases)) != len(args.cases):
        parser.error("Duplicate case")
    if args.command == "report":
        if not args.out:
            parser.error("report requires --out")
        report(args.out.resolve())
        blind(args.out.resolve())
        return
    out = (args.out or ROOT / ("results" if args.command == "run" else "validation") /
           (args.command + "-" + time.strftime("%Y%m%d-%H%M%S"))).resolve()
    if out.exists():
        parser.error(f"Output directory must be new: {out}")
    if args.command == "run" and not args.auth_file.is_file():
        parser.error("Codex auth.json not found; log in or set --auth-file")
    out.mkdir(parents=True)
    manifest = freeze(args, out)
    print(f"{len(manifest['schedule'])} execuções planejadas. Saída: {out}", flush=True)
    if args.command == "plan":
        return
    started = time.monotonic()
    try:
        preflight(args, out)
        print("Contextos verificados: diferença restrita ao tratamento.", flush=True)
        if args.command == "preflight":
            return
        for i, row in enumerate(manifest["schedule"]):
            if i % 3 == 0 and time.monotonic() - started + 3 * args.timeout + 180 > args.budget_seconds:
                print("Orçamento insuficiente para iniciar outro bloco de três condições.", flush=True)
                break
            print(f"[{i + 1}/{len(manifest['schedule'])}] {row['case']} rep={row['rep']} {row['variant']}", flush=True)
            result = run_trial(row, out, args)
            report(out)
            if result["status"] != "completed":
                print(f"Parada: {result['status']}. Consulte {out / row['id']}", flush=True)
                break
            if not result["protocol_pass"]:
                print("Desvio do protocolo registrado; continua na análise por condição atribuída.", flush=True)
    finally:
        if args.command == "run":
            report(out)
            blind(out)
    if args.command == "run":
        print(f"Relatório: {out / 'report.md'}", flush=True)
        if any(r["status"] != "completed" for r in load_rows(out)):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
