# Resultado do implementador

Fase `smoke`. 6 de 6 tentativas iniciadas. 21 chamadas de modelo.

As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sonnet-medium | 1 | 1 | 1 | 1 | 1 | 30.01 | {'completed': 1} |
| sonnet-high | 1 | 1 | 1 | 1 | 1 | 19.63 | {'completed': 1} |
| sol-fast-medium | 1 | 1 | 1 | 1 | 1 | 13.02 | {'completed': 1} |
| sol-fast-high | 1 | 1 | 1 | 1 | 1 | 24.71 | {'completed': 1} |
| opus-medium | 1 | 1 | 1 | 1 | 1 | 9.62 | {'completed': 1} |
| deepseek-max | 1 | 1 | 1 | 1 | 1 | 9.40 | {'completed': 1} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
