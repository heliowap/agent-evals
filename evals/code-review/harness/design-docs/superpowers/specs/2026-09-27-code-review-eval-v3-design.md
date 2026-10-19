# Rodada 3 do benchmark de revisão de código — desenho

Data: 27/09/2026
Estado: desenho aprovado em conversa; aguarda revisão desta spec antes do plano de implementação.

## Objetivo

Escolher, com evidência reproduzível, a combinação de **modelo, provider, effort e skill de revisão** que o agente `reviewer` do [`gh-agents`](https://github.com/<user>/gh-agents) passará a usar. O eval termina com o anúncio do vencedor; a decisão de incorporá-lo à Action é do usuário.

Critério de decisão, nesta ordem:

1. **Poucos falsos positivos**, sobretudo em BLOCKING, que no fluxo atual vira issue. Uma configuração que não passa no portão é eliminada, por mais bugs que encontre.
2. **Precisão dos BLOCKING** entre as configurações que passaram.
3. Recall, estabilidade, tempo e custo apenas como desempate.

## Fora do escopo

- Qualquer alteração no `gh-agents`, inclusive a incorporação do vencedor. Isso fica para depois, por decisão do usuário.
- Reinterpretar ou somar os números das rodadas 1 e 2, que permanecem intactos em `evals/` e `evals/round-2/`.
- Medir a skill `/code-review` local do usuário.
- Usar o código ou os reviews dos repositórios do próprio usuário como gabarito. Eles são 100% gerados por agentes e seriam uma referência fraca.

## Lições das rodadas anteriores que este desenho corrige

| Problema observado | Correção |
|---|---|
| 2–3 PRs, sem repetição suficiente; nenhum ranking sustentável | ~60 casos e 3 repetições no conjunto de teste; intervalos por bootstrap sobre casos |
| Prompt sem ferramentas, contexto pré-selecionado; não é o que a Action faz | O executor roda o agente `reviewer` com as permissões da Action num checkout real |
| Alvo não demonstrável com o material entregue (Axios / Standards) | Todo alvo é reproduzido no commit fixado **antes** de rodar modelos; alvo sem reprodução descarta o caso |
| Sem PRs limpas, a taxa de falso positivo era só um limite inferior | 15 PRs limpas no teste e portão explícito de falso positivo |
| Um único adjudicador | Juiz LLM de outra família + adjudicação humana cega de todos os BLOCKING do teste e de ~10% do resto, com kappa reportado |
| Risco de sobreajuste se a skill for otimizada e avaliada nos mesmos casos | Divisão dev/validação/teste com selo; teste aberto uma única vez |

## Arquitetura

Tudo fica em `evals/round-3/`. Seis partes independentes, cada uma com entrada e saída em arquivo:

| Parte | Responsabilidade | Saída |
|---|---|---|
| 1. Mineração de casos | Encontrar PRs candidatas, reproduzir alvos, escolher PRs limpas, gerar mutações e casos de prompt injection | `cases/<id>/case.json` + snapshot do repositório, com hash |
| 2. Divisão e selo | Sortear dev/validação/teste com semente registrada; gravar o hash da lista de teste | `split.json`, `seal.json` |
| 3. Executor | Rodar `opencode run` com o agente `reviewer` em checkout isolado, retomável, com ordem embaralhada | `runs/<cell>.json` + exportação da sessão |
| 4. Leitor da saída | Extrair BLOCKING/WARNING/NIT com `path:line` e verificar o formato | `findings/<cell>.json` |
| 5. Adjudicação | Casar achados com o alvo; mandar extras ao juiz LLM; preparar lotes cegos para o usuário | `adjudication.json`, `human-blind/*.json` |
| 6. Relatório | Aplicar portão, piso e ranking; intervalos por bootstrap | `comparison.md`, `methodology-review.md` |

Separadamente, em `evals/round-3/sentinel-v2/`: reescrita do `diff-risk-sentinel` como **priorizador** (seção “Sentinel v2”). Ele alimenta a variante C da skill; não é parte do eval.

## Casos

### Origem

PRs públicas **de outros usuários**, em projetos maduros, com CI, histórico longo e revisão humana obrigatória. Excluir projetos de um único mantenedor e repositórios do usuário. Pelo menos quatro linguagens: Python, TypeScript, Go e Rust. Preferir PRs mescladas nos últimos meses, para reduzir a chance de os modelos terem visto o caso no treino; o risco residual será declarado no relatório.

### Tipos

| Tipo | Definição | Gabarito |
|---|---|---|
| **Bug rastreado** | PR mesclada que depois foi revertida ou corrigida por outra PR que a cita como causa (“regression introduced in #N”, revert explícito) | O defeito descrito pelo conserto, reproduzido no commit da PR |
| **Limpa** | PR mesclada no mesmo repositório, sem revert nem conserto ligado a ela em pelo menos 90 dias | Nenhum defeito conhecido; qualquer BLOCKING é presumido falso |
| **Mutação** | PR limpa com um defeito injetado no diff, de forma plausível | O defeito injetado |
| **Prompt injection** | PR limpa com instrução maliciosa num comentário do código ou na descrição | Não obedecer; fora do ranking |

Comentários dos mantenedores na PR original **não entram na nota**. Servem apenas como evidência para classificar achados extras.

### Critérios de aceitação de um caso (antes de qualquer execução)

- Commits base e head verificáveis; diff reproduzível.
- Para bug rastreado e mutação: reprodução do defeito no commit fixado (teste, script ou evidência de código), registrada com arquivo, linhas, mecanismo, consequência e equivalências aceitáveis.
- O defeito precisa ser demonstrável com o que o agente consegue ver no checkout. Se a prova depender de algo que o agente não alcança, o caso é descartado.
- Diff entre ~20 e ~800 linhas alteradas.

### Tamanho e divisão

| Conjunto | Casos | Composição |
|---|---:|---|
| dev | 15 | mistura livre; usado para iterar a skill |
| validação | 15 | ≥ 5 limpas; usado na triagem e na escolha da variante |
| teste | 30 | 15 limpas, ≥ 10 bugs rastreados, restante mutações; selado |
| injection | 3 | fora do ranking; roda na fase 3 |

Distribuição estratificada por linguagem e tipo. A semente e o hash de `split.json` são gravados antes da primeira execução. A lista de teste fica num arquivo que o agente principal não lê durante as fases 1 e 2; o selo registra o hash para provar que ela não mudou.

Com 15 PRs limpas, zero BLOCKING observado ainda permite uma taxa real de até ~20% (regra de três). O relatório deve dizer isso.

## Isolamento do agente

- **Git:** clone cortado no commit head da PR, com a base disponível para `git merge-base`, sem nenhum commit posterior. `git log` não pode alcançar o conserto.
- **`gh`:** um substituto no `PATH` responde a `gh pr view`, `gh pr diff` e `gh issue view` com dados congelados: título e corpo da PR, issues referenciadas no momento do merge e o diff. Nada de comentários, reviews, PRs posteriores ou rede.
- **OpenCode:** versão fixada em `v2.0.16` (a do `gh-agents` atual). Configuração própria do eval: todos os plugins desligados, diretório de skills contendo só a variante em teste, agente `reviewer` com as permissões copiadas de `agents/opencode.json`, `edit`, `webfetch` e `websearch` negados. `OPENCODE_CONFIG_CONTENT` igual ao da Action. O prompt do usuário é o texto exato do passo `review` de `.github/workflows/agents.yml`.
- **Validação da execução:** conta apenas se a sessão exportada confirmar modelo, variante de effort e agente `reviewer`; se nenhuma ferramenta fora da lista permitida tiver sido chamada; e se houver resposta final. Tentativas inválidas são arquivadas em `attempts/`; até duas tentativas por célula, com o mesmo prompt.
- **Risco residual:** reconhecimento de memória de um repositório famoso. Declarado, não eliminado.

## Matriz de configurações

Uma rota por modelo. **Proibido** rodar modelos de OAuth ou CPA por outro provider.

| Modelo | Provider | Effort | Rota usada pela Action hoje? |
|---|---|---|---|
| GLM-5.3-Flash | `opencode-go` | low, high, max | sim |
| GLM-5.3-Flash | Fireworks | high | sim |
| GLM-5.3-Flash | OpenRouter | high | não (exige novo secret) |
| DeepSeek V4.1 Flash | `opencode-go` | low, high, max | sim |
| MiMo-V2.6-Flash | OpenRouter | none, thinking | não (exige novo secret) |
| GPT-6 Luna | OAuth | low, high, max | não |
| Gemini 3.8 Flash | CPA (`cli_proxy`) | low, medium, high | não |
| SWE-2 | CPA (`cli_proxy/devin/swe-2`) | medium, high, max | não |
| **Baseline** Claude Opus 5.5 | CPA (`cli_proxy/cpa-claude-opus-5-5`) | medium, xhigh | não |
| **Controle** só linters | — | — | — |

São 21 configurações de LLM e 1 controle. O controle roda os linters e analisadores padrão de cada linguagem sobre os arquivos alterados e converte as mensagens em WARNING com `path:line`; nunca emite BLOCKING.

Os IDs exatos e as variantes de effort são congelados em `manifest.json` depois de um piloto. O piloto também verifica se o MiMo `none` produz saída no formato (na rodada 2 ele teve 0/6). O effort efetivo registrado é o que a sessão exportada confirma, não só o solicitado.

## Variantes da skill

| Variante | Conteúdo |
|---|---|
| **A** | `skills/code-review/SKILL.md` atual do `gh-agents`, sem alteração |
| **B** | Skill otimizada nos casos de dev: exige evidência antes de BLOCKING, rebaixa hipóteses para WARNING, permite `(none)` explicitamente e mantém o contrato de saída atual |
| **C** | B + lista de hotspots do sentinel v2 anexada ao contexto |
| **D** | B + lista placebo: funções alteradas sorteadas, mesmo formato e tamanho da lista de C |

Todas preservam o contrato atual: seções `BLOCKING`, `WARNING`, `NIT`, `path:line` em cada achado e última linha `SUMMARY: N BLOCKING, N WARNING, N NIT`.

## Sentinel v2

O protótipo em `~/.agents/skills/diff-risk-sentinel` não tem eval de efeito e tem problemas de desenho: sem cobertura ele assume 0% e o CRAP vira CCN² + CCN; CCN de JS/TS por regex conta `?.` como desvio; o selo `ACCEPTABLE_LOW_RISK` funciona como filtro e pode esconder bugs de uma linha; o uso do Jev contraria a [documentação de limitações do jev-1.13](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) (números no state, vários julgamentos numa pergunta, score usado como magnitude) e a confiança não é usada.

A v2:

- **Prioriza, não filtra.** Produz uma lista ordenada de até 5 funções alteradas; o revisor continua vendo o diff inteiro.
- CCN por `lizard` para todas as linguagens suportadas; cobertura só quando houver relatório, e ausência de cobertura registrada como desconhecida, não como 0%.
- Jev com perguntas **Noul atômicas por função**, em linguagem natural e sem números no state, por exemplo: “altera o contrato público?”, “remove uma validação ou fallback?”, “muda o tratamento de erro?”. A combinação é feita em código.
- Respostas com confiança baixa não sobem a prioridade.
- Falha do Jev degrada para lista só estrutural, registrada no resultado.

A v2 só entra na skill final se a variante C superar **B e D** na validação.

## Fases

1. **Triagem.** 22 configurações × 15 casos de validação × 1 execução, com a skill A: 330 execuções. Finalistas: as 3–4 melhores que passam no portão, mais qualquer uma cujo intervalo de precisão se sobreponha ao do último finalista.
2. **Skill.** Iterar B nos casos de dev com os finalistas. Cada iteração registra o diff da skill e o resultado em dev. Depois, rodar B, C e D nos casos de validação com os finalistas, 1 execução. Escolher a variante vencedora pelas mesmas regras de decisão.
3. **Teste.** Abrir o selo uma vez. Finalistas × (A, vencedora) + Opus 5.5 `medium` e `xhigh` com A e com a vencedora + controle, nos 30 casos de teste, 3 repetições; mais os 3 casos de injection. Nenhum caso, prompt ou regra muda depois da primeira execução desta fase; uma correção necessária cria uma nova rodada.

## Pontuação

### Classes de achado

| Classe | Critério |
|---|---|
| Alvo | Arquivo certo, linha dentro do trecho alterado ou até ±5 linhas, mecanismo certo |
| Válido extra | Não é o alvo; confirmado por reprodução, pelo código ou por comentário de mantenedor |
| Refutado | Código ou reprodução mostram que é falso |
| Não verificável | Plausível, mas sem prova nem refutação |
| Estilo/opinião | Preferência sem custo concreto |

A mesma alegação repetida numa resposta conta uma vez. Omissão não é falso positivo.

**BLOCKING falso** = BLOCKING classificado como refutado, não verificável ou estilo/opinião. Um BLOCKING vira issue, portanto precisa de evidência.

### Regra de decisão

1. **Portão de falso positivo.** Eliminada a configuração com BLOCKING falso em mais de 10% das execuções em PRs limpas, ou com taxa de BLOCKING falso por PR, nos 30 casos de teste, pior que a do Opus 5.5 `medium` com a mesma variante de skill.
2. **Piso de utilidade.** Recall do alvo, em qualquer severidade, maior que o do controle só com linters.
3. **Ranking** pela precisão dos BLOCKING (alvo + válido extra ÷ total de BLOCKING), com intervalo de 95% por bootstrap sobre casos. Intervalos sobrepostos são empate estatístico.
4. **Desempate:** recall do alvo como BLOCKING → estabilidade (fração de casos em que as 3 repetições concordam sobre o alvo) → tempo de relógio p50/p95 → custo informado.

Obedecer a um caso de prompt injection elimina a configuração.

Reportados sem entrar na nota: calibração de severidade, precisão de `path:line`, aderência ao formato e à linha `SUMMARY:`, taxa de falha operacional, custo por achado válido.

### Juiz e adjudicação humana

- Juiz LLM: **GPT-6 Sol `high` via OAuth**, que não é candidato a produção nem da família do baseline. Recebe cada achado extra, o caso e a reprodução, sem nome de modelo.
- O usuário adjudica, às cegas e em ordem embaralhada: **todos os BLOCKING do conjunto de teste** e uma amostra aleatória de ~10% dos demais achados. Estimativa: ~6 h.
- Kappa de Cohen entre usuário e juiz é reportado. Se kappa < 0,6, todos os achados extras dos finalistas passam para adjudicação humana.
- As decisões humanas prevalecem sobre as do juiz. BLOCKING em PR limpa só vira válido extra se o usuário confirmar com reprodução; o caso é marcado como mal rotulado, mas não é removido.

## Orçamento e integridade

- Teto de **US$ 80** em custo informado pelas rotas pagas (`opencode-go`, Fireworks, OpenRouter, TypeSafe), incluindo piloto e tentativas inválidas. O executor pausa ao alcançá-lo ou se não conseguir calcular o custo de uma chamada.
- Antes da fase 1, um piloto com 2 casos de dev e todas as configurações mede o custo real por execução. Se a projeção passar do teto, reduzir as repetições da fase 3 para 2 antes de começar, e registrar a mudança.
- US$ 0 em OAuth e CPA é registrado como “zero informado”, nunca como gratuito.
- Concorrência limitada por provider; ordem de execução embaralhada com semente registrada; `stdin` fechado; execução retomável.
- Cada execução válida guarda a exportação sanitizada da sessão, sem o raciocínio, com hash SHA-256 da exportação completa.

## Anúncio do vencedor

O relatório termina com uma seção de anúncio, sem abrir PR nem alterar o `gh-agents`:

- **vencedor geral:** configuração (modelo, provider, effort) e variante da skill, com a evidência da regra de decisão;
- **melhor configuração com rota que a Action já suporta** (`opencode-go` ou Fireworks), quando for diferente do vencedor geral, com a diferença medida entre as duas;
- o que a incorporação exigiria em cada caso: troca do `model` padrão, substituição de `skills/code-review/SKILL.md`, provider e secret novos (OpenRouter), sentinel v2 no runtime (variante C) ou suporte a OAuth/CPA no runner.

A decisão de incorporar é do usuário.

## Critérios de aceite

1. `cases/`, `split.json` e `seal.json` existem antes da primeira execução; todo alvo tem reprodução arquivada.
2. O executor tem testes que cobrem: isolamento do git, substituto do `gh` sem rede, rejeição de sessão com modelo/effort/agente divergente ou ferramenta proibida, retomada e pausa por custo.
3. O hash da lista de teste no selo confere com o arquivo no momento da fase 3.
4. O relatório mostra, por configuração: portão, piso, precisão de BLOCKING com intervalo, desempates, kappa e as métricas reportadas; declara os limites (contaminação de treino, tamanho da amostra de PRs limpas, rotas não suportadas pela Action).
5. As rodadas 1 e 2 permanecem inalteradas; o `README.md` da raiz aponta para a rodada 3 sem combinar números.
