# Fast e metadados do tier no CLIProxyAPI

Leitura em 2026-10-11, sem rede, chamadas de modelo ou acesso a configurações e credenciais privadas. Checkout limpo: `633250c58de154300668f6bd87689d542dee7ae7`. Foram lidas as instruções do [AGENTS.md](~/VSCode/Lab/CLIProxyAPI/AGENTS.md).

## Evidência na fonte

- O executor Codex usa por padrão `https://chatgpt.com/backend-api/codex` e acrescenta `/responses`. Aplica a opção Fast antes de preparar o pedido HTTP: [codex_executor_execute.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_executor_execute.go:31). O caminho HTTP streaming faz o mesmo: [codex_executor_stream.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_executor_stream.go:74).
- `ApplyCodexFastServiceTier` escreve `service_tier="priority"` quando o sufixo inclui Fast e o modelo é elegível. A função separa Fast do esforço de raciocínio: [codex_fast.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/helps/codex_fast.go:10). O tradutor de Responses também preserva `priority` e normaliza `fast` para `priority`: [codex_openai-responses_request.go](~/VSCode/Lab/CLIProxyAPI/internal/translator/codex/openai/responses/codex_openai-responses_request.go:31).
- No OAuth, a fonte acrescenta `X-Codex-Routing-Hint: model=<modelo>;tier=<tier do corpo final>`. O comentário atribui esse formato ao cliente oficial Codex `rust-v0.155.0`. Ele diz que não está documentado se o backend exige esse header para conceder prioridade. Headers definidos pelo operador podem prevalecer: [codex_executor_request.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_executor_request.go:242). O WebSocket usa o corpo final e o mesmo helper: [codex_websockets_execute.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_websockets_execute.go:91).
- O tradutor de resposta Responses repassa os eventos upstream, com eventual preenchimento de `model` ausente. Não substitui `service_tier` por `default`; a saída não streaming extrai diretamente o objeto `response`: [codex_openai-responses_response.go](~/VSCode/Lab/CLIProxyAPI/internal/translator/codex/openai/responses/codex_openai-responses_response.go:15), [extração final](~/VSCode/Lab/CLIProxyAPI/internal/translator/codex/openai/responses/codex_openai-responses_response.go:87).
- Na tradução para Chat Completions, o helper retorna apenas um tier upstream não vazio; não fabrica `default`. O resultado copia esse valor: [codexResponseServiceTier](~/VSCode/Lab/CLIProxyAPI/internal/translator/codex/openai/chat-completions/codex_openai_response.go:801), [cópia na resposta](~/VSCode/Lab/CLIProxyAPI/internal/translator/codex/openai/chat-completions/codex_openai_response.go:441). A extração para telemetria também retorna vazio se nenhum tier consta da resposta: [usage_helpers.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/helps/usage_helpers.go:1266).
- Existe uma constante `DefaultServiceTier`, mantida para callers diretos do SDK e usos fora de OpenAI. Isso é um default interno de telemetria, distinto de reescrever o campo da resposta HTTP: [usage/manager.go](~/VSCode/Lab/CLIProxyAPI/sdk/cliproxy/usage/manager.go:15).
- Um teste de transporte envia Fast com corpo `priority` e header equivalente enquanto seu servidor simulado responde `service_tier="default"`: [codex_executor_routing_hint_test.go](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_executor_routing_hint_test.go:41), [casos Fast](~/VSCode/Lab/CLIProxyAPI/internal/runtime/executor/codex_executor_routing_hint_test.go:60). É um teste simulado de encaminhamento, não uma medição do serviço OpenAI.

## Interpretação e limites

Esta fonte comprova como o CLIProxyAPI solicita Fast e preserva o tier informado pelo upstream. Ela não comprova como o backend OAuth escolhe o processamento, nem demonstra que todas as respostas reais são `default`.

O campo `default` isolado não basta para concluir que a solicitação Fast foi ignorada quando a confiabilidade desse metadado no endpoint OAuth está em questão. Tampouco o corpo `priority` ou o header bastam para comprovar aceleração. Para o relatório, separar: **Fast solicitado**, **tier retornado pela resposta** e **velocidade medida em comparação controlada**. Não chamar o segundo campo de prova independente do tier efetivamente servido sem validar essa correspondência nessa rota.

O eval em questão usa OAuth nativo do OpenCode para os Sol. A implementação do CLIProxyAPI é evidência de um transporte relacionado, não prova de que os pedidos atuais do OpenCode passam por esse proxy ou enviam o mesmo header.

## Registros locais encontrados

O [documento de seleção de modelos](~/VSCode/Lab/CLIProxyAPI/docs/cursor-opencode-model-selection.md:12) registra que uma verificação com endpoint simulado confirmou o envio de `reasoning_effort=high` e `service_tier=priority` ao selecionar `fast-high` no OpenCode. Isso verifica a formação do pedido, sem medir o serviço real.

O histórico local contém estes commits:

- `b97f71da0cf0cadac8b565d02ef9f567e0a52c6e`, de 2026-09-23, acrescenta o routing hint usado pelo Codex nativo. O corpo do commit informa que antes o pedido traduzido levava priority apenas no corpo.
- `c2a3c00dbdf91e05b2d45f7d1385f6018afb6ffb`, de 2026-09-26, habilita Fast para GPT-6 Sol/Luna e preserva service_tier na conversão de Chat Completions para Codex.
- `8fbf152b5b4920fe85e35721e0c719d441934a66`, de 2026-10-02, corrige a extração de uso quando o objeto usage da resposta contém somente metadados de tier. Não relata ganho de velocidade.

A busca em documentação, exemplos, nomes de arquivos incluindo ignorados e mensagens dos commits relacionados não localizou resultados numéricos de um A/B de TPS entre Fast e padrão. Não foram inspecionados históricos globais de sessões, credenciais ou conteúdo privado de logs. Isso limita a busca; não demonstra que o usuário não realizou os benchmarks.

O usuário relata que Fast aumentou TPS em benchmarks anteriores enquanto as respostas continuaram informando default. Esse relato deve permanecer separado das evidências verificadas acima. O relatório do eval conserva o tier retornado como metadado observado, sem tratá-lo como reprovação da configuração Fast ou prova de ausência de aceleração.
