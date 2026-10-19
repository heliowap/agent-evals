# Conciliação das vendas — 10 de outubro de 2026

A receita líquida é **38000 centavos (R$ 380,00)**, sendo 25000 centavos de loja e 13000 de web. Os pedidos incluídos, em ordem, são **P1, P2, P3 e P8**.

## Critérios e evidências

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A coorte contém apenas pagamentos em BRL ocorridos em `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: início inclusivo e fim exclusivo. As datas já estão em UTC; não foi aplicada conversão de fuso. A criação de um pedido não determina sua inclusão e seu valor não é somado. O canal utilizado é o do pagamento.

A deduplicação por `event_id` ocorreu antes dos cálculos: os 15 registros representam 13 eventos únicos. E1 e R1 aparecem duas vezes cada, com conteúdo idêntico; uma repetição de cada foi descartada. Assim, o pagamento E1 de 10000 centavos e o estorno R1 de 2000 centavos foram contabilizados uma única vez. Eventos com IDs diferentes permanecem distintos.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto (centavos) | Estornos abatidos (centavos) | Líquido (centavos) |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra exatamente no início inclusivo. P3 entra um segundo antes do fim. P8 permanece na lista mesmo integralmente estornado, conforme a regra explícita.

## Exclusões de pedidos

| Pedido | Evento | Motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no fim exclusivo da janela; seus 99999 centavos não entram. |
| P5 | E5 | Pagamento em USD; seus 8000 centavos não entram e não são convertidos para BRL. |
| P6 | E6 | Apenas evento `criado`, sem pagamento elegível; seus 7000 centavos não entram. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, um segundo antes do início da janela; seus 12000 centavos não entram. |

## Tratamento dos estornos

Somente estornos confirmados de pedidos incluídos, ocorridos estritamente antes de `2026-10-11T00:00:00Z`, reduzem a receita. A regra não estabelece limite inferior para os estornos.

| Evento | Pedido | Valor (centavos) | Decisão e evidência |
|---|---|---:|---|
| R1 | P1 | 2000 | Abatido uma vez: confirmado em 2026-10-10T16:00:00Z; estorno parcial. A repetição foi descartada. |
| R2 | P2 | 4000 | Não abatido: status `estorno_pendente`, apesar de ocorrer antes do corte. |
| R3 | P3 | 5000 | Não abatido: confirmado exatamente em 2026-10-11T00:00:00Z; fica para o próximo fechamento conforme as regras. |
| R4 | P7 | 12000 | Não abatido: confirmado em 2026-10-10T18:00:00Z, mas P7 não pertence à coorte de pagamentos. |
| R5 | P8 | 3000 | Abatido: confirmado em 2026-10-10T20:00:00Z; estorno integral, deixando P8 com líquido zero. |

## Conferência e ressalvas

| Canal do pagamento | Bruto (centavos) | Estornos abatidos (centavos) | Líquido (centavos) |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

A soma dos canais coincide com o líquido: `25000 + 13000 = 38000`, também igual a `43000 - 5000`. Todos os cálculos usam inteiros em centavos.

Este fechamento é por coorte de pagamentos, não um fluxo de caixa de todos os eventos do dia. Por isso R4 não entra, embora tenha ocorrido no dia, e R3 não reduz este fechamento. O resultado reflete apenas os arquivos fornecidos e os status neles registrados.

Exatamente dois subagentes diretos, sem descendentes, conferiram respectivamente os pagamentos e os estornos. Ambos retornaram suas análises sem escrever arquivos e concluíram antes da geração dos resultados. A conferência local do agente principal coincidiu com ambas as análises. Somente o agente principal escreveu `answer.json` e este relatório; os arquivos de entrada foram preservados e não houve acesso à internet.
