# Grounding B: Serena e fronteiras do novo eval

## Visão geral

O runtime de exploração prepara uma descoberta privada do OpenCode, importa somente a credencial CLIProxy, instala o observador passivo e verifica modelo, esforço e Requests Messages. O loop atual é específico de leitura: configura MCP vazio, só permite read/glob/grep/list, rejeita qualquer outra ferramenta na exportação e exige fixture integralmente inalterada. Adaptar esse loop para implementar significa mudar seus invariantes centrais, não adicionar apenas uma opção de configuração.

O harness de implementação possui um contrato diferente: TaskSpec separa arquivos iniciais, implementação de referência e testes privados; collect_patch verifica o escopo; grade reaplica o patch numa cópia limpa e executa os testes em Docker sem rede, com árvore de arquivos read-only. Sua terminal.js executa comandos somente no container. Entretanto, tanto a enumeração quanto o hook execute.before exigem exclusivamente terminal. Uma cópia local dessa política deve permitir terminal e a lista exata de ferramentas Serena; nenhuma ferramenta host de shell pode aparecer.

## Instalação Serena observada

- Launcher: `~/.local/bin/serena`, link para `~/.local/share/uv/tools/serena-agent/bin/serena`.
- Shebang: Python do ambiente uv `serena-agent`; instalação editable, portanto a versão 2.0.0.dev0 sozinha não congela código.
- Fonte: `~/VSCode/Lab/serena`; HEAD `8e1a255e979746597f6cc05a94022ec2d3d3a3ca`; `git status --short` vazio nesta leitura.
- Serena `pyproject.toml` fixa MCP 2.2.0 e sensai-utils 1.5.0. Registrar também pacotes instalados, Python, uv e hash das fontes/resources realmente carregadas; bloquear alteração após freeze.

Nenhuma fonte dessa instalação foi editada. Não foram lidas credenciais nem resultados históricos para este grounding.

## Schemas e fluxo real

`src/serena/cli.py:302` aceita `start-mcp-server --project PATH --context YAML --mode YAML --language-backend LSP --agent-interface tools --transport stdio --enable-web-dashboard false --open-web-dashboard false --enable-gui-log-window false --log-level INFO --tool-timeout 60`.

`src/serena/config/context_mode.py` carrega context/mode por caminho YAML. O contexto suporta name, prompt, description, single_project, fixed_tools e structured_tool_output. fixed_tools não pode coexistir com excluded_tools/included_optional_tools não vazios. single_project impede troca de projeto e elimina activate_project. Os modos são somados aos base_modes globais: passar apenas --mode não remove interactive/editing herdados. Gerar global config privada com base_modes e default_modes vazios, e um modo próprio para a tarefa.

`src/serena/config/serena_config.py:60` lê SERENA_HOME; daí vêm configuração global, contextos, templates, memórias e logs. Gerar esse diretório por trial. ProjectConfig exige project_name e language_servers. Usar `language_servers: [python]`, `language_backend: LSP`, `agent_interface: tools`, encoding utf-8, read_only verdadeiro na exploração e falso na implementação, workspace relativo '.', sem activation_command. `languages` é somente alias legado. Usar `project_serena_folder_location` absoluto fora da fixture: caches/memórias/metadata do Serena não devem virar alterações fora do escopo no grader.

O contexto built-in claude-code proíbe discovery por Read e edição nativa, e contém instruções específicas do cliente Claude Code. Não serve como controle de uma condição “nativas + Serena”. Gerar um contexto próprio permitindo as ferramentas nativas definidas no papel e o Serena quando útil; o efeito observado é do pacote de ferramentas e instruções.

`src/solidlsp/language_servers/pyright_server.py` fixa Pyright 1.1.403. O backend python usa uvx e aguarda análise inicial até 60 s; depois pode prosseguir mesmo após timeout. “MCP conectado” não comprova LSP funcional. `src/solidlsp/dependency_provider.py` aceita ls_base_cmd/ls_path e ls_args; o provedor uvx resolve pacote fixado. Preparar dependência uma vez, registrar artefatos/versionamento e usar execução offline nos trials. Reutilizar somente cache da distribuição/dependências, não índice de projeto ou memórias.

O MCP normal desta instalação gera schemas diretamente do apply da ferramenta; não assumir session_id do bridge Codex desta conversa. Ler tools/list real. O schema de OpenCode deve ser provado com o binário 2.0.26, pois SDK ou documentação corrente pode ter outro formato.

## Provas necessárias

Antes de inferência: inicializar o MCP stdio, obter tools/list, chamar get_symbols_overview/find_symbol/find_referencing_symbols numa fixture descartável, comprovar corpo/referência esperados e edição de símbolo numa cópia descartável. Checar início/fim do processo LSP, projeto ativo, configuração e ausência de ferramentas de memória, shell, REPL, troca de projeto e web. Nenhuma dessas chamadas de prova pode aquecer o índice do trial medido.

Durante cada trial: exportação nativa regular + hash, identidade/effort e requests passivos; lista exata de ferramentas; chamadas Serena úteis bem-sucedidas separadas de manual/config; erros MCP separados de rejeição funcional. Tempo principal começa no spawn de OpenCode e inclui boot MCP/LSP e ferramentas. Preparação/auditoria/export/grading têm tempos próprios. Se não houver timestamp confiável de prontidão MCP, marcar esse componente indisponível em vez de inventar decomposição.

## Limites de isolamento

Terminal e grader têm namespace Docker sem rede. Serena host, read/edit nativos e processos LSP possuem isolamento por projeto/configuração, não o mesmo namespace Docker. Não afirmar isolamento OS completo. Excluir shell, REPL, ativação e memória, limitar parâmetros relativos à fixture e provar path confinement. Se essa prova falhar, bloquear a condição Serena antes de qualquer modelo; não chamar a vulnerabilidade de erro do Haiku.

Fontes locais: `exploracao/haiku-5-5/{bench,runtime}.py`; `implementacao/opencode-implementador/rounds/money-contract-v2/harness/{domain,grader,isolation}.py` e `terminal.js`; fonte Serena acima.
