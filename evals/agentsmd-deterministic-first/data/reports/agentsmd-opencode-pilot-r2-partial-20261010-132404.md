# Parcial do OpenCode

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/partial-20261010-132404.md). Os links e comandos desta versão acompanham a organização por tema.


Consulta em 10/10/2026 13:24:04 -0300. Estado: {"completed": 61, "running": 1, "not_run": 10}.

Modelo conferido nas 67 exportações dos 61 trials completos: openai/gpt-6.1-sol#xhigh. Nenhuma falha de infraestrutura ou erro de assistente registrado nos trials completos. Todos passaram nos checks automáticos. A revisão dos controles subjetivos ainda está pendente.

Comparação de 30 pares completos, com os mesmos casos e repetições dos dois lados.

| Métrica | Vazio | Trecho | Diferença observada |
|---|---:|---:|---:|
| Passes automáticos | 30/30 | 30/30 | 0 ponto percentual |
| Tempo médio por tarefa, s | 32.7 | 42.4 | +29.7% |
| Tempo mediano por tarefa, s | 28.2 | 32.8 | +16.6% |
| Tokens de saída, contador nativo | 19498.0 | 21826.0 | +11.9% |
| Tokens de raciocínio, contador separado | 3689.0 | 10822.0 | +193.4% |
| Chamadas de ferramentas | 284.0 | 288.0 | +1.4% |

| Caso | Pares completos | Vazio: mediana e min a max, s | Trecho: mediana e min a max, s |
|---|---:|---:|---:|
| count | 2 | 19.6; 16.0 a 23.3 | 31.6; 31.1 a 32.1 |
| money | 3 | 21.9; 19.9 a 22.3 | 19.0; 16.0 a 28.9 |
| convert | 1 | 75.5; 75.5 a 75.5 | 51.7; 51.7 a 51.7 |
| rename | 3 | 53.8; 51.1 a 56.7 | 91.5; 87.3 a 92.7 |
| project_tool | 2 | 15.3; 14.7 a 15.9 | 18.5; 17.7 a 19.3 |
| repeat | 3 | 42.4; 40.3 a 42.6 | 82.8; 75.7 a 87.9 |
| guardrail | 3 | 39.7; 33.2 a 43.4 | 38.7; 36.0 a 49.0 |
| regression | 3 | 40.6; 34.4 a 49.1 | 50.7; 47.2 a 51.8 |
| out_of_scope | 3 | 25.5; 22.0 a 29.4 | 33.6; 29.2 a 36.6 |
| judgment | 2 | 22.1; 20.0 a 24.1 | 19.5; 16.6 a 22.5 |
| independent | 2 | 28.2; 27.3 a 29.0 | 24.6; 21.2 a 27.9 |
| dependent | 3 | 19.6; 19.1 a 26.9 | 24.7; 22.5 a 29.2 |

Este recorte não decide adoção. A composição ainda é parcial e algumas tarefas têm menos repetições. As durações incluem inicialização e chamadas do agente; excluem preparação, auditoria, exportação e correção. Não houve perfil do serviço remoto para identificar o limitante.

Há 10 controles com revisão subjetiva pendente. Não tratar os passes automáticos desses casos como aceitação final. O contexto de configuração e descoberta foi conferido; o OpenCode não expõe aqui o prompt completo para demonstrar sua igualdade.

Os tokens foram reconciliados com a última exportação cumulativa, sem somar novamente o primeiro turno de repeat. Entrada, cache, saída e raciocínio ficam separados. Não comparar diretamente esses contadores com os do Codex nem inferir custo monetário.

Contas, IDs e validações estão em [partial-20261010-132404.json](instrucoes-agents/agentsmd-detfirst-opencode/results/pilot-r2/partial-20261010-132404.json). Os fontes, resultados individuais e processo em andamento permaneceram inalterados.
