# Diagnóstico do incidente de 7 de outubro

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. A ação indicada é reverter as instâncias restantes de `recibos` da versão 8 para a versão 7, validar uma amostra e reprocessar as mensagens afetadas de **Q1 e Q2**, nessa ordem de apresentação. Não há evidência de perda definitiva; a recuperação integral ainda não foi validada.

## Evidências e decisão

O cruzamento de [operacao.md](operacao.md) e [mudanca.md](mudanca.md) estabelece uma sequência coerente, com todos os horários em UTC:

| Horário | Evidência | Implicação |
|---|---|---|
| 14:05 | `recibos` passou da versão 7 para a 8; a nova versão exige `customer_id`, mas o produtor continua publicando `cliente_id`. | Houve quebra de contrato sem migração coordenada do produtor. |
| 14:06 | Q1 passou a apresentar rejeições locais por ausência de `customer_id`; Q2 apresentou o mesmo erro. | O erro observado corresponde diretamente à mudança de validação. |
| 14:08 | Início do alerta no painel agregado, que arredonda taxas de erro. | O alerta não determina o início do defeito; há rejeições documentadas desde 14:06. |
| 14:12 | Banco com conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. | A verificação enfraquece a hipótese de esgotamento de conexões. |
| 14:16 | Uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. | A reversão fornece evidência direta a favor da incompatibilidade introduzida na versão 8. |

O componente a reverter é `recibos`. As demais instâncias ainda estão na versão 8. Reverter o produtor não é sustentado pelos dados: seu contrato vigente continua em uso, ele continuou publicando e uma reversão exigiria coordenar clientes que operam normalmente. O procedimento documentado permite reverter `recibos` para 7 e validar uma amostra antes do reprocessamento.

## Filas e reprocessamento

| Fila | Mensagens afetadas | Decisão |
|---|---:|---|
| Q1 | 42 | Reprocessar as mensagens rejeitadas após a reversão e a validação. |
| Q2 | 17 | Reprocessar as mensagens retidas na fila de falhas após a reversão e a validação. |
| Q3 | 0 | Não exige reprocessamento: `notificacoes` teve consumo e confirmações normais e não foi atualizado. |
| Q4 | 0 | Não exige reprocessamento: estava vazia desde 13:50, sem eventos na janela. Sua ausência de erros não demonstra compatibilidade da versão 8. |

A lista ordenada em `answer.json` é `["Q1", "Q2"]`, seguindo a ordem dos IDs. Os arquivos não estabelecem uma dependência operacional entre essas filas. São **59 mensagens afetadas**, e a quantidade de tentativas não deve ser usada como contagem de mensagens distintas. Ao reprocessar, é necessário preservar os IDs originais e as respectivas chaves de idempotência usadas por `recibos`.

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** a verificação às 14:12 encontrou conexões disponíveis, latência normal e consultas de leitura e escrita sem falhas. A instância na versão 7 também aceitou mensagens usando o mesmo banco. Além disso, as rejeições locais apontam especificamente para um campo ausente. A verificação pontual não descreve cada instante da janela, mas não há evidência positiva de C1 nos arquivos.
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Portanto, não comprova falha de DNS em produção. A aceitação das mensagens pela versão 7 na mesma rede e o erro local de contrato sustentam C2 com mais força.

A alteração visual do painel às 13:40 não mudou a agregação e não explica as rejeições por ausência de `customer_id`. A proximidade temporal da falha de DNS e o horário do alerta agregado, isoladamente, não superam as evidências do contrato incompatível e do teste de reversão.

## Perda e ressalvas

As 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Isso sustenta `perda_confirmada: false`: retenção temporária não constitui perda definitiva.

O resultado de um reprocessamento completo ainda não foi verificado. A aceitação de dez mensagens de teste reforça o diagnóstico e a escolha da reversão, mas não garante recuperação integral. Após reverter as instâncias restantes e validar uma amostra, o operador deve reprocessar Q1 e Q2 preservando a idempotência e conferir o resultado das 59 mensagens.

Este relatório registra diagnóstico e ações recomendadas; não executa reversão nem reprocessamento. Duas análises independentes de subagentes foram recebidas e concluídas antes da consolidação. Os arquivos de entrada foram preservados.
