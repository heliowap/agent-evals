# CPA Claude Opus 5.5 via `cli_proxy`: avaliação de revisão de código

> **Registro da rodada original.** Os acertos do gabarito e tempos permanecem válidos. A coluna de falsos positivos e as comparações baseadas nela são históricas; consulte [comparison.md](comparison.md) e [blind-rescore.json](blind-rescore.json) para os valores readjudicados.

Foram concluídas **12 revisões** de `cli_proxy/cpa-claude-opus-5-5` em `low`, `medium` e `high`: dois [diffs públicos](fixture-research.md), cada um analisado separadamente nos eixos *Standards* e *Spec*. Cada caso/eixo/nível recebeu o mesmo prompt das rodadas anteriores; o [gabarito pré-definido](grading-rubric.md) não foi enviado ao modelo. As exportações confirmaram o modelo CPA, a variante solicitada, o recebimento exato dos prompts e a ausência de chamadas de ferramentas nas 12 sessões. [Respostas e métricas](results-opus-5-5-cli-proxy/) · [Adjudicação](opus-5-5-cli-proxy-scores.json).

| Esforço | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo somado¹ | Saída² | Custo informado³ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `low` | 2/2 | 0/2 | 2 | 72,61 s | 5.981 | US$ 0 |
| `medium` | 2/2 | 1/2 | 1 | 93,25 s | 8.340 | US$ 0 |
| `high` | 2/2 | 1/2 | 1 | 104,06 s | 9.543 | US$ 0 |

¹ Soma das quatro durações individuais por nível, incluindo chamada CLI e exportação; houve até duas revisões em paralelo. As medianas por revisão foram 16,48 s (`low`), 21,59 s (`medium`) e 23,91 s (`high`). Cada combinação foi executada **uma vez**.

² Tokens de saída informados pelo OpenCode, não tokens totais. O `cli_proxy` registrou **somente 4 tokens de entrada e zero de raciocínio em cada chamada**, embora cada prompt contenha os diffs e o protocolo de revisão. Também registrou cache de leitura e gravação em grande volume. Os contadores não oferecem uma medida simples e comparável de tokens totais nem provam ausência de raciocínio interno.

³ O OpenCode registrou US$ 0 nas 12 sessões. Sem fatura ou medição de créditos do serviço, isso **não demonstra gratuidade nem custo real zero**.

## Qualidade das revisões

- **Standards: 6/6.** Todos os níveis encontraram a ausência do teste de regressão na [PR #3773](https://github.com/pallets/click/pull/3773) e a expressão ternária proibida na [PR #3868](https://github.com/pallets/click/pull/3868).
- **Spec: 2/6.** `medium` e `high` explicaram por que a PR #3773 não corrige a quebra das opções: `textwrap.TextWrapper.__init__` define `break_on_hyphens=True` na instância, ocultando o `False` adicionado à classe. `low` não identificou essa causa. Nenhum nível apontou o achado pré-definido da PR #3868: `--arg="a b"` se divide em três tokens. `medium` e `high` mencionaram aspas internas mantidas nos tokens, mas não descreveram a divisão concreta exigida pelo gabarito.
- **Achado adicional, fora do placar:** os três níveis identificaram que barras invertidas em argumentos posteriores ao executável podem desaparecer quando o primeiro token não contém uma barra. A falha foi reproduzida na função de parsing da revisão fixada com `WIN=True` no macOS; isso não comprova comportamento de lançamento real no Windows.
- **Falsos positivos confirmados:** a resposta de *Standards* para a PR #3773 afirmou, nos três níveis, que o novo atributo já muda a formatação visível. Não muda: o atributo da instância mantém o valor `True`. A resposta de *Spec* em `low` também afirmou esse efeito global, perfazendo dois falsos positivos naquele nível. `medium` e `high` descreveram o possível efeito ampliado em *Spec* como condicional, sem receber outro falso positivo por isso. As contagens são limites inferiores conservadores.

As **12 respostas excederam o limite de 400 palavras** pedido nos prompts (de 408 a 535 palavras). Isso não alterou o escore, mas reduz a adequação para uma revisão que precisa ser concisa.

## Tokens, rota e limites

| Esforço | Entrada informada | Saída | Raciocínio informado | Cache lido | Cache gravado |
| --- | ---: | ---: | ---: | ---: | ---: |
| `low` | 16 | 5.981 | 0 | 19.292 | 144.875 |
| `medium` | 16 | 8.340 | 0 | 51.244 | 112.923 |
| `high` | 16 | 9.543 | 0 | 51.244 | 112.927 |
| **12 chamadas** | **48** | **23.864** | **0** | **121.780** | **370.725** |

Uma tentativa anterior de testar esta rota foi barrada por HTTP 400, com o erro `Claude Code 2.1.251 does not support this model; version 2.1.280 or newer is required`. Nesta rodada, **os três testes curtos de acesso responderam e as 12 revisões terminaram**, sem alteração feita por nós na configuração local. As causas da falha anterior e da recuperação não foram identificadas. A [rodada anterior de Opus 5.5 `medium` pelo OpenRouter](opus-5-5-evaluation.md) pertence a outro provedor: também acertou 2/2 em *Standards* e 1/2 em *Spec*, com pelo menos um falso positivo, mas esses dois resultados isolados não estabelecem equivalência entre rotas.

**Escolha entre os esforços CPA testados: `medium`.** Empatou com `high` em acertos e falsos positivos confirmados, com menor tempo somado e menos tokens de saída nesta rodada. Ambos ficaram abaixo do Sol `high` no gabarito (3/4 contra 4/4). Dois diffs do mesmo projeto, uma execução por combinação e fontes entregues diretamente nos prompts não permitem generalizar a taxa de acerto ou medir a capacidade de navegar no repositório e executar a `/code-review` integralmente.
