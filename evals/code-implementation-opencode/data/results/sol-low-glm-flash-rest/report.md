# Resultado do implementador

Fase `screening`. 99 de 99 tentativas iniciadas. 687 chamadas de modelo.

As 3 configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sol-fast-low | 33 | 33 | 32 | 33 | 33 | 27.48 | {'completed': 32, 'integration_error': 1} |
| glm-flash-high | 33 | 33 | 31 | 32 | 33 | 46.39 | {'completed': 32, 'integration_error': 1} |
| glm-flash-max | 33 | 33 | 29 | 31 | 32 | 212.55 | {'completed': 30, 'integration_error': 2, 'budget_exceeded': 1} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
