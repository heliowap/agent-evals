# Aplicação da política aos pedidos

Foram permitidos 6 pedidos e negados 10, conforme `politica.md` e os fatos de `pedidos.md`. Cada pedido foi avaliado isoladamente em **10/10/2026 às 12:00:00 UTC**, usando o retrato de usuários fornecido. Aprovações ausentes não foram presumidas.

## Decisões e evidências

| ID | Decisão | Fundamentação |
| --- | --- | --- |
| A01 | Permitido | Usuário ativo do projeto P solicita leitura de recurso do próprio projeto, conforme a regra geral de leitura. |
| A02 | Negado | O recurso está bloqueado. Embora o usuário seja editor, a política exige também recurso desbloqueado para escrita. |
| A03 | Negado | O recurso está bloqueado. A política afirma expressamente: “Administrador não ignora bloqueio de escrita.” |
| A04 | Negado | A aprovação vence em 10/10/2026 às 12:00:00 UTC, exatamente no instante avaliado. Pela política, “No instante exato do vencimento, a aprovação já expirou.” Falta aprovação ainda válida para exportar. |
| A05 | Permitido | Usuário ativo, admin, do projeto P, com aprovação que vence às 12:00:01 UTC do mesmo dia. Ela ainda é válida às 12:00:00 UTC, atendendo aos requisitos de exportação. |
| A06 | Permitido | A exceção E1 admite esta leitura de outro projeto: usuário ativo, papel suporte e chamado emergencial aberto associado ao recurso. |
| A07 | Negado | O usuário está suspenso. “Suspensão bloqueia qualquer ação, inclusive acesso emergencial.” O chamado aberto não supera essa restrição, e E1 exige usuário ativo. |
| A08 | Negado | Usuário do projeto X solicita exportação. E1 só cobre leitura; suporte não confere exportação. Também faltam papel admin e aprovação válida informada, cuja ausência equivale a não. O chamado aberto não autoriza a operação nem supera a restrição de projeto para exportação. |
| A09 | Permitido | Usuário ativo do projeto P solicita leitura. A política permite expressamente leitura de recurso bloqueado. |
| A10 | Permitido | Usuário ativo do projeto P, com papel editor, solicita escrita em recurso desbloqueado. Os requisitos estão satisfeitos. |
| A11 | Negado | Usuário do projeto X solicita leitura de recurso de P. Admin não concede acesso a outro projeto. E1 não se aplica: o usuário não é suporte e não há chamado emergencial. |
| A12 | Negado | Falta aprovação do titular dos dados. A exportação exige essa aprovação ainda válida; ser admin não dispensa o requisito. |
| A13 | Negado | Usuário do projeto X solicita leitura, mas o chamado emergencial está encerrado. E1 exige chamado aberto associado ao recurso; sem essa exceção, aplica-se a negativa por outro projeto. |
| A14 | Negado | O usuário é editor, mas a exportação exige admin. A aprovação que vence amanhã é válida no instante avaliado, porém não substitui o papel exigido. |
| A15 | Permitido | Usuário ativo do projeto P pode ler recurso do próprio projeto pela regra geral, inclusive com papel suporte. Essa leitura não depende de chamado emergencial. |
| A16 | Negado | O usuário é leitor; escrita exige editor ou admin. O recurso desbloqueado não basta, e a aprovação de exportação válida não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 é negado no próprio instante de expiração; A05 é permitido porque vence um segundo depois. A decisão de A05 não deve ser extrapolada para o horário do vencimento.
- **Emergência:** somente A06 satisfaz E1. A07 falha por suspensão, A08 solicita uma ação fora do alcance da exceção e A13 apresenta chamado encerrado. A15 usa a regra geral de leitura, sem precisar de E1.
- **Bloqueio do recurso:** impede escrita para editor e admin (A02 e A03), mas permite leitura (A09).
- **Autorizações cumulativas:** aprovação válida não substitui admin na exportação (A14), não concede escrita (A16) e não concede acesso a outro projeto. Ausência de aprovação impede exportação (A12 e também A08).

A análise foi dividida entre exatamente dois subagentes diretos, sem descendentes: A01–A08 e A09–A16. Ambos devolveram suas análises por mensagem e concluíram antes da consolidação. O agente principal revisou as decisões e escreveu os arquivos finais. Foram usados somente arquivos desta pasta e ferramentas locais; os arquivos de entrada foram preservados.
