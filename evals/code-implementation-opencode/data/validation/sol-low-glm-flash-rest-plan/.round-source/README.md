# Completar a triagem com Sol low Fast e GLM Flash

Depois de terminar o comando monetário já iniciado, execute na pasta `evals`:

```sh
python3 -B implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest/run.py run \
  --money-run implementacao/opencode-implementador/results/money-sol-low-glm-flash \
  --out implementacao/opencode-implementador/results/sol-low-glm-flash-rest
```

São **99 trials adicionais**: os outros 11 casos originais da triagem, três configurações e três repetições. A rodada monetária corrigida fornece os nove trials restantes, compondo **108 comparativos**. Não haverá novas chamadas para orçamento, smoke ou monetário.

| Configuração | Rota | Effort |
|---|---|---|
| Sol 6.1 low Fast | OAuth nativo do OpenCode | low, Fast solicitado |
| GLM 5.3 Flash high | OpenCode Go | high |
| GLM 5.3 Flash max | OpenCode Go | max |

O runner exige os nove resultados monetários concluídos e os gates budget/smoke aprovados. Reprovação funcional do monetário não bloqueia os outros casos; execução incompleta ou violação de infraestrutura/escopo bloqueia antes de criar a saída e antes de chamar modelos. Os resultados monetários ficam em sua origem, sem copiar ou renomear esses trials.

Os gates são copiados para `gate-proofs/` dentro da nova saída. O core revalida essas cópias, sem reescrever a origem. Catálogo, imagem imutável, 19 arquivos do harness, candidatos, prompts, testes e isolamento permanecem iguais. Os 11 TaskSpecs são comparados integralmente com a triagem original. A única seleção diferente é excluir o caso monetário já executado.

Os limites continuam sendo 1.200 segundos e 60 chamadas por trial, com 15 segundos de graça, e 21.600 segundos globais para a continuação. O limite global é verificado antes de cada bloco, como no executor original. O OAuth é validado por bloco; fontes, agenda, evidências de origem e cópias dos gates são verificadas antes de cada trial. Há parada após `infra_error` ou `scope_violation`; trials restantes continuam visíveis como `not_run`, e uma continuação incompleta retorna erro.

O preflight valida baseline/referência, Docker, namespace, imagem e configurações dos providers sem inferência. Se ficar bloqueado, a saída informa o motivo e registra zero chamadas. Não reutilize uma saída existente: escolha outro `--out` para uma tentativa nova.

Para inspecionar a agenda ou validar os 11 casos sem modelos nem Docker, use `plan` ou `validate` no lugar de `run`, com uma saída nova. Esses dois comandos podem executar enquanto a origem monetária está em andamento. `preflight` e `run` exigem sua conclusão. `report` atualiza somente os relatórios da continuação.

Verificação local:

```sh
python3 -B -m unittest discover -s implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest -p test_run.py
```

Os testes de execução substituem somente o acesso ao modelo/ambiente por fixtures temporárias; plano e validação exercitam o core real. Não executam chamadas de modelos nem escrevem na rodada monetária.
