# Diagnóstico do incidente

A causa mais sustentada é **C2: quebra de compatibilidade no consumidor `recibos`**. Deve-se reverter esse componente para a versão 7 nas instâncias que ainda executam a versão 8, validar uma amostra e então reprocessar as mensagens afetadas de **Q1 e Q2**, nessa ordem de IDs. Não há perda definitiva confirmada.

## Evidências e decisão de reversão

O cruzamento de [operacao.md](operacao.md) e [mudanca.md](mudanca.md) mostra a seguinte sequência, com todos os horários em UTC:

- Às 14:05, `recibos` passou da versão 7 para a 8. A nova versão exige `customer_id`, enquanto o contrato vigente do produtor publica `cliente_id`; não houve migração coordenada.
- Desde 14:06, Q1 apresenta rejeições locais por ausência de `customer_id`. Q2 apresenta o mesmo erro. O sintoma corresponde diretamente à incompatibilidade introduzida.
- Às 14:16, uma instância de `recibos` foi revertida para a versão 7 e aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Essa intervenção reforça a relação causal com a versão do consumidor.

As outras instâncias continuam na versão 8. Portanto, a reversão deve abranger as instâncias restantes de `recibos`. Reverter o produtor é menos sustentado: ele continua publicando conforme o contrato vigente e a medida exigiria coordenar clientes que operam normalmente. O procedimento documentado permite reverter `recibos` para 7 e validar uma amostra antes do reprocessamento.

## Filas que exigem reprocessamento

| Fila | Evidência operacional | Decisão |
|---|---|---|
| Q1 | 42 mensagens rejeitadas por ausência de `customer_id` | Reprocessar as mensagens afetadas |
| Q2 | 17 mensagens com o mesmo erro, retidas na fila de falhas | Reprocessar as mensagens afetadas |
| Q3 | Zero mensagens afetadas; consumo e confirmações normais em `notificacoes` | Não incluir |
| Q4 | Vazia desde 13:50, sem eventos na janela | Não incluir; não há mensagens afetadas a reprocessar |

A lista ordenada é `["Q1", "Q2"]`. Q4 usar o mesmo consumidor não demonstra impacto efetivo; sua ausência de tráfego também não comprova compatibilidade da versão 8. O total afetado é de **59 mensagens**, não uma contagem de tentativas.

## Por que as alternativas são menos sustentadas

**C1 — esgotamento de conexões do banco:** às 14:12, o banco tinha conexões disponíveis, sem aumento de latência nem falhas nas consultas de leitura e escrita. O sucesso das dez mensagens após a reversão, com o mesmo banco, reforça a hipótese de incompatibilidade. A verificação pontual não descreve cada instante da janela, mas não há evidência apresentada de esgotamento de conexões.

**C3 — indisponibilidade de DNS em produção:** a falha das 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Ela não demonstra falha de DNS em produção. A aceitação das mensagens após a reversão, com a mesma rede, também enfraquece essa hipótese.

A alteração visual do painel às 13:40 não mudou sua agregação. O painel agrega todas as filas e arredonda taxas; o alerta das 14:08 não estabelece o início do defeito nem permite inferir impacto em cada fila. As rejeições registradas desde 14:06 são evidência mais específica.

## Perda e ressalvas operacionais

`perda_confirmada` é **false** porque as 59 mensagens rejeitadas permanecem íntegras na fila de falhas, com IDs originais e payload disponível. Essa retenção temporária não constitui perda definitiva.

O resultado de um reprocessamento completo ainda não foi verificado. Assim, a ausência de perda confirmada não garante recuperação integral. Após concluir a reversão e validar uma amostra, o operador deve reprocessar as mensagens afetadas de Q1 e Q2, preservando os IDs originais e a chave de idempotência por ID de mensagem, e verificar o resultado completo.

Este diagnóstico usa somente os dois documentos locais. Exatamente dois subagentes diretos analisaram as evidências e concluíram suas análises; a redação dos arquivos finais foi feita pelo agente principal. Os arquivos de entrada foram preservados. Não foram executados reversão ou reprocessamento no ambiente operacional.
