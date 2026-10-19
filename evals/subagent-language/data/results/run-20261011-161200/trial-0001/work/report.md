# Diagnóstico do incidente de 7 de outubro

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. Recomenda-se reverter as instâncias desse componente que ainda estão na versão 8 para a versão 7, validar uma amostra e reprocessar **Q1 e Q2**, nessa ordem de IDs. As 59 mensagens afetadas estão íntegras e retidas; **não há perda definitiva confirmada**, mas a recuperação integral ainda precisa ser validada.

## Evidências cruzadas e decisão de reversão

Todos os horários são UTC. As referências abaixo apontam para os dois arquivos de entrada.

| Evidência | Fonte | Implicação |
|---|---|---|
| Às 14:05, `recibos` passou da versão 7 para a 8 e começou a exigir `customer_id`; o produtor continua publicando `cliente_id`, conforme o contrato vigente, sem migração coordenada. | [mudanca.md](mudanca.md), linhas 3–5 | Há uma incompatibilidade explícita entre o consumidor atualizado e as mensagens produzidas. |
| Q1 registra rejeições locais por ausência de `customer_id` desde 14:06; Q2 registra o mesmo erro. Ambas usam `recibos`. | [operacao.md](operacao.md), linhas 10–11 | O erro observado corresponde exatamente à exigência introduzida pela atualização e aparece logo depois dela. |
| Às 14:16, uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. As demais instâncias permanecem na versão 8. | [mudanca.md](mudanca.md), linhas 5–8 | A reversão fornece evidência adicional de que a versão do consumidor explica as rejeições. |
| `notificacoes` não foi atualizado e Q3 manteve consumo e confirmações normais durante toda a janela. | [mudanca.md](mudanca.md), linha 8; [operacao.md](operacao.md), linha 12 | O comportamento é coerente com uma falha concentrada no consumidor alterado. |

O componente a reverter é **`recibos`**. O produtor segue o contrato vigente e continuou publicando; seus clientes operam normalmente. Revertê-lo exigiria coordenação e não é a correção sustentada pelos documentos. O procedimento registrado permite reverter `recibos` para 7 e validar uma amostra antes do reprocessamento ([mudanca.md](mudanca.md), linhas 12–14).

## Por que as alternativas são menos sustentadas

- **C1 — esgotamento de conexões do banco:** a verificação às 14:12 encontrou conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita ([operacao.md](operacao.md), linhas 4–5). Além disso, a versão 7 aceitou os testes usando o mesmo banco. A verificação pontual não prova o estado do banco em cada instante, mas não há evidência positiva de esgotamento nem uma explicação melhor para as rejeições locais por campo ausente.
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção ([operacao.md](operacao.md), linhas 5–6). Portanto, esse registro não demonstra falha de DNS em produção. O funcionamento de Q3 e os testes aceitos pela versão 7 na mesma rede também enfraquecem essa hipótese.

A alteração visual do painel às 13:40 não mudou a agregação ([mudanca.md](mudanca.md), linha 2). O painel agrega todas as filas e arredonda as taxas; o alerta às 14:08 não determina o início do defeito ([operacao.md](operacao.md), linhas 2–3). Para o diagnóstico, a sequência atualização às 14:05 → rejeições desde 14:06 é mais informativa que o horário do alerta.

## Filas e reprocessamento

| Fila | Mensagens afetadas | Decisão e justificativa |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por `customer_id` ausente. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Excluir: consumo e confirmações normais durante toda a janela. |
| Q4 | 0 | Excluir: vazia desde 13:50, sem eventos durante a janela. |

Fonte: [operacao.md](operacao.md), linhas 8–19. Q4 usar `recibos` não basta para incluí-la: não houve mensagens afetadas. Sua ausência de erros também não comprova compatibilidade, pois não houve eventos para testar o consumidor.

A lista ordenada de IDs de filas em `answer.json` é `["Q1", "Q2"]`. O total a recuperar é de **59 mensagens distintas** (42 + 17), sem confundir contagens de tentativas com mensagens. Após reverter as instâncias restantes e validar uma amostra, reprocessar as mensagens dessas filas retidas na fila de falhas, preservando os IDs originais e a chave de idempotência por ID de mensagem. Em seguida, verificar o resultado completo das 59 mensagens.

## Perda e limites da conclusão

`perda_confirmada` é **`false`** porque as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível ([operacao.md](operacao.md), linhas 15–19). Essa retenção temporária não constitui evidência de perda definitiva.

Ainda não foi verificado o resultado de um reprocessamento completo. Os dez testes aceitos após a reversão sustentam a compatibilidade da versão 7 com o formato vigente, mas não comprovam a recuperação de todas as mensagens nem a reversão das instâncias restantes. Assim, ausência de perda confirmada não equivale a garantia de recuperação integral ([mudanca.md](mudanca.md), linhas 15–16).

## Método

Foram consultados exclusivamente `operacao.md` e `mudanca.md`, com ferramentas locais. Dois subagentes diretos, sem descendentes, analisaram respectivamente causa/reversão e filas/perda; ambos concluíram suas análises antes da redação final e concordaram nas quatro decisões do contrato. Os arquivos de entrada foram preservados.
