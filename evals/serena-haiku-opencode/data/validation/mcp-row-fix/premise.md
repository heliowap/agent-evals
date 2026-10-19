# Premissa sob revisão

Fonte estática e respostas artificiais de API seriam suficientes para inferir o comportamento completo da descoberta nativa. Os dois runs do Terminal refutaram essa suficiência: as provas locais passam, a fronteira nativa ainda rejeita; a telemetria real é removida no erro.

A causa exata do erro full-2 permanece desconhecida porque a resposta de mcp.list não foi preservada. O censo distingue sucesso local, falha nativa e observação ausente; ausência de recibo não significa zero descobertas concluídas.

Próximo passo: preservar continuamente resposta MCP, catálogo e progresso por configuração/papel antes de validar. Não aceitar servidor inesperado ou formato malformado. Qualquer ajuste de espera exige prova primária do estado transitório, e aprovação exige Serena conectado e superfície exata.
