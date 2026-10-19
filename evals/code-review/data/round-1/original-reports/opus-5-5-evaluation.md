# Claude Opus 5.5 `medium`: avaliação de revisão de código

> **Registro da rodada original.** Os acertos do gabarito, tempos e custos permanecem válidos. A contagem de falsos positivos e as comparações baseadas nela são históricas; consulte [comparison.md](comparison.md) e [blind-rescore.json](blind-rescore.json) para os valores readjudicados.

Foram concluídas **quatro revisões** com `openrouter/anthropic/claude-opus-5.5#medium`: dois [diffs públicos](fixture-research.md), cada um analisado separadamente nos eixos *Standards* e *Spec*. Os prompts e o [gabarito pré-definido](grading-rubric.md) são os mesmos das rodadas anteriores; o gabarito não foi enviado ao modelo. A exportação das quatro sessões confirmou o modelo e o esforço solicitados, o recebimento exato dos prompts e a ausência de chamadas de ferramentas. [Respostas e métricas por chamada](results-opus-5-5/) · [Adjudicação](opus-5-5-scores.json).

| Rota / esforço | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo somado¹ | Tokens nominais² | Custo informado³ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenRouter, `medium` | 2/2 | 1/2 | 1 | 96,37 s | 154.898 | US$ 0,7414582 |

¹ Soma de quatro durações individuais, desde a chamada ao OpenCode até a exportação da sessão; duas revisões foram executadas em paralelo. A mediana foi de aproximadamente 23,3 s por revisão. Cada caso/eixo foi executado **uma vez**.

² Soma aritmética dos contadores do OpenCode: **147.276** de entrada, **4.708** de saída e **2.914** de raciocínio. Foram informados **9.828 tokens de cache gravado** e nenhum de cache lido; o cache não foi somado novamente ao total nominal, que não deve ser tratado como contagem desduplicada de tokens faturáveis.

³ Soma dos custos das **quatro revisões concluídas** segundo as sessões do OpenRouter. A chamada curta de conectividade custou **US$ 0,1352766** adicionais e não entrou na tabela. O total informado para revisões e smoke test foi **US$ 0,8767348**. A tentativa anterior pela rota `cli_proxy` falhou antes de gerar revisão, com HTTP 400 exigindo Claude Code 2.1.280+; o executável local informou 2.1.283. Não alterei a instalação nem substituí o modelo por uma versão anterior.

## Qualidade das revisões

- **Standards: 2/2.** A resposta sobre a [PR #3773](https://github.com/pallets/click/pull/3773) identificou a ausência do teste de regressão exigido pelo template de PR. A resposta sobre a [PR #3868](https://github.com/pallets/click/pull/3868) localizou a expressão ternária proibida por `docs/contributing.md`.
- **Spec: 1/2.** Na PR #3773, o Opus explicou que `textwrap.TextWrapper.__init__` grava `break_on_hyphens=True` na instância, ocultando o `False` adicionado à classe; o defeito da especificação permanece. Na PR #3868, mencionou aspas internas e o fato de aspas literais permanecerem no argumento, mas **não identificou que `--arg="a b"` se divide em três tokens**. Pelo critério congelado, uma menção genérica a aspas, sem o efeito concreto da divisão, não ganha esse ponto.
- **Achado adicional fora do gabarito:** a resposta de *Spec* para a PR #3868 identificou que argumentos posteriores ao executável ainda podem perder barras invertidas quando o primeiro token não contém uma barra. Reproduzi o caso `code --wait C:\tmp\x` na função fixada. Isso testa apenas o parsing com `WIN=True` no macOS, não o lançamento real de um editor no Windows.
- **Falso positivo confirmado:** na resposta de *Standards* para a PR #3773, o Opus afirmou que a nova configuração altera a saída de `wrap_text` e se aplica a todos os usuários da classe. O atributo de instância permanece `True`, portanto essa mudança não tem o efeito alegado. A resposta de *Spec* tratou a possível ampliação de escopo como condicional; não a contei novamente.

As quatro respostas ultrapassaram o limite de **400 palavras** solicitado nos prompts (436 a 505 palavras). A nota de acerto não penaliza o comprimento, mas essa falta de aderência pode importar se a revisão precisar ser concisa.

## Leitura prática

O resultado de `medium` (**2/2 em Standards, 1/2 em Spec**) empata no gabarito com Luna `high` padrão e SWE-2 `high`; Opus e Luna tiveram um falso positivo confirmado cada após a conferência dos dois eixos, e SWE-2 `high` não teve nenhum confirmado. O Sol `high` foi o único nível avaliado até aqui a localizar os quatro achados pré-definidos. Os custos das rotas não são diretamente comparáveis: o OpenRouter informou dólares para o Opus, enquanto as sessões OAuth e `cli_proxy` anteriores registraram US$ 0 sem comprovar consumo nulo.

Dois diffs do mesmo projeto e uma execução por combinação não permitem generalizar taxa de acerto, custo ou velocidade. Como todos os materiais relevantes foram entregues nos prompts e o uso de ferramentas foi proibido, a avaliação não mede navegação no repositório nem a execução integral da `/code-review`.
