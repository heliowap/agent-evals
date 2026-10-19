# Grounding do catálogo nativo

O catálogo registrado e a superfície enviada ao modelo são entidades distintas. `ctx.tool.list()` reconstrói o registro após todas as transforms. O filtro local roda no meio da sequência pre, plugins locais, post. O browser builtin post pode acrescentar tools depois do filtro. O snapshot do modelo ainda aplica permissões e expõe tools diretos (`codemode:false`) ou wrapper `execute`.

No OpenCode2.0.26 instalado, leitura nativa é read/glob/grep. `read` também lê diretórios; não existe builtin list. O ambiente privado não depende da configuração global para registrar browser. O gate full-1 parou antes de conferir formalmente todos os documentos de configuração, portanto esse run não atesta isolamento completo.

Correções comprovadas pelo fonte embarcado: operação plugins `-opencode.browser` remove builtin apenas no documento privado; `mcp.serena.codemode:false` se propaga a cada MCPTool e suas instruções; namespaced permission serena_nome já corresponde ao contrato permitido.

Fontes primárias: root-cause-source.json, mcp-direct-source.json, tool-service-source.txt, codemode-source.json e freeze de full-1. SHA256 binário1b6418a3bd4211344d8a2b75d7d4367b24283ae548bd6b896cf717f6f8858f26.

A reprodução inicial sintetiza uma lista final com browser posterior ao filtro. A hipótese de lista bruta/desatualizada foi refutada pelo fonte Md; o replay será corrigido para aplicar todas as transforms em ordem, sem ocultar linhas do polling.
