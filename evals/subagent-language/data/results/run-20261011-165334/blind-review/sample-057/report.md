# Diagnóstico do incidente

A causa mais sustentada é **C2 — quebra de compatibilidade no consumidor `recibos`**. O componente a reverter é `recibos`, da versão 8 para a versão 7 nas instâncias ainda não revertidas. As filas que exigem reprocessamento são **Q1 e Q2**, com 42 e 17 mensagens afetadas, respectivamente. **Não há evidência de perda definitiva confirmada**; as 59 mensagens rejeitadas estão íntegras na fila de falhas. A recuperação integral ainda depende de validação.

## Evidências da causa

Às 14:05 UTC, `recibos` passou da versão 7 para a 8 e começou a exigir `customer_id`, enquanto o contrato vigente do produtor publica `cliente_id`, sem migração coordenada. Às 14:06, Q1 já apresentava rejeições locais por ausência de `customer_id`; Q2 apresentou o mesmo erro. A mudança explica tanto o tipo de rejeição quanto sua proximidade temporal com a atualização (`mudanca.md`, linhas 3–5; `operacao.md`, linhas 10–11).

Às 14:16, uma instância de `recibos` revertida para a versão 7 aceitou dez mensagens de teste no formato vigente, usando o mesmo banco e a mesma rede. Essa intervenção reforça a relação causal entre a versão do consumidor e as rejeições. As demais instâncias continuam na versão 8 (`mudanca.md`, linhas 5–8).

O alerta às 14:08 não determina o início do defeito: o painel agrega as filas e arredonda as taxas de erro. A alteração visual às 13:40 não mudou a agregação. O diagnóstico se apoia na mudança de contrato, nas rejeições específicas e no teste de reversão (`operacao.md`, linhas 2–3; `mudanca.md`, linha 2).

## Alternativas menos sustentadas

- **C1 — esgotamento de conexões do banco:** às 14:12 havia conexões disponíveis, sem aumento de latência nem falhas de leitura e escrita. O teste após a reversão também funcionou com o mesmo banco. Esses dados enfraquecem C1, embora a verificação pontual não prove a ausência de qualquer falha transitória em outros momentos (`operacao.md`, linhas 4–5; `mudanca.md`, linhas 5–7).
- **C3 — indisponibilidade de DNS em produção:** a falha às 14:04 ocorreu em uma sonda de laboratório que não compartilha o resolvedor de produção. Ela não demonstra indisponibilidade de DNS em produção. A aceitação das mensagens após a reversão, na mesma rede, também favorece C2 (`operacao.md`, linhas 5–6; `mudanca.md`, linhas 5–7).

Q3 manteve consumo e confirmações normais, e seu consumidor `notificacoes` não foi atualizado, o que reforça o caráter específico da falha em `recibos`. Q4 estava vazia desde 13:50: sua ausência de erros não permite concluir que a versão 8 funcionava nessa fila (`operacao.md`, linhas 12–13; `mudanca.md`, linha 8).

## Reversão e reprocessamento

Reverter as instâncias restantes de `recibos` para a versão 7 e validar uma amostra antes do reprocessamento segue o procedimento documentado. A reversão do produtor é menos sustentada: a incompatibilidade foi introduzida no consumidor, e alterar o produtor exigiria coordenar clientes que continuam operando normalmente (`mudanca.md`, linhas 12–14).

| Fila | Mensagens afetadas | Decisão |
|---|---:|---|
| Q1 | 42 | Reprocessar as mensagens rejeitadas retidas na fila de falhas. |
| Q2 | 17 | Reprocessar as mensagens rejeitadas retidas na fila de falhas. |
| Q3 | 0 | Sem reprocessamento indicado; consumo e confirmações normais. |
| Q4 | 0 | Sem reprocessamento indicado; nenhum evento durante a janela. |

A lista `reprocessar` usa a ordem Q1, Q2 da tabela de origem. Os documentos não estabelecem prioridade operacional entre elas. O total documentado é de 59 mensagens, não de tentativas. Não se descontam as dez mensagens de teste desse total, pois os documentos não dizem que elas pertenciam ao conjunto retido (`operacao.md`, linhas 10–18; `mudanca.md`, linhas 5–7).

Ao reprocessar, preservar os IDs originais e a chave de idempotência por ID de mensagem. Depois, verificar o resultado completo das 59 mensagens e reconciliar pendências e confirmações; o sucesso da amostra não comprova a recuperação de todo o conjunto (`operacao.md`, linhas 15–19).

## Perda e limites da conclusão

`perda_confirmada` é `false` porque todas as 59 mensagens rejeitadas permanecem íntegras, com IDs originais e payload disponível. Retenção temporária não constitui perda definitiva. Entretanto, ainda não foi verificado o resultado de um reprocessamento completo: a ausência de evidência de perda não garante recuperação integral sem validação (`operacao.md`, linhas 15–17; `mudanca.md`, linhas 15–16).

Esta análise cruza exclusivamente `operacao.md` e `mudanca.md`. Dois subagentes diretos fizeram análises independentes e retornaram suas conclusões por mensagem, sem alterar arquivos nem criar descendentes. Os arquivos de entrada foram preservados; a entrega registra o diagnóstico e as ações recomendadas, sem executar reversões ou reprocessamentos.
