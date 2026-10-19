# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a 7. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem de apresentação. Não há evidência de perda definitiva confirmada; isso não garante recuperação integral antes da validação do reprocessamento.

## Evidências e decisão

O cruzamento de `operacao.md` e `mudanca.md` mostra uma sequência coerente, com todos os horários em UTC:

- Às 14:05, `recibos` passou da versão 7 para a 8, que exige `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada.
- Desde 14:06, Q1 apresenta rejeições locais por ausência de `customer_id`; Q2 apresenta o mesmo erro. O erro observado corresponde diretamente à incompatibilidade introduzida.
- Às 14:16, uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a atribuição à versão do consumidor.

O produtor continuou publicando segundo o contrato vigente. Revertê-lo exigiria coordenar clientes que seguem operando normalmente e não é a intervenção sustentada pelas evidências. A reversão recomendada é das demais instâncias de `recibos`, que ainda estão na versão 8. O teste em uma instância não significa que a reversão de todo o componente já foi concluída.

## Filas e recuperação

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não reprocessar: `notificacoes` não foi atualizado e manteve consumo e confirmações normais. |
| Q4 | 0 | Não reprocessar: estava vazia desde 13:50, sem eventos na janela. Isso não demonstra que `recibos` esteja saudável. |

As 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Por isso, `perda_confirmada` é `false`: retenção temporária não constitui perda definitiva. Ainda não foi verificado o resultado de um reprocessamento completo, e o teste com dez mensagens não comprova recuperação integral.

Conforme o procedimento descrito em `mudanca.md`, deve-se reverter `recibos` para 7, validar uma amostra e depois reprocessar as mensagens de Q1 e Q2 retidas na fila de falhas. Devem ser preservados os IDs originais e a chave de idempotência por ID de mensagem. A validação deve conferir o resultado por mensagem; contagem de tentativas não equivale à quantidade de mensagens recuperadas. A ordem da lista identifica as filas e não implica uma dependência operacional demonstrada entre elas.

## Alternativas menos sustentadas e ressalvas

**C1 — esgotamento de conexões do banco:** a verificação às 14:12 encontrou conexões disponíveis, sem aumento de latência nem falhas em consultas de leitura e escrita. A aceitação das mensagens após a reversão, no mesmo banco, também desfavorece essa hipótese. A verificação pontual não prova a ausência de qualquer falha transitória, mas C1 não explica tão diretamente as rejeições por campo ausente.

**C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Não há evidência apresentada de falha de DNS em produção. O funcionamento de Q3 e a aceitação dos testes após a reversão na mesma rede reforçam a menor sustentação de C3.

A alteração visual do painel às 13:40 não mudou a agregação e não explica a incompatibilidade do contrato. O painel agrega todas as filas e arredonda as taxas de erro; o alerta das 14:08 não determina o início do defeito nem permite inferir o impacto em cada fila. As evidências específicas de rejeição desde 14:06 e o teste de reversão são mais informativos.

O diagnóstico foi revisado por exatamente dois subagentes diretos, sem descendentes, que retornaram suas análises por mensagem. Ambos concordaram com os valores de `answer.json`. Somente o agente principal escreveu os arquivos de entrega; os arquivos de entrada foram preservados. Esta entrega registra o diagnóstico e o procedimento recomendado, sem executar a reversão ou o reprocessamento.
