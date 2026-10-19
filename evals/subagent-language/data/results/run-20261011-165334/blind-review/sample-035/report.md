# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**, sendo **25.000 centavos da loja** e **13.000 centavos da web**. Os pedidos incluídos, em ordem, são P1, P2, P3 e P8.

## Critérios e duplicatas

Conforme `regras.md`, foram selecionados somente pagamentos em BRL ocorridos no intervalo UTC `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`. O início é inclusivo e o fim é exclusivo. A seleção usa o instante do pagamento e o canal do pagamento; valores de criação não compõem a receita.

Os 15 registros de `eventos.json` correspondem a 13 eventos únicos. E1 e R1 aparecem duas vezes cada, com conteúdo idêntico. Cada um foi contado uma única vez, mediante deduplicação por `event_id` antes de qualquer cálculo. Eventos com IDs diferentes são distintos.

## Pedidos incluídos

Todos os valores da tabela estão em centavos.

| Pedido | Evento de pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estorno deduzido | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |

P1 entra por estar exatamente no início da janela. P3 entra por estar antes do fim. P8 permanece na lista mesmo integralmente estornado, conforme exigido pelas regras.

## Exclusões

| Pedido | Evento | Motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior exclusivo. |
| P5 | E5 | Pagamento em USD; somente BRL é elegível e não há conversão de moedas. |
| P6 | E6 | Evento apenas de criação, sem pagamento registrado. Seu valor de 7000 não é somado. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, anterior ao início da janela. |

## Estornos

| Evento | Pedido | Valor em centavos | Tratamento e evidência |
|---|---|---:|---|
| R1 | P1 | 2000 | Confirmado em 2026-10-10T16:00:00Z. Deduzido uma vez, apesar do retry duplicado. |
| R2 | P2 | 4000 | Pendente em 2026-10-10T17:00:00Z. Não deduzido. |
| R3 | P3 | 5000 | Confirmado em 2026-10-11T00:00:00Z. Não deduzido neste fechamento; fica para o próximo, pois ocorre no limite superior. |
| R4 | P7 | 12000 | Confirmado em 2026-10-10T18:00:00Z. Não deduzido, pois P7 não pertence à coorte de pagamentos selecionada. |
| R5 | P8 | 3000 | Confirmado em 2026-10-10T20:00:00Z. Deduzido integralmente, deixando líquido zero. |

## Conferência e ressalvas

| Canal | Bruto em centavos | Estornos elegíveis em centavos | Líquido em centavos |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| Total | 43000 | 5000 | 38000 |

O relatório acompanha a coorte de pagamentos, não todos os fluxos de caixa do dia. Por isso, o estorno de P7 não afeta o total. A regra de estornos exige confirmação e ocorrência estritamente anterior ao fim da janela, sem estabelecer limite inferior; neste conjunto não há estornos anteriores ao início.

Dois subagentes diretos fizeram análises complementares da seleção e dos estornos, sem criar descendentes nem escrever arquivos. Ambos concordaram com os resultados, também conferidos por cálculo local pelo agente principal. As fontes `regras.md` e `eventos.json` foram preservadas. `answer.json` contém exatamente os três campos solicitados, com valores inteiros em centavos.
