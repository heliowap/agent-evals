"""Audit and summarize the completed OpenCode study without changing trial evidence."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CODEX = ROOT.parent / "agentsmd-detfirst-isolated/results/pilot"
sys.path.insert(0, str(OUT / "frozen-source"))
from cases import snapshot
import opencode_runtime as runtime


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values):
    return {"sum": sum(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


freeze = read(OUT / "freeze.json")
hashes = {**freeze["source_sha256"], "README.md": freeze["protocol_sha256"],
          "REVIEW.md": freeze["review_rubric_sha256"]}
assert all(digest(OUT / "frozen-source" / name) == value for name, value in hashes.items())
assert digest(ROOT / "REVIEW.md") == freeze["review_rubric_sha256"]
assert all(digest(ROOT / "variants" / variant / "AGENTS.md") == value
           for variant, value in freeze["variant_sha256"].items())
codex_freeze = read(CODEX / "freeze.json")
assert freeze["schedule"] == codex_freeze["schedule"]
assert freeze["cases"] == codex_freeze["cases"]
assert freeze["variant_sha256"] == codex_freeze["variant_sha256"]
seal = read(OUT / "review-seal.json")
assert all(digest(OUT / "blind" / label / "review.json") == value
           for label, value in seal["review_sha256"].items())
key = read(OUT / "blind-key.json")
reviews = {key[label]: read(OUT / "blind" / label / "review.json") for label in seal["review_sha256"]}
codex_seal, codex_key = read(CODEX / "review-seal.json"), read(CODEX / "blind-key.json")
codex_reviews = {}
for label, value in codex_seal["review_sha256"].items():
    path = CODEX / "blind" / label / "review.json"
    assert digest(path) == value
    codex_reviews[codex_key[label]] = read(path)
preflight = read(OUT / "preflight.json")
assert preflight["equal_configuration_and_discovery"]

rows, cross_rows, nonzero = [], [], []
export_count = 0
for planned in freeze["schedule"]:
    folder = OUT / planned["id"]
    row = read(folder / "result.json")
    assert all(row[k] == v for k, v in planned.items())
    assert row["status"] == "completed" and row["grade"]["automatic_pass"]
    audit = read(folder / "isolation.json")
    assert audit["agents_sha256"] == freeze["variant_sha256"][row["variant"]]
    assert audit["model"] == runtime.MODEL and audit["effort"] == runtime.EFFORT
    assert audit["discovery"]["skills"] == []
    assert audit["home_is_private"] and audit["project_config_disabled"]
    assert audit["discovery"] == preflight["variants"][row["variant"]]["discovery"]
    for turn in range(1, len(freeze["cases"][row["case"]]["prompts"]) + 1):
        exported = read(folder / f"turn-{turn}-export.json")
        work = Path(exported["info"]["location"]["directory"])
        parsed = runtime.parse_export(exported, row["session_id"], work, turn)
        export_count += 1
    for field in ["usage_raw", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens",
                  "cache_write_tokens", "actual_model"]:
        assert parsed[field] == row[field], (row["id"], field)
    assert not parsed["error_events"] and not row["recoverable_error_events"]
    assert parsed["final"] == (folder / "final.txt").read_text()
    tools = read(folder / "tool-events.json")
    assert parsed["tools"] == tools and len(tools) == row["tool_calls"]
    for index, tool in enumerate(tools):
        state = tool["state"]
        assert state["status"] == "completed"
        if state.get("metadata", {}).get("exit") not in {None, 0}:
            assert row["case"] == "regression" and "unittest" in state["input"]["command"]
            nonzero.append({"trial": row["id"], "tool_index": index,
                            "classification": "expected_failing_test_before_fix"})
    before, after = read(folder / "initial-files.json"), snapshot(folder / "work")
    obs = row["grade"]["observations"]
    assert sorted(after.keys() - before.keys()) == obs["added_files"]
    assert sorted(p for p in before.keys() & after.keys() if before[p] != after[p]) == obs["modified_files"]
    if row["case"] == "out_of_scope":
        assert before == after
    if row["case"] == "judgment":
        assert before.keys() == after.keys() and obs["modified_files"] == ["message.md"]
    if row["grade"]["needs_blind_review"]:
        assert reviews[row["id"]]["outcome_pass"] is True
    row["outcome_pass"] = True
    row["input_inclusive"] = row["input_tokens"] + row["cached_input_tokens"] + row["cache_write_tokens"]
    row["output_inclusive"] = row["output_tokens"] + row["reasoning_tokens"]
    row["total_tokens"] = row["input_inclusive"] + row["output_inclusive"]
    rows.append(row)
    codex = read(CODEX / row["id"] / "result.json")
    assert all(codex[k] == row[k] for k in ["case", "rep", "variant"])
    assert codex["status"] == "completed" and codex["grade"]["automatic_pass"]
    if codex["grade"]["needs_blind_review"]:
        assert codex_reviews[row["id"]]["outcome_pass"] is True
    usage = codex["usage_raw"][-1]
    cross_rows.append({"id": row["id"], "case": row["case"], "rep": row["rep"], "variant": row["variant"],
                       "opencode": {k: row[k] for k in ["wall_s", "input_inclusive", "output_inclusive", "total_tokens"]},
                       "codex": {"wall_s": codex["wall_s"], "input_inclusive": usage["input_tokens"],
                                 "output_inclusive": usage["output_tokens"],
                                 "total_tokens": usage["input_tokens"] + usage["output_tokens"]}})

assert len(rows) == 72 and len(reviews) == 12 and export_count == 78
metrics = ["wall_s", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "tool_calls",
           "input_inclusive", "output_inclusive", "total_tokens"]
summary = {v: {k: describe([r[k] for r in rows if r["variant"] == v]) for k in metrics}
           for v in ["empty", "deterministic"]}
deltas = {k: 100 * (summary["deterministic"][k]["sum"] / summary["empty"][k]["sum"] - 1) for k in metrics}
cases = {case: {v: describe([r["wall_s"] for r in rows if r["case"] == case and r["variant"] == v])
                for v in summary} for case in freeze["cases"]}
cross_summary = {}
for variant in ["empty", "deterministic", "combined"]:
    group = [r for r in cross_rows if variant == "combined" or r["variant"] == variant]
    stats = {agent: {k: describe([r[agent][k] for r in group]) for k in group[0][agent]}
             for agent in ["codex", "opencode"]}
    cross_summary[variant] = {"n": len(group), **stats,
        "opencode_difference_percent": {k: 100 * (stats["opencode"][k]["sum"] / stats["codex"][k]["sum"] - 1)
                                         for k in group[0]["codex"]},
        "opencode_faster_trials": sum(r["opencode"]["wall_s"] < r["codex"]["wall_s"] for r in group)}
normalization = read(OUT / "cross-runtime-partial-20261010-132404.json")
analysis = {"model": runtime.MODEL, "effort": runtime.EFFORT, "completed": 72, "completed_pairs": 36,
            "outcomes": {v: {"pass": 36, "total": 36} for v in summary}, "summary": summary,
            "treatment_difference_percent": deltas, "cases": cases,
            "cross_runtime": {"summary": cross_summary, "matched_trials": cross_rows,
                              "normalization": normalization["normalization"],
                              "binary_sha256": normalization["opencode_binary_sha256"],
                              "verified_binary_fragments": normalization["verified_binary_fragments"]},
            "audit": {"exports_checked": export_count, "subjective_reviews": len(reviews),
                      "scope_hashes_checked": True, "original_sources_preserved": hashes,
                      "equal_configuration_and_discovery": True,
                      "full_prompt_equality_verified": preflight["full_prompt_equality_verified"],
                      "unexpected_tool_failures": 0, "expected_nonzero_tools": nonzero}}
(OUT / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
with (OUT / "metrics.tsv").open("w", newline="") as stream:
    fields = ["id", "case", "rep", "variant", "outcome_pass", *metrics]
    writer = csv.DictWriter(stream, fields, delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

lines = ["# Resultado final do OpenCode", "",
         "O trecho Deterministic first não demonstrou ganho de qualidade. As duas condições entregaram 36/36 tarefas corretas. Com o trecho, o OpenCode usou mais tempo e tokens nesta amostra. O piloto continua inconclusivo para adoção geral.", "",
         "OpenCode 2.0.25, openai/gpt-6.1-sol#xhigh. Doze tarefas sintéticas, três repetições por condição, 36 pares e 72 execuções concluídas em 10/10/2026. Este relatório substitui os recortes parciais para interpretar a rodada.", "",
         "| Métrica | AGENTS vazio | Com o trecho | Diferença observada |",
         "|---|---:|---:|---:|", "| Entregas corretas | 36/36 | 36/36 | 0 ponto percentual |"]
for label, metric, stat in [
    ("Tempo médio por tarefa, s", "wall_s", "mean"),
    ("Tempo mediano por tarefa, s", "wall_s", "median"),
    ("Entrada sem cache", "input_tokens", "sum"),
    ("Entrada em cache", "cached_input_tokens", "sum"),
    ("Saída sem raciocínio", "output_tokens", "sum"),
    ("Raciocínio", "reasoning_tokens", "sum"),
    ("Saída incluindo raciocínio", "output_inclusive", "sum"),
    ("Tokens totais, incluindo cache e raciocínio", "total_tokens", "sum"),
    ("Chamadas de ferramentas", "tool_calls", "sum")]:
    a, b = [summary[v][metric][stat] for v in summary]
    fmt = (lambda value: f"{value:.1f}") if metric == "wall_s" else (lambda value: f"{value:,}".replace(",", "."))
    lines.append(f"| {label} | {fmt(a)} | {fmt(b)} | {100 * (b / a - 1):+.1f}% |")
lines += ["", "A diferença média de duração foi de 8,0 s por tarefa, cerca de 4 min 49 s adicionais nas 36 execuções com o trecho. O número de chamadas de ferramentas pouco mudou; a diferença aparece também no volume de raciocínio e no conteúdo das operações. Não houve perfil que separe a contribuição causal de cada componente para a duração.", "",
          "## Qualidade, isolamento e auditoria", "",
          "As 72 execuções passaram nos corretores. As 78 exportações confirmam modelo, effort, sessão e conclusão de cada turno, inclusive continuidade dos seis casos repeat. Os contadores dos resultados conferem com a última exportação cumulativa, sem duplicar o primeiro turno. Não há erros de infraestrutura ou erros do assistente registrados. Os seis comandos com retorno diferente de zero foram testes de regressão deliberadamente vermelhos antes da correção; todos os artefatos finais passaram.", "",
          "Os 12 controles subjetivos também passaram pela rubrica congelada. A comparação de hashes confirmou que out_of_scope não alterou arquivos e judgment alterou somente message.md. As decisões constam de blind/*/review.json e foram seladas em [review-seal.json](review-seal.json) antes da consulta à chave desta rodada. O revisor foi o assistente e já conhecia métricas e o desenho do estudo. Rótulos estavam ocultos, mas não há garantia de cegamento nem revisão humana independente.", "",
          "A configuração e a descoberta de plugins/skills conferem com o preflight em todos os trials. Não há skills adicionais. O OpenCode não expõe o prompt completo neste fluxo; igualdade do prompt HTTP inteiro não foi demonstrada. Fontes e protocolo originais estão em [frozen-source/](frozen-source/), com hashes iguais ao freeze.json. Casos, rubrica, tratamento e resultados brutos não foram alterados.", "",
          "## Duração por caso", "",
          "Mediana e intervalo mínimo a máximo, em segundos, com três execuções corretas em cada célula.", "",
          "| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |", "|---|---:|---:|"]
for case, groups in cases.items():
    cells = [f"{g['median']:.1f}; {g['min']:.1f} a {g['max']:.1f}" for g in groups.values()]
    lines.append(f"| {case} | {' | '.join(cells)} |")
lines += ["", "Os maiores acréscimos totais estão em rename e repeat. Em ambos, todas as execuções com o trecho foram mais lentas que todas as execuções sem o trecho. Em repeat, o controle calcula os resumos com Python inline e grava por patch. O tratamento cria um arquivo temporário reutilizável e adiciona verificações. A entrega final permaneceu correta em todas as repetições. Evidência: tool-events.json de trial-0019, 0020, 0035, 0036, 0051 e 0052.", "",
          "Há um sinal favorável em convert: mediana de 75,5 s para 51,7 s. Os três controles gravam o JSON por patch; dois dos três tratamentos o gravam por programa. O terceiro tratamento ainda usa patch e leva 103,2 s. Isso sugere que escrever diretamente a transformação computada pode evitar trabalho, mas três repetições e essa variabilidade não sustentam uma promessa de velocidade. Evidência: tool-events.json de trial-0015, 0016, 0067, 0068, 0069 e 0070.", "",
          "Os três checks independentes se sobrepuseram em 3/3 execuções de cada condição. Os casos guardrail e regression detectaram reincidência em 6/6 de cada condição. O trecho não trouxe vantagem de qualidade nesses comportamentos, que já apareciam no controle.", "",
          "## Comparação exploratória com Codex", "",
          "Mesmas 72 combinações de caso, repetição e condição em cada produto. Ambos tiveram 72/72 entregas aceitas pela régua, incluindo os controles revisados. Os tokens foram normalizados: o Codex inclui cache na entrada e raciocínio na saída; no OpenCode essas parcelas são separadas. A transformação foi conferida no código compilado do executável OpenCode 2.0.25; o hash e os trechos estão em analysis.json.", "",
          "| Condição | Tempo médio Codex, s | Tempo médio OpenCode, s | Diferença de tempo | Diferença de tokens totais |",
          "|---|---:|---:|---:|---:|"]
for variant in ["empty", "deterministic"]:
    value = cross_summary[variant]
    lines.append(f"| {variant} | {value['codex']['wall_s']['mean']:.1f} | {value['opencode']['wall_s']['mean']:.1f} | {value['opencode_difference_percent']['wall_s']:+.1f}% | {value['opencode_difference_percent']['total_tokens']:+.1f}% |")
combined = cross_summary["combined"]
lines += ["", f"No conjunto completo, o OpenCode consumiu {-combined['opencode_difference_percent']['total_tokens']:.1f}% menos tokens totais e levou {-combined['opencode_difference_percent']['wall_s']:.1f}% menos tempo que o Codex. Foram 1.983.765 versus 4.438.212 tokens, incluindo contexto reenviado, cache e raciocínio. Foi mais rápido em {combined['opencode_faster_trials']}/72 correspondências. A maior redução está na entrada.", "",
          "Essa comparação entre produtos é exploratória. As rodadas não foram sorteadas/intercaladas entre produtos, houve sobreposição parcial dos seus períodos de execução e instruções internas, ferramentas, permissões e integrações diferem. O desenho isolou o efeito do AGENTS dentro de cada produto; não identifica qual componente explica a diferença entre eles. A duração cobre invocações do agente com inicialização e ferramentas, mas exclui preparação, auditoria, exportação e correção do eval. Não representa tempo total do processo de avaliação nem throughput do modelo. Não foi estimado custo monetário.", "",
          "## Interpretação", "",
          "A evidência das duas rodadas favorece revisar as obrigações do bloco antes de mantê-lo como política global. Não apareceu ganho de acerto; o controle atingiu o teto da régua e o trecho aumentou a duração agregada nos dois produtos. Isso não prova que cada frase seja inútil ou prejudicial. O caso convert no OpenCode sugere uma vantagem localizada de produzir o arquivo por programa, enquanto a regra de criar script na segunda ocorrência acrescentou trabalho em repeat.", "",
          "Há somente três repetições dos mesmos 12 casos sintéticos. O intervalo bootstrap [0,0] do relatório automático resulta do teto de acertos e não demonstra equivalência fora da amostra. Uma confirmação deve usar novas tarefas reais, critérios de ganho mínimo e custo tolerável definidos antes, mais repetições e medição de retrabalho/reincidência. Separar Rules de Actions ajudaria a localizar benefícios; este estudo avaliou o bloco inteiro.", "",
          "Reprodução offline: `python3 agentsmd-detfirst-opencode/results/pilot-r2/analyze.py`. Dados completos: [analysis.json](analysis.json) e [metrics.tsv](metrics.tsv). A análise não chama o modelo nem modifica os trials."]
(OUT / "analysis.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"outcomes": analysis["outcomes"], "treatment_difference_percent": deltas,
                  "cross_runtime_difference_percent": combined["opencode_difference_percent"],
                  "exports_checked": export_count}, ensure_ascii=False))
