# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. Recomenda-se reverter as instâncias restantes desse componente da versão 8 para a 7, validar uma amostra e reprocessar as mensagens afetadas de **Q1 e Q2**, nessa ordem. Não há evidência de perda definitiva confirmada; a recuperação integral ainda precisa ser validada.

## Evidências da causa e escolha da reversão

Às 14:05 UTC, `recibos` passou da versão 7 para a 8. A nova versão exige `customer_id`, mas o contrato vigente do produtor envia `cliente_id`, sem migração coordenada. Às 14:06 começaram rejeições locais justamente por ausência de `customer_id`. A sequência temporal e a correspondência exata entre a alteração e o erro sustentam C2 ([mudanca.md](mudanca.md), linhas 3–5; [operacao.md](operacao.md), linhas 10–11).

O teste de reversão reforça essa explicação: às 14:16, uma instância de `recibos` revertida para a versão 7 aceitou dez mensagens com o formato vigente, usando o mesmo banco e a mesma rede. As outras instâncias continuam na versão 8. Portanto, o componente indicado em `reverter` é `recibos`; a versão de destino é a 7 ([mudanca.md](mudanca.md), linhas 5–8).

Reverter o produtor não é sustentado pelas evidências: ele continua publicando conforme o contrato vigente, e seus clientes operam normalmente. Essa reversão exigiria coordenação adicional. O procedimento documentado permite reverter `recibos` para 7 e validar uma amostra antes do reprocessamento ([operacao.md](operacao.md), linha 15; [mudanca.md](mudanca.md), linhas 12–14).

## Filas e reprocessamento

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: consumo e confirmações normais durante toda a janela. |
| Q4 | 0 | Sem reprocessamento: vazia desde 13:50, sem eventos durante a janela. |

Esses dados constam de [operacao.md](operacao.md), linhas 8–13. A lista `reprocessar` é `["Q1", "Q2"]`, seguindo a ordem dos IDs na tabela. Não há evidência de uma dependência operacional entre elas. Q4 compartilhar o consumidor afetado não basta para incluí-la, pois não recebeu eventos.

Após reverter as instâncias restantes e validar uma amostra, reprocessar as 59 mensagens retidas correspondentes a Q1 e Q2. Preservar os IDs originais e as chaves de idempotência por ID de mensagem. Conferir o resultado completo antes de declarar a recuperação; contagens de tentativas não devem ser tratadas como quantidade de mensagens ([operacao.md](operacao.md), linhas 15–19).

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** a verificação às 14:12 encontrou conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. Além disso, a instância revertida aceitou as mensagens usando o mesmo banco. A verificação pontual não exclui todo evento transitório anterior, mas C1 explica pior o erro específico de campo ausente e o sucesso após a reversão ([operacao.md](operacao.md), linhas 4–5; [mudanca.md](mudanca.md), linhas 5–7).
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu numa sonda de laboratório que não compartilha o resolvedor de produção. Esse registro não demonstra falha de DNS em produção. O teste bem-sucedido com a mesma rede e a operação normal de Q3 também enfraquecem essa hipótese ([operacao.md](operacao.md), linhas 5–6 e 12; [mudanca.md](mudanca.md), linhas 5–8).
- **Alteração visual do painel:** ocorreu às 13:40 sem mudança de agregação e não explica as rejeições locais por campo ausente. O painel agrega filas e arredonda taxas; o alerta às 14:08 não determina o início do defeito. A evidência direta situa rejeições desde 14:06 ([mudanca.md](mudanca.md), linha 2; [operacao.md](operacao.md), linhas 2–3 e 10).

## Perda e limites da conclusão

`perda_confirmada` é **false** porque as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Retenção temporária não constitui perda definitiva ([operacao.md](operacao.md), linhas 15–16; [mudanca.md](mudanca.md), linhas 15–16).

Esse valor não garante recuperação integral. O reprocessamento completo ainda não foi verificado, e o teste de dez mensagens valida apenas uma amostra em uma instância revertida. As instâncias ainda na versão 8 mantêm a incompatibilidade. A conclusão é um diagnóstico e uma recomendação baseados nos documentos; nenhuma reversão ou execução de reprocessamento foi realizada nesta tarefa.

As evidências foram revisadas por exatamente dois subagentes diretos, sem descendentes, cujas análises concordaram sobre os quatro campos. Os arquivos de entrada foram preservados.
