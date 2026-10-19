# Segunda rodada de exploração

A rodada seleciona Sonnet 5.5 xhigh, Sol 6.1 medium com Fast nativo e Gemini 3.8 Flash medium e high. Os seis casos e cinco repetições produzem 120 sessões sequenciais. Aprovação completa exige resposta literal, JSON, evidências e projeto inalterado, conforme os corretores existentes.

## Escolha do desenho

Dois esboços independentes compararam um catálogo com tupla padrão e um catálogo derivado de grupos nomeados. O primeiro recebeu 10/10 e o segundo 9/10 na revisão, segundo preservação do padrão, seleção dos quatro modelos, rotas nativas, propriedade única das definições e tamanho da interface.

O desenho escolhido mantém as sete definições originais em `DEFAULT_CANDIDATES` e deriva `CANDIDATES` acrescentando as quatro novas. A seleção explícita usa o catálogo completo. Os defaults continuam produzindo 210 sessões. O relatório permanece associado ao inventário congelado de cada rodada.

O desenho de grupos nomeados acrescentaria um tipo e um resolvedor sem necessidade nesta rodada. Sua verificação de seleção não vazia, conhecida e sem duplicatas já pertence à fronteira da CLI e da agenda. Não foi necessário introduzir outra opção de seleção ou copiar o executor.

`Candidate` continua representando modelo selecionado, modelo enviado, esforço, protocolo, autenticação e rota. O princípio Model the Domain mantém essas informações no registro existente. O princípio Explain the Number exige verificar os parâmetros enviados e distinguir Fast solicitado de Fast confirmado antes de interpretar qualidade ou tempo.

## Rotas conferidas no código local

- Sonnet xhigh herda variantes Anthropic nativas e envia pensamento adaptativo com `output_config.effort=xhigh`.
- Sol usa `openai/gpt-6.1-sol-fast#medium`, OAuth nativo e wire model `gpt-6.1-sol`. O esforço enviado é medium e Fast solicita priority.
- Gemini reproduz a integração local `cli_proxy_google`, canonical Google, pacote OpenAI-compatible, `/chat/completions` e variantes explícitas `settings.reasoningEffort`. A credencial `cli_proxy` é remapeada para a integração privada.

Fontes lidas no checkout local `~/VSCode/Lab/opencode`: `packages/core/src/models-dev.ts`, `packages/core/src/variant.ts`, `packages/core/src/config/plugin/provider.ts`, `packages/ai/src/providers/openai-compatible.ts`, `packages/ai/src/protocols/openai-compatible-chat.ts`, `packages/ai/src/protocols/openai-chat.ts` e `packages/ai/src/protocols/anthropic-messages.ts`. A configuração Gemini foi conferida em `~/.config/opencode/opencode.jsonc`, sem copiar credenciais.

## Checkpoint de execução

A preparação depende da auditoria de modelos e de um servidor OpenCode privado. Um teste de bind local retornou EPERM neste ambiente. A tentativa real deve registrar esse bloqueio no preflight e nenhuma inferência pode ser tratada como executada antes de o servidor iniciar.

O trabalho de código usa um único proprietário para registro, seleção e testes. Os esboços têm arquivos separados; as sessões do benchmark continuam sequenciais. Estado, verificações e tentativa de execução ficam em [r2-work.json](r2-work.json).

## Estado verificado

Passaram 54 testes Python e 7 testes Node. A revisão independente não encontrou problemas no escopo. O verificador histórico reconferiu os 210 trials e 949 chamadas do piloto usando suas fontes congeladas. Os 33 relatórios publicados também passaram na conferência.

O [plano da segunda rodada](../plans/r2-xhigh-gemini/freeze.json) contém 120 sessões, 30 por configuração. A tentativa de `run` neste sandbox parou no [preflight](r2-sandbox-run/preflight.json), pois o servidor OpenCode privado não iniciou. Essa tentativa registra zero chamadas de inferência e não executou suas sessões. Os comandos para executar no terminal estão no [README](../README.md#executar-a-segunda-rodada).

O usuário executou posteriormente a rodada no terminal. As 120 tentativas terminaram, com 103 respostas concluídas e 17 erros fatais no Gemini. O verificador reconferiu 1.365 chamadas, os corretores e o relatório sem nova inferência. A tentativa no sandbox acima continua preservada como evidência distinta. Leia a [análise final](../results/pilot-r2-xhigh-gemini/analysis.md), que separa falha de integração, qualidade e limitações da observação.
