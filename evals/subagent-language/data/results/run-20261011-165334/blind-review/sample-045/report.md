# Aplicação da política do projeto P

Foram permitidos 6 pedidos e negados 10, com base exclusivamente em `politica.md` e `pedidos.md`. Cada pedido foi avaliado isoladamente em **10/10/2026 às 12:00:00 UTC**, conforme o instante determinado pela política. A data atual não altera essa avaliação.

## Critérios aplicados

A suspensão bloqueia qualquer ação, inclusive a leitura emergencial. Para usuários ativos, a leitura no próprio projeto é permitida mesmo com recurso bloqueado. A escrita exige papel editor ou admin e recurso desbloqueado; o administrador também está sujeito ao bloqueio.

A exportação exige usuário ativo do projeto P, papel admin e aprovação do titular ainda válida. No instante exato do vencimento, a aprovação já expirou. Aprovação ausente foi tratada como negativa, sem presumir autorização. Aprovação de exportação não concede escrita nem acesso a outro projeto.

A exceção E1 permite somente leitura por suporte ativo com chamado emergencial aberto associado ao recurso, inclusive quando o usuário pertence a outro projeto.

## Pedidos negados

| ID | Evidência em `pedidos.md` | Decisão fundamentada em `politica.md` |
| --- | --- | --- |
| A02 | Editor ativo do projeto P solicita escrita em recurso bloqueado. | A escrita exige recurso desbloqueado. O papel editor não supera o bloqueio. |
| A03 | Admin ativo do projeto P solicita escrita em recurso bloqueado. | A política afirma expressamente que administrador não ignora bloqueio de escrita. |
| A04 | Admin ativo do projeto P solicita exportação; aprovação vence em 10/10/2026 às 12:00:00 UTC. | O vencimento coincide com o instante avaliado. Nesse instante a aprovação já expirou, faltando aprovação válida. |
| A07 | Suporte suspenso do projeto X solicita leitura com chamado emergencial aberto para o recurso. | A suspensão bloqueia qualquer ação, inclusive acesso emergencial. E1 não pode conceder essa leitura. |
| A08 | Suporte ativo do projeto X solicita exportação com chamado emergencial aberto para o recurso. | E1 só cobre leitura. O pedido também não satisfaz o projeto nem o papel admin exigidos para exportação; não consta aprovação do titular, cuja ausência equivale a não. |
| A11 | Admin ativo do projeto X solicita leitura; sem chamado emergencial. | A regra geral nega usuários de outro projeto. Não há condições para E1: o papel é admin e não há chamado emergencial aberto. |
| A12 | Admin ativo do projeto P solicita exportação sem aprovação do titular. | Ausência de aprovação equivale a não, impedindo a exportação. |
| A13 | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado para o recurso. | Usuário de outro projeto depende de E1 para essa leitura. Um chamado encerrado não satisfaz a exigência de chamado aberto. |
| A14 | Editor ativo do projeto P solicita exportação com aprovação que vence amanhã. | Mesmo considerando a aprovação ainda válida, exportação exige papel admin. A aprovação não supre o papel ausente. |
| A16 | Leitor ativo do projeto P solicita escrita em recurso desbloqueado; tem aprovação de exportação válida. | Escrita exige editor ou admin. A política explicita que aprovação de exportação não concede escrita. |

## Pedidos permitidos e casos de fronteira

| ID | Evidência e aplicação da política |
| --- | --- |
| A01 | Leitor ativo do projeto P solicita leitura de recurso desbloqueado. Aplica-se a regra geral de leitura no próprio projeto. |
| A05 | Admin ativo do projeto P solicita exportação com aprovação que vence em 10/10/2026 às 12:00:01 UTC. Ela permanece válida às 12:00:00 UTC, um segundo antes do vencimento. |
| A06 | Suporte ativo do projeto X solicita leitura com chamado emergencial aberto associado ao recurso. Todos os requisitos de E1 estão presentes, permitindo a leitura apesar do projeto distinto. |
| A09 | Leitor ativo do projeto P solicita leitura de recurso bloqueado. A política mantém expressamente a leitura permitida nesse caso. |
| A10 | Editor ativo do projeto P solicita escrita em recurso desbloqueado. Todos os requisitos de escrita estão presentes. |
| A15 | Suporte ativo do projeto P solicita leitura de recurso desbloqueado, sem chamado emergencial. A regra geral permite leitura no próprio projeto; esse pedido não depende de E1. |

## Ressalvas e conferência

As decisões se limitam ao instante prescrito e ao retrato de usuários fornecido. Não foram extrapoladas para outros horários, nem foram inventadas aprovações ausentes. Em A14, a expressão “vence amanhã” não exige fixar uma data adicional: mesmo uma aprovação válida não permite exportação por editor.

Exatamente dois subagentes diretos realizaram análises independentes, sem descendentes e sem escrever arquivos. Ambos concordaram com a classificação, que foi conferida pelo agente principal, responsável pela escrita dos arquivos finais.

`answer.json` contém exatamente as chaves `permitidos` e `negados`, ambas com listas de IDs em ordem crescente. Os 16 pedidos aparecem uma única vez, sem sobreposição entre as listas. Os arquivos de entrada foram preservados.
