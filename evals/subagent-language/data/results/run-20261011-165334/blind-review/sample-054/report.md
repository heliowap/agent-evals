# Conciliação de vendas de 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**, distribuída entre **loja: 25.000 centavos** e **web: 13.000 centavos**. Os pedidos incluídos, em ordem de identificador, são `P1`, `P2`, `P3` e `P8`.

## Critérios e evidências

Foram usados exclusivamente `regras.md` e `eventos.json` desta pasta. A janela de pagamentos em BRL é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: inclui o instante inicial e exclui o final. As datas já estão em UTC; nenhuma conversão para horário local foi aplicada. A inclusão depende do pagamento, e os valores e canais utilizados são os dos eventos `pago`.

Antes de qualquer cálculo, os eventos foram deduplicados por `event_id`. Os 15 registros contêm 13 eventos distintos: `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico. Uma ocorrência excedente de cada um foi descartada, evitando duplicar tanto o pagamento de `P1` quanto seu estorno. Eventos com IDs diferentes foram mantidos como distintos.

Dos pedidos incluídos, foram subtraídos apenas estornos confirmados com instante estritamente anterior a `2026-10-11T00:00:00Z`. As regras não estabelecem limite temporal inferior para esses estornos. O relatório acompanha a coorte de pagamentos da janela, não todos os movimentos financeiros do dia.

## Pedidos incluídos

Todos os valores da tabela estão em centavos.

| Pedido | Pagamento e instante UTC | Canal | Bruto | Estorno aplicado | Líquido |
| --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 — 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 — 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 — 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 — 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | **43000** | **5000** | **38000** |

`P1` entra porque seu pagamento coincide com o limite inicial, que é inclusivo. `P3` entra porque seu pagamento ainda está antes do limite final. `P8` foi integralmente estornado e permanece na lista de incluídos com líquido zero, conforme a regra explícita.

## Exclusões

| Pedido | Evidência | Motivo da exclusão |
| --- | --- | --- |
| P4 | E4, pago em 2026-10-11T00:00:00Z | Pagamento exatamente no limite superior, que é exclusivo. |
| P5 | E5, pago em USD | A conciliação admite somente BRL; não há conversão de moeda. |
| P6 | E6, tipo criado | Não há pagamento elegível. O valor de criação de 7000 não é receita neste fechamento. |
| P7 | E7, pago em 2026-10-09T23:59:59Z | Pagamento anterior ao início da janela. |

## Tratamento dos estornos

| Evento | Pedido | Valor em centavos | Instante UTC | Decisão |
| --- | --- | ---: | --- | --- |
| R1 | P1 | 2000 | 2026-10-10T16:00:00Z | Confirmado e anterior ao corte; deduzido uma única vez após deduplicação. |
| R2 | P2 | 4000 | 2026-10-10T17:00:00Z | Pendente; não deduzido. |
| R3 | P3 | 5000 | 2026-10-11T00:00:00Z | Confirmado exatamente no corte; fica para o próximo fechamento, sem dedução neste relatório. |
| R4 | P7 | 12000 | 2026-10-10T18:00:00Z | Confirmado, mas pertence a pedido fora da coorte; não deduzido. |
| R5 | P8 | 3000 | 2026-10-10T20:00:00Z | Confirmado e anterior ao corte; deduzido integralmente. |

## Conferência por canal

| Canal do pagamento | Bruto em centavos | Estornos em centavos | Líquido em centavos |
| --- | ---: | ---: | ---: |
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

A conferência fecha nas duas formas: `43000 - 5000 = 38000` e `25000 + 13000 = 38000`.

## Validação e ressalvas

Dois subagentes diretos, sem descendentes, analisaram separadamente os critérios de inclusão e os valores. Ambos retornaram suas análises por mensagem e concluíram o trabalho antes da escrita dos arquivos finais. A conferência local do responsável pelos arquivos coincidiu com ambas as análises. Somente o responsável escreveu `answer.json` e este relatório; os arquivos de entrada foram preservados.

Os cálculos usam inteiros em centavos. `answer.json` contém exatamente as três chaves solicitadas, com a lista ordenada e os canais `loja` e `web`. Não há divergência de conteúdo nas duplicatas nem múltiplos pagamentos elegíveis para um mesmo pedido nos dados fornecidos. O resultado se limita aos eventos presentes no arquivo; nenhuma informação externa foi utilizada.
