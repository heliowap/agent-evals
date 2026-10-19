# Comparativo dos modelos de revisão de código

As **28 configurações** abaixo produziram **112 revisões válidas**: duas PRs do Click, cada uma analisada uma vez em *Standards* e uma vez em *Spec* por configuração. Os quatro achados do [gabarito](grading-rubric.md) foram definidos antes das respostas. A coluna de falsos positivos vem da [readjudicação cega por caso](blind-rescore.json), detalhada na [revisão metodológica](methodology-review.md), e substitui as contagens históricas das rodadas. As respostas brutas estão no [índice](README.md).

| Modelo e rota | Esforço | Standards | Spec | Total | Falsos positivos¹ | Tempo² | Custo informado³ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-5.3-Flash (OpenRouter) | `high` | 2/2 | 0/2 | 2/4 | 2 | 190,43 s | US$ 0,00687 |
| GLM-5.3-Flash (OpenRouter) | `max` | 2/2 | 0/2 | 2/4 | 2 | 81,65 s | US$ 0,00715 |
| DeepSeek V4.1 Flash (OpenRouter) | `high` | 2/2 | 1/2 | 3/4 | 4 | 153,87 s | US$ 0,02240 |
| DeepSeek V4.1 Flash (OpenRouter) | `max` | 2/2 | 1/2 | 3/4 | 1 | 129,56 s | US$ 0,02894 |
| MiMo-V2.6-Flash Free (OpenCode) | padrão | 2/2 | 1/2 | 3/4 | 4 | 332,34 s | US$ 0* |
| Space Bunny Free (OpenCode) | `xhigh` | 2/2 | 0/2 | 2/4 | 5 | 78,70 s | US$ 0* |
| Space Bunny Free (OpenCode) | `max` | 2/2 | 0/2 | 2/4 | 6 | 88,51 s | US$ 0* |
| GPT-6 Luna (OAuth) | `high` | 2/2 | 1/2 | 3/4 | 1 | 77,88 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `high` | 2/2 | 1/2 | 3/4 | 0 | 61,22 s | US$ 0* |
| GPT-6 Luna (OAuth) | `xhigh` | 2/2 | 0/2 | 2/4 | 2 | 142,65 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `xhigh` | 2/2 | 0/2 | 2/4 | 2 | 81,14 s | US$ 0* |
| GPT-6 Luna (OAuth) | `max` | 2/2 | 1/2 | 3/4 | 1 | 162,18 s | US$ 0* |
| GPT-6 Luna Fast (OAuth) | `max` | 2/2 | 0/2 | 2/4 | 2 | 110,82 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `low` | 2/2 | 0/2 | 2/4 | 2 | 37,34 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `medium` | 2/2 | 0/2 | 2/4 | 3 | 38,60 s | US$ 0* |
| Gemini 3.8 Flash (`cli_proxy`) | `high` | 2/2 | 0/2 | 2/4 | 1 | 72,32 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 95,30 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `high` | 2/2 | 1/2 | 3/4 | 2 | 188,83 s | US$ 0* |
| SWE-2 (`cli_proxy`) | `max` | 2/2 | 1/2 | 3/4 | 1 | 360,47 s | US$ 0* |
| GPT-6 Sol (OAuth) | `low` | 2/2 | 0/2 | 2/4 | 1 | 37,80 s | US$ 0* |
| GPT-6 Sol (OAuth) | `medium` | 2/2 | 1/2 | 3/4 | 0 | 57,09 s | US$ 0* |
| **GPT-6 Sol (OAuth)** | **`high`** | **2/2** | **2/2** | **4/4** | **0** | **69,59 s** | **US$ 0*** |
| GPT-6 Sol (OAuth) | `xhigh` | 2/2 | 1/2 | 3/4 | 0 | 89,32 s | US$ 0* |
| GPT-6 Sol (OAuth) | `max` | 2/2 | 1/2 | 3/4 | 0 | 126,12 s | US$ 0* |
| Claude Opus 5.5 (OpenRouter) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 96,37 s | US$ 0,74146 |
| CPA Claude Opus 5.5 (`cli_proxy`) | `low` | 2/2 | 0/2 | 2/4 | 2 | 72,61 s | US$ 0* |
| CPA Claude Opus 5.5 (`cli_proxy`) | `medium` | 2/2 | 1/2 | 3/4 | 2 | 93,25 s | US$ 0* |
| CPA Claude Opus 5.5 (`cli_proxy`) | `high` | 2/2 | 1/2 | 3/4 | 2 | 104,06 s | US$ 0* |

¹ **Limite inferior** de alegações verificavelmente incorretas nas quatro respostas, adjudicadas separadamente dos acertos. As 28 linhas somam **52**, contra 30 da contagem histórica, que não foi aplicada de forma uniforme aos dois eixos. Zero significa que nenhum falso positivo foi confirmado, não que a resposta inteira tenha sido validada. Os achados válidos descobertos depois do gabarito não alteram a nota. Veja as [citações e casos limítrofes](blind-rescore.json).

² Soma das quatro durações individuais observadas, inclusive quando chamadas foram executadas em paralelo; não é o tempo de relógio da rodada. Houve **uma revisão válida por caso/eixo/configuração**; [tentativas excluídas](attempts/) não entram nas médias nem nas notas.

³ Custo das quatro revisões conforme registrado nas sessões, arredondado a cinco casas decimais. `US$ 0*` significa **zero informado**, não custo ou créditos efetivos comprovadamente nulos; os modelos chamados `Free` são as rotas explicitamente gratuitas. A chamada curta de conectividade e as tentativas malsucedidas não entram na tabela. O roteamento Fast do Luna não teve sua ativação efetiva comprovada.

**Leitura deste recorte:** Sol `high` foi a única configuração a acertar os quatro achados. Entre as rotas explicitamente gratuitas, MiMo obteve o maior escore (3/4). O [Muse Spark 1.3 Contributor](gemini-muse-evaluation.md) foi bloqueado antes das revisões e, por isso, não integra a tabela. Dois diffs do mesmo projeto, sem repetições, não sustentam um ranking geral de capacidade.
