# Revisão independente do runner Haiku × Serena

Snapshot lido em 2026-10-12T21:15:03.562239+00:00. Revisão READONLY da implementação e dos contratos; a única escrita do revisor é este relatório. A implementação recebeu correções durante a revisão. Este resultado se aplica aos hashes abaixo; alterações posteriores precisam de conferência final pelo proprietário. Não houve inferência nem execução de patches de rodadas antigas.

## Achados abertos

### P2 — Tempos das etapas desaparecem quando a operação falha

`bench.py:160` inicializa os tempos como ausentes; `bench.py:178` só recebe o tempo principal quando `invoke` retorna. O mesmo padrão aparece em exportação e grading. Falha/interrupt durante boot, criação da sessão, execução, exportação ou grader conserva o status e o total do trial, mas perde o tempo da etapa já consumida. `detail` ainda soma etapas ausentes como zero. Isso impede comparar o custo operacional de todos os status e subestima os totais por etapa justamente nas falhas. **Correção:** guardar início/fim de cada etapa em `finally`, registrar tempo principal mesmo quando `invoke` levanta exceção, e conservar indisponibilidade em agregados quando a etapa realmente não foi iniciada. Testar boot falho, exportação falha e interrupção sem inferência.

### P2 — O preflight coleta `mcp.list`, mas não verifica a conexão nativa

`runtime.py:150` chama a API real e devolve seu resultado; não exige exatamente o servidor `serena` conectado, nem rejeita um estado de erro. `runtime.py:134` verifica nomes por conjunto, sem validar cardinalidade/IDs duplicados. Uma prova stdio externa e um registro do catálogo não certificam que o OpenCode mantém a conexão pronta no momento da admissão. **Correção:** validar o schema e estado real de `mcp.list` no binário 2.0.26, exigir o servidor e comando privados esperados, recusar erro/desconexão e IDs/nomes repetidos. Conservar a resposta bruta e uma asserção explícita no preflight. A prova nativa ainda precisa de execução em Terminal.

### P2 — Timeouts de instalação/Docker podem escapar do fechamento estruturado

`installation.py:48` usa `subprocess.run(timeout=30)` e `vendor/isolation.py:34` usa timeouts próprios. `subprocess.TimeoutExpired` deriva de `SubprocessError`, não das exceções atualmente capturadas em preparação/preflight/finalização (`bench.py:392`). Um timeout de fingerprint ou Docker pode terminar o comando sem `preparation-blocked.json`, `preflight.json` ou `phase.json`; no último freeze pode impedir também o relatório final. **Correção:** traduzir esses timeouts em falha de infraestrutura na fronteira e garantir a gravação final independentemente de nova falha do verificador. Testar um executável de prova que excede o prazo, sem usar provedores.

## Invariantes conferidas diretamente

- `domain.py` contém somente medium/high × native/serena. `schedule` produz 120 IDs únicos em 30 blocos pareados; cada configuração contém 15 explorações e 15 implementações. A rotação equilibra as quatro posições. Smoke contém oito sessões separadas.
- `main` chama preflight antes de admitir trials; nenhuma aprovação funcional do smoke condiciona full. O loop conserva reprovações funcionais, output limit e task error; infraestrutura/escopo interrompem a campanha. Não há retry do harness.
- Limites iguais por papel: exploração 300 s/25 passos; implementação 1200 s/60 requests. O timer começa antes do spawn OpenCode e há rechecagem de limites após a saída. O freeze verifica inventário e bytes de fontes/documentos/testes, catálogo, instalação e imagem antes dos trials e no fechamento após o último.
- HOME/XDG, sessão, fixture, configuração Serena e metadados são privados por trial. A preparação recria metadados depois de auth import; a tarefa não executa audit. A captura temporizada é conservada antes de exportar; a superfície usada para validar o trial é a temporizada. A exportação nativa continua preservada com receipt/hash.
- A reconciliação acrescentada exige o multiconjunto de nomes Serena exportados igual às requisições do bridge e ausência de calls pendentes nas entregas concluídas. Não exige uso útil para aprovar: manual não conta como uso e trials sem uso continuam no denominador.
- O terminal agora remove qualquer terminal anterior e registra seu próprio executor Docker. Endpoint Unix é transportado para o HOME privado. O grader reaplica fontes permitidas numa cópia limpa, mantém os checks públicos originais, usa outro container sem rede/read-only e mantém os privados fora do projeto do agente. `py-document-scope` testa tenant/proprietário/exclusão, resultados/ordem e parâmetros descritos no enunciado; não encontrei requisito de autorização adicional oculto.
- Inicialização falha do Client agora fecha o processo; Client e servidor local encerram o grupo após o pai sair. Falta a prova dinâmica de processos descendentes sob timeout real. Saídas novas são obrigatórias; `report` recompõe apenas derivados. As fontes históricas foram somente lidas para conferir proveniência.

## Evidência executada e limite da integração

`python3 -B -m unittest test_bench -v`: 17 testes aprovados. Repetição após correções com `-q`: 17 aprovados. `~/.local/bin/node --test test_surface.mjs`: três aprovados nas duas execuções. Os testes são do pacote novo e não fazem inferência.

Li os transcripts completos em `validation/mcp-root-1` e `validation/implementation-mcp-1`: cada papel tem um spawn e um exit; símbolos, corpo e referências reais passaram, e implementação registra as três edições reais. Há zero bridge errors e somente traversal/edição proibida rejeitados de propósito. Essas provas sustentam stdio + LSP Python + permissões; não substituem descoberta/catálogo/execução MCP dentro do OpenCode.

O gate nativo completo permanece sem prova de passagem neste sandbox. A validação no Terminal precisa produzir `preflight.json` passado com zero model calls, oito descobertas configuração/papel, ferramenta identificada por nome e ID no 2.0.26, `mcp.list` conectado, execução do terminal no HOME privado, baseline/reference Docker e teste de cancelamento sem descendentes sobreviventes. Nenhum trial deve ser admitido enquanto o preflight bloquear. Os testes disponíveis não cobrem todos esses fluxos. A conferência final deve rodar novamente depois dos últimos edits e comparar os hashes.

## Complemento Comment Sicko

O complemento cobre `bench.py`, alterações em `runtime.py`/`mcp_bridge.py`/`surface.js` e os novos testes que não estavam no snapshot de `validation/comment-review.md`, além dos arquivos de produção já listados. Tokenização Python + AST encontrou 0 comentários/docstrings; a busca de suppressões encontrou 0 arquivos com marcadores. JavaScript novo foi lido integralmente. Não há comentário para excluir, constraint comment para codificar nem suppression de correção/segurança. Zero exclusões/restaurações/reruns por rejeição/encoding offers; não houve necessidade de sketch. `observer.js` segue byte a byte igual à origem histórica. `vendor/`, `dependencies/` e snapshots em `validation/` permanecem fora do julgamento de comentários.

Doc impact: pending — README/DESIGN descrevem corretamente o gate e os limites de isolamento; falta anexar a prova nativa final e resolver os achados de medição/falha antes de declarar o runner integralmente validado.

## Hashes do snapshot revisado

| Arquivo | Linhas | SHA-256 |
|---|---:|---|
| `README.md` | 68 | `0b118d62eb740e044ce69206e8cc8c5b6f18ba4582fffff16dd27f4c16d69854` |
| `DESIGN.md` | 25 | `16badb6f17493a9c01b09ab2084b4bd73afacb255dd4d77067b10c87e706072e` |
| `bench.py` | 453 | `f281d60cf2f15a60ae708736a7bd5b84fb18055899c41f4db2650c09c523e222` |
| `runtime.py` | 421 | `71a5c6f28dcb7f82097c3b9af994922b89ce84ef5ddafeffec6af3d201f90e04` |
| `domain.py` | 72 | `d4dc2c13ef878480f54301798dc265bc5a89b051d74d74e80f671d0a016c66b0` |
| `cases.py` | 55 | `27241ac9340b9aabc442532665a506189436c350b1261996d68b52fc07b12b21` |
| `installation.py` | 82 | `a187de8f0f3c9ebbf4dfcbae0d81b9dce30e7d93682797d503b8833524aa1e8c` |
| `mcp_bridge.py` | 208 | `893b8bd52cb1000a20814361c97b39e10105923769203f4a02ce6c3fdb516a56` |
| `surface.js` | 72 | `5777cd14f25308cccad416c535e2d60bb99231a9f0eeaef3ae65a68786ed52ab` |
| `observer.js` | 207 | `a9be79b410bc789d4e13013688ec07f484ee5415f82c149f0cd064794e98e622` |
| `test_bench.py` | 205 | `63f13ed527bbfaeaddb32c2f4248b697e69454b908f56b71d708f1b60421cc2c` |
| `test_surface.mjs` | 52 | `ae208fa63bfb181dfe8618de24ed9b6fc6f62cb5c551d531690e9860ae8d2cd3` |
| `provenance.json` | 49 | `b50db99a87939eee3903640b8b502c79453f0e881d5f3a8bc3fe45d167a34192` |
| `models.json` | 1 | `f6a22feaaf4916289ead67712a27b2ba7ccdb38f6dc23ddfae11158b28a1a761` |
| `vendor/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `vendor/capture.py` | 466 | `d67d4057b1e4b5b167b9efee5ecf545657f0eaa27bca26ee9a39c8ef79ca5d99` |
| `vendor/domain.py` | 59 | `9394984dbd31564fae8f102f19449479d00baa5d8bbbc816c5df2518e115a9d2` |
| `vendor/exploration.py` | 400 | `5a32f8cf77552115f9c28bcf6ac543184e3258f0f43fb3e7a71917944a495d02` |
| `vendor/grader.py` | 183 | `86a17dc4bae7378931bc244bc5c8aad4e15635a009afe870371bfa73ccb5c89f` |
| `vendor/isolation.py` | 204 | `3ef4d096d06a08bb8aa7c8dc398576aadeb90fc0059bf03f075758bbed6d88f5` |
| `vendor/tasks_python.py` | 1303 | `6dffe2ab3bc5bcd11b9213df7f97876920c3a57b1f2841d80bbfb8b34d4b8f3b` |

Todos os seis registros `source_sha256`/`copied_sha256` de `provenance.json` foram recalculados e coincidiram. Observer e catálogo foram comparados byte a byte com `exploracao/haiku-5-5` e coincidiram. A instalação congelada é verificável pelo runner; esta revisão não usou a declaração do README como prova da instalação.
