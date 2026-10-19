# Resultado final do OpenCode

O trecho Deterministic first não demonstrou ganho de qualidade. As duas condições entregaram 36/36 tarefas corretas. Com o trecho, o OpenCode usou mais tempo e tokens nesta amostra. O piloto continua inconclusivo para adoção geral.

OpenCode 2.0.25, openai/gpt-6.1-sol#xhigh. Doze tarefas sintéticas, três repetições por condição, 36 pares e 72 execuções concluídas em 10/10/2026. Este relatório substitui os recortes parciais para interpretar a rodada.

| Métrica | AGENTS vazio | Com o trecho | Diferença observada |
|---|---:|---:|---:|
| Entregas corretas | 36/36 | 36/36 | 0 ponto percentual |
| Tempo médio por tarefa, s | 34.1 | 42.2 | +23.5% |
| Tempo mediano por tarefa, s | 27.1 | 31.6 | +16.5% |
| Entrada sem cache | 303.245 | 351.422 | +15.9% |
| Entrada em cache | 621.440 | 636.032 | +2.3% |
| Saída sem raciocínio | 27.092 | 27.892 | +3.0% |
| Raciocínio | 4.206 | 12.436 | +195.7% |
| Saída incluindo raciocínio | 31.298 | 40.328 | +28.9% |
| Tokens totais, incluindo cache e raciocínio | 955.983 | 1.027.782 | +7.5% |
| Chamadas de ferramentas | 326 | 330 | +1.2% |

A diferença média de duração foi de 8,0 s por tarefa, cerca de 4 min 49 s adicionais nas 36 execuções com o trecho. O número de chamadas de ferramentas pouco mudou; a diferença aparece também no volume de raciocínio e no conteúdo das operações. Não houve perfil que separe a contribuição causal de cada componente para a duração.

## Qualidade, isolamento e auditoria

As 72 execuções passaram nos corretores. As 78 exportações confirmam modelo, effort, sessão e conclusão de cada turno, inclusive continuidade dos seis casos repeat. Os contadores dos resultados conferem com a última exportação cumulativa, sem duplicar o primeiro turno. Não há erros de infraestrutura ou erros do assistente registrados. Os seis comandos com retorno diferente de zero foram testes de regressão deliberadamente vermelhos antes da correção; todos os artefatos finais passaram.

Os 12 controles subjetivos também passaram pela rubrica congelada. A comparação de hashes confirmou que out_of_scope não alterou arquivos e judgment alterou somente message.md. As decisões constam de blind/*/review.json e foram seladas em [review-seal.json](review-seal.json) antes da consulta à chave desta rodada. O revisor foi o assistente e já conhecia métricas e o desenho do estudo. Rótulos estavam ocultos, mas não há garantia de cegamento nem revisão humana independente.

A configuração e a descoberta de plugins/skills conferem com o preflight em todos os trials. Não há skills adicionais. O OpenCode não expõe o prompt completo neste fluxo; igualdade do prompt HTTP inteiro não foi demonstrada. Fontes e protocolo originais estão em [frozen-source/](frozen-source/), com hashes iguais ao freeze.json. Casos, rubrica, tratamento e resultados brutos não foram alterados.

## Duração por caso

Mediana e intervalo mínimo a máximo, em segundos, com três execuções corretas em cada célula.

| Caso | Vazio: mediana; min a max | Trecho: mediana; min a max |
|---|---:|---:|
| count | 23.3; 16.0 a 24.8 | 31.1; 20.3 a 32.1 |
| money | 21.9; 19.9 a 22.3 | 19.0; 16.0 a 28.9 |
| convert | 75.5; 67.9 a 91.6 | 51.7; 49.4 a 103.2 |
| rename | 53.8; 51.1 a 56.7 | 91.5; 87.3 a 92.7 |
| project_tool | 15.9; 14.7 a 16.9 | 19.3; 17.7 a 26.0 |
| repeat | 42.4; 40.3 a 42.6 | 82.8; 75.7 a 87.9 |
| guardrail | 39.7; 33.2 a 43.4 | 38.7; 36.0 a 49.0 |
| regression | 40.6; 34.4 a 49.1 | 50.7; 47.2 a 51.8 |
| out_of_scope | 25.5; 22.0 a 29.4 | 33.6; 29.2 a 36.6 |
| judgment | 24.1; 20.0 a 24.9 | 22.5; 16.6 a 24.5 |
| independent | 27.3; 22.9 a 29.0 | 23.5; 21.2 a 27.9 |
| dependent | 19.6; 19.1 a 26.9 | 24.7; 22.5 a 29.2 |

Os maiores acréscimos totais estão em rename e repeat. Em ambos, todas as execuções com o trecho foram mais lentas que todas as execuções sem o trecho. Em repeat, o controle calcula os resumos com Python inline e grava por patch. O tratamento cria um arquivo temporário reutilizável e adiciona verificações. A entrega final permaneceu correta em todas as repetições. Evidência: tool-events.json de trial-0019, 0020, 0035, 0036, 0051 e 0052.

Há um sinal favorável em convert: mediana de 75,5 s para 51,7 s. Os três controles gravam o JSON por patch; dois dos três tratamentos o gravam por programa. O terceiro tratamento ainda usa patch e leva 103,2 s. Isso sugere que escrever diretamente a transformação computada pode evitar trabalho, mas três repetições e essa variabilidade não sustentam uma promessa de velocidade. Evidência: tool-events.json de trial-0015, 0016, 0067, 0068, 0069 e 0070.

Os três checks independentes se sobrepuseram em 3/3 execuções de cada condição. Os casos guardrail e regression detectaram reincidência em 6/6 de cada condição. O trecho não trouxe vantagem de qualidade nesses comportamentos, que já apareciam no controle.

## Comparação exploratória com Codex

Mesmas 72 combinações de caso, repetição e condição em cada produto. Ambos tiveram 72/72 entregas aceitas pela régua, incluindo os controles revisados. Os tokens foram normalizados: o Codex inclui cache na entrada e raciocínio na saída; no OpenCode essas parcelas são separadas. A transformação foi conferida no código compilado do executável OpenCode 2.0.25; o hash e os trechos estão em analysis.json.

| Condição | Tempo médio Codex, s | Tempo médio OpenCode, s | Diferença de tempo | Diferença de tokens totais |
|---|---:|---:|---:|---:|
| empty | 40.5 | 34.1 | -15.6% | -56.3% |
| deterministic | 47.4 | 42.2 | -11.0% | -54.3% |

No conjunto completo, o OpenCode consumiu 55.3% menos tokens totais e levou 13.1% menos tempo que o Codex. Foram 1.983.765 versus 4.438.212 tokens, incluindo contexto reenviado, cache e raciocínio. Foi mais rápido em 56/72 correspondências. A maior redução está na entrada.

Essa comparação entre produtos é exploratória. As rodadas não foram sorteadas/intercaladas entre produtos, houve sobreposição parcial dos seus períodos de execução e instruções internas, ferramentas, permissões e integrações diferem. O desenho isolou o efeito do AGENTS dentro de cada produto; não identifica qual componente explica a diferença entre eles. A duração cobre invocações do agente com inicialização e ferramentas, mas exclui preparação, auditoria, exportação e correção do eval. Não representa tempo total do processo de avaliação nem throughput do modelo. Não foi estimado custo monetário.

## Interpretação

A evidência das duas rodadas favorece revisar as obrigações do bloco antes de mantê-lo como política global. Não apareceu ganho de acerto; o controle atingiu o teto da régua e o trecho aumentou a duração agregada nos dois produtos. Isso não prova que cada frase seja inútil ou prejudicial. O caso convert no OpenCode sugere uma vantagem localizada de produzir o arquivo por programa, enquanto a regra de criar script na segunda ocorrência acrescentou trabalho em repeat.

Há somente três repetições dos mesmos 12 casos sintéticos. O intervalo bootstrap [0,0] do relatório automático resulta do teto de acertos e não demonstra equivalência fora da amostra. Uma confirmação deve usar novas tarefas reais, critérios de ganho mínimo e custo tolerável definidos antes, mais repetições e medição de retrabalho/reincidência. Separar Rules de Actions ajudaria a localizar benefícios; este estudo avaliou o bloco inteiro.

Reprodução offline: `python3 agentsmd-detfirst-opencode/results/pilot-r2/analyze.py`. Dados completos: [analysis.json](analysis.json) e [metrics.tsv](metrics.tsv). A análise não chama o modelo nem modifica os trials.
