# Parcial de Sol low Fast e GLM Flash

Corte em 11/10/2026 às 12:59:32, America/Recife. O snapshot contém 14 trials comparativos concluídos dos 108 planejados, com 12 aprovações pelo grader e 102 chamadas registradas nessas tentativas. Budget e smoke são provas separadas e não entram nesses totais. Um resultado adicional estava marcado como `started`, sem resultado final no corte; isso não prova liveness do processo.

| Configuração | Aprovação nos concluídos | Chamadas | Monetário aprovado, n | Mediana monetária, s | Faixa monetária, s |
|---|---:|---:|---:|---:|---:|
| Sol 6.1 low Fast | 5/5 | 21 | 3 | 38,50 | 35,82 a 39,07 |
| GLM 5.3 Flash high | 4/5 | 39 | 3 | 105,96 | 100,47 a 141,22 |
| GLM 5.3 Flash max | 3/4 | 42 | 2 | 631,79 | 607,44 a 656,13 |

Essas medianas incluem somente as tentativas aprovadas do contrato monetário corrigido. Não são medianas da triagem completa. As quantidades de tarefas concluídas ainda diferem entre candidatos. Nos quatro blocos concluídos pelos três candidatos, Sol e GLM high têm 4/4 aprovações; GLM max tem 3/4.

| Caso e repetição | Sol low Fast | GLM high | GLM max |
|---|---|---|---|
| Pagamento idempotente, repetição 3 | Aprovado, 34,78 s | Aprovado, 47,08 s | Aprovado, 117,08 s |
| PATCH de perfil, repetição 3 | Aprovado, 28,74 s | Reprovado pelo grader, 42,46 s | Sem resultado final |

GLM max foi reprovado no monetário, repetição 1. O patch capturado não contém alterações e a aceitação falhou na exigência explícita de retornar Decimal com expoente -2. A sessão terminou normalmente, com quatro chamadas HTTP 200 completas e sem eventos de erro registrados. A duração dessa tentativa reprovada foi 454,12 s e não entra na mediana das aprovadas.

GLM high foi reprovado no PATCH de perfil. A aceitação exige rejeitar tags que duplicam após trim. O patch usa `if (seen.has(trimmed)) continue`, removendo duplicatas. O enunciado pede uma lista de tags distintas e verificações de unicidade, mas não diz expressamente que duplicatas devem causar erro em vez de serem removidas. Essa reprovação exige ressalva sobre interpretação do contrato e não deve, isoladamente, fundamentar uma classificação de confiabilidade.

Todos os 14 resultados concluídos têm configuração de pedidos verificada, zero respostas não-200 e zero chamadas incompletas. As tentativas aprovadas têm compilação, regressão, aceitação e escopo aprovados. Foram conferidos 104 invariantes de fontes congeladas e resultados. Os tempos cobrem a sessão, modelo e ferramentas do agente; preparação e grading ficam fora. Não houve perfil do limitante nem teste de superioridade estatística. A amostra ainda não sustenta um vencedor ou uma conclusão geral sobre segurança.

Evidências: [snapshot imutável](snapshot.json) e [verificação](verification.json). A leitura e a captura do parcial não modificaram fontes, resultados ou relatórios da execução ativa.
