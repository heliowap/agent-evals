# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. Recomenda-se reverter as instâncias que ainda executam a versão 8 para a versão 7, validar uma amostra e reprocessar as mensagens afetadas de **Q1 e Q2**. Não há evidência de perda definitiva confirmada; a recuperação integral ainda precisa ser validada.

## Evidências e causalidade

O cruzamento de [mudanca.md](mudanca.md) com [operacao.md](operacao.md) estabelece uma sequência coerente, com todos os horários em UTC:

| Horário | Evidência | Implicação |
|---|---|---|
| 14:05 | `recibos` passou da versão 7 para a 8, que exige `customer_id`; o produtor continua publicando `cliente_id`, conforme o contrato vigente, sem migração coordenada. | A mudança introduziu uma incompatibilidade concreta entre consumidor e produtor. |
| 14:06 | Q1 apresenta rejeições locais por ausência de `customer_id`; Q2 apresenta o mesmo erro. | O erro observado corresponde diretamente à nova exigência do consumidor. |
| 14:08 | O painel iniciou o alerta. | O alerta ocorreu após o início observado das rejeições; não define o início do defeito. |
| 14:12 | O banco tinha conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. | O estado observado do banco enfraquece C1. |
| 14:16 | Uma instância de `recibos`, revertida para a versão 7, aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. | A reversão fornece evidência adicional forte a favor de C2. |

Fontes: `mudanca.md`, linhas 3–8; `operacao.md`, linhas 2–13. O mecanismo da incompatibilidade, o início das rejeições após a atualização e a aceitação após a reversão sustentam C2 em conjunto. O teste das dez mensagens valida apenas aquela amostra e instância; não comprova a recuperação de todas as mensagens nem a correção das demais instâncias, ainda na versão 8.

## Componente a reverter

O componente é **`recibos`**, com retorno à **versão 7** nas instâncias restantes. O produtor segue publicando o contrato vigente; sua reversão não corrige a origem demonstrada da incompatibilidade e exigiria coordenar clientes que continuam operando normalmente. `notificacoes` não foi atualizado e manteve funcionamento normal. O procedimento descrito permite reverter `recibos` e validar uma amostra antes do reprocessamento (`mudanca.md`, linhas 8 e 12–14).

## Filas e recuperação

| Fila | Mensagens afetadas | Decisão e fundamento |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro, com mensagens retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento: `notificacoes` consumiu e confirmou normalmente durante toda a janela. |
| Q4 | 0 | Sem reprocessamento: estava vazia desde 13:50, sem eventos durante a janela. |

A lista em `answer.json` está ordenada por ID: `["Q1", "Q2"]`. Essa ordenação não representa uma dependência operacional documentada entre as filas. Q4 usa o consumidor defeituoso, mas não teve mensagens afetadas; sua ausência de erros também não demonstra que a versão 8 funcionava corretamente.

As **59 mensagens rejeitadas** estão íntegras na fila de falhas, com IDs originais e payload disponível (`operacao.md`, linhas 15–19). Por isso, `perda_confirmada` é **`false`**. Retenção temporária não equivale a perda definitiva. Entretanto, o resultado de um reprocessamento completo ainda não foi verificado, de modo que esse valor não garante recuperação integral.

Após a reversão e a validação da amostra, o reprocessamento deve preservar os IDs originais e a chave de idempotência por ID de mensagem. A conferência final deve verificar o processamento das 59 mensagens e seus resultados, sem confundir número de tentativas com quantidade de mensagens. Estas são recomendações; os arquivos de entrada não registram sua execução completa.

## Por que as alternativas são menos sustentadas

- **C1 — esgotamento de conexões do banco:** a verificação às 14:12 encontrou conexões disponíveis e operações normais. As rejeições locais por campo ausente têm uma explicação direta no contrato incompatível. O teste bem-sucedido após a reversão usou o mesmo banco. A verificação é pontual e não exclui todo problema transitório possível, mas não há evidência apresentada que sustente C1 como causa deste incidente.
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Sua proximidade temporal não demonstra falha de DNS em produção. A aceitação após a reversão usando a mesma rede também favorece a explicação no consumidor.
- **Alteração visual do painel:** a mudança das 13:40 não alterou a agregação. O painel agrega todas as filas e arredonda as taxas; esses dados não substituem as evidências por fila para determinar alcance ou início do defeito (`mudanca.md`, linha 2; `operacao.md`, linhas 2–3).

## Escopo da análise

Foram usados somente os dois arquivos locais de entrada, preservados sem alterações. Dois subagentes diretos analisaram, respectivamente, as evidências operacionais e a causalidade das mudanças; ambos concluíram a análise por mensagem, sem escrever arquivos ou criar descendentes. A consolidação e a escrita de `answer.json` e deste relatório foram feitas pelo agente principal.
