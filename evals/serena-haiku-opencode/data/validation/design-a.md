# Design A — experimento fatorial no núcleo existente

## Problem

Medir se o pacote de navegação e edição do Serena melhora aprovação, tempo e uso de tokens do Haiku no OpenCode, mantendo provider, esforço, tarefas e condições do par. O núcleo de exploração já captura identidade e transporte; o grader de implementação já protege o contrato e o aceite privado. A fronteira difícil é permitir MCP no conjunto de ferramentas sem abrir shell host ou compartilhar estado entre trials.

## Usage (caller's view)

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py validate --out ferramentas/haiku-serena-opencode/validation/check-1
python3 -B ferramentas/haiku-serena-opencode/bench.py preflight --out ferramentas/haiku-serena-opencode/validation/native-1
python3 -B ferramentas/haiku-serena-opencode/bench.py run --out ferramentas/haiku-serena-opencode/results/full-1
```

`run` padrão executa 120 trials, sem smoke de qualidade como gate. `plan` congela a agenda sem modelos. Um smoke opcional usa destino novo e casos route/py-document-scope com uma repetição: oito trials, separados do denominador principal. Não acrescentar um campaign wrapper ao usuário.

Três call sites internos concretos:

```python
rows = schedule(case_ids=CASES, reps=5, seed=20261012, configurations=CONFIGURATIONS)
result = run_trial(rows[0], out, private_root, args)
comparison = compare_pairs(load_records(out), frozen_manifest)
```

## Shape

```python
Effort = Literal["medium", "high"]
ToolArm = Literal["native", "serena"]

@dataclass(frozen=True)
class Configuration:
    id: str                  # haiku-medium-native, haiku-medium-serena, etc.
    model: Candidate         # proven existing Haiku identity and transport
    arm: ToolArm

@dataclass(frozen=True)
class ExploreCase:
    id: str
    definition: dict         # existing strict answer/evidence contract

@dataclass(frozen=True)
class ImplementCase:
    id: str
    task: TaskSpec           # corrected, frozen request + patch/acceptance contract

Case = ExploreCase | ImplementCase

def schedule(case_ids, reps, seed, configurations) -> list[dict]: ...
def manifest(case_ids, reps, seed, limits, cache) -> dict: ...
def run_trial(row, out, private_root, args) -> dict: ...
def prepare(root, work, configuration, case, args) -> tuple[dict, dict]: ...
def audit(root, work, configuration, case, args) -> dict: ...
def parse_session(data, model, work, allowed_tools) -> dict: ...
def grade(case: Case, work, final, out, args) -> dict: ...
def compare_pairs(records, frozen) -> dict: ...
```

Núcleo de agenda/loop/report é uma única cópia mínima do runner exploratório. `Configuration` envolve Candidate, sem alterar a identidade de wire em função do MCP. O case union decide materialização, permissões e corretor num único lugar. Não criar interface de plugins/adapters para apenas dois contratos. Validações de CLI/MCP/export entram nas fronteiras existentes; lógica de agenda e pares permanece pura.

Casos exploratórios: route, config, feature. Cobrem fluxo entre arquivos, precedência e resolução de implementação concreta. Implementação: py-document-scope, py-atomic-import e py-money-contract da cópia corrigida. Nenhum request/aceite é inventado ou relaxado para o braço Serena. Três casos × cinco repetições × quatro configurações = 60 por papel, 120 total, 30 pares com/sem MCP por esforço e 15 por papel/esforço. Na verdade são seis problemas distintos e cinco repetições operacionais; o relatório não chamará isso de 120 tarefas independentes.

Defaults mantêm OpenCode 2.0.26, cli_proxy/cpa-claude-haiku-5-5, wire claude-haiku-5-5, adaptive thinking e esforço medium/high, cap inteiro 128000. Fixar 300s/25steps para exploração e o limite implementador aprovado pelo protocolo herdado; o limite de cada papel deve ser idêntico em ambos os braços e aparecer no freeze. Caso o protocolo novo escolha 300s/25steps também para implementação, registrar explicitamente a diferença em relação ao suite implementador antigo. Admission budget global deve comportar a agenda inteira e não virar filtro oculto de quality.

Isolamento: root e projeto por trial, XDG/OPENCODE_TEST_HOME/SERENA_HOME próprios, configuração Serena completa e fixed_tools, memórias vazias/desativadas, context single_project, read_only para exploração, project_serena_folder_location externo à fixture. MCP local stdio iniciado pelo OpenCode. Terminal implementação continua Docker sem rede; patch é reaplicado e aceito em container separado read-only. O braço nativo não inicia Serena. A execução é sequencial; nenhuma pasta/cache de projeto/memória mutável é compartilhada.

Ferramentas de leitura úteis: initial_instructions, get_symbols_overview, find_symbol, find_referencing_symbols, search_for_pattern, possivelmente get_diagnostics_for_file se comprovado no LSP Python. Implementação acrescenta replace_symbol_body, insert_before_symbol e insert_after_symbol; rename_symbol somente se comprovado disponível e adequado no backend Python. Ferramentas administrativas, shell, memória, onboarding, troca de projeto e REPL são excluídas. Derivar permissões/parser da mesma lista, verificando os nomes reais no catálogo nativo antes de modelos.

Métrica principal: aprovação completa por papel/esforço/braço, sem exclusão dos trials que não usam Serena. Exploração divide resposta literal, evidência válida e cobertura; implementação divide escopo, compilação, regressão, aceite e conclusão. Tempo total inclui startup, MCP e ferramentas; reportar startup observável e trechos provider separadamente, sem subtração causal inventada. Comparar tempos pareados tanto no conjunto completo com status quanto nos pares ambos aprovados. Tokens, toolcalls, uso útil MCP, erros/timeout e overhead são secundários. Não converter assinatura em USD a partir de custo reportado zero.

## Synthesis decision

Preenchido pelo orquestrador após cruzar os desenhos. Esta proposta é candidata A, não decisão final.

## Tradeoffs accepted

- Aceitamos duplicar localmente o núcleo congelado em troca de não alterar evidências antigas nem depender de imports mutáveis entre suites.
- Aceitamos medir o pacote ferramentas+instruções Serena em troca de representar o uso real no OpenCode; não alegaremos isolar só algoritmo LSP.
- Aceitamos reutilizar tarefas sintéticas conhecidas em troca de comparação pareada barata; o resultado será piloto operacional e não garantia geral de segurança.

## Alternatives considered

Um wrapper executando dois runners independentes deixaria agenda/pares/estatísticas/stop policies duplicados e esconderia somente a invocação; sua interface aparentaria ser pequena, mas callers ainda precisariam reconciliar duas evidências e controles. Um novo framework de adapters de harness seria mais flexível, mas introduziria uma interface larga para dois casos de contrato que um union resolve localmente. Ambas alternativas foram rejeitadas por menor profundidade da interface e propriedade dividida.

## Open questions and risks

O preflight comprovará ferramentas, LSP Python, startup e ausência de download antes de inferência? Essa é uma questão de prova de integração, resolvida pelo gate infra, não por aprovação humana. O transform terminal do binário preserva tools MCP exatamente como o catálogo indica? O gate deve capturar superfície final e uma chamada de ferramenta sem modelo. Como o tempo de indexação se distribui entre boot e primeira busca? O relatório usará regiões observáveis e assinalará o que não for separável.

## Next implementation step

Copiar o núcleo congelado no pacote novo e escrever primeiro a prova de catálogo/execução MCP no OpenCode sem inferência, junto com o case union e a permissão terminal+Serena, antes de agendar os modelos.
