# Verificação da implementação

Os gates reais `budget-r4` e `smoke` passaram nos seis candidatos, e a triagem original terminou seus 216 trials. A revisão específica do contrato monetário terminou com 18/18 aprovações no Terminal do usuário. Os registros abaixo conservam as verificações e os incidentes anteriores.

O resultado consolidado está em [verification.json](verification.json). Foram executados 26 testes Python e 12 testes JavaScript, todos aprovados. A validação pela CLI admitiu os 12 casos de triagem e os oito casos inéditos de confirmação: baseline com regressões públicas verdes e requisito novo vermelho; referência com todos os critérios verdes. Em refatorações, o requisito estrutural público distingue baseline e referência.

Os testes rejeitaram 26 alterações incompletas nas fixtures e verificaram regressões do próprio executor: saída antecipada com código zero, Promise que não termina, adulteração de verificações públicas, symlink, limite nativo de passos, erro de transporte e limite excedido após o término do processo. Os testes de plugin usam eventos e processos locais controlados; não são prova de funcionamento no servidor nativo.

As agendas congeladas contêm 6 provas de interrupção, 6 sessões smoke, 216 de triagem e 80 de confirmação: 308 sessões se todas as fases forem executadas. Os dois candidatos do manifesto de confirmação são exemplos para verificar a contagem, e não finalistas escolhidos.

A tentativa real de `run --phase budget --build-image` terminou no preflight com acesso negado ao socket Docker. Nenhuma sessão foi iniciada, nenhuma imagem construída e nenhuma inferência realizada. Docker, ativação dos plugins, configuração efetiva e interrupção nativa ainda precisam passar nos gates reais. A disponibilidade do daemon fora deste sandbox é desconhecida.

Evidências:

- [Testes Python](unittest-final.log) e [testes JavaScript](node-tests.log).
- [Validação da triagem](offline-screening/validation.json) e [da confirmação](offline-confirmation/validation.json).
- [Bloqueio do gate](budget-gate-attempt/preflight.json).
- [Decisões](../decisions.tsv).

A revisão independente inicial encontrou três falhas corrigidas com testes de regressão. Uma nova revisão das correções não concluiu; os resultados finais acima vêm da execução dos testes. Os subagentes usaram a mesma família disponível, sem revisão por outra família. A revisão de comentários removeu duas docstrings redundantes; não houve restauração, suppressions, restrições para codificar ou redesenho por comentários. Não existe `agent-transcripts/` neste workspace; o ledger foi conferido contra as ações e evidências deste turno.

Para repetir a verificação de código, execute neste diretório pai:

```sh
python3 -B -m unittest discover -v
node --test test_terminal.mjs test_observer.mjs
```

Para os gates reais, siga os comandos no [README do executor](../README.md). Use novos diretórios de saída. A métrica de tempo é a invocação do agente, incluindo seus testes, antes da parada externa do container; preparação e grading são registrados separadamente.

A rodada posterior do usuário em `results/budget-r2` passou isolamento, versões e auditoria, mas o primeiro trial falhou após duas chamadas de modelo. O terminal devolvia `output` sem schema e a CLI recebia `session.export`, cujo identificador público é `experimental.session.export`. As correções passaram nos [22 testes Python focais](native-contract-fix-python.log), nos [12 testes JavaScript](native-contract-fix-node.log) e no [validador nativo do terminal](native-terminal-fix.log). Este último usa o checkout core 2.0.22 e seu Effect fixado; não substitui a prova com o binário 2.0.26. O preflight passou a exportar uma sessão vazia sem inferência, e o controlador salva `control.json` antes da exportação. A confirmação dos gates corrigidos permanece pendente.

A rodada `results/budget-r3` concluiu as seis interrupções, com 12 chamadas de modelo. Cinco provas passaram; a do DeepSeek falhou devido ao observador, que tentava fechar um stream já cancelado após uma leitura pendente. Essa sequência foi reproduzida antes da correção. Passaram depois [13 testes Node](observer-cancel-fix-node.log), [9 testes do observador no Bun](observer-cancel-fix-bun.log) e [22 testes Python focais](observer-cancel-fix-python.log). Falhas reais de leitura permanecem visíveis; falhas de cancelamento são propagadas e registradas com seu código. Os artefatos `budget-r3` continuam inalterados e o gate permanece reprovado nessa rodada. É necessário um novo gate após a correção.

## Revisão específica do contrato monetário

A rodada em [money-contract-v2](../rounds/money-contract-v2/README.md) explicita a gramática ASCII das strings, os erros de tipo da API e a independência da precisão decimal. Só o pedido e sua cópia no README do projeto mudam. Aceitação privada, referência, código inicial e testes públicos permanecem iguais.

O [plano congelado](money-contract-v2-plan/freeze.json) tem 18 trials de um caso, seis candidatos e três repetições. A [validação real de baseline e referência](money-contract-v2-validate/validation.json) passou sem inferência. Os [13 testes do runner](money-contract-v2-tests.log) passaram, incluindo preservação dos gates, alteração do contrato barrada antes da execução e fixação da agenda e do orçamento. A revisão independente pela mesma família GPT não encontrou outro defeito material.

A [tentativa neste sandbox](money-contract-v2-run-attempt/preflight.json) foi bloqueada por permission denied no socket Docker. Seu resumo conserva zero trials iniciados e zero chamadas de modelo. A execução posterior do usuário concluiu [18/18 trials](../results/money-contract-v2/summary.json) e 105 chamadas, com aprovação de compilação, regressão, aceitação e escopo nos seis candidatos. A [análise verificada](money-contract-v2-analysis.json) conserva as métricas e os hashes de origem. A comparação completa e sua ressalva adicional sobre o envelope de `py-atomic-import` estão no [relatório de resultados](../../../implementacao-opencode-resultado.md).

## Sol low Fast e GLM Flash

A [nova coorte](../rounds/money-sol-low-glm-flash/README.md) contém Sol 6.1 low Fast, GLM 5.3 Flash high e GLM 5.3 Flash max. O plano congela 15 sessões, com três provas de interrupção, três smokes e nove execuções do mesmo contrato monetário corrigido. Runtime, controlador, isolamento e grader preservam os bytes originais. A imagem é selecionada pelo SHA256 anterior e o catálogo também permanece igual.

Passaram os [12 testes do runner](money-extra-models-tests-r2.log), a CLI de [plano](money-extra-models-plan-r2/round-freeze.json) e a [validação real do caso](money-extra-models-validate-r2/screening/validation.json), sem inferência. A [tentativa neste sandbox](money-extra-models-run-attempt-r2/budget/preflight.json) foi bloqueada no socket Docker com zero chamadas de modelo. Depois, a execução no Terminal do usuário aprovou os gates reais de [budget, 3/3](../results/money-sol-low-glm-flash/budget/summary.json) e [smoke, 3/3](../results/money-sol-low-glm-flash/smoke/summary.json), cobrindo as três variantes nativas. As decisões anteriores estão no [registro de trabalho](money-extra-models-work.md).

## Continuação da triagem completa

O escopo completo dessa coorte tem 12 casos, três configurações e três repetições, totalizando 108 trials comparativos. O [runner complementar](../rounds/sol-low-glm-flash-rest/README.md) executa os outros 11 casos, 99 trials, após os nove monetários corrigidos. Mantém o caso TypeScript `ts-money-consolidation` e exclui somente o Python `py-money-contract` já substituído pelo contrato corrigido. Os gates aprovados são copiados para a nova saída e revalidados nas cópias. As evidências de origem permanecem somente leitura.

A verificação independente aprovou os [15 testes](sol-low-glm-flash-rest-tests.log), o [plano real de 99 sessões](sol-low-glm-flash-rest-plan/round-freeze.json) e a [validação real dos 11 casos](sol-low-glm-flash-rest-validate/validation.json), sem chamadas de modelos. A [conferência de 32 hashes](sol-low-glm-flash-rest-origin-check.json) não encontrou alterações nas fontes e provas protegidas da origem. A [tentativa prematura de preflight](sol-low-glm-flash-rest-preflight-attempt.log) bloqueou por origem monetária incompleta, antes de criar saída. A execução nativa da continuação ainda depende da conclusão dos nove trials monetários e de seu próprio preflight. Detalhes e limites constam no [registro de trabalho](sol-low-glm-flash-rest-work.md).

## Resultado completo de Sol low Fast e GLM Flash

A execução posterior concluiu os nove trials monetários e os 99 complementares. A [análise final](sol-low-glm-flash-final-report.md) cobre 108 trials, 12 casos e três repetições por configuração. Foram 100 aprovações completas e 104 patches aprovados, com 762 chamadas comparativas e 18 nos seis gates.

Sol low Fast teve 35/36 aprovações completas e 36/36 patches aprovados; GLM high, 34/36 e 35/36; GLM max, 31/36 e 33/36. As medianas dos aprovados foram 28,34 s, 47,92 s e 194,06 s. O relatório separa rejeição funcional, interrupção, transporte e observação incompleta. Também registra a ambiguidade do contrato de tags duplicadas.

Os [dados e hashes](sol-low-glm-flash-final-analysis.json) conservam as verificações de solicitações, grades, controles e sessões. A [conferência independente](sol-low-glm-flash-final-root-check.json) confirmou 1.250 arquivos intactos. Outra revisão da família GPT reproduziu contagens, tempos e causas, sem findings materiais. Nenhum revisor de outra família estava disponível. Os resultados não atestam novidade perante treinamento nem ausência geral de bugs ou brechas.

## Haiku 5.5 nos cinco esforços

O [novo pacote](../rounds/haiku-5-5/README.md) compara `low`, `medium`, `high`, `xhigh` e `max` pela rota CLIProxy no OpenCode. A agenda tem cinco provas de orçamento, cinco smokes e 180 trials comparativos. Os dois gates precisam passar para a triagem começar. O corpus conserva onze casos originais e o Python monetário corrigido, incluindo também o TypeScript monetário.

Passaram os [20 testes](haiku55-tests.log), o [plano real](haiku55-plan/round-freeze.json) e a [validação real dos 12 casos](haiku55-validate/screening/validation.json), sem inferência. A [conferência independente](haiku55-root-check.json) verificou 36 trials por esforço, os deltas exatos do pacote e os 1.250 hashes anteriores. Quinze arquivos do harness mantêm os bytes originais; só a coorte, a seleção monetária e o registro privado das variantes mudam, com `contract.py` acrescentado.

A [tentativa real de preflight](haiku55-preflight-attempt/budget/preflight.json) bloqueou no socket Docker, sem sessões iniciadas ou chamadas de modelo. O registro local e os testes do audit não substituem descoberta nativa e inferência. Essas provas continuam pendentes no Terminal do usuário. A revisão de comentários encontrou zero comentários, docstrings ou suppressions novos, sem alterações. A [revisão final](haiku55-review.md), pela mesma família GPT, não encontrou defeitos materiais. O [registro de trabalho](haiku55-work.md) documenta o alcance dos guardas por trial e por fase.

