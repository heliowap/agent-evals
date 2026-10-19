# Candidato A: recibo privado do runtime

## Uso

`runtime.audit(root, work, configuration, case, args, env, expected)` mantém assinatura e exceções atuais. Escreve `root/discovery-receipt.json` desde a entrada e antes de cada validação; seu `finally` atualiza contagem de inferência, fase e desfecho.

`bench.preflight(out, args)` inicializa `stages.native_opencode_discovery` antes do loop; registra configuração/papel/caso corrente imediatamente e persiste progresso após cada descoberta. Seu `finally`, dentro de `TemporaryDirectory`, copia o recibo sanitizado para `out/discovery/<configuration>-<role>.json`, inclusive em falha. Usa `save`/`copyfile` existentes; nenhuma API pública nova.

## Tipos e assinaturas privadas

`DiscoveryReceipt = {configuration, role, case, phase, attempts: list[McpObservation], sources, effective_mcp, observed_surface, model_inference_calls, outcome}`.

`McpObservation = {attempt, elapsed_s, envelope_shape, row_count, rows: list[SafeMcpRow]}`.

`SafeMcpRow = {name_class: serena|unexpected|invalid, status_shape, state: pending|connected|disabled|failed|needs_auth|invalid, integration_id_present}`.

`_receipt_snapshot(root, context, observations) -> None`: corpo não implementado; grava atomicamente projeção por allowlist. Configuração efetiva preserva fontes relativas, estrutura MCP, campos nativos conhecidos e identidade do comando reconhecido; auth, environment, comandos desconhecidos e erros brutos são omitidos. Superfície observada é projetada antes de `surface()` validar.

`validate_mcp_status(value) -> bool`: corpo não implementado; envelope válido com `[]` ou Serena `pending` retorna falso. Apenas uma linha Serena estruturalmente válida `connected` retorna verdadeiro. Outros estados, duplicatas, nomes extras ou formato inválido falham. Prazo esgotado continua falha; catálogo direto exato continua obrigatório.

## Justificativa

Runtime possui protocolo, sanitização e recibo; bench possui publicação/progresso. Nenhum escritor compartilha o recibo mutável. Documento muda para `mcp.servers.serena`; campos nativos permanecem. Full-2 não preservou a resposta MCP: causa concreta segue desconhecida.

Alternativa: exceção tipada carregando recibo exige consumidores conscientes do transporte de evidência. A reduz essa superfície, aceitando convenção de caminho privado.

Verificação: `[]→pending→connected`, `[]` até timeout, linha nomeada malformada e recibo/progresso em falha; zero inferência. Preservar 32 testes Python, 7 Node, 120 trials, medium/high, limites e freeze.
