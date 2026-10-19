# Resultado do implementador

Fase `screening`. 9 de 9 tentativas iniciadas. 75 chamadas de modelo.

As 3 configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sol-fast-low | 3 | 3 | 3 | 3 | 3 | 38.50 | {'completed': 3} |
| glm-flash-high | 3 | 3 | 3 | 3 | 3 | 105.96 | {'completed': 3} |
| glm-flash-max | 3 | 3 | 2 | 2 | 3 | 607.44 | {'completed': 3} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
