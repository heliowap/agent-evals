# Conciliação de vendas — fechamento de 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**: loja soma 25.000 centavos e web soma 13.000 centavos. Os pedidos incluídos, em ordem, são **P1, P2, P3 e P8**.

## Critérios e decisões

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A seleção considera pagamentos em BRL no intervalo UTC `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início é inclusivo e o fim é exclusivo. As datas já estão em UTC; não houve ajuste para o fuso local. A criação do pedido não determina a janela nem acrescenta receita. O canal é o do pagamento.

Antes de selecionar pagamentos ou calcular valores, os 15 registros foram deduplicados por `event_id`, resultando em 13 eventos únicos. E1 e R1 aparecem duas vezes cada, com conteúdo idêntico; uma repetição de cada foi descartada. Eventos com IDs diferentes foram mantidos como eventos distintos.

Dos pedidos selecionados, foram subtraídos somente os estornos confirmados ocorridos estritamente antes do fim da janela. Essa regra não impõe um limite inferior aos estornos. O fechamento é por coorte de pagamentos; estornos de pedidos fora da coorte não entram, mesmo quando ocorridos no dia.

## Pagamentos e valores conciliados

Todos os valores da tabela estão em centavos.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estorno aplicado | Líquido |
| --- | --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10.000 | 2.000 (R1) | 8.000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25.000 | 0 | 25.000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5.000 | 0 | 5.000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3.000 | 3.000 (R5) | 0 |
| **Total** | | | | **43.000** | **5.000** | **38.000** |

P1 entra por ter sido pago exatamente no início inclusivo. P8 permanece na lista apesar de estar integralmente estornado, conforme a regra explícita.

| Canal do pagamento | Bruto | Estornos aplicados | Líquido |
| --- | ---: | ---: | ---: |
| loja | 28.000 | 3.000 | 25.000 |
| web | 15.000 | 2.000 | 13.000 |
| **Total** | **43.000** | **5.000** | **38.000** |

## Exclusões de pedidos

| Pedido / evento | Evidência | Decisão |
| --- | --- | --- |
| P4 / E4 | Pagamento em 2026-10-11T00:00:00Z, de 99.999 centavos | Excluído por ocorrer exatamente no fim exclusivo da janela. |
| P5 / E5 | Pagamento em USD, valor 8.000 na moeda informada | Excluído por não ser BRL; nenhuma conversão foi realizada. |
| P6 / E6 | Evento `criado`, de 7.000 centavos | Excluído por não representar pagamento. |
| P7 / E7 | Pagamento em 2026-10-09T23:59:59Z, de 12.000 centavos | Excluído por ser anterior ao início da janela. |

## Tratamento dos estornos

| Evento / pedido | Valor em centavos | Evidência | Decisão |
| --- | ---: | --- | --- |
| R1 / P1 | 2.000 | Confirmado em 2026-10-10T16:00:00Z | Subtraído uma vez; o retry idêntico foi descartado. |
| R2 / P2 | 4.000 | Pendente em 2026-10-10T17:00:00Z | Não subtraído, pois falta confirmação. |
| R3 / P3 | 5.000 | Confirmado em 2026-10-11T00:00:00Z | Não subtraído neste fechamento; fica para o próximo, pois está no limite superior. |
| R4 / P7 | 12.000 | Confirmado em 2026-10-10T18:00:00Z | Não subtraído: P7 está fora da coorte de pagamentos. |
| R5 / P8 | 3.000 | Confirmado em 2026-10-10T20:00:00Z | Subtraído integralmente; P8 continua incluído com líquido zero. |

## Validação e ressalvas

Dois subagentes diretos analisaram separadamente a seleção dos pagamentos e o tratamento dos estornos, sem criar descendentes ou escrever arquivos. Ambos retornaram suas análises por mensagem e concluíram antes da produção dos arquivos finais. Os resultados coincidiram com o cálculo local do agente principal: 43.000 − 5.000 = 38.000 centavos, e 25.000 + 13.000 = 38.000 centavos.

`answer.json` contém exatamente os campos solicitados, com pedidos ordenados e valores inteiros em centavos. As conclusões se limitam aos eventos fornecidos e às regras deste fechamento: não representam o fluxo de caixa de todos os eventos do dia. Os arquivos de entrada foram preservados, e nenhuma fonte externa foi consultada.
