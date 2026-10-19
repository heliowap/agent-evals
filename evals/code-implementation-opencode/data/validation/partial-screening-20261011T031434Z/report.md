# Parcial do implementador

Corte UTC: 2026-10-11T03:14:34.452010+00:00.

140 de 216 trials finalizados. A comparação usa 138 trials em 23 blocos completos, com 23 execuções por candidato. São 12 tarefas distintas.

| Candidato | Aprovação | Mediana s | Mínimo s | Máximo s | Chamadas |
|---|---:|---:|---:|---:|---:|
| sonnet-high | 23/23 | 22.34 | 11.55 | 38.85 | 89 |
| deepseek-max | 22/23 | 87.40 | 15.93 | 209.76 | 217 |
| sonnet-medium | 20/23 | 16.94 | 9.88 | 28.97 | 87 |
| sol-fast-medium | 20/23 | 30.28 | 17.86 | 46.37 | 96 |
| opus-medium | 20/23 | 34.33 | 16.85 | 46.18 | 99 |
| sol-fast-high | 20/23 | 40.61 | 21.09 | 61.15 | 97 |

125/138 aprovações completas e 685 chamadas no corte balanceado. Os tempos incluem sessões concluídas com patches reprovados; preparação e avaliação externa ficam fora. Não houve respostas não-200, chamadas incompletas ou erros operacionais nesse corte.

As 13 reprovações estão em py-money-contract. Fora desse caso, todos os candidatos aprovaram 20/20. 11 reprovações pararam primeiro em .1. O enunciado não proíbe explicitamente .1 e 1., embora a aceitação privada proíba ambos. A vantagem em aprovação precisa desta ressalva; não se presume que todos os demais critérios desses patches passariam.

Fast foi solicitado nos dois Sol; o tier terminal observado foi default em todas as 23 sessões de cada Sol.

Não há vencedor definido. As repetições não são tarefas independentes, a cobertura ainda está incompleta e não há perfil de desempenho para atribuir as diferenças a um limitante.

snapshot.json conserva as métricas do corte e o hash de cada result.json de origem. As fontes congeladas, os resultados e os gates anteriores foram preservados.
