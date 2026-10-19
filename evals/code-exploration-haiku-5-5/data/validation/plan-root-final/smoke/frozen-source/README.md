# Haiku 5.5: leitura, pesquisa no código e exploração

Execute da raiz de `evals`:

```sh
python3 -B exploracao/haiku-5-5/haiku.py run \
  --out exploracao/haiku-5-5/results/round-1
```

O wrapper cria cinco smokes novos do caso `route`. Exige respostas corretas, citações válidas, fixture intacta e parâmetros nativos verificados nos cinco esforços. O gate rejeita requisições não-200, incompletas ou com erro registrado pelo observador, inclusive quando o HTTP é 200. Só depois executa 150 trials: seis casos × cinco repetições × Haiku low, medium, high, xhigh e max. Cada esforço recebe 30 trials comparativos. Sem retomada, sobrescrita, retry de inferência ou troca automática de esforço.

```sh
python3 -B exploracao/haiku-5-5/haiku.py plan --out exploracao/haiku-5-5/results/plan-1
python3 -B exploracao/haiku-5-5/haiku.py validate-offline --out exploracao/haiku-5-5/results/check-1
python3 -B exploracao/haiku-5-5/haiku.py preflight --out exploracao/haiku-5-5/results/preflight-1
python3 -B exploracao/haiku-5-5/haiku.py report --out exploracao/haiku-5-5/results/round-1
```

`--binary`, `--database` e `--cache` permitem escolher os recursos nativos. Por padrão usa `opencode`, o SQLite habitual em modo somente leitura e o catálogo congelado incluído no pacote. As credenciais nunca aparecem no relatório; importação privada usa um arquivo efêmero 0600. `report` recompõe relatórios locais sem inferência.

## Protocolo

OpenCode 2.0.26; modelo `cli_proxy/cpa-claude-haiku-5-5#<effort>`; wire `claude-haiku-5-5`; Messages em `http://127.0.0.1:8317/v1/messages`; thinking adaptive; Fast desativado. Todas as requisições observadas devem preservar identidade, esforço e `max_tokens` inteiro 128000. Essa prova mostra parâmetros enviados; não atesta qual modelo o provedor executou internamente.

Controles iguais entre esforços: 300 segundos por processo de tarefa, 25 passos, contexto 272000, saída 128000, seed 20261010, cinco repetições. O cap de saída mudou deliberadamente de 32768 para 128000: esta é uma nova configuração experimental. O [limite publicado do Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) admite 128K de saída.

Orçamento de admissão de 21600 segundos por fase: antes de iniciar cada trial, o core verifica o tempo decorrido. Preparação, auditoria e exportação têm seus próprios limites; portanto seis horas não são um deadline rígido do processo completo. Um piloto pode acabar incompleto; trials ausentes ficam visíveis e o exit é não-zero. Erros de infraestrutura ou alteração da fixture interrompem a fase; limite de saída, timeout e erro de tarefa continuam a coleta. Uma resposta entregue incorreta permanece uma observação concluída.

A agenda intercala esforços por caso e repetição, com rotações balanceadas: cada esforço ocupa cada posição seis vezes no piloto. A região medida é o processo `opencode run`, incluindo boot, ferramentas e recuperações nativas. Exclui construção da fixture, importação de credencial, auditoria, exportação e grader. Comparações pareadas exigem aprovação completa de ambos no mesmo caso/repetição. Limites terminais de saída ficam fora de respostas incorretas e pares aprovados.

Ferramentas permitidas: read, glob, grep e list. Shell, web, edição, skills, MCP, LSP, formatters e delegação nativa desabilitados. Descoberta usa HOME/XDG e configuração privados. Isso não equivale a sandbox do sistema operacional. Plugins nativos permanecem ativos, junto do observador local verificado; skills e plugins externos do usuário não são importados.

## Corpus, captura e integridade

Os seis casos investigam rota ativa, precedência de configuração, retry, permissão, feature flag e ausência de rota. Os 23 arquivos, prompts, respostas e grader vêm da base R2 congelada em `../sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. `cases.py`, `test_cases.py` e `observer.js` são byte equivalentes; `provenance.json` registra origem e hashes. `bench.py` conserva um único scheduler e loop; `runtime.py` adapta a coorte, cap, captura e diagnóstico; `haiku.py` adiciona o gate e envelopes. `test_haiku.py` contém provas novas, sem modelos. O catálogo vem da cópia histórica `implementacao/opencode-implementador/results/screening/models.json`.

Exportação nativa usa stdout em arquivo regular 0600, preservando bytes sanitizados antes de decodificação/parse. `export.json` registra exit, timeout, tamanhos, hashes brutos/sanitizados e offset de JSON/UTF-8 inválido. A captura não reserializa, corrige ou repete exportações. Provas sintéticas de captura não demonstram a causa de uma falha no binário nativo.

`finish` e `rawFinish` de todos os assistentes são preservados. `length`/`max_tokens` no último assistente identifica limite terminal; um limite intermediário seguido de entrega válida registra recuperação. Falhas de exportação ou identidade continuam infraestrutura; não se inferem limites pelo número de tokens.

Cada fase congela as fontes realmente usadas. O core verifica fontes/protocolo/catálogo antes dos trials e após a fase, incluindo o último trial. Envelopes comparam fontes, catálogo, executável e inventário histórico antes/depois. Resultados anteriores ficam intactos. O plano e validações não fazem inferência; preflight só comprova descoberta, e smoke comprova parâmetros encaminhados.

A suíte tem seis tarefas sintéticas; cinco repetições medem variação operacional, não 30 problemas inéditos. Ela permite comparar estas configurações neste corpus, sem certificar confiabilidade geral nem declarar vencedor automaticamente. Custo informado zero não significa uso gratuito; cache remoto pode persistir. Revisões de desenho usaram apenas modelos da família GPT.
