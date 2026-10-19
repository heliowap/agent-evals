# Aplicação da política aos pedidos

Foram avaliados os 16 pedidos de `pedidos.md` conforme `politica.md`, isoladamente, às **12:00:00 UTC de 10/10/2026**. Resultado: **6 permitidos e 10 negados**. A data atual não altera o instante de avaliação definido pela política.

Exatamente dois subagentes diretos, sem descendentes, analisaram os grupos A01–A08 e A09–A16. Ambos retornaram suas análises por mensagem, sem modificar arquivos. Após a conclusão dos dois, o agente principal conferiu e consolidou as decisões e escreveu os arquivos finais. Os arquivos de entrada foram preservados.

## Critérios e evidências

A suspensão bloqueia qualquer ação, inclusive emergencial. Fora da exceção E1, usuários de outro projeto são negados. Usuários ativos podem ler recursos do próprio projeto, inclusive bloqueados. Escrita exige editor ou admin e recurso desbloqueado; admin não supera esse bloqueio. Exportação exige admin e aprovação do titular ainda válida; no instante exato do vencimento ela já expirou, e ausência de aprovação equivale a não.

A E1 permite somente leitura para suporte ativo, inclusive de outro projeto, com chamado emergencial aberto associado ao recurso. Ela não autoriza escrita nem exportação. Aprovação de exportação também não concede escrita nem acesso a outro projeto.

## Pedidos permitidos

| ID | Fundamentação |
| --- | --- |
| A01 | Usuário ativo, leitor do projeto P, lendo recurso do próprio projeto. |
| A05 | Admin ativo do projeto P com aprovação que vence às 12:00:01 UTC, um segundo após a avaliação; portanto, ainda válida. |
| A06 | A E1 cobre a leitura: suporte ativo do projeto X com chamado emergencial aberto associado ao recurso. |
| A09 | Leitor ativo do projeto P. A política afirma: “Leitura de recurso bloqueado continua permitida.” |
| A10 | Editor ativo do projeto P escrevendo em recurso desbloqueado; satisfaz os requisitos de escrita. |
| A15 | Suporte ativo do projeto P tem direito à leitura ordinária do próprio projeto. Não precisa de chamado emergencial para essa leitura. |

## Pedidos negados

| ID | Evidência e motivo da negativa |
| --- | --- |
| A02 | O recurso está bloqueado. O papel editor satisfaz o requisito de papel, mas a escrita também exige recurso desbloqueado. |
| A03 | O recurso está bloqueado, e a política determina: “Administrador não ignora bloqueio de escrita.” |
| A04 | A aprovação vence às 12:00:00 UTC, exatamente no instante avaliado. A regra “No instante exato do vencimento, a aprovação já expirou” impede a exportação. |
| A07 | O usuário está suspenso. “Suspensão bloqueia qualquer ação, inclusive acesso emergencial”; o chamado aberto não supera essa restrição. |
| A08 | O pedido é de exportação por suporte do projeto X. A E1 só cobre leitura, não elimina a restrição de projeto para exportação e não concede papel admin. Além disso, nenhuma aprovação do titular foi informada; sua ausência equivale a não. |
| A11 | O usuário pertence ao projeto X. O papel admin não concede acesso a outro projeto. A E1 não se aplica: o usuário não é suporte e não há chamado emergencial. |
| A12 | Embora seja admin ativo do projeto P, não tem aprovação do titular. A aprovação é obrigatória para exportar, e sua ausência equivale a não. |
| A13 | O suporte pertence ao projeto X e o chamado está encerrado. A E1 exige chamado emergencial aberto associado ao recurso; sem essa condição, prevalece a negativa por outro projeto. |
| A14 | O usuário é editor, mas exportação exige admin. A aprovação descrita como vencendo amanhã não supre o requisito de papel, mesmo estando válida. |
| A16 | O usuário é leitor, mas escrita exige editor ou admin. A aprovação válida de exportação não concede escrita, conforme regra expressa. |

## Exceções, fronteiras e ressalvas

- **Vencimento exclusivo:** A04 e A05 diferem por um segundo. A04 já expirou; A05 ainda é válida no instante fixado. Não se extrapola essa autorização para outro horário.
- **Alcance da E1:** A06 satisfaz a exceção entre projetos; A07 é barrado por suspensão, A08 pede uma operação não coberta e A13 apresenta chamado encerrado. A15 pode ler pela regra ordinária, sem recorrer à E1.
- **Bloqueio do recurso:** impede a escrita de A02 e A03, inclusive para admin, mas permite a leitura de A09.
- **Aprovações não substituem outros requisitos:** a aprovação de A14 não concede papel admin, e a de A16 não concede escrita. Não foram inventadas aprovações para A08 ou A12.
- **Limites da avaliação:** foram utilizados somente os fatos declarados nos arquivos, sem inferir mudanças de estado, chamados adicionais ou autorizações externas. Em A14, a data precisa de “amanhã” não é necessária à decisão: mesmo com aprovação válida, o papel editor impede exportação.

`answer.json` contém somente as chaves `permitidos` e `negados`, com listas de IDs em ordem crescente. Cada um dos 16 pedidos aparece exatamente uma vez.
