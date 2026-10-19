# Conferência final das correções do runner

Snapshot conferido em 2026-10-12 21:21:33 UTC. Revisão READONLY: nenhum arquivo de implementação ou teste foi alterado. As escritas persistentes do revisor são este relatório, os resultados em `final-fix-reproductions.json` e o censo rerodável `final-fix-census.py`. Foram lidos os sete arquivos solicitados, os contratos de isolamento usados por eles, README/DESIGN e o extrato atual do binário. Sem inferência, MCP fullprobe, rodadas históricas ou Git nesta revisão.

## Veredito

**Reprovado para fechar os três P2 de `final-review.md`: dois permanecem parcialmente corrigidos.** A captura de `TimeoutExpired` nas fases da CLI foi corrigida e passou nas verificações unitárias de falha. O gate nativo completo permanece pendente/bloqueado por Docker no ambiente; esta revisão não declara passagem de catálogo/conexão/terminal/cancelamento dentro do OpenCode.

| P2 original | Estado neste snapshot | Evidência atual |
|---|---|---|
| Tempos parciais em falhas | Parcial | `wall_s` é salvo em `finally`, e agregados expõem contagem de ausências; `export_s` e `grading_s` continuam `null` quando a etapa iniciada falha. |
| Admissão por conexão MCP e superfície exata | Parcial | O schema `data` e o estado Serena conectado são exigidos; cardinalidade/IDs da superfície nativa continuam sem validação. Linha malformada no status escapa como `AttributeError`. |
| Timeout de instalação/Docker e fechamento estruturado | Corrigido no fluxo verificado | Preparação, preflight e loop/finalização capturam `subprocess.TimeoutExpired`; falha repetida do freeze ainda conserva relatório, summary e phase. A suíte persistente ainda não cobre esse fluxo. |

## Achados abertos

### P2 — Exportação e grading ainda perdem tempo iniciado

`bench.py:190-192` e `bench.py:216-219` gravam a duração somente depois do retorno de `export_session`/`cases.grade`. O `finally` de `run_trial` recupera somente preparação e total; a exceção conserva `result.json`, mas deixa a duração da etapa iniciada ausente. Os novos agregados distinguem ausência de observação, porém não recuperam o custo perdido. Uma reprodução unitária do próprio `run_trial`, com provider/instalação substituídos e `ValueError` forçado em cada fronteira, produziu:

```json
[
  {"stage":"export","status":"infra_error","export_s":null,"grading_s":null,"result_json_exists":true},
  {"stage":"grading","status":"infra_error","grading_s":null,"result_json_exists":true}
]
```

A etapa principal passou a ter `finally` e flag `primary_timing_incomplete`; isso corrige boot/session/invoke falhos, sem provar exportação/grading. **Correção restante:** `finally` em cada etapa iniciada; teste de boot, exportação, grading e interrupção que leia o `result.json` real e preserve `null` para etapas não iniciadas. `test_bench.py` não contém esses testes no snapshot revisado.

### P2 — Superfície nativa continua aceitando duplicatas e status malformado pode quebrar o preflight

`runtime.py:130-141` procura igualdade de conjuntos de nomes. Não exige comprimento exato, IDs presentes/únicos nem um nome por ferramenta. Uma linha com as quatro ferramentas nativas de exploração mais uma cópia da primeira (mesmo nome e ID) foi aceita por `runtime.surface`: **cinco ferramentas observadas para quatro permitidas**. `surface.js:55` também põe os IDs permitidos num conjunto, sem recusar multiplicidade. A deduplicação do catálogo stdio em `mcp_bridge.py` não substitui o contrato da superfície OpenCode.

`validate_mcp_status` agora exige envelope `data` como lista, exatamente um servidor `serena` e `status.status == 'connected'`. Entretanto, `{'data':[null]}` levanta `AttributeError`, porque `runtime.py:436` chama `.get` antes de validar o tipo da linha; essa exceção não pertence às capturadas por `bench.preflight`. O campo `integrationID`, presente no schema extraído do binário, não é validado. O comando esperado permanece conferido pela igualdade do documento efetivo com a configuração privada em `audit`; não há lacuna de comparação de comando nessa etapa.

**Correção restante:** validar a forma da linha como erro de infraestrutura estruturado, conservar a resposta nativa e uma asserção explícita; validar nomes por cardinalidade/multiconjunto e IDs únicos/presentes, com testes de duplicata e linha malformada. Exigir a identidade da integração conforme o schema real, sem inventar uma associação que o binário não exponha.

## Correções e invariantes conferidas

- `TimeoutExpired` consta em preparação (`bench.py:392`), preflight (`141`), trial (`225`), loop (`438`) e rechecagem final (`444`). A injeção dessa exceção gerou `preparation-blocked.json` com blocked/exit 1; `preflight.json` bloqueado; e falha no loop e no freeze final ainda gerou `integrity-error.json`, `summary.json`, `report.md` e `phase.json` com `integrity_failure`, zero tentativas e exit 1. São verificações unitárias atuais; não houve executável real lento nem Docker nesta revisão.
- `implementation-binary-surface.json` registra o schema `mcp.list` com `{name,status,integrationID}` e registro de MCP com `name` cru e `options.namespace` derivado do servidor. `exposedToolName` compõe `serena_<nome>` para a namespace Serena; o plugin registra nome completo, nome cru, namespace e ID, e seu hook compara o ID do evento aos IDs registrados. Isso é coerente para os nomes fixos desta instalação. A multiplicidade continua aberta conforme o achado acima.
- O plugin remove o terminal pré-existente e registra seu próprio terminal. `executeTerminal` usa Docker exec; exec e kill recebem HOME privado e DOCKER_HOST. `prepare` transporta o endpoint local Unix obtido antes de trocar o HOME. O teste Node exercita a substituição do terminal e recusa execução desconhecida/preabortada. A passagem real pelo daemon e a morte de descendentes seguem pendentes no gate nativo.
- `prepare` recria `serena-home`/`serena-project` depois da importação de auth e apaga observações/surface/MCP/terminal antes da execução temporizada. O trial copia os logs temporizados e calcula o summary MCP antes da exportação. `reconcile_mcp` compara multiconjuntos de chamadas Serena ao export nativo e rejeita pendências em entrega completa. O teste Python cobre divergência e pendência. Manual não conta como uso útil.
- `infra_error`/`scope_violation` encerram a campanha no primeiro trial assim classificado; não há retry do harness. O Client fecha o processo em falha de initialize e Client/local_server encerram o grupo. Não foi feita prova dinâmica de processos descendentes ou de ausência de vazamento sob timeout real; esses pontos não são certificados pelos testes de fonte/mocks.

## Testes executados

`python3 -B -m unittest test_bench -v`: **20/20 aprovados**. `~/.local/bin/node --test test_surface.mjs`: **4/4 aprovados**. Também foram executadas as reproduções unitárias descritas acima sobre as funções atuais. Nenhuma chamou provider ou Serena real. A suíte persistente confirma regressões cobertas, mas sua aprovação não fecha as lacunas de timing/cardinalidade nem substitui o preflight nativo.

## Complemento de comentários e suppressões

Tokenização e AST dos arquivos Python próprios do pacote: zero comentários e zero docstrings. Busca nos `.py`, `.js` e `.mjs` próprios: zero `noqa`, `type: ignore`, suppressões TypeScript/ESLint, `nosec`, `pragma: no cover` e `pyright: ignore`. O JavaScript de produção e testes foi conferido integralmente. Nenhuma exclusão, restauração, comentário de constraint ou suppression a tratar. `vendor/`, `dependencies/` e snapshots não foram incluídos nesse julgamento. Não foram criados testes espelho nem mudanças de estilo fora do escopo.

Doc impact: pending — README/DESIGN descrevem duração de etapas e gate nativo; o primeiro contrato ainda não vale nas falhas de exportação/grading, e a prova nativa final deve ser anexada antes da declaração de validação integral.

## Hashes do snapshot revisado

| Arquivo | Linhas | SHA-256 |
|---|---:|---|
| `bench.py` | 456 | `a0d7470bc961f310988093978a17ad78b6e26453e1fcb99c34487d711cade3e6` |
| `runtime.py` | 446 | `42f3889500fffe9e2542300a1eb57a3549361f00382c0f65ed9cabe7becd7655` |
| `installation.py` | 82 | `f7f98e1d902a59eafcd83da0ff690219a5d42417fcda7bf8978799207ead7e0a` |
| `mcp_bridge.py` | 212 | `7290b18079335a6f6e18f66c3b11842cf862476ead45ecd789257700230f0b1f` |
| `surface.js` | 80 | `661498c97a2833609db77c08e49c38898812d82652ad3848e21fbfcec743fbbe` |
| `test_bench.py` | 225 | `c86c8596183fd7fbc6229fcb94347cc2abe7a13522236d1a99b377c558342643` |
| `test_surface.mjs` | 53 | `7a9ee5c281345c7e7e8a0b8ee40bef0cc87ea36f2a60f02ceb3a907d9d5acb64` |
| `README.md` | 68 | `0b118d62eb740e044ce69206e8cc8c5b6f18ba4582fffff16dd27f4c16d69854` |
| `DESIGN.md` | 25 | `16badb6f17493a9c01b09ab2084b4bd73afacb255dd4d77067b10c87e706072e` |
| `domain.py` | 72 | `d4dc2c13ef878480f54301798dc265bc5a89b051d74d74e80f671d0a016c66b0` |
| `cases.py` | 55 | `27241ac9340b9aabc442532665a506189436c350b1261996d68b52fc07b12b21` |
| `observer.js` | 207 | `a9be79b410bc789d4e13013688ec07f484ee5415f82c149f0cd064794e98e622` |
| `models.json` | 1 | `f6a22feaaf4916289ead67712a27b2ba7ccdb38f6dc23ddfae11158b28a1a761` |
| `provenance.json` | 49 | `b50db99a87939eee3903640b8b502c79453f0e881d5f3a8bc3fe45d167a34192` |
| `validation/implementation-binary-surface.json` | 8 | `2e4166fb18d80824c572b62697f6f4d6570980a6d30eae83fd6e886d261abb75` |

Este veredito vale para os hashes acima. Correções posteriores precisam de nova conferência; a existência deste relatório não prova que o snapshot permaneceu estável após sua escrita. Root comunicou que corrigirá as lacunas e executará o preflight independente em `validation/native-root-final-1`; essas futuras correções/provas não foram examinadas nem antecipadas aqui. Este relatório deve permanecer como evidência histórica do snapshot revisado. O censo pode ser rerodado com `python3 -B validation/final-fix-census.py`; ele imprime os hashes e contagens do código que estiver presente no momento da execução.
