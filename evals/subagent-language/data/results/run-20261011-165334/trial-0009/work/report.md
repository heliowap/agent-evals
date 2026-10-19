# Conciliação de vendas de 10 de outubro de 2026

A receita líquida é **38000 centavos (R$ 380,00)**, sendo **25000 centavos em loja** e **13000 centavos em web**. Os pedidos incluídos, em ordem, são **P1, P2, P3 e P8**.

## Critérios e evidências

Foram aplicadas as regras de `regras.md` aos eventos de `eventos.json`. A seleção considera pagamentos em BRL no intervalo UTC **[2026-10-10T00:00:00Z, 2026-10-11T00:00:00Z)**: início inclusivo e fim exclusivo. O instante de criação não determina a inclusão, e o canal utilizado é o do pagamento.

Antes de calcular valores, os 15 registros foram deduplicados por `event_id`, resultando em 13 eventos distintos. **E1 e R1 aparecem duas vezes cada**, com conteúdo idêntico; cada evento foi contado uma única vez. IDs diferentes foram preservados como eventos distintos.

Todos os valores das tabelas estão em centavos.

| Pedido | Pagamento | Instante do pagamento (UTC) | Canal | Bruto | Estornos aplicados | Líquido |
|---|---|---|---|---:|---:|---:|
| P1 | E1 | 2026-10-10T00:00:00Z | web | 10000 | 2000 (R1) | 8000 |
| P2 | E2 | 2026-10-10T09:00:00Z | loja | 25000 | 0 | 25000 |
| P3 | E3 | 2026-10-10T23:59:59Z | web | 5000 | 0 | 5000 |
| P8 | E8 | 2026-10-10T12:00:00Z | loja | 3000 | 3000 (R5) | 0 |
| **Total** | | | | **43000** | **5000** | **38000** |

P1 entra exatamente no início da janela. P3 entra antes do fim. P8 permanece na lista apesar de ter sido integralmente estornado.

## Pedidos excluídos

| Pedido | Evento | Evidência e motivo |
|---|---|---|
| P4 | E4 | Pagamento em 2026-10-11T00:00:00Z, exatamente no limite superior exclusivo; seus 99999 centavos não entram. |
| P5 | E5 | Pagamento em USD; seu valor 8000 não entra e não foi convertido para BRL. |
| P6 | E6 | Há somente um evento `criado`, sem pagamento; seus 7000 centavos não entram. |
| P7 | E7 | Pagamento em 2026-10-09T23:59:59Z, antes do início da janela; seus 12000 centavos não entram. |

## Tratamento dos estornos

| Evento | Pedido | Valor | Instante (UTC) | Decisão |
|---|---|---:|---|---|
| R1 | P1 | 2000 | 2026-10-10T16:00:00Z | Subtraído uma vez: confirmado antes do fim, referente a pedido incluído; a repetição foi descartada. |
| R2 | P2 | 4000 | 2026-10-10T17:00:00Z | Não subtraído: estorno pendente. |
| R3 | P3 | 5000 | 2026-10-11T00:00:00Z | Não subtraído: ocorre exatamente no limite superior e fica para o próximo fechamento, conforme as regras. |
| R4 | P7 | 12000 | 2026-10-10T18:00:00Z | Não subtraído: P7 está fora da coorte, embora o estorno ocorra no dia. |
| R5 | P8 | 3000 | 2026-10-10T20:00:00Z | Subtraído: confirmado antes do fim; zera o líquido de P8 sem remover o pedido. |

## Conferência e ressalvas

| Canal do pagamento | Bruto | Estornos aplicados | Líquido |
|---|---:|---:|---:|
| loja | 28000 | 3000 | 25000 |
| web | 15000 | 2000 | 13000 |
| **Total** | **43000** | **5000** | **38000** |

A conferência fecha em **43000 − 5000 = 38000** e **25000 + 13000 = 38000**, com valores inteiros em centavos. O relatório é por coorte de pagamentos; estornos de pedidos fora dessa coorte não compõem o resultado. Para estornos confirmados, a regra exige instante estritamente anterior ao fim, sem impor o início da janela como limite inferior.

Foram usados exatamente dois subagentes diretos, sem descendentes e sem escrita de arquivos: um analisou a seleção dos pagamentos, e outro conferiu os estornos e os líquidos. Ambos concluíram suas análises antes da geração das entregas. A conferência local do agente principal concordou com os dois resultados. O contrato de `answer.json` contém somente `pedidos_incluidos`, `receita_liquida_centavos` e `por_canal_centavos`, com os canais `loja` e `web`. Os arquivos de entrada foram preservados; toda a análise utilizou ferramentas locais, sem acesso à internet.
