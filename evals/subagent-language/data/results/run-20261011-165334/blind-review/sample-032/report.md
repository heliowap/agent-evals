# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a versão 7. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. **Não há evidência de perda definitiva confirmada**, mas a recuperação integral ainda não foi validada.

## Evidências da causa e da reversão

Segundo `mudanca.md`, às 14:05 UTC `recibos` passou da versão 7 para a 8, que exige `customer_id`. O contrato vigente do produtor publica `cliente_id`, e não houve migração coordenada. Segundo `operacao.md`, Q1 e Q2 apresentaram rejeições locais por ausência de `customer_id`, com início registrado às 14:06. A sequência temporal e o erro específico correspondem à incompatibilidade introduzida.

Às 14:16, uma instância de `recibos` revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede (`mudanca.md`). Esse teste reforça a relação causal e sustenta reverter as instâncias que ainda estão na versão 8. O produtor continuou publicando conforme seu contrato; sua reversão exigiria coordenar clientes que continuam operando normalmente.

## Filas e recuperação

| Fila | Mensagens afetadas | Decisão e evidência em `operacao.md` |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por `customer_id` ausente. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Não incluir: `notificacoes` manteve consumo e confirmações normais. |
| Q4 | 0 | Não incluir: estava vazia desde 13:50, sem eventos na janela. Compartilhar o consumidor não comprova mensagens afetadas; tampouco sua ausência de erros demonstra que `recibos` estava saudável. |

As 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Essa retenção temporária sustenta `perda_confirmada: false`. O valor expressa ausência de perda confirmada, sem garantir recuperação integral: ainda não foi verificado o resultado de um reprocessamento completo.

O procedimento sustentado pelos arquivos é reverter `recibos` para a versão 7, validar uma amostra e então reprocessar as mensagens afetadas de Q1 e Q2 a partir da fila de falhas. É necessário preservar os IDs e a chave de idempotência por ID de mensagem. A validação final deve conferir os resultados das mensagens únicas, sem confundir quantidade de tentativas com quantidade de mensagens. Este relatório recomenda essas ações; não as executa.

## Alternativas menos sustentadas e limites

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita (`operacao.md`). O teste bem-sucedido com a versão 7 usou o mesmo banco. Esses dados enfraquecem C1, embora uma verificação pontual não descreva cada instante da janela.
- **C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção (`operacao.md`). Portanto, ela não demonstra falha de DNS em produção. Q3 operou normalmente, e o teste com a versão 7 usou a mesma rede, reforçando o diagnóstico de incompatibilidade.
- **Painel e horário do alerta:** a alteração visual das 13:40 não mudou a agregação (`mudanca.md`). O painel agrega filas e arredonda taxas; o alerta das 14:08 não determina o início do defeito (`operacao.md`). As rejeições específicas das 14:06 fornecem evidência mais direta.

O sucesso das dez mensagens de teste sustenta a reversão, mas não substitui a validação de todas as mensagens afetadas. As conclusões foram obtidas exclusivamente pelo cruzamento de `operacao.md` e `mudanca.md`, com duas análises de subagentes diretos e consolidação pelo agente principal. Os arquivos de entrada foram preservados.
