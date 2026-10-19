# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**: 25.000 centavos de loja e 13.000 centavos de web. Os pedidos incluídos, em ordem crescente de identificador, são **P1, P2, P3 e P8**.

## Critérios e evidências

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A janela de pagamentos é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`, em UTC: inclui o instante inicial e exclui o final. Apenas pagamentos em BRL entram. A seleção usa a data e o canal do pagamento; eventos de criação não geram receita.

Antes de qualquer cálculo, os eventos foram deduplicados por `event_id`. Dos 15 registros, restaram 13 eventos distintos. `E1` aparece duas vezes com conteúdo idêntico: seu pagamento de 10.000 centavos foi contado uma única vez. `R1` também aparece duas vezes com conteúdo idêntico: seu estorno de 2.000 centavos foi descontado uma única vez. Eventos com IDs diferentes foram mantidos como eventos distintos.

## Pedidos incluídos

Todos os valores da tabela estão em centavos. Os estornos são atribuídos ao canal do pagamento do respectivo pedido.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estornos aplicados | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra porque o limite inicial é inclusivo. P3 entra porque foi pago antes do limite final. P8 permanece na lista mesmo após estorno integral, conforme a regra explícita de manter pedidos integralmente estornados com líquido zero.

## Exclusões

| Pedido | Evento | Evidência e motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior excluído. |
| P5 | E5 | Pagamento em USD; outras moedas não são convertidas nem incluídas. |
| P6 | E6 | Somente evento `criado`, sem pagamento; os 7000 centavos de criação não entram. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, anterior ao início da janela. |

## Tratamento dos estornos

São descontados apenas estornos confirmados de pedidos incluídos, ocorridos estritamente antes de `2026-10-11T00:00:00Z`. A regra não impõe limite inferior ao instante do estorno.

| Evento | Pedido | Valor (centavos) | Tratamento e evidência |
|---|---|---:|---|
| R1 | P1 | 2000 | Aplicado uma vez: confirmado em 2026-10-10T16:00:00Z; estorno parcial. |
| R2 | P2 | 4000 | Ignorado por estar pendente, apesar de ocorrer antes do corte. |
| R3 | P3 | 5000 | Não aplicado neste fechamento: confirmado exatamente em 2026-10-11T00:00:00Z; fica para o próximo fechamento conforme a regra. |
| R4 | P7 | 12000 | Ignorado: embora confirmado em 2026-10-10T18:00:00Z, pertence a pedido pago fora da janela. |
| R5 | P8 | 3000 | Aplicado: confirmado em 2026-10-10T20:00:00Z; estorno integral. |

## Conferência dos totais

| Canal do pagamento | Bruto (centavos) | Estornos aplicados (centavos) | Líquido (centavos) |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

As duas conferências fecham: `43000 - 5000 = 38000` e `25000 + 13000 = 38000`. `answer.json` contém somente as três chaves solicitadas, com lista ordenada e valores inteiros em centavos.

## Ressalvas e validação

O resultado é por coorte de pagamentos, não o fluxo de caixa de todos os eventos do dia. Assim, R4 não reduz este fechamento e R3 não reduz P3 neste corte. Não foi feita conversão de moeda ou de fuso horário; as datas de entrada já estão em UTC.

As conclusões se limitam aos arquivos fornecidos. Não foram encontrados conteúdos conflitantes nas duplicatas. Dois subagentes diretos, sem descendentes, concluíram análises independentes de regras e valores; ambos concordaram com o cálculo local do agente principal. Apenas o agente principal escreveu os arquivos de entrega, e os arquivos de entrada foram preservados.
