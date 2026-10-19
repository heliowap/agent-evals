# Deterministic first no OpenCode

Mesmo experimento de [Codex CLI](../agentsmd-detfirst-isolated/README.md). O executor atual usa **OpenCode 2.0.25 + `cli_proxy/cpa-claude-opus-5-5#medium`**, pelo CPA Proxy local em `http://127.0.0.1:8317/v1`. Compara `AGENTS.md` vazio com o trecho exato de 992 bytes. Não herda o restante do seu arquivo global.

**Piloto Sol concluído em 10/10/2026:** usou `openai/gpt-6.1-sol#xhigh`, com 72/72 execuções e 36/36 entregas corretas em cada condição, incluindo os controles revisados. O trecho aumentou a duração média observada em 23,5% e o total normalizado de tokens em 7,5%. A [análise final](results/pilot-r2/analysis.md) contém resultados por caso e a comparação exploratória com Codex. O protocolo e os fontes originais estão preservados em `results/pilot-r2/frozen-source/` com os hashes conferidos contra `freeze.json`. O script `results/pilot-r2/analyze.py` usa esses fontes congelados. Esses resultados não medem o Opus.

São 12 casos × 2 condições × 3 repetições, total de **72 execuções planejadas**. `cases.py`, a rubrica e os dois arquivos de instrução são cópias exatas da versão Codex. O executor verifica essa igualdade antes de congelar uma rodada. A ordem dos pares, seed `20261010`, prompts e corretores são os mesmos. Não altera o executor nem os resultados do Codex.

## Rodar no terminal

Use Python 3.10 ou superior, Git e OpenCode 2.0.25. O CPA Proxy precisa estar ativo em `http://127.0.0.1:8317/v1`, com acesso a `claude-opus-5-5`. O executor usa a chave de `CLIPROXY_API_KEY`, a mesma variável referenciada pela configuração local do provider `cli_proxy`.

```sh
cd ~/VSCode/Lab/evals/agentsmd-detfirst-opencode
python3 -m unittest -v
python3 run.py preflight --out validation/opus-terminal-preflight
python3 run.py run --out results/opus-5-5-medium
```

`preflight` abre um servidor local temporário por condição e mantém esse servidor durante toda a auditoria. Aguarda a ativação dos plugins por `integration.list` antes de consultar configuração, skills e plugins. Não pede inferência ao modelo. `run` repete essa checagem automaticamente antes de iniciar as tarefas e por execução. Uma falha interrompe a rodada, aparece no terminal e fica registrada em JSON e no relatório. Não substitui o modelo, não reduz o esforço e não repete automaticamente inferências que falharam.

As pastas de saída precisam ser novas. Para outra tentativa, escolha outro `--out`. `--binary /caminho/opencode` permite selecionar o executável, mas sua versão precisa continuar sendo 2.0.25. Se `CLIPROXY_API_KEY` estiver ausente, o executor lê a credencial ativa de `cli_proxy` no banco local do OpenCode v2, sem modificá-lo. `--auth-file /caminho/arquivo.json` permite selecionar explicitamente uma exportação de `opencode auth export` ou um `auth.json` legado contendo `cli_proxy`. A identidade pedida é registrada na configuração, na linha de comando e conferida na sessão exportada, inclusive em cada mensagem do assistente.

Para um teste inicial de dois casos, antes das 72 execuções:

```sh
python3 run.py run --out results/smoke-opus-5-5-medium --cases count,repeat --reps 1
```

O padrão permite até 600 segundos de invocação do agente por execução e 7.200 segundos de orçamento da rodada. Esse orçamento pode encerrar a rodada antes das 72 execuções. Use `--budget-seconds 46800` se quiser reservar tempo para os 72 limites de dez minutos e parte da preparação. O limite por execução cobre todos os prompts daquele caso. Preparação, auditoria e exportação têm limites separados; o orçamento da rodada é checado entre pares, portanto não é um encerramento rígido pelo relógio.

Os comandos abaixo não precisam do OpenCode nem de rede:

```sh
python3 run.py plan --out plans/new-plan
python3 run.py report results/opus-5-5-medium
python3 run.py blind results/opus-5-5-medium
```

## O que mede

| Casos | Resultado observado |
|---|---|
| `count`, `money`, `convert` | Exatidão de contagem, soma filtrada e conversão de tipos |
| `rename`, `project_tool`, `repeat` | Edição em lote, contrato da ferramenta existente e repetição em dois prompts na mesma sessão |
| `guardrail`, `regression` | Verificação executável que rejeita reincidência e aceita entradas válidas |
| `independent`, `dependent` | Execução real de comandos independentes e preservação da ordem quando há dependência |
| `out_of_scope`, `judgment` | Respeito à tarefa de revisão e qualidade de uma edição que exige julgamento |

O relatório mede passes automáticos, falhas de infraestrutura e tempo. `out_of_scope` e `judgment` exigem também [revisão cega](REVIEW.md). Logs e artefatos permitem verificar separadamente uso de ferramentas, reutilização de scripts, paralelismo, alterações extras e avisos ao usuário. Contar ferramentas não mede qualidade.

Os ganhos possíveis são menos erros mecânicos, proteções que detectam reincidências e menor esforço em tarefas repetidas. Custos possíveis incluem mais tokens, preparação de automações sem benefício e perda de tempo em tarefas simples. Este piloto sintético identifica sinais e falhas do protocolo; três repetições por caso não sustentam uma decisão geral de adoção.

O relatório usa pares completos, diferença de passes com peso igual por caso e bootstrap agrupado por caso. Mantém visíveis as execuções ausentes. O tempo inclui boot do OpenCode e retries internos, mas exclui auditoria, exportação e correção. Os contadores nativos de entrada, saída, raciocínio e cache ficam separados. Não inferimos total de tokens nem preço; custo informado zero não significa uso gratuito. Cada exportação contém todo o histórico e só a última entra na soma, para não duplicar o primeiro prompt do caso `repeat`.

## Isolamento e evidências

Cada execução recebe projeto Git, diretórios XDG, home de descoberta e banco de sessões novos em uma pasta temporária. O subprocesso descarta configurações, endpoints e chaves herdadas. A configuração privada fixa a rota CPA e a variante `medium`; a chave selecionada entra apenas no banco privado. `OPENCODE_TEST_HOME` aponta a descoberta de `.agents` e `.claude` para um diretório privado. `OPENCODE_CONFIG_PROJECT_DISABLE=1` desliga a descoberta dos diretórios ancestrais e suas instruções. Apenas o `AGENTS.md` global privado recebe a condição experimental.

O agente `build` conserva as instruções internas do OpenCode. A configuração desliga o plugin `opencode.skill`, que fornece as skills internas `opencode` e `report`, usando `plugins: ["-opencode.skill"]`. Não carrega plugins externos, skills adicionais ou MCPs; também desliga LSP, formatadores, warming e atualizações. Permissões negam ferramentas de subagentes, skills e web. O catálogo de modelos não é atualizado pela rede. A configuração adiciona o alias `cli_proxy/cpa-claude-opus-5-5`, com provider canônico `anthropic`, adaptador `@opencode/ai/providers/anthropic`, modelo de API `claude-opus-5-5` e esforço `medium`. O executor deixa o OpenCode aprovar suas demais solicitações de ferramentas com `--auto`, igualmente nas duas condições. Isso não cria um sandbox de sistema operacional; o isolamento descrito é de estado e de descoberta de instruções.

Somente a credencial selecionada de `cli_proxy` é copiada com permissão `0600` e importada no banco privado por `opencode auth import`. A chave não entra na configuração pública, no manifesto ou nas auditorias. Depois da execução, o executor remove os arquivos de autenticação e o banco privado que também contém credenciais. Não altera o banco ou arquivo original. Um encerramento externo com `kill -9` pode impedir essa limpeza. O diretório temporário está em `runtime-path.txt`.

O `preflight` confere versão, documentos efetivos de configuração, ausência de skills e plugins exclusivamente internos, incluindo a descoberta de instruções. Compara as duas configurações após normalizar os caminhos temporários. **Não verifica igualdade do prompt completo enviado ao modelo**, que não é exposto por esse fluxo do OpenCode. Registra explicitamente essa limitação. A checagem por execução ocorre depois da cópia de autenticação, para detectar também configuração adicional trazida pela conta.

Os inventários de skills e plugins são consultas ao estado atual e podem estar vazios durante a inicialização. Por isso a auditoria aguarda a ativação no mesmo servidor que responderá às consultas. Não aceita uma lista vazia como evidência de isolamento. `discovery-probe.json`, no diretório temporário de cada auditoria, preserva IDs, origens e estados dos plugins mesmo quando a validação rejeita o resultado.

Cada rodada grava `freeze.json` antes das inferências, com a configuração pública do provider e hashes dos fontes, instruções e protocolo. Cada execução preserva eventos JSONL, stderr, exportações da sessão, identidade efetiva do modelo, resultado da auditoria, resposta final, artefatos e correção em uma cópia separada. O gabarito fica fora do diretório da tarefa. `blind` exporta artefatos sem rótulos de variante, mas a própria resposta pode revelar a condição.

Compare primeiro vazio versus trecho **dentro do OpenCode**. Diferenças absolutas entre OpenCode e Codex também incluem ferramentas, instruções internas, políticas de execução e contagem de tokens de cada produto. Não atribua essas diferenças ao trecho do `AGENTS.md`.

## Validação desta entrega

Para Opus via CPA, os 24 testes offline passaram. Verificam também a seleção de provider, modelo e esforço, a importação exclusiva da credencial CPA e a ausência de chaves na configuração pública. O plano em `plans/opus-5-5-medium/freeze.json` mantém os mesmos 72 casos agendados da rodada Sol. A validação está registrada em `validation/opus-5-5-medium/verification.json`. Ainda falta executar inferência com Opus no terminal; os testes simulados não confirmam disponibilidade nem autenticação no proxy.

Os testes verificam os 12 corretores com soluções de referência e resultados inválidos, paridade da suíte, balanceamento dos pares, descarte de configuração herdada, identidade da sessão e continuidade sem dupla contagem. Um CLI simulado testa o fluxo completo de dois prompts e a remoção das credenciais temporárias. Esse teste não executa inferência e não substitui validação com o serviço real.

### Histórico da validação com Sol

O teste do fluxo completo também reproduz uma inicialização em que `plugin.list` retorna vazio antes da ativação. Ele exige que o executor aguarde essa ativação e consulte o mesmo servidor, além de desligar o catálogo das duas skills internas. Outro teste verifica que falhas do preflight aparecem no terminal. A primeira tentativa no terminal, preservada em `results/pilot`, terminou antes de qualquer tarefa com a mensagem `Expected only the built-in OpenCode plugins`. Após corrigir a sequência de inicialização, `validation/terminal-r2` confirmou o carregamento dos plugins e revelou as duas skills internas, agora desativadas no ambiente do eval.

O teste real no terminal concluiu **4 de 4 execuções**, todas aprovadas, nos casos `count` e `repeat`, uma repetição por condição. O [relatório do teste curto](results/smoke-r3/report.md) e suas exportações confirmam `openai/gpt-6.1-sol#xhigh`, catálogo de skills vazio em ambas as condições e continuidade da mesma sessão nos dois prompts de `repeat`. Os contadores conferem com a última exportação cumulativa. As cópias temporárias de credenciais e dos bancos de cada execução foram removidas. Isso valida o funcionamento do executor; a amostra não demonstra ganho da instrução.

O servidor local continua impedido de iniciar no sandbox deste assistente, conforme `validation/activation-fix-local/preflight.json`. A rodada completa `results/pilot-r2` foi executada no terminal do usuário e concluiu 72/72. A auditoria final conferiu as 78 exportações, o modelo e effort, a contagem cumulativa, a descoberta de configuração e os artefatos. Os 21 testes offline passaram após as correções do executor. A análise final foi offline e não chamou o modelo novamente.

Detalhes da integração foram conferidos na documentação de [modelos](https://opencode.ai/v2/docs/models), [instruções](https://opencode.ai/v2/docs/instructions), [configuração](https://opencode.ai/v2/docs/config) e [API](https://opencode.ai/v2/docs/api), além do código-fonte local do OpenCode. A versão é fixada porque essas interfaces podem mudar.
