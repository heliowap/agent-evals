# Revisão final da correção MCP

Data: 2026-10-12. Revisão somente leitura, comparada diretamente a `results/full-2/frozen-source`. Produção examinada: `runtime.py`, `bench.py`, `test_bench.py`; documentação examinada: `README.md` e `DESIGN.md`. Este relatório conserva o estado em que o achado foi reproduzido; correções posteriores devem ter sua resolução registrada separadamente.

## Achado priorizado

### P2 — Catálogo histórico completo admite uma superfície atual incompleta

**Local exato:** `runtime.py:149-153`, consumido pela nova barreira em `runtime.py:302-305` e por `invoke` em `runtime.py:489`.

`surface()` procura todas as linhas que já tiveram o conjunto exato de ferramentas e retorna a última dessas linhas. Uma observação posterior contendo apenas um subconjunto permitido não invalida essa aprovação. Assim, um log com nove ferramentas esperadas de exploração Serena seguido de uma linha com apenas `read/glob/grep` é aceito. Com a resposta MCP atual `serena/connected`, `_wait_readiness()` retorna e `invoke()` cria a sessão e lança o processo da tarefa usando a prova antiga, embora a última superfície observada não tenha as ferramentas Serena.

Isso permite admitir um trial de tratamento sem comprovar seu catálogo atual e pode comprometer a comparação com o braço nativo. A seleção histórica já existia na fonte congelada; a correção passa a utilizá-la também como barreira antes de cada trial. O achado trata dessa garantia nova, não atribui uma ocorrência dessa condição a `full-2`.

**Reprodução determinística, sem servidor ou modelo:** escrever duas linhas em `surface.jsonl`: primeira com os nove nomes de `allowed_tools('exploration', 'serena')`, segunda somente com os três nomes nativos. Todas as ferramentas têm `id == name`, `codemode: false` e `permission == name`. A chamada real `runtime.surface()` retornou:

```json
{"accepted": true, "accepted_tool_count": 9, "latest_tool_count": 3, "latest_is_exact": false}
```

Uma segunda reprodução chamou o `invoke()` real, substituindo somente `local_server`, `api` e `subprocess.Popen` por mocks locais. `mcp.list` respondeu conectado e o processo mock terminou imediatamente. Resultado:

```json
{"events": ["mcp.list", "session.create"], "status": "task_launched", "latest_tools": 3, "required_tools": 9, "calls_at_exit": 0}
```

**Correção sugerida:** exigir que a última observação tenha o conjunto exato antes de aprovar. Conservar as rejeições de ferramentas extras, duplicatas, identidade incorreta, Code Mode e permissão incorreta em todo o histórico. Uma regressão deve cobrir `exato → incompleto → exato`, comprovando que a linha intermediária impede sessão/prompt até a recuperação ou o prazo.

## Verificação e demais pontos

- `python3 -B -m unittest test_bench`: 42 testes passaram no estado identificado abaixo.
- `node --test test_surface.mjs`: 7 testes passaram.
- O documento grava `mcp.servers.serena` com os campos nativos em `runtime.py:92-94`; o probe usa esse mesmo caminho em `runtime.py:429`. Conferência direta no binário fixado confirmou o wrapper `servers` e o status MCP como objeto discriminado.
- `validate_mcp_status()` em `runtime.py:609-626` bloqueia nomes extras, duplicatas, linha/status malformados e estados terminais. Vazio e pending permitem somente espera limitada. O braço nativo exige lista MCP vazia em `runtime.py:297-299`.
- A espera compartilhada precede `session.create`; o prazo da tarefa deriva do relógio iniciado antes do servidor em `runtime.py:483-503`. Há nova checagem de orçamento antes de lançar o processo. Não identifiquei reinício do relógio ou do limite de chamadas.
- Observações MCP são projetadas e salvas antes da validação em `runtime.py:288-295`. Configuração, superfície e inferências entram nos snapshots sem copiar comando, environment, credencial ou erro bruto do servidor. A publicação no `preflight` ocorre no `finally` interno em `bench.py:147-161`, antes do cleanup temporário, conservando progresso anterior e a configuração em andamento.
- A lacuna de cópia dos diagnósticos de `invoke`, comunicada pela raiz durante esta revisão, já estava corrigida no estado final examinado: `bench.py:271-276` conserva os três arquivos no `finally`; a regressão `test_bench.py:254-286` passou. Não é achado pendente deste relatório.

Nenhum outro bug concreto foi identificado dentro do foco solicitado. Não houve campanha, chamada de modelo, mudança em produção, configuração do operador, casos, modelos ou resultados históricos. A integração nativa completa não foi executada; a resposta original de `full-2` não existe no material preservado, portanto sua causa concreta permanece desconhecida.

Doc impact: sim — README e DESIGN refletem wrapper nativo, recibos, progresso e orçamento; a promessa de superfície exata antes do prompt depende da resolução do P2 acima.

## Identidade do estado revisado

| Arquivo | SHA256 |
|---|---|
| `runtime.py` | `ac162967e4d1f0786ff698a19aeca1e79145300f68e272da6f1d1676d0dcecd6` |
| `bench.py` | `a5ca377434d8c3769a8534130fc4cb75125de466975a429179521bc51410c8b2` |
| `test_bench.py` | `2232977a25d6c09dcb0734141ebcccc4b18cc9667b54b886516282908ed069db` |
| `README.md` | `b501465a114e5315ab3be01e29c798dd8197bd4896d8c166ae7648acdf71e44e` |
| `DESIGN.md` | `f176209526ccf875bbac8e2b5b2bcc8187c3451140e6e4b54cd08f5cb21b454c` |
