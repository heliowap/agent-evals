# Code-review benchmark — rodada 2 (comparação exploratória)

Versão de leitura publicada na raiz de `evals/`. [Original preservado para auditoria](revisao-de-codigo/round-2/revision-2/comparison.md). Os links e comandos desta versão acompanham a organização por tema.


**300/300 revisões válidas**: 25 configurações × 3 casos × 2 eixos × 2 execuções independentes. Uma sessão válida não torna todos os alvos comparáveis: o caso Axios / Standards omitiu do prompt a condição necessária para demonstrar a falha do teste. Os números abaixo preservam a adjudicação cega, mas **não sustentam uma nota geral de seis alvos**. Veja a [revisão metodológica](revisao-de-codigo-rodada-2-metodologia.md).

## Cobertura por caso e eixo

| Caso | Eixo | Alvo encontrado (bruto) | Alegações refutadas (brutas) | Menções extras verificadas | Não verificáveis |
| --- | --- | ---: | ---: | ---: | ---: |
| axios-10852 | spec | 42/50 | 0 | 47 | 7 |
| axios-10852 | standards | 10/50 | 1 | 53 | 0 |
| requests-6991 | spec | 47/50 | 1 | 23 | 11 |
| requests-6991 | standards | 47/50 | 4 | 34 | 1 |
| rust-161834 | spec | 39/50 | 4 | 62 | 21 |
| rust-161834 | standards | 48/50 | 0 | 0 | 10 |

**Atenção:** Axios / Standards (10/50) não é demonstrável só com o material recebido; Requests / Spec (47/50) diz respeito a uma chamada direta do helper, não a uma falha demonstrada de uma requisição normal.

## Configurações (contagens brutas; sem nota geral nem ranking)

| Configuração | Standards / 6* | Spec / 6† | Refutadas‡ | Extras§ | Inconclusivas | Mediana s [IQR] | Custo válido informado US$ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-6-luna#high` | 4/6 | 3/6 | 0 | 5 | 0 | 20,7 [16,9–24,2] | 0,00000 |
| `openai/gpt-6-luna-fast#high` | 4/6 | 5/6 | 0 | 5 | 0 | 13,4 [10,6–17,0] | 0,00000 |
| `openai/gpt-6-luna#xhigh` | 4/6 | 4/6 | 1 | 6 | 0 | 40,9 [32,8–72,0] | 0,00000 |
| `openai/gpt-6-luna-fast#xhigh` | 4/6 | 4/6 | 0 | 6 | 0 | 24,0 [19,1–34,1] | 0,00000 |
| `openai/gpt-6-luna#max` | 5/6 | 5/6 | 0 | 5 | 0 | 49,8 [36,9–62,7] | 0,00000 |
| `openai/gpt-6-luna-fast#max` | 4/6 | 5/6 | 0 | 4 | 0 | 31,8 [27,3–43,1] | 0,00000 |
| `openai/gpt-6-sol#low` | 5/6 | 6/6 | 0 | 6 | 0 | 9,7 [7,5–9,9] | 0,00000 |
| `openai/gpt-6-sol#medium` | 4/6 | 5/6 | 1 | 5 | 0 | 19,7 [16,8–24,7] | 0,00000 |
| `openai/gpt-6-sol#high` | 4/6 | 6/6 | 0 | 6 | 0 | 19,0 [16,3–26,0] | 0,00000 |
| `openai/gpt-6-sol#xhigh` | 5/6 | 6/6 | 0 | 9 | 0 | 27,4 [21,7–32,1] | 0,00000 |
| `openai/gpt-6-sol#max` | 4/6 | 6/6 | 0 | 7 | 0 | 46,3 [34,8–53,7] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#low` | 4/6 | 6/6 | 0 | 7 | 3 | 5,8 [4,9–7,6] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#medium` | 4/6 | 6/6 | 0 | 5 | 3 | 12,9 [10,3–17,2] | 0,00000 |
| `cli_proxy/gemini-3.8-flash#high` | 6/6 | 4/6 | 0 | 2 | 3 | 38,4 [18,6–43,7] | 0,00000 |
| `cli_proxy/devin/swe-2#medium` | 5/6 | 5/6 | 1 | 16 | 2 | 21,9 [19,5–26,9] | 0,00000 |
| `cli_proxy/devin/swe-2#high` | 5/6 | 5/6 | 1 | 12 | 5 | 47,2 [38,7–56,3] | 0,00000 |
| `cli_proxy/devin/swe-2#max` | 6/6 | 6/6 | 1 | 16 | 3 | 83,1 [68,6–90,3] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#low` | 4/6 | 6/6 | 0 | 17 | 6 | 16,4 [14,7–17,8] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#medium` | 4/6 | 6/6 | 0 | 15 | 3 | 19,2 [17,9–19,5] | 0,00000 |
| `cli_proxy/cpa-claude-opus-5-5#high` | 4/6 | 6/6 | 0 | 16 | 4 | 22,9 [21,4–23,4] | 0,00000 |
| `openrouter/z-ai/glm-5.3-flash#high` | 4/6 | 5/6 | 2 | 11 | 5 | 16,7 [12,8–20,3] | 0,01786 |
| `openrouter/z-ai/glm-5.3-flash#max` | 4/6 | 6/6 | 1 | 16 | 6 | 50,6 [37,7–62,3] | 0,05524 |
| `openrouter/deepseek/deepseek-v4.1-flash#high` | 4/6 | 6/6 | 1 | 10 | 2 | 37,4 [17,2–68,2] | 0,07152 |
| `openrouter/deepseek/deepseek-v4.1-flash#max` | 4/6 | 6/6 | 1 | 12 | 5 | 65,0 [36,3–114,5] | 0,21108 |
| `openrouter/xiaomi/mimo-v2.6-flash#none` | 0/6 | 0/6 | 0 | 0 | 0 | 6,7 [4,0–8,1] | 0,01195 |

- `*` Um dos três alvos de Standards, Axios, não é demonstrável pelo prompt: as contagens por modelo são históricas, não um escore comparável.
- `†` Requests / Spec registra o comportamento condicional de `build_digest_header()`, sem prova de regressão no fluxo normal.
- `‡` O total bruto inclui a alegação de `b0026`, cuja refutação depende de código omitido do prompt; não tratá-la como falso positivo confirmado.
- `§` As menções extras incluem alvos do outro eixo e observações factuais; não equivalem a defeitos inéditos.

## Limites e auditoria

- **0 células faltantes**; as 25 configurações têm dois resultados por caso/eixo, sem troca de rota.
- O prompt pediu menos de 400 palavras; pela contagem por espaços, **30/300 respostas têm 400 ou mais** (29 passam de 400; máximo 470). 24/36 respostas CPA Opus excedem esse limite. A execução não as excluiu; a extensão desigual também afeta a oportunidade de encontrar extras.
- **304 tentativas** arquivadas, inclusive 4 excluídas. Uma tentativa MiMo sem resposta final teve o custo conciliado, mas não virou revisão válida.
- **US$ 0,37721 informados pelo OpenRouter** em todas as tentativas dessa rota, inclusive excluídas; o valor não é o total da conta nem um limite de cobrança imposto pelo provedor.
- US$ 0 informado nas sessões OAuth e `cli_proxy` **não demonstra custo real nulo**. A rota Fast é a variante solicitada; não há prova independente de aceleração do serviço.
- Um alvo exige local, mecanismo e consequência no eixo correto. Extras foram classificados à parte; hipóteses não verificáveis não foram contadas como falsas, ressalvada a classificação contestada de `b0026`.
- Uma passagem cega por resposta, sem segundo adjudicador independente. Consulte [gabarito](revisao-de-codigo/round-2/revision-2/grading-rubric.md), [selo anterior à identificação](revisao-de-codigo/round-2/revision-2/blind-seal.json), [decisões](revisao-de-codigo/round-2/revision-2/adjudication.json) e [mapa](revisao-de-codigo/round-2/revision-2/blind-map.json). As [300 exportações sanitizadas](revisao-de-codigo/round-2/revision-2/session-evidence.json) permitem verificar novamente prompt, modelo/variante, agente, término, ausência de partes de ferramentas, resposta, tokens e custo informado; o raciocínio e o fluxo de eventos original do CLI não foram arquivados.
- São três PRs e duas repetições por célula; não compare numericamente com a rodada Click anterior. Esta amostra não mede o efeito causal dos novos prompts nem a execução integral da skill.
