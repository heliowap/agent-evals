# Rodada final Haiku 5.5

## Etapas

- [x] Ground. Conferidos executor, configuração privada, modelo global e registro CLIProxy.
- [x] Sketch. Comparados CLI congelado e adapter explícito.
- [x] Agree. Escolhido CLI congelado, 10/10 contra 8/10, com selo externo.
- [x] Implement. Um proprietário escreveu pacote novo e vinte testes.
- [x] Scrap. Os deltas exatos conservam o loop e os controles; não foi necessário trocar o desenho.
- [x] Verify. Plano e validação reais passaram, hashes conferidos e preflight tentado.

## Execução e responsabilidades

- Blocking first steps. Confirmar as cinco variantes e preservar o corpus existente. Gates novos precedem os 180 comparativos.
- Independent workstreams. A consolidação de Sol/GLM escreve apenas sua análise e seu relatório. Haiku recebe um proprietário separado no novo diretório.
- Shared mutable state. Fontes e saídas existentes permanecem somente leitura. O coordenador cuida do índice e da documentação externa.
- Smallest safe decomposition. Um proprietário reúne candidatos, inventário, declaração privada e wrapper porque seus hashes e gates dependem uns dos outros.

## Evidências e limites

A configuração local declara `cpa-claude-haiku-5-5` com `modelID` `claude-haiku-5-5` e cinco variantes. O registro `~/VSCode/Lab/CLIProxyAPI/internal/registry/models/models.json` também contém o modelo e os cinco esforços. A [documentação oficial](https://platform.claude.com/docs/en/build-with-claude/effort) confirma low, medium, high, xhigh e max para Haiku 5.5, com medium como padrão. Pensamento adaptativo deve permanecer ativo.

A listagem HTTP de `127.0.0.1:8317/v1/models` ficou bloqueada por EPERM neste sandbox, sem inferência. Declaração local e registro não provam disponibilidade a montante. O preflight nativo e os dez gates de execução do novo pacote farão essa verificação no Terminal do usuário. Nenhuma descoberta nativa ou chamada de Haiku foi realizada ainda.

Passaram [20 testes](haiku55-tests.log), a CLI de [plano](haiku55-plan/round-freeze.json) e a [validação dos 12 casos](haiku55-validate/screening/validation.json). A [conferência independente](haiku55-root-check.json) confirma 5/5/180 sessões, 36 comparativas por esforço e 1.250 arquivos anteriores intactos. A [tentativa de preflight](haiku55-preflight-attempt/budget/preflight.json) bloqueou no socket Docker com zero sessões e zero inferência.

O core verifica os 19 arquivos do harness antes de cada trial. O wrapper verifica o envelope externo antes e depois de cada fase. O brief inicial dizia guard externo por trial; foi corrigido para conservar o loop original sem duplicar o scheduler nem alterar bench/controller. Agenda e fontes adulteradas, gates falhos e triagem incompleta são exercitados nos testes.

A revisão de comentários encontrou zero comentários, docstrings ou suppressions novos. A [revisão final de código](haiku55-review.md), por GPT-5.6 Sol, não encontrou defeitos materiais. Nenhum revisor de outra família estava disponível.

O princípio Separate Before Serializing Shared State manteve Haiku e Sol/GLM em artefatos independentes. Prove It Works foi aplicado à CLI e aos projetos reais, com o bloqueio nativo registrado separadamente.
