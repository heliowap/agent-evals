# Resultado do implementador

Fase `screening`. 18 de 18 tentativas iniciadas. 105 chamadas de modelo.

As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sonnet-medium | 3 | 3 | 3 | 3 | 3 | 26.65 | {'completed': 3} |
| sonnet-high | 3 | 3 | 3 | 3 | 3 | 39.56 | {'completed': 3} |
| sol-fast-medium | 3 | 3 | 3 | 3 | 3 | 43.26 | {'completed': 3} |
| sol-fast-high | 3 | 3 | 3 | 3 | 3 | 66.59 | {'completed': 3} |
| opus-medium | 3 | 3 | 3 | 3 | 3 | 54.89 | {'completed': 3} |
| deepseek-max | 3 | 3 | 3 | 3 | 3 | 193.86 | {'completed': 3} |

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
