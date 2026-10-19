# Rodada 2 do benchmark de revisão de código — desenho

Data: 26/09/2026
Estado: coleta e adjudicação concluídas em `round-2/revision-2/`; o relatório é **exploratório**, pois a auditoria posterior identificou [limites de validade](../../../round-2/revision-2/methodology-review.md) sem alterar os casos, prompts, gabarito ou decisões cegas.

## Objetivo e limite da inferência

Comparar a qualidade e o tempo observado de 25 configurações de modelos diante de prompts **em inglês**, inspirados nos dois eixos da `/code-review`. Cada modelo recebe o mesmo material fixado para um caso e um eixo, sem ferramentas. Esta rodada mede análise de contexto fornecido, não a execução integral da skill. O efeito causal da otimização dos prompts **não** será medido: casos e prompts mudam em relação à rodada anterior, e o prompt antigo não será executado nos casos novos.

Os 112 resultados da primeira rodada, inclusive falhas arquivadas e a readjudicação, permanecem intactos. A rodada 2 terá seus próprios casos, prompts, respostas, gabarito e relatório em `round-2/`; o `README.md` da raiz passará a apontar para ela. As notas de quatro pontos da rodada Click não serão comparadas numericamente às notas novas.

## Matriz e rotas

Há **25 configurações**, três casos, dois eixos e duas execuções independentes por célula: `25 × 3 × 2 × 2 = 300` revisões válidas como máximo planejado. As duas execuções usam sessões distintas e recebem prompts idênticos.

| Família e rota | Variantes | Total |
| --- | --- | ---: |
| GPT-6 Luna, OAuth da OpenAI | padrão e Fast, cada um em `high/xhigh/max` | 6 |
| GPT-6 Sol, OAuth da OpenAI | `low/medium/high/xhigh/max` | 5 |
| Gemini 3.8 Flash, `cli_proxy` | `low/medium/high` | 3 |
| SWE-2, `cli_proxy` | `medium/high/max` | 3 |
| CPA Claude Opus 5.5, `cli_proxy` | `low/medium/high` | 3 |
| GLM-5.3-Flash | `high/max` | 2 |
| DeepSeek V4.1 Flash | `high/max` | 2 |
| MiMo-V2.6-Flash, OpenRouter | padrão | 1 |

GLM e DeepSeek mantêm os IDs do OpenRouter já usados. A rota inicialmente planejada para MiMo era `opencode/mimo-v2.6-flash-free`, mas o preflight anterior às revisões recebeu HTTP 403 (`OpenCode's free tier can only be used from within OpenCode`), sem resposta nem tokens. A alternativa **fixada antes da primeira revisão** é `openrouter/xiaomi/mimo-v2.6-flash#none`, ao preço informado de US$ 0,14 por milhão de tokens de entrada e US$ 0,28 por milhão de saída; essa configuração também entra no teto de US$ 10 do OpenRouter. Os [manifestos preliminares](../../../round-2/manifest-v1-preflight.json) e [da segunda tentativa](../../../round-2/manifest-v2-preflight.json) foram arquivados, sem nenhuma revisão válida. Uma falha no decodificador depois da primeira resposta exigiu preservar o [manifesto original da execução](../../../round-2/manifest.json) e congelar outro [manifesto, da revisão 1](../../../round-2/revision-1/manifest.json), sem mudar casos, prompts, gabarito, matriz ou política de ferramentas. Três sessões antigas foram revalidadas: duas preenchem células distintas; a terceira é uma tentativa excedente preservada, não uma repetição adicional. Não misturar rotas entre as duas execuções da mesma configuração. Space Bunny e Opus via OpenRouter ficam fora; Muse permanece bloqueado e não entra na matriz. Falha de rota após o congelamento não autoriza trocar modelo ou provedor silenciosamente.

Quando `opencode run` retornou sem ID de sessão para uma chamada MiMo, a revisão 1 preservou a tentativa excluída com custo desconhecido e pausou o OpenRouter. A exportação posterior encontrou **a sessão da mesma chamada**, com prompt, agente e rota fixados e custo informado de US$ 0,00106231; ela não tinha resposta final e **não** conta como revisão válida. Com aprovação do usuário, a [revisão 2](../../../round-2/revision-2/manifest.json) congelou o [registro do custo](../../../round-2/revision-2/cost-resolution.json) e a [exportação original](../../../round-2/revision-2/cost-evidence.json), revalidou e [copiou os resultados anteriores](../../../round-2/revision-2/migration.json) sem alterar os arquivos de origem. A pausa por custo desconhecido continua valendo para qualquer nova tentativa sem comprovação; o limite de US$ 10 segue baseado no custo **informado**, não é um bloqueio de cobrança da conta.

## Seleção e congelamento dos três casos

- Selecionar três PRs públicos de três repositórios distintos, preferencialmente com linguagens, tamanho de diff e tipos de defeito diferentes. Não reutilizar as duas PRs Click.
- Exigir commit base/head verificáveis, diff reproduzível, issue ou especificação de origem acessível na revisão, regra documentada de *Standards* vigente naquela revisão e contexto suficiente para seguir os caminhos afetados. Se uma PR não satisfizer isso, descartá-la **antes** de chamar modelos.
- Separar no material entregue ao modelo: pedido original, alegações do autor da PR, diff, contexto inalterado e regras do repositório. Usar trechos fiéis às fontes, sem uma interpretação editorial que insinue o defeito ou o esperado. Não incluir o gabarito nem testes de reprodução que revelem o achado-alvo.
- Antes de qualquer resposta, verificar os defeitos-alvo no código fixado e registrar no gabarito: requisito/regra, linha, mecanismo, reprodução ou prova, limites da prova e equivalências aceitáveis. Buscar alvos de dificuldade variada nos dois eixos; não depender apenas de ausência de testes ou changelog.
- Fixar também, antes da execução, versão e hash dos casos, das instruções em inglês, da matriz, dos critérios de pontuação e da ordem aleatória planejada. Após a primeira resposta, não modificar esses insumos; uma correção necessária cria uma versão de rodada distinta.

## Prompts em inglês

O material comum especificará revisão de **um único eixo**, commit e diff fixados, fontes, ausência de ferramentas e limite de concisão. O eixo *Standards* exigirá regra vigente e aplicável, local alterado, mecanismo e consequência; distinguirá regra de processo, convenção de código e *code smell* heurístico. O eixo *Spec* tratará o issue como objetivo e a descrição da PR como alegação sobre a solução; exigirá requisito, local, mecanismo e impacto. Em ambos:

- Relatar apenas achados sustentados; permitir explicitamente `No supported findings`.
- Examinar requisitos ausentes, comportamento errado e escopo indevido sem exigir que todas as categorias apareçam. Uma ausência de teste é falta de cobertura/evidência, não prova de que a correção falhou.
- Distinguir efeito atual confirmado, hipótese condicional e resultado não verificável com os materiais disponíveis. Não transformar uma hipótese de plataforma em falha demonstrada.
- Evitar citações inventadas; cada achado deve apontar sua fonte e trecho alterado. Quando um *code smell* não tiver custo concreto, omiti-lo.
- Usar o mesmo formato de achado, com localização, base da alegação, mecanismo e consequência; limitar a quantidade de achados fundamentados, sem preencher espaço com categorias vazias.

Os textos integrais em inglês e seus hashes serão registrados em `round-2/` antes das chamadas. A skill `/code-review` instalada não será alterada.

## Execução, integridade e custo

O executor terá IDs por caso/eixo/configuração/repetição e escrita retomável. Ele fechará o `stdin`, limitará a concorrência, registrará tentativas e só aceitará uma resposta se a sessão exportada confirmar **prompt exato, rota/modelo/esforço efetivos, resposta não vazia e ausência de ferramentas**. Excluir e preservar erros de API, respostas truncadas, prompts contaminados ou sessões sem confirmação; até duas tentativas por célula com o mesmo prompt, sem alterar o gabarito. A ordem de chamadas será embaralhada com semente registrada, para reduzir viés temporal entre configurações.

O custo informado pelo OpenRouter, inclusive preflight e tentativas malsucedidas faturadas, terá **teto de US$ 10**; o executor pausará ao alcançá-lo ou se não puder calcular o consumo informado com segurança. OAuth e `cli_proxy` podem registrar US$ 0 sem que o custo real seja nulo: registrar esse limite de observabilidade, sem estimar preço ou chamar essas rotas de gratuitas. Os tempos por chamada, mediana e dispersão por configuração serão exibidos; somas de durações não serão tratadas como tempo de relógio. A seleção Fast será anotada como solicitada, sem presumir aceleração efetiva.

## Pontuação e publicação

O gabarito fixado mede cobertura dos alvos conhecidos por eixo. Todo achado adicional será classificado separadamente como **válido verificado**, **refutado por evidência**, **não verificável** ou **opinião/estilo**, com citação da resposta e justificativa; a mesma alegação repetida numa resposta conta uma vez, e respostas independentes contam separadamente. Uma omissão não é falso positivo. Achados posteriores não alteram os alvos predefinidos. As respostas serão embaralhadas e desidentificadas por caso para adjudicação; pontos limítrofes serão expostos e as decisões vinculadas às respostas originais. Não alegar dupla avaliação independente se ela não ocorrer.

Publicar cobertura de alvos, alegações falsas verificadas, achados válidos adicionais, inconclusivos, duração e custo informado em colunas separadas. Não criar uma nota única de qualidade/velocidade com pesos decididos após as respostas; apresentar a fronteira de trocas e indicar a pequena amostra. Se casos, rotas, custo ou integridade impedirem as 300 revisões válidas, publicar o estado parcial e as combinações faltantes, sem preencher lacunas por suposição.

## Critérios de aceite

1. Três casos de três repositórios e a régua estão arquivados e verificados antes da primeira revisão.
2. Manifesto das 25 configurações, hashes dos prompts em inglês e 300 IDs de célula são gerados antes de executar; os testes locais do executor validam cobertura, retomada e rejeição de sessão contaminada.
3. Cada resposta considerada válida tem uma sessão auditável com prompt, modelo, esforço, tempo e custo informado; falhas e tentativas excluídas ficam separadas.
4. A adjudicação não transforma afirmações não demonstradas em falsas e não reclassifica novos bugs como alvos predefinidos.
5. Relatório e `README.md` apresentam a rodada 2 separada da rodada Click, sem afirmar vitória geral ou custos reais não medidos.
