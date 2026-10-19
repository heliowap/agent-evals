# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. Deve-se reverter esse componente para a versão 7 e, após validar uma amostra, reprocessar **Q1 e Q2**, nessa ordem. **Não há evidência de perda definitiva confirmada**. A análise cruza exclusivamente `operacao.md` e `mudanca.md`; todos os horários citados estão em UTC.

## Causa e evidências

Às 14:05, o consumidor `recibos` passou da versão 7 para a 8. A nova versão exige `customer_id`, enquanto o contrato vigente do produtor fornece `cliente_id`. Não houve migração coordenada do produtor. Às 14:06, Q1 já apresentava rejeições locais por ausência de `customer_id`; Q2 apresentou o mesmo erro. Essa correspondência entre alteração, sequência temporal e erro observado sustenta C2.

Às 14:16, uma instância de `recibos` foi revertida para a versão 7 e aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Esse resultado reforça a atribuição ao consumidor. As demais instâncias ainda estão na versão 8, portanto a reversão parcial não demonstra que o incidente foi resolvido integralmente.

O alerta das 14:08 não determina o início do defeito: o painel agrega todas as filas e arredonda as taxas de erro. O primeiro erro observado em Q1 é das 14:06. A alteração visual do painel às 13:40 não modificou a agregação e não explica as rejeições locais.

## Componente a reverter

Reverter as instâncias de **`recibos` que ainda executam a versão 8 para a versão 7**, conforme o procedimento operacional, e validar uma amostra antes de reprocessar. O teste de dez mensagens sustenta essa escolha, mas não substitui a validação do conjunto afetado.

O produtor continuou publicando conforme o contrato vigente. Revertê-lo não é a ação sustentada pelas evidências: a incompatibilidade foi introduzida em `recibos`, e uma reversão do produtor exigiria coordenar clientes que continuam operando normalmente.

## Filas e reprocessamento

| Fila | Mensagens afetadas | Decisão e evidência |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id` desde 14:06. |
| Q2 | 17 | Reprocessar: mesmo erro; mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: `notificacoes` manteve consumo e confirmações normais e não foi atualizado. |
| Q4 | 0 | Sem reprocessamento: vazia desde 13:50, sem eventos durante a janela. |

A lista ordenada é `["Q1", "Q2"]`, com **59 mensagens distintas afetadas**. Todas as mensagens rejeitadas estão íntegras na fila de falhas. Ao reprocessá-las, preservar os IDs originais e a chave de idempotência por ID de mensagem utilizada por `recibos`. Conferir os resultados por mensagem; contagens de tentativas não equivalem à quantidade de mensagens.

Q4 utiliza o consumidor afetado, mas não teve mensagens na janela. Sua ausência de erros não demonstra imunidade à incompatibilidade; apenas não há mensagens dessa fila que exijam reprocessamento.

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência ou falhas nas consultas de leitura e escrita. A instância revertida aceitou mensagens usando o mesmo banco. A verificação pontual não exclui todo problema transitório possível, mas C1 não explica tão bem as rejeições explícitas por campo ausente e a aceitação após reversão.
- **C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Ela não comprova falha de DNS em produção. As rejeições locais por campo ausente e o teste bem-sucedido após reversão, na mesma rede, sustentam C2 com mais força.

## Perda e limites da conclusão

`perda_confirmada` é **`false`** porque as 59 mensagens rejeitadas permanecem íntegras, com IDs originais e payload disponível. Os registros sustentam retenção temporária, sem evidência de perda definitiva.

Isso **não garante recuperação integral**: o resultado de um reprocessamento completo ainda não foi verificado. Após a reversão e a validação da amostra, será necessário verificar o resultado das 59 mensagens, preservando a idempotência. Este relatório recomenda essas ações; os arquivos de entrada não registram sua execução completa.

## Revisão da análise

Foram usados exatamente dois subagentes diretos, sem descendentes: um priorizou a operação, as filas e a perda; o outro, a mudança, a causalidade e as alternativas. Ambos leram os dois arquivos e retornaram análises concordantes por mensagem. Somente o agente principal escreveu os arquivos finais. Os arquivos de entrada foram preservados e nenhuma fonte externa foi utilizada.
