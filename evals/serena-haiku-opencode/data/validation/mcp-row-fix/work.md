# MCP row bug fix

- [x] 1. Reproduce it yourself on the matching surface. Preflight real do usuário reproduzido em full-2; root não pode iniciar servidor local no sandbox. Resposta exata não foi capturada.
- [x] 2. Binary-search the cause. Fonte primária confirma configuração legada com campos nativos incompatíveis; full-2 perdeu sua resposta, portanto não se atribui formato concreto a essa falha.
- [x] 3. Plan the fix. Duas alternativas julgadas; ownership no runtime, publicação no runner e um único proprietário de código.
- [ ] 4. Verify on the same surface. Contratos locais, 44 Python e 7 Node passaram; P2 da revisão corrigido e reproduzido em vermelho/verde. Serena/LSP real passou para os dois papéis. Integração OpenCode completa exige Terminal: socket Docker bloqueado no sandbox, zero inferência. Não marcar esta etapa completa antes do preflight real.
- [x] 5. Stage the commits. skip: workspace sem Git; snapshots vermelho/verde locais.
- [x] 6. Run Opening a PR. skip: entrega local sem Git/PR pedido.

Throughput checkpoint: root preserva full-1/full-2 e escreve docs/receipts; investigador readonly confere schema/cold states; um writer corrige telemetria e somente transições comprovadas; root valida e entrega comando sem inferência. Raw config/auth não entram nos recibos.
