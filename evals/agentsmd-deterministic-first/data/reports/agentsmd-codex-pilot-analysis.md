# Resultado do Codex: Deterministic first

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/analysis.md). Os links e comandos desta versão acompanham a organização por tema.


O trecho não demonstrou ganho de qualidade neste piloto. As duas condições entregaram 36/36 tarefas corretas. A condição com o trecho usou mais tempo e tokens de saída nesta amostra. O resultado continua inconclusivo para adoção no trabalho real.

Codex CLI 0.162.1, gpt-6.1-sol, xhigh. Doze casos sintéticos, três repetições, 36 pares, 72 execuções em 10/10/2026. A condição vazia tinha zero bytes em AGENTS.md; a outra continha somente o trecho fornecido.

| Medida | AGENTS vazio | Com o trecho | Diferença observada |
|---|---:|---:|---:|
| Entregas corretas | 36/36 | 36/36 | 0 ponto percentual |
| Tempo médio por tarefa | 40.5 s | 47.4 s | +17.1% |
| Tempo mediano por tarefa | 39.0 s | 42.4 s | +8.7% |
| Tempo somado das invocações | 1456.6 s | 1705.2 s | +17.1% |
| Tokens de entrada, cache incluído | 2.153.921 | 2.205.259 | +2.4% |
| Entrada em cache, subconjunto | 1.703.808 | 1.841.792 | +8.1% |
| Entrada sem cache | 450.113 | 363.467 | -19.2% |
| Tokens de saída | 35.800 | 43.232 | +20.8% |
| Eventos de ferramentas concluídos | 218 | 250 | +14.7% |

A média de tempo cresceu 6,9 s por tarefa, totalizando cerca de 4 min 9 s adicionais. A tabela mede a espera pelas invocações do agente, incluindo inicialização e chamadas de ferramentas; exclui preparação e correção. O consumo de entrada sem cache foi menor com o trecho. Portanto, mais tokens de saída não basta para afirmar maior custo monetário. Nenhum custo em dinheiro foi estimado.

## Qualidade e integridade

As 72 execuções terminaram e passaram nos checks. Há 78 turnos concluídos, sem turn.failed ou eventos de reconexão. Os 12 controles com julgamento foram revisados conforme a rubrica anterior à execução. Os textos preservam todos os fatos; os reviews identificam o defeito e propõem testes sem editar os arquivos. A conferência dos arquivos confirmou o escopo nos 12 controles.

As decisões estão em blind/*/review.json e seus hashes em [review-seal.json](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/review-seal.json), registrados antes da consulta à chave. A revisão foi feita pelo assistente, que já conhecia métricas agregadas. Alguns textos expõem IDs de trial e palavras sugestivas do tratamento. Isso limita o cegamento; não houve revisão humana independente.

Os contextos auditados dos 36 pares coincidem exceto pelo tratamento e caminhos temporários. Os 72 rollouts registram o modelo e effort pedidos. A auditoria não equivale à captura do request HTTP ao provedor. As fontes e o protocolo originais foram preservados em [frozen-source/](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/frozen-source/) e conferidos contra freeze.json antes de qualquer correção posterior.

Houve 21 comandos com retorno diferente de zero: 13 buscas sem correspondência, seis testes deliberadamente vermelhos antes da correção, um diff que encontrou alterações e um erro em uma asserção temporária de verificação. Esse último ocorreu no controle trial-0012 e foi corrigido em item_9; a entrega final passou. Nenhum desses trials foi excluído.

## Tempo por caso

Mediana e intervalo mínimo a máximo, em segundos. Três execuções por célula; todas corretas.

| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |
|---|---:|---:|
| count | 45.0; 36.2 a 49.9 | 42.2; 42.0 a 42.6 |
| money | 22.8; 21.8 a 23.0 | 25.0; 21.8 a 30.5 |
| convert | 32.2; 32.0 a 36.2 | 65.2; 58.1 a 80.3 |
| rename | 61.2; 51.9 a 61.4 | 76.8; 60.4 a 80.8 |
| project_tool | 32.9; 23.6 a 41.2 | 30.3; 26.4 a 31.3 |
| repeat | 48.5; 48.4 a 61.5 | 84.8; 83.3 a 91.7 |
| guardrail | 55.0; 48.5 a 66.9 | 56.1; 50.6 a 72.6 |
| regression | 51.2; 48.5 a 53.5 | 45.7; 39.4 a 49.4 |
| out_of_scope | 42.9; 34.6 a 43.2 | 43.5; 40.5 a 46.1 |
| judgment | 29.9; 28.1 a 33.7 | 31.0; 29.5 a 31.1 |
| independent | 36.9; 26.8 a 41.1 | 36.6; 29.5 a 44.9 |
| dependent | 27.6; 27.2 a 31.4 | 25.6; 24.8 a 34.9 |

Os maiores acréscimos se concentram em convert e repeat. Nesses dois casos, cada uma das três execuções com o trecho foi mais lenta que todas as execuções correspondentes sem o trecho. Eles somam cerca de 205 s dos 249 s adicionais. Isso localiza o efeito observado, mas não isola latência do serviço, raciocínio e execução local como causas de tempo.

## Comportamento observado

| Comportamento | Vazio | Trecho | Evidência |
|---|---|---|---|
| Conversão por programa | 3/3, Python inline | 3/3, arquivo temporário e verificações | tool-events.json de trial-0015, 0016, 0067 a 0070 |
| Renomeação em lote | 3/3, patch gerado pelo modelo | 3/3, substituição por script e verificação | tool-events.json de trial-0003, 0004, 0027 a 0030 |
| Automação na segunda solicitação | 3/3, um loop inline processa B e C | 3/3, cria script temporário testado e reutiliza para B e C | turn-2.jsonl de trial-0019, 0020, 0035, 0036, 0051, 0052 |
| Três comandos independentes sobrepostos | 3/3 | 3/3 | grade.observations.all_three_overlap e arquivos *-timing.json |
| Proteção detecta reincidência em guardrail e regression | 6/6 | 6/6 | grade.checks nos resultados individuais |

O trecho mudou o método em alguns casos. O controle já calculava por Python, automatizava os dois lotes seguintes e executava os checks independentes em paralelo. Em convert e repeat, criar o arquivo de script e verificá-lo acrescentou trabalho sem corrigir um erro que aparecesse no controle. Mais automação não recebeu pontos extras na nota de qualidade. Os eventos sustentam essa interpretação do método, mas não uma atribuição exata do tempo por componente.

## Correção da contagem de tokens

O runner original somava turn.completed.usage dos dois turnos de repeat. Os contadores são cumulativos por sessão. Essa soma duplicava o primeiro turno nos seis trials de repeat. A análise usa apenas usage_raw[-1] em cada trial. O último contador foi confrontado com total_token_usage e com os incrementos last_token_usage dos 72 rollouts, conforme [usage-audit.json](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/usage-audit.json). A auditoria conta incrementos somente quando o acumulado avança; trial-0062 contém uma notificação de contador repetida, sem novo consumo.

Os result.json originais permanecem intactos. Para totais reconciliados, usar [corrected-metrics.tsv](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/corrected-metrics.tsv) ou [analysis.json](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/analysis.json). O runner foi corrigido para futuras execuções e um teste de regressão falhou antes da correção e passou depois; a suíte completa passou em 13/13 testes. Não houve nova chamada ao modelo para a análise.

## O que este piloto permite concluir

Não apareceu ganho de acerto, paralelismo ou prevenção de regressão nos casos testados. O controle atingiu o teto da régua; o bootstrap de [0,0] no relatório automático resulta desse teto e não prova equivalência fora da amostra. Três repetições dos mesmos 12 casos não são 36 tarefas independentes.

O tempo agregado e a saída aumentaram nesta rodada. Não houve perfil de recursos ou controle do serviço remoto que permita identificar o limitante de desempenho. A ordem dos pares foi sorteada e a primeira condição ficou balanceada, 18 por lado. Ainda assim, os resultados não sustentam uma promessa geral de velocidade nem uma decisão definitiva de adoção.

Uma rodada confirmatória deveria usar novas tarefas reais em que o controle ainda comete erros, medir explicitamente reincidência e retrabalho, definir antes o ganho mínimo útil e o custo tolerável, e ampliar as repetições. Se a intenção for reduzir o texto, comparar separadamente Rules e Actions em casos novos; este estudo testou o bloco inteiro.

Reprodução offline: `python3 instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/analyze.py`. O script verifica a evidência preservada e regenera esta análise e a tabela de métricas sem alterar os trials.
