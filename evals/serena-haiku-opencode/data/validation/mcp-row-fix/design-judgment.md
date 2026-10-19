# Julgamento dos desenhos

Notas de 0–2 sobre os sketches atuais:

| Critério | A | B |
|---|---:|---:|
| Sucesso somente com conexão e superfície exatas | 1 | 1 |
| Recibo e progresso sobrevivem à falha | 2 | 2 |
| Ausência de segredos | 2 | 2 |
| Menor API | 2 | 1 |
| Verificação capaz de falhar, sem inferência | 2 | 2 |
| Total | 9 | 8 |

**Base: A.** Mantém assinaturas e exceções; runtime possui o protocolo e a projeção sanitizada, bench possui publicação e progresso. A cópia em `finally`, ainda dentro de `TemporaryDirectory`, satisfaz sobrevivência às falhas tratadas sem acrescentar callback ou exceção como transporte de evidência.

**Graft:** incorporar de B os snapshots explícitos antes de validar cada resposta, códigos fechados de erro e preservação incremental das descobertas anteriores. Usar uma projeção única por allowlist, incluindo superfície malformada como classificação segura; nunca copiar auth, environment, comandos desconhecidos ou erro bruto.

Ambos perdem um ponto no sucesso porque os sketches não incorporam a barreira de `invoke`. Extrair uma espera privada compartilhada entre `audit` e `invoke`: nativo exige ausência de MCP e catálogo nativo exato; Serena aceita ausência/pending temporários, aprovando somente uma entrada Serena connected e catálogo direto canônico exato. Aplicá-la antes de sessão/prompt. O relógio permanece iniciado antes do boot; espera MCP consome o limite existente, sem iniciar inferência após esgotá-lo.

Provar sem modelo: vazio→pending→connected, vazio até timeout, linha malformada, servidor extra/duplicado, superfície errada, recibo/progresso após exceção e nenhuma sessão/prompt antes da prontidão. Preservar full-1/full-2, casos, 120 trials, papéis, medium/high e caps.

Limitações: `finally` não garante persistência após encerramento abrupto; full-2 não preservou a resposta MCP, portanto sua causa concreta permanece desconhecida. Doc Delta: README/DESIGN precisam refletir barreira e evidências na implementação.
