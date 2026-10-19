# Sol low com Fast versus DeepSeek max no OpenCode

Benchmark de exploração de código com duas configurações fixas. Mede correção da resposta, evidência de código e tempo de conclusão da tarefa. Não há resultado comparativo até uma rodada real terminar.

| Configuração | Seleção OpenCode | Parâmetros enviados | Autenticação |
|---|---|---|---|
| Sol low com Fast | `cli_proxy_openai/gpt-6.1-sol#fast-low` | `reasoning_effort=low`, `service_tier=priority` | Credencial `cli_proxy` do banco local |
| DeepSeek V4.1 Flash max | `opencode-go/deepseek-v4.1-flash#max` | `reasoning_effort=max` | Credencial `opencode-go` do banco local |

O alias Fast corresponde à configuração local encontrada no provider `cli_proxy_openai`. O Sol usa o CLIProxy em `http://127.0.0.1:8317/v1`. Esta rodada não usa a integração direta OpenAI OAuth. O DeepSeek usa a assinatura Go em `https://opencode.ai/zen/go/v1`.

O executor exige OpenCode **2.0.26**, versão conferida durante a preparação, Python 3.10 ou superior e o catálogo local `~/.cache/opencode/models.json`. Uma versão ou catálogo diferente exige outra preparação e outra pasta de saída. Não substitui modelos nem reduz o esforço para contornar uma falha.

## Executar

Execute os comandos a partir de `~/VSCode/Lab/evals`.

Confira os corretores e o processamento de evidências sem chamar modelos:

```sh
python3 -B -m unittest discover -s exploracao/sol-fast-vs-deepseek -v
```

Congele o plano de 60 execuções sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py plan \
  --out exploracao/sol-fast-vs-deepseek/plans/initial
```

Confira configuração, autenticação privada e descoberta, sem inferência:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py preflight \
  --out exploracao/sol-fast-vs-deepseek/validation/terminal
```

Execute primeiro um caso em cada configuração para conferir as chamadas reais:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --cases route --reps 1 \
  --out exploracao/sol-fast-vs-deepseek/results/smoke
```

Execute a rodada completa em uma pasta nova:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py run \
  --out exploracao/sol-fast-vs-deepseek/results/pilot
```

São seis casos × cinco repetições × duas configurações, total de **60 execuções planejadas**. Os pares ficam adjacentes, com a ordem dos modelos balanceada e sorteada pela seed `20261010`. Não há inferências concorrentes. O limite padrão é 300 segundos por tarefa e 7.200 segundos para a rodada, verificados entre execuções. Uma tarefa em curso pode ultrapassar o orçamento global até o seu limite individual, além da preparação. Use `--budget-seconds` e `--timeout` para alterar os limites antes do congelamento.

O executor interrompe a rodada após falha de preparação, exportação, configuração, identidade ou alteração do projeto. Falhas da tarefa ou do provider, respostas incorretas e timeouts permanecem registrados e não interrompem automaticamente os casos seguintes. Não tenta novamente automaticamente uma inferência. Recuperações internas do OpenCode permanecem nos eventos e no tempo da tarefa. A segunda metade de um par pode ficar ausente quando o orçamento termina ou há falha de infraestrutura.

Para regenerar o relatório sem chamar modelos:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/bench.py report \
  --out exploracao/sol-fast-vs-deepseek/results/pilot
```

As pastas de saída precisam ser novas para `plan`, `preflight` e `run`. `run` cria seu próprio congelamento e repete o preflight. O plano anterior serve para revisão, não é consumido por `run`. Uma retomada exige outra pasta e aparece como outra rodada, sem apagar tentativas anteriores.

`--binary`, `--database` e `--cache` selecionam explicitamente o executável, banco de credenciais e catálogo. Alternativamente, `CLIPROXY_API_KEY` e `OPENCODE_GO_API_KEY` fornecem as chaves das duas rotas. As chaves não entram na configuração pública. Não altera o arquivo global de configuração nem o banco de credenciais original.

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

## Isolamento e evidência de Fast

Cada tarefa recebe um projeto, home de descoberta, diretórios XDG e banco de sessões privados. O agente `navigator` recebe o mesmo texto de instrução nas duas configurações. Permissões permitem somente leitura, busca e listagem. Shell, edição, web, skills e subagentes são negados. A descoberta de configurações ancestrais e os plugins externos são desativados. A auditoria consulta um servidor privado após a ativação dos plugins internos.

O benchmark executa o papel de explorador como uma sessão principal controlada. Não mede a delegação por um agente pai nem o empacotamento de contexto numa sessão filha.

Um observador HTTP local encaminha as chamadas para cada provider. Registra somente modelo, esforço, classe de serviço, status, tempos e metadados selecionados de resposta. Não arquiva cabeçalhos de autenticação nem o corpo completo das chamadas nessa captura. As sessões exportadas conservam as mensagens e ferramentas do projeto.

Fast tem três estados distintos de evidência:

1. A configuração solicita `low` e `priority`.
2. O observador confirma os campos encaminhados ao provider.
3. O provider devolve `service_tier=priority` ou `fast` nas chamadas bem-sucedidas.

Se o terceiro estado não for observável, o relatório diz **Fast servido desconhecido**. Se houver outra classe devolvida, diz **não confirmado**. O alias `fast-low` sozinho não comprova prioridade efetiva. Da mesma forma, esforço `max` enviado não comprova quanto raciocínio o modelo executou internamente.

O proxy introduz algum custo local no tempo medido e é usado em ambos os lados. Preserve `requests.json` para distinguir espera do provider de outros componentes. O relatório não declara um gargalo nem uma diferença causal sem inspeção dessas evidências.

A cópia privada da credencial é importada com permissão `0600`. O arquivo é removido após a importação e o banco privado é removido ao terminar. Um encerramento externo abrupto pode impedir a limpeza. O isolamento descrito não é um sandbox do sistema operacional.

## Interpretar os resultados

`freeze.json` registra fontes, protocolo, catálogo, casos, ordem e limites antes da inferência. Cada tentativa conserva prompt, eventos, exportação da sessão, ferramentas, resposta, parâmetros observados, correção e identidade de todas as mensagens do assistente. Qualquer troca de modelo, esforço, agente ou diretório invalida a tentativa.

`report.md` e `summary.json` mantêm ausências, falhas e acertos visíveis. Tempos incluem boot da invocação, ferramentas e recuperações internas. Excluem preparação, auditoria, exportação e correção. A tabela geral inclui todas as respostas concluídas, inclusive incorretas. As razões de tempo por caso usam somente pares em que ambos acertaram. Entrada, saída, raciocínio e cache ficam separados em cada `result.json`; não são tratados como consumo comparável de assinatura.

Esta é uma comparação exploratória de configurações completas. Não identifica o efeito isolado de Fast. Cinco repetições por caso medem variabilidade operacional, mas não equivalem a 30 tarefas independentes. Uma rodada sintética curta não estabelece o melhor explorador para todos os projetos. O relatório mantém o veredito inconclusivo até uma análise das evidências, qualidade, variabilidade e confirmação de Fast.

## Referências de preparação

- [Agentes OpenCode V2](https://opencode.ai/v2/docs/agents).
- [Modelos e variantes OpenCode V2](https://opencode.ai/v2/docs/models).
- [Fast mode OpenAI](https://developers.openai.com/api/docs/guides/fast-mode).
- [OpenCode Go](https://opencode.ai/docs/go/).
