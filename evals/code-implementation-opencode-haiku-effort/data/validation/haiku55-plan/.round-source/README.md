# Haiku 5.5 no eval completo de implementação

Esta rodada compara Haiku 5.5 nos esforços `low`, `medium`, `high`, `xhigh` e `max`, usando OpenCode 2.0.26 e a rota `cli_proxy/cpa-claude-haiku-5-5`. O modelo enviado ao CLIProxy é `claude-haiku-5-5`. O alias e as variantes são declarados na configuração privada; a execução não importa a configuração global do usuário.

Execute da pasta `evals`:

```sh
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py run \
  --out implementacao/opencode-implementador/results/haiku-5-5
```

O comando executa cinco provas de interrupção por orçamento, cinco smokes e 180 trials comparativos: 12 casos, três repetições e cinco esforços. São 190 sessões sequenciais. Os dois gates são novos para esta coorte e precisam passar antes da triagem. Na prova de orçamento, `budget_exceeded` com `proof_passed=True` é esperado; `accepted` permanece falso.

A triagem conserva integralmente onze TaskSpecs da rodada original e substitui apenas o Python monetário pelo TaskSpec corrigido de `money-contract-v2`. O caso TypeScript monetário também faz parte dos 12 casos. Arquivos iniciais, referência, testes privados e regras de aprovação são os mesmos dessas fontes. As ambiguidades já registradas no contrato de perfil e no envelope da importação permanecem; esta rodada não acrescenta requisitos a esses enunciados.

A prova de orçamento permite 20 segundos e duas chamadas. Smoke e triagem permitem 1.200 segundos e 60 chamadas por sessão, com 15 segundos de tolerância do controlador. Cada fase mantém o limite global de seis horas e a seed original. As configurações são alternadas em blocos de caso e repetição. O catálogo congelado e a imagem Docker por SHA são os mesmos da rodada original; uma imagem ausente bloqueia o preflight.

O catálogo congelado ainda não inclui Haiku 5.5. Por isso `runtime.configuration()` registra explicitamente as cinco variantes Anthropic, mantendo os limites do experimento: 272.000 tokens de contexto e 32.768 de saída. Nenhum outro trecho do runtime muda. O audit nativo precisa encontrar o alias, o modelo enviado e o esforço selecionado. As chamadas observadas precisam conservar modelo, esforço, rota, sessão e `thinking_type=adaptive`. Essa identidade não atesta o backend a montante do CLIProxy.

O núcleo difere do baseline somente na coorte de `domain.py`, na seleção de `tasks.py`, no registro das variantes em `runtime.py` e no novo `contract.py`. Os demais arquivos mantêm os bytes congelados. O wrapper verifica que cada alteração corresponde exatamente a esses limites antes de importar o núcleo. O core verifica os hashes dos 19 arquivos de harness antes de cada trial. Wrapper, README, testes, proveniência, agenda e orçamento externos são verificados antes e depois de cada fase; o loop de trials permanece o original.

`plan` congela as agendas 5/5/180 sem chamar modelos. `validate` também executa os projetos e referências dos 12 casos sem chamar modelos. `preflight` verifica Docker, isolamento e descoberta nativa sem inferência. Todos usam a mesma CLI e exigem uma saída nova. `--phase budget` limita a sequência ao primeiro gate; `--phase smoke` inclui ambos; `--phase screening` equivale ao padrão `all`.

Cada fase escreve em `budget/`, `smoke/` ou `screening/`. `round-freeze.json` registra as fontes, comandos e agendas. `round-summary.json` reúne o estado das fases e a contagem de chamadas. Para atualizar somente os relatórios de uma saída existente, use `report --out CAMINHO`. Os rótulos dos relatórios derivados são ajustados para cinco configurações, sem alterar o gerador congelado.

Falhas de gates, infraestrutura, escopo, alterações de fontes ou fases incompletas interrompem a sequência e mantêm as tentativas restantes visíveis. Uma reprovação funcional na triagem não impede os demais trials. O resultado mede execução e aceitação nesses pequenos projetos; não demonstra ausência geral de bugs ou brechas de segurança. Nenhum candidato é promovido automaticamente.
