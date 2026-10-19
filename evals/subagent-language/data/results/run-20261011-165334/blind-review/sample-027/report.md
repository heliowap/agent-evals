# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, nas instâncias que ainda executam a versão 8, retornando à versão 7. As filas que exigem reprocessamento são **Q1 e Q2**, nessa ordem. **Não há perda definitiva confirmada**; a recuperação integral ainda não foi validada.

## Evidências da causa e da reversão

O histórico registra a atualização de `recibos` da versão 7 para a 8 às 14:05 UTC. A versão 8 exige `customer_id`, enquanto o contrato vigente do produtor fornece `cliente_id`; não houve migração coordenada ([mudanca.md](mudanca.md), linhas 3–5). Em seguida, desde 14:06, Q1 apresentou rejeições locais por ausência de `customer_id`, e Q2 registrou o mesmo erro ([operacao.md](operacao.md), linhas 10–11). O tipo de erro e a sequência temporal correspondem à incompatibilidade introduzida.

Às 14:16, uma instância de `recibos` voltou à versão 7 e aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Essa intervenção reforça a relação causal e a escolha da reversão; as demais instâncias continuam na versão 8 ([mudanca.md](mudanca.md), linhas 5–8). Reverter o produtor tem menos sustentação: ele continuou publicando, e sua reversão exigiria coordenar clientes que operam normalmente ([operacao.md](operacao.md), linha 15; [mudanca.md](mudanca.md), linhas 12–14).

## Alternativas menos sustentadas

| Hipótese | Avaliação das evidências |
|---|---|
| C1 — esgotamento de conexões do banco | Às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura ou escrita. A versão 7 também aceitou os testes no mesmo banco. Essa verificação pontual não exclui todo evento transitório anterior, mas não sustenta C1 nem explica tão diretamente o erro de campo ausente. |
| C3 — indisponibilidade de DNS em produção | A falha das 14:04 ocorreu em uma sonda de laboratório que usa outro resolvedor. Não é evidência de falha do DNS de produção. A aceitação dos testes pela versão 7 na mesma rede também favorece C2. |

As evidências sobre banco e DNS constam em [operacao.md](operacao.md), linhas 4–6, e o teste após reversão em [mudanca.md](mudanca.md), linhas 5–7. A alteração visual do painel às 13:40 não mudou sua agregação. Como o painel agrega filas e arredonda taxas, o alerta às 14:08 não determina o início do defeito nem substitui a evidência por fila ([mudanca.md](mudanca.md), linha 2; [operacao.md](operacao.md), linhas 2–3).

## Filas e reprocessamento

| Fila | Mensagens afetadas | Decisão e fundamento |
|---|---:|---|
| Q1 | 42 | Reprocessar: rejeições locais por ausência de `customer_id`. |
| Q2 | 17 | Reprocessar: mesmo erro; mensagens retidas na fila de falhas. |
| Q3 | 0 | Não exige reprocessamento: consumo e confirmações normais durante toda a janela; `notificacoes` não foi atualizado. |
| Q4 | 0 | Não exige reprocessamento: estava vazia desde 13:50, sem eventos na janela. A ausência de erros não comprova que `recibos` v8 funcionaria nessa fila. |

A tabela operacional sustenta esse escopo ([operacao.md](operacao.md), linhas 8–13). O total é **42 + 17 = 59 mensagens**, sem confundir tentativas com mensagens únicas. O procedimento recomendado é reverter as instâncias restantes de `recibos` para 7, validar uma amostra e então reprocessar as mensagens de Q1 e Q2 retidas na fila de falhas. Devem ser preservados os IDs originais e a chave de idempotência por ID de mensagem ([mudanca.md](mudanca.md), linhas 13–14; [operacao.md](operacao.md), linhas 15–19).

## Perda e limites da conclusão

As 59 mensagens rejeitadas estão íntegras na fila de falhas, com IDs originais e payload disponível. Trata-se de retenção temporária documentada, sem evidência de perda definitiva. Por isso, `perda_confirmada` é `false`.

Esse valor não garante recuperação integral. Os dez testes aceitos após a reversão apoiam o diagnóstico, mas não comprovam o processamento bem-sucedido das 59 mensagens. Ainda é necessário validar o resultado do reprocessamento completo, conforme a ressalva explícita dos dois documentos ([operacao.md](operacao.md), linhas 15–19; [mudanca.md](mudanca.md), linhas 15–16).

## Método e entrega

Foram usados somente os dois arquivos locais de entrada. Exatamente dois subagentes diretos, com `fork_turns="none"`, modelo e esforço herdados da sessão e sem descendentes, analisaram respectivamente causa/reversão e filas/perda. Ambos retornaram suas análises por mensagem e concluíram antes da consolidação. Somente o agente principal escreveu os arquivos finais. Os arquivos de entrada foram preservados. A reversão e o reprocessamento são recomendações; nenhuma operação no ambiente de produção foi executada.
