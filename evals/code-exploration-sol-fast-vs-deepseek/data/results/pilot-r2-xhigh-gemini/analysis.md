# Segunda rodada de exploração no OpenCode

Esta rodada não justifica substituir a indicação inicial de Sonnet medium para exploração delimitada com JSON e citações. Sonnet xhigh teve 24/30 aprovações completas e Sol medium teve 17/30. Gemini medium teve 23/30 e Gemini high 12/30, mas a interpretação do Gemini exige separar qualidade de uma incompatibilidade no encerramento do agente. Não há uma comparação limpa de capacidade entre as quatro configurações.

As 120 tentativas terminaram em 10 de outubro de 2026. Foram 103 respostas concluídas, 27 delas reprovadas, e 17 erros de tarefa. Nenhuma sessão ficou ausente. Todos os erros ocorreram no Gemini. O OpenCode permaneceu na versão 2.0.26, com seis casos, cinco repetições e até 25 passos por sessão.

## Aprovação e tempo

| Configuração | Aprovação completa, entre 30 tentativas | Resposta literal correta, entre respostas concluídas | Erros de tarefa | Mediana das respostas concluídas | Intervalo observado |
|---|---:|---:|---:|---:|---:|
| Sonnet xhigh | 24/30, 80,0% | 28/30 | 0 | 15,82 s | 11,48 a 22,19 s |
| Sol medium, Fast selecionado | 17/30, 56,7% | 30/30 | 0 | 17,23 s | 8,57 a 22,55 s |
| Gemini medium | 23/30, 76,7% | 26/26 | 4 | 75,48 s | 39,14 a 120,18 s |
| Gemini high | 12/30, 40,0% | 17/17 | 13 | 108,86 s | 75,59 a 158,86 s |

A mediana inclui respostas concluídas incorretas e exclui os erros de tarefa. Cada configuração recebeu 30 tentativas; apenas Gemini medium e high tiveram menos respostas concluídas. A duração mede a invocação OpenCode com boot, ferramentas e recuperações internas, sem preparação, auditoria, exportação e correção. Somadas, as invocações duraram 103,6 minutos; os trials, incluindo preparação e fechamento, somaram 107,9 minutos. Esses totais não incluem preflight e processamento global.

Aprovação completa exige resposta literal correta, JSON e estrutura válidos, citações verificáveis, trechos obrigatórios e preservação do projeto. Sol acertou todas as respostas literais e perdeu 13 aprovações nas evidências: seis por citações inválidas e sete por cobertura incompleta. Sonnet xhigh perdeu quatro aprovações por cobertura incompleta em feature e duas pelo nome incompleto de `service.client.DatabaseClient.execute` em retry. As cinco outras propriedades de suas duas respostas de retry estavam corretas; o contrato exige o nome completo do método.

Gemini medium perdeu três aprovações de respostas concluídas por evidência incompleta em absence. Gemini high perdeu cinco pelo mesmo motivo. Todas as respostas concluídas do Gemini acertaram o objeto answer. Nenhuma resposta concluída falhou no parse JSON. As correções originais permaneceram intactas.

## Os 17 erros do Gemini

Quatro sessões medium e 13 high retornaram HTTP 400 com a mensagem `Requests ending with a model turn are not supported.` Todas haviam concluído 24 passos e falharam na chamada 25. As primeiras 24 chamadas dessas sessões retornaram HTTP 200. Não foram timeouts, recusas iniciais de autenticação ou esforço ignorado.

O código local do OpenCode em `packages/core/src/session/runner/llm.ts`, linhas 223 a 241, verifica `step >= loaded.agent.info.steps`. Quando alcança o limite, acrescenta `Message.assistant(MAX_STEPS_PROMPT)` ao fim das mensagens e desabilita a escolha de ferramentas. Esse comportamento fornece um mecanismo para a rejeição de uma requisição terminada em turno do modelo.

A relação causal é uma inferência apoiada pelo código e pela coincidência dos 17 erros com o limite. O observador conserva metadados, sem registrar o corpo completo das mensagens enviadas. Não há captura direta desse corpo para provar a tradução feita pelo CLIProxy. A incompatibilidade deve ser corrigida e verificada numa rodada separada antes de usar as taxas do Gemini como classificação de sua capacidade.

O limite de passos também importa como comportamento operacional. Nos trials concluídos, a mediana de chamadas de modelo foi quatro no Sonnet, cinco no Sol, 13 no Gemini medium e 17 no Gemini high. A maior quantidade de chamadas do Gemini permanece observada mesmo sem as sessões que falharam. Alterar o limite ou a estratégia de encerramento altera o protocolo; esta análise não corrige nem repete os trials encerrados.

## Aprovação por caso

| Caso | Sonnet xhigh | Sol medium | Gemini medium | Gemini high |
|---|---:|---:|---:|---:|
| route | 5/5 | 5/5 | 5/5 | 1/5, quatro erros |
| config | 5/5 | 1/5 | 5/5 | 5/5 |
| retry | 3/5 | 2/5 | 3/5, dois erros | 0/5, cinco erros |
| permission | 5/5 | 1/5 | 3/5, dois erros | 1/5, quatro erros |
| feature | 1/5 | 3/5 | 5/5 | 5/5 |
| absence | 5/5 | 5/5 | 2/5 | 0/5 |

## Comparações pareadas e Fast

Sonnet e Sol tiveram 15 pares com aprovação completa de ambos no mesmo caso e repetição. Sol foi mais rápido em dez e Sonnet em cinco. A mediana das razões Sonnet/Sol foi 1,100. A menor mediana geral do Sonnet não significa que foi mais rápido nesse subconjunto pareado; os conjuntos de respostas aprovadas diferem.

Gemini medium foi mais rápido que high nos 11 pares aprovados conjuntamente, com razão mediana medium/high de 0,697. Sonnet foi mais rápido nos 19 pares aprovados com Gemini medium, com razão mediana de 0,226. São descrições desta execução, condicionadas ao sucesso de ambos. A falha do encerramento e a pequena quantidade de casos impedem uma conclusão geral sobre modelos ou esforço.

As 141 chamadas do Sol usaram OAuth nativo, WebSocket, esforço medium e `service_tier=priority`. As respostas terminais informaram `default`, e nenhuma das 30 sessões confirmou Fast atendido. Esta rodada mede a configuração com Fast selecionado, sem demonstrar um benefício causal de Fast.

Sonnet enviou esforço xhigh e pensamento adaptativo na rota Anthropic do CLIProxy. Gemini enviou medium ou high na rota Chat Completions do CLIProxy. Todos os parâmetros, identidades e endpoints coincidiram com o congelamento. Isso verifica o envio ao proxy, sem atestar sua execução a montante.

Os metadados das respostas Gemini identificam `gemini-3.8-flash-n`, enquanto as requisições enviaram `gemini-3.8-flash`. O significado e a equivalência desse identificador não foram verificados. Os dados não comprovam que o backend executou o modelo e o esforço esperados.

O observador também marcou erro genérico em 311 chamadas HTTP 200 do Gemini medium e 432 do high. Esses 743 registros são distintos dos 17 HTTP 400 fatais. O código congelado do observador marca cancelamento do stream como erro, e `read_requests` reduz os códigos originais a uma mensagem genérica. As cópias persistidas não permitem distinguir cancelamento esperado de outras falhas do stream. As 103 sessões concluídas foram verificadas pelo estado final nativo e pelas respostas, mas essas marcações impedem afirmar transporte limpo no Gemini. Não equivalem a 743 tarefas reprovadas.

## Relação com o piloto anterior

No [piloto anterior](../pilot-oauth-matrix/analysis.md), Sonnet medium teve 27/30 aprovações completas e mediana de 9,84 s. Opus low também teve 27/30, com mediana de 11,89 s. Sonnet xhigh teve nesta rodada 24/30 e 15,82 s; Sol medium teve 17/30 contra 14/30 do Sol low na rodada anterior.

Esses resultados não compartilham blocos de execução e não formam comparações pareadas. Não demonstram efeito causal de elevar esforço. As novas observações não trazem evidência suficiente para promover xhigh ou Sol medium ao lugar da indicação inicial. A escolha operacional anterior continua provisória e restrita a este contrato.

## Verificação e limites

As fontes e o README coincidiram com os hashes congelados e foram preservados em [frozen-source](frozen-source). O verificador releu os 120 registros, corrigiu novamente as 103 respostas sobre a fixture de referência e verificou as 1.365 chamadas de modelo: 1.348 HTTP 200 ou status 200 equivalente no WebSocket, e 17 HTTP 400. Todos os registros de chamada receberam marcação de encerramento; os 743 flags de erro de stream permanecem com causa desconhecida. Não houve troca de identidade selecionada ou alteração de projeto. O relatório automático foi recalculado numa pasta temporária e coincidiu com o original.

A mediana da proporção entre tempo observado das chamadas ao provider e tempo da tarefa foi 96,3% no Sonnet, 72,3% no Sol, 98,8% no Gemini medium e 98,9% no Gemini high, considerando todas as tentativas. Isso identifica as chamadas externas como componente predominante. Não distingue raciocínio remoto, geração, espera da rede ou tradução no proxy, nem substitui um perfil de CPU. A máquina registrou 14 CPUs e carga média de 4,77 no início, sem monitoramento contínuo.

O benchmark mantém o veredito geral inconclusivo. As sessões foram sequenciais e intercaladas por blocos com posições balanceadas. Cinco repetições continuam sendo medições de seis tarefas distintas, num projeto sintético com 23 arquivos. Cache remoto pode persistir. Não mede delegação, qualidade geral de programação ou consumo comparável das assinaturas. Explain the Number orientou a separação entre qualidade, falha de integração e tempo observado.

Para reproduzir a verificação sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/verify_analysis.py
```

Os registros usados e contagens adicionais estão em [analysis.json](analysis.json). A tabela automática permanece em [report.md](report.md).
