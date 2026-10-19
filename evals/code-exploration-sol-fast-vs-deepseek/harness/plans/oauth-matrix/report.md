# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 210. Concluídas 0. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| deepseek-max | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| sonnet-low | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| sonnet-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| sonnet-high | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| opus-low | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| opus-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |

A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.

| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |
|---|---|---|---:|---:|---:|---:|---:|
| route | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| route | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| route | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| route | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| route | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| route | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| route | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| config | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| config | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| config | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| config | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| retry | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| retry | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| retry | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| permission | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| permission | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| permission | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| permission | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| feature | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| absence | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| absence | deepseek-max | opus-low | 0 | n/d | 0 | 0 | 0 |
| absence | deepseek-max | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-medium | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-medium | opus-low | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-medium | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-high | opus-low | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-high | opus-medium | 0 | n/d | 0 | 0 | 0 |
| absence | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |

Uma razão A/B abaixo de 1 indica menor tempo observado para A. As contagens descrevem observações e não declaram vencedor.

## Limites

- Fast solicitado precisa de confirmação do serviço. Ausência de metadados não confirma atendimento na classe Fast.
- A observação passiva registra parâmetros e metadados selecionados sem redirecionar as chamadas dos provedores.
- Repetições do mesmo caso não são tarefas independentes. A suíte sintética não qualifica o modelo para todo repositório.
- Não mede delegação nativa, nem o efeito causal de Fast. Modelo, rota e esforço variam juntos.
- A identidade da sessão e da requisição não atesta qual modelo foi executado a montante.
- Cache remoto pode persistir entre repetições. Contadores nativos de cache ficam nos resultados.
- Custo informado zero não significa gratuidade. Não estima consumo real das assinaturas.
- Isolamento de descoberta e permissões não equivale a sandbox do sistema operacional.
- O relatório não declara vencedor automaticamente. Falhas, variabilidade, qualidade e confirmação de Fast exigem revisão.
