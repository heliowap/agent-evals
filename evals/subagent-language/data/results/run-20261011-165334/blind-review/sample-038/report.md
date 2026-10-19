# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos**, sendo **25.000 centavos em loja** e **13.000 centavos em web**. Os pedidos incluídos, em ordem, são **P1, P2, P3 e P8**.

## Critérios e evidências

Foram usados somente `regras.md` e `eventos.json`, preservados sem alterações. Conforme as regras, entram pagamentos em BRL ocorridos na janela UTC `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início é inclusivo e o fim é exclusivo. A seleção usa o instante e o canal do pagamento; valores e datas de criação não determinam a inclusão.

Antes de qualquer cálculo, os eventos foram deduplicados por `event_id`. Há 15 registros e 13 eventos únicos. As duas ocorrências de `E1` são idênticas, assim como as duas de `R1`; uma cópia de cada foi descartada. Assim, o pagamento de P1 e seu estorno parcial são contados uma única vez. IDs diferentes representam eventos distintos; não houve duplicatas conflitantes.

Todos os valores abaixo são inteiros em centavos.

## Pedidos incluídos

| Pedido | Pagamento e instante UTC | Canal do pagamento | Bruto | Estorno deduzido | Líquido |
| --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 — 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 — 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 — 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 — 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | **43000** | **5000** | **38000** |

P1 entra por ter sido pago exatamente no início da janela. P3 entra por ter sido pago antes do limite superior. P8 permanece na lista mesmo integralmente estornado, conforme a regra explícita.

## Exclusões de pedidos

| Pedido | Evidência | Motivo |
| --- | --- | --- |
| P4 | E4 — pagamento em 2026-10-11T00:00:00Z, valor 99999 | O pagamento coincide com o limite superior, que é exclusivo. |
| P5 | E5 — pagamento em USD, valor 8000 | Apenas BRL entra; não há conversão de moedas. |
| P6 | E6 — evento `criado`, valor 7000 | Não existe pagamento para este pedido no arquivo; a criação não gera receita neste fechamento. |
| P7 | E7 — pagamento em 2026-10-09T23:59:59Z, valor 12000 | O pagamento ocorreu antes da janela. |

## Tratamento dos estornos

| Evento | Pedido | Valor | Instante UTC | Decisão |
| --- | --- | ---: | --- | --- |
| R1 | P1 | 2000 | 2026-10-10T16:00:00Z | Deduzido uma única vez: confirmado, antes do limite superior e de pedido incluído. |
| R2 | P2 | 4000 | 2026-10-10T17:00:00Z | Excluído por estar pendente. |
| R3 | P3 | 5000 | 2026-10-11T00:00:00Z | Não deduzido: ocorre exatamente no limite superior e fica para o próximo fechamento. |
| R4 | P7 | 12000 | 2026-10-10T18:00:00Z | Excluído: P7 não pertence à coorte de pagamentos incluída, embora o estorno ocorra no dia. |
| R5 | P8 | 3000 | 2026-10-10T20:00:00Z | Deduzido integralmente: confirmado e antes do limite superior; P8 fica com líquido zero. |

## Conferência por canal

| Canal | Bruto | Estornos aplicáveis | Líquido |
| --- | ---: | ---: | ---: |
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

O líquido total corresponde tanto a `43000 − 5000 = 38000` quanto a `25000 + 13000 = 38000`. Dois subagentes diretos fizeram análises independentes, sem escrever arquivos ou criar descendentes; ambas concordaram com o cálculo local do agente principal.

## Ressalvas

Este relatório representa a coorte de pagamentos da janela, não o fluxo de caixa de todos os eventos do dia. Para estornos confirmados de pedidos incluídos, a regra exige apenas ocorrência estritamente anterior ao limite superior; não impõe um limite inferior aos estornos. Não foram criadas restrições adicionais.

O resultado reflete os eventos fornecidos. Estornos pendentes e eventos no limite superior não alteram este fechamento. As datas já estão em UTC e não foram convertidas para o horário local. `answer.json` contém exclusivamente as três chaves solicitadas, com a lista ordenada, o total inteiro e os canais `loja` e `web`.
