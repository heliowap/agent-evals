# Exploração Haiku 5.5, candidato B

## Uso, escrito antes dos tipos

Este desenho cria `exploracao/haiku-5-5` como um experimento independente. A CLI nova controla cinco esforços Haiku e chama funções da base congelada por um adapter. Os arquivos congelados continuam com os mesmos bytes.

Execute os comandos abaixo a partir de `~/VSCode/Lab/evals`. São exemplos de uso futuro, não comandos executados nesta etapa.

```sh
python3 -B exploracao/haiku-5-5/haiku.py plan \
  --out exploracao/haiku-5-5/plans/haiku-20261011

python3 -B exploracao/haiku-5-5/haiku.py validate \
  --plan exploracao/haiku-5-5/plans/haiku-20261011 \
  --out exploracao/haiku-5-5/validation/static-20261011

python3 -B exploracao/haiku-5-5/haiku.py preflight \
  --plan exploracao/haiku-5-5/plans/haiku-20261011 \
  --out exploracao/haiku-5-5/validation/native-20261011

python3 -B exploracao/haiku-5-5/haiku.py run \
  --plan exploracao/haiku-5-5/plans/haiku-20261011 \
  --phase smoke \
  --out exploracao/haiku-5-5/results/smoke-20261011

python3 -B exploracao/haiku-5-5/haiku.py run \
  --plan exploracao/haiku-5-5/plans/haiku-20261011 \
  --phase pilot \
  --smoke exploracao/haiku-5-5/results/smoke-20261011 \
  --out exploracao/haiku-5-5/results/pilot-20261011

python3 -B exploracao/haiku-5-5/haiku.py report \
  --in exploracao/haiku-5-5/results/pilot-20261011 \
  --out exploracao/haiku-5-5/reports/pilot-20261011
```

`plan` e `validate` não executam OpenCode. `preflight` executa descoberta local e importa uma credencial privada, sem inferência. Cada `run` repete seu próprio preflight. O preflight anterior é evidência de diagnóstico e não substitui esse controle.

O plano congela os dois perfis. O smoke tem `route`, uma repetição e os cinco esforços, total de cinco sessões. O piloto tem `route`, `config`, `retry`, `permission`, `feature` e `absence`, cinco repetições e os cinco esforços, total de 150 sessões. Não existem flags para trocar casos, candidatos, esforços, seed, limite de saída, timeout ou orçamento desta comparação. `--binary`, `--database` e `--cache` escolhem entradas locais antes do congelamento.

Todo destino precisa ser novo, estar sob `exploracao/haiku-5-5` e não resolver para um caminho antigo por symlink. Uma pasta existente não é resumida nem sobrescrita. `report` lê a fase inteira e escreve somente documentos derivados numa pasta nova.

As chamadas do consumidor dentro do processo exclusivo da CLI são estas. A CLI não expõe os objetos do core.

```python
# haiku.py, chamada de smoke
experiment = Experiment.open(package_root)
plan = experiment.load_plan(args.plan)
receipt = experiment.run(plan, SmokePhase(NewOutput(args.out)))
raise SystemExit(receipt.exit_code)
```

```python
# haiku.py, chamada de piloto
experiment = Experiment.open(package_root)
plan = experiment.load_plan(args.plan)
permit = experiment.accept_smoke(plan, args.smoke)
receipt = experiment.run(plan, PilotPhase(NewOutput(args.out), permit))
raise SystemExit(receipt.exit_code)
```

```python
# report, sem credencial, OpenCode ou inferência
experiment = Experiment.open(package_root)
phase = experiment.load_phase(args.input)
receipt = experiment.report(phase, NewOutput(args.out))
raise SystemExit(receipt.exit_code)
```

`accept_smoke` confere as cinco evidências originais da fase. Um `passed: true` isolado ou uma linha de relatório não concede o permit. O piloto recusa smoke histórico, smoke parcial, smoke de outro plano e smoke com hashes diferentes dos controles atuais.

## Mapa dos módulos

```text
exploracao/haiku-5-5/
  haiku.py                    CLI e bootstrap de imports, sem política experimental
  experiment.py               contrato Haiku, adapter do core, execução e diagnóstico
  evidence.py                 congelamento, guards, arquivos exclusivos e exportação
  README.md                   contrato e comandos desta configuração experimental
  baseline/
    freeze.json               cópia do freeze da rodada R2, somente proveniência
    frozen-source/
      bench.py                bytes originais
      runtime.py              bytes originais
      cases.py                bytes originais
      observer.js             bytes originais
      test_cases.py            bytes originais
      test_matrix.py           bytes originais
      test_runtime.py          bytes originais
      README.md               bytes originais, documentação histórica
  tests/
    test_experiment.py         coorte, agenda, gate, configuração e diagnósticos
    test_evidence.py           guards e exportação real com subprocesso sintético
  plans/, validation/, results/, reports/
```

Não há uma CLI alternativa dentro do adapter, daemon, RPC, worker por trial ou framework de providers. O caminho de leitura principal é `haiku.py`, `experiment.py` e `evidence.py`. As funções originais chamadas pelo adapter ficam visíveis na tabela abaixo.

| Conhecimento | Único dono | Reuso do core |
|---|---|---|
| Coorte e controles Haiku | `experiment.py` | Constrói `runtime.Candidate`, nunca consulta o registry antigo |
| Ordem dos trials | `bench.schedule` congelado | Passa os cinco candidatos explicitamente em toda chamada |
| Corpus, perguntas e notas | `cases.py` congelado | `build`, `prompt`, `snapshot`, `grade` |
| Configuração comum e isolamento | Adapter em `experiment.py` | `runtime.configuration`, `private_env`, `credential`, `credential_secrets` |
| Descoberta e identidade | Core congelado | `audit`, `read_requests`, `verify_requests`, `parse_session` |
| Cap efetivo e fins nativos | Adapter em `experiment.py` | Acrescenta provas ao resultado dos verificadores existentes |
| Subprocessos comuns | `runtime.command` congelado | Versão, importação, invocação da tarefa e APIs de descoberta |
| Export da sessão | `evidence.py` | Não usa `runtime.command` para exportação |
| Proveniência e integridade | `evidence.py` | Usa os hashes originais como entrada, sem chamar `bench.manifest` |
| Relatório Haiku | `experiment.py` | Reusa `bench.pair_detail` após adaptar somente os resultados elegíveis |

## A fronteira do core

A origem é `exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. Antes de copiar, o construtor do pacote confere seus sete arquivos de código, o README e os 23 hashes da fixture contra o `freeze.json` R2. O pacote copia os oito arquivos sem alterações e registra o hash do próprio freeze. `cases.py`, `test_cases.py` e `observer.js` permanecem byte equivalentes. O construtor não executa a CLI histórica.

O adapter importa a base com os nomes naturais `bench`, `runtime` e `cases`, dentro do processo dedicado da CLI nova. `haiku.py` não se chama `bench.py`, por isso não concorre com o módulo histórico. O loader faz uma carga única, antes de iniciar qualquer thread ou subprocesso:

1. Verifica todos os hashes da base copiada.
2. Recusa qualquer `bench`, `runtime` ou `cases` já carregado de outra origem.
3. Usa temporariamente o diretório congelado para os imports naturais e restaura o caminho de busca depois da carga.
4. Confere `__file__` dos três módulos e entrega somente um objeto privado `_FrozenCore` ao adapter.

Esse bootstrap usa o mecanismo normal de import do Python. Não escreve aliases em `sys.modules`, não substitui funções, não altera `DEFAULT_CANDIDATES`, `CANDIDATES`, `ROOT`, `configuration`, `command` ou `parse_session`. Os defaults antigos permanecem intocados e inacessíveis à seleção da CLI Haiku. O processo usa `-B` e `PYTHONDONTWRITEBYTECODE=1`, sem gerar `__pycache__` na base. Não se promete que esse adapter seja uma biblioteca para carregar várias bases no mesmo interpreter. Uma tentativa desse uso falha no loader.

`bench.schedule(selected, reps, seed, candidates)` já aceita coorte explícita. O adapter passa os cinco candidatos e valida o retorno em tipos próprios. Portanto, não duplica o algoritmo de embaralhamento e rotação. A execução sequencial da fase pertence à CLI nova, pois o `bench.main` antigo inclui a CLI e os estados antigos.

Não se chamam `bench.main`, `bench.run_trial`, `bench.preflight`, `bench.manifest`, `bench.check_freeze` nem `bench.report`. `run_trial` escolhe candidatos no registry global. `prepare` grava diretamente a configuração antiga. `manifest` descobre fontes no diretório antigo e declara políticas de Fast. `report` tem categorias e texto que não distinguem truncamento. Trocar essas funções por monkeypatch faria o contrato real depender da ordem de carga e tornaria o freeze enganoso.

Há duplicação deliberada de cerca de três fluxos curtos, não de uma segunda suíte: a preparação privada, a execução e persistência de um trial, e o loop de admissão da fase. O adapter reaproveita os cálculos e validadores existentes dentro desses fluxos. Não copia seu grader, corpus, scheduler, observador ou parser de identidade.

## Tipos derivados do uso

Os tipos abaixo são um contrato de desenho. Os corpos são stubs. Não constituem implementação entregue.

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal, NewType, TypeAlias

Sha256 = NewType("Sha256", str)
PlanId = NewType("PlanId", str)
TrialId = NewType("TrialId", str)
SessionId = NewType("SessionId", str)

class Effort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"

CaseId: TypeAlias = Literal[
    "route", "config", "retry", "permission", "feature", "absence"
]

@dataclass(frozen=True)
class Controls:
    seed: Literal[20261010] = 20261010
    steps: Literal[25] = 25
    trial_timeout_s: Literal[300] = 300
    phase_budget_s: Literal[21600] = 21600
    export_timeout_s: Literal[45] = 45
    context_limit: Literal[272000] = 272000
    output_limit: Literal[128000] = 128000
    tools: tuple[str, ...] = ("read", "glob", "grep", "list")
    automatic_inference_retries: Literal[0] = 0

@dataclass(frozen=True)
class Trial:
    id: TrialId
    pair: int
    case: CaseId
    repetition: int
    position: int
    effort: Effort

@dataclass(frozen=True)
class LocalInputs:
    binary: Path
    credential_database: Path
    catalog: Path

@dataclass(frozen=True)
class ReviewedPlan:
    id: PlanId
    root: Path
    fingerprint: Sha256
    controls: Controls
    smoke_schedule: tuple[Trial, ...]
    pilot_schedule: tuple[Trial, ...]
    inputs: LocalInputs

@dataclass(frozen=True)
class NewOutput:
    path: Path
    # Boundary parser exige pasta inexistente sob o pacote novo, sem symlink.

@dataclass(frozen=True)
class CompleteSmoke:
    phase_root: Path
    plan_id: PlanId
    fingerprint: Sha256
    evidence_digest: Sha256
    # Construtor privado. Só accept_smoke cria este tipo após reler evidências.

@dataclass(frozen=True)
class SmokePhase:
    output: NewOutput

@dataclass(frozen=True)
class PilotPhase:
    output: NewOutput
    smoke: CompleteSmoke

PhaseRequest: TypeAlias = SmokePhase | PilotPhase

@dataclass(frozen=True)
class Grade:
    passed: bool
    answer_correct: bool
    evidence_correct: bool
    checks: dict[str, bool]
    # Espelha o resultado original. Não recalcula nem flexibiliza o contrato.

@dataclass(frozen=True)
class AssistantEnd:
    index: int
    finish: str | None
    raw_finish: str | None

@dataclass(frozen=True)
class NativeDiagnosis:
    assistant_ends: tuple[AssistantEnd, ...]
    output_limit_reached: bool
    terminal_output_limit_reached: bool
    execution_outcome: str | None
    # Campos ausentes ficam desconhecidos, nunca são inventados a partir de tokens.

@dataclass(frozen=True)
class Delivered:
    grade: Grade

@dataclass(frozen=True)
class Undelivered:
    reason: Literal["missing_final", "task_failed", "not_exportable"]

Delivery: TypeAlias = Delivered | Undelivered

@dataclass(frozen=True)
class Attested:
    request_count: int
    output_limit: Literal[128000]
    session: SessionId
    evidence_digest: Sha256

@dataclass(frozen=True)
class BrokenIntegrity:
    kind: Literal["infra_error", "scope_violation"]
    stage: str
    explanation: str

Integrity: TypeAlias = Attested | BrokenIntegrity

@dataclass(frozen=True)
class TrialResult:
    trial: Trial
    integrity: Integrity
    delivery: Delivery
    native: NativeDiagnosis
    process_end: Literal[
        "returned", "task_error", "timeout", "interrupted"
    ]
    run_wall_s: float | None
    # Uso/custo mantêm input/output/reasoning/cache separados e valores unknown.
    # Uma nota incorreta e um fim length podem coexistir, sem perder a causa.

@dataclass(frozen=True)
class NotRun:
    trial: Trial
    reason: str
    # Não inventa integridade, entrega, duração nem sessão para uma tarefa ausente.

PhaseRow: TypeAlias = TrialResult | NotRun

@dataclass(frozen=True)
class PhaseReceipt:
    root: Path
    planned: int
    attempted: int
    stop_reason: Literal[
        "all_attempted", "budget_exhausted", "infra_error",
        "scope_violation", "interrupted", "preflight_blocked", "gate_blocked"
    ]
    exit_code: int

class Experiment:
    @classmethod
    def open(cls, package_root: Path) -> "Experiment":
        raise NotImplementedError

    def plan(self, inputs: LocalInputs, output: NewOutput) -> ReviewedPlan:
        raise NotImplementedError

    def load_plan(self, root: Path) -> ReviewedPlan:
        raise NotImplementedError

    def validate(self, plan: ReviewedPlan, output: NewOutput) -> Path:
        raise NotImplementedError

    def preflight(self, plan: ReviewedPlan, output: NewOutput) -> Path:
        raise NotImplementedError

    def accept_smoke(self, plan: ReviewedPlan, root: Path) -> CompleteSmoke:
        raise NotImplementedError

    def run(self, plan: ReviewedPlan, phase: PhaseRequest) -> PhaseReceipt:
        raise NotImplementedError

    def load_phase(self, root: Path) -> PhaseReceipt:
        raise NotImplementedError

    def report(self, phase: PhaseReceipt, output: NewOutput) -> PhaseReceipt:
        raise NotImplementedError
```

As dataclasses representam dados já validados. `Literal` é uma prova estática auxiliar, não um mecanismo de validação de JSON. O loader valida tipos, valores, inventários e cardinalidades na entrada. Objetos públicos não carregam uma lista arbitrária de providers ou o dicionário de configuração nativo.

O único catálogo da coorte é o enum `Effort`, na ordem mostrada. IDs, seleção OpenCode, variantes, inventário e relatório derivam dele. `_HaikuCohort` exige os cinco valores uma vez cada, sem duplicatas. Sua conversão privada cria cinco `runtime.Candidate` com os valores constantes:

```text
id                haiku-<effort>
provider          cli_proxy
model             cpa-claude-haiku-5-5
variant           <effort>
credential        cli_proxy
upstream          http://127.0.0.1:8317/v1
effort            <effort>
fast              false
wire_model        claude-haiku-5-5
protocol          messages
auth_type         key
```

## Signatures internas e fluxo

```python
# experiment.py. Estes nomes são privados ao pacote.

class _FrozenCore:
    @classmethod
    def load_verified(cls, source_root: Path, origin_freeze: Path) -> "_FrozenCore":
        raise NotImplementedError

    def schedule(self, kind: Literal["smoke", "pilot"], controls: Controls) -> tuple[Trial, ...]:
        # TODO: criar coorte completa, chamar bench.schedule com candidates explícitos,
        # validar linhas, converter candidate ID em Effort e descartar wire objects.
        raise NotImplementedError

    def build_fixture(self, work: Path) -> "CorpusSnapshot":
        raise NotImplementedError

    def prompt(self, case: CaseId) -> str:
        raise NotImplementedError

    def grade(self, case: CaseId, work: Path, final: str) -> Grade:
        raise NotImplementedError

def _haiku_configuration(core: _FrozenCore, effort: Effort, plugin: Path) -> "NativeConfig":
    # TODO: obter runtime.configuration de um Candidate novo e dicionário novo.
    # Mudar somente limit.output para 128000 e cadastrar as cinco variantes explícitas.
    # Cada variante tem settings.effort igual ao seu id. Conferir o delta permitido.
    raise NotImplementedError

def _prepare_trial(core: _FrozenCore, plan: ReviewedPlan, root: Path,
                   work: Path, effort: Effort) -> "PrivateRuntime":
    # TODO: private_env, observer original, configuração Haiku, catálogo congelado,
    # versão exata 2.0.26, import auth key 0600 e unlink no finally.
    # Não chamar runtime.prepare e regravar uma configuração que já ficou obsoleta.
    raise NotImplementedError

def _inspect_native_export(data: object) -> NativeDiagnosis:
    # TODO: validar estrutura mínima, preservar finish/rawFinish de todos os assistentes
    # e o fim do último, antes de chamar o parser de tarefa do core.
    raise NotImplementedError

def _attest_transport(core: _FrozenCore, effort: Effort, records: object,
                      session: SessionId | None) -> Attested:
    # TODO: runtime.verify_requests primeiro; exigir max_tokens inteiro 128000
    # em TODAS as requisições, mesmo as não-200 ou incompletas.
    raise NotImplementedError

def _execute_trial(core: _FrozenCore, plan: ReviewedPlan, trial: Trial,
                   output: Path, private_root: Path, guards: "GuardSet") -> TrialResult:
    # TODO: checks antes; fixture fria; prepare + audit; run exato; salvar eventos;
    # exportar uma vez para arquivo regular; preservar bytes; extrair fins;
    # parse_session original; atestar requests; grade original; finally com checks depois.
    raise NotImplementedError

def _render_report(plan: ReviewedPlan, rows: tuple[PhaseRow, ...]) -> "ReportData":
    # TODO: contar categorias separadas; dez comparações entre esforços;
    # chamar pair_detail somente com duas entregas elegíveis no mesmo caso e repetição.
    raise NotImplementedError
```

`_prepare_trial` conserva canonical `anthropic`, pacote `@opencode/ai/providers/anthropic`, baseURL, modelID, contexto, instrução do `navigator`, permissões e 25 passos produzidos pela função original. As cinco variantes explícitas ficam em `model.variants` com `settings.effort`. Não se inventa uma opção nativa de thinking não documentada. O contrato exige `adaptive`, e a prova é a observação das requisições.

`runtime.audit` recebe a configuração final e o Candidate explícito, verifica fontes privadas, plugin ativo, modelo nativo, wire model e esforço. O observer original já captura `thinking_type` e `max_tokens`; o adapter verifica ambos. Um preflight com zero requisições não declara esses campos encaminhados. Somente o smoke pode demonstrar isso.

O comando medido permanece `opencode run --standalone --auto --format json --agent navigator --model <selection> --title Navigation <prompt>`. Só o processo `run` entra em `run_wall_s`, incluindo boot, ferramentas e recuperações internas. Preparação, auditoria, export e grade continuam fora dessa medida. O adapter não agenda uma segunda inferência para o mesmo trial.

O parser original de sessão continua verificando workspace, identidade de todas as mensagens, agente, uma mensagem do usuário, idle terminal e ferramentas. A extração diagnóstica acontece antes porque esse parser lança `TaskFailure` para final vazio e não devolve `finish`. `length` ou `max_tokens` registrados não desaparecem atrás desse erro.

## Captura e integridade

```python
# evidence.py. Um dono por artefato. Nenhum processo publica result.json além do adapter.

@dataclass(frozen=True)
class FileDigest:
    path: str
    bytes: int
    sha256: Sha256

@dataclass(frozen=True)
class ExportReceipt:
    artifact: Path
    exit_code: int | None
    timed_out: bool
    raw_bytes: int
    raw_sha256: Sha256
    preserved_bytes: int
    preserved_sha256: Sha256
    parse_error: str | None
    json_char_offset: int | None
    json_byte_offset: int | None

class GuardSet:
    def before_phase(self) -> "GuardReceipt":
        raise NotImplementedError

    def before_trial(self, private: Path, corpus: "CorpusSnapshot") -> "GuardReceipt":
        raise NotImplementedError

    def after_trial(self, private: Path, corpus: "CorpusSnapshot") -> "GuardReceipt":
        raise NotImplementedError

    def after_phase(self) -> "GuardReceipt":
        raise NotImplementedError

def capture_export(argv: tuple[str, ...], work: Path, env: dict[str, str],
                   destination: Path, secrets: "SecretSet", timeout_s: Literal[45]) -> ExportReceipt:
    # TODO: criar stdout temporário e stderr com O_EXCL, 0600, em runtime privado.
    # Popen recebe lista argv, shell=False, DEVNULL e start_new_session=True.
    # stdout é o FD de arquivo regular. Esperar, matar grupo no timeout e esperar de novo.
    # Após saída, ler os bytes completos; redigir segredos por substituição de bytes.
    # Publicar a cópia sanitizada antes de tentar UTF-8 estrito e json.loads.
    # Registrar hashes/tamanhos brutos e preservados, exit/timeout e offsets do parse.
    # Remover somente os temporários não sanitizados no finally.
    raise NotImplementedError

def freeze_phase(plan: ReviewedPlan, kind: Literal["smoke", "pilot"],
                 output: NewOutput) -> "PhaseEnvelope":
    raise NotImplementedError
```

Não há stdout de export em `PIPE`, shell, cap de captura, decodificação com `errors="replace"`, reserialização do JSON preservado ou tentativa de consertar JSON. A sanitização preserva a ordem e todos os bytes não secretos. O sanitizador também conhece as representações JSON escapadas das credenciais e remove valores sobrepostos em ordem de comprimento. Seus testes incluem segredo dividido entre chunks do produtor, Unicode e bytes inválidos. Ele opera depois de o processo terminar, sem depender de fronteiras de chunks.

Uma exportação válida, inválida, parcial, com exit não-zero ou timeout sempre deixa `session.export.sanitized.json`, `export.stderr.sanitized.txt` e `export-meta.json`. O nome não afirma que o conteúdo passou no parser. O JSON diagnóstico conserva offsets, linha e coluna quando disponíveis. Se a exportação não é confiável, o trial é `infra_error`; uma nota zero de capacidade não substitui essa falha. A primeira exportação nunca é descartada nem sobrescrita. Uma exportação manual futura da mesma sessão precisa de outro nome e não reabre o trial oficial.

O manifesto novo tem schema próprio, `haiku-experiment/v1`. Não se chama `bench.manifest` e não se alteram seus objetos. O envelope contém:

- Hash e caminho da origem R2, mais o mapa dos oito arquivos herdados.
- Inventário de todos os arquivos executáveis novos e da documentação que define o protocolo, inclusive o loader e testes.
- Cópia verificável de core, adapter e catálogo no `frozen-source` da fase, organizada em diretórios diferentes. O runner externo à cópia entra no inventário também.
- Executável resolvido, hash do arquivo realmente passado aos subprocessos, versão esperada e versão observada no preflight.
- Coorte derivada, configurações finais, hashes dos seis prompts, definições dos casos, 23 arquivos da fixture, agenda e controles.
- Política de export, sanitização, classificação, retries, gate e orçamento.
- Identificador do plano, fingerprint comum do experimento e, no piloto, digest das evidências do novo smoke.
- Inventário inicial dos arquivos antigos de exploração, com caminhos e hashes, excluindo somente `exploracao/haiku-5-5`.

O fingerprint comum exclui apenas atributos que diferem por definição entre smoke e piloto, como perfil, contagem e diretório de saída. Inclui coorte, cap, casos originais, prompts, grader, observador, adapter, runtime, catálogo e controles compartilhados. O PlanId único impede reaproveitar um smoke de outro plano mesmo quando os hashes coincidem.

Cada trial verifica fonte, protocolo, executável e catálogo antes e depois. Confere o catálogo original e a cópia privada. Confere a fixture inteira depois, inclusive conjunto de caminhos, conteúdo, tipo e symlinks, sem depender apenas do snapshot original, que ignora symlinks. Alteração do corpus é `scope_violation`; alteração dos controles ou impossibilidade de observá-los é `infra_error`. Os checks pós-trial executam no `finally`, mesmo com export inválido, timeout ou erro de parser. Checks de envelope no começo e no fim da fase cobrem também o último trial e fases sem nenhum trial iniciado.

Um writer controla a pasta de cada trial. Arquivos de resultado são publicados por substituição atômica. Um acidente entre a gravação de `running` e o terminal fica visível como incompleto. O leitor usa a agenda do envelope para produzir `not_run`, em vez de reduzir o total planejado ao número de pastas que encontrou.

## Diagnóstico e gate

O relatório não usa uma única propriedade `passed` para decidir toda a interpretação. Ele mantém estes fatos:

| Fato observado | Categoria principal no relatório | Conduta |
|---|---|---|
| Entrega válida, fim sem limite e grade original aprovada | Correta | Elegível para pares |
| Entrega válida, fim sem limite e grade original reprovada | Incorreta | Conserva `answer_correct`, `evidence_correct` e checks |
| `finish=length` ou `rawFinish=max_tokens` no último assistente | Limite de saída | Conserva grade se houver entrega, mas não conta como incorreta comum |
| Limite numa mensagem anterior, com conclusão posterior válida | Correta ou incorreta, com recuperação registrada | Conserva todos os fins e o indicador de limite intermediário |
| Final ausente ou idle de falha, sem limite terminal conhecido | Erro da tarefa | Não inventa nota nem causa de truncamento |
| Tarefa excede 300 s | Timeout | Continua para o próximo trial |
| Export inválido, identidade errada, cap ou thinking não comprovados | Infraestrutura | Para a fase, preserva diagnóstico e próximos `not_run` |
| Corpus alterado | Violação de escopo | Para a fase |
| Orçamento esgotado ou interrupção | Fase incompleta | Mantém agenda inteira e exit não-zero |

`output_limit_reached` considera todos os assistentes. `terminal_output_limit_reached` identifica o último. O adapter não infere limite a partir de 128.000 tokens, de resposta vazia ou de idle `succeeded`. O último caso histórico com `finish=length`, `rawFinish=max_tokens`, raciocínio de 32.768 e saída zero deve produzir diagnóstico de limite mesmo quando `parse_session` rejeita a entrega.

Uma falha de infraestrutura pode coexistir com `length`; a integridade continua determinando se a medição é utilizável. Os fatos nativos ficam preservados no diagnóstico. A mesma separação vale para nota correta sob limite terminal.

O gate exige cinco trials do novo smoke, exatamente um por esforço, com todas as integridades atestadas, nenhuma interrupção ou timeout, nenhuma truncagem terminal e grade original aprovada em cinco de cinco. Confere o encaminhamento do modelo, rota Messages, `adaptive`, esforço, identidade, agente e `max_tokens=128000` em todas as chamadas. Relê os artefatos e hashes, inclusive sessão, requests e receipts de guard. Falha em qualquer condição impede iniciar o primeiro trial do piloto.

O piloto tem dez pares de esforços. Cada par usa somente as duas entregas aprovadas e sem limite terminal no mesmo caso e repetição. Os tempos gerais de entregas normais continuam incluindo respostas incorretas e dizem isso no texto. Limites de saída, timeouts, infraestrutura e ausências ficam em contagens próprias. O relatório conserva o caráter descritivo e não declara vencedor automático. Os resultados sob cap 128.000 constituem outra configuração experimental e não são misturados com cap 32.768.

## Orçamento e códigos de saída

Cada fase possui seu próprio orçamento de 21.600 s. Este candidato conserva a política da base, admissão entre trials. O relógio da fase começa antes do loop, após o preflight obrigatório. Preparação, export e grade dos trials consomem esse orçamento, embora fiquem fora de `run_wall_s`. Ao alcançar o orçamento, o adapter não inicia outro trial e grava `budget_exhausted`.

O envelope declara `budget_policy="admission_between_trials"`. Uma tarefa admitida pode terminar até 300 s depois do limite, além de preparação e export. O relatório registra o total real e não chama essa política de deadline rígido de parede. Um limite rígido exigiria supervisão adicional dos subprocessos criados dentro do core, que não oferece deadline global injetável. Não se introduz esse mecanismo neste adapter pequeno.

O loop grava o relatório de fase no `finally` e verifica o envelope após o último trial. `infra_error` e `scope_violation` interrompem a fase. Incorreta, limite de saída, erro da tarefa e timeout continuam, sem retry automático. As recuperações nativas do OpenCode permanecem nos eventos e no tempo medido.

- Exit `0` significa fase com todos os trials tentados e nenhum bloqueio de integridade. No smoke, significa também gate de cinco de cinco aprovado.
- Exit `1` significa preflight ou gate bloqueado, infraestrutura ou violação de escopo.
- Exit `2` significa entrada inválida ou contrato divergente antes de iniciar a fase.
- Exit `3` significa orçamento esgotado ou cobertura incompleta por outro motivo.
- Exit `130` significa interrupção pelo operador, com persistência dos artefatos já disponíveis.

Um piloto que tentou todos os 150 trials pode sair `0` com respostas incorretas, erros de tarefa ou timeouts. Essa saída comprova cobertura do experimento, não aprovação dos modelos. Uma fase com 149 trials tentados nunca sai `0`. `report` também devolve não-zero ao reconstituir uma fase incompleta, enquanto publica o relatório completo das ausências.

## Provas exigidas antes de inferência

Estas provas são comportamentais e locais. Nenhuma chama modelo, rede ou Docker.

| Prova | Observação esperada |
|---|---|
| Origem e cópia | Oito arquivos copiados com hashes idênticos à origem R2 e hashes previstos no freeze; `cases.py`, `test_cases.py` e `observer.js` byte equivalentes |
| Testes históricos isolados | `test_cases.py`, `test_runtime.py` e `test_matrix.py` continuam executando contra o core histórico, com o registry histórico intacto |
| Registry novo | Cinco IDs Haiku literais, cinco seleções locais exatas, nenhum candidato externo selecionável, defaults históricos sem alteração após carga |
| Imports adversários | Uma origem estrangeira de `bench`, `runtime` ou `cases` impede a carga; o loader não substitui esse módulo |
| Agenda completa | 150 linhas únicas por caso, repetição e esforço; 30 por esforço; 30 blocos de cinco; cada esforço ocupa cada posição seis vezes |
| Smoke | Cinco linhas de `route`, repetição um, uma por esforço, em pasta própria |
| Configuração | Cinco variantes com `settings.effort` correto, cap 128.000, contexto 272.000, 25 passos e somente as quatro ferramentas; delta em relação à configuração comum restrito aos controles declarados |
| Wire | Uma chamada ausente, cap 32.768, cap ausente, float ou booleano, esforço errado, thinking diferente, rota errada ou identidade diferente falham a atestação |
| Export grande | Subprocesso Python sintético escreve JSON UTF-8 com mais de 10 MiB e sai; o stdout regular preservado tem tamanho e SHA-256 esperados, sem shell |
| Export inválido | JSON truncado com exit zero e JSON válido com exit não-zero preservam stdout sanitizado e metadata; ambos falham como infraestrutura |
| Timeout de export | Processo sintético ultrapassa limite, grupo encerra, bytes parciais ficam preservados e metadata informa timeout |
| Redação | Segredo com Unicode, segredo sobreposto, segredo dividido na escrita e segredo em representação JSON escapada desaparecem, com demais bytes idênticos |
| Fins nativos | Sessão sintética `length/max_tokens`, final vazio e idle succeeded preserva o limite antes da exceção do parser; não vira incorreta comum |
| Gate | Smoke quatro de cinco, outro plano, arquivo adulterado, cap errado ou ausência de check final impedem qualquer chamada de inferência no piloto |
| Guards | Mudança de fonte, catálogo, fixture, symlink ou envelope após o último trial é detectada; interrupção de teste executa o check final |
| Cobertura e budget | Relógio sintético esgota orçamento antes do segundo trial; a agenda mantém os restantes, registra causa e retorna `3` |
| Relatório | Cinco esforços produzem dez pares; par exige dois acertos; limite terminal e infraestrutura não entram como resposta incorreta comum |
| Preservação anterior | Inventário final dos caminhos antigos é idêntico ao inicial, sem exclusões além do pacote novo |

O teste histórico de sete candidatos e 210 trials permanece isolado porque prova a base preservada. O teste novo de cinco candidatos e 150 trials prova o adapter. Um teste não é reescrito para afirmar a semântica do outro.

## Rationale

### Problema

A rodada precisa de uma coorte Haiku nova, cap uniforme comprovado e exportações diagnosticáveis. A base congelada tem um scheduler reutilizável, grader exato e bons checks de isolamento. Sua CLI resolve o registry antigo e grava uma configuração de 32.768 tokens. Alterar esses estados em memória esconderia mudanças do manifesto e faria a seleção depender da ordem de import.

### Uso

A interface inicial descreve cinco comandos e dois perfis fechados. `run` concentra carga do plano, validação, gate, preflight, execução, persistência e saída. O operador informa caminhos e entradas locais. Não coordena helpers nativos nem escolhe opções que invalidam a comparação.

### Forma

O core byte equivalente fornece corpus, grader, ordem, observação e validadores. O adapter possui somente o contrato Haiku, captura, diagnóstico e ciclo de vida da fase. A validação fica na entrada de arquivos e no retorno do core, conforme boundary-discipline. A coorte deriva de um único enum, conforme encode-lessons-in-structure. Um writer por pasta e resultados atômicos evitam estado compartilhado, conforme separate-before-serializing-shared-state. O objeto `Experiment` esconde políticas suficientes para justificar seus métodos, sem obrigar o consumidor a conhecer o wire ou as etapas internas.

### Decisão de síntese

Este é o candidato B independente. A decisão do arena pertence ao orquestrador. Sua diferença estrutural é preservar o código herdado e acrescentar um adapter com contratos próprios, em vez de editar uma cópia da CLI antiga. A síntese deve aceitar ou rejeitar o custo dos três fluxos novos e do loader isolado como uma decisão de conjunto.

### Tradeoffs aceitos

- Aceitamos repetir a orquestração de preparação e trial para preservar os arquivos e defaults originais, mantendo as funções de cálculo e validação herdadas.
- Aceitamos uma CLI com menos flexibilidade para tornar impossível selecionar uma coorte ou controle diferente nesta comparação.
- Aceitamos o bootstrap de imports numa CLI exclusiva para reusar `bench.schedule` sem AST, aliases ou monkeypatch.
- Aceitamos guardar duas árvores de fontes identificadas para distinguir a base herdada do código que controla o experimento real.
- Aceitamos o orçamento de admissão da base em troca de um adapter pequeno, com o eventual excesso e a saída incompleta declarados.

### Alternativas consideradas

Editar uma cópia de `bench.py` e `runtime.py` reduz a adaptação, mas cria duas implementações editáveis dos mesmos mecanismos e exige que o autor do próximo ajuste saiba quais arquivos são históricos. Seu custo fica dentro do código replicado. Este candidato concentra as diferenças no adapter e mantém a base verificável.

Executar a CLI antiga e fazer monkeypatch do registry, config e comando de export economiza linhas, mas expõe ordem de carga e objetos globais ao consumidor. O manifesto histórico não descreve o código substituído. Essa forma perdeu por quebrar a relação entre proveniência e execução.

Um worker permanente com protocolo próprio permitiria várias bases no mesmo processo do cliente. Ele esconde imports, mas acrescenta transporte, lifecycle e um segundo tipo de falha. A CLI exclusiva já resolve o conflito e conserva chamadas diretas, por isso o worker perdeu.

### Questões e riscos

O runner exclusivo é suficiente para a utilização prevista por CLI, ou existe requisito de carregar este experimento como biblioteca junto de outro `bench` no mesmo interpreter? A forma proposta fecha esse uso e falha antes de executar.

A política global precisa permanecer equivalente à base, ou o operador exige 21.600 s como deadline rígido incluindo preflight e finalização? Este candidato declara e conserva o orçamento de admissão. Uma exigência rígida muda o desenho do controle de processos e deve entrar na síntese, sem ser simulada por um campo no freeze.

O CLIProxy realmente serve o modelo e traduz os cinco esforços? O pedido observado prova encaminhamento, não execução a montante. O relatório precisa manter esse limite de evidência.

### Próximo passo de implementação

Construir primeiro o loader verificado, o plano fechado e as provas de byte equivalência e agenda 150, depois preencher preparação, captura, diagnóstico e execução contra esse contrato.

## Doc Delta do desenho

O README novo precisa explicar os comandos consumindo plano, o gate obrigatório, os perfis fechados, o cap observado de 128.000, as categorias diagnósticas, a política de budget, códigos de saída e a distinção entre core preservado e adapter. O README histórico copiado permanece evidência da origem. Fontes e documentação antigas não precisam de atualização porque a nova configuração vive em pacote separado. Este documento registra os deltas previstos; não há implementação ou edição de documentação do repositório nesta etapa.

Leituras de base: `bench.py` linhas 22, 42, 83, 173, 235 e 311, `runtime.py` linhas 23, 75, 108, 171, 238, 333 e 371, `cases.py` linhas 296, 306 e 352, e `observer.js` função `requestMetadata`. Grounding recebido em `/private/tmp/haiku-exploration-ground.md`. Skills lidas: architect, runner-prompt, rationale-template, design-red-flags, unslop, technical-writing e Doc Delta. O desenho foi produzido apenas por GPT, sem inferência de benchmark, rede ou Docker.
