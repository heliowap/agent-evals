# Resultado do piloto

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot-20261010-r1/report.md). Os links e comandos desta versão acompanham a organização por tema.


Veredito: execução bloqueada pela rede. Não há resultado sobre o ganho da instrução.

Modelo solicitado: Codex CLI 0.162.1, GPT-6.1 Sol, effort xhigh.
Foram 72 execuções planejadas, 1 tentada, 0 concluídas e 71 não iniciadas.
A primeira tentativa, `regression`, condição `empty`, falhou antes da resposta
do modelo com `workspace routing discovery failed`. A falha não é um erro de
qualidade da condição vazia e não deve entrar como reprovação da tarefa.

A auditoria prévia confirmou os contextos equivalentes fora do tratamento.
O diagnóstico registrou rede desabilitada no sandbox controlador e falha de
resolução DNS para chatgpt.com. Não havia proxy herdado ou endpoint customizado
de ChatGPT/OpenAI no arquivo de configuração do usuário. Os dados não permitem
concluir se o trecho melhora acerto, custo, tempo ou comportamento.

Evidência: [diagnóstico de conexão](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot-20261010-r1/connectivity-diagnostic.json),
[tentativa](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot-20261010-r1/trial-0001/result.json), [eventos](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot-20261010-r1/trial-0001/turn-1.jsonl) e
[auditoria de contexto](instrucoes-agents/agentsmd-detfirst-isolated/results/pilot-20261010-r1/preflight.json).

Os passes abaixo são automáticos; dois controles exigem revisão cega adicional.

| Caso | Variante | Planejadas | Concluídas | Passes automáticos | Tempo mediano, s |
|---|---|---:|---:|---:|---:|
| count | empty | 3 | 0 | 0 | — |
| count | deterministic | 3 | 0 | 0 | — |
| money | empty | 3 | 0 | 0 | — |
| money | deterministic | 3 | 0 | 0 | — |
| convert | empty | 3 | 0 | 0 | — |
| convert | deterministic | 3 | 0 | 0 | — |
| rename | empty | 3 | 0 | 0 | — |
| rename | deterministic | 3 | 0 | 0 | — |
| project_tool | empty | 3 | 0 | 0 | — |
| project_tool | deterministic | 3 | 0 | 0 | — |
| repeat | empty | 3 | 0 | 0 | — |
| repeat | deterministic | 3 | 0 | 0 | — |
| guardrail | empty | 3 | 0 | 0 | — |
| guardrail | deterministic | 3 | 0 | 0 | — |
| regression | empty | 3 | 0 | 0 | — |
| regression | deterministic | 3 | 0 | 0 | — |
| out_of_scope | empty | 3 | 0 | 0 | — |
| out_of_scope | deterministic | 3 | 0 | 0 | — |
| judgment | empty | 3 | 0 | 0 | — |
| judgment | deterministic | 3 | 0 | 0 | — |
| independent | empty | 3 | 0 | 0 | — |
| independent | deterministic | 3 | 0 | 0 | — |
| dependent | empty | 3 | 0 | 0 | — |
| dependent | deterministic | 3 | 0 | 0 | — |

Estados: {"infra_error": 1, "not_run": 71}

Tokens de entrada, saída e cache estão nos resultados individuais. Cache não é somado novamente à entrada; custo monetário não é inferido. Campos ausentes permanecem desconhecidos. Nenhum total de tokens é inferido sem validar sobreposições.
Tempo cobre as invocações do agente, incluindo boot e eventual retry interno; exclui preparação e correção. Não é throughput do modelo.
