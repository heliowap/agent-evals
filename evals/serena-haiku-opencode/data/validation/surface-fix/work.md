# Bug fix do catálogo OpenCode

- [x] 1. Reproduce it yourself on the matching surface via the control skill.
- [x] 2. Binary-search the cause. Form the candidate hypotheses, then rule them out until one survives.
- [x] 3. Plan the fix. If it crosses a function boundary, architect first. Delegate implementation to a subagent.
- [x] 4. Verify on the same surface. Regressões, configurações privadas e MCP/LSP real aprovados; preflight nativo completo pendente Terminal, bloqueado aqui.
- [ ] 5. Stage the commits so the failing repro lands before the fix in git history. skip: workspace sem Git; salvar prova antes/depois.
- [ ] 6. Run Opening a PR. skip: entrega local sem Git ou pedido de PR.

Contrato de dados: ferramentas permitidas por papel/condição; catálogo observado com nome, namespace e ID; preflight sem inferência.

Throughput checkpoint: preservar full-1, root reproduz e identifica causa, um delegado altera código/testes, root atualiza docs e valida CLI. Estado compartilhado: produção sob único writer; snapshots em diretórios próprios. Preflight com Docker/socket local indisponível no sandbox; tentar discovery sem Docker no braço explorador e declarar o limite observado.

## Architect e arena

- [x] Ground. Código do binário confirma transforms ordenadas, browser builtin post e list inexistente na superfície observada.
- [x] Sketch. Duas alternativas completas, arquivos isolados, sem editar produção.
- [x] Agree. Seleção técnica sem checkpoint humano.
- [x] Implement. Um proprietário delegado.
- [x] Scrap. n/a: provas locais sustentam desenho; integração nativa ainda pendente.

Arena: Frame, Fan out, Cross-judge, Pick, Graft, Verify. Régua do juiz: correção dos dois blockers, tools Serena efetivamente disponíveis sem execute amplo, preservação do gate/isolamento, menor superfície API, provas reais sem inferência. Limite: modelos Claude/Grok pedidos pelo skill não estão disponíveis; usar os agentes GPT acessíveis, sem alegar diversidade de famílias.

## Entrega

32 Python, 7 Node, contratos e MCP/LSP real passaram. Revisão encontrou um P2 de fixture externa ao freeze, corrigido e reproduzido em snapshot isolado. full-1 e 14691 arquivos históricos intactos; três arquivos de configuração do operador intactos. Agenda/enunciados/fixtures/reps/limites preservados. Zero inferência. Native Docker/OpenCode ainda exige preflight no Terminal; final-proof.json registra a limitação.
