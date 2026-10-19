# Aplicação da política do projeto P

Resultado: **6 pedidos permitidos e 10 negados**, avaliados isoladamente às **12:00:00 UTC de 10/10/2026**, conforme o instante estabelecido em [politica.md](politica.md). Os fatos de cada pedido vêm de [pedidos.md](pedidos.md). O resultado estruturado está em [answer.json](answer.json).

## Critérios e evidências

A suspensão impede qualquer ação, inclusive acesso emergencial. Usuários ativos podem ler recursos do próprio projeto, mesmo bloqueados. Escrita exige papel editor ou admin e recurso desbloqueado; admin não pode ignorar o bloqueio. Exportação exige papel admin e aprovação do titular ainda válida, além do vínculo com o projeto. A aprovação já está expirada no instante exato de seu vencimento; sua ausência equivale a não aprovação e ela não concede escrita nem acesso a outro projeto.

A exceção E1 permite somente leitura por usuário ativo do suporte, inclusive de outro projeto, quando há chamado emergencial aberto associado ao recurso. Ela não afasta a suspensão nem autoriza escrita ou exportação.

## Decisões por pedido

| ID | Decisão | Fundamentação |
| --- | --- | --- |
| A01 | Permitido | Usuário ativo do projeto P pode ler seu recurso desbloqueado. |
| A02 | Negado | O recurso está bloqueado. O papel editor não satisfaz a exigência de recurso desbloqueado para escrita. |
| A03 | Negado | O recurso está bloqueado. A política determina expressamente que admin não ignora bloqueio de escrita. |
| A04 | Negado | A aprovação vence às 12:00:00 UTC de 10/10/2026, exatamente no instante avaliado. Nesse instante, ela já expirou. |
| A05 | Permitido | Usuário ativo, admin do projeto P, com aprovação que vence às 12:00:01 UTC de 10/10/2026, um segundo após a avaliação. A aprovação ainda é válida. |
| A06 | Permitido | A exceção E1 se aplica: usuário ativo do suporte, pedido de leitura e chamado emergencial aberto associado ao recurso. Ela permite essa leitura apesar do projeto X. |
| A07 | Negado | O usuário está suspenso. A suspensão bloqueia inclusive acesso emergencial, mesmo havendo chamado aberto. |
| A08 | Negado | O usuário pertence ao projeto X e tem papel suporte, que não autoriza exportação. E1 cobre somente leitura. O pedido também não informa aprovação do titular; o chamado emergencial não a substitui. |
| A09 | Permitido | Usuário ativo do projeto P pode ler o recurso. O bloqueio não impede leitura, conforme regra expressa. |
| A10 | Permitido | Usuário ativo, editor do projeto P, solicita escrita em recurso desbloqueado. As condições de escrita estão satisfeitas. |
| A11 | Negado | O usuário pertence ao projeto X. O papel admin não concede leitura em outro projeto; também não há condições para E1. |
| A12 | Negado | Falta aprovação do titular, requisito obrigatório para exportação mesmo por admin ativo do projeto P. |
| A13 | Negado | O usuário pertence ao projeto X e o chamado emergencial está encerrado. E1 exige chamado aberto associado ao recurso. |
| A14 | Negado | Exportação exige admin, mas o usuário é editor. A aprovação com vencimento futuro não supre esse requisito de papel. |
| A15 | Permitido | A regra comum de leitura se aplica ao usuário ativo do próprio projeto P, inclusive com papel suporte. Não é necessário chamado emergencial nesse caso. |
| A16 | Negado | O usuário é leitor, enquanto escrita exige editor ou admin. A aprovação de exportação válida não concede escrita, mesmo com recurso desbloqueado. |

## Exceções, fronteiras e ressalvas

A04 e A05 demonstram a fronteira temporal: validade exige vencimento estritamente posterior ao instante avaliado. A decisão de A05 vale para o instante fixado; não se estende ao segundo seguinte.

A06 é o único pedido permitido pela exceção E1. A07 mostra que a suspensão prevalece sobre o acesso emergencial; A08 mostra que a exceção não cobre exportação; A13 mostra que um chamado encerrado não atende à exigência de chamado aberto. A15 usa a regra comum de leitura no próprio projeto, sem depender de E1.

A02, A03 e A09 distinguem o efeito do bloqueio: ele impede escrita, inclusive por admin, mas permite leitura. A14 e A16 mostram que uma aprovação não substitui o papel exigido nem autoriza outra operação.

Não foram presumidas aprovações ausentes, reabertura de chamados ou mudanças no estado dos usuários. A lista de usuários foi tratada como retrato válido apenas para o instante especificado, sem extrapolação para a data atual ou outros horários.

## Revisão e validação

Exatamente dois subagentes diretos, iniciados com `fork_turns="none"` e sem descendentes, analisaram A01–A08 e A09–A16, respectivamente; o segundo também conferiu a fronteira temporal de A04/A05. Ambos devolveram suas análises por mensagem e concluíram antes da redação. As conclusões coincidiram com a revisão do agente principal, único responsável por escrever os arquivos finais. Foram utilizadas apenas ferramentas locais.

O JSON foi validado quanto às duas chaves exigidas, às listas de IDs em ordem crescente e à cobertura de todos os 16 pedidos, sem duplicidades ou sobreposição. Os hashes SHA-256 de `politica.md` e `pedidos.md` foram comparados antes e depois para confirmar a preservação dos arquivos de entrada.
