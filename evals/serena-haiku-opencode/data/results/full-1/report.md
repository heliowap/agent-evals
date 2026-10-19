# Haiku com e sem Serena no OpenCode

Piloto descritivo. Nenhum vencedor automático. Problemas distintos por papel: exploration=3, implementation=3. Repetições não são tarefas independentes.

Planejadas 120; tentadas 0; concluídas 0.

| Papel | Configuração | Aprovação/planejadas | Concluídas | Mediana s | Faixa s | MCP usado | Erros MCP |
|---|---|---:|---:|---:|---:|---:|---:|
| exploration | haiku-medium-native | 0/15 | 0 | n/d | n/d | 0 | 0 |
| exploration | haiku-medium-serena | 0/15 | 0 | n/d | n/d | 0 | 0 |
| exploration | haiku-high-native | 0/15 | 0 | n/d | n/d | 0 | 0 |
| exploration | haiku-high-serena | 0/15 | 0 | n/d | n/d | 0 | 0 |
| implementation | haiku-medium-native | 0/15 | 0 | n/d | n/d | 0 | 0 |
| implementation | haiku-medium-serena | 0/15 | 0 | n/d | n/d | 0 | 0 |
| implementation | haiku-high-native | 0/15 | 0 | n/d | n/d | 0 | 0 |
| implementation | haiku-high-serena | 0/15 | 0 | n/d | n/d | 0 | 0 |

O tempo principal começa antes de iniciar o servidor OpenCode e inclui inicialização fria MCP/LSP, processamento remoto, ferramentas e recuperações internas. Preparação, exportação e correção aparecem separadamente no JSON; o total por trial inclui essas etapas. Nenhum custo de indexação é subtraído.

A mediana inclui todas as respostas concluídas, inclusive reprovadas. Razões pareadas usam somente casos e repetições em que ambos passaram; rejeições e ausências permanecem no denominador e nas observações completas.

A condição Serena permanece no denominador mesmo sem uso. initial_instructions não conta como uso útil. Prontidão do catálogo mede somente a região observável do processo MCP; não isola indexação nem atribui diferenças causalmente ao provedor.

Terminal e corretor executam em Docker sem rede. Serena/LSP em host possuem confinamento de projeto, configuração e paths; não possuem namespace OS. Autenticação, wire e esforço observados não certificam a identidade real executada a montante. Custo informado zero não estima assinatura nem gratuidade.
