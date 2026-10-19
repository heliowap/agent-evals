"""Validate blind decisions, then join model identities and report separate metrics."""

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from benchmark import ROOT, atomic_new, frozen_manifest, openrouter_spend, pending_cells


CATEGORIES = {"valid_extra", "refuted", "inconclusive", "opinion_style"}


def freeze_blind_grades(root):
    packet_path = root / "blind-answers.json"
    packet = json.loads(packet_path.read_text())
    if packet["partial"]:
        raise ValueError("cannot seal a partial blind packet")
    groups = {(item["case"], item["axis"]) for item in packet["answers"]}
    hashes = {}
    group_hashes = {}
    covered = set()
    for case, axis in sorted(groups):
        name = f"{case}-{axis}.json"
        group = json.loads((root / "blind-groups" / name).read_text())
        expected = [item for item in packet["answers"] if (item["case"], item["axis"]) == (case, axis)]
        if group != expected:
            raise ValueError(f"blind group differs from full packet: {name}")
        grade_path = root / "adjudication-groups" / name
        decisions = validate_group(group, json.loads(grade_path.read_text()))
        if covered & set(decisions):
            raise ValueError("duplicate blind decision across groups")
        covered.update(decisions)
        hashes[name] = hashlib.sha256(grade_path.read_bytes()).hexdigest()
        group_hashes[name] = hashlib.sha256((root / "blind-groups" / name).read_bytes()).hexdigest()
    if covered != {item["blind_id"] for item in packet["answers"]}:
        raise ValueError("missing blind decisions")
    seal = {"blind_answers_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
            "decision_sha256": hashes, "group_sha256": group_hashes}
    atomic_new(root / "blind-seal.json", seal)
    return seal


def verify_blind_seal(root):
    seal = json.loads((root / "blind-seal.json").read_text())
    if (seal["blind_answers_sha256"] != hashlib.sha256((root / "blind-answers.json").read_bytes()).hexdigest() or
            seal["decision_sha256"] != {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "adjudication-groups").glob("*.json")} or
            seal["group_sha256"] != {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "blind-groups").glob("*.json")}):
        raise ValueError("blind seal differs from packet or decisions")
    return seal


def validate_group(packets, document):
    if not packets or (document.get("case"), document.get("axis")) != (packets[0]["case"], packets[0]["axis"]):
        raise ValueError("group case/axis mismatch")
    expected = {packet["blind_id"]: packet["answer"] for packet in packets}
    decisions = document.get("decisions", [])
    ids = [item.get("blind_id") for item in decisions]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate blind decision")
    if set(ids) != set(expected):
        raise ValueError(f"missing or unexpected blind decisions: {set(expected) ^ set(ids)}")
    for item in decisions:
        answer = expected[item["blind_id"]]
        if not isinstance(item.get("target_hit"), bool) or not item.get("target_reason", "").strip():
            raise ValueError(f"invalid target decision: {item['blind_id']}")
        quote = item.get("target_quote")
        if item["target_hit"] and (not isinstance(quote, str) or not quote.strip() or quote not in answer):
            raise ValueError(f"target quote not in answer: {item['blind_id']}")
        if not isinstance(item.get("additional_claims"), list):
            raise ValueError(f"missing additional claims list: {item['blind_id']}")
        quotes = [claim.get("quote") for claim in item["additional_claims"]]
        if len(quotes) != len(set(quotes)):
            raise ValueError(f"duplicate additional claim: {item['blind_id']}")
        for claim in item["additional_claims"]:
            if claim.get("category") not in CATEGORIES or not claim.get("quote") or claim["quote"] not in answer:
                raise ValueError(f"unsupported quote/category: {item['blind_id']}")
            if claim["category"] in ("valid_extra", "refuted") and not claim.get("evidence", "").strip():
                raise ValueError(f"missing evidence for factual classification: {item['blind_id']}")
    return {item["blind_id"]: item for item in decisions}


def join_validated(decisions, mapping, cells, results, packets):
    cell_by_id = {cell["id"]: cell for cell in cells}
    packet_by_id = {packet["blind_id"]: packet for packet in packets}
    if (len(packet_by_id) != len(packets) or set(decisions) != set(mapping) or
            set(decisions) != set(packet_by_id) or set(mapping.values()) != set(cell_by_id) or
            set(results) != set(cell_by_id)):
        raise ValueError("missing or unexpected identity/result mapping")
    joined = []
    for blind_id, decision in decisions.items():
        cell_id = mapping[blind_id]
        cell, result = cell_by_id[cell_id], results[cell_id]
        if (result.get("model"), result.get("case"), result.get("axis"), result.get("repeat")) != (
                cell["model"], cell["case"], cell["axis"], cell["repeat"]):
            raise ValueError(f"result/cell mismatch: {cell_id}")
        if (packet_by_id[blind_id]["answer"], packet_by_id[blind_id]["case"], packet_by_id[blind_id]["axis"]) != (
                result.get("answer"), cell["case"], cell["axis"]):
            raise ValueError(f"blind packet answer/axis differs from result: {blind_id}")
        joined.append({**decision, "cell_id": cell_id, "model": cell["model"],
                       "case": cell["case"], "axis": cell["axis"], "repeat": cell["repeat"],
                       "session": result["session"], "elapsed_seconds": result["elapsed_seconds"],
                       "reported_cost_usd": result["cost_usd"]})
    return joined


def summarize_models(joined):
    groups = defaultdict(list)
    for item in joined:
        groups[item["model"]].append(item)
    output = {}
    for model, group in groups.items():
        durations = [item["elapsed_seconds"] for item in group]
        quartiles = statistics.quantiles(durations, n=4, method="inclusive") if len(durations) > 1 else durations * 3
        claims = [claim["category"] for item in group for claim in item["additional_claims"]]
        output[model] = {
            "n": len(group),
            "standards_hits": sum(item["target_hit"] for item in group if item["axis"] == "standards"),
            "spec_hits": sum(item["target_hit"] for item in group if item["axis"] == "spec"),
            "refuted_claims": claims.count("refuted"),
            "refuted_answers": sum(any(c["category"] == "refuted" for c in item["additional_claims"])
                                   for item in group),
            "valid_extras": claims.count("valid_extra"),
            "inconclusive": claims.count("inconclusive"),
            "opinion_style": claims.count("opinion_style"),
            "median_seconds": statistics.median(durations),
            "iqr_seconds": [quartiles[0], quartiles[2]],
            "reported_valid_cost_usd": sum(item["reported_cost_usd"] or 0 for item in group),
        }
    return output


def word_limit_stats(results):
    counts = {"breaches": 0, "over_400": 0, "maximum": 0, "by_model": {}}
    for result in results:
        length = len(result["answer"].split())
        counts["maximum"] = max(counts["maximum"], length)
        if length >= 400:
            counts["breaches"] += 1
            model = result["model"]
            counts["by_model"][model] = counts["by_model"].get(model, 0) + 1
        if length > 400:
            counts["over_400"] += 1
    return counts


def render_report(joined, models, manifest, all_openrouter_cost, attempts, word_stats):
    def pt(value, digits):
        return f"{value:.{digits}f}".replace(".", ",")

    case_axis = defaultdict(list)
    for item in joined:
        case_axis[(item["case"], item["axis"])].append(item)
    lines = [
        "# Code-review benchmark — rodada 2 (comparação exploratória)",
        "",
        "**300/300 revisões válidas**: 25 configurações × 3 casos × 2 eixos × 2 execuções independentes. "
        "Uma sessão válida não torna todos os alvos comparáveis: o caso Axios / Standards omitiu do prompt "
        "a condição necessária para demonstrar a falha do teste. Os números abaixo preservam a adjudicação cega, "
        "mas **não sustentam uma nota geral de seis alvos**. Veja a [revisão metodológica](methodology-review.md).",
        "",
        "## Cobertura por caso e eixo",
        "",
        "| Caso | Eixo | Alvo encontrado (bruto) | Alegações refutadas (brutas) | Menções extras verificadas | Não verificáveis |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for (case, axis), items in sorted(case_axis.items()):
        categories = [c["category"] for item in items for c in item["additional_claims"]]
        lines.append(f"| {case} | {axis} | {sum(i['target_hit'] for i in items)}/{len(items)} | "
                     f"{categories.count('refuted')} | {categories.count('valid_extra')} | "
                     f"{categories.count('inconclusive')} |")
    lines += ["", "**Atenção:** Axios / Standards (10/50) não é demonstrável só com o material recebido; "
              "Requests / Spec (47/50) diz respeito a uma chamada direta do helper, não a uma falha demonstrada de uma requisição normal.",
              "", "## Configurações (contagens brutas; sem nota geral nem ranking)", "",
              "| Configuração | Standards / 6* | Spec / 6† | Refutadas‡ | Extras§ | Inconclusivas | Mediana s [IQR] | Custo válido informado US$ |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for model in manifest["models"]:
        item = models[model]
        lo, hi = item["iqr_seconds"]
        lines.append(f"| `{model}` | {item['standards_hits']}/6 | {item['spec_hits']}/6 | "
                     f"{item['refuted_claims']} | {item['valid_extras']} | {item['inconclusive']} | "
                     f"{pt(item['median_seconds'], 1)} [{pt(lo, 1)}–{pt(hi, 1)}] | "
                     f"{pt(item['reported_valid_cost_usd'], 5)} |")
    cpa_long = sum(n for model, n in word_stats["by_model"].items() if model.startswith("cli_proxy/cpa-claude-opus-5-5#"))
    lines += ["", "- `*` Um dos três alvos de Standards, Axios, não é demonstrável pelo prompt: as contagens por modelo são históricas, não um escore comparável.",
              "- `†` Requests / Spec registra o comportamento condicional de `build_digest_header()`, sem prova de regressão no fluxo normal.",
              "- `‡` O total bruto inclui a alegação de `b0026`, cuja refutação depende de código omitido do prompt; não tratá-la como falso positivo confirmado.",
              "- `§` As menções extras incluem alvos do outro eixo e observações factuais; não equivalem a defeitos inéditos.",
              "", "## Limites e auditoria", "",
              "- **0 células faltantes**; as 25 configurações têm dois resultados por caso/eixo, sem troca de rota.",
              f"- O prompt pediu menos de 400 palavras; pela contagem por espaços, "
              f"**{word_stats['breaches']}/300 respostas têm 400 ou mais** ({word_stats['over_400']} passam de 400; "
              f"máximo {word_stats['maximum']}). {cpa_long}/36 respostas CPA Opus excedem esse limite. "
              "A execução não as excluiu; a extensão desigual também afeta a oportunidade de encontrar extras.",
              f"- **{len(attempts)} tentativas** arquivadas, inclusive {sum(a['status'] == 'excluded' for a in attempts)} excluídas. "
              "Uma tentativa MiMo sem resposta final teve o custo conciliado, mas não virou revisão válida.",
              f"- **US$ {pt(all_openrouter_cost, 5)} informados pelo OpenRouter** em todas as tentativas dessa rota, "
              "inclusive excluídas; o valor não é o total da conta nem um limite de cobrança imposto pelo provedor.",
              "- US$ 0 informado nas sessões OAuth e `cli_proxy` **não demonstra custo real nulo**. "
              "A rota Fast é a variante solicitada; não há prova independente de aceleração do serviço.",
              "- Um alvo exige local, mecanismo e consequência no eixo correto. Extras foram classificados à parte; "
              "hipóteses não verificáveis não foram contadas como falsas, ressalvada a classificação contestada de `b0026`.",
              "- Uma passagem cega por resposta, sem segundo adjudicador independente. Consulte "
              "[gabarito](grading-rubric.md), [selo anterior à identificação](blind-seal.json), "
              "[decisões](adjudication.json) e [mapa](blind-map.json). "
              "As [300 exportações sanitizadas](session-evidence.json) permitem verificar novamente prompt, "
              "modelo/variante, agente, término, ausência de partes de ferramentas, resposta, tokens e custo informado; "
              "o raciocínio e o fluxo de eventos original do CLI não foram arquivados.",
              "- São três PRs e duas repetições por célula; não compare numericamente com a rodada Click anterior. "
              "Esta amostra não mede o efeito causal dos novos prompts nem a execução integral da skill.",
              ""]
    return "\n".join(lines)


def main():
    root = ROOT
    _, manifest = frozen_manifest(root)
    if pending_cells(manifest, root):
        raise ValueError("refuse partial comparison")
    packet = json.loads((root / "blind-answers.json").read_text())
    if packet["partial"]:
        raise ValueError("blind packet is partial")
    seal = verify_blind_seal(root)  # Check judgments were frozen before reading identities.
    decisions = {}
    for path in sorted((root / "blind-groups").glob("*.json")):
        group = json.loads(path.read_text())
        graded = json.loads((root / "adjudication-groups" / path.name).read_text())
        overlap = set(decisions) & {item["blind_id"] for item in group}
        if overlap:
            raise ValueError(f"duplicate blind group: {overlap}")
        decisions.update(validate_group(group, graded))
    if len(decisions) != len(manifest["cells"]):
        raise ValueError("missing blinded decisions")
    mapping = json.loads((root / "blind-map.json").read_text())
    results = {path.stem: json.loads(path.read_text()) for path in (root / "results").glob("*.json")}
    joined = join_validated(decisions, mapping, manifest["cells"], results, packet["answers"])
    models = summarize_models(joined)
    if any(models[model]["n"] != 12 for model in manifest["models"]):
        raise ValueError("not every configuration has 12 graded answers")
    attempts = [json.loads(path.read_text()) for path in (root / "attempts").glob("*.json")]
    adjudication = {"manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
                    "blind_map_sha256": hashlib.sha256((root / "blind-map.json").read_bytes()).hexdigest(),
                    "blind_seal_sha256": hashlib.sha256((root / "blind-seal.json").read_bytes()).hexdigest(),
                    "second_independent_adjudicator": False, "decisions": joined}
    report = render_report(joined, models, manifest, openrouter_spend(root), attempts,
                           word_limit_stats(results.values()))
    atomic_new(root / "adjudication.json", adjudication)
    with (root / "comparison.md").open("x") as file:
        file.write(report)
    print(f"Graded {len(joined)} blind responses; wrote adjudication.json and comparison.md")


if __name__ == "__main__":
    main()
