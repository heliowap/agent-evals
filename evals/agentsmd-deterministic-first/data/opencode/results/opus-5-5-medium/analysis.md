# Resultado do Opus 5.5 medium via CPA

O trecho Deterministic first não trouxe ganho de acerto nesta amostra. As duas condições entregaram 36/36 tarefas corretas. Com o trecho, a duração média foi 5,8% maior e os tokens de saída reportados aumentaram 14,9%. A diferença global de tempo é pequena frente à variação entre casos; não há evidência suficiente de uma piora geral de velocidade.

OpenCode 2.0.25, cli_proxy/cpa-claude-opus-5-5#medium. São 12 casos sintéticos, três repetições por condição, 36 pares e 72 execuções em 10/10/2026. A ordem dentro dos pares foi balanceada, com cada condição primeiro em 18 pares.

| Métrica | AGENTS vazio | Com o trecho | Diferença |
|---|---:|---:|---:|
| Entregas corretas | 36/36 | 36/36 | 0 p.p. |
| Tempo médio, s | 12,70 | 13,43 | +5,8% |
| Tempo mediano, s | 12,23 | 13,64 | +11,5% |
| Tokens de saída reportados | 28.740 | 33.034 | +14,9% |
| Chamadas de ferramentas | 159 | 165 | +3,8% |

O tratamento foi mais rápido em 18/36 pares. O intervalo exploratório de 95% por bootstrap agrupado nos 12 casos foi [-7.0%, +24.1%] para a diferença de duração média. Esse cálculo foi escolhido após a rodada; não é um teste confirmatório pré-registrado. O intervalo inclui zero.

## Onde o comportamento mudou

Em repeat, a mediana passou de 12,53 s para 24,42 s. Todas as três execuções com o trecho foram mais lentas que todas as três sem ele. O controle já calculava os JSONs com Python. O tratamento criou um script temporário no segundo turno e acrescentou inspeções ou reexecuções de validação. A entrega continuou correta nas duas condições. Evidência: tool-events.json de trial-0019, 0020, 0035, 0036, 0051 e 0052.

Excluindo repeat apenas como análise de sensibilidade, a diferença de tempo fica em -1.6%. Portanto, o acréscimo global está concentrado nesse caso, não distribuído uniformemente pela suíte.

O trecho não aumentou o paralelismo observado. Os três checks independentes se sobrepuseram em 1/3 execuções do controle e 0/3 com o trecho. Os seis resultados numéricos estavam corretos; a rubrica congelada registra sobreposição como comportamento, sem torná-la requisito de acerto. Assim, 72/72 entregas corretas não significa obediência perfeita a todas as frases do bloco. Evidência: arquivos *-timing.json dos trials 0045, 0046, 0059, 0060, 0071 e 0072.

As proteções de guardrail e regression passaram em 6/6 entregas de cada condição, incluindo probes e reintrodução da falha em cópias dos artefatos. Não houve vantagem de prevenção dentro desses casos. O controle também gerou customers.json por Python nas três repetições de convert; a instrução não era necessária para esse comportamento no Opus.

## Duração por caso

Mediana e intervalo mínimo a máximo, em segundos. Três repetições por célula.

| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |
|---|---:|---:|
| count | 12.45; 10.87 a 12.68 | 11.03; 10.76 a 11.06 |
| money | 8.98; 7.92 a 9.23 | 8.00; 7.68 a 8.53 |
| convert | 10.57; 10.31 a 15.68 | 14.51; 13.82 a 16.18 |
| rename | 12.72; 9.51 a 19.68 | 14.60; 10.99 a 16.99 |
| project_tool | 8.76; 7.93 a 9.15 | 10.79; 10.70 a 11.41 |
| repeat | 12.53; 11.97 a 14.88 | 24.42; 22.48 a 25.43 |
| guardrail | 15.92; 14.47 a 17.72 | 16.13; 15.78 a 16.37 |
| regression | 15.72; 15.47 a 21.41 | 16.10; 15.15 a 16.90 |
| out_of_scope | 17.75; 17.60 a 18.25 | 13.95; 13.46 a 15.58 |
| judgment | 8.25; 8.24 a 8.73 | 8.41; 7.47 a 12.77 |
| independent | 12.31; 12.14 a 17.55 | 14.22; 10.30 a 16.81 |
| dependent | 9.93; 9.33 a 10.72 | 7.90; 7.30 a 9.67 |

## Auditoria e limites

Foram conferidas 78 exportações, incluindo a continuidade dos dois prompts de repeat. Provider, alias, variante medium e agente build conferem em todas as mensagens do assistente. Os contadores batem com a última exportação cumulativa. Os 72 artefatos foram corrigidos novamente em cópias separadas, incluindo as mutações usadas para testar prevenção de reincidência. Nenhuma inferência nova foi feita nesta análise.

Os 12 controles subjetivos passaram na rubrica original. As revisões dos artefatos sem rótulos foram seladas antes da consulta à chave atual. O assistente já conhecia o desenho, o relatório automático agregado e a rodada Sol. O embaralhamento usa a mesma seed da rodada anterior, e a redação sugere o tratamento em alguns casos. Não há revisão humana independente nem cegamento garantido. Os hashes confirmam ausência de mudanças em out_of_scope e alteração exclusiva de message.md em judgment.

Não houve falha de infraestrutura nem erro final do assistente. Houve duas chamadas à ferramenta inexistente tool_write, recuperadas depois: trial-0037 no tratamento e trial-0042 no controle. Também houve dois comandos shell com saída 1 no controle: head -0 incompatível com macOS em trial-0008 e leitura de arquivos opcionais ausentes em trial-0010. As quatro execuções terminaram corretas. O campo recoverable_error_events do executor contém erros de mensagem, não todos os erros de ferramentas; esta auditoria consultou tool-events.json diretamente.

O tempo mede as invocações do agente, incluindo inicialização, ferramentas e eventuais retries internos; exclui preparação, auditoria, exportação e correção. Não há perfil nem telemetria do servidor para separar inferência, proxy, rede e inicialização. Os intervalos de execução das ferramentas estão somados sem sobreposição em metrics.tsv, mas o restante do tempo não pode ser atribuído a um componente específico. Não se identificou um gargalo causal de desempenho.

O CPA reportou entrada nativa de apenas 2 tokens em 307 mensagens e 4 tokens em seis mensagens, raciocínio zero e volumes altos de cache. Preservamos entrada, cache de leitura, cache de gravação e saída separados em analysis.json. O aumento de 14,9% refere-se somente à saída reportada; não equivale a aumento de custo ou tokens totais. Raciocínio zero no contador não comprova ausência de raciocínio. O custo informado pelo OpenCode não foi conciliado com cobrança do proxy.

Configuração e descoberta conferem com o preflight nas duas condições e em todos os trials; não há skills adicionais. Isso não comprova igualdade integral do prompt HTTP. As exportações confirmam a seleção no cliente, sem atestar a identidade efetivamente servida pelo provedor a montante. Fontes, protocolo e variantes estão em frozen-source/, conferidos contra freeze.json. Os dados brutos da rodada foram preservados.

## Comparação exploratória com Sol no OpenCode

| Condição | Sol xhigh, média em s | Opus medium via CPA, média em s | Diferença |
|---|---:|---:|---:|
| empty | 34.14 | 12.70 | -62.8% |
| deterministic | 42.17 | 13.43 | -68.1% |

Ambas as rodadas entregaram 72/72 resultados aceitos na mesma suíte. O Opus via CPA levou menos tempo observado, mas modelo, esforço, provider e horário da rodada mudaram juntos. As rodadas não foram intercaladas; isso não isola um efeito do modelo ou do provider. A contabilidade de tokens do CPA impede transportar diretamente a normalização usada na comparação anterior Codex/OpenCode.

## Recomendação

Manter o bloco removido do AGENTS global continua sendo a escolha apoiada por estes pilotos. Não apareceu ganho de qualidade nas três configurações avaliadas, e o custo de criar script em repeat se repetiu no Opus. Isso não prova que cada recomendação do bloco seja inútil. A suíte é pequena, sintética e já está no teto de acertos; benefícios em tarefas reais mais difíceis, reutilização futura ou reincidência fora destes probes não foram medidos. A diferença global de tempo nesta rodada permanece inconclusiva.

Reprodução offline: `python3 agentsmd-detfirst-opencode/results/opus-5-5-medium/analyze.py`. Dados: [analysis.json](analysis.json), [metrics.tsv](metrics.tsv), [review-seal.json](review-seal.json).
