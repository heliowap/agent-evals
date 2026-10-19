# Comparação de exploradores no OpenCode

O executor compara sete configurações no mesmo papel de exploração de código. Mede correção da resposta, evidências e tempo de conclusão. A ampliação está preparada. O smoke histórico de duas configurações usou Sol pelo CLIProxy e não comprova o resultado da nova rota OAuth.

| Configuração | Seleção OpenCode | Esforço | Autenticação e rota |
|---|---|---|---|
| `sol-fast-low` | `openai/gpt-6.1-sol-fast#low` | low com Fast nativo | OAuth OpenCode, ChatGPT |
| `deepseek-max` | `opencode-go/deepseek-v4.1-flash#max` | max | Assinatura OpenCode Go |
| `sonnet-low` | `cli_proxy/cpa-claude-sonnet-5-5#low` | low | CLIProxy, protocolo Anthropic |
| `sonnet-medium` | `cli_proxy/cpa-claude-sonnet-5-5#medium` | medium | CLIProxy, protocolo Anthropic |
| `sonnet-high` | `cli_proxy/cpa-claude-sonnet-5-5#high` | high | CLIProxy, protocolo Anthropic |
| `opus-low` | `cli_proxy/cpa-claude-opus-5-5#low` | low | CLIProxy, protocolo Anthropic |
| `opus-medium` | `cli_proxy/cpa-claude-opus-5-5#medium` | medium | CLIProxy, protocolo Anthropic |

O Sol usa a integração builtin `openai` e a credencial OAuth completa do banco local. O OpenCode expande o modo Fast em `gpt-6.1-sol-fast`, com a variante `low`. O modelo enviado continua sendo `gpt-6.1-sol`, com `reasoning.effort=low` e `service_tier=priority`. O executor conserva o WebSocket nativo e o fallback HTTP.

Sonnet e Opus usam `http://127.0.0.1:8317/v1/messages`. O esforço vem das variantes Anthropic nativas, que enviam `thinking.type=adaptive` e `output_config.effort`. O DeepSeek conserva o provider Go em `https://opencode.ai/zen/go/v1`, com `reasoning_effort=max`.

São necessários OpenCode **2.0.26**, Python 3.10 ou superior, o catálogo local `~/.cache/opencode/models.json` e as credenciais locais `openai`, `cli_proxy` e `opencode-go`. O preflight confere o modelo e a variante resolvidos pelo executável. Não substitui modelos nem reduz esforço quando há falha.

## Executar

Execute a partir de `~/VSCode/Lab/evals`.

Confira os corretores, a agenda e os registros sem chamar modelos:

```sh
python3 -B -m unittest discover -s exploracao/sol-fast-vs-deepseek -v
node --test exploracao/sol-fast-vs-deepseek/test_observer.mjs
```

Congele o plano de 210 execuções sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py plan \
  --out exploracao/sol-fast-vs-deepseek/plans/oauth-matrix
```

Confira configuração, autenticação privada, catálogo e observador, sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py preflight \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/validation/oauth-terminal
```

Execute o smoke de sete sessões para conferir as chamadas reais:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/smoke-oauth-matrix
```

Execute o piloto completo em outra pasta:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --out exploracao/sol-fast-vs-deepseek/results/pilot-oauth-matrix
```

São seis casos × cinco repetições × sete configurações, total de **210 sessões planejadas**. Cada sessão tem uma mensagem do usuário e até 25 passos do agente. Um passo pode fazer várias chamadas de ferramentas. Chamadas adicionais por retry permanecem registradas.

Cada bloco de caso e repetição contém todas as configurações. A seed `20261010` embaralha os blocos e uma ordem base. Rotações dessa ordem balanceiam as posições: em 30 blocos, cada configuração ocupa cada posição quatro ou cinco vezes. As sessões são sequenciais.

O limite padrão é 300 segundos por tarefa e 21.600 segundos para a rodada, verificados entre execuções. Uma tarefa em curso pode ultrapassar o orçamento global até seu limite individual, além da preparação. Use `--timeout` e `--budget-seconds` antes do congelamento para alterar esses limites. O smoke anterior não permite estimar a duração dos cinco novos agentes.

A credencial OAuth original é lida sem escrita. O preflight exige que seu token dure pelo orçamento completo, limite individual e margem de 900 segundos. Isso evita rotacionar um refresh token numa cópia descartável. Se esse controle falhar, renove a sessão no OpenCode normal ou diminua o orçamento antes de iniciar outra rodada.

O executor para após falhas de preparação, exportação, configuração, identidade, observação ou alteração do projeto. Erros da tarefa ou do provider, respostas incorretas e timeouts continuam visíveis sem interromper os próximos casos. Não repete inferências automaticamente. Recuperações internas do OpenCode entram no tempo e nos eventos.

Para selecionar um subconjunto:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --candidates sol-fast-low,sonnet-medium,opus-low \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/subset-oauth
```

Para regenerar um relatório sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py report \
  --out exploracao/sol-fast-vs-deepseek/results/pilot-oauth-matrix
```

`plan`, `preflight` e `run` exigem uma pasta nova. `run` cria seu próprio congelamento e repete o preflight. O plano serve para revisão, não é consumido por `run`. Uma nova rodada não apaga tentativas anteriores.

`--binary`, `--database` e `--cache` selecionam executável, banco e catálogo. `CLIPROXY_API_KEY` e `OPENCODE_GO_API_KEY` podem fornecer as duas chaves. O Sol exige OAuth nativo e não aceita substituir essa autenticação por chave. Credenciais não entram na configuração pública.

## Casos e correção

Os seis casos usam a mesma aplicação Python sintética com 23 arquivos. Código legado e funções semelhantes servem como alternativas plausíveis. A pergunta informa o dispatcher ativo para delimitar a tarefa.

| Caso | Entrega exigida |
|---|---|
| `route` | Seguir o POST de pedido até a chamada ao transporte do banco |
| `config` | Identificar precedência e preservar um valor vazio do ambiente |
| `retry` | Encontrar limite, exceções e fronteira da repetição |
| `permission` | Resolver filtro por tenant, dono, publicação e exclusão |
| `feature` | Identificar o renderer com uma flag de tenant desativada |
| `absence` | Demonstrar que uma rota existe apenas no código legado |

O agente devolve JSON com resposta e citações de arquivo, símbolo, linha e trecho exato. A correção exige a resposta literal correta, tipos corretos, evidências válidas e os trechos necessários. Citações fabricadas, incompletas ou fora do símbolo falham. As provas de execução das fixtures e as soluções de referência ficam em `test_cases.py`, fora do projeto visível ao agente.

Formato JSON e citação exata fazem parte do contrato. Uma falha de formato pode reprovar uma resposta semanticamente correta. O resultado registra separadamente `answer_correct` e `evidence_correct` para permitir revisão desse efeito. A correção não julga explicações abertas nem utilidade de texto livre.

## Isolamento e observação

Cada tarefa recebe um projeto, home de descoberta, diretórios XDG e banco de sessões privados. Todas as configurações usam o agente `navigator`, as mesmas instruções e os mesmos limites. Permissões permitem somente leitura, busca e listagem. Shell, edição, web, skills e subagentes são negados.

A descoberta de configurações ancestrais fica desativada. A auditoria permite os plugins internos e exatamente um plugin local de observação. Confere sua origem, ativação e registro de prontidão. O agente não tem acesso ao diretório desse plugin.

`observer.js` registra hooks HTTP e WebSocket do OpenCode. Mantém URLs e autenticação nativas. Não altera requisições nem frames. Em HTTP, uma passagem do stream coleta metadados e entrega os mesmos bytes, status e cabeçalhos ao consumidor. Não espera o stream inteiro antes de entregá-lo. Todos os modelos usam esse observador.

A captura conserva apenas identidade, sessão, agente, tipo de chamada, URL sem query, modelo enviado, esforço, Fast, uso, status e tempos. Não grava cabeçalhos, prompts, ferramentas ou tokens nessa captura. As sessões exportadas conservam as mensagens e ferramentas do projeto.

Fast mantém três estados de evidência:

1. A seleção nativa usa o modelo Fast e a variante low.
2. Cada chamada observada envia `service_tier=priority` e esforço low.
3. As respostas terminais `response.completed` informam `service_tier=priority` ou `fast` em todas as chamadas bem-sucedidas e completas.

O estado inicial `response.created` pode informar `auto`. A classe terminal é a evidência utilizada para atendimento. Sem classe terminal, Fast servido permanece **desconhecido**. Uma classe terminal diferente ou incompleta impede a confirmação. O executor conserva ambos os estados para auditoria. Esforço enviado não comprova quanto raciocínio interno o modelo executou.

A cópia privada da credencial é importada com permissão `0600`. O arquivo é removido após a importação e o banco privado é removido ao terminar. Encerramento externo abrupto pode impedir a limpeza. O isolamento de descoberta e permissões não equivale a um sandbox do sistema operacional.

## Interpretar os resultados

`freeze.json` registra fontes, protocolo, catálogo, configurações, casos, ordem e limites antes da inferência. Inclui o hash do observador. Cada tentativa conserva prompt, eventos, exportação da sessão, ferramentas, resposta, parâmetros observados, correção e identidade de todas as mensagens do assistente.

O relatório lê as configurações do próprio congelamento. O smoke anterior continua com dois modelos. A rodada OAuth é independente e seus tempos não se misturam com os da rota antiga. As fontes históricas verificadas estão em `results/smoke/frozen-source`.

`report.md` e `summary.json` mostram acertos, erros, respostas incorretas e ausências. Tempos incluem boot, ferramentas e recuperações internas. Excluem preparação, auditoria, exportação e correção. A tabela geral inclui respostas concluídas incorretas. Há 21 comparações pareadas na matriz completa. Cada uma exige acerto dos seus dois modelos no mesmo caso e repetição.

Entrada, saída, raciocínio e cache ficam separados em cada `result.json`. Não representam consumo comparável das assinaturas. A identidade da sessão e da requisição também não atesta qual modelo um proxy executou a montante.

A comparação mede configurações completas, incluindo modelo, esforço e rota. Não identifica o efeito isolado de Fast. Cinco repetições medem variação operacional, mas seis casos continuam sendo seis tarefas distintas. A suíte sintética não estabelece o melhor explorador para todos os projetos. O relatório mantém o veredito inconclusivo até análise de qualidade, variabilidade e metadados reais.

## Referências

- [Agentes OpenCode V2](https://opencode.ai/v2/docs/agents).
- [Modelos e variantes OpenCode V2](https://opencode.ai/v2/docs/models).
- [Fast mode OpenAI](https://developers.openai.com/api/docs/guides/fast-mode).
- [OpenCode Go](https://opencode.ai/docs/go/).
- [Decisão de ampliação e fontes locais](validation/matrix-design.md).
