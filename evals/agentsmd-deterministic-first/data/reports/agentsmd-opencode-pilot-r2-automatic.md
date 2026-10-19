# Resultado do piloto

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/report.md). Os links e comandos desta versão acompanham a organização por tema.


Veredito: inconclusivo. Este piloto não decide adoção.

Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.

| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |
|---|---|---:|---:|---:|---:|
| count | empty | 3 | 3 | 3 | 23.26 |
| count | deterministic | 3 | 3 | 3 | 31.09 |
| money | empty | 3 | 3 | 3 | 21.94 |
| money | deterministic | 3 | 3 | 3 | 18.98 |
| convert | empty | 3 | 3 | 3 | 75.51 |
| convert | deterministic | 3 | 3 | 3 | 51.71 |
| rename | empty | 3 | 3 | 3 | 53.85 |
| rename | deterministic | 3 | 3 | 3 | 91.54 |
| project_tool | empty | 3 | 3 | 3 | 15.95 |
| project_tool | deterministic | 3 | 3 | 3 | 19.31 |
| repeat | empty | 3 | 3 | 3 | 42.44 |
| repeat | deterministic | 3 | 3 | 3 | 82.79 |
| guardrail | empty | 3 | 3 | 3 | 39.73 |
| guardrail | deterministic | 3 | 3 | 3 | 38.69 |
| regression | empty | 3 | 3 | 3 | 40.64 |
| regression | deterministic | 3 | 3 | 3 | 50.72 |
| out_of_scope | empty | 3 | 3 | 3 | 25.52 |
| out_of_scope | deterministic | 3 | 3 | 3 | 33.57 |
| judgment | empty | 3 | 3 | 3 | 24.10 |
| judgment | deterministic | 3 | 3 | 3 | 22.47 |
| independent | empty | 3 | 3 | 3 | 27.30 |
| independent | deterministic | 3 | 3 | 3 | 23.54 |
| dependent | empty | 3 | 3 | 3 | 19.58 |
| dependent | deterministic | 3 | 3 | 3 | 24.72 |

Diferença exploratória de passes automáticos, com peso igual por caso: +0.0%.
Intervalo bootstrap por caso de 95%: [+0.0%, +0.0%].
Apenas pares completos; não mede tarefas ausentes nem substitui revisão dos controles. Casos sintéticos não estimam a distribuição do seu trabalho.

Estados: {"completed": 72}

Contadores nativos de tokens e custo informado pelo OpenCode estão nos resultados individuais. Cada exportação é cumulativa; usamos somente a última. Entrada, saída, raciocínio e cache ficam separados, sem inferir um total. Custo reportado zero não comprova gratuidade. Campos ausentes permanecem desconhecidos.
Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação, auditoria, exportação e correção. Não é throughput do modelo.
