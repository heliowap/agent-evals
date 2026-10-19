# Comparação exploratória de Codex e OpenCode

Recorte do OpenCode de 2026-10-10T13:24:04.783564-03:00. Mesmos 30 casos/repetições em cada condição, 60 correspondências entre os produtos. Ambos usam gpt-6.1-sol xhigh.

| Medida | Condição | Codex | OpenCode | Diferença do OpenCode |
|---|---|---:|---:|---:|
| Tempo médio, s | empty | 41.3 | 32.7 | -21.0% |
| Entrada incluindo cache | empty | 1840974.0 | 771732.0 | -58.1% |
| Saída incluindo raciocínio | empty | 31357.0 | 23187.0 | -26.1% |
| Tokens totais | empty | 1872331.0 | 794919.0 | -57.5% |
| Tempo médio, s | deterministic | 47.8 | 42.4 | -11.3% |
| Entrada incluindo cache | deterministic | 1887916.0 | 830025.0 | -56.0% |
| Saída incluindo raciocínio | deterministic | 35856.0 | 32648.0 | -8.9% |
| Tokens totais | deterministic | 1923772.0 | 862673.0 | -55.2% |

A contagem foi normalizada antes da comparação. O Codex inclui cache na entrada e raciocínio na saída. O OpenCode exporta essas parcelas separadamente. O código compilado do executável instalado confirma a transformação; seus trechos e hash estão no JSON da análise. A fonte local consultada é 2.0.22, por isso a checagem adicional usou o executável 2.0.25 da rodada.

No conjunto pareado, OpenCode teve -56.3% tokens totais e -15.8% de duração em relação ao Codex. Foi mais rápido em 47/60 correspondências. Os 60 trials de cada produto passaram nos checks automáticos; a avaliação subjetiva do OpenCode está pendente.

Isso é um achado exploratório destas execuções. Os dois produtos rodaram em momentos diferentes, sem sorteio/intercalação entre produtos. Instruções internas, ferramentas, permissões e integração com o provedor diferem. O desenho isolou o efeito do AGENTS dentro de cada produto, não o efeito causal de trocar Codex por OpenCode.

A duração cobre invocações do agente, com inicialização e ferramentas, mas exclui preparação, auditoria, exportação e correção do eval. Não mede o processo completo do eval nem throughput do modelo. Tokens incluem contexto reenviado e cache; não são tokens únicos nem preço.

Contas e evidência: [cross-runtime-partial-20261010-132404.json](cross-runtime-partial-20261010-132404.json). Resultados brutos e rodada em andamento não foram alterados.
