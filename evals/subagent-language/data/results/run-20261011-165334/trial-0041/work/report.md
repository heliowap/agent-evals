# Aplicação da política aos pedidos

Foram permitidos 6 pedidos e negados 10, conforme `politica.md` e os fatos declarados em `pedidos.md`. Cada pedido foi avaliado isoladamente em **10/10/2026 às 12:00:00 UTC**, usando o retrato de usuários válido para esse instante.

## Critérios e evidências

A política estabelece que um usuário ativo pode ler recursos de seu próprio projeto. A suspensão bloqueia qualquer ação, inclusive acesso emergencial. O acesso de outro projeto é negado, ressalvada a leitura pela exceção E1.

Para escrita, os requisitos são cumulativos: usuário ativo do projeto P, papel editor ou admin e recurso desbloqueado. A regra explicita: “Administrador não ignora bloqueio de escrita”. O bloqueio não impede leitura.

Para exportação, são necessários usuário ativo do projeto P, papel admin e aprovação do titular ainda válida. A política determina: “No instante exato do vencimento, a aprovação já expirou” e “Ausência de aprovação equivale a não”. Aprovação de exportação não concede escrita nem acesso a outro projeto.

A exceção E1 cobre somente leitura por suporte ativo com chamado emergencial aberto associado ao recurso, inclusive quando o usuário pertence a outro projeto. Ela não concede escrita ou exportação e não supera suspensão.

## Decisões por pedido

| ID | Decisão | Fatos e fundamento |
|---|---|---|
| A01 | Permitido | Usuário ativo, leitor, do projeto P, solicitando leitura de recurso desbloqueado: satisfaz a regra geral de leitura. |
| A02 | Negado | Embora ativo, editor e do projeto P, solicita escrita em recurso bloqueado. O bloqueio impede a escrita. |
| A03 | Negado | Embora ativo, admin e do projeto P, solicita escrita em recurso bloqueado. A política não permite que administrador ignore o bloqueio. |
| A04 | Negado | A aprovação vence em 10/10/2026 às 12:00:00 UTC, exatamente o instante avaliado. Já está expirada; o papel admin não substitui aprovação válida. |
| A05 | Permitido | Usuário ativo, admin, do projeto P, com aprovação que vence às 12:00:01 UTC do mesmo dia. Às 12:00:00 UTC ela ainda está válida. |
| A06 | Permitido | Suporte ativo do projeto X solicita leitura e possui chamado emergencial aberto associado ao recurso. E1 permite essa leitura entre projetos. |
| A07 | Negado | O usuário está suspenso. A suspensão bloqueia a leitura mesmo com papel suporte e chamado emergencial aberto associado ao recurso. |
| A08 | Negado | Suporte do projeto X solicita exportação. E1 só cobre leitura; o chamado aberto não concede exportação nem acesso geral entre projetos. Também falta o papel admin, e não há aprovação do titular informada. |
| A09 | Permitido | Usuário ativo, leitor, do projeto P solicita leitura. A política permite leitura de recurso bloqueado. |
| A10 | Permitido | Usuário ativo, editor, do projeto P solicita escrita em recurso desbloqueado: todos os requisitos de escrita são satisfeitos. |
| A11 | Negado | Admin do projeto X solicita leitura de recurso do projeto P. O papel admin não permite acesso entre projetos. E1 não se aplica: o usuário não tem papel suporte e não há chamado emergencial. |
| A12 | Negado | Usuário ativo, admin, do projeto P solicita exportação sem aprovação do titular. A ausência de aprovação equivale a não. |
| A13 | Negado | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado. E1 exige chamado aberto; permanece a restrição entre projetos. |
| A14 | Negado | Usuário ativo, editor, do projeto P solicita exportação. Mesmo com aprovação que vence amanhã, falta o papel admin exigido para exportar. |
| A15 | Permitido | Suporte ativo do projeto P solicita leitura de recurso desbloqueado. A regra geral permite leitura no próprio projeto; não exige chamado emergencial. |
| A16 | Negado | Usuário ativo, leitor, do projeto P solicita escrita em recurso desbloqueado. Falta papel editor ou admin; a aprovação de exportação válida não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 e A05 estão em lados diferentes da fronteira temporal. Vencimento igual ao instante avaliado implica aprovação expirada; vencimento um segundo depois implica aprovação ainda válida. A decisão de A05 não se estende ao instante de seu vencimento.
- **Emergência:** A06 satisfaz todos os requisitos de E1. A07 falha por suspensão, A08 solicita uma ação fora do alcance da exceção e A13 apresenta chamado encerrado. A15 usa a regra geral de leitura no próprio projeto e dispensa E1.
- **Bloqueio do recurso:** impede A02 e A03, mas permite a leitura de A09. O papel admin não remove a restrição de escrita.
- **Limites da aprovação:** a aprovação ausente impede A12; a aprovação válida não supre o papel admin em A14 nem o papel de escrita em A16. Nenhuma aprovação não informada foi presumida.

Dois subagentes diretos, iniciados com `fork_turns="none"` e sem descendentes, analisaram respectivamente A01–A08 e A09–A16. Ambos retornaram suas análises por mensagem e concluíram antes da redação dos arquivos finais pelo agente principal. As decisões foram conferidas contra as entradas, sem extrapolar o estado dos usuários ou das aprovações para outros horários. Os arquivos de entrada foram preservados.
