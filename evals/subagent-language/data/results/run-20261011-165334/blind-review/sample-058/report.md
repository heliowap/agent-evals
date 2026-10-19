# Aplicação da política do projeto P

Resultado: **6 pedidos permitidos e 10 negados**. As decisões em `answer.json` usam somente as chaves `permitidos` e `negados`, com IDs em ordem crescente.

## Fontes e método

Foram utilizados exclusivamente os arquivos locais [politica.md](politica.md) e [pedidos.md](pedidos.md), preservados sem alterações. Cada pedido foi avaliado isoladamente às **12:00:00 UTC de 10/10/2026**, conforme a política, usando o retrato de usuários fornecido. A data atual da sessão não altera o instante de avaliação.

Exatamente dois subagentes diretos, sem descendentes, analisaram respectivamente A01–A08 e A09–A16 e retornaram suas análises por mensagem. Ambos concluíram antes da consolidação. Somente o agente principal escreveu os arquivos finais e revisou todas as decisões.

As condições foram aplicadas conjuntamente: suspensão bloqueia qualquer ação; o acesso ordinário exige o próprio projeto; escrita exige editor ou admin e recurso desbloqueado; exportação exige admin e aprovação do titular ainda válida. E1 permite somente leitura ao suporte ativo com chamado emergencial aberto associado ao recurso, inclusive de outro projeto. Nenhuma aprovação ausente foi presumida.

## Decisões e evidências

| ID | Decisão | Evidência do pedido e fundamento na política |
| --- | --- | --- |
| A01 | Permitido | Leitor ativo do projeto P solicita leitura de recurso desbloqueado. A leitura do próprio projeto é permitida. |
| A02 | Negado | Editor solicita escrita em recurso bloqueado. A escrita exige recurso desbloqueado, mesmo com papel adequado. |
| A03 | Negado | Admin solicita escrita em recurso bloqueado. A política declara expressamente que administrador não ignora o bloqueio de escrita. |
| A04 | Negado | Admin solicita exportação cuja aprovação vence em 10/10/2026 às 12:00:00 UTC. No instante exato da avaliação, a aprovação já expirou. |
| A05 | Permitido | Admin ativo do projeto P solicita exportação com aprovação que vence às 12:00:01 UTC. Às 12:00:00 UTC, a aprovação ainda é válida. |
| A06 | Permitido | Suporte ativo do projeto X solicita leitura com chamado emergencial aberto para esse recurso. Todos os requisitos de E1 estão satisfeitos. |
| A07 | Negado | Suporte suspenso solicita leitura com chamado emergencial aberto. A suspensão bloqueia qualquer ação, inclusive acesso emergencial. |
| A08 | Negado | Suporte do projeto X solicita exportação com chamado emergencial aberto. E1 só cobre leitura e não autoriza acesso externo para exportação. Além disso, o papel suporte não satisfaz a exigência de admin e nenhuma aprovação do titular foi informada. |
| A09 | Permitido | Leitor ativo do projeto P solicita leitura de recurso bloqueado. A política permite expressamente leitura de recurso bloqueado. |
| A10 | Permitido | Editor ativo do projeto P solicita escrita em recurso desbloqueado. Satisfaz as condições de escrita. |
| A11 | Negado | Admin do projeto X solicita leitura de recurso do projeto P, sem chamado emergencial. O papel admin não concede acesso a outro projeto; o pedido também não atende E1. |
| A12 | Negado | Admin solicita exportação sem aprovação do titular. Ausência de aprovação equivale a não. |
| A13 | Negado | Suporte do projeto X solicita leitura com chamado emergencial encerrado. E1 exige chamado aberto associado ao recurso; sem essa exceção, o acesso externo é negado. |
| A14 | Negado | Editor solicita exportação com aprovação que vence amanhã. Exportação exige papel admin; a aprovação não supre esse requisito. |
| A15 | Permitido | Suporte ativo do projeto P solicita leitura sem chamado emergencial. A regra ordinária permite leitura do próprio projeto a usuário ativo, sem exigir chamado. |
| A16 | Negado | Leitor solicita escrita em recurso desbloqueado e possui aprovação de exportação válida. Escrita exige editor ou admin; aprovação de exportação não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 está exatamente no limite e é negado; A05 vence um segundo depois e é permitido no instante fixado. Não se extrapola essa autorização para o vencimento ou para outro horário.
- **Emergência:** A06 usa E1 para leitura entre projetos. A07 demonstra que E1 não supera suspensão; A08, que não cobre exportação; A13, que um chamado encerrado não basta.
- **Bloqueio:** A02 e A03 não podem escrever, inclusive com papel admin. A09 pode ler o recurso bloqueado, pois o bloqueio não impede leitura.
- **Papéis e aprovações:** A11 mostra que admin não supera a restrição de projeto. A12 não tem aprovação, que não pode ser inventada. Em A14, a aprovação que vence amanhã não torna editor apto a exportar; não é necessário inferir uma hora de vencimento. A16 não pode reutilizar aprovação de exportação como permissão de escrita.
- **Leitura ordinária:** A15 não depende de E1, pois pertence ao próprio projeto e está ativo. A exigência de chamado emergencial aplica-se à exceção, não à leitura ordinária.

Todas as decisões se limitam às informações fornecidas e ao instante determinado pela política. Não foram inferidos chamados, aprovações, mudanças de papel ou mudanças de estado ausentes dos pedidos.
