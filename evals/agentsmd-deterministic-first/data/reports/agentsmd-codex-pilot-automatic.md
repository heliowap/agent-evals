# Resultado do piloto

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot/report.md). Os links e comandos desta versão acompanham a organização por tema.


Veredito: inconclusivo. Este piloto não decide adoção.

Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.

| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |
|---|---|---:|---:|---:|---:|
| count | empty | 3 | 3 | 3 | 45.01 |
| count | deterministic | 3 | 3 | 3 | 42.24 |
| money | empty | 3 | 3 | 3 | 22.82 |
| money | deterministic | 3 | 3 | 3 | 25.01 |
| convert | empty | 3 | 3 | 3 | 32.15 |
| convert | deterministic | 3 | 3 | 3 | 65.17 |
| rename | empty | 3 | 3 | 3 | 61.20 |
| rename | deterministic | 3 | 3 | 3 | 76.83 |
| project_tool | empty | 3 | 3 | 3 | 32.91 |
| project_tool | deterministic | 3 | 3 | 3 | 30.29 |
| repeat | empty | 3 | 3 | 3 | 48.49 |
| repeat | deterministic | 3 | 3 | 3 | 84.79 |
| guardrail | empty | 3 | 3 | 3 | 55.04 |
| guardrail | deterministic | 3 | 3 | 3 | 56.06 |
| regression | empty | 3 | 3 | 3 | 51.18 |
| regression | deterministic | 3 | 3 | 3 | 45.72 |
| out_of_scope | empty | 3 | 3 | 3 | 42.94 |
| out_of_scope | deterministic | 3 | 3 | 3 | 43.50 |
| judgment | empty | 3 | 3 | 3 | 29.86 |
| judgment | deterministic | 3 | 3 | 3 | 30.98 |
| independent | empty | 3 | 3 | 3 | 36.95 |
| independent | deterministic | 3 | 3 | 3 | 36.55 |
| dependent | empty | 3 | 3 | 3 | 27.59 |
| dependent | deterministic | 3 | 3 | 3 | 25.56 |

Diferença exploratória de passes automáticos, com peso igual por caso: +0.0%.
Intervalo bootstrap por caso de 95%: [+0.0%, +0.0%].
Apenas pares completos; não mede tarefas ausentes nem substitui revisão dos controles. Casos sintéticos não estimam a distribuição do seu trabalho.

Estados: {"completed": 72}

Tokens de entrada, saída e cache estão nos resultados individuais. Cache não é somado novamente à entrada; custo monetário não é inferido. Campos ausentes permanecem desconhecidos. Nenhum total de tokens é inferido sem validar sobreposições.
Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação e correção. Não é throughput do modelo.
