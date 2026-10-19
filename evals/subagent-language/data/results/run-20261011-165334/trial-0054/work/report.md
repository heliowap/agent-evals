# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**, sendo 25.000 centavos de loja e 13.000 centavos de web. A lista ordenada de pedidos incluídos é `P1`, `P2`, `P3`, `P8`.

## Critérios e evidências

Foram usados somente `regras.md` e `eventos.json`, preservados sem alterações. A janela de pagamentos em UTC é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: inclui o início e exclui o fim. Entram somente pagamentos em BRL, usando o instante e o canal do pagamento. Valores de criação não são somados e outras moedas não são convertidas.

Os 15 registros foram deduplicados por `event_id` antes de qualquer cálculo, resultando em 13 eventos únicos. `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico; uma cópia de cada foi descartada. IDs diferentes foram mantidos como eventos distintos.

## Pedidos incluídos

Todos os valores da tabela estão em centavos. Os estornos descontados são confirmados e ocorreram estritamente antes do limite superior.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estorno descontado | Líquido |
| --- | --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra exatamente no início da janela. Seu estorno parcial `R1`, de 2000 centavos, ocorreu em `2026-10-10T16:00:00Z` e foi descontado uma única vez. P8 teve estorno integral confirmado `R5`, de 3000 centavos, em `2026-10-10T20:00:00Z`; permanece na lista de incluídos com líquido zero, conforme a regra.

## Exclusões e estornos não descontados

| Evento | Pedido | Valor em centavos | Motivo |
| --- | --- | ---: | --- |
| E4 | P4 | 99999 | Pagamento em `2026-10-11T00:00:00Z`, exatamente no limite superior excluído. |
| E5 | P5 | 8000 | Pagamento em USD; moeda excluída, sem conversão. |
| E6 | P6 | 7000 | Evento de criação; não há pagamento desse pedido nos dados. |
| E7 | P7 | 12000 | Pagamento em `2026-10-09T23:59:59Z`, anterior ao início da janela. |
| R2 | P2 | 4000 | Estorno pendente em `2026-10-10T17:00:00Z`; não reduz a receita. |
| R3 | P3 | 5000 | Estorno confirmado em `2026-10-11T00:00:00Z`, exatamente no limite superior; fica para o próximo fechamento. P3 mantém líquido de 5000 neste relatório. |
| R4 | P7 | 12000 | Estorno confirmado em `2026-10-10T18:00:00Z`, mas referente a pagamento fora da coorte; não entra neste relatório. |

## Conferência e ressalvas

Por canal do pagamento, loja soma `25000 + 0 = 25000` e web soma `8000 + 5000 = 13000`. A soma dos canais é `25000 + 13000 = 38000`, igual ao bruto menos os estornos elegíveis: `43000 - 5000 = 38000`.

O resultado representa a coorte de pagamentos definida nas regras, e não todos os movimentos financeiros do dia. Para estornos confirmados de pedidos incluídos, a regra exige apenas instante anterior ao limite superior; não impõe um limite inferior adicional. Todos os cálculos usam inteiros em centavos, sem arredondamento.

Exatamente dois subagentes diretos, sem descendentes, analisaram os pagamentos e auditaram os estornos por ferramentas locais. Ambos concluíram suas análises por mensagem e concordaram com o cálculo independente do agente principal, que escreveu os arquivos finais. Não houve acesso à internet.
