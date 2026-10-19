# Resultado do implementador

Fase `budget`. 1 de 6 tentativas iniciadas. 2 chamadas de modelo.

As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sonnet-medium | 1 | 0 | 0 | 0 | 0 | n/d | {'not_run': 1} |
| sonnet-high | 1 | 0 | 0 | 0 | 0 | n/d | {'not_run': 1} |
| sol-fast-medium | 1 | 0 | 0 | 0 | 0 | n/d | {'not_run': 1} |
| sol-fast-high | 1 | 1 | 0 | 0 | 0 | n/d | {'infra_error': 1} |
| opus-medium | 1 | 0 | 0 | 0 | 0 | n/d | {'not_run': 1} |
| deepseek-max | 1 | 0 | 0 | 0 | 0 | n/d | {'not_run': 1} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
