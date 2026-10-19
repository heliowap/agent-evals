# Piloto TB4 — GLM-5.3-Flash vs SWE-2

Subconjunto de 3 tarefas, k=1. Não é pontuação oficial nem amostra suficiente para um ranking geral.

**Concluído: 6/6 trials, nenhum sucesso integral em ambos os modelos.** O job durou cerca de 5h08, incluindo interrupções. OpenCode 2.0.24/high nos dois braços; dataset e tarefas preservados. Não há vencedor demonstrado.

| Modelo (high) | Concluídos | Passou | Erros | Custo informado USD |
| --- | ---: | ---: | ---: | ---: |
| opencode-go/glm-5.3-flash | 3/3 | 0 | 1 | 0.928553 (3/3 trials) |
| cli_proxy_openai/devin/swe-2 | 3/3 | 0 | 1 | não informado |

| Tarefa | Modelo | Reward | Erro | Tempo agente (s) |
| --- | --- | ---: | --- | ---: |
| terminal-bench/interleaved-vigenere | cli_proxy_openai/devin/swe-2 | 0.0 | NonZeroAgentExitCodeError | 2987.19 |
| terminal-bench/interleaved-vigenere | opencode-go/glm-5.3-flash | 0.0 | — | 5886.91 |
| terminal-bench/session-window-debug | opencode-go/glm-5.3-flash | 0.0 | NonZeroAgentExitCodeError | 1596.4 |
| terminal-bench/session-window-debug | cli_proxy_openai/devin/swe-2 | 0.0 | — | 760.44 |
| terminal-bench/wal-recovery-ordering | cli_proxy_openai/devin/swe-2 | 0.0 | — | 367.41 |
| terminal-bench/wal-recovery-ordering | opencode-go/glm-5.3-flash | 0.0 | — | 1202.49 |

Erros permanecem no denominador. Custo ausente/zero não comprova gratuidade, especialmente no CLI Proxy. Custos são telemetria do harness, não fatura; testes de integração anteriores não entram nessa soma.

Os erros foram streaming interno do provider para GLM em `session-window-debug` e socket fechado para SWE-2 em `interleaved-vigenere`. A suíte de verificação rodou nos seis trials, inclusive sobre os artefatos dos dois trials com erro. Reward exige sucesso integral; os testes individuais abaixo são diagnóstico, **não outra pontuação oficial**:

| Tarefa | GLM: testes aprovados | SWE-2: testes aprovados |
| --- | ---: | ---: |
| session-window-debug | 4/7 | 4/7 |
| wal-recovery-ordering | 95/97 | 94/97 |
| interleaved-vigenere | 3/6 | 2/6 |

Fonte: `verifier/ctrf.json` em cada pasta de trial. Não somar os testes como ranking: as suítes têm pesos e tamanhos diferentes.

Além dos trials finais, duas tentativas interrompidas de GLM foram preservadas em `../../interruptions/`; registraram custo parcial de USD 0,31619886. Somado aos trials finais: USD 1,24475160 de telemetria observada, sem smoke/auxiliares não registrados. Interrupções, amostra pequena e erros de API limitam a interpretação; nada foi publicado. Cleanup verificado: nenhum container do piloto permanece e a porta da ponte está fechada.

Tokens de entrada incluem cache; não somar o cache novamente. Durações refletem Docker Desktop local, potencialmente com emulação amd64 no Mac ARM64. Não foi calculado IC oficial porque k=1.
