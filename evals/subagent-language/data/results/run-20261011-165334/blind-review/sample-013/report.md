# Diagnóstico do incidente de 7 de outubro

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a 7 nas instâncias ainda não revertidas. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. **Não há perda definitiva confirmada**; a recuperação integral ainda depende de validação.

## Evidências cruzadas

Todos os horários são UTC. Às 14:05, `recibos` passou da versão 7 para a 8, que exige `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada ([mudanca.md](mudanca.md), linhas 3–5). Às 14:06, Q1 apresentou rejeições locais por ausência de `customer_id`; Q2 apresentou o mesmo erro ([operacao.md](operacao.md), linhas 10–11). A sequência temporal e o campo rejeitado correspondem diretamente à mudança de contrato.

Às 14:16, uma instância de `recibos` revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, utilizando o mesmo banco e a mesma rede. As demais instâncias continuam na versão 8 ([mudanca.md](mudanca.md), linhas 5–8). Esse resultado reforça a ligação causal entre a atualização e as rejeições.

O alerta às 14:08 não determina o início do defeito: há rejeições observadas desde 14:06, e o painel agrega filas e arredonda taxas. A alteração visual às 13:40 não mudou a agregação ([operacao.md](operacao.md), linhas 2–3; [mudanca.md](mudanca.md), linha 2).

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura e escrita. A aceitação dos testes após a reversão, com o mesmo banco, também enfraquece essa hipótese. A verificação do banco é pontual e não exclui toda falha transitória, mas não há evidência que sustente C1 como explicação principal ([operacao.md](operacao.md), linhas 4–5; [mudanca.md](mudanca.md), linhas 5–7).
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Esse registro não demonstra falha de DNS em produção. Os testes bem-sucedidos após a reversão, usando a mesma rede, reforçam C2 ([operacao.md](operacao.md), linhas 5–6; [mudanca.md](mudanca.md), linhas 5–7).

Q3, atendida por `notificacoes`, manteve consumo e confirmações normais durante toda a janela; esse consumidor não foi atualizado. Isso reforça a localização do problema em `recibos`. Q4 estava vazia e, portanto, não permite concluir que a versão 8 funcionava corretamente para ela ([operacao.md](operacao.md), linhas 12–13; [mudanca.md](mudanca.md), linha 8).

## Reversão e reprocessamento

Deve-se concluir a reversão das instâncias de `recibos` ainda na versão 8 para a versão 7 e validar uma amostra antes de reprocessar, conforme o procedimento descrito em [mudanca.md](mudanca.md), linhas 13–14. Reverter o produtor não corrige a mudança incompatível introduzida no consumidor e exigiria coordenar clientes que seguem operando normalmente (linhas 3–5 e 12–13).

| Fila | Mensagens afetadas | Decisão e fundamento |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: consumo e confirmações normais. |
| Q4 | 0 | Sem reprocessamento: vazia desde 13:50, sem eventos na janela. |

Fonte: [operacao.md](operacao.md), linhas 8–13. A lista ordenada em `answer.json` é `["Q1", "Q2"]`; ela contém apenas filas efetivamente afetadas. As 42 e 17 mensagens somam 59 mensagens rejeitadas, não uma contagem de tentativas.

Ao reprocessar as mensagens retidas na fila de falhas, preservar os IDs originais e a chave de idempotência por ID de mensagem. Verificar o resultado completo para confirmar a recuperação das 59 mensagens ([operacao.md](operacao.md), linhas 15–19).

## Perda e limites da conclusão

`perda_confirmada` é `false` porque as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível; o produtor continuou publicando ([operacao.md](operacao.md), linhas 15–16). Retenção temporária não constitui perda definitiva.

Ainda não se verificou o resultado de um reprocessamento completo. A aceitação das dez mensagens de teste demonstra compatibilidade na amostra, mas não comprova recuperação integral. Portanto, a ausência de perda confirmada não é uma garantia de recuperação sem validação ([operacao.md](operacao.md), linhas 16–19; [mudanca.md](mudanca.md), linhas 15–16).

Este diagnóstico cruza exclusivamente os dois arquivos de entrada. Nenhuma reversão ou operação de reprocessamento foi executada; essas ações são recomendações fundamentadas nos registros fornecidos.
