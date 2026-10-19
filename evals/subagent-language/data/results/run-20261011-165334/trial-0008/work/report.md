# Conciliação das vendas — fechamento de 10 de outubro de 2026

A receita líquida é **38.000 centavos (R$ 380,00)**, distribuída em **25.000 centavos na loja** e **13.000 centavos na web**. Os pedidos incluídos, em ordem, são **P1, P2, P3 e P8**.

## Critérios e deduplicação

Foram aplicadas as regras de `regras.md` aos registros de `eventos.json`. A coorte inclui pagamentos em BRL ocorridos no intervalo UTC `[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)`: o início entra e o limite superior fica fora. A data de criação não determina a inclusão e seu valor não compõe a receita. Não houve conversão de moeda.

Antes de calcular qualquer valor, os 15 registros foram reduzidos a 13 eventos únicos por `event_id`. E1 e R1 aparecem duas vezes cada, com conteúdo idêntico; uma cópia de cada foi descartada. Assim, o pagamento E1 de 10.000 centavos e o estorno R1 de 2.000 centavos foram contados uma única vez. IDs diferentes foram mantidos como eventos distintos; não há duplicatas conflitantes nos dados.

## Pedidos incluídos e evidências

Todos os valores da tabela estão em centavos. O canal é o do pagamento, inclusive para atribuir os abatimentos.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estorno aplicado | Líquido |
| --- | --- | --- | --- | ---: | ---: | ---: |
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |

O bruto é `10000 + 25000 + 5000 + 3000 = 43000`. Os estornos aplicáveis somam `2000 + 3000 = 5000`. Portanto, o líquido é `43000 - 5000 = 38000`.

Por canal: loja = `25000 + 0 = 25000`; web = `8000 + 5000 = 13000`. A soma dos canais coincide com a receita líquida total.

## Pedidos excluídos

| Pedido / evento | Evidência e motivo |
| --- | --- |
| P4 / E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior excluído. Seus 99999 centavos não entram. |
| P5 / E5 | Pagamento em USD. Seus 8000 centavos não entram, sem conversão para BRL. |
| P6 / E6 | Evento `criado`, sem pagamento registrado. Seus 7000 centavos não entram. |
| P7 / E7 | Pagamento em 2026-10-09T23:59:59Z, antes do início da janela. Seus 12000 centavos não entram. |

## Tratamento dos estornos

| Evento | Pedido | Valor (centavos) | Decisão e evidência |
| --- | --- | ---: | --- |
| R1 | P1 | 2000 | Aplicado uma vez: confirmado em 2026-10-10T16:00:00Z, antes do limite superior. Estorno parcial; P1 fica com 8000. |
| R2 | P2 | 4000 | Excluído por estar pendente, mesmo tendo ocorrido antes do limite superior. |
| R3 | P3 | 5000 | Excluído deste fechamento: confirmado em 2026-10-11T00:00:00Z, exatamente no limite superior. Fica para o próximo fechamento conforme as regras; P3 mantém 5000 neste relatório. |
| R4 | P7 | 12000 | Excluído porque P7 foi pago fora da janela, embora o estorno tenha sido confirmado em 2026-10-10T18:00:00Z. |
| R5 | P8 | 3000 | Aplicado: confirmado em 2026-10-10T20:00:00Z. O estorno integral deixa P8 com líquido zero, mantendo-o na lista de incluídos. |

## Ressalvas e validação

O fechamento é por coorte de pagamentos, não por fluxo de caixa de todos os eventos do dia. Para estornos confirmados de pedidos incluídos, a regra exige somente que ocorram estritamente antes do limite superior; não foi imposto um limite inferior adicional.

Os estornos não informam moeda ou canal. Foram associados pelo campo `pedido` ao pagamento incluído, usando o canal desse pagamento. Há um único pagamento elegível por pedido neste arquivo, sem ambiguidade nessa associação. Os cálculos usam inteiros em centavos.

Dois subagentes diretos fizeram a conferência de valores e a auditoria das regras, sem criar descendentes nem escrever arquivos. Ambos concluíram suas análises e concordaram com o resultado. O agente principal também recalculou os valores localmente e validou o contrato de `answer.json`: exatamente as três chaves solicitadas, lista ordenada, receita inteira e objeto por canal com `loja` e `web`. Os arquivos de entrada foram preservados, com integridade conferida por SHA-256. Foram utilizadas somente ferramentas locais, sem acesso à internet.
