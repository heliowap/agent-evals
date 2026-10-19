# Haiku 5.5: leitura, pesquisa no código e exploração

Execute da raiz de `evals`:

```sh
python3 -B exploracao/haiku-5-5/bench.py run \
  --cache exploracao/haiku-5-5/models.json \
  --budget-seconds 86400 \
  --out exploracao/haiku-5-5/results/full-1
```

Este comando executa diretamente o piloto completo, com preflight privado nos cinco esforços e 150 trials: seis casos × cinco repetições × Haiku low, medium, high, xhigh e max. Cada esforço recebe 30 trials comparativos. Os defaults de `bench.py` já selecionam todos esses casos e esforços. Sem retomada, sobrescrita, retry de inferência ou troca automática de esforço.

O smoke anterior em `results/round-1` terminou cinco sessões e verificou modelo, esforço, pensamento adaptativo e cap nas 27 chamadas. Houve três aprovações completas; medium falhou no tipo de `chain` e high numa citação extra. Por isso o wrapper histórico não iniciou o piloto. Essas reprovações de qualidade são resultados a medir, não critérios para impedir a coleta completa. O comando acima não reutiliza nem altera o gate antigo, não repete os smokes e mantém o mesmo corretor estrito.

```sh
python3 -B exploracao/haiku-5-5/bench.py plan --cache exploracao/haiku-5-5/models.json --budget-seconds 86400 --out exploracao/haiku-5-5/results/full-plan-1
python3 -B exploracao/haiku-5-5/haiku.py validate-offline --out exploracao/haiku-5-5/results/full-check-1
python3 -B exploracao/haiku-5-5/bench.py report --out exploracao/haiku-5-5/results/full-1
```

`--binary`, `--database` e `--cache` permitem escolher os recursos nativos. Por padrão usa `opencode`, o SQLite habitual em modo somente leitura e o catálogo congelado incluído no pacote. As credenciais nunca aparecem no relatório; importação privada usa um arquivo efêmero 0600. `report` recompõe relatórios locais sem inferência.

## Protocolo

OpenCode 2.0.26; modelo `cli_proxy/cpa-claude-haiku-5-5#<effort>`; wire `claude-haiku-5-5`; Messages em `http://127.0.0.1:8317/v1/messages`; thinking adaptive; Fast desativado. Todas as requisições observadas devem preservar identidade, esforço e `max_tokens` inteiro 128000. Essa prova mostra parâmetros enviados; não atesta qual modelo o provedor executou internamente.

Controles iguais entre esforços: 300 segundos por processo de tarefa, 25 passos, contexto 272000, saída 128000, seed 20261010, cinco repetições. O cap de saída mudou deliberadamente de 32768 para 128000: esta é uma nova configuração experimental. O [limite publicado do Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) admite 128K de saída.

O piloto completo usa orçamento de admissão de 86400 segundos. Esse teto de 24 horas evita o corte em seis horas do wrapper anterior; não é uma previsão de duração. Só as tarefas podem consumir até 150 × 300 = 45000 segundos se todas chegarem ao timeout, além de preparação e exportação. Antes de iniciar cada trial, o core verifica o tempo decorrido. Preparação, auditoria e exportação têm seus próprios limites; o orçamento global não é um deadline rígido do processo completo. Um piloto pode acabar incompleto; trials ausentes ficam visíveis e o exit é não-zero. Erros de infraestrutura ou alteração da fixture interrompem a fase; limite de saída, timeout, erro de tarefa e resposta entregue incorreta continuam a coleta.

A agenda intercala esforços por caso e repetição, com rotações balanceadas: cada esforço ocupa cada posição seis vezes no piloto. A região medida é o processo `opencode run`, incluindo boot, ferramentas e recuperações nativas. Exclui construção da fixture, importação de credencial, auditoria, exportação e grader. Comparações pareadas exigem aprovação completa de ambos no mesmo caso/repetição. Limites terminais de saída ficam fora de respostas incorretas e pares aprovados.

Ferramentas permitidas: read, glob, grep e list. Shell, web, edição, skills, MCP, LSP, formatters e delegação nativa desabilitados. Descoberta usa HOME/XDG e configuração privados. Isso não equivale a sandbox do sistema operacional. Plugins nativos permanecem ativos, junto do observador local verificado; skills e plugins externos do usuário não são importados.

## Corpus, captura e integridade

Os seis casos investigam rota ativa, precedência de configuração, retry, permissão, feature flag e ausência de rota. Os 23 arquivos, prompts, respostas e grader vêm da base R2 congelada em `../sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. `cases.py`, `test_cases.py` e `observer.js` são byte equivalentes; `provenance.json` registra origem e hashes. `bench.py` conserva um único scheduler e loop; `runtime.py` adapta a coorte, cap, captura e diagnóstico; `haiku.py` adiciona o gate e envelopes. `test_haiku.py` contém provas novas, sem modelos. O catálogo vem da cópia histórica `implementacao/opencode-implementador/results/screening/models.json`.

Exportação nativa usa stdout em arquivo regular 0600, preservando bytes sanitizados antes de decodificação/parse. `export.json` registra exit, timeout, tamanhos, hashes brutos/sanitizados e offset de JSON/UTF-8 inválido. A captura não reserializa, corrige ou repete exportações. Provas sintéticas de captura não demonstram a causa de uma falha no binário nativo.

`finish` e `rawFinish` de todos os assistentes são preservados. `length`/`max_tokens` no último assistente identifica limite terminal; um limite intermediário seguido de entrega válida registra recuperação. Falhas de exportação ou identidade continuam infraestrutura; não se inferem limites pelo número de tokens.

O runner direto congela as fontes do pacote e o catálogo. Verifica fontes/protocolo/catálogo antes dos trials e após a fase, incluindo o último trial. Cada sessão tem auditoria privada, identidade e parâmetros de requisição verificados e fixture conferida após a execução. O plano e validações não fazem inferência; preflight só comprova descoberta. Resultados anteriores ficam intactos em seus destinos existentes.

O wrapper `haiku.py run` permanece disponível para o protocolo anterior, com cinco smokes novos, gate de 5/5 aprovações completas, 150 trials condicionados ao gate e envelopes adicionais de integridade do executável e do inventário histórico. O piloto direto não produz esses envelopes de campanha. Seus resultados, congelamento, relatório e status ficam diretamente em `results/full-1`, sem subpastas `smoke` e `pilot`. O comando `bench.py report` recompõe esse relatório; não usar `haiku.py report` para o piloto direto. Os snapshots históricos em `results/round-1` continuam descrevendo o protocolo antigo.

A suíte tem seis tarefas sintéticas; cinco repetições medem variação operacional, não 30 problemas inéditos. Ela permite comparar estas configurações neste corpus, sem certificar confiabilidade geral nem declarar vencedor automaticamente. Custo informado zero não significa uso gratuito; cache remoto pode persistir. Revisões de desenho usaram apenas modelos da família GPT.
