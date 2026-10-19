# Eval de implementador no OpenCode

Estado: plano aprovado e executor implementado. Há 20 tarefas TypeScript/Node e Python, além do smoke e da prova de interrupção. A execução com modelos depende dos gates descritos abaixo; ainda não há resultado comparativo deste papel. O objetivo é selecionar configurações para receber uma tarefa delimitada e entregar uma alteração funcional, preservando o restante do projeto.

## Configurações

| Configuração | Seleção no OpenCode | Motivo para comparar |
|---|---|---|
| Sonnet 5.5 medium | `cli_proxy/cpa-claude-sonnet-5-5#medium` | Candidato inicial para mudanças delimitadas; bom resultado local no papel de exploração |
| Sonnet 5.5 high | `cli_proxy/cpa-claude-sonnet-5-5#high` | Verificar se esforço adicional melhora implementação, sem extrapolar o eval de exploração |
| Sol 6.1 medium, Fast selecionado | `openai/gpt-6.1-sol-fast#medium` | Candidato OpenAI com OAuth nativo; o teste anterior acertou todas as respostas literais |
| Sol 6.1 high, Fast selecionado | `openai/gpt-6.1-sol-fast#high` | Medir o ganho de esforço em código com controle dentro da mesma família |
| Opus 5.5 medium | `cli_proxy/cpa-claude-opus-5-5#medium` | Referência de maior capacidade para tarefas que exigem julgamento |
| DeepSeek V4.1 Flash max | `opencode-go/deepseek-v4.1-flash#max` | Representante da assinatura Go numa rota já exercitada localmente |

Essas são hipóteses de comparação, não uma classificação de implementadores. A [documentação OpenAI](https://developers.openai.com/api/docs/models/gpt-6.1-sol) descreve Sol para trabalho complexo de código e suporta medium e high. A [publicação Anthropic](https://www.anthropic.com/claude-sonnet-5-5) descreve Sonnet para tarefas delimitadas e correção de bugs, e Opus para trabalho complexo com mais julgamento. A escolha dos esforços e a composição da matriz são decisões deste desenho, não recomendações comprovadas pelos benchmarks dos fornecedores.

DeepSeek consta na [oferta Go](https://opencode.ai/docs/go/) e no catálogo local. GLM-5.3 e Kimi K2.7 Code podem entrar numa ampliação posterior, se o objetivo passar a ser comparar alternativas Go. Não acrescentá-los agora limita o tamanho da primeira matriz.

Gemini fica fora da rodada inicial até verificar identidade do backend, esforço e encerramento do agente. A [segunda rodada de exploração](../../exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/analysis.md) teve 17 erros no encerramento por limite, respondeu com o identificador `gemini-3.8-flash-n` e apresentou flags de stream cuja causa não ficou preservada.

Os dois Sol conservam Fast selecionado para manter a configuração OAuth já usada. O relatório precisa distinguir seleção, priority encaminhado e tier terminal atendido. Os trials anteriores retornaram default; nenhum orçamento ou resultado presume Fast atendido. Os custos de API publicados não estimam consumo das assinaturas OAuth, Anthropic via CLIProxy ou Go.

## Papel e entrega

Cada sessão recebe uma delegação com comportamento desejado, critérios de aceitação, restrições, pontos de entrada e comandos de testes públicos. O candidato pode explorar, editar arquivos e executar verificações dentro do projeto. Não recebe solução sugerida, testes ocultos ou feedback do grader.

Uma mensagem do usuário inicia cada trial. O agente pode executar vários ciclos de edição e testes públicos. Não há segunda mensagem corretiva, revisor auxiliando durante a execução, web, MCP ou subagentes. Instruções e ferramentas são iguais em todas as configurações. A resposta final é texto livre com um resumo; não se exige JSON ou citações exatas.

A entrega avaliada é o patch efetivamente produzido. Uma declaração de sucesso não substitui testes. O papel é implementador delegado, não um agente que precisa descobrir e esclarecer uma issue aberta antes de trabalhar.

Exemplo de enunciado público:

> Adicione paginação por cursor à listagem de pedidos. O cursor deve preservar a ordenação por data e ID, inclusive quando dois pedidos têm a mesma data. Uma página seguinte não pode repetir itens. Preserve o filtro de tenant e o comportamento dos clientes que não fornecem cursor. Comece pelo handler de pedidos e pelo repositório indicado. Inclua testes e execute os comandos públicos do projeto.

## Tarefas da triagem

São 12 casos distintos, seis TypeScript/Node e seis Python. Cada caso usa um pequeno projeto com camadas e dependências explícitas. Os cenários representam padrões de projetos reais, com contratos novos; a curadoria pode incorporar snapshots reais quando houver uma tarefa equivalente reproduzível. Evitar funções isoladas cujo único trabalho seja completar algumas linhas.

| Família | Caso TypeScript/Node | Caso Python |
|---|---|---|
| Funcionalidade entre camadas | Paginação por cursor com ordenação estável e compatibilidade | Importação em lote com validação, resumo e atomicidade |
| Correção e efeitos colaterais | Retry de operação idempotente sem duplicar efeitos | Rollback de transação com publicação somente após commit |
| Autorização e escopo | Nova operação sem acesso cruzado entre tenants | Consulta com tenant, proprietário e exclusão lógica |
| Validação e contratos | Campos ausentes, null e vazios com contrato explícito | Valores monetários e limites sem arredondamento indevido |
| Streaming e limpeza | Cancelamento de iterador assíncrono liberando recurso uma vez | Fechamento antecipado de generator e limpeza em exceções |
| Refatoração com preservação | Consolidar conversões e retirar uma API interna especificada | Unificar exporters preservando interfaces e comportamento |

O conjunto de confirmação usa oito tarefas inéditas, quatro por linguagem, cobrindo as mesmas famílias. Nenhum caso de confirmação pode ser usado para escolher finalistas ou ajustar prompts. Não basta renomear os casos da triagem.

Antes de admitir uma tarefa, executar o baseline e a solução de referência no grader. O baseline precisa falhar no requisito novo e a referência passar. Numa refatoração, os testes comportamentais podem passar desde o início; o requisito estrutural público precisa distinguir a mudança solicitada. Nunca exigir igualdade com o patch de referência.

Os testes ocultos verificam comportamentos descritos no enunciado, inclusive suas bordas. Não acrescentam requisitos surpresa. Dependências e relógios ficam fixos, com rede externa substituída por componentes locais determinísticos quando não fizer parte da tarefa.

## Aprovação completa

Uma tentativa recebe aprovação completa somente quando satisfaz todos os critérios:

1. A sessão termina normalmente dentro do orçamento, com a identidade e o esforço solicitados.
2. O patch implementa todo o contrato, demonstrado pelos testes privados de aceitação.
3. A suíte original de regressão, compilação e checagem de tipos continua passando no ambiente confiável do grader.
4. O diff respeita o escopo público da tarefa. Não modifica o mecanismo de avaliação, nem substitui comportamento por retornos fixos para os exemplos.
5. Os requisitos estruturais explícitos, quando houver, estão atendidos.

Registrar separadamente `patch_correct`, `session_completed`, regressões, violação de escopo, limite excedido e falha de integração. Isso permite mostrar um patch correto deixado por uma sessão interrompida sem fingir aprovação completa. Toda tentativa iniciada entra no denominador operacional; uma falha de transporte não vira evidência de incapacidade de implementar.

Testes escritos ou editados pelo candidato são parte da entrega, mas não definem o resultado. O grader reaplica somente o patch permitido numa cópia limpa e usa a suíte original, dependências confiáveis e seus testes privados. Uma refatoração pode ter vários patches válidos.

## Qualidade do diff

Aprovação funcional é a métrica primária. Revisão do diff é secundária e cega para modelo, esforço e rota. Sua rubrica tem quatro critérios, cada um de zero a dois:

- Clareza e coerência com os padrões do projeto.
- Alterações pertinentes ao contrato, sem mudanças não solicitadas.
- Testes da entrega que exercitam comportamento e regressões relevantes.
- Tratamento de limites, erros e recursos nos casos em que isso faz parte da tarefa.

A nota não compensa um teste funcional reprovado. Número de linhas e arquivos é descritivo; não penaliza uma solução por ser maior ou menor. Caso um juiz LLM seja adotado, avaliar os patches sob identificadores neutros, numa mesma rubrica, com revisão humana de divergências. Contabilizar as chamadas desse juiz separadamente. O plano inicial não depende de pontuações de LLM para decidir aprovação.

## Fases e tamanho

| Fase | Composição | Sessões planejadas |
|---|---|---:|
| Provas de encerramento | Uma por configuração, com orçamento reduzido | 6 |
| Smoke de implementação | Uma alteração pequena por configuração | 6 |
| Triagem | 12 casos × 6 configurações × 3 repetições | 216 |
| Confirmação | 8 casos inéditos × 2 finalistas × 5 repetições | 80 |
| Total, se todas as fases forem executadas | | 308 |

São 302 sessões de smoke e comparação, mais seis provas de encerramento que também usam modelos. Sessão, passo, chamada de modelo e chamada de ferramenta são contagens diferentes. O total de chamadas, tokens e eventual revisão LLM ainda não pode ser estimado sem smoke. Não somar verificações sem inferência ao consumo de modelo.

Três repetições sustentam triagem exploratória de aprovação, não uma declaração de vantagem de latência. Selecionar finalistas por aprovação funcional equilibrada por caso, com os erros operacionais expostos e os defeitos críticos destacados. Se os resultados não distinguirem duas configurações com segurança, reportar o empate; não forçar uma eliminação por uma diferença pequena de tempo. Um terceiro finalista acrescentaria 40 sessões de confirmação, totalizando 348.

A confirmação permite comparar cinco repetições por tarefa, mediana e intervalo, além de pares em que ambos entregaram patches aprovados. Não chamar as 40 tentativas de cada finalista de 40 tarefas independentes; são oito tarefas. Não misturar triagem e confirmação para declarar resultado sobre casos que influenciaram a seleção.

## Orçamento e encerramento

A proposta inicial é um limite de 20 minutos por tarefa e alvo de 60 chamadas de modelo por sessão. O smoke calibra esse orçamento para tarefas representativas antes de congelar a comparação. Todas as configurações recebem o mesmo limite. Raciocínio, tentativas internas e retries contam no consumo.

Usar um controlador externo que acompanha a sessão e a interrompe ao atingir o orçamento. A versão local oferece `session.interrupt`; a fase `budget` precisa provar interrupção, encerramento dos subprocessos e captura do patch. Uma chamada já em curso pode terminar durante a interrupção, e o relatório precisa registrar eventual excesso. O timeout externo é a última barreira.

Não configurar o orçamento comparativo apenas como `agent.steps=60`. O OpenCode local acrescenta um turno assistant ao atingir qualquer limite nativo; aumentar 25 para 60 desloca o mecanismo que falhou no Gemini. A configuração efetiva deve verificar que o limite nativo não aciona esse caminho antes do controlador. A mesma política de encerramento vale para todas as integrações.

Congelar orçamento global por lote depois do smoke. Como a validade do OAuth precisa cobrir cada lote, rodadas longas podem ser divididas somente entre blocos completos de caso e repetição. Renovação acontece na sessão normal do OpenCode, sem rotacionar refresh tokens numa cópia descartável. Não prometemos uma duração total a partir do tempo do explorador.

## Isolamento, transporte e medição

Cada trial recebe filesystem e estado privados. O OpenCode e os provedores rodam no host; a única ferramenta disponível ao agente é `terminal`, executada num container Linux sem rede e com somente o projeto montado. Leitura, edição e testes usam essa mesma ferramenta nas seis configurações. As ferramentas nativas de leitura, edição e shell são removidas. Portanto, o resultado mede implementação com esse terminal isolado, e não o conjunto habitual de ferramentas do OpenCode. O gate verifica a lista efetiva e rejeita ferramentas externas ao terminal.

Testes ocultos e soluções ficam fora do filesystem do candidato. O grader recebe o patch numa cópia limpa em outro container, restaura as verificações públicas originais e adiciona suas verificações privadas. `external_directory=deny` sozinho não seria isolamento do sistema operacional. O preflight exige provas reais de montagem, acesso negado a arquivos externos, rede desativada e encerramento de subprocessos.

Pré-instalar dependências antes da medição, com versões e lockfiles congelados. Instalação não deve variar por candidato. Testes públicos, código e contexto normal ficam disponíveis; artefatos do experimento, soluções e histórico da correção ficam fora. Diretórios e prompts do projeto não revelam que há comparação ou juiz.

Conservar OpenCode, OAuth nativo, variantes, cache local congelado e observação de HTTP/WebSocket. CLIProxy é acessado pelo OpenCode no host em `127.0.0.1:8317`; o container de código não precisa acessar provedores. Skills ficam desativadas. Os únicos plugins locais são o observador passivo e o terminal isolado. O endpoint do Docker é resolvido no host e congelado sem montar credenciais ou o socket dentro do container.

Registrar o código original de erro do observador, distinguindo cancelamento do stream, falha de transporte, HTTP não exitoso, limite excedido e falha da tarefa. Não repetir a perda de informação da rodada Gemini. Metadados enviados e recebidos permanecem separados; o nome escolhido não prova o modelo executado a montante.

A agenda é sequencial, organizada por blocos de caso e repetição com ordem balanceada. Cada candidato usa uma sessão nova, mas cache remoto pode persistir. Medir a invocação completa, incluindo testes públicos executados pelo agente. Mostrar preparação e grading externos separadamente. Tokens de entrada, saída, raciocínio e cache não equivalem a consumo comparável das assinaturas.

## Executor e uso

`domain.py` define tarefas, configurações e orçamento. `tasks_python.py` e `tasks_typescript.py` guardam os projetos e os verificadores privados. `bench.py` congela fontes, catálogo, agenda e parâmetros; executa os gates e gera `summary.json` e `report.md`. `controller.py` acompanha chamadas e tempo, usando `session.interrupt` no mesmo servidor da sessão. `runtime.py` prepara o OpenCode privado e verifica transporte, identidade e esforço. `grader.py` reaplica o patch permitido sem executar código do candidato no host. Os arquivos do explorador permanecem separados.

Requisitos: OpenCode 2.0.26, credenciais na instalação normal, catálogo local em `~/.cache/opencode/models.json`, Docker acessível e CLIProxy ativo. A imagem fixa Node 24.9.0, TypeScript 5.9.3 e o Python fornecido pela imagem; o preflight registra versões reais e congela o ID de conteúdo da imagem. A validação local de fixtures usa o Python/Node do host e o TypeScript 5.9.3 existente no cache Bun; essa verificação não substitui a validação nos containers.

Execute da raiz deste repositório. Cada `--out` precisa ser novo; evidências anteriores não são sobrescritas.

```sh
python3 -B implementacao/opencode-implementador/bench.py validate \
  --out implementacao/opencode-implementador/results/validate-screening
python3 -B implementacao/opencode-implementador/bench.py validate \
  --phase confirmation --candidates sonnet-medium,sol-fast-medium \
  --out implementacao/opencode-implementador/results/validate-confirmation

python3 -B implementacao/opencode-implementador/bench.py run \
  --phase budget --build-image \
  --out implementacao/opencode-implementador/results/budget
python3 -B implementacao/opencode-implementador/bench.py run \
  --phase smoke \
  --budget-proof implementacao/opencode-implementador/results/budget \
  --out implementacao/opencode-implementador/results/smoke
python3 -B implementacao/opencode-implementador/bench.py run \
  --phase screening \
  --budget-proof implementacao/opencode-implementador/results/budget \
  --smoke-proof implementacao/opencode-implementador/results/smoke \
  --out implementacao/opencode-implementador/results/screening
```

Os dois nomes no comando de validação da confirmação servem apenas para exigir uma lista explícita; a validação não faz inferência nem escolhe finalistas. Depois da triagem, use os finalistas escolhidos em `run --phase confirmation --candidates ...`, com os mesmos `--budget-proof` e `--smoke-proof`. São 80 sessões para dois finalistas.

`plan` congela a agenda sem inferência; `preflight` verifica ambiente, referências no container e configuração nativa sem chamar modelos; `report --out CAMINHO` recalcula o relatório. `--block-start` e `--block-count` delimitam blocos completos de caso/repetição para lotes novos. O orçamento global padrão é seis horas; a validade do OAuth precisa cobrir esse lote, e o executor só começa outro bloco antes do limite global. Um bloco em andamento pode ultrapassá-lo. Ajuste `--global-seconds` e o número de blocos ao período disponível, renovando OAuth na instalação normal antes de iniciar.

A janela exigida do OAuth inclui o último bloco completo e margens conservadoras para preparação, grader e auditoria. Essas margens são limites de reserva, não estimativas de duração. A validade é conferida novamente antes de cada bloco; a cópia privada não renova tokens. O relatório mostra mediana, mínimo/máximo observados e razões de tempo entre pares aprovados; não calcula intervalo de confiança nem comprova vantagem estatística por si só.

A prova de interrupção usa 20 segundos e duas chamadas como limites reduzidos. Smoke e comparação usam inicialmente 1.200 segundos e 60 chamadas por sessão. O controlador registra qual limite acionou, eventual chamada excedente, interrupção nativa e parada do container. Não há retry automático de uma tentativa. O relatório separa planejadas, iniciadas e não executadas; a taxa operacional de aprovação usa todas as tentativas iniciadas, inclusive falhas.

Arquivos e catálogo precisam continuar iguais aos gates, incluindo este README. Se o smoke justificar mudar orçamento ou código, use novos diretórios e refaça os gates antes da comparação. A revisão cega do diff continua secundária e manual; o executor não inventa uma nota nem escolhe vencedor automaticamente.

## Decisão de desenho e próximos passos

Dois esboços independentes compararam tarefas delimitadas e snapshots de repositórios reais. A revisão deu 9/10 a ambos: o primeiro reduz curadoria inicial, o segundo aumenta representatividade. A base escolhida é o conjunto delimitado, incorporando projetos contextualizados e requisitos derivados de trabalho real. A comparação evita medir principalmente descoberta de uma issue, e a confirmação reserva tarefas inéditas.

Foundational Thinking orientou a separação entre tarefa, configuração e resultado. Explain the Number exige distinguir patch correto, sessão concluída, falha de integração e tempo. O trabalho independente fica na curadoria e validação de cada tarefa; credenciais, agenda e relatórios têm um proprietário. Todas as sessões comparativas continuam sequenciais.

Próximo gate operacional: provar isolamento e interrupção e executar o smoke. Na execução reportada pelo usuário, o Docker respondeu e a imagem foi construída, mas a prova no container falhou antes das inferências. Aqui, o acesso ao socket Docker retorna permission denied e a abertura de loopback retorna EPERM; isso impede demonstrar os gates reais neste sandbox. O executor registra o bloqueio antes de qualquer inferência.

Se um comando de namespace ou versão retornar falha, `preflight.json` conserva `isolation.namespace` e `isolation.versions`, com código de saída, stdout e stderr de cada comando. A prova de credenciais exige que o arquivo seja inacessível: ausência ou `PermissionError` são resultados válidos para um processo sem privilégios. Uma falha do preflight continua bloqueando inferências. Depois de corrigir o executor, repita o gate num novo `--out`; a imagem existente pode ser reutilizada sem `--build-image` quando o Dockerfile não mudou.
