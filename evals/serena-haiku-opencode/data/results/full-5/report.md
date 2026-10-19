# Haiku com e sem Serena no OpenCode

Piloto descritivo. Nenhum vencedor automático. Problemas distintos por papel: exploration=3, implementation=3. Repetições não são tarefas independentes.

Planejadas 120; tentadas 120; concluídas 110.

| Papel | Configuração | Aprovação/planejadas | Concluídas | Mediana s | Faixa s | MCP usado | Erros MCP |
|---|---|---:|---:|---:|---:|---:|---:|
| exploration | haiku-medium-native | 9/15 | 13 | 19.31 | 13.06–31.94 | 0 | 0 |
| exploration | haiku-medium-serena | 9/15 | 14 | 21.95 | 14.91–38.46 | 5 | 0 |
| exploration | haiku-high-native | 12/15 | 14 | 21.81 | 15.88–41.65 | 0 | 0 |
| exploration | haiku-high-serena | 7/15 | 13 | 26.31 | 16.80–54.02 | 7 | 0 |
| implementation | haiku-medium-native | 9/15 | 14 | 37.83 | 15.18–865.69 | 0 | 0 |
| implementation | haiku-medium-serena | 9/15 | 14 | 34.97 | 15.96–88.63 | 1 | 0 |
| implementation | haiku-high-native | 9/15 | 14 | 62.54 | 14.96–94.57 | 0 | 0 |
| implementation | haiku-high-serena | 9/15 | 14 | 55.90 | 22.56–92.28 | 2 | 0 |

O tempo principal começa antes de iniciar o servidor OpenCode e inclui inicialização fria MCP/LSP, processamento remoto, ferramentas e recuperações internas. Preparação, exportação e correção aparecem separadamente no JSON; o total por trial inclui essas etapas. Nenhum custo de indexação é subtraído.

A mediana inclui todas as respostas concluídas, inclusive reprovadas. Razões pareadas usam somente casos e repetições em que ambos passaram; rejeições e ausências permanecem no denominador e nas observações completas.

A condição Serena permanece no denominador mesmo sem uso. initial_instructions não conta como uso útil. Prontidão do catálogo mede somente a região observável do processo MCP; não isola indexação nem atribui diferenças causalmente ao provedor.

Terminal e corretor executam em Docker sem rede. Serena/LSP em host possuem confinamento de projeto, configuração e paths; não possuem namespace OS. Autenticação, wire e esforço observados não certificam a identidade real executada a montante. Custo informado zero não estima assinatura nem gratuidade.
