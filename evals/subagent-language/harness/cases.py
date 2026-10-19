"""Synthetic Portuguese tasks. Expected answers stay outside the agent workspace."""
import json

COMMON = """Trabalhe somente com os arquivos desta pasta. Use exatamente dois subagentes
diretos, com fork_turns="none", sem outros descendentes. Escolha a divisão de trabalho,
envie a cada um o contexto necessário e aguarde a conclusão de ambos. Use o mesmo
modelo e esforço desta sessão. Os subagentes devem retornar suas análises por mensagem;
somente você deve escrever os arquivos finais. Pode haver perguntas e correções entre vocês.
Entregue answer.json conforme o contrato solicitado e report.md em português, explicando
as decisões, evidências e ressalvas. Responda ao usuário em português. Preserve os
arquivos de entrada. Use apenas ferramentas locais; a tarefa dispensa acesso à internet.
"""

CASES = {
    "incidente": {
        "prompt": """Diagnostique o incidente cruzando operacao.md e mudanca.md. Identifique
a causa mais sustentada, o componente a reverter, as filas que exigem reprocessamento e
se há evidência de perda definitiva. Em answer.json use exatamente as chaves causa,
reverter, reprocessar e perda_confirmada. causa deve ser um dos códigos C1, C2, C3;
reverter deve ser o nome do componente; reprocessar é uma lista ordenada de IDs de filas;
perda_confirmada é booleano. Explique também por que as alternativas são menos sustentadas.""",
        "files": {
            "operacao.md": """# Operação de 7 de outubro
O painel agrega todas as filas e arredonda as taxas de erro. O início do alerta,
às 14:08 UTC, não é necessariamente o início do defeito. Todos os horários abaixo
estão em UTC. O banco foi verificado às 14:12: conexões disponíveis, sem aumento
de latência nem falhas nas consultas de leitura e escrita. Às 14:04 houve uma
falha de DNS em uma sonda de laboratório, que não compartilha o resolvedor de produção.

| Fila | Consumidor | Mensagens afetadas | Evidência |
|---|---|---|---|
| Q1 | recibos | 42 | rejeições locais com campo customer_id ausente desde 14:06 |
| Q2 | recibos | 17 | mesmo erro; mensagens retidas na fila de falhas |
| Q3 | notificacoes | 0 | consumo e confirmações normais durante toda a janela |
| Q4 | recibos | 0 | vazia desde 13:50; nenhum evento durante a janela |

O produtor continuou publicando. As 59 mensagens rejeitadas estão íntegras na
fila de falhas, com IDs originais e payload disponível. Não se verificou ainda
o resultado de um reprocessamento completo. Contagem de tentativas não deve
ser confundida com quantidade de mensagens. Os recibos usam uma chave de
idempotência por ID de mensagem; o operador deve preservá-la ao reprocessar.
""",
            "mudanca.md": """# Histórico e hipóteses
Às 13:40 houve uma alteração visual no painel, sem mudança de agregação.
Às 14:05 o consumidor recibos passou da versão 7 para a 8. A versão 8 passou
a exigir customer_id, enquanto o contrato vigente do produtor publica cliente_id.
Não houve migração coordenada do produtor. Às 14:16 uma instância de recibos
foi revertida para a versão 7: dez mensagens de teste com o formato vigente
foram aceitas, usando o mesmo banco e a mesma rede. As outras instâncias ainda
estão na versão 8. O consumidor notificacoes não foi atualizado.

O catálogo de hipóteses é: C1 = esgotamento de conexões do banco; C2 = quebra
de compatibilidade no consumidor recibos; C3 = indisponibilidade de DNS em produção.
Uma reversão do produtor exigiria coordenar clientes que continuam operando
normalmente. O procedimento operacional permite reverter recibos para 7 e
validar uma amostra antes de reprocessar as filas efetivamente afetadas.
Não classifique retenção temporária como perda definitiva. Ausência de
evidência de perda não é garantia de recuperação integral sem validação.
""",
        },
        "expected": {"causa": "C2", "reverter": "recibos", "reprocessar": ["Q1", "Q2"], "perda_confirmada": False},
        "rubric": "Distinguir retenção de perda, rejeitar C1/C3 com evidências, propor reversão e validação antes do reprocessamento com idempotência.",
    },
    "fornecedor": {
        "prompt": """Escolha o fornecedor elegível de menor custo em 12 meses, cruzando
requisitos.md e propostas.md. Em answer.json use exatamente escolhido, elegiveis,
custo_12_meses_centavos e excluidos. elegiveis é uma lista de nomes em ordem alfabética;
excluidos mapeia cada nome inelegível para a lista ordenada dos códigos de requisitos
violados. Explique os cálculos, os motivos de exclusão e o desempate se necessário.""",
        "files": {
            "requisitos.md": """# Compra de um serviço de processamento
O horizonte de comparação é de 12 meses com 80.000 eventos por mês. A implantação
acontece uma única vez. Compare todos os valores em reais, sem atualização monetária.
Não há desconto por pagamento antecipado. Franquia não utilizada não acumula.
Cada evento excedente custa o valor indicado, inclusive quando o excesso não
completa um lote. O orçamento desejável de R$ 32.000 não é eliminatório.

Requisitos obrigatórios: R1 = dados primários e backups armazenados no Brasil;
R2 = exportação completa em formato aberto, incluída no preço e disponível em
até 48 horas; R3 = início de operação em até 20 dias corridos, contados da assinatura.
Atender exatamente o limite atende o requisito. Uma promessa de funcionalidade
futura não vale como atendimento atual. Condições específicas assinadas prevalecem
sobre o texto comercial genérico. Escolha o menor custo total entre os elegíveis.
Em empate, prefira menor prazo de implantação e, persistindo, ordem alfabética.
""",
            "propostas.md": """# Propostas assinadas
Alfa: mensalidade R$ 2.000; franquia de 60.000 eventos; excedente R$ 0,02 por
evento; implantação R$ 4.000; prazo 20 dias. Dados e backups no Brasil.
Exportação JSON integral incluída, em 48 horas.

Beta: mensalidade R$ 1.600; franquia de 100.000; implantação R$ 2.000;
prazo 10 dias. Dados primários no Brasil, backups no Chile. Exportação CSV
integral incluída em 24 horas. A proposta não prevê mudança dos backups.

Gama: mensalidade R$ 2.400; franquia de 80.000; implantação R$ 3.000;
prazo 18 dias. Dados e backups no Brasil. Exportação JSON integral incluída
em 36 horas. Eventos acima da franquia custam R$ 0,04 cada.

Delta: mensalidade R$ 1.800; franquia de 80.000; implantação R$ 1.000;
prazo 15 dias. Dados e backups no Brasil. A página comercial anuncia
"exportação fácil", mas a condição assinada entrega somente PDF e prevê
exportação JSON em uma versão futura, sem data contratual.

Épsilon: mensalidade R$ 2.400; franquia de 80.000; implantação R$ 3.000;
prazo 19 dias. Dados e backups no Brasil. Exportação CSV integral incluída
em 24 horas. Os valores de todas as propostas já incluem impostos.
""",
        },
        "expected": {"escolhido": "Gama", "elegiveis": ["Alfa", "Épsilon", "Gama"], "custo_12_meses_centavos": 3180000, "excluidos": {"Beta": ["R1"], "Delta": ["R2"]}},
        "rubric": "Calcular Alfa=32.800 e Gama/Épsilon=31.800 reais; desempatar pelo prazo; explicar backups e exportação, sem transformar orçamento desejável em veto.",
    },
    "acessos": {
        "prompt": """Aplique a política aos pedidos. Em answer.json use exatamente permitidos
e negados, ambas listas de IDs em ordem crescente. No report.md explique cada decisão
negada e os casos de exceção ou fronteira. Não invente aprovações ausentes.""",
        "files": {
            "politica.md": """# Política do projeto P, versão vigente
Um usuário ativo pode ler um recurso de seu próprio projeto. Suspensão bloqueia
qualquer ação, inclusive acesso emergencial. Usuários de outro projeto são negados.
Escrita exige papel editor ou admin e recurso desbloqueado. Administrador não
ignora bloqueio de escrita. Leitura de recurso bloqueado continua permitida.
Exportação exige papel admin e aprovação do titular dos dados ainda válida.
No instante exato do vencimento, a aprovação já expirou. Uma aprovação de exportação
não concede escrita nem acesso a outro projeto. Ausência de aprovação equivale a não.

Exceção E1: leitura emergencial pode ser concedida a usuário ativo do papel suporte,
mesmo de outro projeto, se houver chamado de emergência aberto associado ao recurso.
Essa exceção só cobre leitura. Estar no suporte não dá escrita nem exportação.
Avalie cada pedido isoladamente às 12:00:00 UTC de 10/10/2026. A lista de usuários
é um retrato válido para esse instante; não extrapole uma decisão para outro horário.
""",
            "pedidos.md": """# Pedidos para recursos do projeto P
A01: ativo, leitor, projeto P, ler recurso desbloqueado.
A02: ativo, editor, projeto P, escrever recurso bloqueado.
A03: ativo, admin, projeto P, escrever recurso bloqueado.
A04: ativo, admin, projeto P, exportar; aprovação vence 10/10/2026 12:00:00 UTC.
A05: ativo, admin, projeto P, exportar; aprovação vence 10/10/2026 12:00:01 UTC.
A06: ativo, suporte, projeto X, ler; chamado emergencial aberto para esse recurso.
A07: suspenso, suporte, projeto X, ler; chamado emergencial aberto para esse recurso.
A08: ativo, suporte, projeto X, exportar; chamado emergencial aberto para esse recurso.
A09: ativo, leitor, projeto P, ler recurso bloqueado.
A10: ativo, editor, projeto P, escrever recurso desbloqueado.
A11: ativo, admin, projeto X, ler recurso desbloqueado; sem chamado emergencial.
A12: ativo, admin, projeto P, exportar; sem aprovação do titular.
A13: ativo, suporte, projeto X, ler; chamado emergencial encerrado para esse recurso.
A14: ativo, editor, projeto P, exportar; aprovação vence amanhã.
A15: ativo, suporte, projeto P, ler recurso desbloqueado; sem chamado emergencial.
A16: ativo, leitor, projeto P, escrever recurso desbloqueado; aprovação de exportação válida.
""",
        },
        "expected": {"permitidos": ["A01", "A05", "A06", "A09", "A10", "A15"], "negados": ["A02", "A03", "A04", "A07", "A08", "A11", "A12", "A13", "A14", "A16"]},
        "rubric": "Justificar cada negativa; observar vencimento exclusivo, suspensão, bloqueio de escrita do admin e escopo somente leitura da exceção.",
    },
    "conciliacao": {
        "prompt": """Concilie as vendas conforme regras.md e eventos.json. Em answer.json
use exatamente pedidos_incluidos (lista ordenada), receita_liquida_centavos (inteiro)
e por_canal_centavos (objeto com loja e web). Explique exclusões, duplicatas e estornos.""",
        "files": {
            "regras.md": """# Fechamento de 10 de outubro
Incluir pedidos BRL pagos cujo instante de pagamento esteja em [2026-10-10T00:00:00Z,
2026-10-11T00:00:00Z). Datas já estão em UTC. Não usar a criação do pedido para
decidir a janela. O arquivo contém eventos repetidos por retry: deduplicar pelo
event_id antes de calcular qualquer valor. IDs diferentes representam eventos distintos.

Subtrair de cada pedido incluído os estornos confirmados ocorridos estritamente
antes de 2026-10-11T00:00:00Z, inclusive parciais. Estornos pendentes não entram.
Estorno no limite superior fica para o próximo fechamento. Pedido integralmente
estornado permanece na lista de incluídos, com líquido zero. Um estorno de pedido
fora da janela não entra neste relatório. Não converter outras moedas. Valores
são inteiros em centavos. Use o canal do pagamento; não some o valor de criação.
O relatório é por coorte de pagamentos, não um fluxo de caixa de todos os eventos do dia.
""",
            "eventos.json": json.dumps([
                {"event_id": "E1", "pedido": "P1", "tipo": "pago", "moeda": "BRL", "valor": 10000, "canal": "web", "em": "2026-10-10T00:00:00Z"},
                {"event_id": "E1", "pedido": "P1", "tipo": "pago", "moeda": "BRL", "valor": 10000, "canal": "web", "em": "2026-10-10T00:00:00Z"},
                {"event_id": "E2", "pedido": "P2", "tipo": "pago", "moeda": "BRL", "valor": 25000, "canal": "loja", "em": "2026-10-10T09:00:00Z"},
                {"event_id": "E3", "pedido": "P3", "tipo": "pago", "moeda": "BRL", "valor": 5000, "canal": "web", "em": "2026-10-10T23:59:59Z"},
                {"event_id": "E4", "pedido": "P4", "tipo": "pago", "moeda": "BRL", "valor": 99999, "canal": "web", "em": "2026-10-11T00:00:00Z"},
                {"event_id": "E5", "pedido": "P5", "tipo": "pago", "moeda": "USD", "valor": 8000, "canal": "web", "em": "2026-10-10T10:00:00Z"},
                {"event_id": "E6", "pedido": "P6", "tipo": "criado", "moeda": "BRL", "valor": 7000, "canal": "loja", "em": "2026-10-10T11:00:00Z"},
                {"event_id": "E7", "pedido": "P7", "tipo": "pago", "moeda": "BRL", "valor": 12000, "canal": "loja", "em": "2026-10-09T23:59:59Z"},
                {"event_id": "E8", "pedido": "P8", "tipo": "pago", "moeda": "BRL", "valor": 3000, "canal": "loja", "em": "2026-10-10T12:00:00Z"},
                {"event_id": "R1", "pedido": "P1", "tipo": "estorno_confirmado", "valor": 2000, "em": "2026-10-10T16:00:00Z"},
                {"event_id": "R1", "pedido": "P1", "tipo": "estorno_confirmado", "valor": 2000, "em": "2026-10-10T16:00:00Z"},
                {"event_id": "R2", "pedido": "P2", "tipo": "estorno_pendente", "valor": 4000, "em": "2026-10-10T17:00:00Z"},
                {"event_id": "R3", "pedido": "P3", "tipo": "estorno_confirmado", "valor": 5000, "em": "2026-10-11T00:00:00Z"},
                {"event_id": "R4", "pedido": "P7", "tipo": "estorno_confirmado", "valor": 12000, "em": "2026-10-10T18:00:00Z"},
                {"event_id": "R5", "pedido": "P8", "tipo": "estorno_confirmado", "valor": 3000, "em": "2026-10-10T20:00:00Z"},
            ], ensure_ascii=False, indent=2),
        },
        "expected": {"pedidos_incluidos": ["P1", "P2", "P3", "P8"], "receita_liquida_centavos": 38000, "por_canal_centavos": {"loja": 25000, "web": 13000}},
        "rubric": "Explicar deduplicação, janela semiaberta, P8 com zero, R2 pendente, R3 no limite e R4 fora da coorte.",
    },
}


def build(case, work):
    for name, content in CASES[case]["files"].items():
        (work / name).write_text(content, encoding="utf-8")
    return COMMON + "\n" + CASES[case]["prompt"]


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    return actual == expected


def grade(case, work):
    try:
        actual = json.loads((work / "answer.json").read_text())
    except (OSError, ValueError):
        actual = None
    inputs_intact = all((work / n).is_file() and (work / n).read_text() == c
                        for n, c in CASES[case]["files"].items())
    report = work / "report.md"
    checks = {"answer_exact": exact(actual, CASES[case]["expected"]),
              "inputs_intact": inputs_intact,
              "report_present": report.is_file() and bool(report.read_text().strip())}
    return {"checks": checks, "automatic_pass": all(checks.values()), "human_review": "pending"}
