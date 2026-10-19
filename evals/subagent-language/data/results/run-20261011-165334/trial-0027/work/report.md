# Aplicação da política aos pedidos

Foram permitidos 6 pedidos e negados 10, conforme `answer.json`. As únicas fontes são `politica.md` e `pedidos.md`, preservadas sem alterações. Cada pedido foi avaliado isoladamente às **12:00:00 UTC de 10/10/2026**, usando o retrato de usuários válido nesse instante. Não foram presumidas aprovações ausentes nem extrapoladas decisões para outros horários.

A análise foi dividida entre exatamente dois subagentes diretos, sem descendentes: um examinou A01–A08 e o outro A09–A16. Ambos retornaram suas análises por mensagem e concluíram o trabalho antes da consolidação. Somente o agente principal escreveu os arquivos finais; foram usadas apenas ferramentas locais.

## Decisões negadas

| ID | Evidência no pedido e fundamento da negativa |
| --- | --- |
| A02 | Editor ativo de P solicita escrita em recurso bloqueado. A escrita exige recurso desbloqueado. |
| A03 | Admin ativo de P solicita escrita em recurso bloqueado. A política diz expressamente que administrador não ignora esse bloqueio. |
| A04 | A aprovação de exportação vence em 10/10/2026 às 12:00:00 UTC, exatamente no instante da avaliação. A política considera a aprovação já expirada nesse instante. |
| A07 | O usuário de suporte está suspenso, embora haja chamado emergencial aberto associado ao recurso. Suspensão bloqueia qualquer ação, inclusive acesso emergencial. |
| A08 | Suporte ativo do projeto X solicita exportação com chamado emergencial aberto. E1 só cobre leitura; suporte não tem o papel admin exigido para exportar, e o projeto diferente também impede acesso ordinário. Não há aprovação do titular informada, e o chamado não a substitui. |
| A11 | Admin ativo do projeto X solicita leitura de recurso de P, sem chamado emergencial. Outro projeto impede acesso ordinário; E1 não se aplica, pois exige papel suporte e chamado emergencial aberto associado ao recurso. |
| A12 | Admin ativo de P solicita exportação sem aprovação do titular. A política exige aprovação ainda válida e determina que sua ausência equivale a não. |
| A13 | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado. A fronteira entre projetos só seria superada por E1 com chamado aberto associado ao recurso; chamado encerrado não atende. |
| A14 | Editor ativo de P solicita exportação com aprovação que vence amanhã. Mesmo ainda válida no instante avaliado, a aprovação não supre o papel admin exigido para exportação. |
| A16 | Leitor ativo de P solicita escrita em recurso desbloqueado e possui aprovação de exportação válida. Escrita exige editor ou admin; aprovação de exportação não concede escrita. |

## Decisões permitidas e casos de exceção ou fronteira

| ID | Evidência e fundamento da permissão |
| --- | --- |
| A01 | Leitor ativo de P solicita leitura de recurso desbloqueado do próprio projeto. Atende à regra ordinária de leitura. |
| A05 | Admin ativo de P solicita exportação com aprovação que vence às 12:00:01 UTC de 10/10/2026. Ela ainda é válida às 12:00:00 UTC, um segundo antes do vencimento. |
| A06 | Suporte ativo do projeto X solicita leitura com chamado emergencial aberto associado ao recurso. Satisfaz E1, que permite essa leitura mesmo entre projetos. |
| A09 | Leitor ativo de P solicita leitura de recurso bloqueado. A política mantém expressamente a leitura permitida apesar do bloqueio. |
| A10 | Editor ativo de P solicita escrita em recurso desbloqueado. Satisfaz os requisitos de atividade, projeto, papel e desbloqueio. |
| A15 | Suporte ativo de P solicita leitura de recurso desbloqueado, sem chamado emergencial. A regra ordinária permite leitura no próprio projeto a usuário ativo; não é necessário recorrer a E1. |

## Ressalvas

A04 e A05 demonstram a fronteira temporal: no vencimento exato a aprovação já expirou; um segundo antes, ainda está válida. A autorização de A05 vale para o instante solicitado, sem previsão sobre horários posteriores.

E1 foi aplicada somente à leitura de A06. Ela não supera suspensão (A07), não autoriza exportação (A08) e exige chamado aberto, não encerrado (A13). Administrador também não supera bloqueio de escrita (A03) ou a restrição de projeto (A11).

Os requisitos são cumulativos: aprovação válida não substitui o papel admin para exportação (A14) nem autoriza escrita (A16). Nenhuma aprovação ausente foi inventada, inclusive em A08 e A12.
