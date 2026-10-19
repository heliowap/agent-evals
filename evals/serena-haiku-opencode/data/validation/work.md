# Haiku com Serena no OpenCode

## Trabalho autorizado

Preparar um eval de pesquisa no código e implementação para Haiku 5.5 medium e high. Comparar ferramentas nativas com ferramentas nativas mais Serena. Não modificar evidências anteriores nem iniciar inferência nesta preparação.

## Etapas

- [x] 1. `how` over the affected subsystem.
- [x] 2. `architect` for parallel design exploration.
- [x] 3. Blocking first steps. Contratos, instalação e MCP/LSP real verificados; gate Docker/OpenCode permanece bloqueado neste sandbox e obrigatório antes dos trials.
- [x] 3. Independent workstreams. Desenhos em arquivos próprios; código sob um proprietário, seguido por correções finais do root.
- [x] 3. Shared mutable state. HOME, XDG, sessão, projeto, memórias e logs separados por trial. Execuções de modelos sequenciais.
- [x] 3. Smallest safe decomposition. Runner com um proprietário e revisão independente dos artefatos.
- [x] 4. Delegate code-writing to a subagent.
- [x] 5. Verify on the matching surface. Contratos, regressões de falha, testes Node e MCP/LSP real executados. Integração Docker/OpenCode declarada pendente e protegida pelo preflight.
- [x] 6. Rebase into small, ordered commits. n/a: workspace sem repositório Git; arquivos locais e provas.
- [x] 7. If the design is contested, `interrogate` before shipping. n/a: juiz selecionou desenho; revisões de implementação geraram correções e provas, sem disputa arquitetural.
- [x] 8. Run Opening a PR. n/a: entrega local, sem pedido de PR ou repositório Git.

Architect segue Ground, Sketch, Agree, Implement, Scrap. Agree não requer checkpoint humano neste pedido. Arena segue Frame, Fan out, Cross-judge, Pick, Graft, Verify.

## Régua dos desenhos

1. Comprovar identidade, esforço, isolamento e uso efetivo do MCP.
2. Comparação pareada com mesmos casos, limites e corretor.
3. Reutilizar contratos corrigidos e preservar evidências anteriores.
4. Falhas de infraestrutura distintas de reprovação funcional.
5. CLI pequena, executável e verificável sem inferência.

## Estado

Grounding, desenhos, implementação e revisões concluídos. Juiz pontuou A e B em 8/10 e confirmou base B com CLI direta de A. Root corrigiu os achados finais de tempo parcial e validação da superfície com regressões reproduzidas antes e depois. Contratos e provas locais passaram. O gate nativo completo permanece bloqueado pelo socket Docker neste sandbox; o comando entregue exige sua aprovação no Terminal antes de inferência. Evidências finais em `final-proof.json`. Sem chamadas de modelos nesta preparação.
