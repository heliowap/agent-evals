# GPT-6 Luna: avaliação de revisão de código com e sem Fast

> **Registro da rodada original.** Os acertos do gabarito, tempos e custos permanecem válidos. A coluna de falsos positivos e as comparações baseadas nela refletem a contagem histórica; consulte [comparison.md](comparison.md) e [blind-rescore.json](blind-rescore.json) para os valores readjudicados.

Foram concluídas **24 revisões**, sem chamadas de ferramentas, via OAuth da OpenAI: seis seleções de modelo × dois [diffs públicos](fixture-research.md) × dois eixos do protocolo `/code-review`. Os prompts e o [gabarito](grading-rubric.md) são os mesmos da [rodada anterior](evaluation.md), e os IDs efetivamente usados foram conferidos nas sessões. As respostas completas, os prompts, os tokens e os tempos estão em [`results-luna/`](results-luna/); a adjudicação manual está em [`luna-scores.json`](luna-scores.json).

| Esforço | Seleção OAuth | Standards | Spec | Falsos positivos confirmados (mín.) | Tempo CLI¹ | Turnos do modelo¹ | Tokens nominais² |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high` | `openai/gpt-6-luna` | 2/2 | 1/2 | 1 | 77,88 s | 70,83 s | 106.296 |
| `high` | `openai/gpt-6-luna-fast` | 2/2 | 1/2 | 1 | 61,22 s | 54,94 s | 105.458 |
| `xhigh` | `openai/gpt-6-luna` | 2/2 | 0/2 | 2 | 142,65 s | 136,19 s | 106.049 |
| `xhigh` | `openai/gpt-6-luna-fast` | 2/2 | 0/2 | 2 | 81,14 s | 74,68 s | 108.715 |
| `max` | `openai/gpt-6-luna` | 2/2 | 1/2 | 1 | 162,18 s | 155,54 s | 107.318 |
| `max` | `openai/gpt-6-luna-fast` | 2/2 | 0/2 | 2 | 110,82 s | 104,05 s | 104.693 |

¹ Soma de quatro durações por seleção, não o tempo de relógio da avaliação: houve até duas chamadas em paralelo. “Tempo CLI” mede desde a chamada ao OpenCode até a exportação da sessão; “turnos” mede, na exportação, do início ao fim da mensagem do assistente, excluindo parte da preparação e da exportação. Cada combinação caso/eixo/seleção foi executada **uma vez**; tempo e qualidade podem variar entre execuções. O segundo caso de Spec concentrou os maiores tempos (até 85,87 s de CLI no `max` sem Fast).

² Soma dos contadores `input + output + reasoning` informados pelo OpenCode, não uma medida desduplicada de tokens faturáveis. O cache fica separado na tabela abaixo.

## Qualidade das revisões

- **Standards: 12/12.** As seis seleções apontaram a falta do teste exigido na [PR #3773](https://github.com/pallets/click/pull/3773) e a expressão ternária proibida pelas [regras do Click](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38) na [PR #3868](https://github.com/pallets/click/pull/3868).
- **Spec: 3/12 no gabarito pré-definido.** No primeiro diff, `high` com e sem Fast e `max` sem Fast perceberam que o atributo da classe é sobrescrito pelo construtor de `textwrap.TextWrapper`; `xhigh` e `max` com Fast deixaram passar. No segundo, **nenhuma** seleção apontou que aspas internas de `--arg="a b"` são quebradas em três argumentos.
- **Achados adicionais, fora do placar:** todas as seis respostas de Spec do segundo diff apontaram ao menos uma falha distinta e fundamentada, como perda de barras invertidas em argumentos posteriores ao executável ou resolução de `shutil.which` com um `PATH` diferente de `Editor.env`. A perda de barras e o desvio causado pela condição `"\\ "` foram reproduzidos na função da revisão fixada; isso **não** equivale a provar uma falha de lançamento real do Notepad no Windows.
- **Falsos positivos (adjudicação corrigida):** pelo menos quatro respostas de *Spec* e cinco de *Standards* para o primeiro diff afirmaram que a mudança já alterava a formatação de texto. Ela não teve esse efeito: o atributo de instância preserva o valor `True`. A resposta de *Spec* em `high` sem Fast descreveu o risco de forma condicional, mas sua resposta **separada de Standards** afirmou que o comportamento já mudara; ela conta como um falso positivo. A contagem anterior omitia esse e outros enunciados de *Standards*. O [prompt do caso](fixtures.json) trazia uma frase editorial sobre escopo capaz de favorecer esse erro. Cada contagem continua sendo um limite inferior de alegações refutadas.

No gabarito estrito, `high` **empatou com os melhores resultados** da rodada anterior em Spec (1/2) e acertou ambos os casos de Standards. `xhigh` não melhorou o resultado; `max` sem Fast empatou com `high`, usando mais tempo e tokens de raciocínio. O `max` selecionado como Fast perdeu o achado do primeiro diff. A amostra é pequena demais para concluir que aumentar esforço *causa* piora ou que um modelo é superior em geral.

O teste forneceu diff, especificação e regras no prompt. Não mediu a capacidade do agente de localizar fontes no repositório, executar testes ou conduzir o fluxo completo da skill; os dois casos também pertencem ao mesmo projeto.

## Tokens e custo

| Esforço / seleção | Entrada | Saída | Raciocínio | Cache lido | Cache gravado |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high` padrão | 103.293 | 817 | 2.186 | 0 | 0 |
| `high` Fast | 101.764 | 937 | 2.757 | 1.536 | 0 |
| `xhigh` padrão | 99.961 | 838 | 5.250 | 3.328 | 0 |
| `xhigh` Fast | 103.297 | 867 | 4.551 | 0 | 0 |
| `max` padrão | 98.680 | 1.588 | 7.050 | 4.608 | 0 |
| `max` Fast | 97.412 | 901 | 6.380 | 5.888 | 0 |
| **24 chamadas** | **604.407** | **5.948** | **28.174** | **15.360** | **0** |

**Total nominal:** 638.529 tokens e 635,89 s de durações individuais somadas. O OpenCode informou **US$ 0** em todas as sessões OAuth, mas isso **não** significa consumo zero de créditos ChatGPT. A [documentação da OpenAI](https://developers.openai.com/codex/speed) diz que o Fast para GPT-6 Luna consome **2,5×** os créditos da modalidade padrão onde disponível. Não obtivemos um extrato de créditos para calcular o custo real destas chamadas.

## O que “Fast” significa neste teste

O OAuth estava ativo (`opencode auth list` identificou `method: oauth`) e as sessões registraram `gpt-6-luna-fast` ou `gpt-6-luna` com o esforço solicitado. Em **todas as três comparações**, a seleção `-fast` terminou mais cedo na soma das quatro revisões; em **11 dos 12 pares caso/eixo** teve um turno menor. Como os textos gerados, os tokens de raciocínio e as condições de serviço diferiram, isso **não comprova** aceleração da rota. Há um [relato ainda aberto no OpenCode](https://github.com/anomalyco/opencode/issues/39864) de seleções OAuth `-fast` que enviam `service_tier: priority` sem obter a aceleração efetiva; a [proposta de correção](https://github.com/anomalyco/opencode/pull/39882) foi fechada sem merge. Esse relato testou outra versão/modelo e não prova que a instalação atual sofre do mesmo problema, mas impede que o sufixo `-fast` seja tomado como verificação independente da rota.

**Escolha provisória para estes casos:** `high` padrão, que encontrou o defeito do primeiro diff com menor tempo somado que `max` padrão. A seleção Fast `high` deu a mesma nota e foi mais rápida nesta rodada; antes de pagar o possível multiplicador de créditos, seria preciso confirmar o roteamento Fast com um teste controlado na conta, preferencialmente no Codex oficial. Nenhuma das seis seleções substitui revisão humana nos dois casos.
