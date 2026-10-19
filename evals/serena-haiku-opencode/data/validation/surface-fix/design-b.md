# Candidato B: exposição declarativa, prova no limite

## Uso

O comando público continua o mesmo, com saída nova e sem sobrescrever `full-1`:

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py preflight \
  --phase full --out ferramentas/haiku-serena-opencode/results/preflight-r2
```

Os três usos internos derivados desse contrato:

```python
env, config = prepare(root, work, Configuration('medium', 'native'), exploration, args)
env, config = prepare(root, work, Configuration('high', 'serena'), implementation, args)
receipt = audit(root, work, configuration, case, args, env, config)
```

`prepare` controla exclusivamente o runtime privado; `audit` devolve uma prova de exposição direta ou bloqueia com zero chamadas. Nenhuma flag pública nova.

## Problema

O filtro do plugin roda antes do builtin `opencode.browser`, que repõe ferramentas depois. O contrato ainda pede `list`, inexistente no OpenCode 2.0.26. Além disso, MCP entra por padrão em CodeMode: o registro raw pode conter Serena enquanto nenhuma definição direta chega ao modelo, porque `execute` está negado. São problemas de composição e representação, não lentidão de inicialização.

## Forma

Preservar `Configuration` e a tabela única `TOOLS`; corrigir a derivação do baseline:

```python
NativeSurface = Exploration(read, glob, grep) | Implementation(terminal)
ExpectedSurface = NativeSurface + SerenaTools(role) if arm == 'serena'

def native_tools(role) -> tuple[str, ...]: ...
def prepare(...) -> tuple[PrivateEnvironment, PrivateConfig]: ...
def audit(...) -> DiscoveryReceipt: ...
```

Em `prepare`, acrescentar `-opencode.browser` à configuração privada, mantendo observer e surface. No MCP Serena, definir explicitamente `codemode: false`. Isso usa o schema real e o caminho confirmado `MCP config → tool metadata → McpTool.options.codemode`; também corrige as instruções MCP para chamada direta. Não abrir `execute`.

`surface.js` continua responsável pelo recorte de ferramentas e terminal Docker. Seu registro passa a preservar `options.codemode` e a chave de permissão junto dos nomes e IDs. Nenhuma transformação tardia ou mutação periódica do catálogo.

`runtime.surface` certifica cada ferramenta admitida: nome/ID únicos, conjunto final exatamente igual ao derivado, `codemode === false` em todas, nenhuma ferramenta inesperada em qualquer registro. O gate de plugins também recusa `opencode.browser` ativo. Gate de configuração exige o documento privado completo, incluindo remoção e `codemode: false`; permissões negam tudo e liberam somente o conjunto derivado, em agent e global.

Esse certificado é suficiente para a representação efetiva no binário fixado: `Tool.snapshot` inclui definições diretas somente quando `codemode === false`; filtros usam a chave de permissão ou ID. Para Serena, `wa(server,name)` produz `serena_nome` (offset 120148354), igual à permissão derivada existente. Registrar catalog raw sem esses atributos não é prova de disponibilidade.

Mapa: `domain.py` deriva contrato; `runtime.py` compõe config e valida; `surface.js` restringe e registra. Não adicionar módulo, framework de adaptação ou segunda lista de ferramentas. Interface pequena esconde ordenação de plugins, namespace e CodeMode no limite, conforme boundary-discipline e single-source-of-truth.

## Alternativas

- Reinscrever `ctx.tool.transform` depois dos plugins post: não há hook final fundamentado disponível; timer/registro tardio cria corrida entre descobrimento, MCP e emissão de prompt. Interface parece pequena, mas transfere ordenação temporal ao plugin e ao gate.
- Remover todos os builtins e reativar uma lista manual: mais superfície de configuração e inventário de dependências; fragiliza serviços necessários sem reduzir o problema específico.
- Liberar `execute`: muda o tratamento avaliado e enfraquece o contrato de ferramentas. É outra modalidade, não correção deste eval.

## Verificação e riscos

Reprodução Node deve simular builtin browser depois do filtro e falhar no estado anterior. Config tests exigem remoção privada, baseline três e MCP direto. Fixtures de catálogo devem rejeitar ferramenta CodeMode mesmo com nome correto. Preflight real verifica os quatro braços/roles sem inferência. Preservar evidências antigas e rodar com saída nova. Dependência aceita: binário fixado; qualquer atualização exige novo grounding, não aceitação permissiva.

## Síntese

Preferência deste candidato: configuração declarativa e certificado explícito de representação. A decisão comparativa pertence ao juiz; não há implementação nesta proposta.
