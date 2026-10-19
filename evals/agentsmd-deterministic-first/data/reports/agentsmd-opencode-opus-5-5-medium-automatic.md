# Resultado do piloto

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/report.md). Os links e comandos desta versão acompanham a organização por tema.


Veredito: inconclusivo. Este piloto não decide adoção.

Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.

| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |
|---|---|---:|---:|---:|---:|
| count | empty | 3 | 3 | 3 | 12.45 |
| count | deterministic | 3 | 3 | 3 | 11.03 |
| money | empty | 3 | 3 | 3 | 8.98 |
| money | deterministic | 3 | 3 | 3 | 8.00 |
| convert | empty | 3 | 3 | 3 | 10.57 |
| convert | deterministic | 3 | 3 | 3 | 14.51 |
| rename | empty | 3 | 3 | 3 | 12.72 |
| rename | deterministic | 3 | 3 | 3 | 14.60 |
| project_tool | empty | 3 | 3 | 3 | 8.76 |
| project_tool | deterministic | 3 | 3 | 3 | 10.79 |
| repeat | empty | 3 | 3 | 3 | 12.53 |
| repeat | deterministic | 3 | 3 | 3 | 24.42 |
| guardrail | empty | 3 | 3 | 3 | 15.92 |
| guardrail | deterministic | 3 | 3 | 3 | 16.13 |
| regression | empty | 3 | 3 | 3 | 15.72 |
| regression | deterministic | 3 | 3 | 3 | 16.10 |
| out_of_scope | empty | 3 | 3 | 3 | 17.75 |
| out_of_scope | deterministic | 3 | 3 | 3 | 13.95 |
| judgment | empty | 3 | 3 | 3 | 8.25 |
| judgment | deterministic | 3 | 3 | 3 | 8.41 |
| independent | empty | 3 | 3 | 3 | 12.31 |
| independent | deterministic | 3 | 3 | 3 | 14.22 |
| dependent | empty | 3 | 3 | 3 | 9.93 |
| dependent | deterministic | 3 | 3 | 3 | 7.90 |

Diferença exploratória de passes automáticos, com peso igual por caso: +0.0%.
Intervalo bootstrap por caso de 95%: [+0.0%, +0.0%].
Apenas pares completos; não mede tarefas ausentes nem substitui revisão dos controles. Casos sintéticos não estimam a distribuição do seu trabalho.

Estados: {"completed": 72}

Contadores nativos de tokens e custo informado pelo OpenCode estão nos resultados individuais. Cada exportação é cumulativa; usamos somente a última. Entrada, saída, raciocínio e cache ficam separados, sem inferir um total. Custo reportado zero não comprova gratuidade. Campos ausentes permanecem desconhecidos.
Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação, auditoria, exportação e correção. Não é throughput do modelo.
