A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a versão 7 nas instâncias que ainda executam a versão 8. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. Não há evidência de perda definitiva confirmada; por isso, `perda_confirmada` é `false`.

O cruzamento de `operacao.md` e `mudanca.md` estabelece uma sequência coerente, com horários em UTC: às 14:05, `recibos` passou para a versão 8, que exige `customer_id`; o contrato vigente do produtor publica `cliente_id`, sem migração coordenada. Desde 14:06, Q1 apresentou rejeições locais por ausência de `customer_id`, e Q2 apresentou o mesmo erro. Às 14:16, uma instância revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. A incompatibilidade explícita do contrato, o tipo de rejeição e o resultado da reversão sustentam C2 além da simples proximidade temporal.

**C1 — esgotamento de conexões do banco** é menos sustentada: a verificação às 14:12 encontrou conexões disponíveis, sem aumento de latência nem falhas nas consultas de leitura e escrita. As rejeições observadas são locais e identificam um campo ausente. Essa verificação não demonstra o estado do banco em cada instante da janela, mas não há evidência apresentada que sustente C1 como causa do incidente.

**C3 — indisponibilidade de DNS em produção** também é menos sustentada: a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Ela não comprova falha de DNS em produção. O consumo normal de `notificacoes` e a aceitação das mensagens após a reversão, com a mesma rede, reforçam o diagnóstico de incompatibilidade em `recibos`.

Reverter o produtor não é sustentado pelos registros: ele continuou publicando conforme o contrato vigente, e uma reversão exigiria coordenar clientes que operam normalmente. O procedimento documentado permite reverter `recibos` para 7 e validar uma amostra antes de reprocessar as filas afetadas. Como apenas uma instância foi revertida, ainda é necessário reverter as demais instâncias na versão 8 antes de prosseguir.

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não exige reprocessamento: consumo e confirmações normais durante toda a janela; `notificacoes` não foi atualizado. |
| Q4 | 0 | Não exige reprocessamento: vazia desde 13:50, sem eventos na janela. Isso não comprova compatibilidade de `recibos`, pois não houve mensagens para exercitá-lo. |

As **59 mensagens rejeitadas** estão íntegras na fila de falhas, com IDs originais e payload disponível. Essa retenção temporária não caracteriza perda definitiva. Contudo, ainda não foi verificado o resultado de um reprocessamento completo: a amostra de dez mensagens aceitas não garante recuperação integral das 59. Ao reprocessar Q1 e Q2, devem ser preservados os IDs originais e a chave de idempotência por ID de mensagem usada por `recibos`. A validação final deve conferir o resultado de cada mensagem e distinguir a quantidade de mensagens da contagem de tentativas.

O início do alerta às 14:08 não determina o início do defeito. O painel agrega todas as filas e arredonda as taxas de erro; por isso, as evidências por fila são mais úteis para delimitar o impacto. A alteração visual às 13:40 não mudou a agregação e não explica a incompatibilidade de campos nem as rejeições locais.

A análise usou somente os dois arquivos de entrada e ferramentas locais. Exatamente dois subagentes diretos, sem descendentes, analisaram causa/reversão e filas/perda, respectivamente, e retornaram suas conclusões por mensagem. Ambos concluíram antes da redação dos arquivos finais pelo agente principal. Os arquivos de entrada foram preservados.
