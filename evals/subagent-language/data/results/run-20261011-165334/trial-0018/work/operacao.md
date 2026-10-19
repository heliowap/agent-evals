# Operação de 7 de outubro
O painel agrega todas as filas e arredonda as taxas de erro. O início do alerta,
às 14:08 UTC, não é necessariamente o início do defeito. Todos os horários abaixo
estão em UTC. O banco foi verificado às 14:12: conexões disponíveis, sem aumento
de latência nem falhas nas consultas de leitura e escrita. Às 14:04 houve uma
falha de DNS em uma sonda de laboratório, que não compartilha o resolvedor de produção.

| Fila | Consumidor | Mensagens afetadas | Evidência |
|---|---|---|---|
| Q1 | recibos | 42 | rejeições locais com campo customer_id ausente desde 14:06 |
| Q2 | recibos | 17 | mesmo erro; mensagens retidas na fila de falhas |
| Q3 | notificacoes | 0 | consumo e confirmações normais durante toda a janela |
| Q4 | recibos | 0 | vazia desde 13:50; nenhum evento durante a janela |

O produtor continuou publicando. As 59 mensagens rejeitadas estão íntegras na
fila de falhas, com IDs originais e payload disponível. Não se verificou ainda
o resultado de um reprocessamento completo. Contagem de tentativas não deve
ser confundida com quantidade de mensagens. Os recibos usam uma chave de
idempotência por ID de mensagem; o operador deve preservá-la ao reprocessar.
