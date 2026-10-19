# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 120. Concluídas 0. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sonnet-xhigh | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| sol-fast-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| gemini-medium | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |
| gemini-high | 30 | 0 | 0 | 0 | 0 | 30 | n/d | n/d | n/d |

A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.

| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |
|---|---|---|---:|---:|---:|---:|---:|
| route | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| route | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| route | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| route | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| config | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| config | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| retry | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| permission | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| permission | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| feature | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-xhigh | sol-fast-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-xhigh | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-medium | gemini-medium | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| absence | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |

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
