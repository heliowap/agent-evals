# Resultado do piloto

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-opencode/results/smoke-r3/report.md). Os links e comandos desta versão acompanham a organização por tema.


Veredito: inconclusivo. Este piloto não decide adoção.

Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.

| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |
|---|---|---:|---:|---:|---:|
| count | empty | 1 | 1 | 1 | 17.24 |
| count | deterministic | 1 | 1 | 1 | 40.87 |
| repeat | empty | 1 | 1 | 1 | 40.73 |
| repeat | deterministic | 1 | 1 | 1 | 67.14 |

Diferença exploratória de passes automáticos, com peso igual por caso: +0.0%.
Intervalo bootstrap por caso de 95%: [+0.0%, +0.0%].
Apenas pares completos; não mede tarefas ausentes nem substitui revisão dos controles. Casos sintéticos não estimam a distribuição do seu trabalho.

Estados: {"completed": 4}

Contadores nativos de tokens e custo informado pelo OpenCode estão nos resultados individuais. Cada exportação é cumulativa; usamos somente a última. Entrada, saída, raciocínio e cache ficam separados, sem inferir um total. Custo reportado zero não comprova gratuidade. Campos ausentes permanecem desconhecidos.
Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação, auditoria, exportação e correção. Não é throughput do modelo.
