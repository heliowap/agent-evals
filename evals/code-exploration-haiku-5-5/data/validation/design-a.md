# Candidato A: copiar o core e acrescentar um wrapper fino

## Usage, pela visão de quem executa

O pacote novo é `exploracao/haiku-5-5`. O operador usa o wrapper `haiku.py`, que mantém os comandos do CLI existente e acrescenta a campanha com smoke obrigatório. Todas as saídas exigem pastas novas, salvo `report`.

```sh
python exploracao/haiku-5-5/haiku.py plan --out exploracao/haiku-5-5/results/plan-20261011
python exploracao/haiku-5-5/haiku.py validate-offline --out exploracao/haiku-5-5/results/checks-20261011
python exploracao/haiku-5-5/haiku.py preflight --out exploracao/haiku-5-5/results/preflight-20261011
python exploracao/haiku-5-5/haiku.py run --out exploracao/haiku-5-5/results/run-20261011
python exploracao/haiku-5-5/haiku.py report --out exploracao/haiku-5-5/results/run-20261011
```

Três usos concretos:

1. `plan` mostra cinco smokes e 150 trials comparativos, com os seis casos e cinco esforços. Não chama modelos. O plano não é entrada de `run`.
2. `validate-offline` verifica o corpus herdado, a agenda e a captura de exportação com processos sintéticos. `preflight` usa somente descoberta privada e exige zero requisições de modelo.
3. `run` cria seu próprio freeze, executa um smoke novo de `route`, uma repetição e cinco esforços, exige 5/5 acertos com parâmetros verificados, e só então inicia o piloto. `report` recompõe os relatórios a partir dos artefatos, sem inferência.

O wrapper aceita as localizações já existentes de `--binary`, `--database` e `--cache`. Os controles desta campanha ficam fixos: casos originais, cinco repetições no piloto, seed20261010, 25 passos, timeout300s, orçamento21600s independente por fase e saída128000. Não há opção para reutilizar o smoke da implementação anterior ou completar automaticamente uma rodada.

```text
results/run-20261011/
  campaign.json                 # fases esperadas e controles
  preserved-before.json
  preserved-after.json          # fontes e resultados antigos
  envelopes/smoke.json
  envelopes/pilot.json          # apenas se o piloto iniciar
  smoke-gate.json                # resultado do smoke recém-executado
  smoke/                        # freeze, preflight, cinco trials e relatório
  pilot/                        # freeze, preflight, 150 trials e relatório
  summary.json
  report.md
```

Se o smoke falhar, o relatório mantém o piloto previsto como `not_started`, com 150 trials `not_run`, e o processo sai não-zero. Se o orçamento terminar antes da agenda ou houver tarefas sem conclusão, também sai não-zero. O exit não avalia competência: respostas entregues e incorretas segundo o grader ainda são observações `completed`. Limite de saída, timeout e erro de tarefa permitem continuar a coleta; infraestrutura e violação de escopo interrompem a fase como na origem.

## Problem

O baseline congelado tem o isolamento, a agenda, o observador e o grader necessários, mas usa uma coorte antiga, cap32768, exportação em PIPE e um parser que perde `finish` e `rawFinish`. Seu loop também sai com sucesso quando o orçamento deixa trials pendentes. A campanha precisa conservar os seis casos e a execução sequencial, corrigir essas fronteiras e deixar fontes e resultados antigos intactos. A origem é `exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`; o grounding é `/private/tmp/haiku-exploration-ground.md`.

## Shape

### Mapa

| Arquivo na cópia nova | Responsabilidade e alteração |
|---|---|
| `haiku.py` | Wrapper da campanha, smoke gate, envelopes externos e relatório agregado. Não possui loop de trials. |
| `bench.py` | Mesmo scheduler e único loop existentes; mantém freeze, run_trial e relatório de fase; retorna exit explícito por completude. |
| `runtime.py` | `Candidate` frozen existente, tupla canônica Haiku, configuração Messages, verificação de cap, export em arquivo regular e diagnóstico de sessão. |
| `observer.js` | Cópia do observador; acrescenta somente fins nativos selecionados, inclusive stop_reason Anthropic. |
| `cases.py`, `test_cases.py` | Cópias byte a byte do baseline. Perguntas, fixture, prompts e grader não mudam. |
| `test_matrix.py`, `test_runtime.py`, `test_haiku.py`, `test_observer.mjs` | Provas relevantes adaptadas ou novas somente nesta cópia. |
| `README.md` | Protocolo desta campanha e origem de cada arquivo novo ou adaptado. |

Não há novo arquivo de spec nem loader. O domínio já está representado por `Candidate(frozen=True)`. Uma única tupla em `runtime.py` contém os cinco registros; `CANDIDATES` e `DEFAULT_CANDIDATES` usam essa tupla. Cada registro fixa provider `cli_proxy`, modelo local `cpa-claude-haiku-5-5`, wire model `claude-haiku-5-5`, protocol `messages`, credential_provider `cli_proxy`, auth_type `key`, Fast falso e baseURL `http://127.0.0.1:8317/v1`. Os IDs são `haiku-low`, `haiku-medium`, `haiku-high`, `haiku-xhigh` e `haiku-max`; variante e effort têm o respectivo valor.

`OUTPUT_LIMIT=128000` é o único dado do cap. Configuração, freeze e `verify_requests` o derivam. `configuration` declara explicitamente as cinco variantes com `settings.effort`. Mantém canonical anthropic, pacote provider nativo, contexto272000 e a mesma política read/glob/grep/list. Não precisa de branches para os outros modelos na nova coorte.

O scheduler congelado recebe essa tupla. Seus 30 blocos de caso/repetição resultam em 150 trials, 30 por esforço, com cada esforço ocupando cada posição seis vezes. O smoke usa a mesma função com `route` e uma repetição, resultando em cinco trials. O relatório usa o inventário do freeze e conserva pares somente quando ambos passaram no mesmo caso e repetição.

### Usage derivado em assinaturas

```python
# runtime.py: conserva Candidate e seus campos/propriedades existentes.
@dataclass(frozen=True)
class Candidate:
    id: str
    provider: str
    model: str
    variant: str
    credential_provider: str
    upstream: str
    effort: str
    fast: bool
    wire_model: str
    protocol: str
    auth_type: str

    @property
    def selection(self) -> str:
        raise NotImplementedError

    @property
    def identity(self) -> dict[str, str]:
        raise NotImplementedError

OUTPUT_LIMIT = 128000
# DEFAULT_CANDIDATES = tupla canônica dos cinco registros Haiku.
# CANDIDATES = DEFAULT_CANDIDATES.

# bench.py: interfaces existentes, sem outro executor.
def schedule(selected, reps, seed, candidates=None) -> list[dict]:
    # Corpo congelado conservado.
    raise NotImplementedError

def manifest(selected, reps, seed, timeout, budget, cache, candidates=None) -> dict:
    # TODO: derivar cap da constante e registrar proveniência baseline + novas fontes.
    raise NotImplementedError

def check_freeze(frozen, cache) -> None:
    # Guards existentes por trial conservados.
    raise NotImplementedError

def main(argv: list[str] | None = None) -> int:
    # TODO: aceitar argv, conservar único loop e devolver exit após report em finally.
    raise NotImplementedError

# haiku.py: opera fases, não trials.
def phase_envelope(name: str, out: Path, locations: dict):
    # TODO: contexto before/after em finally; preservar inventário e saída do core.
    raise NotImplementedError

def smoke_passed(smoke_out: Path) -> bool:
    # TODO: ler cinco resultados reais; completed+passed+request_settings_verified.
    # TODO: verificar adaptive e max_tokens128000 em toda chamada, fixture e envelope.
    raise NotImplementedError

def run_campaign(out: Path, locations: dict) -> int:
    # TODO: criar pasta exclusiva; chamar bench.main para smoke sob envelope.
    # TODO: conferir smoke_passed; chamar bench.main para piloto sob outro envelope.
    # TODO: report offline em finally; nenhum loop por trial e nenhuma mutação global.
    raise NotImplementedError

def validate_offline(out: Path) -> dict:
    raise NotImplementedError

def report_campaign(out: Path) -> dict:
    raise NotImplementedError

def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError
```

O wrapper monta argv do CLI existente e chama `bench.main(argv)` sequencialmente. `plan`, `preflight` e `report` continuam usando as funções do core; o plano agregado chama o scheduler existente. Ele não faz monkeypatch de `runtime`, não recodifica o budget e não percorre a agenda. O core escreve as pastas de fase. O wrapper escreve somente campanha, gate, envelopes e agregado. Isso mantém um único dono por artefato, per separate-before-serializing-shared-state.

O gate pertence ao `run` que acabou de criar a pasta, lê o smoke que esse mesmo `run` acabou de executar e não aceita caminho externo de smoke. Não introduz um sistema de autorização contra adulteração coordenada do operador. O CLI de `bench.py` continua disponível como executor interno de uma fase, enquanto o README apresenta o wrapper como o caminho de campanha. A política do smoke fica em uma função do wrapper, não em dois loops.

### Exportação

`runtime.command` fica intacto. A captura especializada substitui somente a chamada de exportação em `run_trial`.

```python
@dataclass(frozen=True)
class ExportCapture:
    stdout_path: Path
    stderr_path: Path
    exit_code: int
    timed_out: bool
    wall_s: float
    captured_bytes: int
    captured_sha256: str
    preserved_bytes: int
    preserved_sha256: str

# runtime.py, esconde detalhes de subprocess do bench.
def export_session(binary: str, session_id: str, work: Path,
                   env: dict[str, str], artifacts: Path,
                   secret_values: tuple[str, ...]) -> ExportCapture:
    # TODO: argv nativo, shell=False, stdout em arquivo regular0600 privado.
    # TODO: start_new_session; timeout45s; killpg e wait em timeout.
    # TODO: preservar bytes sanitizados antes de checar exit ou parsear JSON.
    # TODO: gravar metadata e remover o temporário não sanitizado.
    raise NotImplementedError
```

O filho recebe um descritor de arquivo regular para stdout. Após o término, o executor substitui segredos conhecidos nos bytes e grava `session.json` e `export.stderr` sanitizados com modo0600. Nenhum byte não secreto é trocado por `decode(errors="replace")` antes da preservação. `export.json` guarda exit, timeout, tempo, tamanhos e hashes da captura e do artefato sanitizado. Após preservar, o bench tenta decodificar e parsear; falha de UTF-8 ou JSON acrescenta diagnóstico com offset, linha e coluna quando disponíveis. JSON inválido, timeout e exit não-zero permanecem infraestrutura, com evidência intacta. Não há reexportação nem inferência automática adicional.

### Limite de saída

`parse_session` coleta identidade, fins de todos os assistentes, último fim, ferramentas, uso e idle antes de decidir sobre a entrega. Para uma sessão parseável com identidade correta, ele devolve os diagnósticos mesmo quando o final está vazio, em vez de lançar `TaskFailure` antes dessa coleta.

```python
# runtime.py; amplia o resultado existente em vez de criar uma hierarquia nova.
def parse_session(data: dict, candidate: Candidate, work: Path) -> dict:
    # TODO: conservar finish/rawFinish por assistente, final_finish e uso.
    # TODO: devolver delivery=completed|output_limit_reached|task_error.
    # TODO: manter falhas de identidade, workspace e ferramentas como infraestrutura/escopo.
    raise NotImplementedError

def verify_requests(candidate, records, session_id=None) -> dict:
    # TODO: guards existentes + max_tokens == OUTPUT_LIMIT em TODAS as chamadas.
    # TODO: conservar stop_reason nativo observado e indicador de limite de saída.
    raise NotImplementedError
```

O observador registra `body.delta.stop_reason` nas respostas Anthropic e mantém os bytes entregues e o cap de metadados existentes. `finish=length`, `rawFinish=max_tokens` ou stop_reason nativo max_tokens produz `output_limit_reached`, mesmo com idle succeeded. Esse trial não vira completed, infra_error ou incorreta, e não recebe nota de competência. Uma violação real de fonte, identidade ou transporte ainda pode ter seu status próprio, com o diagnóstico de limite conservado como campo adicional. Somente completed chega ao grader original.

O resultado e o relatório mostram esse diagnóstico separado de timeout, erro de tarefa e infraestrutura. As medianas e pares seguem a regra herdada de delivered/approved explicitada no relatório. Os números desta configuração128000 não se misturam às rodadas históricas32768.

### Proveniência e integridade

Antes de copiar, conferir hashes do baseline contra o freeze R2. O novo freeze registra o caminho e hash desse freeze, hashes dos arquivos herdados, hashes das fontes novas e a origem dos testes adaptados. `cases.py` e `test_cases.py` precisam coincidir byte a byte; qualquer delta bloqueia a validação. O README registra a origem do observador e de qualquer teste que venha do pacote ativo, fora do frozen-source.

Os guards atuais de código, README, catálogo e fixture por trial permanecem. O wrapper está no mesmo diretório e entra no glob `.py` do manifesto. Cada envelope externo compara inventário/hashes do pacote novo, baseline, catálogo e executável OpenCode no início e no fim da fase, incluindo adições e remoções. Isso fecha a lacuna depois do último trial. O envelope finaliza em finally, e uma mudança bloqueia gate ou conclusão.

Um inventário separado de fontes e resultados antigos antes/depois prova sua preservação. Nenhuma execução importa código do baseline; só a cópia nova executa. O banco original continua SQLite mode=ro. Cada fase conserva o orçamento21600s. A medida wall_s do trial continua excluindo preparação, auditoria, exportação e guards externos.

### Validação offline

`test_cases.py` é o único teste histórico copiado integralmente. Dos testes de matrix/runtime, adaptar apenas agenda, inventário congelado, isolamento, key read-only, identidade, ferramentas, uso desconhecido e redaction. Excluir os pressupostos de sete candidatos,210 trials, Fast, OAuth, DeepSeek, Google e métricas históricas específicas. `test_observer.mjs` será novo ou terá sua origem fora do frozen-source registrada explicitamente.

Provas propostas, todas sem modelos, rede ou Docker:

- Agenda150,30 por esforço, cinco candidatos por bloco e seis ocorrências por posição; smoke5; seed reprodutível.
- Variantes explícitas e cap128000 na config, freeze e requests. Um cap errado ou ausente em qualquer chamada reprova.
- Filho sintético confirma `stat.S_ISREG(fstat(1).st_mode)` e escreve uma carga grande conhecida. O arquivo sanitizado tem todos os bytes e o hash esperado.
- Export JSON inválido, exit não-zero e timeout deixam stdout e metadata preservados; segredos simulados desaparecem e os demais bytes coincidem.
- Sessão idle succeeded com length/max_tokens e zero texto resulta em output_limit_reached com uso/fins conservados.
- Stream Anthropic sintético entrega os mesmos bytes e guarda max_tokens/stop_reason sem prompt, header ou credencial.
- Smoke4/5 ou parâmetros errados iniciam zero trials piloto. Um smoke antigo externo não é entrada aceita.
- Orçamento esgotado deixa not_run visível e exit não-zero; alteração após o último trial torna o envelope falho.
- Relatório usa os candidatos do freeze e exclui limites de saída das incorretas e dos pares aprovados.

## Synthesis decision

Este documento é o candidato A, não a síntese. Sua base é o core congelado; o wrapper acrescenta a política de campanha sem mudar o dono do scheduler, grader ou loop. O ponto para comparar com outra direção é preservar o CLI existente versus transformar a execução inteira em uma API interna.

## Tradeoffs accepted

- Aceitamos copiar o core em troca de isolamento verificável do experimento antigo. Não extraímos uma biblioteca compartilhada nesta rodada.
- Aceitamos manter o CLI de fase em troca de alterações pequenas no executor. O caminho público documentado de campanha passa pelo wrapper e seu smoke.
- Aceitamos hashing antes/depois das fases em troca da prova após o último trial, fora da medida de tempo da tarefa.
- Aceitamos que seis horas deixem o piloto incompleto. Os 150 timeouts somam até45000s; o executor registra a incompletude e sai não-zero sem mudar o protocolo.
- Aceitamos que o request observado prove apenas parâmetros encaminhados. Ele não atesta o modelo servido a montante ou o raciocínio realizado.

## Alternatives considered

Um wrapper com loop próprio sobre `run_trial` perdeu porque duplica agenda, budget, parada e relatório. Expõe ao operador duas políticas de execução e ao próximo agente dois exemplos para copiar.

Uma fachada que monkeypatche `runtime.CANDIDATES` perdeu porque coloca no caller a responsabilidade de sincronizar configuração, freeze e relatório. A tupla canônica local esconde essa decisão com menos interface.

Uma API única `run_phase(spec)` esconderia mais detalhes do CLI e é uma alternativa estrutural válida. Nesta direção A, a mudança menor conserva a execução comprovada e concentra as novas decisões no wrapper e nas fronteiras de export/request/session.

## Open questions and risks

- O smoke novo encaminha exatamente128000 em todas as chamadas de cada esforço, ou o provider reduz o cap?
- A descoberta e o smoke aceitam os cinco esforços explicitamente cadastrados?
- A exportação real do OpenCode fica íntegra com stdout regular? A prova sintética confirma o descritor do executor; o smoke precisa confirmar o binário.
- O orçamento21600s permite150 conclusões? Se não, o relatório e o exit precisam mostrar a incompletude.

Essas perguntas são verificações da implementação e do smoke autorizado. Não exigem ampliar o escopo nem repetir inferências automaticamente.

## Next implementation step

Verificar o baseline e copiar `cases.py` e `test_cases.py` intactos; então preencher a tupla Haiku e provar a captura regular/diagnóstico de limite offline antes do wrapper.

## Triagem dos red flags

Há um único scheduler, loop, grader e registro de candidatos. Os módulos mantêm o conhecimento que já possuíam. O wrapper esconde smoke, preservação e envelopes, em vez de expor ao caller a sequência de trials. Cada artefato tem um escritor. Não introduz spec, loader ou protocolo de autorização adicional. A coexistência do CLI de fase é um tradeoff declarado da direção A, não uma segunda implementação da campanha.

Somente desenho. Nenhum código final, modelo, rede ou Docker foi executado para produzi-lo.
