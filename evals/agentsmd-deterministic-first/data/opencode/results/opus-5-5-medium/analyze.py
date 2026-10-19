"""Reproduce the Opus CPA analysis offline, using the frozen evaluator."""
import csv
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import sys
import tempfile
from collections import Counter

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT / "frozen-source"))
from cases import build, grade, snapshot
import opencode_runtime as runtime


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values):
    return {"sum": sum(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


def percent(a, b):
    return 100 * (b / a - 1) if a else None


def active_tool_seconds(tools):
    intervals = sorted((t["time"]["ran"], t["time"]["completed"]) for t in tools)
    total, end = 0, 0
    for start, stop in intervals:
        assert stop >= start
        total += max(0, stop - max(end, start))
        end = max(end, stop)
    return total / 1000


freeze = read(OUT / "freeze.json")
hashes = {**freeze["source_sha256"], "README.md": freeze["protocol_sha256"],
          "REVIEW.md": freeze["review_rubric_sha256"]}
assert all(digest(OUT / "frozen-source" / name) == value for name, value in hashes.items())
assert all(digest(OUT / "frozen-source/variants" / v / "AGENTS.md") == value
           for v, value in freeze["variant_sha256"].items())
seal = read(OUT / "review-seal.json")
key = read(OUT / "blind-key.json")
reviews = {}
for label, value in seal["review_sha256"].items():
    path = OUT / "blind" / label / "review.json"
    assert digest(path) == value
    reviews[key[label]] = read(path)
preflight = read(OUT / "preflight.json")
assert preflight["equal_configuration_and_discovery"]
assert freeze["provider_config"] == runtime.config()["providers"]
assert freeze["model"] == runtime.MODEL and freeze["effort"] == runtime.EFFORT
rows, tool_errors, nonzero = [], [], []
exports = 0
for planned in freeze["schedule"]:
    folder = OUT / planned["id"]
    row = read(folder / "result.json")
    assert all(row[k] == v for k, v in planned.items())
    assert row["status"] == "completed"
    audit = read(folder / "isolation.json")
    assert audit["agents_sha256"] == freeze["variant_sha256"][row["variant"]]
    assert audit["model"] == runtime.MODEL and audit["effort"] == runtime.EFFORT
    assert audit["config"] == runtime.config()
    assert audit["home_is_private"] and audit["project_config_disabled"]
    assert audit["discovery"] == preflight["variants"][row["variant"]]["discovery"]
    assert audit["discovery"]["skills"] == []
    for turn in range(1, len(freeze["cases"][row["case"]]["prompts"]) + 1):
        exported = read(folder / f"turn-{turn}-export.json")
        parsed = runtime.parse_export(exported, row["session_id"], Path(exported["info"]["location"]["directory"]), turn)
        exports += 1
    for field in ["usage_raw", "input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens",
                  "reasoning_tokens", "actual_model", "reported_cost_usd"]:
        assert parsed[field] == row[field], (row["id"], field)
    assert parsed["error_events"] == row["recoverable_error_events"] == []
    assert parsed["final"] == (folder / "final.txt").read_text()
    tools = read(folder / "tool-events.json")
    assert tools == parsed["tools"] and len(tools) == row["tool_calls"]
    for i, tool in enumerate(tools):
        state = tool["state"]
        info = {"trial": row["id"], "case": row["case"], "variant": row["variant"], "tool_index": i}
        if state["status"] != "completed":
            tool_errors.append({**info, "name": tool["name"], "error": state.get("error")})
        if state.get("metadata", {}).get("exit") not in (None, 0):
            nonzero.append({**info, "exit": state["metadata"]["exit"], "input": state["input"]})
    with tempfile.TemporaryDirectory(prefix="opus-regrade-") as temp:
        temp = Path(temp)
        fixture = temp / "fixture"
        fixture.mkdir()
        state = build(row["case"], fixture)
        assert state["initial"] == read(folder / "initial-files.json")
        work = temp / "work"
        shutil.copytree(folder / "work", work)
        checked = grade(row["case"], work, parsed["final"], state)
        assert checked == row["grade"], row["id"]
    assert checked["automatic_pass"]
    if checked["needs_blind_review"]:
        assert reviews[row["id"]]["outcome_pass"] is True
        label = next(label for label, trial in key.items() if trial == row["id"])
        assert snapshot(OUT / "blind" / label / "work") == snapshot(folder / "work")
        assert (OUT / "blind" / label / "final.txt").read_bytes() == (folder / "final.txt").read_bytes()
    row["outcome_pass"] = True
    row["tool_active_s"] = active_tool_seconds(tools)
    row["tool_errors"] = sum(t["state"]["status"] != "completed" for t in tools)
    rows.append(row)

assert len(rows) == 72 and exports == 78 and len(reviews) == 12
metrics = ["wall_s", "output_tokens", "input_tokens", "cached_input_tokens", "cache_write_tokens",
           "reasoning_tokens", "tool_calls", "tool_active_s", "tool_errors"]
variants = ["empty", "deterministic"]
summary = {v: {m: describe([r[m] for r in rows if r["variant"] == v]) for m in metrics} for v in variants}
deltas = {m: percent(summary["empty"][m]["sum"], summary["deterministic"][m]["sum"]) for m in metrics}
cases = {c: {v: {m: describe([r[m] for r in rows if r["case"] == c and r["variant"] == v])
                 for m in metrics} for v in variants} for c in freeze["cases"]}
pairs = [{"case": a["case"], "rep": a["rep"],
          "delta_s": next(r["wall_s"] for r in (a, b) if r["variant"] == "deterministic")
                     - next(r["wall_s"] for r in (a, b) if r["variant"] == "empty")}
         for a, b in zip(rows[::2], rows[1::2])]
rng = random.Random(20261010)
bootstrap = []
for _ in range(20000):
    sample = rng.choices(list(cases), k=len(cases))
    a, b = [sum(cases[c][v]["wall_s"]["mean"] for c in sample) for v in variants]
    bootstrap.append(percent(a, b))
bootstrap.sort()
interval = [bootstrap[499], bootstrap[19499]]
without_repeat = {v: describe([r["wall_s"] for r in rows if r["variant"] == v and r["case"] != "repeat"])
                  for v in variants}
overlap = {v: sum(r["grade"]["observations"].get("all_three_overlap", False)
                  for r in rows if r["variant"] == v and r["case"] == "independent") for v in variants}
prior = read(OUT.parent / "pilot-r2/analysis.json")
prior_freeze = read(OUT.parent / "pilot-r2/freeze.json")
for field in ["schedule", "cases", "variant_sha256", "review_rubric_sha256"]:
    assert freeze[field] == prior_freeze[field]
cross_time = {v: {"sol_mean_s": prior["summary"][v]["wall_s"]["mean"],
                  "opus_mean_s": summary[v]["wall_s"]["mean"],
                  "difference_percent": percent(prior["summary"][v]["wall_s"]["sum"], summary[v]["wall_s"]["sum"])}
              for v in variants}
analysis = {"model": runtime.SELECTION, "completed": 72, "completed_pairs": 36,
            "outcomes": {v: {"pass": 36, "total": 36} for v in variants},
            "summary": summary, "treatment_difference_percent": deltas, "cases": cases, "paired_times": pairs,
            "exploratory_time_cluster_bootstrap": {"unit": "case, preserving all three paired repetitions", "samples": 20000,
                "seed": 20261010, "interval_95_percent": interval, "pre_registered": False},
            "treatment_faster_pairs": sum(p["delta_s"] < 0 for p in pairs),
            "without_repeat": {"summary": without_repeat, "time_difference_percent": percent(without_repeat["empty"]["sum"], without_repeat["deterministic"]["sum"])},
            "all_three_independent_checks_overlap": overlap,
            "exploratory_opus_vs_sol_time": cross_time,
            "audit": {"exports_checked": exports, "artifacts_regraded": 72, "subjective_reviews": 12,
                "tool_errors": tool_errors, "nonzero_shell_commands": nonzero,
                "assistant_errors": 0, "infrastructure_failures": 0,
                "all_stderr_empty": all(p.stat().st_size == 0 for p in OUT.glob("trial-*/*.stderr")),
                "native_input_value_frequency": dict(Counter(u["input"] for r in rows for u in r["usage_raw"])),
                "source_sha256": hashes, "equal_configuration_and_discovery": True,
                "full_prompt_equality_verified": preflight["full_prompt_equality_verified"]},
            "limitations": ["Three repetitions of 12 synthetic tasks; outcome ceiling",
                "Assistant subjective review; not independent or guaranteed blind",
                "CPA/OpenCode accounting not verified against upstream; no monetary or total-token comparison",
                "Requested alias and effort verified in exports, not attested by upstream provider",
                "No resource profile or server timing to separate model, proxy, boot and network latency",
                "Cross-model comparison changes model, effort and provider in separate, non-interleaved rounds"]}
(OUT / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n")
with (OUT / "metrics.tsv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["id", "case", "rep", "variant", "outcome_pass", *metrics], delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

lines = ["# Resultado do Opus 5.5 medium via CPA", "",
    "O trecho Deterministic first não trouxe ganho de acerto nesta amostra. As duas condições entregaram 36/36 tarefas corretas. Com o trecho, a duração média foi 5,8% maior e os tokens de saída reportados aumentaram 14,9%. A diferença global de tempo é pequena frente à variação entre casos; não há evidência suficiente de uma piora geral de velocidade.", "",
    "OpenCode 2.0.25, cli_proxy/cpa-claude-opus-5-5#medium. São 12 casos sintéticos, três repetições por condição, 36 pares e 72 execuções em 10/10/2026. A ordem dentro dos pares foi balanceada, com cada condição primeiro em 18 pares.", "",
    "| Métrica | AGENTS vazio | Com o trecho | Diferença |", "|---|---:|---:|---:|",
    "| Entregas corretas | 36/36 | 36/36 | 0 p.p. |"]
for label, metric, stat in [("Tempo médio, s", "wall_s", "mean"), ("Tempo mediano, s", "wall_s", "median"),
                          ("Tokens de saída reportados", "output_tokens", "sum"), ("Chamadas de ferramentas", "tool_calls", "sum")]:
    a, b = [summary[v][metric][stat] for v in variants]
    cells = [f"{x:.2f}".replace(".", ",") if metric == "wall_s" else f"{x:,}".replace(",", ".") for x in (a, b)]
    delta = f"{percent(a, b):+.1f}".replace(".", ",")
    lines.append(f"| {label} | {cells[0]} | {cells[1]} | {delta}% |")
lines += ["", f"O tratamento foi mais rápido em {analysis['treatment_faster_pairs']}/36 pares. O intervalo exploratório de 95% por bootstrap agrupado nos 12 casos foi [{interval[0]:+.1f}%, {interval[1]:+.1f}%] para a diferença de duração média. Esse cálculo foi escolhido após a rodada; não é um teste confirmatório pré-registrado. O intervalo inclui zero.", "",
    "## Onde o comportamento mudou", "",
    "Em repeat, a mediana passou de 12,53 s para 24,42 s. Todas as três execuções com o trecho foram mais lentas que todas as três sem ele. O controle já calculava os JSONs com Python. O tratamento criou um script temporário no segundo turno e acrescentou inspeções ou reexecuções de validação. A entrega continuou correta nas duas condições. Evidência: tool-events.json de trial-0019, 0020, 0035, 0036, 0051 e 0052.", "",
    f"Excluindo repeat apenas como análise de sensibilidade, a diferença de tempo fica em {analysis['without_repeat']['time_difference_percent']:+.1f}%. Portanto, o acréscimo global está concentrado nesse caso, não distribuído uniformemente pela suíte.", "",
    "O trecho não aumentou o paralelismo observado. Os três checks independentes se sobrepuseram em 1/3 execuções do controle e 0/3 com o trecho. Os seis resultados numéricos estavam corretos; a rubrica congelada registra sobreposição como comportamento, sem torná-la requisito de acerto. Assim, 72/72 entregas corretas não significa obediência perfeita a todas as frases do bloco. Evidência: arquivos *-timing.json dos trials 0045, 0046, 0059, 0060, 0071 e 0072.", "",
    "As proteções de guardrail e regression passaram em 6/6 entregas de cada condição, incluindo probes e reintrodução da falha em cópias dos artefatos. Não houve vantagem de prevenção dentro desses casos. O controle também gerou customers.json por Python nas três repetições de convert; a instrução não era necessária para esse comportamento no Opus.", "",
    "## Duração por caso", "", "Mediana e intervalo mínimo a máximo, em segundos. Três repetições por célula.", "",
    "| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |", "|---|---:|---:|"]
for c, group in cases.items():
    cells = [f"{group[v]['wall_s']['median']:.2f}; {group[v]['wall_s']['min']:.2f} a {group[v]['wall_s']['max']:.2f}" for v in variants]
    lines.append(f"| {c} | {' | '.join(cells)} |")
lines += ["", "## Auditoria e limites", "",
    "Foram conferidas 78 exportações, incluindo a continuidade dos dois prompts de repeat. Provider, alias, variante medium e agente build conferem em todas as mensagens do assistente. Os contadores batem com a última exportação cumulativa. Os 72 artefatos foram corrigidos novamente em cópias separadas, incluindo as mutações usadas para testar prevenção de reincidência. Nenhuma inferência nova foi feita nesta análise.", "",
    "Os 12 controles subjetivos passaram na rubrica original. As revisões dos artefatos sem rótulos foram seladas antes da consulta à chave atual. O assistente já conhecia o desenho, o relatório automático agregado e a rodada Sol. O embaralhamento usa a mesma seed da rodada anterior, e a redação sugere o tratamento em alguns casos. Não há revisão humana independente nem cegamento garantido. Os hashes confirmam ausência de mudanças em out_of_scope e alteração exclusiva de message.md em judgment.", "",
    "Não houve falha de infraestrutura nem erro final do assistente. Houve duas chamadas à ferramenta inexistente tool_write, recuperadas depois: trial-0037 no tratamento e trial-0042 no controle. Também houve dois comandos shell com saída 1 no controle: head -0 incompatível com macOS em trial-0008 e leitura de arquivos opcionais ausentes em trial-0010. As quatro execuções terminaram corretas. O campo recoverable_error_events do executor contém erros de mensagem, não todos os erros de ferramentas; esta auditoria consultou tool-events.json diretamente.", "",
    "O tempo mede as invocações do agente, incluindo inicialização, ferramentas e eventuais retries internos; exclui preparação, auditoria, exportação e correção. Não há perfil nem telemetria do servidor para separar inferência, proxy, rede e inicialização. Os intervalos de execução das ferramentas estão somados sem sobreposição em metrics.tsv, mas o restante do tempo não pode ser atribuído a um componente específico. Não se identificou um gargalo causal de desempenho.", "",
    "O CPA reportou entrada nativa de apenas 2 tokens em 307 mensagens e 4 tokens em seis mensagens, raciocínio zero e volumes altos de cache. Preservamos entrada, cache de leitura, cache de gravação e saída separados em analysis.json. O aumento de 14,9% refere-se somente à saída reportada; não equivale a aumento de custo ou tokens totais. Raciocínio zero no contador não comprova ausência de raciocínio. O custo informado pelo OpenCode não foi conciliado com cobrança do proxy.", "",
    "Configuração e descoberta conferem com o preflight nas duas condições e em todos os trials; não há skills adicionais. Isso não comprova igualdade integral do prompt HTTP. As exportações confirmam a seleção no cliente, sem atestar a identidade efetivamente servida pelo provedor a montante. Fontes, protocolo e variantes estão em frozen-source/, conferidos contra freeze.json. Os dados brutos da rodada foram preservados.", "",
    "## Comparação exploratória com Sol no OpenCode", "",
    "| Condição | Sol xhigh, média em s | Opus medium via CPA, média em s | Diferença |", "|---|---:|---:|---:|"]
for v, values in cross_time.items():
    lines.append(f"| {v} | {values['sol_mean_s']:.2f} | {values['opus_mean_s']:.2f} | {values['difference_percent']:+.1f}% |")
lines += ["", "Ambas as rodadas entregaram 72/72 resultados aceitos na mesma suíte. O Opus via CPA levou menos tempo observado, mas modelo, esforço, provider e horário da rodada mudaram juntos. As rodadas não foram intercaladas; isso não isola um efeito do modelo ou do provider. A contabilidade de tokens do CPA impede transportar diretamente a normalização usada na comparação anterior Codex/OpenCode.", "",
    "## Recomendação", "",
    "Manter o bloco removido do AGENTS global continua sendo a escolha apoiada por estes pilotos. Não apareceu ganho de qualidade nas três configurações avaliadas, e o custo de criar script em repeat se repetiu no Opus. Isso não prova que cada recomendação do bloco seja inútil. A suíte é pequena, sintética e já está no teto de acertos; benefícios em tarefas reais mais difíceis, reutilização futura ou reincidência fora destes probes não foram medidos. A diferença global de tempo nesta rodada permanece inconclusiva.", "",
    "Reprodução offline: `python3 agentsmd-detfirst-opencode/results/opus-5-5-medium/analyze.py`. Dados: [analysis.json](analysis.json), [metrics.tsv](metrics.tsv), [review-seal.json](review-seal.json)."]
(OUT / "analysis.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"outcomes": analysis["outcomes"], "deltas": deltas, "time_interval": interval,
                  "faster_pairs": analysis["treatment_faster_pairs"], "without_repeat": analysis["without_repeat"]["time_difference_percent"],
                  "overlap": overlap, "cross_time": cross_time}, ensure_ascii=False))
