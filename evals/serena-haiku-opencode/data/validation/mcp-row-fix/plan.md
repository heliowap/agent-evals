# Contrato da correção

Configuration e Case permanecem iguais. A configuração de documento usa `mcp.servers.serena`; servidor local mantém disabled:false, codemode:false e timeout startup/catalog/execution180000. Nenhuma permissão ampla nova.

DiscoveryReceipt registra configuração, papel, caso, fontes de config, descrição segura do MCP efetivo, respostas/status MCP, superfície observada, fase, erro e chamadas de inferência observadas. Valores de credenciais, environment, comandos desconhecidos e erro bruto de servidor não são capturados. Recibo parcial deve sobreviver ao fechamento do servidor e à remoção de temp.

Estado MCP: ausência de servidor ainda é inicialização, dentro de prazo; somente uma linha Serena válida conectada + catálogo canônico direto exato aprova. Envelopes malformados, servidor inesperado, duplicata, failed/disabled/needs_auth falham. Nenhum timeout ou[] permanente aprova.

Architect: Ground concluído; Sketch por duas alternativas de ownership do receipt; Agree técnica; Implement um writer; Scrap condicional. Arena Frame/Fan out/Cross-judge/Pick/Graft/Verify. Régua0-2: sucesso só porcontrato exato; respostas/progresso sobrevivemfalha; semsegredos; menorAPI; red-capable semmodelo.

A instância temporizada também deve provar prontidão antes da primeira chamada de modelo. Hoje invoke cria sessão/prompt imediatamente após servidor pronto, sem barreira explícita de MCP. Compartilhar a espera limitada e o gate de superfície entre audit e invoke; o relógio de invoke já começa antes do boot e continua incluindo essa espera. Nenhum custo é subtraído. Nativo aguarda somente sua superfície; tratamento exige conexão Serena e seus tools diretos. Sem prontidão, zero inferência e falha de infraestrutura. Não alegar ocorrência concreta dessa corrida em full-2.
