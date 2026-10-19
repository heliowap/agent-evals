Sol low Fast teve os menores tempos observados e **36/36 patches aprovados pelos testes**. A aprovação completa foi 35/36, devido a uma observação de chamada incompleta.

Foram concluídos os 108 trials: 12 casos, três repetições e três configurações, com o Python monetário corrigido. Nenhum trial pendente ou duplicado; confirmação excluída.

| Configuração | Aprovação completa | Patch aprovado | Chamadas | Mediana dos aprovados | Faixa de sessões fechadas |
|---|---:|---:|---:|---:|---:|
| Sol 6.1 low Fast | 35/36 | 36/36 | 140 | 28,34 s | 14,06 a 39,07 s |
| GLM 5.3 Flash high | 34/36 | 35/36 | 270 | 47,92 s | 6,37 a 234,41 s |
| GLM 5.3 Flash max | 31/36 | 33/36 | 352 | 194,06 s | 15,10 a 1.087,83 s |

As medianas das sessões fechadas, incluindo rejeições, foram 28,34 s, 47,92 s e 232,35 s, com 36, 36 e 35 sessões. O timeout de max durou 1.200,21 s. O cronômetro exclui preparação e avaliação privada.

Nos pares aprovados do mesmo caso e repetição, Sol foi mais rápido em 28/33 contra high e 29/30 contra max. As razões medianas GLM/Sol foram 1,78 e 6,49. São dados descritivos, sem perfil de gargalo ou controle da carga dos providers.

| Caso | Sol low Fast | GLM high | GLM max |
|---|---:|---:|---:|
| Importação atômica | 3/3 | 3/3 | 2/3 |
| Escopo de documentos | 3/3 | 3/3 | 3/3 |
| Consolidação do exportador | 3/3 | 2/3 | 3/3 |
| Limpeza do gerador | 2/3 | 3/3 | 3/3 |
| Python monetário corrigido | 3/3 | 3/3 | 2/3 |
| Transferência e commit | 3/3 | 3/3 | 2/3 |
| Arquivamento de documento | 3/3 | 3/3 | 3/3 |
| Paginação por cursor | 3/3 | 3/3 | 3/3 |
| Fluxo de eventos | 3/3 | 3/3 | 2/3 |
| Pagamento idempotente | 3/3 | 3/3 | 3/3 |
| Consolidação monetária TypeScript | 3/3 | 3/3 | 3/3 |
| PATCH de perfil | 3/3 | 2/3 | 2/3 |

Sol teve [uma rejeição de observabilidade](../results/sol-low-glm-flash-rest/trials/trial-0023/result.json), com patch correto, saída normal e uma chamada websocket sem status ou evento final. Isso não comprova falha do provider.

GLM high deduplicou tags no [perfil](../results/sol-low-glm-flash-rest/trials/trial-0004/result.json). O teste exige rejeitar duplicatas; o contrato não explicita essa rejeição. A falha tem ambiguidade contratual. Sua outra rejeição foi [ECONNRESET com patch correto](../results/sol-low-glm-flash-rest/trials/trial-0011/result.json).

GLM max deixou patches vazios no [monetário](../results/money-sol-low-glm-flash/screening/trials/trial-0005/result.json), na [transferência](../results/sol-low-glm-flash-rest/trials/trial-0082/result.json) e na [importação interrompida pelo limite](../results/sol-low-glm-flash-rest/trials/trial-0046/result.json). Também teve [timeout upstream](../results/sol-low-glm-flash-rest/trials/trial-0006/result.json) e [ECONNRESET](../results/sol-low-glm-flash-rest/trials/trial-0037/result.json), ambos com patch correto.

Foram 762 chamadas comparativas e 18 nos seis gates aprovados. Fontes, solicitações, grades e sessões conferidas; 1.250 arquivos inalterados. Sol solicitou priority em 140 chamadas; 139 finais reportaram default. O tier servido permanece inconclusivo.

Os projetos têm 12 a 34 linhas iniciais em src/. Repetições não são novos problemas; novidade perante treinamento não foi auditada. Os testes não garantem ausência de bugs ou brechas.

[Dados, verificações e hashes](sol-low-glm-flash-final-analysis.json).
