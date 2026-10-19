# Sol low Fast e GLM Flash no caso monetário

Esta rodada usa o contrato corrigido de `money-contract-v2`, com os mesmos arquivos iniciais, referência, testes privados e regras de aprovação. A coorte contém Sol 6.1 low Fast via OAuth nativo do OpenCode e GLM 5.3 Flash high e max via OpenCode Go.

```sh
python3 -B implementacao/opencode-implementador/rounds/money-sol-low-glm-flash/run.py run \
  --out implementacao/opencode-implementador/results/money-sol-low-glm-flash
```

São 15 sessões sequenciais. Três provam a interrupção por orçamento, três executam o smoke e nove comparam o caso monetário, com três repetições por configuração. Os gates são novos e devem passar antes da fase seguinte. No gate de orçamento, `budget_exceeded` com `proof_passed=True` é o resultado esperado.

A prova de orçamento permite 20 segundos e duas chamadas. Smoke e caso monetário permitem 1200 segundos e 60 chamadas por sessão. O controlador conserva a tolerância de 15 segundos. O catálogo congelado, o identificador imutável da imagem existente e o OpenCode 2.0.26 são os mesmos da rodada anterior. Uma imagem removida bloqueia o preflight. A configuração, o estado e as ferramentas pessoais permanecem isolados pelo executor original.

`plan`, `validate` e `preflight` usam a mesma CLI. `plan` e `validate` não fazem chamadas de modelo. `preflight` verifica Docker, isolamento e descoberta nativa sem inferência. `--phase budget` limita a sequência ao gate de orçamento; `--phase smoke` inclui os dois gates; `--phase screening` equivale a `all`. A saída precisa ser nova, inclusive ao repetir uma rodada interrompida.

Cada fase escreve em `budget/`, `smoke/` ou `screening/`. `round-freeze.json` registra as 15 sessões, as fontes, a origem do contrato e os comandos. `round-summary.json` reúne o estado das fases. Para atualizar o relatório de uma saída existente, use `report --out CAMINHO`.

O runner ajusta a contagem de configurações nos relatórios Markdown derivados para a coorte de três candidatos, sem alterar a fonte congelada do gerador.

O núcleo mudou somente em `domain.py` para a coorte, em `tasks.py` para selecionar o contrato corrigido e no novo `contract.py`. Os demais arquivos conservam os bytes da fotografia original. O executor congela e verifica também `contract.py` antes de cada trial. O runner verifica sua fotografia antes e depois de cada fase e interrompe a sequência se houver gate reprovado, infraestrutura ou escopo inválido, ou fase incompleta mesmo com retorno zero do subprocesso.

Fast solicitado como `priority` e `service_tier` retornado são metadados separados. O retorno `default` no OAuth não demonstra ausência de aceleração. Esta comparação mede a tarefa inteira, incluindo comandos e verificações feitos pelos agentes. Três repetições de um caso não determinam uma escolha geral de implementador.
