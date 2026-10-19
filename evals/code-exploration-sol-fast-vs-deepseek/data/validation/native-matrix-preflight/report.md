# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 7. Concluídas 0. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| deepseek-max | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| sonnet-low | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| sonnet-medium | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| sonnet-high | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| opus-low | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |
| opus-medium | 1 | 0 | 0 | 0 | 0 | 1 | n/d | n/d | n/d |

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
