"""Reproduce the completed pilot analysis offline without changing trial evidence."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from cases import snapshot
from codex_runtime import normalized_context


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values):
    return {"sum": sum(values), "mean": statistics.mean(values),
            "median": statistics.median(values), "min": min(values), "max": max(values)}


frozen = read(OUT / "freeze.json")
source_hashes = {**frozen["source_sha256"], "README.md": frozen["protocol_sha256"],
                 "REVIEW.md": frozen["review_rubric_sha256"]}
assert all(digest(OUT / "frozen-source" / name) == expected for name, expected in source_hashes.items())
assert all(digest(ROOT / "variants" / variant / "AGENTS.md") == expected
           for variant, expected in frozen["variant_sha256"].items())
assert digest(ROOT / "cases.py") == frozen["source_sha256"]["cases.py"]
assert digest(ROOT / "REVIEW.md") == frozen["review_rubric_sha256"]
assert read(OUT / "preflight.json")["equal_except_treatment"]

seal = read(OUT / "review-seal.json")
assert all(digest(OUT / "blind" / label / "review.json") == expected
           for label, expected in seal["review_sha256"].items())
key = read(OUT / "blind-key.json")
reviews = {key[label]: read(OUT / "blind" / label / "review.json")
           for label in seal["review_sha256"]}
usage_audits = {r["id"]: r for r in read(OUT / "usage-audit.json")["trials"]}
rows, nonzero, audits = [], [], {}
terminal_events = 0
error_events = 0
for planned in frozen["schedule"]:
    folder = OUT / planned["id"]
    row = read(folder / "result.json")
    assert all(row[k] == v for k, v in planned.items())
    assert row["status"] == "completed" and row["grade"]["automatic_pass"]
    assert row["model"] == "gpt-6.1-sol" and row["effort"] == "xhigh"
    audit = read(folder / "isolation.json")
    assert audit["agents_sha256"] == frozen["variant_sha256"][row["variant"]]
    assert not any("<skills_instructions>" in c.get("text", "")
                   for m in audit["context"] for c in m.get("content", []))
    audits[row["id"]] = audit
    turns = []
    for path in sorted(folder.glob("turn-*.jsonl")):
        events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        finished = [e for e in events if e["type"] == "turn.completed"]
        started = [e for e in events if e["type"] == "thread.started"]
        assert len(finished) == 1 and len(started) == 1
        assert started[0]["thread_id"] == row["session_id"]
        error_events += sum(e["type"] in {"error", "turn.failed"} for e in events)
        terminal_events += 1
        turns.append(finished[0]["usage"])
    assert turns == row["usage_raw"]
    assert len(turns) == len(frozen["cases"][row["case"]]["prompts"])
    usage = usage_audits[row["id"]]
    assert usage["model_effort"] == {"gpt-6.1-sol": "xhigh"}
    assert all(turns[-1][k] == usage["last_total_token_usage"][k] for k in turns[-1])
    previous = {k: 0 for k in usage["last_total_token_usage"]}
    for count in usage["token_count_records"]:
        total = count["total_token_usage"]
        if total == previous:
            continue
        assert all(total[k] - previous[k] == count["last_token_usage"][k] for k in previous)
        previous = total
    assert previous == usage["last_total_token_usage"]
    assert usage["last_total_token_usage"] == usage["summed_last_token_usage"]
    before, after = read(folder / "initial-files.json"), snapshot(folder / "work")
    obs = row["grade"]["observations"]
    assert sorted(after.keys() - before.keys()) == obs["added_files"]
    assert sorted(p for p in before.keys() & after.keys() if before[p] != after[p]) == obs["modified_files"]
    if row["case"] == "out_of_scope":
        assert before == after
    if row["case"] == "judgment":
        assert obs["modified_files"] == ["message.md"] and before.keys() == after.keys()
    if row["grade"]["needs_blind_review"]:
        assert reviews[row["id"]]["outcome_pass"] is True
    tools = read(folder / "tool-events.json")
    assert len(tools) == row["tool_calls"]
    for event in tools:
        if event["type"] == "command_execution" and event.get("exit_code") not in {0, None}:
            if row["case"] == "regression" and "unittest" in event["command"]:
                category = "expected_red_test"
            elif row["id"] == "trial-0012" and event["id"] == "item_7":
                category = "temporary_verification_bug_corrected_in_item_9"
            elif "git diff --no-index" in event["command"]:
                category = "expected_diff_found"
            else:
                assert "rg --files" in event["command"]
                category = "search_no_match"
            nonzero.append({"trial": row["id"], "item": event["id"], "category": category})
    row["historical_derived_usage"] = {k: row[k] for k in ("input_tokens", "cached_input_tokens", "output_tokens")}
    row.update({k: turns[-1][k] for k in row["historical_derived_usage"]})
    row["uncached_input_tokens"] = row["input_tokens"] - row["cached_input_tokens"]
    row["outcome_pass"] = True
    rows.append(row)

assert len(rows) == 72 and len(reviews) == 12 and error_events == 0
pairs = []
for first, second in zip(rows[::2], rows[1::2]):
    assert (first["case"], first["rep"]) == (second["case"], second["rep"])
    assert normalized_context(audits[first["id"]]) == normalized_context(audits[second["id"]])
    pair = {r["variant"]: r for r in [first, second]}
    pairs.append({"case": first["case"], "rep": first["rep"],
                  "wall_delta_s": pair["deterministic"]["wall_s"] - pair["empty"]["wall_s"]})

metrics = ["wall_s", "input_tokens", "cached_input_tokens", "uncached_input_tokens", "output_tokens", "tool_calls"]
summary = {v: {k: describe([r[k] for r in rows if r["variant"] == v]) for k in metrics}
           for v in ["empty", "deterministic"]}
case_summary = {case: {v: {k: describe([r[k] for r in rows if r["variant"] == v and r["case"] == case])
                         for k in metrics} for v in summary} for case in frozen["cases"]}
delta_pct = {k: 100 * (summary["deterministic"][k]["sum"] / summary["empty"][k]["sum"] - 1) for k in metrics}
analysis = {"model": frozen["model"], "effort": frozen["effort"], "trials": len(rows), "paired_trials": len(pairs),
            "outcomes": {v: {"pass": 36, "total": 36} for v in summary},
            "summary": summary, "case_summary": case_summary, "relative_difference_percent": delta_pct,
            "paired_wall_delta_s": describe([p["wall_delta_s"] for p in pairs]),
            "slower_treatment_pairs": sum(p["wall_delta_s"] > 0 for p in pairs), "pairs": pairs,
            "audit": {"terminal_events": terminal_events, "error_events": error_events,
                      "source_hashes_preserved": source_hashes, "paired_contexts_match": True,
                      "reviewed_controls": len(reviews), "nonzero_commands": nonzero,
                      "usage_semantics": "Last cumulative session counter, checked against all 72 rollouts"}}
(OUT / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
with (OUT / "corrected-metrics.tsv").open("w", newline="") as stream:
    fields = ["id", "case", "rep", "variant", "outcome_pass", *metrics]
    writer = csv.DictWriter(stream, fields, delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

lines = ["# Resultado do Codex: Deterministic first", "",
         "O trecho não demonstrou ganho de qualidade neste piloto. As duas condições entregaram 36/36 tarefas corretas. A condição com o trecho usou mais tempo e tokens de saída nesta amostra. O resultado continua inconclusivo para adoção no trabalho real.", "",
         "Codex CLI 0.162.1, gpt-6.1-sol, xhigh. Doze casos sintéticos, três repetições, 36 pares, 72 execuções em 10/10/2026. A condição vazia tinha zero bytes em AGENTS.md; a outra continha somente o trecho fornecido.", "",
         "| Medida | AGENTS vazio | Com o trecho | Diferença observada |",
         "|---|---:|---:|---:|", "| Entregas corretas | 36/36 | 36/36 | 0 ponto percentual |"]
for label, metric, stat, unit in [
    ("Tempo médio por tarefa", "wall_s", "mean", " s"),
    ("Tempo mediano por tarefa", "wall_s", "median", " s"),
    ("Tempo somado das invocações", "wall_s", "sum", " s"),
    ("Tokens de entrada, cache incluído", "input_tokens", "sum", ""),
    ("Entrada em cache, subconjunto", "cached_input_tokens", "sum", ""),
    ("Entrada sem cache", "uncached_input_tokens", "sum", ""),
    ("Tokens de saída", "output_tokens", "sum", ""),
    ("Eventos de ferramentas concluídos", "tool_calls", "sum", "")]:
    a, b = (summary[v][metric][stat] for v in summary)
    display = (lambda n: f"{n:.1f}{unit}") if metric == "wall_s" else (lambda n: f"{n:,}".replace(",", "."))
    lines.append(f"| {label} | {display(a)} | {display(b)} | {100 * (b / a - 1):+.1f}% |")
lines += ["", "A média de tempo cresceu 6,9 s por tarefa, totalizando cerca de 4 min 9 s adicionais. A tabela mede a espera pelas invocações do agente, incluindo inicialização e chamadas de ferramentas; exclui preparação e correção. O consumo de entrada sem cache foi menor com o trecho. Portanto, mais tokens de saída não basta para afirmar maior custo monetário. Nenhum custo em dinheiro foi estimado.", "",
          "## Qualidade e integridade", "",
          "As 72 execuções terminaram e passaram nos checks. Há 78 turnos concluídos, sem turn.failed ou eventos de reconexão. Os 12 controles com julgamento foram revisados conforme a rubrica anterior à execução. Os textos preservam todos os fatos; os reviews identificam o defeito e propõem testes sem editar os arquivos. A conferência dos arquivos confirmou o escopo nos 12 controles.", "",
          "As decisões estão em blind/*/review.json e seus hashes em [review-seal.json](review-seal.json), registrados antes da consulta à chave. A revisão foi feita pelo assistente, que já conhecia métricas agregadas. Alguns textos expõem IDs de trial e palavras sugestivas do tratamento. Isso limita o cegamento; não houve revisão humana independente.", "",
          "Os contextos auditados dos 36 pares coincidem exceto pelo tratamento e caminhos temporários. Os 72 rollouts registram o modelo e effort pedidos. A auditoria não equivale à captura do request HTTP ao provedor. As fontes e o protocolo originais foram preservados em [frozen-source/](frozen-source/) e conferidos contra freeze.json antes de qualquer correção posterior.", "",
          "Houve 21 comandos com retorno diferente de zero: 13 buscas sem correspondência, seis testes deliberadamente vermelhos antes da correção, um diff que encontrou alterações e um erro em uma asserção temporária de verificação. Esse último ocorreu no controle trial-0012 e foi corrigido em item_9; a entrega final passou. Nenhum desses trials foi excluído.", "",
          "## Tempo por caso", "",
          "Mediana e intervalo mínimo a máximo, em segundos. Três execuções por célula; todas corretas.", "",
          "| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |",
          "|---|---:|---:|"]
for case, groups in case_summary.items():
    cells = [f"{g['wall_s']['median']:.1f}; {g['wall_s']['min']:.1f} a {g['wall_s']['max']:.1f}" for g in groups.values()]
    lines.append(f"| {case} | {' | '.join(cells)} |")
lines += ["", "Os maiores acréscimos se concentram em convert e repeat. Nesses dois casos, cada uma das três execuções com o trecho foi mais lenta que todas as execuções correspondentes sem o trecho. Eles somam cerca de 205 s dos 249 s adicionais. Isso localiza o efeito observado, mas não isola latência do serviço, raciocínio e execução local como causas de tempo.", "",
          "## Comportamento observado", "",
          "| Comportamento | Vazio | Trecho | Evidência |",
          "|---|---|---|---|",
          "| Conversão por programa | 3/3, Python inline | 3/3, arquivo temporário e verificações | tool-events.json de trial-0015, 0016, 0067 a 0070 |",
          "| Renomeação em lote | 3/3, patch gerado pelo modelo | 3/3, substituição por script e verificação | tool-events.json de trial-0003, 0004, 0027 a 0030 |",
          "| Automação na segunda solicitação | 3/3, um loop inline processa B e C | 3/3, cria script temporário testado e reutiliza para B e C | turn-2.jsonl de trial-0019, 0020, 0035, 0036, 0051, 0052 |",
          "| Três comandos independentes sobrepostos | 3/3 | 3/3 | grade.observations.all_three_overlap e arquivos *-timing.json |",
          "| Proteção detecta reincidência em guardrail e regression | 6/6 | 6/6 | grade.checks nos resultados individuais |", "",
          "O trecho mudou o método em alguns casos. O controle já calculava por Python, automatizava os dois lotes seguintes e executava os checks independentes em paralelo. Em convert e repeat, criar o arquivo de script e verificá-lo acrescentou trabalho sem corrigir um erro que aparecesse no controle. Mais automação não recebeu pontos extras na nota de qualidade. Os eventos sustentam essa interpretação do método, mas não uma atribuição exata do tempo por componente.", "",
          "## Correção da contagem de tokens", "",
          "O runner original somava turn.completed.usage dos dois turnos de repeat. Os contadores são cumulativos por sessão. Essa soma duplicava o primeiro turno nos seis trials de repeat. A análise usa apenas usage_raw[-1] em cada trial. O último contador foi confrontado com total_token_usage e com os incrementos last_token_usage dos 72 rollouts, conforme [usage-audit.json](usage-audit.json). A auditoria conta incrementos somente quando o acumulado avança; trial-0062 contém uma notificação de contador repetida, sem novo consumo.", "",
          "Os result.json originais permanecem intactos. Para totais reconciliados, usar [corrected-metrics.tsv](corrected-metrics.tsv) ou [analysis.json](analysis.json). O runner foi corrigido para futuras execuções e um teste de regressão falhou antes da correção e passou depois; a suíte completa passou em 13/13 testes. Não houve nova chamada ao modelo para a análise.", "",
          "## O que este piloto permite concluir", "",
          "Não apareceu ganho de acerto, paralelismo ou prevenção de regressão nos casos testados. O controle atingiu o teto da régua; o bootstrap de [0,0] no relatório automático resulta desse teto e não prova equivalência fora da amostra. Três repetições dos mesmos 12 casos não são 36 tarefas independentes.", "",
          "O tempo agregado e a saída aumentaram nesta rodada. Não houve perfil de recursos ou controle do serviço remoto que permita identificar o limitante de desempenho. A ordem dos pares foi sorteada e a primeira condição ficou balanceada, 18 por lado. Ainda assim, os resultados não sustentam uma promessa geral de velocidade nem uma decisão definitiva de adoção.", "",
          "Uma rodada confirmatória deveria usar novas tarefas reais em que o controle ainda comete erros, medir explicitamente reincidência e retrabalho, definir antes o ganho mínimo útil e o custo tolerável, e ampliar as repetições. Se a intenção for reduzir o texto, comparar separadamente Rules e Actions em casos novos; este estudo testou o bloco inteiro.", "",
          "Reprodução offline: `python3 agentsmd-detfirst-isolated/results/pilot/analyze.py`. O script verifica a evidência preservada e regenera esta análise e a tabela de métricas sem alterar os trials."]
(OUT / "analysis.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"trials": len(rows), "outcomes": analysis["outcomes"], "relative_difference_percent": delta_pct,
                  "terminal_events": terminal_events, "nonzero_commands": len(nonzero)}, ensure_ascii=False))
