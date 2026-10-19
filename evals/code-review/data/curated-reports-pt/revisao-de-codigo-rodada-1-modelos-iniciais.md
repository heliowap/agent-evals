# Avaliação exploratória de modelos para revisão de código

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](revisao-de-codigo/relatorios-originais/evaluation.md). Os links e comandos desta versão acompanham a organização por tema.


> **Registro da rodada original.** Os acertos do gabarito, tempos e custos abaixo permanecem válidos. Para a contagem de falsos positivos, que foi readjudicada, consulte [comparison.md](revisao-de-codigo-rodada-1-comparacao.md) e [blind-rescore.json](revisao-de-codigo/blind-rescore.json); as conclusões de qualidade desta rodada anteriores à readjudicação são históricas.

Foram avaliadas 28 revisões independentes: dois [diffs públicos do Click](revisao-de-codigo/fixture-research.md), dois eixos da `/code-review` (*Standards* e *Spec*) e sete configurações. Os diffs, commits, trechos da especificação e regras do repositório foram congelados em [`revisao-de-codigo/fixtures.json`](revisao-de-codigo/fixtures.json). Todos os modelos receberam o mesmo prompt em cada combinação de caso e eixo; nenhuma resposta usou ferramentas. O [gabarito](revisao-de-codigo/grading-rubric.md) contém um achado verificável por caso e eixo, definido na pesquisa antes das respostas.

| Modelo / esforço | Standards | Spec | Outro bug confirmado¹ | Custo das 4 chamadas | Tempo somado² |
| --- | ---: | ---: | :---: | ---: | ---: |
| GLM-5.3-Flash `high` | 2/2 | 0/2 | sim | US$ 0,00687 | 190 s |
| GLM-5.3-Flash `max` | 2/2 | 0/2 | não | US$ 0,00715 | 82 s |
| DeepSeek V4.1 Flash `high` | 2/2 | 1/2 | sim | US$ 0,02240 | 154 s |
| DeepSeek V4.1 Flash `max` | 2/2 | 1/2 | sim | US$ 0,02894 | 130 s |
| MiMo-V2.6-Flash Free, padrão | 2/2 | 1/2 | sim | US$ 0 | 332 s |
| Space Bunny Free `xhigh` | 2/2 | 0/2 | sim | US$ 0 | 79 s |
| Space Bunny Free `max` | 2/2 | 0/2 | não | US$ 0 | 89 s |

¹ Achado **posterior ao gabarito**: `code.cmd C:\src\a.txt` vira `['code.cmd', 'C:srca.txt']` na função alterada pela [PR #3868](https://github.com/pallets/click/pull/3868). Cinco configurações apontaram a perda de barras invertidas em argumentos posteriores ao executável. É um defeito reproduzido, mas não foi somado ao escore pré-definido.

² Soma do tempo observado nas quatro chamadas concluídas por configuração, sujeita à carga e aos limites dos provedores. Houve uma tentativa de GLM `high` que retornou HTTP 429; ela foi [arquivada](revisao-de-codigo/attempts/click-3868/) e repetida com o mesmo prompt. O custo da tentativa malsucedida, US$ 0,00037, não entra na tabela. Os custos dos 28 resultados aproveitados somam US$ 0,06536; chamadas iniciais de conectividade também ficaram fora desse total.

### Tempo e tokens

Os tempos da tabela anterior são **somas das durações individuais**, não o tempo de relógio da avaliação completa: as revisões de Standards e Spec foram executadas em paralelo. A mediana por revisão foi de 35,3 s / 20,3 s para GLM `high/max`, 19,3 s / 32,2 s para DeepSeek `high/max`, 35,1 s para MiMo e 14,5 s / 22,2 s para Space Bunny `xhigh/max`. Uma chamada do MiMo levou 234,1 s e uma do DeepSeek `high`, 105,1 s; esta amostra não permite atribuir as diferenças de tempo apenas ao modelo.

| Modelo / esforço | Entrada | Saída | Raciocínio | Soma nominal³ | Cache lido / gravado |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLM `high` | 96.292 | 2.634 | 6.330 | 105.256 | 0 / 9.828 |
| GLM `max` | 96.295 | 2.473 | 8.682 | 107.450 | 0 / 9.828 |
| DeepSeek `high` | 97.757 | 2.593 | 8.275 | 108.625 | 1.536 / 9.828 |
| DeepSeek `max` | 98.199 | 2.485 | 19.174 | 119.858 | 1.152 / 9.828 |
| MiMo padrão | 91.568 | 2.470 | 12.749 | 106.787 | 16.640 / 0 |
| Space Bunny `xhigh` | 105.208 | 2.713 | 4.400 | 112.321 | 1.806 / 0 |
| Space Bunny `max` | 99.586 | 2.525 | 6.954 | 109.065 | 7.430 / 0 |
| **28 chamadas** | **684.905** | **17.893** | **66.564** | **769.362** | **28.564 / 39.312** |

³ Soma aritmética dos três contadores informados pelo OpenCode (`input + output + reasoning`); o cache é exibido separadamente para evitar somá-lo duas vezes. Não interprete essa soma como contagem desduplicada de tokens faturáveis. Os números incluem o contexto do agente e do protocolo, não somente os diffs.

## Standards

**Todos acertaram os dois achados pré-definidos.** Na [PR #3773](https://github.com/pallets/click/pull/3773), não foi adicionado o teste exigido pelo template de PR. Na [PR #3868](https://github.com/pallets/click/pull/3868), a expressão ternária nova contraria [`docs/contributing.md`](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38). Várias respostas também apontaram a ausência de uma entrada em `CHANGES.rst`, exigência expressa no template; ela não integrou os quatro achados pré-definidos. Os *code smells* do protocolo foram tratados como juízos, não como infrações automáticas.

## Spec

Na [PR #3773](https://github.com/pallets/click/pull/3773), DeepSeek (`high` e `max`) e MiMo identificaram a causa: o construtor de `textwrap.TextWrapper` grava `self.break_on_hyphens=True`, ocultando o novo atributo da classe. [Reproduzimos o exemplo do issue #3362](https://github.com/pallets/click/issues/3362) na revisão fixada; as opções continuam partidas. GLM e Space Bunny não identificaram essa causa em nenhum dos esforços testados.

Na PR #3868, **nenhuma configuração** apontou o achado pré-definido sobre aspas internas: `C:\tools\vim.exe --arg="a b"` produz três argumentos, embora a PR prometa respeitar aspas. O achado posterior da nota ¹, apontado por cinco configurações, demonstra que algumas respostas encontraram uma falha distinta e válida; ele permanece separado do escore inicial para evitar alterar o critério depois de ver os resultados. A reprodução exercitou apenas a função de parsing com `WIN=True` no macOS: não houve teste de lançamento real no Windows.

### Falsos positivos confirmados

**Todas as sete respostas de Spec para a PR #3773** também afirmaram que a mudança ampliou o comportamento para todo o texto formatado. Como o atributo novo é ineficaz, esse efeito global não ocorreu. Parte desse erro pode ter sido favorecida pela frase de escopo usada no trecho editorial do caso; a alegação de efeito continua incorreta, mas não deve ser generalizada para outros prompts. Space Bunny `max` ainda atribuiu ao `textwrap` um contrato inexistente de `__init_subclass__` e citou um caso de teste com barra final que não está no diff da PR #3868. [`revisao-de-codigo/scores.json`](revisao-de-codigo/scores.json) registra apenas um **limite inferior conservador** de falsos positivos evidentes, sem rotular automaticamente outros achados discutíveis como erros.

## Leitura prática e limites

Neste recorte, **DeepSeek V4.1 Flash `high`** oferece a melhor combinação paga: acertou o mesmo gabarito que `max` por um custo menor. **MiMo-V2.6-Flash Free** empatou no gabarito sem custo por chamada, mas levou mais tempo nas quatro rodadas. `max` não aumentou os acertos pré-definidos em GLM, DeepSeek nem Space Bunny; no caso de Space Bunny, `xhigh` encontrou o defeito adicional que `max` deixou passar. O modelo stealth é interessante como segunda opinião gratuita, não como único revisor para decisões importantes.

O esforço maior consumiu mais tokens de raciocínio sem elevar esse escore: GLM passou de **6,3 mil** (`high`) para **8,7 mil** (`max`); DeepSeek, de **8,3 mil** para **19,2 mil**; Space Bunny, de **4,4 mil** (`xhigh`) para **7,0 mil** (`max`). São totais das quatro chamadas, não uma medição controlada da capacidade ou da velocidade intrínseca dos modelos.

Esta é uma amostra pequena de **dois commits não mesclados do mesmo projeto**, sem repetições por configuração. O teste forneceu os materiais relevantes e proibiu ferramentas; portanto, mede análise de um contexto congelado, **não** a capacidade de descobrir issues, navegar pelo repositório ou executar a skill integralmente. GLM e DeepSeek foram chamados pelos [IDs fixos do OpenRouter](revisao-de-codigo/provider-metadata.json) em `high/max`, porque a rota do OpenCode Go devolveu HTTP 402. O MiMo gratuito não expõe variante de esforço; ele não permite a comparação solicitada entre `max` e o nível imediatamente anterior. Space Bunny Free foi testado em `xhigh/max`, sem pressupor a identidade permanente do modelo stealth.

Para auditar: [`revisao-de-codigo/results`](revisao-de-codigo/results/) contém prompt, resposta, ID realmente usado, tokens, duração e custo de cada chamada; [`revisao-de-codigo/benchmark.py`](revisao-de-codigo/benchmark.py) executa a matriz; [`revisao-de-codigo/summarize_results.py`](revisao-de-codigo/summarize_results.py) confere a cobertura das 28 respostas e resume as métricas.
