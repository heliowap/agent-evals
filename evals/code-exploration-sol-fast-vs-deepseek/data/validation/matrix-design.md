# Ampliação da matriz de exploração

Estado: implementação preparada. Verificação offline concluída, 49 testes Python e 7 testes do observador aprovados. Preflight nativo bloqueado por loopback EPERM antes de qualquer inferência.

Fases: conferir as rotas nativas, comparar os desenhos, ampliar o executor, verificar os registros e documentar os comandos.

O objetivo é comparar sete configurações no mesmo papel de explorador. A seleção Sol usa `openai/gpt-6.1-sol-fast#low`, com autenticação OAuth nativa. DeepSeek permanece na assinatura Go. Sonnet 5.5 low, medium e high e Opus 5.5 low e medium usam o protocolo Anthropic do CLIProxy.

A unidade de agenda é um bloco de caso e repetição com as sete configurações. Os seis casos e cinco repetições produzem 210 sessões, cada uma com uma mensagem do usuário e até 25 passos do agente. O relatório deve ler a matriz do congelamento da rodada, para preservar a interpretação do smoke anterior.

O checkpoint de execução é um smoke de sete sessões antes do piloto de 210. Uma falha de preparação interrompe a rodada. Erros de inferência, timeouts e respostas incorretas continuam visíveis. Nenhuma inferência concorrente é necessária.

## Escolha do desenho

O desenho A propõe uma tabela de configurações e um único plugin observador para todos os transportes. O desenho B conserva o proxy HTTP para Go e CLIProxy e acrescenta hooks para OAuth. Escolhido A: o OpenCode mantém autenticação, URLs, WebSocket e fallback HTTP. O executor não precisa administrar dois mecanismos de captura.

Do desenho B foram mantidos os controles sobre a correspondência entre cada chamada, sua identidade e seus metadados. O observador permite somente os campos de transporte necessários à medição. Não grava cabeçalhos, prompts, ferramentas ou tokens de autenticação.

O identificador selecionado e o modelo enviado são campos distintos. O catálogo nativo gera `gpt-6.1-sol-fast`, mas as chamadas usam `gpt-6.1-sol`. O esforço Anthropic fica em `output_config.effort`, enquanto OpenAI Responses usa `reasoning.effort` e Go usa `reasoning_effort`.

O plugin acompanha HTTP por passagem do stream, sem esperar a resposta inteira antes de entregá-la ao OpenCode. Frames WebSocket permanecem iguais. Todos os registros ficam fora do projeto visível ao agente. O hash do observador entra no congelamento.

## Fontes locais conferidas

- OpenCode `packages/core/src/models-dev.ts`: expansão dos modos em modelos selecionáveis.
- OpenCode `packages/core/src/plugin/provider/openai.ts`: OAuth, endpoint ChatGPT e WebSocket padrão.
- OpenCode `packages/core/src/session/model-request.ts`: hooks HTTP e WebSocket.
- OpenCode `packages/plugin/src/promise/session.ts`: contrato dos hooks.
- OpenCode `packages/core/src/plugin/module.ts`: carregamento de plugin local com `id` e `setup`.
- OpenCode `packages/core/src/variant.ts`: esforço e pensamento adaptativo Anthropic.

As fontes do smoke anterior foram verificadas contra seu congelamento e preservadas em `results/smoke/frozen-source`. Seus registros e relatórios permanecem históricos.
