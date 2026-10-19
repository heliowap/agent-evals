# Aplicação da política do projeto P

Foram avaliados os 16 pedidos de [pedidos.md](pedidos.md), conforme a versão vigente de [politica.md](politica.md), exclusivamente em **10/10/2026 às 12:00:00 UTC**. O resultado é de **6 permitidos e 10 negados**, registrado em [answer.json](answer.json).

## Critérios e evidências

Cada pedido foi avaliado isoladamente. Suspensão impede qualquer ação, inclusive emergência. Usuário ativo pode ler recursos do próprio projeto, mesmo bloqueados. Escrita exige papel editor ou admin e recurso desbloqueado. Exportação exige papel admin e aprovação do titular ainda válida; no instante exato do vencimento, a aprovação já expirou. Aprovação de exportação não concede escrita nem acesso a outro projeto.

A exceção E1 permite somente leitura por suporte ativo de outro projeto, desde que exista chamado emergencial aberto associado ao recurso. Ela não supera suspensão nem autoriza escrita ou exportação. Nenhuma aprovação ausente foi presumida.

## Pedidos permitidos

| ID | Evidência do pedido e fundamento |
| --- | --- |
| A01 | Usuário ativo, leitor do projeto P, solicita leitura de recurso desbloqueado. Satisfaz a regra de leitura do próprio projeto. |
| A05 | Admin ativo do projeto P, com aprovação que vence às 12:00:01 UTC de 10/10/2026. A aprovação está válida no instante da avaliação, um segundo antes do vencimento. |
| A06 | Suporte ativo do projeto X, com chamado emergencial aberto para o recurso. A leitura é permitida pela exceção E1, apesar do projeto diferente. |
| A09 | Leitor ativo do projeto P solicita leitura de recurso bloqueado. O bloqueio não impede leitura. |
| A10 | Editor ativo do projeto P solicita escrita de recurso desbloqueado. Satisfaz as condições de escrita. |
| A15 | Suporte ativo do projeto P solicita leitura de recurso desbloqueado. A regra comum de leitura permite o acesso; não exige chamado emergencial. |

## Pedidos negados

| ID | Evidência do pedido e motivo da negativa |
| --- | --- |
| A02 | Editor ativo do projeto P solicita escrita de recurso bloqueado. O bloqueio impede escrita mesmo com papel editor. |
| A03 | Admin ativo do projeto P solicita escrita de recurso bloqueado. Administrador não ignora esse bloqueio. |
| A04 | Admin ativo do projeto P solicita exportação com aprovação que vence exatamente em 10/10/2026 às 12:00:00 UTC. Nesse instante a aprovação já expirou. |
| A07 | Suporte suspenso do projeto X solicita leitura com chamado emergencial aberto. Suspensão bloqueia qualquer ação e impede a aplicação de E1. |
| A08 | Suporte ativo do projeto X solicita exportação com chamado emergencial aberto. E1 só cobre leitura; o chamado não autoriza exportação entre projetos. O papel suporte também não satisfaz a exigência de admin, e o pedido não informa aprovação do titular. |
| A11 | Admin ativo do projeto X solicita leitura de recurso do projeto P, sem chamado emergencial. Outro projeto é negado; admin não concede esse acesso. E1 não se aplica, pois exige suporte e chamado emergencial aberto. |
| A12 | Admin ativo do projeto P solicita exportação sem aprovação do titular. Ausência de aprovação equivale a não. |
| A13 | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado. E1 exige chamado aberto; permanece a negativa por projeto diferente. |
| A14 | Editor ativo do projeto P solicita exportação com aprovação que vence amanhã. Mesmo considerando a aprovação válida no instante avaliado, o papel editor não satisfaz a exigência de admin. |
| A16 | Leitor ativo do projeto P solicita escrita de recurso desbloqueado e tem aprovação de exportação válida. Escrita exige editor ou admin; aprovação de exportação não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 está exatamente na fronteira e é negado; A05 ainda tem aprovação válida e é permitido. A validade exige que o vencimento seja posterior ao instante avaliado.
- **Emergência:** A06 satisfaz E1. A07 falha por suspensão; A08 solicita uma ação não coberta; A13 apresenta chamado encerrado. A15 não depende de E1, pois é leitura por usuário ativo do próprio projeto.
- **Bloqueio e papel:** A02 e A03 mostram que nem editor nem admin podem escrever em recurso bloqueado. A09 mostra que o mesmo bloqueio não impede leitura.
- **Alcance da aprovação:** A14 tem aprovação, mas não tem o papel exigido para exportar. A16 tem aprovação de exportação, mas não tem o papel exigido para escrever. A12 não tem aprovação e é negado sem presumir autorização.
- **Tempo e independência:** a expressão “amanhã” em A14 indica vencimento posterior ao instante de avaliação; não é necessário inferir uma hora exata, pois o papel já impede exportação. As decisões não são extrapoladas para outro horário e nenhum pedido concede autorização a outro.

## Procedimento de revisão

Exatamente dois subagentes diretos, iniciados com `fork_turns="none"` e sem descendentes, analisaram A01–A08 e A09–A16, respectivamente. Ambos retornaram seus pareceres por mensagem e concluíram antes da redação dos arquivos finais. O agente principal conferiu as decisões com as fontes e foi o único a escrever os arquivos finais. Foram usadas apenas ferramentas locais, e os arquivos de entrada foram preservados.
