# Aplicação da política do projeto P

A avaliação resulta em **6 pedidos permitidos e 10 negados**. As fontes são `politica.md` e `pedidos.md`, preservados sem alterações. Cada pedido foi avaliado isoladamente às **12:00:00 UTC de 10/10/2026**, conforme a política; a data atual não altera essa referência.

## Critérios e evidências

A política permite leitura a usuários ativos do próprio projeto, inclusive de recursos bloqueados. Escrita exige papel editor ou admin e recurso desbloqueado; administradores também estão sujeitos ao bloqueio. Exportação exige papel admin e aprovação do titular ainda válida. A aprovação já está expirada no instante exato do vencimento, e sua ausência equivale a uma negativa.

Usuários de outro projeto são negados, salvo a exceção E1: leitura emergencial por usuário ativo do papel suporte com chamado de emergência aberto associado ao recurso. Essa exceção cobre somente leitura. A regra “Suspensão bloqueia qualquer ação, inclusive acesso emergencial” prevalece mesmo quando existe chamado aberto.

## Pedidos negados

| ID | Decisão e evidência |
| --- | --- |
| A02 | O recurso está bloqueado. O papel editor atende ao requisito de papel, mas a política exige também recurso desbloqueado para escrita. |
| A03 | O recurso está bloqueado. A política declara expressamente: “Administrador não ignora bloqueio de escrita.” |
| A04 | A aprovação vence às 12:00:00 UTC de 10/10/2026, exatamente no instante avaliado. “No instante exato do vencimento, a aprovação já expirou”; portanto, falta aprovação ainda válida para exportar. |
| A07 | O usuário está suspenso. A suspensão bloqueia inclusive o acesso emergencial, apesar do papel suporte e do chamado aberto associado ao recurso. |
| A08 | O pedido é de exportação por suporte do projeto X. E1 só autoriza leitura; não afasta a restrição entre projetos para exportar. Além disso, suporte não é admin e não há aprovação informada, cuja ausência equivale a não. |
| A11 | O usuário pertence ao projeto X. O papel admin não concede acesso a outro projeto; E1 não se aplica, pois o usuário não é suporte e não há chamado emergencial. |
| A12 | Falta aprovação do titular. Embora o usuário seja admin ativo do projeto P, exportação exige essa aprovação ainda válida; “Ausência de aprovação equivale a não.” |
| A13 | O chamado emergencial está encerrado. E1 exige chamado aberto associado ao recurso; sem essa condição, aplica-se a negativa para usuários de outro projeto. |
| A14 | O usuário é editor, mas exportação exige admin. A aprovação que vence amanhã não substitui o requisito de papel. |
| A16 | O usuário é leitor, mas escrita exige editor ou admin. O recurso desbloqueado não basta; “Uma aprovação de exportação não concede escrita”. |

## Pedidos permitidos e casos de fronteira

| ID | Decisão e evidência |
| --- | --- |
| A01 | Usuário ativo do projeto P pode ler o recurso desbloqueado do próprio projeto. |
| A05 | Admin ativo do projeto P com aprovação que vence às 12:00:01 UTC de 10/10/2026. No instante avaliado, a aprovação ainda é válida por mais um segundo, ao contrário de A04. |
| A06 | Aplicação de E1: usuário ativo, papel suporte e chamado emergencial aberto associado ao recurso. A leitura é permitida mesmo pertencendo ao projeto X. |
| A09 | Usuário ativo do projeto P pode ler o recurso bloqueado: “Leitura de recurso bloqueado continua permitida.” O bloqueio impede escrita, não leitura. |
| A10 | Editor ativo do projeto P solicita escrita em recurso desbloqueado, atendendo aos requisitos. |
| A15 | Suporte ativo do projeto P pode realizar leitura comum do próprio projeto. A regra geral não exige chamado emergencial para essa leitura. |

## Ressalvas e conferência

Nenhuma aprovação ausente foi presumida. Aprovações de exportação não concedem escrita nem acesso a outro projeto. As decisões valem apenas para o instante e os dados apresentados, sem extrapolação para outros horários.

A análise foi dividida entre exatamente dois subagentes diretos, sem descendentes: um avaliou A01–A08, e o outro A09–A16 e as fronteiras da política. Ambos retornaram suas análises por mensagem; somente o agente principal escreveu os arquivos finais após a conclusão de ambos. A conferência final verificou os 16 IDs, sua classificação única e a ordem crescente nas duas listas de `answer.json`, que contém exclusivamente as chaves `permitidos` e `negados`.
