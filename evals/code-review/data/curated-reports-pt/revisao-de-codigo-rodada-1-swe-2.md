# SWE-2: avaliação de revisão de código

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](revisao-de-codigo/relatorios-originais/swe-2-evaluation.md). Os links e comandos desta versão acompanham a organização por tema.


> **Registro da rodada original.** Os acertos do gabarito e tempos permanecem válidos. A coluna de falsos positivos e as recomendações baseadas nela são históricas; consulte [comparison.md](revisao-de-codigo-rodada-1-comparacao.md) e [blind-rescore.json](revisao-de-codigo/blind-rescore.json) para os valores readjudicados.

Foram concluídas **12 revisões** de `cli_proxy/devin/swe-2` em `medium`, `high` e `max`. Cada nível recebeu os mesmos dois [diffs públicos](revisao-de-codigo/fixture-research.md) e prompts das rodadas anteriores, com *Standards* e *Spec* em sessões independentes. Pontuei as respostas com o mesmo [gabarito pré-definido](revisao-de-codigo/grading-rubric.md), que não foi mostrado ao modelo. As exportações confirmaram a variante solicitada, o prompt exato e a ausência de chamadas de ferramentas nas 12 sessões. [Respostas brutas](revisao-de-codigo/results-swe-2/) · [Adjudicação](revisao-de-codigo/swe-2-scores.json).

| Esforço | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo somado¹ | Tokens nominais² |
| --- | ---: | ---: | ---: | ---: | ---: |
| `medium` | 2/2 | 1/2 | 1 | 95,30 s | 106.665 |
| `high` | 2/2 | 1/2 | 0 | 188,83 s | 110.629 |
| `max` | 2/2 | 1/2 | 0 | 360,47 s | 118.696 |

¹ Soma de quatro durações por esforço, desde a chamada CLI até a exportação da sessão. Não é o tempo de relógio da avaliação, que executou até duas revisões em paralelo. A mediana por revisão foi de 25,39 s (`medium`), 41,66 s (`high`) e 94,73 s (`max`); há apenas **uma execução por caso/eixo/nível**.

² Soma aritmética dos contadores de entrada, saída e raciocínio do OpenCode, sem cache. A rota `cli_proxy` registrou **zero tokens de raciocínio em todos os níveis**, o que não demonstra ausência de raciocínio interno. Também registrou custo de US$ 0, sem informar o custo real do provedor. Nas 12 revisões, os contadores somaram **311.328 tokens de entrada e 24.662 de saída**: **335.990 tokens nominais** e **644,60 s** de durações individuais.

## Achados

Os três níveis localizaram os dois achados de *Standards*: o teste de regressão ausente na [PR #3773](https://github.com/pallets/click/pull/3773) e a expressão ternária proibida na [PR #3868](https://github.com/pallets/click/pull/3868). Em *Spec*, todos identificaram a causa concreta da correção ineficaz na PR #3773: o construtor de `textwrap.TextWrapper` cria `self.break_on_hyphens=True`, ocultando o atributo adicionado à classe. Nenhum encontrou o outro achado pré-definido, no qual aspas internas de `--arg="a b"` fazem o parser da PR #3868 produzir três argumentos.

No segundo diff, todos apontaram outro defeito verificável, **fora do gabarito**: uma barra invertida seguida de espaço faz a função cair no `shlex.split` em modo POSIX, que pode eliminar barras de um caminho do Windows. Reproduzi a transformação de `C:\dir\ app.exe` para `C:dir app.exe` na função fixada, sem afirmar que houve lançamento real no Windows.

Em `medium`, a resposta também afirmou que a alteração da PR #3773 mudou imediatamente a formatação dos demais textos. Esse é um falso positivo confirmado: o atributo novo não surte efeito. `high` e `max` descreveram a ampliação de escopo **como hipótese caso o conserto fosse tornado efetivo**, sem atribuir o efeito ao código atual; por isso não receberam esse falso positivo.

## Leitura prática

**`high` é a escolha mais equilibrada entre os três níveis testados:** preservou os mesmos acertos de `max`, sem falso positivo confirmado nesta amostra, com aproximadamente metade do tempo somado. `medium` terminou antes e teve o mesmo gabarito, mas fez uma afirmação incorreta a mais. `max` consumiu mais tempo e tokens sem localizar outro achado pré-definido.

SWE-2 `high` **empatou no gabarito** com Luna `high` padrão, DeepSeek V4.1 Flash `high` e MiMo gratuito (2/2 em *Standards*, 1/2 em *Spec*). Luna `high` padrão teve **um falso positivo confirmado** após a conferência dos dois eixos, contra nenhum confirmado para SWE-2 `high`, mas observou menor tempo somado (**77,88 s** contra **188,83 s**). As rotas e cargas dos provedores são diferentes; dois diffs do mesmo projeto e uma execução por configuração não sustentam uma superioridade geral entre modelos.
