# Aplicação da política aos pedidos

Foram permitidos 6 pedidos e negados 10, conforme `politica.md` e os fatos de `pedidos.md`. Cada pedido foi avaliado isoladamente às **12:00:00 UTC de 10/10/2026**, usando o retrato de usuários fornecido. Não foram presumidas aprovações ou permissões adicionais. Os arquivos de entrada foram preservados.

Dois subagentes diretos, sem descendentes, analisaram respectivamente A01–A08 e A09–A16 e retornaram suas análises por mensagem. Após a conclusão de ambos, o agente principal conferiu as decisões e escreveu os arquivos finais.

## Decisões e evidências

| ID | Decisão | Fatos do pedido e aplicação da política |
|---|---|---|
| A01 | Permitido | Usuário ativo, leitor, do projeto P, solicita leitura. A política permite leitura no próprio projeto. |
| A02 | Negado | Editor ativo do projeto P solicita escrita em recurso bloqueado. Escrita exige recurso desbloqueado, mesmo quando o papel é suficiente. |
| A03 | Negado | Admin ativo do projeto P solicita escrita em recurso bloqueado. A política determina expressamente que administrador não ignora bloqueio de escrita. |
| A04 | Negado | Admin ativo do projeto P solicita exportação com aprovação que vence às 12:00:00 UTC de 10/10/2026. Esse é o instante da avaliação; a política estabelece que, no instante exato do vencimento, a aprovação já expirou. |
| A05 | Permitido | Admin ativo do projeto P solicita exportação com aprovação que vence às 12:00:01 UTC de 10/10/2026. Às 12:00:00 UTC ela ainda está válida, satisfazendo os requisitos de exportação. |
| A06 | Permitido | Suporte ativo do projeto X solicita leitura e tem chamado emergencial aberto associado ao recurso. Satisfaz a exceção E1, que permite essa leitura mesmo a usuário de outro projeto. |
| A07 | Negado | Suporte suspenso do projeto X solicita leitura com chamado emergencial aberto. Suspensão bloqueia qualquer ação, inclusive acesso emergencial; E1 exige usuário ativo. |
| A08 | Negado | Suporte ativo do projeto X solicita exportação com chamado emergencial aberto. E1 só cobre leitura, não exportação. O usuário também não possui o papel admin exigido, e o projeto X não recebe acesso de exportação ao projeto P. O pedido não informa aprovação do titular; nenhuma foi presumida. |
| A09 | Permitido | Leitor ativo do projeto P solicita leitura de recurso bloqueado. A política mantém permitida a leitura de recurso bloqueado. |
| A10 | Permitido | Editor ativo do projeto P solicita escrita em recurso desbloqueado. Satisfaz os requisitos de papel, projeto, estado do usuário e desbloqueio. |
| A11 | Negado | Admin ativo do projeto X solicita leitura sem chamado emergencial. A regra geral nega usuários de outro projeto. O papel admin não oferece exceção; E1 exige suporte e chamado emergencial aberto associado ao recurso. |
| A12 | Negado | Admin ativo do projeto P solicita exportação sem aprovação do titular. A política exige aprovação ainda válida e determina que ausência de aprovação equivale a não. |
| A13 | Negado | Suporte ativo do projeto X solicita leitura com chamado emergencial encerrado. E1 exige chamado aberto; sem essa condição, prevalece a negativa a usuários de outro projeto. |
| A14 | Negado | Editor ativo do projeto P solicita exportação com aprovação que vence amanhã. Ainda que a aprovação esteja válida no instante avaliado, exportação exige papel admin, que o usuário não possui. |
| A15 | Permitido | Suporte ativo do projeto P solicita leitura sem chamado emergencial. A regra geral permite leitura a usuário ativo do próprio projeto; essa leitura não depende de E1 nem de chamado. |
| A16 | Negado | Leitor ativo do projeto P solicita escrita em recurso desbloqueado e possui aprovação de exportação válida. Escrita exige editor ou admin; a política afirma que aprovação de exportação não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** A04 e A05 diferem por um segundo. A validade exige que o vencimento seja posterior ao instante de avaliação; igualdade já significa expiração. A decisão de A05 não foi extrapolada para 12:00:01 UTC.
- **Emergência:** E1 autoriza A06 porque há suporte ativo, leitura e chamado emergencial aberto associado ao recurso. Não supera suspensão em A07, não cobre exportação em A08 e não aceita chamado encerrado em A13.
- **Bloqueio:** impede escrita em A02 e A03, inclusive por admin, mas permite leitura em A09.
- **Papel e aprovação:** os requisitos de exportação são cumulativos. A aprovação válida de A14 não substitui o papel admin; a de A16 não concede escrita. Também não concede acesso a outro projeto.
- **Leitura comum:** A15 não precisa de emergência porque o usuário está ativo e pertence ao projeto P. Em A11, ser admin não elimina a restrição entre projetos.
- **Limites da evidência:** foram usados somente os fatos fornecidos e a versão vigente da política. Não foram inventadas aprovações, chamados ou mudanças no estado dos usuários. As conclusões valem para o instante fixado, sem projeção para outros horários.
