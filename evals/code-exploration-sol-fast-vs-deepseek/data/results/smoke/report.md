# Sol low com Fast versus DeepSeek max

Veredito: inconclusivo. Piloto descritivo de exploração individual no OpenCode.

Planejadas: 2. Concluídas: 2. Fast servido confirmado: não.

Tempo cobre a invocação OpenCode, ferramentas e recuperações internas. Preparação, auditoria, exportação e correção ficam fora.

| Configuração | Planejadas | Concluídas | Corretas | Mediana das concluídas, s | Mínimo, s | Máximo, s |
|---|---:|---:|---:|---:|---:|---:|
| sol-fast-low | 1 | 1 | 1 | 29.15 | 29.15 | 29.15 |
| deepseek-max | 1 | 1 | 1 | 75.51 | 75.51 | 75.51 |

A tabela de tempo inclui respostas concluídas incorretas. As comparações pareadas abaixo exigem acerto de ambos.

| Caso | Sol correto | DeepSeek correto | Pares com ambos corretos | Mediana Sol/DeepSeek |
|---|---:|---:|---:|---:|
| route | 1 | 1 | 1 | 0.386 |

Uma razão abaixo de 1 significa menor tempo observado para Sol naquele caso. Não equivale a uma conclusão geral.

## Limites

- Se Fast servido estiver desconhecido, o resultado compara Sol com Fast solicitado e encaminhado, sem comprovar atendimento na classe Fast.
- O proxy observador registra somente parâmetros e metadados selecionados. Ambos os modelos passam por ele.
- Repetições do mesmo caso não são tarefas independentes. A suíte sintética não qualifica o modelo para todo repositório.
- Não mede delegação nativa, nem o efeito causal de Fast. Modelo, rota e esforço variam juntos.
- A identidade da sessão e da requisição não atesta qual modelo o proxy executou a montante.
- Cache remoto pode persistir entre repetições. Contadores nativos de cache ficam nos resultados.
- Custo informado zero não significa gratuidade. Não estima consumo real das assinaturas.
- Isolamento de descoberta e permissões não equivale a sandbox do sistema operacional.
- O relatório não declara vencedor automaticamente. Falhas, variabilidade, qualidade e confirmação de Fast exigem revisão.
