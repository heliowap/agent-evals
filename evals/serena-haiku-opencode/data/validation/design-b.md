# Desenho B: runner misto compacto com contratos congelados

## Problema

Comparar Haiku medium/high em exploração e implementação exige duas definições de aceite e de escopo. O loop de exploração atual presume ausência de edição e MCP. Reescrevê-lo para implementação introduz caminhos condicionais em preparação, descoberta, parser, fixture e grader. Recomendo um novo loop pequeno que possua o experimento misto e reutilize somente primitivas passivas e corretoras congeladas. Os benchmarks antigos permanecem intactos.

## Uso: visão do operador

CLI proposta, todos os destinos novos:

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py plan --out ferramentas/haiku-serena-opencode/validation/plan-1
python3 -B ferramentas/haiku-serena-opencode/bench.py preflight --out ferramentas/haiku-serena-opencode/validation/preflight-1
python3 -B ferramentas/haiku-serena-opencode/bench.py run --phase smoke --out ferramentas/haiku-serena-opencode/results/smoke-1
python3 -B ferramentas/haiku-serena-opencode/bench.py run --phase full --smoke-proof ferramentas/haiku-serena-opencode/results/smoke-1 --out ferramentas/haiku-serena-opencode/results/full-1
```

O plan informa 120 trials: 6 casos × 5 repetições × 2 efforts × 2 condições. O smoke contém route e py-money-contract para as quatro configurações: oito trials separados do denominador final. Smoke valida integração, identidade, entrega e grade executável; não exige 8/8 de qualidade para admitir o piloto. Uma reprovação funcional corretamente medida é dado válido. Infraestrutura, escape de escopo, servidor/LSP indisponível ou identidade incorreta bloqueiam o full.

Chamadas internas de referência:

```python
protocol = frozen_protocol()
receipt = run_trial(protocol, Trial(case='route', rep=1, effort='medium', serena=False))
receipt = run_trial(protocol, Trial(case='py-money-contract', rep=1, effort='high', serena=True))
comparison = report(protocol, read_receipts(out))
```

O operador não coordena servidores, credenciais, containers ou graders. Um loop possui esse ciclo de vida. Nenhuma importação busca módulos mutáveis em diretórios de resultados; snapshots locais documentados e hashados entram no freeze do novo pacote.

## Forma

Arquivos novos: bench.py possui CLI/agenda/loop/report; runtime.py possui configuração privada, MCP, observação e parsing; cases.py possui os seis contratos, materialização e dispatch dos graders. vendor/ armazena as primitivas congeladas necessárias, com provenance manifest e sem o scheduler antigo. Serene context/mode e terminal.js ficam no pacote e são congelados. Evitar framework de adapters, registry de plugins, inheritance de loops e monkeypatch de runtime.AGENT/CANDIDATES/permissões.

Tipos derivados do uso:

```python
Effort = Literal['medium', 'high']
Role = Literal['exploration', 'implementation']

@dataclass(frozen=True)
class Trial:
    case: str
    rep: int
    effort: Effort
    serena: bool

@dataclass(frozen=True)
class Protocol:
    cases: tuple[Case, ...]
    configurations: tuple[Configuration, ...]
    source_hashes: dict[str, str]
    installations: InstallationProof
    limits_by_role: dict[Role, Limits]

def plan(protocol: Protocol, phase: str) -> tuple[Trial, ...]:
    raise NotImplementedError

def run_trial(protocol: Protocol, trial: Trial) -> Receipt:
    raise NotImplementedError

def report(protocol: Protocol, receipts: list[Receipt]) -> Comparison:
    raise NotImplementedError
```

Case é uma união ExplorationCase/ImplementationCase: o primeiro leva contrato JSON e âncoras, o segundo TaskSpec e contrato corrigido de patch/testes. Assim o dispatch depende do papel do próprio caso, não de um argumento independente que possa divergir. Configuration deriva identidade CLIProxy do effort e política de tools do papel+serena; uma única tabela de ferramentas gera contexto, permissões e validação do parser.

Casos: exploração route/config/feature; implementação py-money-contract corrigido, py-document-scope e py-atomic-import. Mesmos prompts, arquivos iniciais, testes e limites em ambas as condições. Tasks privadas existem somente no trusted grading root. Ordem pareada por caso/repetição e alternada dentro de blocos, seed fixo e posições balanceadas. Sem inferência concorrente para não converter contenção local/quota em tratamento.

Primitivas mantidas: exportação para arquivo regular com identidade e SHA; observador de requests passivo; cap 128000, thinking adaptive e effort; credencial importada por descoberta privada; patch reaplicado em cópia limpa; testes com marcador de execução completa. Mudanças locais explícitas: configuration/audit/parser passam a aceitar uma política exata de ferramentas; terminal.js permite terminal + ferramentas Serena fixadas, mantendo outros tools host negados.

Ferramentas Serena de exploração: initial_instructions, get_symbols_overview, find_symbol, find_referencing_symbols, search_for_pattern, get_diagnostics_for_file. Implementação acrescenta replace_symbol_body, insert_before_symbol, insert_after_symbol, rename_symbol e safe_delete_symbol. Shell, REPL, memórias, onboarding, web e activate_project ficam indisponíveis. Contexto single_project e projeto explícito no boot. initial_instructions/config não contam como uso útil; chamadas sem uso permanecem no denominador da condição com Serena. Não exigir uso para aprovação funcional nem selecionar só trials que usaram a ferramenta.

Instalação: executar o launcher local existente fixado pelo fingerprint, não `uvx --from ...@main`. SERENA_HOME, OPENCODE_TEST_HOME, XDGs, TMPDIR e pasta Serena do projeto por trial. Preservar binários/dependências instalados e hashados; cache de dependências pode ser compartilhado e precisa ser declarado. Índice, source caches e memória são frios por trial. Global config privada remove base_modes herdados e aponta project_serena_folder_location para fora da fixture.

Decisão de dependências offline: provisionar Pyright 1.1.403 uma única vez fora da região medida, copiar somente seu cache de pacotes/runtime para um cache dedicado do eval e congelar seu fingerprint. Configurar `ls_specific_settings.python.ls_base_cmd` como lista com uvx absoluto, `--offline`, `-p`, o Python fixado, `--from`, `pyright==1.1.403`, `pyright-langserver`; o backend acrescenta `--stdio`. Passar UV_CACHE_DIR dedicado e UV_OFFLINE=1, fixar Node instalado e comprovar esse comando sem rede no preflight. Cache ausente/Node ausente bloqueia, sem fallback de download durante trials. O cache compartilhado contém apenas dependências; HOME e SERENA_HOME privados e armazenamento de projeto distinto impedem reuso de índices/configurações/memórias do operador. Nunca usar `uvx --from git...@main`.

Comando MCP concreto:

```sh
~/.local/bin/serena start-mcp-server --project /private/tmp/TRIAL/work --context /private/tmp/TRIAL/context.yml --mode /private/tmp/TRIAL/mode.yml --language-backend LSP --agent-interface tools --transport stdio --enable-web-dashboard false --open-web-dashboard false --enable-gui-log-window false --log-level INFO --tool-timeout 60
```

O runtime passa ambiente privado programaticamente; não imprimir credenciais nem copiar a configuração real do usuário. A integração OpenCode usa MCP local comandado pelo próprio OpenCode. Não reutiliza o bridge/session do Codex nem inicia um servidor compartilhado HTTP. Validar o schema concreto no binário instalado antes de congelar o JSON.

## Infraestrutura e provas

1. Validar contratos: baseline compila/public passa/aceite falha, referência passa tudo; JSON de referência passa sem tornar testes privados visíveis.
2. Congelar fontes, snapshots, context/mode, binários/versões/pacotes Serena e LSP, imagem Docker por SHA e catálogo modelo. Confirmar importação editable aponta para o commit/fingerprint esperado.
3. Provar MCP sem modelo por stdio, tools/list e chamadas reais de símbolo/referência/edição em clone descartável. Provar paths relativos confinados, projeto único, sem memórias/servidores externos. Um MCP conectado com LSP quebrado não passa.
4. Provar descoberta OpenCode: tools nativas por papel + conjunto Serena exato, nenhuma instrução/plugin/skill/MCP do operador. O preflight não reutiliza índices da fixture do trial.
5. Provar terminal Docker e grading sem rede com os testes de isolamento existentes. Serena host recebe somente operações relativas à fixture; declarar que esse isolamento não é namespace OS.
6. No trial, captar delivery, requests e identidade, erros MCP, chamadas úteis, export regular+SHA e patch escopo. Timeout e limite de saída são falhas operacionais; ausência de campo/identidade/wire incompatível é infra_error e interrompe a campanha.

## Medição e decisão

Relatório separado por papel. Aprovação completa/30 por configuração; decompor resposta/citação e patch/compilação/regressão/aceite/segurança. Latência do processo OpenCode inclui boot frio MCP/LSP, tools e retries. Também medir total trial, preparação, export e grading; prontidão MCP somente se houver marcador temporal confiável. Não subtrair indexação para favorecer Serena. Comparação paired por mesmo caso/repetição: delta de aprovação e razão de latência nos pares ambos aprovados, mas tempos de rejeições e falhas aparecem separados. Distribuição de chamadas/tokens, erros e Serena usada/sem uso completam a interpretação. Três problemas por papel e cinco repetições sustentam decisão de piloto, não certificação de ausência de bugs.

## Decisão de síntese

Reservada ao orquestrador. B recomenda novo loop misto compacto, não ampliar o loop exploration.6cases.

## Trocas aceitas

- Aceitamos um novo loop explícito em troca de preservar invariantes e evidências dos dois benchmarks antigos.
- Aceitamos pequenas cópias congeladas de código estável em troca de não depender de internals mutáveis e não precisar alterar pacotes existentes.
- Aceitamos LSP em host confinado por projeto/configuração, declarando seu limite, em troca de usar exatamente a instalação Serena do operador; execução de código continua exclusivamente Docker.

## Alternativas consideradas

Estender exploration.run_trial centraliza um scheduler existente, mas força cada função a conhecer contratos de patch, MCP e diferenças de papel; o contrato público simples esconde decisões que ficariam espalhadas em ramos. Wrapper que executa dois runners completos perde a alternância por caso/repetição e duplica gates/status. Framework de adapters resolve extensibilidade futura, porém expõe tipos e métodos por estágio sem necessidade para seis casos e quatro configurações.

## Riscos a resolver antes da implementação

O OpenCode efetivamente entrega MCP instructions ou o agente precisa chamar initial_instructions? Provar na superfície real e congelar essa política. O path confinement Serena cobre todos os símbolos/paths expostos? Se não, bloquear ou retirar a ferramenta problemática. A instrumentação consegue separar boot/indexação sem aquecer o trial? Se não, medir apenas tempo total confiável. Há discrepância entre bibliotecas do ambiente uv e o lockfile? Capturar instalação real, não presumir lock executado.

## Próximo passo

Implementar primeiro preflight e manifest do runner compacto, com chamadas stdio reais e provas offline de ambos os graders, antes do primeiro trial de modelo.
