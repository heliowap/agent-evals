# Sistemas envolvidos

O eval de exploração existente usa `exploracao/haiku-5-5/bench.py` como único scheduler e loop. O runtime importa somente a credencial CLIProxy em descoberta privada do OpenCode 2.0.26, instala observador local passivo e verifica configurações, modelo, esforço, rota Messages, thinking adaptive e cap inteiro 128000. O parser conserva exportação nativa, mensagens e chamadas de ferramentas. Os seis casos usam o mesmo projeto Python de 23 arquivos e corretor estrito de JSON e citações. Todas as permissões MCP são atualmente negadas.

O eval de implementação usa TaskSpec com arquivos iniciais, referência, contrato e testes privados separados. `rounds/money-contract-v2/harness/` contém o contrato monetário corrigido. O grader reaplica somente o patch permitido em cópia limpa, preserva testes públicos originais, executa aceite fora do workspace do agente e exige marcador de conclusão. O núcleo original executa testes em Docker sem rede. São candidatos úteis py-money-contract, py-document-scope e py-atomic-import, sujeitos à seleção final.

Serena está instalado em `~/.local/bin/serena`, aponta para o ambiente uv de serena-agent e importa a fonte local `~/VSCode/Lab/serena/src/serena`. A versão observada é 2.0.0.dev0. A configuração atual deste chat usa outro launcher, serena-codex-bridge, e TypeScript. Não reutilizar essa sessão nem suas memórias para o eval. O novo MCP deve iniciar como subprocesso stdio de cada OpenCode, ativar somente a fixture Python, com configuração, memórias e logs próprios.

O CLI instalado aceita contexto YAML personalizado, modos YAML, backend LSP, stdio, dashboard desativado e projeto explícito. Conferir schemas na fonte instalada, evitando assumir que a documentação corrente do OpenCode usa exatamente o schema do binário 2.0.26. O OpenCode permite MCP local junto das ferramentas nativas. O efeito a medir é o pacote de ferramentas e instruções do Serena sob a mesma política de tarefa, não apenas a existência do servidor.

A preparação deve congelar fontes, contrato, catálogo, seleção de casos, limites, configuração MCP e identidade da instalação Serena. Evidências antigas são somente leitura. Não comparar latências novas diretamente com coortes históricas. As condições devem alternar dentro de cada caso/repetição. Registrar início do MCP e uso real, erros, overhead e região de tempo. Os trials sem uso útil de Serena permanecem no denominador e são identificados no relatório.

Fontes oficiais consultadas: https://oraios.github.io/serena/02-usage/030_clients.html e https://opencode.ai/docs/mcp-servers/ .
