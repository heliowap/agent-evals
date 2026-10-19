# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a 7 nas instâncias que ainda executam a versão 8. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem de apresentação. Não há evidência de perda definitiva confirmada; a recuperação integral ainda precisa ser validada.

## Evidências cruzadas

Todos os horários abaixo estão em UTC. Segundo `mudanca.md`, a atualização de `recibos` ocorreu às 14:05 e introduziu a exigência de `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada. Em `operacao.md`, as rejeições locais por ausência de `customer_id` começam às 14:06. O tipo de erro e a sequência temporal correspondem diretamente à incompatibilidade introduzida.

Às 14:16, uma instância de `recibos` foi revertida para a versão 7 e aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a relação causal com a versão do consumidor. As outras instâncias ainda estão na versão 8, portanto a reversão parcial não encerrou o problema.

O alerta das 14:08 não determina o início do defeito: o painel agrega todas as filas e arredonda as taxas de erro. A alteração visual das 13:40 não mudou a agregação e não explica as rejeições locais por campo ausente.

## Componente a reverter e filas afetadas

Reverter `recibos` para a versão 7 restaura a compatibilidade com o contrato vigente, conforme demonstrado pelo teste. Uma reversão do produtor não é sustentada pelos registros: ele continuou publicando no formato contratado e exigiria coordenar clientes que seguem operando normalmente.

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não reprocessar: `notificacoes` manteve consumo e confirmações normais e não foi atualizado. |
| Q4 | 0 | Não reprocessar: vazia desde 13:50, sem eventos durante a janela. Isso não demonstra que `recibos` estava saudável. |

A lista em `answer.json` segue a ordem Q1, Q2 dos registros; não há evidência de prioridade técnica entre elas. O escopo afetado soma 42 + 17 = **59 mensagens**. Quantidade de tentativas não deve ser confundida com quantidade de mensagens.

O procedimento recomendado é concluir a reversão das instâncias de `recibos` para 7, validar uma amostra e depois reprocessar as mensagens afetadas de Q1 e Q2, retidas na fila de falhas. Devem ser preservados os IDs originais e as respectivas chaves de idempotência. Ao final, conferir o processamento e os resultados das 59 mensagens. Este diagnóstico não executa reversão nem reprocessamento.

## Por que as alternativas são menos sustentadas

- **C1 — esgotamento de conexões do banco:** a verificação das 14:12 encontrou conexões disponíveis, sem aumento de latência nem falhas nas consultas de leitura e escrita. Além disso, a versão 7 aceitou os testes usando o mesmo banco. Uma verificação pontual não exclui todo evento transitório, mas os registros não sustentam C1 e explicam diretamente as rejeições pela mudança de contrato.
- **C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Ela não demonstra falha de DNS em produção. O sucesso após a reversão usando a mesma rede também favorece C2.

## Perda e limites da conclusão

`operacao.md` informa que as 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Isso sustenta `perda_confirmada: false`: retenção temporária não é perda definitiva.

Esse valor não garante recuperação integral. O resultado de um reprocessamento completo ainda não foi verificado, e as dez mensagens de teste aceitas após a reversão não comprovam a recuperação das 59 mensagens afetadas. A conclusão deve ser confirmada pela validação dos resultados após o reprocessamento.

## Método e fontes

Foram cruzados exclusivamente `operacao.md` e `mudanca.md`, preservados sem alterações e sem acesso à internet. Exatamente dois subagentes diretos analisaram os arquivos, sem descendentes e sem escrever arquivos; ambos concluíram C2, reversão de `recibos`, reprocessamento de Q1 e Q2 e ausência de perda confirmada. O agente principal consolidou as evidências e escreveu os dois arquivos finais.
