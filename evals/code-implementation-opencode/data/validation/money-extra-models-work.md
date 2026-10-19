# Nova coorte do contrato monetário corrigido

Pedido de 2026-10-11. Comparar Sol 6.1 low Fast, GLM 5.3 Flash high e GLM 5.3 Flash max no mesmo caso monetário corrigido, com três repetições por configuração.

## Etapas

- [x] Ground. Traçar o runner monetário, o núcleo congelado e a verificação dos gates.
- [x] Sketch. Comparados composição do núcleo existente e pacote independente.
- [x] Agree. Escolhido pacote independente sobre o CLI congelado, dentro do escopo autorizado.
- [x] Implement. Runner e testes implementados por um proprietário. O coordenador corrigiu a contagem no relatório derivado.
- [x] Scrap. Não necessário; os invariantes couberam no desenho escolhido.
- [x] Verify. CLI de plano, validação confiável e 12 testes passaram. Tentativa real bloqueada no Docker antes de inferência; gates novos e comparação aguardam o Terminal do usuário.

## Execução e responsabilidades

- Blocking first steps. Confirmar as variantes no catálogo, preservar o contrato e verificar a origem das fontes. Gates novos precisam passar antes dos nove trials comparativos.
- Independent workstreams. Leitura do catálogo e dois desenhos usam saídas independentes. A implementação terá um proprietário; documentação e verificação ficam com o coordenador.
- Shared mutable state. Fontes e resultados antigos são somente leitura. Cada fase nova usa diretório próprio, e sessões com modelos continuam sequenciais.
- Smallest safe decomposition. Um proprietário implementa o runner porque agenda, proveniência e gates compartilham invariantes.

## Critérios de escolha

1. Preservar literalmente o contrato corrigido, código inicial, referência, aceitação e escopo.
2. Conferir candidatos, variantes e budgets antes da inferência; não aproveitar gates de outras configurações.
3. Congelar as fontes e o catálogo e rejeitar alterações durante a rodada.
4. Oferecer um comando que execute três provas de interrupção, três smokes e nove trials monetários em sequência.
5. Manter o menor código adicional que respeite os invariantes, sem alterar o núcleo histórico.

Os modelos de famílias distintas indicados nas skills não estão disponíveis nas ferramentas de colaboração desta sessão. Os desenhos e a revisão usam o modelo herdado; não serão apresentados como revisão entre famílias.

## Evidência final

O [plano](money-extra-models-plan-r2/round-freeze.json) contém 3 provas de interrupção, 3 smokes e 9 trials monetários. A [validação](money-extra-models-validate-r2/screening/validation.json) executou baseline e referência reais sem inferência. Os [12 testes](money-extra-models-tests-r2.log) passaram após a correção da contagem de configurações nos relatórios derivados.

A [tentativa real](money-extra-models-run-attempt-r2/budget/preflight.json) registrou acesso negado ao socket Docker e zero chamadas de modelo. Ela não confirma a descoberta nativa das três variantes no binário 2.0.26. O [snapshot de hashes históricos](money-extra-models-history-before.json) conserva 25 arquivos de evidência e fontes anteriores; todos permaneceram iguais.

A revisão dos desenhos atribuiu 8/10 à composição por importação e 9/10 ao pacote sobre o CLI congelado. A revisão de comentários não encontrou flags. A revisão final de código usa GPT-5.6 Sol, da mesma família disponível, sem revisão por outra família.
