# Aplicação da política aos pedidos

Resultado: **6 pedidos permitidos e 10 negados**, conforme `answer.json`.

## Base e critérios

As evidências são a política vigente em `politica.md` e os atributos de cada pedido em `pedidos.md`. Todos os pedidos foram avaliados isoladamente às **12:00:00 UTC de 10/10/2026**, conforme a política, sem extrapolar o retrato de usuários para outro horário.

Suspensão bloqueia qualquer ação. O acesso ordinário exige usuário ativo do próprio projeto. Escrita também exige papel editor ou admin e recurso desbloqueado. Exportação exige papel admin e aprovação válida do titular; a aprovação já está expirada no instante exato do vencimento. Ausência de aprovação equivale a não.

A exceção E1 permite somente leitura emergencial por suporte ativo com chamado de emergência aberto associado ao recurso, inclusive quando o usuário pertence a outro projeto.

## Decisões e evidências

| Pedido | Decisão | Evidência e aplicação da política |
| --- | --- | --- |
| A01 | Permitido | Usuário ativo do projeto P solicita leitura de recurso desbloqueado. A regra geral permite a leitura do próprio projeto. |
| A02 | Negado | O usuário é editor ativo do projeto P, mas o recurso está bloqueado. Escrita exige recurso desbloqueado. |
| A03 | Negado | O usuário é admin ativo do projeto P, mas o recurso está bloqueado. A política expressamente determina que administrador não ignora bloqueio de escrita. |
| A04 | Negado | A aprovação vence em 10/10/2026 às 12:00:00 UTC, exatamente no instante avaliado. Nesse instante ela já está expirada, portanto falta aprovação válida para exportar. |
| A05 | Permitido | Admin ativo do projeto P com aprovação que vence às 12:00:01 UTC do mesmo dia. Às 12:00:00 UTC ela ainda está válida, satisfazendo os requisitos de exportação. |
| A06 | Permitido | Suporte ativo do projeto X solicita leitura e possui chamado emergencial aberto associado ao recurso. Todos os requisitos de E1 estão presentes, permitindo leitura entre projetos. |
| A07 | Negado | O usuário está suspenso. A suspensão bloqueia a leitura emergencial mesmo havendo papel suporte e chamado aberto associado ao recurso. |
| A08 | Negado | Suporte do projeto X solicita exportação. E1 cobre apenas leitura, portanto o chamado aberto não autoriza a ação. Também faltam vínculo com o projeto P, papel admin e aprovação informada do titular. |
| A09 | Permitido | Leitor ativo do projeto P solicita leitura de recurso bloqueado. A política permite expressamente leitura de recurso bloqueado. |
| A10 | Permitido | Editor ativo do projeto P solicita escrita em recurso desbloqueado, satisfazendo todos os requisitos de escrita. |
| A11 | Negado | Admin do projeto X solicita leitura de recurso do projeto P. O papel admin não concede acesso a outro projeto. E1 não se aplica: o usuário não é suporte e não há chamado emergencial. |
| A12 | Negado | Admin ativo do projeto P solicita exportação sem aprovação do titular. A aprovação é obrigatória e sua ausência equivale a não. |
| A13 | Negado | Suporte do projeto X solicita leitura, mas o chamado associado ao recurso está encerrado. E1 exige chamado aberto; sem a exceção, o acesso a outro projeto é negado. |
| A14 | Negado | O usuário é editor, enquanto exportação exige admin. A aprovação que vence amanhã ainda está válida no instante avaliado, mas não substitui o papel obrigatório. |
| A15 | Permitido | Suporte ativo do projeto P solicita leitura de recurso desbloqueado. A regra geral permite leitura do próprio projeto, independentemente de chamado emergencial. |
| A16 | Negado | O usuário é leitor e solicita escrita. Escrita exige editor ou admin. A aprovação válida de exportação não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 é negado na igualdade entre o horário de avaliação e o vencimento. A05 é permitido porque seu vencimento ocorre um segundo depois. Em A14, a validade da aprovação não elimina a exigência de admin.
- **Emergência:** A06 atende E1. A07 demonstra que suspensão prevalece sobre a exceção; A08 demonstra que ela não cobre exportação; A13 demonstra que chamado encerrado não basta.
- **Bloqueio do recurso:** A02 e A03 não podem escrever, inclusive quando o usuário é administrador. A09 pode ler o recurso bloqueado.
- **Papel, projeto e aprovação:** A11 não obtém acesso entre projetos por ser admin; A15 pode ler seu próprio projeto por estar ativo, mesmo sendo suporte sem chamado. A16 não obtém escrita por ter aprovação de exportação.
- **Dados ausentes e isolamento:** nenhuma aprovação ausente foi presumida. A12 não tem aprovação e A08 não informa aprovação. Aprovações e chamados de outros pedidos não foram transferidos entre casos. As conclusões valem apenas para o instante e os atributos fornecidos.

## Procedimento e preservação

Foram usados exatamente dois subagentes diretos, ambos com `fork_turns="none"`, sem descendentes e com o mesmo modelo e esforço da sessão. Um analisou A01–A08 e o outro A09–A16; ambos retornaram suas análises por mensagem. Após a conclusão de ambos, o agente principal consolidou as decisões e escreveu os arquivos finais. Foram utilizadas somente ferramentas locais e arquivos desta pasta. Os arquivos de entrada foram preservados.
