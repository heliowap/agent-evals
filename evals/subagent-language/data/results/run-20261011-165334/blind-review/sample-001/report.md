# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. Deve-se reverter esse componente da versão 8 para a versão 7 nas instâncias que ainda estão na versão 8. As filas que exigem reprocessamento são **Q1 e Q2**. Não há evidência de perda definitiva confirmada; a recuperação integral ainda precisa ser validada.

## Evidências da causa e da reversão

Às 14:05 UTC, `recibos` passou da versão 7 para a 8 e começou a exigir `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada. Às 14:06, Q1 começou a apresentar rejeições locais por ausência de `customer_id`; Q2 apresentou o mesmo erro. A sequência temporal e a correspondência exata entre a mudança de campo e o erro sustentam C2 ([mudanca.md](mudanca.md), linhas 3–5; [operacao.md](operacao.md), linhas 10–11).

Às 14:16, uma instância de `recibos` revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a relação entre a versão do consumidor e as rejeições, embora valide apenas uma amostra em uma instância. As demais instâncias ainda estão na versão 8 ([mudanca.md](mudanca.md), linhas 5–8).

O componente a reverter é `recibos`: o produtor continua publicando de acordo com o contrato vigente, e reverter o produtor exigiria coordenar clientes que operam normalmente. O procedimento documentado permite voltar `recibos` para a versão 7 e validar uma amostra antes do reprocessamento ([mudanca.md](mudanca.md), linhas 12–14).

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas nas consultas de leitura e escrita. A amostra também funcionou após a reversão usando o mesmo banco. Essas evidências favorecem a incompatibilidade do consumidor; a verificação pontual do banco, isoladamente, não prova sua condição em todos os instantes ([operacao.md](operacao.md), linhas 4–5; [mudanca.md](mudanca.md), linhas 5–7).
- **C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Portanto, ela não demonstra falha de DNS em produção. O sucesso da amostra com a mesma rede e a operação normal de `notificacoes` também tornam essa hipótese menos sustentada ([operacao.md](operacao.md), linhas 5–6 e 12; [mudanca.md](mudanca.md), linhas 5–8).
- **Alteração visual do painel:** a mudança das 13:40 não alterou a agregação. O painel agrega todas as filas e arredonda taxas; o alerta das 14:08 não determina o início do defeito nem identifica sozinho as filas afetadas ([mudanca.md](mudanca.md), linha 2; [operacao.md](operacao.md), linhas 2–3).

## Filas e recuperação

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por `customer_id` ausente. |
| Q2 | 17 | Reprocessar: mesmo erro e mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: consumo e confirmações normais em `notificacoes`, que não foi atualizado. |
| Q4 | 0 | Sem reprocessamento: vazia desde 13:50, sem eventos durante a janela. |

A lista ordenada é `["Q1", "Q2"]`, seguindo a ordem do registro; não há prioridade operacional adicional documentada. Q4 compartilha o consumidor afetado, mas não contém mensagens afetadas, e sua ausência de erros não demonstra que a versão 8 esteja funcionando ([operacao.md](operacao.md), linhas 10–13).

A recuperação indicada pelos documentos é:

1. Reverter as instâncias restantes de `recibos` para a versão 7.
2. Validar uma amostra com o formato vigente antes de reprocessar.
3. Reprocessar as mensagens retidas correspondentes a Q1 e Q2, preservando os IDs originais, os payloads e a chave de idempotência por ID de mensagem.
4. Conferir o resultado de todas as 59 mensagens e eventuais rejeições remanescentes, contando mensagens distintas separadamente das tentativas.

## Perda e limites da conclusão

As **59 mensagens rejeitadas (42 + 17)** estão íntegras na fila de falhas, com IDs originais e payload disponível. Isso sustenta `perda_confirmada: false`: a retenção temporária observada não constitui perda definitiva. O resultado de um reprocessamento completo ainda não foi verificado, portanto não há garantia de recuperação integral ([operacao.md](operacao.md), linhas 15–19; [mudanca.md](mudanca.md), linhas 15–16).

As dez mensagens de teste aceitas demonstram o sucesso da amostra após a reversão. Os documentos não dizem que elas pertenciam às 59 rejeitadas ou que foram removidas desse conjunto; não é possível descontá-las para concluir que restam 49 mensagens.

Este diagnóstico utiliza somente `operacao.md` e `mudanca.md`. Duas análises independentes foram recebidas e concluídas antes da consolidação: uma sobre causa e alternativas, outra sobre filas e recuperação. Os arquivos de entrada foram preservados. Não foram executados reversão ou reprocessamento em sistemas operacionais.
