# Continuação da triagem completa

O escopo correto é executar os 12 casos de triagem para Sol 6.1 low Fast e GLM 5.3 Flash high e max. A rodada já iniciada executa nove trials do contrato Python monetário corrigido. A continuação executa 99 trials dos outros 11 casos, incluindo `ts-money-consolidation`, sem repetir os gates ou o caso Python monetário.

## Etapas

- [x] Ground. Conferido o executor ativo e o comportamento de escrita de `require_gate`.
- [x] Sketch. Comparados seleção explícita por funções e troca de inventário em memória.
- [x] Agree. Escolhida seleção explícita, com selo externo e cópias privadas dos gates.
- [x] Implement. Um proprietário escreveu o novo runner e seus testes.
- [x] Scrap. Não foi necessário redesenhar. Os controles existentes couberam na seleção explícita e nas cópias dos gates.
- [x] Verify. Plano real de 99 sessões, baseline/referência dos 11 casos e 15 testes do loop e dos selos passaram.

## Execução e responsabilidades

- Blocking first steps. Preservar as fontes ativas, conferir gates concluídos e exigir conclusão monetária antes de novas chamadas.
- Independent workstreams. Desenhos independentes concluídos. Um proprietário implementa; o coordenador verifica e documenta fora da pasta ativa.
- Shared mutable state. A rodada monetária fica somente leitura. O restante usa saída própria e cópias dos gates, sem alterar a origem.
- Smallest safe decomposition. Um proprietário reúne agenda, guardas e execução porque esses invariantes se cruzam.

## Escolha

Seleção explícita recebeu 10/10 e troca de inventário em memória recebeu 8/10. A escolha mantém o core intacto, evita mudanças invisíveis a seu guard e preserva o loop de controles por meio das funções existentes. O selo externo também confere a seleção e a agenda antes de cada trial.

O [snapshot inicial](sol-low-glm-flash-rest-origin-before.json) registra 32 arquivos estáveis de fontes e provas da origem. Não inclui resumos ou relatórios que o processo ativo ainda pode atualizar.

Revisões usam a família GPT disponível. A prova nativa dos três candidatos e do executor já passou nos gates da origem; isso não substitui a verificação do novo adapter.

## Verificação

O coordenador executou os [15 testes](sol-low-glm-flash-rest-tests.log) e leu as evidências das CLIs reais de [plan](sol-low-glm-flash-rest-plan/round-freeze.json) e [validate](sol-low-glm-flash-rest-validate/validation.json). A agenda possui 99 combinações, com 33 por configuração. Os 11 TaskSpecs são iguais aos originais e conservam `ts-money-consolidation`. O orçamento segue em 1.200 segundos, 60 chamadas e 15 segundos de graça por trial.

O princípio Prove It Works orientou a validação pela CLI real, além dos testes com modelos substituídos por fixtures. O princípio Separate Before Serializing Shared State orientou o uso de saída própria e cópias dos gates. O [snapshot inicial](sol-low-glm-flash-rest-origin-before.json) e a [conferência final](sol-low-glm-flash-rest-origin-check.json) demonstram 32 arquivos protegidos sem alterações.

O [preflight prematuro](sol-low-glm-flash-rest-preflight-attempt.log) recusou a origem incompleta, antes de criar a saída e sem inferência. A execução dos 99 trials permanece para o Terminal do usuário depois dos nove monetários. O novo preflight verificará Docker, namespace, imagem e providers antes de inferência.

A revisão de comentários e docstrings não encontrou flags. GPT-5.6 Sol revisou código e trilha, sem bloqueadores funcionais. A revisão é da mesma família GPT, pois outras famílias não estão disponíveis para os subagentes desta sessão.

O revisor identificou um detalhe cosmético. O core escreve "As seis configurações" nos relatórios privados de `gate-proofs/`, embora a coorte tenha três. O relatório principal corrige esse rótulo. As contagens numéricas, gates, hashes e chamadas permanecem corretos. A correção desse rótulo nas cópias fica pendente, sem afetar a execução ou a decisão. Ela poderia ocorrer nos relatórios derivados sem modificar o core.
