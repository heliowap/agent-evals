# Conciliação de vendas — fechamento de 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**: **25.000 centavos em loja** e **13.000 centavos em web**. Os pedidos incluídos são **P1, P2, P3 e P8**.

## Critérios e decisões

Foram usados somente `regras.md` e `eventos.json` desta pasta. A janela de pagamentos em BRL é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: inclui o instante inicial e exclui o final. Todos os instantes são UTC, sem ajuste de fuso. A inclusão depende do pagamento, não da criação do pedido.

Os eventos foram deduplicados por `event_id` antes dos cálculos. Para cada pedido incluído, foram subtraídos os estornos confirmados anteriores a `2026-10-11T00:00:00Z`, usando o canal do pagamento. A regra dos estornos impõe somente esse limite superior, sem exigir que ocorram dentro da janela de pagamentos. Este relatório acompanha a coorte de pagamentos, não todos os movimentos de caixa do dia.

O contrato exige uma lista ordenada, mas não define o critério. Foi adotada a ordem crescente dos IDs dos pedidos: `P1`, `P2`, `P3`, `P8`. Todos os valores do JSON são inteiros em centavos; nenhuma moeda foi convertida.

## Pedidos incluídos

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto (centavos) | Estornos aplicados (centavos) | Líquido (centavos) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 está exatamente no limite inferior e entra. P8 foi integralmente estornado, mas permanece na lista de incluídos com líquido zero, conforme a regra.

## Exclusões de pedidos

| Pedido | Evento | Evidência | Motivo da exclusão |
| --- | --- | --- | --- |
| P4 | E4 | Pagamento BRL em 2026-10-11T00:00:00Z | Está exatamente no limite superior, que é excluído. |
| P5 | E5 | Pagamento USD em 2026-10-10T10:00:00Z | A coorte aceita somente BRL; não há conversão. |
| P6 | E6 | Evento `criado` em 2026-10-10T11:00:00Z, valor 7000 | Não há pagamento registrado; o valor de criação não é receita. |
| P7 | E7 | Pagamento BRL em 2026-10-09T23:59:59Z | O pagamento ocorreu antes do início da janela. |

## Duplicatas

Há 15 registros e 13 eventos distintos. `E1` aparece duas vezes com conteúdo idêntico: uma repetição foi descartada, e o pagamento de P1 conta 10000 centavos uma única vez. `R1` também aparece duas vezes com conteúdo idêntico: uma repetição foi descartada, e o estorno de P1 desconta 2000 centavos uma única vez. Os demais IDs são distintos e foram tratados como eventos separados.

## Estornos

| Evento | Pedido | Tipo | Instante (UTC) | Valor (centavos) | Tratamento |
| --- | --- | --- | --- | ---: | --- |
| R1 | P1 | `estorno_confirmado` | 2026-10-10T16:00:00Z | 2000 | Aplicado uma vez; estorno parcial anterior ao corte. |
| R2 | P2 | `estorno_pendente` | 2026-10-10T17:00:00Z | 4000 | Excluído por estar pendente. |
| R3 | P3 | `estorno_confirmado` | 2026-10-11T00:00:00Z | 5000 | Excluído deste fechamento; está no limite superior e fica para o próximo, conforme a regra. |
| R4 | P7 | `estorno_confirmado` | 2026-10-10T18:00:00Z | 12000 | Excluído porque P7 não pertence à coorte, mesmo com estorno ocorrido no dia. |
| R5 | P8 | `estorno_confirmado` | 2026-10-10T20:00:00Z | 3000 | Aplicado; estorno integral que deixa P8 com líquido zero. |

## Totais por canal e validação

| Canal do pagamento | Bruto (centavos) | Estornos aplicados (centavos) | Líquido (centavos) |
| --- | ---: | ---: | ---: |
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

A conciliação fecha em `43000 - 5000 = 38000` e `25000 + 13000 = 38000`. Exatamente dois subagentes diretos, sem descendentes, analisaram os arquivos e retornaram suas conclusões por mensagem; ambos concluíram antes da escrita dos arquivos finais. Suas análises concordaram com o cálculo local independente. Somente o agente principal escreveu `answer.json` e este relatório.

`answer.json` contém exatamente as três chaves solicitadas, com os tipos e canais exigidos. Os arquivos de entrada foram preservados, com verificação de SHA-256 antes e depois da geração dos resultados.

## Ressalvas

O fechamento considera exclusivamente os eventos fornecidos e as regras locais. Não houve consulta externa nem eventos duplicados conflitantes. A única escolha não explicitada no contrato foi o critério de ordenação dos pedidos, documentado acima; não há outra ambiguidade identificada que afete os valores.
