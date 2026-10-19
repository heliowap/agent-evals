# Conciliação de vendas — 10 de outubro de 2026

A receita líquida é **38000 centavos (R$ 380,00)**. Os pedidos incluídos, em ordem crescente de identificador, são **P1, P2, P3 e P8**. O canal loja soma 25000 centavos e o canal web soma 13000 centavos.

## Critérios aplicados

Foram utilizados somente `regras.md` e `eventos.json` desta pasta. Conforme as regras, a coorte contém pagamentos em BRL ocorridos em `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início é inclusivo e o fim é exclusivo. Todos os instantes foram tratados em UTC, sem conversão de fuso. A seleção usa a data do pagamento, e os valores são atribuídos ao canal do pagamento; valores de criação não são somados.

Antes de qualquer soma, os eventos foram deduplicados por `event_id`. Dos 15 registros, restaram 13 eventos únicos. `E1` e `R1` aparecem duas vezes cada, com conteúdo idêntico; uma repetição de cada foi descartada. Assim, o pagamento de P1 conta 10000 centavos uma única vez, e seu estorno conta 2000 centavos uma única vez. Eventos com identificadores diferentes foram mantidos como eventos distintos.

Para cada pedido incluído, foram subtraídos somente os estornos confirmados com instante estritamente anterior a `2026-10-11T00:00:00Z`. A regra não impõe limite inferior aos estornos aplicáveis. Estornos pendentes, no limite superior ou vinculados a pedidos fora da coorte não reduzem este fechamento.

## Pedidos incluídos e evidências

Todos os valores das tabelas estão em centavos.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estornos aplicados | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 é incluído por ter pagamento exatamente no início inclusivo. P8 permanece na lista mesmo integralmente estornado, conforme determinação expressa das regras.

| Canal do pagamento | Bruto | Estornos aplicados | Líquido |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

## Exclusões de pedidos

| Pedido | Evento | Evidência e decisão |
|---|---|---|
| P4 | E4 | Pagamento em `2026-10-11T00:00:00Z`, exatamente no fim exclusivo; fora da janela. |
| P5 | E5 | Pagamento em USD; excluído sem conversão de moeda. |
| P6 | E6 | Evento apenas de criação, sem pagamento registrado; seus 7000 centavos não entram. |
| P7 | E7 | Pagamento em `2026-10-09T23:59:59Z`, anterior ao início da janela. |

## Tratamento dos estornos

| Evento | Pedido | Valor | Instante (UTC) | Decisão |
|---|---|---:|---|---|
| R1 | P1 | 2000 | 2026-10-10T16:00:00Z | Confirmado e anterior ao corte; subtraído uma única vez após deduplicação. |
| R2 | P2 | 4000 | 2026-10-10T17:00:00Z | Pendente; não subtraído. |
| R3 | P3 | 5000 | 2026-10-11T00:00:00Z | Confirmado exatamente no limite superior; fica para o próximo fechamento, sem reduzir P3 neste relatório. |
| R4 | P7 | 12000 | 2026-10-10T18:00:00Z | Confirmado no dia, mas referente a pedido fora da coorte; excluído. |
| R5 | P8 | 3000 | 2026-10-10T20:00:00Z | Confirmado e anterior ao corte; subtraído integralmente, mantendo P8 incluído com líquido zero. |

## Verificação e ressalvas

Exatamente dois subagentes diretos, sem descendentes, concluíram análises somente de leitura: um auditou as regras e outro conferiu os valores independentemente. Ambos concordaram com a conferência local do agente principal, que escreveu os arquivos finais. Não foi utilizado acesso à internet.

A soma dos canais confere com o total: `25000 + 13000 = 38000`. A receita bruta elegível menos os estornos aplicáveis também confere: `43000 - 5000 = 38000`. `answer.json` contém exclusivamente as três chaves solicitadas, com pedidos ordenados e valores inteiros em centavos.

Este fechamento representa a coorte de pagamentos elegíveis, e não o fluxo de caixa de todos os eventos do dia. A apuração se limita aos eventos fornecidos: R2 permanece pendente e R3 não é antecipado para este fechamento. Os arquivos de entrada foram preservados.
