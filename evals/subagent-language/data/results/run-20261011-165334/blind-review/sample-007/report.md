# Conciliação de vendas — fechamento de 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**, com **25.000 centavos em loja** e **13.000 centavos em web**. Os pedidos incluídos, em ordem crescente de identificador, são **P1, P2, P3 e P8**.

## Critérios e duplicatas

Foram aplicadas as regras de `regras.md` aos eventos de `eventos.json`. A janela de pagamentos é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início é inclusivo e o fim é exclusivo. As datas foram tratadas em UTC, sem ajuste ao fuso local.

O arquivo contém 15 registros e 13 eventos únicos. `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico. Uma ocorrência repetida de cada ID foi descartada antes de qualquer cálculo. IDs diferentes representam eventos distintos.

Entram apenas pagamentos em BRL dentro da janela. A data e o valor de criação não determinam a inclusão nem a receita. Cada valor líquido é atribuído ao canal do pagamento. Dos pedidos incluídos, foram subtraídos somente os estornos confirmados anteriores, estritamente, ao fim da janela.

## Pedidos incluídos

Todos os valores das tabelas são inteiros em centavos.

| Pedido | Evento de pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estorno aplicado | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra por estar exatamente no início inclusivo. P3 entra por ter sido pago antes do fim exclusivo. P8 permanece na lista mesmo após estorno integral, conforme a regra explícita.

## Exclusões de pedidos

| Pedido | Evento | Evidência | Decisão |
|---|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z | Excluído por estar exatamente no fim exclusivo. |
| P5 | E5 | Pagamento em USD, valor 8000 | Excluído pela moeda, sem conversão. |
| P6 | E6 | Tipo `criado`, valor 7000 | Excluído por não haver pagamento elegível; valor de criação não somado. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z | Excluído por ser anterior ao início da janela. |

## Tratamento de estornos

| Evento | Pedido | Valor | Estado e instante (UTC) | Tratamento |
|---|---|---:|---|---|
| R1 | P1 | 2000 | Confirmado em 2026-10-10T16:00:00Z | Subtraído uma única vez; estorno parcial. |
| R2 | P2 | 4000 | Pendente em 2026-10-10T17:00:00Z | Não subtraído, pois ainda está pendente. |
| R3 | P3 | 5000 | Confirmado em 2026-10-11T00:00:00Z | Não subtraído neste fechamento; no limite superior, fica para o próximo fechamento conforme a regra. |
| R4 | P7 | 12000 | Confirmado em 2026-10-10T18:00:00Z | Não subtraído, pois P7 está fora da coorte de pagamentos incluída. |
| R5 | P8 | 3000 | Confirmado em 2026-10-10T20:00:00Z | Subtraído integralmente; P8 permanece incluído com líquido zero. |

## Totais por canal

| Canal do pagamento | Bruto | Estornos aplicados | Líquido |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

As conferências fecham: `43000 - 5000 = 38000` e `25000 + 13000 = 38000`.

## Ressalvas e verificação

Este relatório acompanha a coorte de pagamentos elegíveis, portanto não representa o fluxo de caixa de todos os eventos do dia. Isso explica a exclusão de R4, mesmo tendo ocorrido durante o dia. A regra dos estornos exige apenas que sejam anteriores ao fim da janela; não impõe um limite inferior para eles. R1 e R5 são associados aos pagamentos elegíveis pelo pedido, usando o canal desses pagamentos.

O tratamento contábil de R3 em fechamentos futuros não é calculado aqui; seu efeito neste fechamento é zero. Não foram convertidas outras moedas nem inferidos pagamentos ausentes.

Exatamente dois subagentes diretos, sem descendentes e com `fork_turns="none"`, fizeram o cálculo e a auditoria separadamente e retornaram suas análises por mensagem. Ambos concluíram e concordaram com o resultado antes da gravação dos arquivos finais pelo agente principal. Foram usadas somente ferramentas locais. `answer.json` contém exclusivamente as três chaves solicitadas, com a lista ordenada e os valores inteiros em centavos. Os arquivos de entrada foram preservados.
