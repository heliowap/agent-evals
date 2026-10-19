# Grounding MCP — full-2

Investigação somente de leitura; zero inferência. Binário `~/.opencode/bin/opencode`, SHA256 `1b6418a3bd4211344d8a2b75d7d4367b24283ae548bd6b896cf717f6f8858f26`. Offsets abaixo são bytes nesse binário.

`full-2/preflight.json` prova contratos locais, Serena/Python LSP por stdio, imagem, namespace, terminal nativo e contratos Docker. Falhou na descoberta OpenCode. Não contém a resposta `mcp.list`, a configuração efetiva, a configuração/papel em andamento ou descobertas já concluídas. Não é possível atribuir o erro a lista vazia, nome inesperado, multiplicidade ou formato de status.

## Protocolo publicado no próprio binário

- Handler `mcp.list`, offset **121007007**: transforma `servers()` em `{name,status,integrationID}`. O retorno tem envelope `data`.
- Schema nativo, **113418900–113419500**: `status` é objeto discriminado por `status`, com estados `pending`, `connected`, `disabled`, `failed` e `needs_auth`; os últimos dois trazem `error`. Não há evidência de um formato alternativo em que `status` seja string simples. `integrationID` pode ser ausente em MCP local.
- Serviço MCP, **120055260**: registro vivo `E` começa como `new Map`.
- `servers()`, **120062550**: lê `E` diretamente, sem esperar inicialização/conexão. Lista vazia é representável durante início ou permanentemente quando nenhum servidor foi registrado. Isso não prova que `full-2` observou `[]`.
- Reconciliação, **120060750–120061650**: adiciona entradas com estado `pending`; a conexão assíncrona muda para `connected`, `failed` ou `needs_auth`. Uma entrada conectada e catálogo exato continuam necessários para admitir o tratamento Serena.

## Configuração e atores

`Config.MCP`, **113429230**, usa `{timeout?, servers?}`. O plugin `opencode.config.mcp`, **120553354**, percorre exclusivamente `document.info.mcp.servers`. O runner atual grava `mcp.serena` diretamente.

O normalizador **120229396** suporta posição legada `mcp.<nome>`, mas a interpreta pelo schema legado `OS`. O MCP local legado, **120216987**, espera `enabled` e `timeout` numérico. O runner mistura posição legada com `disabled`, `codemode` e `timeout` objeto nativos. A conversão `$S`, **120222654**, descarta `codemode`, converte `enabled` em `disabled` e transforma timeout numérico em `{catalog,execution}`. Essa incompatibilidade é comprovada no contrato; seu efeito concreto em `full-2` ainda depende da configuração efetiva/raw.

Outros atores: política **120572359** pode remover servidores; defaults Code Mode **120779838** ajustam configuração; integração builtin OpenCode **120865263** pode acrescentar servidores recebidos de sua configuração remota. Nenhuma atuação desses atores foi observada nesta execução. Não existe servidor hardcoded no mapa inicial examinado.

`qh`, **120515894**, lê políticas somente de `document.info.experimental.policies` e `ManagedPolicy.current.statements`. `j0`, **120516217**, procura a ação literal `integration.use` e permite por padrão. O `config.permissions` com deny global é processado separadamente como permissão dos agentes; não é a fonte desse filtro MCP. Não há justificativa para acrescentar uma permissão ampla de integração.

| Braço | Estado esperado para admissão |
|---|---|
| Nativo | Nenhum servidor MCP; sem ferramentas Serena |
| Serena, início | Ausência transitória ou uma entrada `pending`, com espera limitada |
| Serena, pronto | Exatamente `serena`, `connected`, catálogo/ferramentas exatos |
| Serena, falha | `failed`, `disabled`, `needs_auth`, nomes extras ou formato inválido bloqueiam |

## Evidência mínima para a próxima descoberta

Preservar cada resposta `mcp.list` antes da validação, com configuração, papel, tentativa e tempo; salvar as entradas `config.get` efetivas e a superfície observada mesmo em falha; manter descobertas anteriores incrementalmente. Copiar logs privados relevantes com redação explícita de credenciais, antes de destruir o diretório temporário. Configuração nativa evita interpretação legada; não substituir uma prova de conexão por tolerância genérica a formato desconhecido.
