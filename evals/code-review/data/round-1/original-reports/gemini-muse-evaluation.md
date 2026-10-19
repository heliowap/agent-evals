# Avaliação parcial — Gemini 3.8 Flash e Muse Spark 1.3 Contributor

> **Registro da rodada original.** Os acertos do gabarito, tempos e estado do Muse permanecem válidos. A coluna de falsos positivos é histórica; consulte [comparison.md](comparison.md) e [blind-rescore.json](blind-rescore.json) para os valores readjudicados.

O Gemini 3.8 Flash concluiu **12 revisões** pelo provedor `cli_proxy`, nos níveis `low`, `medium` e `high`. Usei os [dois diffs públicos](fixture-research.md), os prompts e o [gabarito](grading-rubric.md) das rodadas anteriores, com os eixos *Standards* e *Spec* independentes. As exportações das 12 sessões confirmaram os IDs e esforços solicitados, o recebimento exato dos prompts e **nenhuma chamada de ferramenta**. As respostas completas estão em [`results-gemini-muse/`](results-gemini-muse/), e a adjudicação manual em [`gemini-muse-scores.json`](gemini-muse-scores.json).

| Gemini via `cli_proxy` | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo somado¹ | Tokens nominais² |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 2/2 | 0/2 | 2 | 37,34 s | 113.611 |
| `medium` | 2/2 | 0/2 | 2 | 38,60 s | 115.378 |
| `high` | 2/2 | 0/2 | 1 | 72,32 s | 127.354 |

¹ Soma das quatro durações de cada nível, incluindo a chamada CLI e a exportação da sessão, não o tempo de relógio da rodada. Houve até duas execuções em paralelo e apenas uma execução por caso/eixo/nível; os tempos não caracterizam a velocidade estável do modelo.

² Soma aritmética de `input + output + reasoning` informada pelo OpenCode; cache à parte. Os contadores do `cli_proxy` requerem cautela: no nível `high`, **`output` foi zero nas quatro sessões apesar de haver respostas em texto**. Portanto, o total não serve como contagem exata de tokens produzidos nem como estimativa de custo. O campo de custo das sessões também veio como US$ 0, sem comprovar gratuidade da rota.

No primeiro diff, os três níveis apontaram a falta de testes em *Standards*, mas afirmaram em *Spec* que o novo atributo da classe altera a formatação de todos os textos. A reprodução mostra o contrário: `textwrap.TextWrapper.__init__` define `self.break_on_hyphens=True` em cada instância e a mudança é ineficaz. O nível `medium` ainda afirmou incorretamente que não seria possível passar `break_on_hyphens=True` ao construtor; isso também foi testado. No segundo diff, todos apontaram a expressão ternária proibida em *Standards* e encontraram uma falha adicional real na preservação de barras invertidas em argumentos posteriores ao executável. Nenhum descreveu o achado de *Spec* do gabarito — a divisão de `--arg="a b"` em três argumentos. O nível `high` mencionou aspas internas, mas sem identificar essa divisão concreta; por isso o gabarito não lhe atribui o ponto.

Uma primeira tentativa do Gemini foi **excluída**: o script que iniciava a rodada vazou pelo `stdin` herdado para os prompts e algumas sessões chamaram ferramentas. Preservei as nove respostas em [`attempts/gemini-stdin-leak-20260926/`](attempts/gemini-stdin-leak-20260926/) e repeti a rodada com `stdin` fechado; somente as 12 sessões verificadas compõem a tabela. No total aproveitado, o OpenCode informou **335.782 tokens de entrada, 4.503 de saída e 16.058 de raciocínio** — soma nominal de **356.343 tokens** e **148,26 s** de durações individuais.

## Muse Contributor: bloqueado antes da avaliação

O ID solicitado foi confirmado como `openrouter/meta/muse-spark-1.3-contributor`, com variantes `high`, `xhigh` e `max`. A chamada curta retornou `provider.invalid-request` (HTTP 404): o único endpoint disponível foi excluído pela política de privacidade da conta, que impede treinamento com dados enviados a modelos pagos. **Nenhuma das 12 revisões Muse foi executada.** A pedido do usuário, mantive a escolha pelo OpenRouter; não usei a rota gratuita nem alterei a política da conta. O teste só poderá continuar se o usuário decidir habilitar conscientemente essa opção em [OpenRouter → Privacy](https://openrouter.ai/settings/privacy) e avisar que concluiu a mudança.

Até lá, a comparação entre **Gemini e Muse** permanece inconclusiva. Contra o gabarito já usado para Luna, DeepSeek e MiMo, os três níveis do Gemini ficaram abaixo dos melhores resultados em *Spec* (0/2 contra 1/2), mas dois casos de um mesmo projeto não sustentam um ranking geral.
