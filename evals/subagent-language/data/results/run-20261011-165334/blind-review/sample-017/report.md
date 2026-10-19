# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a 7 nas instâncias que ainda executam a versão 8. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. Não há evidência de perda definitiva confirmada.

## Evidências e cronologia

O cruzamento de [mudanca.md](mudanca.md) com [operacao.md](operacao.md) conecta a alteração de contrato às rejeições observadas. Todos os horários são UTC.

| Horário | Evidência | Implicação |
|---|---|---|
| 13:40 | Alteração visual do painel, sem mudança de agregação. | Não explica as rejeições locais do consumidor. |
| 14:04 | Falha de DNS em uma sonda de laboratório com resolvedor distinto do de produção. | Não demonstra indisponibilidade de DNS em produção. |
| 14:05 | `recibos` passou da versão 7 para a 8, que exige `customer_id`; o produtor continua publicando `cliente_id`, conforme o contrato vigente, sem migração coordenada. | Há uma incompatibilidade concreta entre produtor e consumidor. |
| 14:06 | Q1 apresenta rejeições locais por ausência de `customer_id`; Q2 registra o mesmo erro. | O erro observado corresponde diretamente à nova exigência da versão 8. |
| 14:08 | Início do alerta no painel, que agrega filas e arredonda taxas. | O horário do alerta não determina o início do defeito nem quais filas foram afetadas. |
| 14:12 | Banco com conexões disponíveis, sem aumento de latência ou falhas de leitura e escrita. | Enfraquece a hipótese de esgotamento de conexões. |
| 14:16 | Uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. | A reversão fornece evidência adicional de que a versão do consumidor explica a falha. |

## Decisões de recuperação

Deve-se reverter **`recibos` para a versão 7** nas demais instâncias e validar uma amostra antes de reprocessar, conforme o procedimento descrito em `mudanca.md`. A amostra de dez mensagens já aceita sustenta essa escolha, mas não comprova a recuperação das 59 mensagens afetadas. Reverter o produtor não é sustentado pelas evidências: ele segue o contrato vigente e uma reversão exigiria coordenar clientes que continuam operando normalmente.

| Fila | Mensagens afetadas | Decisão e justificativa |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não reprocessar: `notificacoes` manteve consumo e confirmações normais e não foi atualizado. |
| Q4 | 0 | Não reprocessar: vazia desde 13:50, sem eventos na janela. Isso não comprova compatibilidade da versão 8, apenas ausência de mensagens afetadas nessa fila. |

A lista ordenada em `answer.json` é `["Q1", "Q2"]`, seguindo a ordem dos IDs. As mensagens rejeitadas dessas filas devem ser recuperadas da fila de falhas após a validação. Preservar os IDs originais e a chave de idempotência por ID de mensagem é necessário durante o reprocessamento. As 42 + 17 mensagens totalizam **59 mensagens**, sem confundir esse total com contagens de tentativas.

## Hipóteses alternativas

**C1 — esgotamento de conexões do banco:** é menos sustentada porque a verificação às 14:12 mostrou conexões disponíveis e operações normais. Além disso, o erro é uma rejeição local por campo ausente, e a versão 7 aceitou mensagens usando o mesmo banco. A verificação pontual não exclui toda falha transitória possível, mas os arquivos não apresentam evidência de que uma falha desse tipo explique o incidente.

**C3 — indisponibilidade de DNS em produção:** é menos sustentada porque a única falha de DNS registrada ocorreu em laboratório, com outro resolvedor. O teste com a versão 7 funcionou na mesma rede, e Q3 operou normalmente durante toda a janela. A proximidade temporal da falha da sonda não estabelece uma causa em produção.

## Perda e ressalvas

`perda_confirmada` é **`false`** porque as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível (`operacao.md`). Retenção temporária não equivale a perda definitiva.

O resultado de um reprocessamento completo ainda não foi verificado. Portanto, a ausência de perda confirmada não garante recuperação integral: é preciso validar os resultados após o reprocessamento antes de declarar o incidente totalmente recuperado. Este diagnóstico se limita às evidências dos dois arquivos; nenhuma reversão ou operação de reprocessamento foi executada.

## Revisão das análises

Dois subagentes diretos analisaram os arquivos sem modificá-los: um com foco operacional e outro com foco na mudança e nas hipóteses alternativas. Ambos concluíram suas análises e retornaram a mesma decisão para as quatro chaves do contrato. Os arquivos finais foram escritos somente pelo agente principal, preservando os arquivos de entrada.
