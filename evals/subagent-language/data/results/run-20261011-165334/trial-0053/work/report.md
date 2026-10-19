# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38.000 centavos de BRL (R$ 380,00)**, composta por 25.000 centavos no canal loja e 13.000 no canal web. Os pedidos incluídos, em ordem, são `P1`, `P2`, `P3` e `P8`.

## Critérios e deduplicação

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A janela dos pagamentos é `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início entra e o fim fica fora. Todos os horários são UTC. Apenas pagamentos BRL entram, usando o canal do pagamento e valores inteiros em centavos; eventos de criação não geram receita.

Os 15 registros de entrada contêm 13 `event_id` distintos. `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico. Uma ocorrência repetida de cada foi descartada antes dos cálculos. Eventos com IDs diferentes foram mantidos como distintos.

Para cada pedido incluído, foram subtraídos os estornos confirmados ocorridos estritamente antes de `2026-10-11T00:00:00Z`. A regra dos estornos não impõe limite inferior de horário. Estornos pendentes e estornos de pedidos fora da coorte não entram.

## Pedidos incluídos e valores

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto (centavos) | Estorno deduzido (centavos) | Líquido (centavos) |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

`P1` entra exatamente no limite inferior inclusivo. `P3` entra um segundo antes do limite superior. `P8` permanece na lista mesmo com estorno integral e líquido zero.

## Pedidos excluídos

| Pedido | Evidência | Decisão |
|---|---|---|
| P4 | E4: pagamento BRL em 2026-10-11T00:00:00Z | Fora da janela, exatamente no limite superior exclusivo. |
| P5 | E5: pagamento em USD em 2026-10-10T10:00:00Z | Moeda diferente de BRL; não houve conversão. |
| P6 | E6: evento `criado` em 2026-10-10T11:00:00Z | Não há pagamento registrado; os 7000 centavos da criação não são receita. |
| P7 | E7: pagamento BRL em 2026-10-09T23:59:59Z | Pagamento anterior ao início da janela. |

## Tratamento dos estornos

| Evento | Pedido | Estado | Instante (UTC) | Valor (centavos) | Tratamento |
|---|---|---|---|---:|---|
| R1 | P1 | Confirmado | 2026-10-10T16:00:00Z | 2000 | Deduzido uma única vez após remover a duplicata. |
| R2 | P2 | Pendente | 2026-10-10T17:00:00Z | 4000 | Não deduzido porque ainda está pendente. |
| R3 | P3 | Confirmado | 2026-10-11T00:00:00Z | 5000 | Não deduzido neste fechamento; ocorreu no limite superior e fica para o próximo fechamento, conforme as regras. |
| R4 | P7 | Confirmado | 2026-10-10T18:00:00Z | 12000 | Não deduzido porque P7 está fora da coorte de pagamentos. |
| R5 | P8 | Confirmado | 2026-10-10T20:00:00Z | 3000 | Deduzido integralmente; P8 continua incluído com líquido zero. |

## Conferência e ressalvas

O canal loja soma `25000 + 0 = 25000` centavos; web soma `8000 + 5000 = 13000` centavos. A soma dos canais é `25000 + 13000 = 38000`, igual ao bruto incluído menos estornos elegíveis: `43000 - 5000 = 38000`.

O resultado representa a coorte de pagamentos elegíveis, e não o fluxo de caixa de todos os eventos do dia. Por isso R4 não reduz o total, apesar de ter ocorrido em 10 de outubro, e R3 não reduz P3 neste fechamento. A análise se limita aos eventos fornecidos, sem inferir pagamentos ausentes ou confirmação futura de estornos pendentes.

Dois subagentes diretos fizeram análises independentes somente de leitura e retornaram suas conclusões por mensagem, sem criar descendentes. O agente principal aguardou ambos, conferiu os cálculos e escreveu os arquivos finais. As três conferências concordaram, e os arquivos de entrada foram preservados.
