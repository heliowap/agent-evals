# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a versão 7 nas instâncias que ainda executam a versão 8. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. **Não há evidência de perda definitiva confirmada**, mas a recuperação integral ainda depende da validação do reprocessamento.

## Evidências cruzadas

Segundo [mudanca.md](mudanca.md), às 14:05 UTC o consumidor `recibos` passou da versão 7 para a 8 e começou a exigir `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada. Em [operacao.md](operacao.md), as rejeições locais por ausência de `customer_id` aparecem desde 14:06 UTC, logo após essa atualização. O produtor continuou publicando.

O teste de reversão reforça o diagnóstico: às 14:16 UTC, uma instância de `recibos` voltou à versão 7 e aceitou dez mensagens no formato vigente, usando o mesmo banco e a mesma rede. Essa mudança isolada, junto ao erro específico de campo ausente, sustenta a incompatibilidade como causa. As demais instâncias ainda estão na versão 8.

O alerta às 14:08 UTC não deve ser tratado como início do defeito: o painel agrega todas as filas e arredonda as taxas de erro. A alteração visual às 13:40 UTC não mudou a agregação e não explica as rejeições locais.

## Filas e recuperação

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por `customer_id` ausente desde 14:06 UTC. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não requer reprocessamento: consumo e confirmações normais durante toda a janela; `notificacoes` não foi atualizado. |
| Q4 | 0 | Não requer reprocessamento: vazia desde 13:50 UTC, sem eventos na janela. Sua ausência de erros não comprova compatibilidade de `recibos`. |

Há **59 mensagens afetadas**, correspondentes a 42 de Q1 e 17 de Q2. A contagem de tentativas não deve ser usada como quantidade de mensagens. Todas as 59 rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível.

O procedimento sustentado pelos documentos é reverter as instâncias restantes de `recibos` para a versão 7, validar uma amostra e então reprocessar as mensagens afetadas de Q1 e Q2. Ao reprocessar, preservar os IDs originais e as chaves de idempotência por ID de mensagem. Este relatório recomenda essas ações; não executa reversão nem reprocessamento.

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 UTC havia conexões disponíveis, sem aumento de latência ou falhas de leitura e escrita. O teste bem-sucedido após a reversão usou o mesmo banco. Esses dados não sustentam esgotamento como explicação das rejeições por campo ausente.
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 UTC ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Não há evidência apresentada de falha de DNS em produção, e o teste após a reversão funcionou na mesma rede.
- **Reverter o produtor:** a mudança incompatível ocorreu no consumidor. O produtor segue o contrato vigente, e sua reversão exigiria coordenar clientes que continuam operando normalmente. A reversão de `recibos` tem apoio direto no teste e no procedimento operacional.

## Ressalvas

`perda_confirmada` é `false` porque os documentos demonstram retenção íntegra das mensagens, não perda definitiva. Isso não garante recuperação integral: ainda não foi verificado o resultado de um reprocessamento completo, e o teste de dez mensagens cobre apenas uma amostra em uma instância revertida. O diagnóstico é o mais sustentado pelas evidências disponíveis; as verificações de banco e rede não constituem prova de ausência de qualquer falha transitória em toda a janela.

A análise foi dividida entre exatamente dois subagentes diretos, sem descendentes: um avaliou a causa e a reversão; o outro avaliou as filas, a perda e os cuidados de recuperação. Ambos retornaram suas análises por mensagem e concluíram antes da redação destes arquivos pelo agente principal. Os arquivos de entrada foram preservados.
