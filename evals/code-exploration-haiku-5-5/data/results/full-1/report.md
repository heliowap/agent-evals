# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 150. Concluídas 150. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Limite de saída | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| haiku-low | 30 | 30 | 20 | 10 | 0 | 0 | 0 | 13.92 | 6.90 | 23.73 |
| haiku-medium | 30 | 30 | 20 | 10 | 0 | 0 | 0 | 18.03 | 12.19 | 24.42 |
| haiku-high | 30 | 30 | 28 | 2 | 0 | 0 | 0 | 22.40 | 14.58 | 63.18 |
| haiku-xhigh | 30 | 30 | 28 | 2 | 0 | 0 | 0 | 39.30 | 23.50 | 63.13 |
| haiku-max | 30 | 30 | 24 | 6 | 0 | 0 | 0 | 135.46 | 84.95 | 202.75 |

Limite terminal de saída é uma categoria própria, fora de incorretas e erros comuns. A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.

| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |
|---|---|---|---:|---:|---:|---:|---:|
| route | haiku-low | haiku-medium | 3 | 0.767 | 3 | 0 | 0 |
| route | haiku-low | haiku-high | 3 | 0.431 | 3 | 0 | 0 |
| route | haiku-low | haiku-xhigh | 4 | 0.298 | 4 | 0 | 0 |
| route | haiku-low | haiku-max | 3 | 0.098 | 3 | 0 | 0 |
| route | haiku-medium | haiku-high | 3 | 1.020 | 1 | 2 | 0 |
| route | haiku-medium | haiku-xhigh | 4 | 0.526 | 4 | 0 | 0 |
| route | haiku-medium | haiku-max | 3 | 0.143 | 3 | 0 | 0 |
| route | haiku-high | haiku-xhigh | 4 | 0.554 | 3 | 1 | 0 |
| route | haiku-high | haiku-max | 2 | 0.304 | 2 | 0 | 0 |
| route | haiku-xhigh | haiku-max | 3 | 0.309 | 3 | 0 | 0 |
| config | haiku-low | haiku-medium | 1 | 0.959 | 1 | 0 | 0 |
| config | haiku-low | haiku-high | 1 | 0.442 | 1 | 0 | 0 |
| config | haiku-low | haiku-xhigh | 1 | 0.284 | 1 | 0 | 0 |
| config | haiku-low | haiku-max | 1 | 0.113 | 1 | 0 | 0 |
| config | haiku-medium | haiku-high | 5 | 0.829 | 5 | 0 | 0 |
| config | haiku-medium | haiku-xhigh | 5 | 0.426 | 5 | 0 | 0 |
| config | haiku-medium | haiku-max | 4 | 0.137 | 4 | 0 | 0 |
| config | haiku-high | haiku-xhigh | 5 | 0.573 | 5 | 0 | 0 |
| config | haiku-high | haiku-max | 4 | 0.206 | 4 | 0 | 0 |
| config | haiku-xhigh | haiku-max | 4 | 0.404 | 4 | 0 | 0 |
| retry | haiku-low | haiku-medium | 2 | 0.835 | 2 | 0 | 0 |
| retry | haiku-low | haiku-high | 5 | 0.692 | 5 | 0 | 0 |
| retry | haiku-low | haiku-xhigh | 4 | 0.313 | 4 | 0 | 0 |
| retry | haiku-low | haiku-max | 5 | 0.126 | 5 | 0 | 0 |
| retry | haiku-medium | haiku-high | 2 | 0.758 | 2 | 0 | 0 |
| retry | haiku-medium | haiku-xhigh | 1 | 0.364 | 1 | 0 | 0 |
| retry | haiku-medium | haiku-max | 2 | 0.131 | 2 | 0 | 0 |
| retry | haiku-high | haiku-xhigh | 4 | 0.460 | 4 | 0 | 0 |
| retry | haiku-high | haiku-max | 5 | 0.197 | 5 | 0 | 0 |
| retry | haiku-xhigh | haiku-max | 4 | 0.382 | 4 | 0 | 0 |
| permission | haiku-low | haiku-medium | 3 | 1.019 | 1 | 2 | 0 |
| permission | haiku-low | haiku-high | 4 | 0.692 | 4 | 0 | 0 |
| permission | haiku-low | haiku-xhigh | 4 | 0.429 | 4 | 0 | 0 |
| permission | haiku-low | haiku-max | 4 | 0.108 | 4 | 0 | 0 |
| permission | haiku-medium | haiku-high | 3 | 0.663 | 2 | 1 | 0 |
| permission | haiku-medium | haiku-xhigh | 3 | 0.422 | 3 | 0 | 0 |
| permission | haiku-medium | haiku-max | 3 | 0.135 | 3 | 0 | 0 |
| permission | haiku-high | haiku-xhigh | 5 | 0.638 | 5 | 0 | 0 |
| permission | haiku-high | haiku-max | 5 | 0.169 | 5 | 0 | 0 |
| permission | haiku-xhigh | haiku-max | 5 | 0.258 | 5 | 0 | 0 |
| feature | haiku-low | haiku-medium | 0 | n/d | 0 | 0 | 0 |
| feature | haiku-low | haiku-high | 1 | 0.635 | 1 | 0 | 0 |
| feature | haiku-low | haiku-xhigh | 1 | 0.314 | 1 | 0 | 0 |
| feature | haiku-low | haiku-max | 0 | n/d | 0 | 0 | 0 |
| feature | haiku-medium | haiku-high | 1 | 0.619 | 1 | 0 | 0 |
| feature | haiku-medium | haiku-xhigh | 1 | 0.394 | 1 | 0 | 0 |
| feature | haiku-medium | haiku-max | 0 | n/d | 0 | 0 | 0 |
| feature | haiku-high | haiku-xhigh | 4 | 0.566 | 4 | 0 | 0 |
| feature | haiku-high | haiku-max | 1 | 0.139 | 1 | 0 | 0 |
| feature | haiku-xhigh | haiku-max | 1 | 0.193 | 1 | 0 | 0 |
| absence | haiku-low | haiku-medium | 5 | 0.621 | 5 | 0 | 0 |
| absence | haiku-low | haiku-high | 5 | 0.507 | 5 | 0 | 0 |
| absence | haiku-low | haiku-xhigh | 5 | 0.334 | 5 | 0 | 0 |
| absence | haiku-low | haiku-max | 5 | 0.084 | 5 | 0 | 0 |
| absence | haiku-medium | haiku-high | 5 | 0.816 | 4 | 1 | 0 |
| absence | haiku-medium | haiku-xhigh | 5 | 0.537 | 5 | 0 | 0 |
| absence | haiku-medium | haiku-max | 5 | 0.165 | 5 | 0 | 0 |
| absence | haiku-high | haiku-xhigh | 5 | 0.658 | 5 | 0 | 0 |
| absence | haiku-high | haiku-max | 5 | 0.209 | 5 | 0 | 0 |
| absence | haiku-xhigh | haiku-max | 5 | 0.318 | 5 | 0 | 0 |

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
