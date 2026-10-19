# Aplicação da política aos pedidos

Foram permitidos **6 pedidos** e negados **10 pedidos**, conforme a política vigente em `politica.md` e os fatos de `pedidos.md`. Todos foram avaliados isoladamente às **12:00:00 UTC de 10/10/2026**, usando o retrato de usuários válido para esse instante. A data atual não altera essa referência.

## Critérios de decisão

A suspensão impede qualquer ação, inclusive acesso emergencial. Usuários ativos podem ler recursos do próprio projeto; o bloqueio do recurso não impede leitura. Escrita exige projeto correspondente, papel editor ou admin e recurso desbloqueado. Administradores também estão sujeitos ao bloqueio de escrita.

Exportação exige usuário ativo do próprio projeto, papel admin e aprovação do titular ainda válida. A aprovação já está expirada no instante exato de seu vencimento. Não se presumiu nenhuma aprovação ausente, e uma aprovação de exportação não concede escrita nem acesso a outro projeto.

A exceção E1 permite leitura emergencial a usuário ativo com papel suporte, inclusive de outro projeto, quando existe chamado emergencial aberto associado ao recurso. Ela não autoriza escrita nem exportação e não supera suspensão.

## Pedidos negados

| ID | Evidência do pedido e motivo da negativa |
| --- | --- |
| A02 | O usuário é editor ativo do projeto P, mas solicita escrita em recurso bloqueado. O requisito de recurso desbloqueado não é atendido. |
| A03 | O usuário é admin ativo do projeto P, mas o recurso está bloqueado para escrita. A política declara que administrador não ignora esse bloqueio. |
| A04 | A aprovação vence em 10/10/2026 às 12:00:00 UTC, exatamente no instante da avaliação. Como nesse instante ela já expirou, falta aprovação válida para exportar. |
| A07 | O usuário está suspenso. Mesmo com papel suporte e chamado emergencial aberto para o recurso, a suspensão bloqueia a leitura emergencial. |
| A08 | O usuário é suporte do projeto X e pede exportação de recurso do projeto P. A E1 cobre somente leitura, e suporte não atende ao requisito de papel admin. Também não há aprovação do titular informada; o chamado não a substitui. |
| A11 | O usuário é admin do projeto X e pede leitura de recurso do projeto P. O papel admin não concede acesso a outro projeto, e não há condições para aplicar E1: o usuário não é suporte e não há chamado emergencial. |
| A12 | O usuário é admin ativo do projeto P, mas não tem aprovação do titular. A política equipara ausência de aprovação a negativa. |
| A13 | O usuário é suporte ativo do projeto X, mas o chamado emergencial está encerrado. A E1 exige chamado aberto associado ao recurso; permanece a negativa por projeto diferente. |
| A14 | O usuário é editor, enquanto exportação exige papel admin. A aprovação com vencimento amanhã não supre o requisito de papel, mesmo estando vigente no instante de referência. |
| A16 | O usuário é leitor e solicita escrita. Faltam os papéis editor ou admin, apesar de o recurso estar desbloqueado. A aprovação de exportação válida não concede escrita. |

## Pedidos permitidos e casos de fronteira

| ID | Evidência e fundamento da permissão |
| --- | --- |
| A01 | Usuário ativo do projeto P lê recurso do próprio projeto, conforme a regra geral. |
| A05 | Admin ativo do projeto P tem aprovação que vence às 12:00:01 UTC, um segundo após a avaliação. Ela ainda está válida às 12:00:00 UTC, atendendo aos requisitos de exportação. |
| A06 | Suporte ativo do projeto X tem chamado emergencial aberto associado ao recurso. A E1 permite especificamente essa leitura entre projetos. |
| A09 | Leitor ativo do projeto P pode ler recurso bloqueado. A política mantém expressamente a permissão de leitura quando há bloqueio. |
| A10 | Editor ativo do projeto P solicita escrita em recurso desbloqueado. Todos os requisitos de escrita estão atendidos. |
| A15 | Suporte ativo do projeto P lê recurso do próprio projeto pela regra geral. Um chamado emergencial não é necessário para essa leitura. |

A04 e A05 demonstram o limite temporal estrito da aprovação: vencimento igual ao instante de referência implica negativa; vencimento posterior permanece válido naquele instante. A06, A07, A08 e A13 delimitam a E1: ela exige usuário ativo, papel suporte, leitura e chamado aberto associado ao recurso. A15 mostra que essa exceção não é necessária para leitura comum no próprio projeto.

## Evidências, revisão e ressalvas

Foram utilizados somente os dois arquivos de entrada da pasta, preservados sem alterações. Exatamente dois subagentes diretos, sem descendentes e sem histórico herdado (`fork_turns="none"`), analisaram respectivamente A01–A08 e A09–A16; o segundo também revisou os limites e a precedência das regras. Ambos devolveram as análises por mensagem e concluíram antes da consolidação. Somente o agente principal escreveu os arquivos finais.

As decisões não extrapolam o instante indicado, não presumem privilégios adicionais e não inventam aprovações. Em A14, o requisito de papel já basta para negar exportação, independentemente de precisar o horário do vencimento amanhã. Em A08, os impedimentos de projeto e papel já bastam para negar; nenhuma aprovação ausente foi tratada como existente.

`answer.json` contém exatamente as chaves `permitidos` e `negados`, ambas com listas de IDs em ordem crescente. Cada um dos 16 pedidos aparece exatamente uma vez.
