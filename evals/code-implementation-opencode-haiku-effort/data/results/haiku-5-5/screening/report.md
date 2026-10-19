# Resultado do implementador

Fase `screening`. 100 de 180 tentativas iniciadas. 763 chamadas de modelo.

As 5 configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| haiku-low | 36 | 20 | 20 | 20 | 20 | 22.04 | {'completed': 20, 'not_run': 16} |
| haiku-medium | 36 | 20 | 20 | 20 | 20 | 36.13 | {'completed': 20, 'not_run': 16} |
| haiku-high | 36 | 20 | 20 | 20 | 20 | 64.65 | {'completed': 20, 'not_run': 16} |
| haiku-xhigh | 36 | 20 | 20 | 20 | 20 | 136.22 | {'completed': 20, 'not_run': 16} |
| haiku-max | 36 | 20 | 6 | 6 | 19 | 167.43 | {'completed': 19, 'infra_error': 1, 'not_run': 16} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
