# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 120. Concluídas 103. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sonnet-xhigh | 30 | 30 | 24 | 6 | 0 | 0 | 15.82 | 11.48 | 22.19 |
| sol-fast-medium | 30 | 30 | 17 | 13 | 0 | 0 | 17.23 | 8.57 | 22.55 |
| gemini-medium | 30 | 26 | 23 | 3 | 4 | 0 | 75.48 | 39.14 | 120.18 |
| gemini-high | 30 | 17 | 12 | 5 | 13 | 0 | 108.86 | 75.59 | 158.86 |

A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.

| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |
|---|---|---|---:|---:|---:|---:|---:|
| route | sonnet-xhigh | sol-fast-medium | 5 | 1.036 | 2 | 3 | 0 |
| route | sonnet-xhigh | gemini-medium | 5 | 0.174 | 5 | 0 | 0 |
| route | sonnet-xhigh | gemini-high | 1 | 0.123 | 1 | 0 | 0 |
| route | sol-fast-medium | gemini-medium | 5 | 0.184 | 5 | 0 | 0 |
| route | sol-fast-medium | gemini-high | 1 | 0.135 | 1 | 0 | 0 |
| route | gemini-medium | gemini-high | 1 | 0.705 | 1 | 0 | 0 |
| config | sonnet-xhigh | sol-fast-medium | 1 | 0.909 | 1 | 0 | 0 |
| config | sonnet-xhigh | gemini-medium | 5 | 0.247 | 5 | 0 | 0 |
| config | sonnet-xhigh | gemini-high | 5 | 0.151 | 5 | 0 | 0 |
| config | sol-fast-medium | gemini-medium | 1 | 0.348 | 1 | 0 | 0 |
| config | sol-fast-medium | gemini-high | 1 | 0.167 | 1 | 0 | 0 |
| config | gemini-medium | gemini-high | 5 | 0.701 | 5 | 0 | 0 |
| retry | sonnet-xhigh | sol-fast-medium | 2 | 1.173 | 1 | 1 | 0 |
| retry | sonnet-xhigh | gemini-medium | 3 | 0.185 | 3 | 0 | 0 |
| retry | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-medium | gemini-medium | 2 | 0.174 | 2 | 0 | 0 |
| retry | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| retry | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| permission | sonnet-xhigh | sol-fast-medium | 1 | 0.710 | 1 | 0 | 0 |
| permission | sonnet-xhigh | gemini-medium | 3 | 0.226 | 3 | 0 | 0 |
| permission | sonnet-xhigh | gemini-high | 1 | 0.163 | 1 | 0 | 0 |
| permission | sol-fast-medium | gemini-medium | 1 | 0.318 | 1 | 0 | 0 |
| permission | sol-fast-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| permission | gemini-medium | gemini-high | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-xhigh | sol-fast-medium | 1 | 1.120 | 0 | 1 | 0 |
| feature | sonnet-xhigh | gemini-medium | 1 | 0.351 | 1 | 0 | 0 |
| feature | sonnet-xhigh | gemini-high | 1 | 0.236 | 1 | 0 | 0 |
| feature | sol-fast-medium | gemini-medium | 3 | 0.286 | 3 | 0 | 0 |
| feature | sol-fast-medium | gemini-high | 3 | 0.158 | 3 | 0 | 0 |
| feature | gemini-medium | gemini-high | 5 | 0.671 | 5 | 0 | 0 |
| absence | sonnet-xhigh | sol-fast-medium | 5 | 1.205 | 0 | 5 | 0 |
| absence | sonnet-xhigh | gemini-medium | 2 | 0.270 | 2 | 0 | 0 |
| absence | sonnet-xhigh | gemini-high | 0 | n/d | 0 | 0 | 0 |
| absence | sol-fast-medium | gemini-medium | 2 | 0.228 | 2 | 0 | 0 |
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
