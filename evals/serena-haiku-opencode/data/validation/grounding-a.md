# Grounding A — um único loop de trials

## Overview

O núcleo de exploração já concentra agenda, congelamento, preparação privada, execução OpenCode, exportação nativa, verificação de identidade/transporte e resultado por trial. É o proprietário adequado do novo experimento. A integração acrescenta uma dimensão de ferramentas, dois contratos de tarefa e um ciclo de subprocesso Serena; não requer um segundo scheduler.

## Key concepts

Um candidato experimental é Haiku medium/high × ferramentas nativas/Serena. A identidade do modelo permanece a mesma entre os braços; o id experimental inclui o braço. Um bloco é o mesmo caso e repetição com quatro configurações. As tarefas de exploração são somente leitura; as de implementação permitem somente o patch contratado, com teste público preservado e aceite privado fora da fixture do agente.

## How it works

`exploracao/haiku-5-5/bench.py:schedule` produz blocos permutados e rotações de candidatos. `manifest` congela configuração, fontes, fixtures e catálogo. `run_trial` materializa projeto privado, chama `runtime.prepare/audit`, roda exatamente uma sessão, exporta para arquivo regular, verifica solicitações e aplica o corretor. `runtime.private_env` já fecha a descoberta OpenCode em XDG e OPENCODE_TEST_HOME próprios. `runtime.configuration` atualmente fixa `mcp={}` e somente read/glob/grep/list. `runtime.parse_session` rejeita todas as outras ferramentas: a nova cópia precisa aceitar a superfície autorizada por papel e braço, sem alterar o runtime histórico.

Para implementação, `rounds/money-contract-v2/harness/domain.py:TaskSpec` já encapsula request, files, reference, acceptance e allowed. `grader.collect_patch/apply_patch` valida o escopo e reconstrói o projeto limpo. `grader.grade` executa compilação, regressão e aceite no `CodeContainer` read-only e sem rede; `require_completion` rejeita uma saída prematura sem marcador. `terminal.js` envia comandos exclusivamente ao Docker. Seu transform e execute.before hoje exigem terminal como ferramenta única; devem preservar terminal e permitir somente o conjunto exato de ferramentas Serena no braço experimental. Nenhum bash host será liberado. Se ferramentas nativas de leitura forem acrescentadas, ambos os braços receberão exatamente as mesmas.

O launcher Serena instalado é `~/.local/bin/serena`, cujo shebang usa o ambiente uv serena-agent e importa a fonte em `~/VSCode/Lab/serena/src/serena`. `cli.py:start_mcp_server` aceita `--project`, `--context <yaml>`, `--mode <yaml>`, `--agent-interface tools`, `--language-backend LSP`, `--transport stdio`, dashboards e GUI desabilitados. `config/serena_config.py:SerenaPaths.__init__` usa SERENA_HOME; `ToolInclusionDefinition` aceita fixed_tools; `ProjectConfig` aceita read_only; `SerenaConfig.get_project_serena_folder` permite metadata fora da fixture via project_serena_folder_location. Use pasta externa própria, pré-criada, sem `.serena` dentro do código, evitando transformar metadata em uma exceção genérica no coletor de patch.

`resources/config/contexts/ide.yml` tem single_project:true, que desativa activate_project após startup com projeto explícito. `resources/config/modes/no-memories.yml` desativa memórias e onboarding. `benchmark.yml` aplica operação autônoma. O contexto próprio deve fixar as ferramentas necessárias ao experimento e preservar o protocolo de tarefa. O manual Serena informa linhas 0-based, enquanto o corretor histórico exige linhas 1-based: a instrução do contrato continuará explícita nos dois braços; o relatório classificará esse tipo de rejeição.

## Where things live

- Agenda, captura e relatório: cópia mínima do núcleo em `ferramentas/haiku-serena-opencode/bench.py` e `runtime.py`.
- Casos e contratos: módulo único `cases.py`, reutilizando as definições histórico-exploratórias e três TaskSpec corrigidos. Helpers de patch/aceite e terminal Docker ficam locais ao pacote novo.
- Integração Serena: `runtime.py` é o único proprietário de YAML, env, launcher e verificação de superfície; um registrador stdio local opcional registra apenas MCP, sem tocar transporte de modelos.
- `grounding-a-proof.json` registra versão do binário, SHA e extração de schema McpLocalConfig embutido; zero chamadas de modelos.

## Gotchas

O corpus OpenCode em `pesquisa/research-eval-design-20261007T184125Z/corpus/opencode/` declara versão 1.18.35 e não prova comportamento do binário 2.0.26. O binário instalado contém McpLocalConfig com type local, command, cwd, environment, enabled e timeout em ms. A inicialização real e o nome dos tools precisam ser comprovados num preflight sem inferência. O preflight não deve reusar o MCP/SERENA_HOME do chat. A sessão do chat usa TypeScript; cada fixture deste eval requer LSP Python. Dependências LSP podem tentar download: provisionar e provar antes da campanha, sem mascarar startup como tempo do modelo.

O audit OpenCode atual pode inicializar MCP em processo separado. Não usar esse aquecimento como prova de startup medido: resetar o cache de projeto, ou capturar o startup do processo efetivamente usado no trial. Como controle mínimo, o tempo de `opencode run` inclui boot/initialização/ferramentas nos dois braços, e warm-up não é reaproveitado entre trials.

Um MCP stdio conectado não demonstra uso pelo modelo; contar chamadas úteis de símbolos/referências/edição por trial, incluindo trials sem uso no denominador. Não reclassificar falhas MCP como erros funcionais de implementação. Não comparar tempos desta campanha causalmente com as coortes antigas.
