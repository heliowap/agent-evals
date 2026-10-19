# Aplicação da política aos pedidos

A avaliação usa exclusivamente `politica.md` e `pedidos.md`, no instante fixado pela política: **10/10/2026 às 12:00:00 UTC**. Cada pedido foi avaliado isoladamente, usando o retrato de usuários válido para esse instante. Resultado: **6 permitidos e 10 negados**.

Dois subagentes diretos fizeram análises independentes, sem descendentes e sem escrever arquivos. Ambos retornaram suas análises por mensagem e concordaram com todas as classificações. A consolidação e a escrita dos arquivos finais foram feitas pelo agente principal. Os arquivos de entrada foram preservados.

## Pedidos permitidos

| ID | Evidência do pedido e fundamento da decisão |
| --- | --- |
| A01 | Usuário ativo do projeto P solicita leitura de recurso desbloqueado. A regra geral permite leitura no próprio projeto. |
| A05 | Admin ativo do projeto P, com aprovação que vence às 12:00:01 UTC de 10/10/2026. Às 12:00:00 UTC, a aprovação ainda está válida; a exportação é permitida. |
| A06 | Suporte ativo do projeto X, com chamado emergencial aberto associado ao recurso. Satisfaz a exceção E1, que permite essa leitura mesmo de outro projeto. |
| A09 | Leitor ativo do projeto P solicita leitura de recurso bloqueado. A política estabelece expressamente que o bloqueio não impede leitura. |
| A10 | Editor ativo do projeto P solicita escrita de recurso desbloqueado. Satisfaz os requisitos de escrita. |
| A15 | Suporte ativo do projeto P solicita leitura. A regra geral permite leitura por usuário ativo do próprio projeto; não exige chamado emergencial. |

## Pedidos negados

| ID | Evidência do pedido e fundamento da decisão |
| --- | --- |
| A02 | Editor ativo do projeto P solicita escrita de recurso bloqueado. Escrita exige recurso desbloqueado, mesmo quando o papel é editor. |
| A03 | Admin ativo do projeto P solicita escrita de recurso bloqueado. A política determina: “Administrador não ignora bloqueio de escrita.” |
| A04 | A aprovação vence exatamente em 10/10/2026 às 12:00:00 UTC, o instante da avaliação. A política determina que, no instante exato do vencimento, ela já expirou. Falta aprovação ainda válida para exportar. |
| A07 | Suporte suspenso do projeto X, embora tenha chamado emergencial aberto. Suspensão bloqueia qualquer ação, inclusive acesso emergencial; E1 não se aplica a usuário suspenso. |
| A08 | Suporte ativo do projeto X solicita exportação com chamado emergencial aberto. E1 só cobre leitura, portanto não autoriza exportação entre projetos. Além disso, suporte não tem o papel admin exigido e não há aprovação do titular informada; aprovação ausente equivale a não. |
| A11 | Admin ativo do projeto X solicita leitura de recurso de P, sem chamado emergencial. A regra geral nega acesso de outro projeto. O papel admin não cria exceção, e o pedido não satisfaz E1. |
| A12 | Admin ativo do projeto P solicita exportação sem aprovação do titular. A política exige aprovação ainda válida e determina que sua ausência equivale a não. |
| A13 | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado. E1 exige chamado aberto associado ao recurso; sem essa condição, prevalece a negativa para outro projeto. |
| A14 | Editor ativo do projeto P solicita exportação com aprovação que vence amanhã. Embora a aprovação ainda esteja válida no instante avaliado, exportação exige papel admin. A aprovação não substitui esse requisito. |
| A16 | Leitor ativo do projeto P solicita escrita de recurso desbloqueado com aprovação de exportação válida. Escrita exige editor ou admin, e uma aprovação de exportação não concede escrita. |

## Exceções, fronteiras e ressalvas

**Vencimento:** A04 e A05 estão em lados distintos da fronteira temporal. A04 já expirou às 12:00:00 UTC; A05 vence um segundo depois e está válida naquele instante. Não se extrapola a permissão de A05 para o instante do seu vencimento nem para horários posteriores. “Amanhã”, em A14, indica vencimento posterior ao instante avaliado, mas não supre a exigência de papel admin.

**Emergência:** A06 reúne as condições de E1: usuário ativo, papel suporte e chamado emergencial aberto associado ao recurso. A07 falha por suspensão, A08 solicita uma ação fora do alcance da exceção e A13 tem chamado encerrado. A15 pode ler pela regra comum do próprio projeto, sem precisar recorrer a E1.

**Bloqueio e permissões específicas:** O bloqueio impede escrita em A02 e A03, inclusive para admin, mas permite leitura em A09. Aprovação de exportação não concede escrita, como em A16, nem acesso a outro projeto. Papéis e aprovações devem satisfazer os requisitos da ação solicitada.

Não foram presumidas aprovações ausentes, reabertura de chamados, alterações de estado dos usuários ou privilégios adicionais. As decisões valem apenas para os pedidos e o instante fornecidos. `answer.json` contém exatamente as chaves `permitidos` e `negados`, com todos os IDs classificados uma única vez e em ordem crescente.
