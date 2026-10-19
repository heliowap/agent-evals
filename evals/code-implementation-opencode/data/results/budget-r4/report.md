# Resultado do implementador

Fase `budget`. 6 de 6 tentativas iniciadas. 12 chamadas de modelo.

As seis configurações usam somente o terminal isolado. Este resultado não mede o conjunto normal de ferramentas nativas do OpenCode.

| Configuração | Planejadas | Iniciadas | Aprovação completa | Patch correto | Concluídas | Mediana s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| sonnet-medium | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |
| sonnet-high | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |
| sol-fast-medium | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |
| sol-fast-high | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |
| opus-medium | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |
| deepseek-max | 1 | 1 | 0 | 1 | 0 | n/d | {'budget_exceeded': 1} |

Provas de interrupção aprovadas: 6/6. Gate aprovado: True.
Nessa fase, budget_exceeded é esperado; accepted continua falso porque a sessão é interrompida de propósito.

A mediana inclui sessões concluídas com patches reprovados. Pares de tempo exigem aprovação de ambos no mesmo caso e repetição.

Fast solicitado, esforço enviado e tier atendido ficam separados em summary.json. A identidade observada não atesta o backend a montante.

Nenhum modelo é promovido automaticamente. Repetições não são tarefas independentes. Qualidade do patch e falhas de integração devem ser avaliadas separadamente.
