# Conciliação de vendas — fechamento de 10 de outubro de 2026

A receita líquida é **38.000 centavos de BRL**, distribuída entre **loja: 25.000** e **web: 13.000**. A lista ordenada de pedidos incluídos é **P1, P2, P3 e P8**.

## Critérios e evidências

Foram aplicadas as regras de `regras.md` aos eventos de `eventos.json`. A seleção considera pagamentos em BRL no intervalo **[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)**: o início entra e o fim não entra. Todas as datas foram tratadas em UTC, sem conversão para o fuso local. O instante de criação não determina a inclusão, e seu valor não compõe a receita.

Antes de qualquer cálculo, os 15 registros foram deduplicados por `event_id`, restando 13 eventos distintos. `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico; cada um foi considerado uma única vez. Eventos de IDs diferentes foram preservados como distintos.

## Pedidos incluídos

Todos os valores da tabela são inteiros em centavos. O canal é o do pagamento.

| Pedido | Evento de pagamento | Pagamento em UTC | Canal | Bruto | Estornos aplicados | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra por ter sido pago exatamente no início inclusivo. P3 entra por ter sido pago antes do fim exclusivo. P8 foi integralmente estornado, mas permanece na lista de incluídos com líquido zero, conforme a regra.

## Pedidos excluídos

| Pedido | Evento | Evidência e motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior exclusivo. |
| P5 | E5 | Pagamento em USD; somente BRL é elegível e não há conversão de moedas. |
| P6 | E6 | Evento do tipo `criado`, sem pagamento elegível no arquivo. Os 7000 centavos da criação não são somados. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, antes do início da janela. |

## Tratamento dos estornos

| Evento | Pedido | Valor | Evidência e decisão |
|---|---|---:|---|
| R1 | P1 | 2000 | Confirmado em 2026-10-10T16:00:00Z; estorno parcial subtraído uma vez após deduplicação. |
| R2 | P2 | 4000 | Pendente em 2026-10-10T17:00:00Z; não reduz a receita. |
| R3 | P3 | 5000 | Confirmado em 2026-10-11T00:00:00Z; não é estritamente anterior ao corte. Não é abatido neste fechamento; a regra o reserva para o próximo. |
| R4 | P7 | 12000 | Confirmado em 2026-10-10T18:00:00Z, mas pertence a um pedido fora da coorte de pagamentos; não entra no relatório. |
| R5 | P8 | 3000 | Confirmado em 2026-10-10T20:00:00Z; subtraído integralmente, deixando P8 com líquido zero. |

## Conferência e ressalvas

A soma dos pagamentos elegíveis é 43000 centavos. Os estornos aplicáveis somam 5000 centavos: R1 (2000) e R5 (3000). Assim, **43000 − 5000 = 38000**. Por canal, **loja = 25000 + 0 = 25000** e **web = 8000 + 5000 = 13000**; a soma dos canais confere com a receita líquida.

Este fechamento representa uma coorte de pagamentos, não o fluxo de caixa de todos os eventos do dia. Para pedidos incluídos, a regra dos estornos exige confirmação e ocorrência estritamente anterior ao limite superior, sem impor limite inferior; não há estornos anteriores ao início neste arquivo. A conciliação se limita aos dados fornecidos.

Dois subagentes diretos, sem descendentes, retornaram análises independentes por mensagem: um revisou a seleção da coorte e outro auditou estornos e totais. Ambos concluíram antes da escrita dos arquivos finais, feita somente pelo agente principal. Um cálculo local adicional confirmou os resultados. O contrato de `answer.json` e a preservação dos arquivos de entrada foram verificados.
