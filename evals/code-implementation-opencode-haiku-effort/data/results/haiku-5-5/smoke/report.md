# Resultado do implementador

Fase `smoke`. 5 de 5 tentativas iniciadas. 32 chamadas de modelo.

As 5 configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| haiku-low | 1 | 1 | 1 | 1 | 1 | 7.58 | {'completed': 1} |
| haiku-medium | 1 | 1 | 1 | 1 | 1 | 12.24 | {'completed': 1} |
| haiku-high | 1 | 1 | 1 | 1 | 1 | 17.27 | {'completed': 1} |
| haiku-xhigh | 1 | 1 | 1 | 1 | 1 | 53.45 | {'completed': 1} |
| haiku-max | 1 | 1 | 1 | 1 | 1 | 154.71 | {'completed': 1} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
