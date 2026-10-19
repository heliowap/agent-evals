# Candidato A: configuração declarativa, adaptador existente

## Uso

O usuário executa o mesmo comando, com saída nova `results/full-2`. A preparação deriva a política do papel e braço; o preflight continua sem inferência.

```python
policy = tool_policy(case.role, configuration.arm)
config = prepare(..., policy=policy)
receipt = audit(..., expected=config, policy=policy)
trial = run_trial(...)  # somente após recibo aprovado
```

```python
tool_policy('exploration', 'native').names == ('read', 'glob', 'grep')
tool_policy('implementation', 'serena').names == ('terminal', *serena_write_names)
```

## Tipos e assinaturas

```python
ToolSpec(name: str, namespace: str | None, direct: Literal[True],
         permission: str, owner: Literal['builtin', 'docker', 'serena'])
ToolPolicy(role: Role, arm: Arm, tools: tuple[ToolSpec, ...])

def tool_policy(role: Role, arm: Arm) -> ToolPolicy: ...
def prepare(..., policy: ToolPolicy) -> PrivateConfiguration: ...
def validate_surface(rows: list[SurfaceRow], policy: ToolPolicy) -> SurfaceReceipt: ...
```

`ToolPolicy` é derivada da tabela existente, sem segunda lista de ferramentas Serena. Não precisa ser uma nova classe pública: tuplas/dicionários privados bastam para este patch. A interface externa do runner permanece igual.

## Problema

Há três causas independentes: o baseline exige `list`, inexistente no binário fixado; o builtin browser registra ferramentas depois do filtro do plugin; e MCP usa Code Mode por padrão, deixando Serena fora das definições diretas enquanto `execute` está proibido. Um catálogo contendo nomes permitidos não prova um tratamento disponível ao modelo.

## Forma

1. `domain.py`: baseline explorador passa a `read/glob/grep`. Mantém implementação exclusivamente `terminal`.
2. `runtime.prepare`: acrescenta `-opencode.browser` aos plugins privados e `codemode: false` à configuração do servidor MCP Serena. Não altera o OpenCode global. Mantém permissões fechadas, com ações derivadas de `policy.names`, incluindo os nomes normalizados MCP; `execute` segue proibido.
3. `surface.js`: preserva seu trabalho necessário de substituir terminal host por Docker e filtrar os builtins anteriores. Não transforma opções MCP para contornar sua configuração. Registra também `options.codemode` e a ação de permissão efetiva, além de nome/ID/namespace. O guard usa as identidades concretas registradas. Nenhum registro browser é descartado da evidência: sua presença bloqueia.
4. `runtime.audit`: verifica configuração privada efetiva, ausência de plugin `opencode.browser`, MCP conectado e opção `codemode: false` preservada. Valida catálogo final exato, IDs/nomes únicos e todas as ferramentas esperadas diretas. Para cada ferramenta, a permissão efetiva deve ser a ação derivada e permitida. Opção ausente/true bloqueia, mesmo com nome correto. Aguarda apenas startup MCP bounded; não passa por aceitar interseção, esconder snapshots ou expandir allowlist.
5. Binário fixado define `snapshot`: ferramentas com `codemode:false` são diretas; `execute` é omitido quando proibido. Essa regra, catálogo e permissões formam uma prova reproduzível da superfície efetiva sem chamar modelo. A interpretação depende do SHA fixado, como o restante do harness.

## Justificativa e alternativas

Esta mudança concentra transporte na configuração e conserva o adaptador que já garante Docker. É menor que reimplementar terminal, introduzir um catálogo paralelo ou registrar um último filtro tardio. A configuração é a dona do browser desligado e de MCP direto; o gate é a dona da prova, sem tentar reparar condições divergentes.

Desligar todos os builtins e reativar individualmente os necessários permitiria retirar parte do filtro, mas introduziria uma nova lista de dependências internas e risco sobre autenticação/serviços obrigatórios. Fazer atualização dinâmica `codemode:false` em todas as ferramentas Serena é redundante com a opção nativa e depende da ordem de registro que causou o erro. Reabilitar `execute` ampliaria o contrato e deixaria de comparar o tratamento planejado.

## Verificação e limites

Persistir regressões: catálogo real sem `list`; rejeição browser pós-filtro; ferramenta Serena default/true rejeitada; permissões não efetivas rejeitadas; MCP direto aceito; terminal host substituído. Reexecutar preflight real das quatro combinações sem inferência. Preservar `full-1` byte a byte. O primeiro run bloqueado não fornece resultado de qualidade.

## Síntese

Reservado ao juiz. Primeiro passo: testes vermelhos que reproduzam as três causas com o catálogo e a regra `snapshot` do binário fixado.
