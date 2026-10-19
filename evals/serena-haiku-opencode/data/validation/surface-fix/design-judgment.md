# Julgamento das propostas

Base escolhida: **B**, incorporando os casos adversariais de A. As propostas convergiram na mesma correção declarativa; não representam arquiteturas distintas. Os revisores herdaram a família disponível: Claude e Grok não estavam disponíveis. Esta revisão não chamou modelos nem alterou produção.

| Critério (0–2) | A | B |
|---|---:|---:|
| Resolve os três bloqueios concretos | 2 | 2 |
| Serena chega diretamente, sem abrir `execute` | 2 | 2 |
| Preserva gate, isolamento e evidências | 2 | 2 |
| Mantém API pequena | 1 | 2 |
| Oferece prova sem inferência | 2 | 2 |
| Total | **9** | **10** |

A torna explícita uma política útil, mas `ToolSpec` e `ToolPolicy` repetiriam propriedades já deriváveis da tabela `TOOLS` e do papel. A própria proposta permite descartá-las. B mantém as funções existentes e concentra a correção em configuração, registro e validação.

O catálogo real não contém `list`; o baseline explorador deve ser `read/glob/grep`. O builtin browser é posterior ao filtro local: `-opencode.browser` deve removê-lo no documento privado, mantendo o gate que rejeita qualquer registro inesperado. O schema MCP aceita `codemode:false` e propaga a opção às ferramentas. Assim, Serena fica disponível diretamente sem mudar a proibição de `execute`.

A interpretação foi conferida contra o fonte embarcado do binário fixado. Em **119874554**, `In(e)` sanitiza o nome e normaliza pontos do namespace para underscores; o editor usa esse resultado como ID. Para os nomes fixos desta avaliação, ID e nome exposto são `serena_nome`. `Tool.snapshot`, em **119884203**, filtra a ação **`options.permission ?? ID`** antes de separar ferramentas diretas por `codemode === false`. A ação interna MCP `wa(server,name)`, em **120148354**, coincide com esse ID. Portanto o recibo deve guardar ID, nome exposto, opção CodeMode e ação efetiva; comparar apenas nomes seria insuficiente. O guard de execução permanece baseado na identidade concreta registrada.

Grafts de A: regressões que rejeitem permissão efetivamente negada, CodeMode ausente/true, browser registrado depois do filtro e terminal host preservado. A aceitação deve provar o conjunto exato, IDs e nomes únicos, permissões globais e do agente, configuração privada e MCP conectado. Preservar `full-1` integralmente e produzir saída nova.

O filtro tardio foi rejeitado com fundamento: não há hook final comprovado, e timer/reinscrição introduziria ordem temporal como requisito oculto. Liberar `execute` alteraria o tratamento; remover todos os builtins acrescentaria dependências desnecessárias.

Pendências de prova: corrigir o replay para recompor transforms na ordem real, testar as quatro combinações de papel/braço sem inferência e executar o preflight nativo. Catálogo sintético ou fonte embarcado isoladamente não certificam o runtime completo.
