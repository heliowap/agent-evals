# Resultado do implementador

Fase `screening`. 216 de 216 tentativas iniciadas. 1065 chamadas de modelo.

As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sonnet-medium | 36 | 36 | 33 | 33 | 36 | 16.92 | {'completed': 36} |
| sonnet-high | 36 | 36 | 36 | 36 | 36 | 22.29 | {'completed': 36} |
| sol-fast-medium | 36 | 36 | 33 | 33 | 36 | 29.26 | {'completed': 36} |
| sol-fast-high | 36 | 36 | 33 | 33 | 36 | 37.07 | {'completed': 36} |
| opus-medium | 36 | 36 | 33 | 33 | 36 | 31.71 | {'completed': 36} |
| deepseek-max | 36 | 36 | 34 | 34 | 36 | 89.47 | {'completed': 36} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
