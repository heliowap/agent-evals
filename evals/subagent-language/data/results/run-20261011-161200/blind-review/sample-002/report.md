# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, retornando as instâncias ainda na versão 8 à versão 7. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem na resposta. Não há evidência de perda definitiva confirmada.

## Evidências cruzadas

Segundo [mudanca.md](mudanca.md), às 14:05 UTC o consumidor `recibos` passou da versão 7 para a 8, que exige `customer_id`. O contrato vigente do produtor fornece `cliente_id`, e não houve migração coordenada. Segundo [operacao.md](operacao.md), Q1 registra rejeições locais por ausência de `customer_id` desde 14:06; Q2 apresenta o mesmo erro. Assim, a mudança antecede as rejeições documentadas e explica diretamente a falha observada.

Às 14:16, uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a incompatibilidade da versão 8 como causa. A amostra é limitada: não comprova recuperação integral nem resolve as outras instâncias que permanecem na versão 8.

## Reversão e reprocessamento

Reverter as instâncias restantes de `recibos` para a versão 7, validar uma amostra e, em seguida, reprocessar as mensagens afetadas de Q1 e Q2 retidas na fila de falhas. Essa sequência segue o procedimento descrito em `mudanca.md`. O produtor continua publicando conforme o contrato vigente; revertê-lo exigiria coordenar clientes que operam normalmente e não é a correção sustentada pelas evidências.

| Fila | Evidência operacional | Decisão |
|---|---|---|
| Q1 | 42 mensagens rejeitadas por ausência de `customer_id` | Reprocessar as mensagens afetadas |
| Q2 | 17 mensagens com o mesmo erro, retidas na fila de falhas | Reprocessar as mensagens afetadas |
| Q3 | Nenhuma mensagem afetada; consumo e confirmações normais em `notificacoes`, que não foi atualizado | Sem reprocessamento indicado |
| Q4 | Vazia desde 13:50, sem eventos durante a janela | Sem mensagens a reprocessar; não permite avaliar o funcionamento do consumidor |

As 59 mensagens distintas afetadas (42 + 17) estão íntegras na fila de falhas, com IDs originais e payload disponível. Preservar os IDs e as chaves de idempotência de `recibos` durante o reprocessamento e conferir o resultado por mensagem. Contagens de tentativas não equivalem à quantidade de mensagens.

## Por que as alternativas são menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. A aceitação das mensagens pela versão 7 usando o mesmo banco também enfraquece essa hipótese. A verificação pontual não exclui, sozinha, um episódio transitório anterior, mas C1 não explica tão diretamente as rejeições locais pelo campo ausente nem o resultado da reversão.
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu numa sonda de laboratório que usa outro resolvedor. Ela não demonstra falha de DNS em produção. O teste bem-sucedido após a reversão, mantendo a mesma rede, favorece C2. A proximidade temporal da falha de laboratório não basta para atribuir causalidade.

A alteração visual do painel às 13:40 não mudou a agregação e não fornece explicação para as rejeições. O painel agrega filas e arredonda taxas; o alerta às 14:08 não determina o início do defeito. O primeiro registro de rejeição informado em Q1 é às 14:06, sem provar que esse seja o instante exato de início de todo o incidente.

## Perda e ressalvas

`perda_confirmada: false` significa que **não há perda definitiva confirmada**: as mensagens rejeitadas permanecem disponíveis e íntegras. Retenção temporária não deve ser classificada como perda definitiva. Esse valor não garante recuperação integral, pois o resultado de um reprocessamento completo ainda não foi verificado.

Este diagnóstico cruza somente os dois arquivos de entrada. Dois subagentes diretos, sem descendentes, analisaram respectivamente a operação e a causalidade da mudança; ambos concordaram com os valores de `answer.json`. Apenas o agente principal escreveu os arquivos finais. Não foram executadas reversões nem reprocessamentos reais.
