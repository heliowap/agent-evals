# Aplicação da política do projeto P

A avaliação aplica exclusivamente `politica.md` aos pedidos de `pedidos.md`, individualmente, às **12:00:00 UTC de 10/10/2026**. O retrato de usuários é válido nesse instante. Resultado: **6 pedidos permitidos e 10 negados**. Os arquivos de entrada foram preservados.

## Decisões e evidências

| ID | Decisão | Evidência e fundamento na política |
| --- | --- | --- |
| A01 | Permitido | Usuário ativo, leitor do projeto P, solicita leitura de recurso próprio desbloqueado; atende à regra geral de leitura. |
| A02 | Negado | O recurso está bloqueado. Escrita exige recurso desbloqueado, mesmo para editor ativo do projeto P. |
| A03 | Negado | O recurso está bloqueado. A política declara expressamente que administrador não ignora bloqueio de escrita. |
| A04 | Negado | A aprovação vence às 12:00:00 UTC de 10/10/2026, exatamente no instante avaliado. Nesse instante ela já expirou, deixando de atender ao requisito de aprovação válida para exportação. |
| A05 | Permitido | Admin ativo do projeto P, com aprovação que vence às 12:00:01 UTC; a aprovação ainda é válida no instante avaliado. |
| A06 | Permitido | A exceção E1 autoriza leitura por suporte ativo do projeto X com chamado emergencial aberto associado ao recurso. Todos os requisitos da exceção estão presentes. |
| A07 | Negado | O usuário está suspenso. Suspensão bloqueia qualquer ação, inclusive acesso emergencial; o chamado aberto não supera essa regra. |
| A08 | Negado | O usuário é suporte do projeto X e solicita exportação. E1 só cobre leitura; não elimina a restrição de projeto para exportar. O papel suporte também não atende ao requisito de admin, e não consta aprovação do titular, cuja ausência equivale a não. |
| A09 | Permitido | Leitor ativo do projeto P pode ler recurso próprio bloqueado. A política mantém permitida a leitura de recurso bloqueado. |
| A10 | Permitido | Editor ativo do projeto P solicita escrita em recurso desbloqueado; atende aos requisitos de escrita. |
| A11 | Negado | Admin do projeto X solicita leitura de recurso de P. Usuários de outro projeto são negados; não há E1 aplicável, pois não é suporte nem há chamado emergencial aberto. |
| A12 | Negado | Não há aprovação do titular. Exportação exige aprovação ainda válida, e a política equipara ausência de aprovação a não. O papel admin, sozinho, não basta. |
| A13 | Negado | Suporte do projeto X tem chamado emergencial encerrado. E1 exige chamado aberto associado ao recurso; sem a exceção, prevalece a negativa a usuários de outro projeto. |
| A14 | Negado | O usuário é editor. Exportação exige admin, mesmo que a aprovação vença amanhã. Aprovação não substitui o papel exigido. |
| A15 | Permitido | Suporte ativo do projeto P solicita leitura de recurso próprio desbloqueado. A regra geral de leitura basta; não exige chamado emergencial. |
| A16 | Negado | O usuário é leitor. Escrita exige editor ou admin; recurso desbloqueado não dispensa esse requisito. A aprovação de exportação válida não concede escrita. |

## Exceções, fronteiras e ressalvas

- **Vencimento:** a validade é estrita. A04 já perdeu a aprovação no instante exato do vencimento; A05 ainda tem aprovação válida por vencer um segundo depois. A decisão de A05 não deve ser extrapolada para outro horário.
- **Emergência:** E1 permite A06, apesar de o usuário pertencer ao projeto X, por reunir suporte, estado ativo, leitura e chamado aberto associado ao recurso. A suspensão impede A07; a ação de exportar fica fora do alcance da exceção em A08; o chamado encerrado impede E1 em A13. Não foi presumida aprovação adicional para E1, pois a política não a exige.
- **Bloqueio:** impede escrita em A02 e A03, inclusive para admin, mas mantém a leitura permitida em A09.
- **Papel e aprovação:** a aprovação de exportação não substitui o papel admin em A14 nem concede escrita em A16. A ausência de aprovação foi tratada como negativa em A12 e A08, sem inventar autorizações.
- **Leitura comum:** A15 é permitido pela regra geral do próprio projeto, independentemente de chamado emergencial. O papel admin de A11 não concede acesso a outro projeto.
- **Expressão temporal:** não é necessário atribuir hora exata a “amanhã” em A14, pois o papel editor já impede exportação, independentemente da validade da aprovação.

Foram usados somente os dados locais fornecidos, sem consultas externas. Exatamente dois subagentes diretos, sem descendentes, analisaram respectivamente A01–A08 e A09–A16; o segundo também revisou as fronteiras do conjunto. Ambos retornaram suas análises por mensagem, sem alterar arquivos. Após a conclusão de ambos, o agente principal consolidou as decisões e escreveu os arquivos finais.
