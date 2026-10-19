# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente indicado para reversão é `recibos`, levando as instâncias que ainda estão na versão 8 de volta à versão 7. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem na lista de saída. Não há evidência de perda definitiva: `perda_confirmada` é `false`.

## Evidências cruzadas

Segundo [mudanca.md](mudanca.md), às 14:05 UTC o consumidor `recibos` foi atualizado da versão 7 para a 8. A nova versão exige `customer_id`, enquanto o contrato vigente do produtor publica `cliente_id`; não houve migração coordenada. Segundo [operacao.md](operacao.md), Q1 começou a apresentar rejeições locais por ausência de `customer_id` às 14:06, e Q2 apresentou o mesmo erro. A sequência temporal e a correspondência exata do campo rejeitado sustentam C2.

Às 14:16, uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a relação entre a versão do consumidor e as rejeições. As outras instâncias permanecem na versão 8; o teste não demonstra recuperação completa.

O alerta das 14:08 não estabelece o início do defeito: o painel agrega filas e arredonda taxas. A alteração visual das 13:40 não mudou a agregação e não explica as rejeições locais.

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. A aceitação pela versão 7 no mesmo banco também enfraquece essa hipótese. A verificação pontual não descreve cada instante da janela, mas não há evidência apresentada que sustente C1.
- **C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório com resolvedor diferente do de produção. Ela não demonstra indisponibilidade em produção. A versão 7 aceitou os testes na mesma rede, e `notificacoes` manteve consumo e confirmações normais.

## Reversão e reprocessamento

Reverter as instâncias restantes de `recibos` para a versão 7 e validar uma amostra com o contrato vigente antes de reprocessar, conforme o procedimento descrito em `mudanca.md`. A reversão do produtor não é sustentada: ele continuou publicando conforme seu contrato, e alterá-lo exigiria coordenar clientes que operam normalmente.

| Fila | Mensagens afetadas | Decisão e fundamento |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: consumo e confirmações normais em `notificacoes`, que não foi atualizado. |
| Q4 | 0 | Sem reprocessamento: vazia desde 13:50 e sem eventos na janela. Compartilhar o consumidor não demonstra mensagens afetadas; sua ausência de erros também não valida a versão 8. |

A lista ordenada de IDs é `["Q1", "Q2"]`; os documentos não estabelecem prioridade operacional entre essas filas. Reprocessar as mensagens retidas correspondentes a elas, preservando os IDs originais e a chave de idempotência por ID usada por `recibos`. São 59 mensagens afetadas (42 + 17); a contagem de tentativas não deve ser usada como contagem de mensagens.

## Perda e ressalvas

`operacao.md` informa que as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Essa retenção temporária não constitui perda definitiva e sustenta `perda_confirmada: false`.

O resultado de um reprocessamento completo ainda não foi verificado. A ausência de perda confirmada não garante recuperação integral: após a reversão e a validação da amostra, é necessário conferir o processamento e as confirmações das 59 mensagens, preservando a idempotência.

## Escopo da análise

Foram usados somente `operacao.md` e `mudanca.md`, com ferramentas locais. Exatamente dois subagentes diretos, sem descendentes, retornaram análises por mensagem e concluíram suas tarefas antes da consolidação. Apenas o agente principal escreveu os arquivos finais. Os documentos de entrada foram preservados. Este relatório recomenda ações operacionais; a reversão e o reprocessamento não foram executados nesta tarefa.
