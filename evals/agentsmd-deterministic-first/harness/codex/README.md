# Eval isolado de Deterministic first

Estado: piloto concluído em 10/10/2026. As 72 execuções passaram, incluindo os
12 controles revisados pela rubrica. Houve empate de qualidade e maior duração
observada com o trecho. Consulte a [análise completa](../../agentsmd-codex-pilot-analise.md).

Compara Codex CLI 0.162.1, `gpt-6.1-sol`, reasoning effort `xhigh`, com dois
arquivos globais de instruções privados. `variants/empty/AGENTS.md` tem zero
bytes. `variants/deterministic/AGENTS.md` contém apenas o trecho fornecido pelo
usuário, sem reescrita. O `AGENTS.md` global real não é alterado.

Este experimento mede o efeito do trecho sobre a configuração básica do CLI.
Não mede seu efeito marginal no conjunto completo de instruções e skills do
usuário. O prompt de sistema do modelo e as instruções internas do CLI continuam
iguais nas duas condições. Eles podem já induzir parte do comportamento testado.
O experimento avalia o trecho inteiro; não atribui causalidade a cada frase.

## Hipóteses e critérios

Hipótese principal: o trecho aumenta a proporção de tarefas entregues corretamente.
Hipóteses secundárias: reduz consumo e duração para entregas corretas, aumenta a
reutilização de ferramentas e cria verificações que detectam reincidência de erros.
Possíveis prejuízos: scripts desnecessários, alterações fora do escopo, excesso de
automação para decisões subjetivas e execução concorrente de etapas dependentes.

Acerto e obediência são medidas separadas. Usar um script, executar comandos em
paralelo ou criar um teste não aumenta a nota de resultado por si só. A exceção é
quando a própria tarefa pede uma prevenção verificável. Nesse caso, o corretor
introduz o defeito e verifica se a proteção funciona, inclusive em casos válidos.

O piloto tem 12 tarefas sintéticas, duas condições e três repetições: 72 execuções
em 36 pares. As repetições medem variabilidade sobre os mesmos dados. Não são 36
tarefas independentes. Três repetições não sustentam uma conclusão de velocidade;
um estudo confirmatório usaria pelo menos cinco e novos casos reais.

| Caso | Grupo | Resultado avaliado |
|---|---|---|
| count | actions | Contagem exata com limites de horário e números que confundem buscas ingênuas |
| money | actions | Soma inteira, com valores negativos e filtros por moeda/estado |
| convert | actions | Conversão com tipos corretos, zeros iniciais, Unicode, aspas e quebras de linha |
| rename | actions | Renomeação em vários módulos, preservando nome semelhante e comportamento |
| project_tool | actions | Relatório correto quando o projeto já oferece uma ferramenta |
| repeat | actions | Três resumos corretos em dois turnos da mesma sessão |
| guardrail | rules | Checker rejeita chamadas proibidas e aceita comentários, strings e métodos |
| regression | rules | Código correto e teste que falha quando o defeito reaparece |
| out_of_scope | controls | Review correto e proposta de prevenção, sem editar arquivos |
| judgment | controls | Texto adequado, com todos os fatos preservados e sem alterações adicionais |
| independent | actions | Resultados reais de três comandos; sobreposição é observação secundária |
| dependent | controls | Configuração e artefato gerado correspondem ao mesmo estado |

Para `out_of_scope` e `judgment`, os checks automáticos são parciais. A aceitação
depende da revisão cega definida em `REVIEW.md`. Não contar esses checks como
prova suficiente de qualidade. Os grupos têm composição artificial; a média
não estima o ganho no trabalho cotidiano do usuário.

## Isolamento e evidência

Cada execução tem diretório de trabalho, repositório Git, estado do Codex e
temporários próprios. O executor usa um dicionário de ambiente específico do
processo filho e aponta a configuração suportada `CODEX_HOME` para esse estado.
Não muda `HOME`, a variável do shell do usuário ou sua configuração instalada.
Somente o arquivo de autenticação indicado é copiado, com permissão 0600. Ele
fica no estado temporário, fora dos resultados, e não é impresso.

O CLI roda com `--no-daemon`, sandbox `workspace-write` e aprovação `never`.
Plugins, apps, hooks, memória e multiagente ficam desabilitados na configuração
privada. O diretório temporário tem um Git próprio. Não há symlinks para a
configuração global, nem skills ou instruções do executor dentro dos casos.

Antes de qualquer inferência, `codex debug prompt-input` revela as instruções
que serão apresentadas ao modelo. A preparação descobre e desabilita cada skill
pelo caminho de seu `SKILL.md` e repete a inspeção. Na versão fixada, desabilitar
só o caminho da pasta não remove a skill. A execução para se ainda houver um
catálogo de skills, se a condição vazia tiver instruções de `AGENTS.md`, ou se a
outra condição não contiver exatamente o trecho esperado. `isolation.json`
preserva o contexto inspecionado, hashes e configuração solicitada.

Esse isolamento impede herança automática de instruções. Não é isolamento
completo de leitura do sistema operacional: um comando do agente ainda poderia
ler arquivos fora do caso. O gabarito fica no processo controlador, não no
diretório de trabalho. A inspeção do contexto não é captura do request HTTP ao
provedor. A versão, modelo e effort são fixados nos argumentos/configuração;
o serviço remoto e sua implementação não são controlados por este estudo.

As instruções carregadas por Codex combinam escopos globais e locais. A
documentação oficial descreve essa descoberta em
[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
As opções de configuração estão na
[referência oficial](https://learn.chatgpt.com/docs/config-file/config-reference).
O comportamento efetivo de desabilitar skills é verificado pelo CLI instalado.

## Execução

Dependências: Python 3.10+, Git e a versão indicada do Codex CLI, com login já
disponível. As tarefas não dependem de pacotes Python externos.

```sh
cd ~/VSCode/Lab/evals/instrucoes-agents/agentsmd-detfirst-isolated
python3 -m unittest -v test_eval.py
python3 run.py preflight --out validation/isolated-context
python3 run.py plan --out plans/pilot
python3 run.py run --out results/pilot
python3 run.py report results/pilot
python3 run.py blind results/pilot
```

O comando `plan` é offline. `run` usa o modelo e effort escolhidos pelo usuário,
sem fallback, e consome a cota do login. `--auth-file /caminho/auth.json` permite
selecionar o arquivo de autenticação. O padrão é o do Codex instalado. Não colocar
credenciais no terminal ou nos arquivos do estudo.

Uma rodada pequena de acesso usa os mesmos casos, mas é separada do piloto:

```sh
python3 run.py run --out results/smoke --cases count --reps 1 --timeout 120 --budget-seconds 300
```

O diretório de resultados precisa ser novo. `freeze.json` registra hashes do
código, protocolo, variantes, casos e ordem antes da primeira inferência.
Os pares são sorteados com semente 20261010 e a ordem das condições é balanceada.
Executa-se uma condição por vez, para reduzir disputa por recursos. A regra de
paralelismo é avaliada dentro da tarefa. `repeat` continua somente a própria
sessão, nunca uma sessão da outra condição.

O limite padrão é 600 segundos de agente por execução e 7200 segundos de orçamento
da rodada. Um par só começa se os dois limites individuais ainda couberem no
saldo. Preparação e correção são adicionais ao limite individual. O executor
interrompe o grupo de processos no timeout, preserva os eventos e para na primeira
falha de infraestrutura. Não tenta novamente nem troca modelo/provider. Eventuais
retries internos do CLI estão sujeitos ao mesmo limite. Interrupção ou esgotamento
de orçamento deixam execuções `not_run`; não contam como acerto.

## Métricas e análise

Registrar por execução: resultado de cada check, resposta final, artefatos,
eventos do CLI, chamadas de ferramentas, tempo e tokens informados. Preservar
falhas, timeouts e ausências. Erros rápidos não são ganhos de velocidade.

Entrada e saída são os contadores nativos de `turn.completed`; cache é reportado
separadamente, sem somá-lo outra vez à entrada. Campos ausentes ficam desconhecidos.
O contador é cumulativo na sessão, inclusive após `exec resume`. Usar somente o
último evento terminal, sem somar turnos sobrepostos. A auditoria dos 72 rollouts
confirmou essa semântica. Os totais derivados dos seis casos `repeat` no piloto
original duplicam o primeiro turno; a análise usa `usage_raw[-1]` corrigido e
preserva os JSONs originais. Não inferir reais,
dólares, gratuidade de OAuth ou tokens de raciocínio não informados.

O relatório separa casos e condições, mostra o denominador planejado e calcula
uma diferença exploratória de passes automáticos nos pares completos. O intervalo
usa bootstrap por caso, não por repetição, preservando o pareamento. Ler a taxa de
falhas ao lado dessa análise; exclusão diferencial pode enviesar o resultado.
Revisão cega e inspeção comportamental são registradas separadamente. Tempos de
entregas incorretas não justificam uma recomendação de eficiência.

O piloto sempre produz veredito inconclusivo sobre adoção. Ele serve para localizar
efeitos, custos e falhas dos casos. Antes de uma confirmação, congelar novas tarefas,
a melhora mínima útil e a tolerância de regressão/custo. Não ajustar o trecho com
base nos casos e depois apresentar esses mesmos casos como confirmação independente.

## Estado de validação

`verification.json` registra os testes locais e a inspeção de contexto realizada.
Esses checks validam o mecanismo de execução/correção, não provam ganho do trecho.
A avaliação anterior em `../agentsmd-detfirst/` permanece independente deste estudo.

Em 10/10/2026, a rodada curta `results/smoke/` tentou uma execução e parou antes
de uma resposta do modelo: `workspace routing discovery failed`, acompanhado de
erros de conexão ao atualizar o catálogo. A outra condição ficou `not_run`.
Não há comparação de qualidade, tokens ou velocidade válida nessa rodada.
Na execução solicitada em seguida, `results/pilot-20261010-r1/` tentou o primeiro
dos 72 casos programados e parou com o mesmo erro; 71 ficaram não iniciados.
O diagnóstico confirmou `CODEX_SANDBOX_NETWORK_DISABLED=1` e falha de DNS para
chatgpt.com no ambiente controlador. Essas duas tentativas ficaram incompletas.
A rodada `results/pilot/`, executada no terminal do usuário, concluiu 72/72.

A [análise](../../agentsmd-codex-pilot-analise.md) concilia notas, revisão dos controles e
tokens corrigidos. O protocolo, rubrica e fontes usados na rodada estão em
`results/pilot/frozen-source/`, conferidos contra os hashes de `freeze.json`
antes da correção do contador. Casos, tratamento e notas não foram alterados.
O teste de regressão da contagem reproduziu a duplicação antes da correção.
