# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos de BRL (R$ 380,00)**, distribuída entre **loja: 25.000 centavos** e **web: 13.000 centavos**. Os pedidos incluídos, em ordem crescente de identificador, são **P1, P2, P3 e P8**.

## Critérios e evidências

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A janela de pagamentos é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início está incluído e o fim está excluído. As datas já estão em UTC e não foram convertidas. Somente pagamentos em BRL determinam a inclusão; criação de pedido não constitui receita. O canal utilizado é o do pagamento.

Antes de qualquer cálculo, os eventos foram deduplicados por `event_id`. As 15 ocorrências de entrada correspondem a 13 eventos distintos. `E1` aparece duas vezes com conteúdo idêntico: seu pagamento de 10.000 centavos foi contado uma única vez. `R1` também aparece duas vezes com conteúdo idêntico: seu estorno de 2.000 centavos foi subtraído uma única vez. Eventos com identificadores diferentes foram tratados como distintos.

## Pedidos incluídos

Todos os valores da tabela estão em centavos de BRL.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Valor pago | Estorno aplicado | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra por estar exatamente no limite inferior inclusivo. P8 foi integralmente estornado, mas permanece na lista de incluídos com líquido zero, conforme a regra explícita.

## Estornos

São descontados somente estornos confirmados de pedidos incluídos, ocorridos estritamente antes de `2026-10-11T00:00:00Z`. A regra não exige um limite inferior para a data do estorno.

| Evento | Pedido | Valor em centavos | Decisão e evidência |
|---|---|---:|---|
| R1 | P1 | 2000 | Aplicado uma vez: confirmado em 2026-10-10T16:00:00Z; estorno parcial. A repetição é um retry. |
| R2 | P2 | 4000 | Excluído: estorno pendente em 2026-10-10T17:00:00Z. |
| R3 | P3 | 5000 | Excluído deste fechamento: confirmado exatamente em 2026-10-11T00:00:00Z, no limite superior; fica para o próximo fechamento conforme as regras. |
| R4 | P7 | 12000 | Excluído: embora confirmado em 2026-10-10T18:00:00Z, refere-se a pedido cujo pagamento está fora da janela. |
| R5 | P8 | 3000 | Aplicado: confirmado em 2026-10-10T20:00:00Z; estorno integral. |

## Pedidos excluídos

| Pedido | Evento | Motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior excluído. |
| P5 | E5 | Pagamento em USD; a regra permite apenas BRL e proíbe conversão de outras moedas. |
| P6 | E6 | Há apenas um evento `criado`, sem pagamento. Seu valor de 7000 centavos não é somado. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, anterior ao limite inferior. Seu estorno R4 também não entra. |

## Totais por canal

Os estornos seguem o canal do pagamento do respectivo pedido.

| Canal | Pagamentos em centavos | Estornos aplicados em centavos | Receita líquida em centavos |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

## Validação e ressalvas

Dois subagentes diretos, sem descendentes, conferiram os arquivos locais: um analisou a elegibilidade dos pagamentos e o outro os estornos e os totais. Ambos retornaram análises concordantes, e o cálculo local independente confirmou os mesmos valores. Somente o agente principal escreveu `answer.json` e este relatório.

O resultado representa a coorte de pagamentos da janela definida, não o fluxo de caixa de todos os eventos do dia. Assim, o estorno de P7 não reduz este total, e o estorno de P3 no limite superior não foi antecipado. O cálculo usa inteiros em centavos e depende exclusivamente dos eventos fornecidos. Os arquivos de entrada foram preservados.
