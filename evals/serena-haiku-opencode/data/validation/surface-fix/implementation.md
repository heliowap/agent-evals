# Correção do gate de ferramentas

Produção estabilizada em domain.py, runtime.py e surface.js. Nenhum resultado histórico, configuração do operador ou credencial foi alterado. O comando público e o cronograma permanecem iguais.

O baseline explorador agora deriva read/glob/grep, sem o builtin list inexistente. O documento privado remove apenas opencode.browser além da remoção anterior de skills. Serena declara codemode:false e usa o schema MCP nativo do binário fixado: disabled:false e timeout com startup/catalog/execution de 180000 ms. A permissão execute continua negada.

O recibo raw do catálogo inclui ID, nome exposto, nome bruto, namespace, CodeMode e ação efetiva de permissão. runtime.surface exige identidade canônica ID igual ao nome, exposição direta estritamente false e ação de permissão igual ao nome permitido; mantém unicidade, conjunto exato e rejeição de qualquer ferramenta inesperada. runtime.audit recusa browser builtin registrado mesmo se um recibo exato anterior existir. A comparação do documento privado completo, plugins externos, permissões globais/agente e status MCP permanece.

A regressão Node recompôs transforms em ordem a partir do estado inicial e comprovou uma falha adicional: o callback intermediário do filtro apagava allowedIds antes de o MCP posterior ser acrescentado. O guard passou a comparar o ID concreto recebido com o conjunto canônico derivado, cuja equivalência com nome é exigida pelo gate e fundamentada em In(e) no binário fixado. Isso remove estado mutável e consulta por chamada; ferramentas desconhecidas e execute continuam recusados. O terminal host continua substituído pelo terminal Docker.

Antes da correção, seis testes Python novos reprovaram sete vezes e produziram dois erros; três testes Node novos reprovaram, preservando os quatro anteriores verdes. A regressão posterior do schema MCP produziu quatro erros antes da alteração declarativa. Ao final, 32 testes Python e sete Node passaram. Foram geradas oito configurações privadas reais por runtime.prepare, sem autenticação e sem inferência, cobrindo medium/high e os dois braços para ambos os papéis. O replay confirma a superfície direta exata e conserva a observação de 45 ferramentas browser adicionadas depois do filtro quando sua remoção privada é omitida.

Evidências: implementation-proof.json, logs implementation-*-red/green-final, implementation-private-configs-r2.json, implementation-replay.json e implementation.patch. O replay anterior foi corrigido para aplicar todas as transforms em ordem, mantendo replay-red.txt como evidência histórica.

Esta validação não executou discovery nativo completo nem Docker. O replay é uma simulação fundamentada no fonte fixado; o preflight nativo ainda precisa passar. Zero chamadas de modelo.
