# GPT-6 Sol: avaliação de revisão de código

> **Registro da rodada original.** Os acertos do gabarito e tempos permanecem válidos. Para a contagem atual de falsos positivos, consulte [comparison.md](comparison.md) e [blind-rescore.json](blind-rescore.json); os exemplos limítrofes são explicados na [revisão metodológica](methodology-review.md).

Foram concluídas **20 revisões** via `openai/gpt-6-sol` com OAuth, nos níveis `low`, `medium`, `high`, `xhigh` e `max`, sem Fast. Cada nível recebeu os mesmos dois [diffs públicos](fixture-research.md) e prompts das rodadas anteriores; *Standards* e *Spec* foram executados em sessões separadas. O [gabarito](grading-rubric.md) foi fixado antes das respostas e não integrou os prompts. As exportações das 20 sessões confirmaram a variante solicitada, o texto exato do prompt e a ausência de chamadas de ferramentas. [Respostas e métricas por chamada](results-sol/) · [Adjudicação](sol-scores.json).

| Esforço | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo somado¹ | Tokens nominais² |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 2/2 | 0/2 | 1 | 37,80 s | 96.636 |
| `medium` | 2/2 | 1/2 | 0 | 57,09 s | 101.195 |
| `high` | 2/2 | **2/2** | 0 | 69,59 s | 95.334 |
| `xhigh` | 2/2 | 1/2 | 0 | 89,32 s | 99.255 |
| `max` | 2/2 | 1/2 | 0 | 126,12 s | 102.150 |

¹ Soma das quatro durações individuais por nível, desde a chamada ao OpenCode até a exportação da sessão. Houve até duas chamadas em paralelo, e cada combinação caso/eixo/nível foi executada **uma vez**. As medianas por revisão foram 9,21 s (`low`), 12,41 s (`medium`), 15,39 s (`high`), 17,52 s (`xhigh`) e 24,56 s (`max`). São tempos observados nesta rodada, não medidas estáveis da velocidade do modelo.

² Soma aritmética dos contadores `input + output + reasoning` informados pelo OpenCode. O cache é mostrado separadamente abaixo; esses totais não são uma medição desduplicada de tokens faturáveis.

## Achados e falsos positivos

Em *Standards*, os cinco níveis localizaram a falta de teste de regressão exigido para a [PR #3773](https://github.com/pallets/click/pull/3773) e a expressão ternária proibida na [PR #3868](https://github.com/pallets/click/pull/3868).

Em *Spec*, `medium`, `high`, `xhigh` e `max` explicaram por que a PR #3773 não corrige a quebra das opções: `textwrap.TextWrapper.__init__` atribui `True` à instância, ocultando o `break_on_hyphens = False` adicionado à classe. `low` deixou passar esse mecanismo e afirmou que a alteração já muda a quebra de hífens em todos os textos formatados; como o novo atributo não surte efeito, essa afirmação é um **falso positivo confirmado**.

Somente `high` identificou o outro achado pré-definido: na PR #3868, o ramo não POSIX retira aspas apenas quando envolvem o token inteiro, de modo que um argumento com aspas internas e espaços pode ser dividido incorretamente. Sua resposta localizou o ramo em `_termui_impl.py:691–703` e deu o exemplo `--config="C:\Program Files\editor config"`, cuja divisão reproduzi na revisão fixada. É a mesma causa do caso `--arg="a b"` do gabarito; os exemplos não precisam ser idênticos para pontuar o mecanismo. Os demais níveis apontaram falhas diferentes de preservação de barras invertidas, mantidas **fora do placar pré-definido**. As reproduções executaram apenas a função de parsing com `WIN=True` no macOS, sem testar o lançamento do editor no Windows.

Nenhum falso positivo adicional foi confirmado nas respostas de `medium` a `max`; esse número é um limite inferior conservador, não uma certificação de que todos os outros comentários sejam corretos ou relevantes.

## Tokens e custo

| Esforço | Entrada | Saída | Raciocínio | Cache lido | Cache gravado |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 95.352 | 1.013 | 271 | 7.936 | 0 |
| `medium` | 99.187 | 1.054 | 954 | 4.096 | 0 |
| `high` | 92.527 | 872 | 1.935 | 10.752 | 0 |
| `xhigh` | 95.601 | 990 | 2.664 | 7.680 | 0 |
| `max` | 96.629 | 1.032 | 4.489 | 6.656 | 0 |
| **20 chamadas** | **479.296** | **4.961** | **10.313** | **37.120** | **0** |

As sessões somaram **494.570 tokens nominais** e **379,92 s** de durações individuais. O campo de custo retornou **US$ 0** nas 20 chamadas OAuth, mas não houve extrato de créditos nem preço por chamada; esse registro **não comprova consumo nulo**.

## Comparação e limites

Nesta amostra, **`high` foi a melhor seleção do Sol**: acertou os quatro achados pré-definidos, sem falso positivo confirmado, e levou menos tempo somado que `xhigh` e `max`. Foi a **única seleção avaliada até aqui** a atingir 2/2 também em *Spec*; as melhores seleções anteriores ficaram em 1/2. O `high` do Sol levou 69,59 s nas quatro revisões, diante de 77,88 s do Luna `high` padrão e 188,83 s do SWE-2 `high`; as rotas, o momento de execução e as condições de serviço diferiram.

Dois diffs do mesmo projeto, uma execução por combinação e materiais relevantes fornecidos diretamente nos prompts não permitem inferir superioridade geral ou estabilidade da taxa de acerto. Esta avaliação mede a análise do contexto congelado, sem navegação no repositório, uso de ferramentas ou execução integral da `/code-review`.
