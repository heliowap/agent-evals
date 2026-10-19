# Completar a triagem do implementador

O usuário pediu a triagem completa. A rodada monetária já iniciada cobre um dos 12 casos e deve continuar intacta. A continuação seleciona os outros 11 casos originais, com três repetições dos mesmos três candidatos. São 99 trials adicionais e 108 comparativos no conjunto completo.

```sh
python3 -B implementacao/opencode-implementador/rounds/sol-low-glm-flash-rest/run.py run \
  --money-run implementacao/opencode-implementador/results/money-sol-low-glm-flash \
  --out implementacao/opencode-implementador/results/sol-low-glm-flash-rest
```

O comando deve começar depois da conclusão da rodada monetária. Falhas funcionais são resultados legítimos e não impedem a continuação; evidência incompleta ou violação de infraestrutura/escopo impedem novas chamadas.

## Forma escolhida

O novo runner importa o harness monetário existente sem alterar suas 19 fontes. Os 11 `TaskSpec` vêm de `tasks_python` e `tasks_typescript`, filtrados pela fase screening e pela exclusão de `py-money-contract`. Cada campo deve coincidir com o congelamento da triagem original. A tupla de `Candidate` continua a mesma da rodada iniciada.

As funções existentes recebem tarefas e candidatos explícitos. O runner chama `freeze`, `preflight`, `require_gate`, `run_trial` e `report`; ele não substitui funções nem inventários do core em memória. Seu pequeno loop conserva o limite global antes de cada bloco, verificação de OAuth por bloco, verificação antes de cada trial, relatório incremental, parada por infraestrutura/escopo e relatório final.

Os gates já concluídos são copiados para a nova saída. A verificação que reescreve relatórios opera somente nessas cópias. Origem, hashes, catálogo, imagem, coorte e limites precisam coincidir; nenhum gate é repetido ou afrouxado. O runner sela adicionalmente suas próprias fontes, os TaskSpec, a agenda e os hashes das evidências de origem, e confere esse selo antes de cada trial.

O diretório de saída é novo e fica fora da origem monetária. A continuação não escreve fontes, freezes, resultados ou documentação da execução já iniciada.

## Síntese e verificação

A seleção explícita por argumento recebeu 10/10 na revisão dos desenhos. A alternativa de trocar o inventário em memória recebeu 8/10 e foi rejeitada por acrescentar estado invisível ao guard original, além de passar provas originais a uma função que reescreve relatórios. Incorporamos dela o selo adicional do adapter e as verificações antes de cada trial.

Model the Domain mantém `TaskSpec` e `Candidate` como estruturas canônicas. Laziness Protocol mantém o núcleo e suas funções, sem outro controlador. Prove It Works exige plano real de 99 sessões e validação de baseline/referência dos 11 casos.

Os testes devem provar a agenda exata, exclusão do monetário, equivalência integral das tarefas, compatibilidade dos gates, conclusão prévia da origem, preservação das provas originais, limites e OAuth, parada após violação e rejeição de alterações nas fontes/dados. Plan e validate permanecem sem inferência.

A revisão dos desenhos usou a família GPT disponível. Gates reais cobrem o executor e as configurações; a nova seleção e seu selo exigem verificação própria.
