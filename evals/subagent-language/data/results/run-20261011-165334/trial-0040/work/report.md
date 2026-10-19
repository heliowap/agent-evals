# Aplicação da política aos pedidos

A análise aplica exclusivamente `politica.md` aos 16 pedidos de `pedidos.md`, individualmente, no instante **10/10/2026 às 12:00:00 UTC**. O resultado é de **6 permitidos e 10 negados**. A lista de usuários é considerada válida apenas nesse instante; as decisões não são extrapoladas para outros horários.

## Pedidos permitidos

| ID | Evidência e fundamento |
| --- | --- |
| A01 | Usuário ativo, leitor do projeto P, solicitando leitura. A regra geral permite ler recurso do próprio projeto. |
| A05 | Admin ativo do projeto P, com aprovação de exportação que vence às 12:00:01 UTC de 10/10/2026. No instante avaliado, a aprovação ainda é válida. |
| A06 | Suporte ativo do projeto X, com chamado emergencial aberto associado ao recurso. A exceção E1 autoriza essa leitura mesmo de outro projeto. |
| A09 | Leitor ativo do projeto P. A política permite expressamente a leitura de recurso bloqueado. |
| A10 | Editor ativo do projeto P e recurso desbloqueado: os requisitos de escrita estão satisfeitos. |
| A15 | Suporte ativo do projeto P solicitando leitura de recurso desbloqueado. A regra geral de leitura do próprio projeto basta; não exige chamado emergencial. |

## Pedidos negados

| ID | Evidência e fundamento |
| --- | --- |
| A02 | O recurso está bloqueado. O papel editor satisfaz o requisito de papel, mas a escrita também exige recurso desbloqueado. |
| A03 | O recurso está bloqueado. A política declara que administrador não ignora o bloqueio de escrita. |
| A04 | A aprovação vence em 10/10/2026 às 12:00:00 UTC, exatamente no instante avaliado. Pela política, no instante exato do vencimento ela já expirou; portanto falta aprovação válida para exportar. |
| A07 | O usuário está suspenso. A suspensão bloqueia qualquer ação, inclusive acesso emergencial, e E1 exige usuário ativo. O chamado aberto não supera essa restrição. |
| A08 | O usuário é do projeto X e pede exportação. E1 cobre somente leitura, o papel suporte não autoriza exportação e nenhuma aprovação do titular foi informada. Há, portanto, impedimentos de projeto, papel e aprovação. |
| A11 | O usuário é do projeto X. A regra geral nega acesso de outro projeto; ser admin não altera essa regra. E1 não se aplica, pois o usuário não é suporte e não há chamado emergencial. |
| A12 | Não há aprovação do titular. Exportação exige aprovação ainda válida, e a política equipara ausência de aprovação a não. |
| A13 | O usuário é do projeto X e o chamado emergencial está encerrado. E1 exige chamado aberto associado ao recurso; sem a exceção, prevalece a negativa por outro projeto. |
| A14 | O papel é editor, mas exportação exige admin. A aprovação que vence amanhã não concede o papel exigido. |
| A16 | O papel é leitor, mas escrita exige editor ou admin. A aprovação válida de exportação não concede escrita, conforme regra expressa. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 e A05 ficam em lados distintos da fronteira temporal. Validade exige vencimento posterior ao instante da avaliação; igualdade já significa expiração. A05 está válida nesse instante por mais um segundo, sem implicar autorização futura.
- **Emergência:** A06 reúne todos os requisitos de E1: usuário ativo, papel suporte, leitura e chamado emergencial aberto associado ao recurso. A07 falha por suspensão, A08 solicita uma ação fora da exceção e A13 tem chamado encerrado.
- **Bloqueio:** O bloqueio impede escrita tanto para editor (A02) quanto para admin (A03), mas permite leitura (A09).
- **Leitura pelo suporte:** A15 pertence ao projeto P, portanto sua leitura é permitida pela regra geral, sem depender de E1 ou de chamado emergencial.
- **Aprovações e papéis:** Aprovação de exportação não substitui o papel admin (A14), não autoriza escrita (A16) nem concede acesso a outro projeto. Nenhuma aprovação ausente foi presumida, inclusive em A08 e A12. As aprovações mencionadas nos pedidos de exportação A04, A05 e A14 foram interpretadas no contexto como as aprovações exigidas para essa ação.
- **Expressão relativa em A14:** Não é necessário atribuir um horário exato a “amanhã”, pois o papel editor já impede a exportação mesmo com aprovação válida.

Exatamente dois subagentes diretos analisaram, respectivamente, A01–A08 e A09–A16, sem descendentes e sem escrever arquivos. Ambos concluíram suas análises antes da consolidação pelo agente principal. Não houve divergência material entre as análises e a revisão final. Foram usadas somente ferramentas locais e os arquivos de entrada foram preservados.
