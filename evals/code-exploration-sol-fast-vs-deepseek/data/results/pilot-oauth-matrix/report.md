# Comparação de exploradores no OpenCode

Veredito inconclusivo. Piloto descritivo de exploração individual.

Planejadas 210. Concluídas 210. Fast servido confirmado não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Incorretas | Erros | Ausentes | Mediana, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 30 | 30 | 14 | 16 | 0 | 0 | 15.42 | 6.16 | 25.80 |
| deepseek-max | 30 | 30 | 25 | 5 | 0 | 0 | 31.93 | 16.86 | 67.98 |
| sonnet-low | 30 | 30 | 25 | 5 | 0 | 0 | 10.69 | 6.53 | 17.03 |
| sonnet-medium | 30 | 30 | 27 | 3 | 0 | 0 | 9.84 | 8.19 | 19.46 |
| sonnet-high | 30 | 30 | 22 | 8 | 0 | 0 | 11.08 | 9.11 | 15.47 |
| opus-low | 30 | 30 | 27 | 3 | 0 | 0 | 11.89 | 6.73 | 18.32 |
| opus-medium | 30 | 30 | 27 | 3 | 0 | 0 | 14.02 | 9.02 | 22.77 |

A tabela de tempo inclui respostas concluídas incorretas. Comparações pareadas exigem acerto de ambos na mesma tarefa e repetição.

| Caso | Configuração A | Configuração B | Pares corretos | Mediana A/B | A mais rápido | B mais rápido | Empates |
|---|---|---|---:|---:|---:|---:|---:|
| route | sol-fast-low | deepseek-max | 3 | 0.345 | 3 | 0 | 0 |
| route | sol-fast-low | sonnet-low | 1 | 0.994 | 1 | 0 | 0 |
| route | sol-fast-low | sonnet-medium | 3 | 1.069 | 0 | 3 | 0 |
| route | sol-fast-low | sonnet-high | 3 | 1.331 | 1 | 2 | 0 |
| route | sol-fast-low | opus-low | 3 | 1.082 | 1 | 2 | 0 |
| route | sol-fast-low | opus-medium | 3 | 0.972 | 2 | 1 | 0 |
| route | deepseek-max | sonnet-low | 3 | 2.107 | 0 | 3 | 0 |
| route | deepseek-max | sonnet-medium | 5 | 2.712 | 0 | 5 | 0 |
| route | deepseek-max | sonnet-high | 5 | 3.042 | 0 | 5 | 0 |
| route | deepseek-max | opus-low | 5 | 2.649 | 0 | 5 | 0 |
| route | deepseek-max | opus-medium | 5 | 2.346 | 0 | 5 | 0 |
| route | sonnet-low | sonnet-medium | 3 | 1.050 | 1 | 2 | 0 |
| route | sonnet-low | sonnet-high | 3 | 1.083 | 1 | 2 | 0 |
| route | sonnet-low | opus-low | 3 | 0.943 | 2 | 1 | 0 |
| route | sonnet-low | opus-medium | 3 | 0.835 | 3 | 0 | 0 |
| route | sonnet-medium | sonnet-high | 5 | 1.122 | 2 | 3 | 0 |
| route | sonnet-medium | opus-low | 5 | 0.840 | 4 | 1 | 0 |
| route | sonnet-medium | opus-medium | 5 | 0.865 | 5 | 0 | 0 |
| route | sonnet-high | opus-low | 5 | 0.841 | 5 | 0 | 0 |
| route | sonnet-high | opus-medium | 5 | 0.771 | 5 | 0 | 0 |
| route | opus-low | opus-medium | 5 | 0.924 | 4 | 1 | 0 |
| config | sol-fast-low | deepseek-max | 2 | 0.315 | 2 | 0 | 0 |
| config | sol-fast-low | sonnet-low | 2 | 2.118 | 0 | 2 | 0 |
| config | sol-fast-low | sonnet-medium | 2 | 1.771 | 0 | 2 | 0 |
| config | sol-fast-low | sonnet-high | 2 | 1.821 | 0 | 2 | 0 |
| config | sol-fast-low | opus-low | 0 | n/d | 0 | 0 | 0 |
| config | sol-fast-low | opus-medium | 1 | 1.977 | 0 | 1 | 0 |
| config | deepseek-max | sonnet-low | 5 | 5.579 | 0 | 5 | 0 |
| config | deepseek-max | sonnet-medium | 4 | 5.576 | 0 | 4 | 0 |
| config | deepseek-max | sonnet-high | 4 | 5.535 | 0 | 4 | 0 |
| config | deepseek-max | opus-low | 2 | 6.177 | 0 | 2 | 0 |
| config | deepseek-max | opus-medium | 2 | 4.228 | 0 | 2 | 0 |
| config | sonnet-low | sonnet-medium | 4 | 0.822 | 3 | 1 | 0 |
| config | sonnet-low | sonnet-high | 4 | 0.852 | 4 | 0 | 0 |
| config | sonnet-low | opus-low | 2 | 0.918 | 2 | 0 | 0 |
| config | sonnet-low | opus-medium | 2 | 0.698 | 2 | 0 | 0 |
| config | sonnet-medium | sonnet-high | 3 | 0.972 | 2 | 1 | 0 |
| config | sonnet-medium | opus-low | 1 | 1.011 | 0 | 1 | 0 |
| config | sonnet-medium | opus-medium | 2 | 0.973 | 1 | 1 | 0 |
| config | sonnet-high | opus-low | 2 | 1.191 | 0 | 2 | 0 |
| config | sonnet-high | opus-medium | 1 | 0.791 | 1 | 0 | 0 |
| config | opus-low | opus-medium | 0 | n/d | 0 | 0 | 0 |
| retry | sol-fast-low | deepseek-max | 2 | 0.512 | 2 | 0 | 0 |
| retry | sol-fast-low | sonnet-low | 2 | 1.714 | 0 | 2 | 0 |
| retry | sol-fast-low | sonnet-medium | 2 | 2.002 | 0 | 2 | 0 |
| retry | sol-fast-low | sonnet-high | 1 | 1.483 | 0 | 1 | 0 |
| retry | sol-fast-low | opus-low | 2 | 1.236 | 0 | 2 | 0 |
| retry | sol-fast-low | opus-medium | 2 | 1.518 | 0 | 2 | 0 |
| retry | deepseek-max | sonnet-low | 5 | 3.140 | 0 | 5 | 0 |
| retry | deepseek-max | sonnet-medium | 5 | 3.725 | 0 | 5 | 0 |
| retry | deepseek-max | sonnet-high | 2 | 2.458 | 0 | 2 | 0 |
| retry | deepseek-max | opus-low | 5 | 2.316 | 0 | 5 | 0 |
| retry | deepseek-max | opus-medium | 5 | 2.211 | 0 | 5 | 0 |
| retry | sonnet-low | sonnet-medium | 5 | 1.186 | 0 | 5 | 0 |
| retry | sonnet-low | sonnet-high | 2 | 0.786 | 2 | 0 | 0 |
| retry | sonnet-low | opus-low | 5 | 0.737 | 5 | 0 | 0 |
| retry | sonnet-low | opus-medium | 5 | 0.772 | 5 | 0 | 0 |
| retry | sonnet-medium | sonnet-high | 2 | 0.696 | 2 | 0 | 0 |
| retry | sonnet-medium | opus-low | 5 | 0.622 | 5 | 0 | 0 |
| retry | sonnet-medium | opus-medium | 5 | 0.697 | 5 | 0 | 0 |
| retry | sonnet-high | opus-low | 2 | 0.914 | 2 | 0 | 0 |
| retry | sonnet-high | opus-medium | 2 | 1.038 | 1 | 1 | 0 |
| retry | opus-low | opus-medium | 5 | 1.057 | 2 | 3 | 0 |
| permission | sol-fast-low | deepseek-max | 1 | 0.431 | 1 | 0 | 0 |
| permission | sol-fast-low | sonnet-low | 1 | 1.662 | 0 | 1 | 0 |
| permission | sol-fast-low | sonnet-medium | 1 | 1.522 | 0 | 1 | 0 |
| permission | sol-fast-low | sonnet-high | 1 | 1.307 | 0 | 1 | 0 |
| permission | sol-fast-low | opus-low | 1 | 1.062 | 0 | 1 | 0 |
| permission | sol-fast-low | opus-medium | 1 | 0.900 | 1 | 0 | 0 |
| permission | deepseek-max | sonnet-low | 4 | 3.463 | 0 | 4 | 0 |
| permission | deepseek-max | sonnet-medium | 4 | 3.469 | 0 | 4 | 0 |
| permission | deepseek-max | sonnet-high | 4 | 3.263 | 0 | 4 | 0 |
| permission | deepseek-max | opus-low | 4 | 2.477 | 0 | 4 | 0 |
| permission | deepseek-max | opus-medium | 4 | 2.099 | 0 | 4 | 0 |
| permission | sonnet-low | sonnet-medium | 5 | 1.073 | 1 | 4 | 0 |
| permission | sonnet-low | sonnet-high | 5 | 0.766 | 4 | 1 | 0 |
| permission | sonnet-low | opus-low | 5 | 0.742 | 5 | 0 | 0 |
| permission | sonnet-low | opus-medium | 5 | 0.495 | 5 | 0 | 0 |
| permission | sonnet-medium | sonnet-high | 5 | 0.714 | 4 | 1 | 0 |
| permission | sonnet-medium | opus-low | 5 | 0.702 | 5 | 0 | 0 |
| permission | sonnet-medium | opus-medium | 5 | 0.469 | 5 | 0 | 0 |
| permission | sonnet-high | opus-low | 5 | 1.053 | 2 | 3 | 0 |
| permission | sonnet-high | opus-medium | 5 | 0.672 | 5 | 0 | 0 |
| permission | opus-low | opus-medium | 5 | 0.668 | 5 | 0 | 0 |
| feature | sol-fast-low | deepseek-max | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-low | 1 | 0.993 | 1 | 0 | 0 |
| feature | sol-fast-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | sol-fast-low | opus-low | 1 | 1.005 | 0 | 1 | 0 |
| feature | sol-fast-low | opus-medium | 1 | 0.936 | 1 | 0 | 0 |
| feature | deepseek-max | sonnet-low | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | sonnet-medium | 1 | 1.735 | 0 | 1 | 0 |
| feature | deepseek-max | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | deepseek-max | opus-low | 1 | 1.807 | 0 | 1 | 0 |
| feature | deepseek-max | opus-medium | 1 | 1.546 | 0 | 1 | 0 |
| feature | sonnet-low | sonnet-medium | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | sonnet-high | 0 | n/d | 0 | 0 | 0 |
| feature | sonnet-low | opus-low | 2 | 1.076 | 0 | 2 | 0 |
| feature | sonnet-low | opus-medium | 2 | 0.956 | 2 | 0 | 0 |
| feature | sonnet-medium | sonnet-high | 1 | 1.253 | 0 | 1 | 0 |
| feature | sonnet-medium | opus-low | 3 | 1.054 | 0 | 3 | 0 |
| feature | sonnet-medium | opus-medium | 3 | 0.836 | 3 | 0 | 0 |
| feature | sonnet-high | opus-low | 1 | 0.841 | 1 | 0 | 0 |
| feature | sonnet-high | opus-medium | 1 | 0.605 | 1 | 0 | 0 |
| feature | opus-low | opus-medium | 5 | 0.850 | 5 | 0 | 0 |
| absence | sol-fast-low | deepseek-max | 5 | 0.372 | 5 | 0 | 0 |
| absence | sol-fast-low | sonnet-low | 5 | 1.356 | 1 | 4 | 0 |
| absence | sol-fast-low | sonnet-medium | 5 | 0.996 | 3 | 2 | 0 |
| absence | sol-fast-low | sonnet-high | 5 | 0.811 | 4 | 1 | 0 |
| absence | sol-fast-low | opus-low | 5 | 1.294 | 1 | 4 | 0 |
| absence | sol-fast-low | opus-medium | 5 | 0.665 | 4 | 1 | 0 |
| absence | deepseek-max | sonnet-low | 5 | 3.040 | 0 | 5 | 0 |
| absence | deepseek-max | sonnet-medium | 5 | 2.188 | 0 | 5 | 0 |
| absence | deepseek-max | sonnet-high | 5 | 1.957 | 0 | 5 | 0 |
| absence | deepseek-max | opus-low | 5 | 3.018 | 0 | 5 | 0 |
| absence | deepseek-max | opus-medium | 5 | 1.820 | 0 | 5 | 0 |
| absence | sonnet-low | sonnet-medium | 5 | 0.735 | 5 | 0 | 0 |
| absence | sonnet-low | sonnet-high | 5 | 0.642 | 5 | 0 | 0 |
| absence | sonnet-low | opus-low | 5 | 0.993 | 3 | 2 | 0 |
| absence | sonnet-low | opus-medium | 5 | 0.520 | 5 | 0 | 0 |
| absence | sonnet-medium | sonnet-high | 5 | 0.838 | 4 | 1 | 0 |
| absence | sonnet-medium | opus-low | 5 | 1.365 | 0 | 5 | 0 |
| absence | sonnet-medium | opus-medium | 5 | 0.722 | 4 | 1 | 0 |
| absence | sonnet-high | opus-low | 5 | 1.544 | 0 | 5 | 0 |
| absence | sonnet-high | opus-medium | 5 | 0.862 | 3 | 2 | 0 |
| absence | opus-low | opus-medium | 5 | 0.524 | 5 | 0 | 0 |

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
