# Revisão independente da correção de superfície

Escopo: `domain.py`, `runtime.py`, `surface.js`, `test_bench.py` e `test_surface.mjs`, comparados com `results/full-1/frozen-source`. Leitura independente do diff, julgamento das propostas e trechos do fonte embarcado. Nenhuma alteração de produção, inferência, configuração do operador ou evidência histórica.

**Veredito:** nenhum P1; um P2 de reprodutibilidade dos testes do snapshot. O caminho de execução corrigido não apresentou outro achado no escopo.

## Achado P2

`test_bench.py:318` depende de `validation/surface-fix/observed-catalog.json`, que não integra o inventário de `bench.source_files()`. Reproduzi copiando o inventário atual de scripts raiz e `vendor` para um diretório temporário e executando somente `DirectSurfaceTests.test_exploration_baseline_matches_observed_native_catalog`: o teste falha com `FileNotFoundError`. No workspace completo o teste passa; isto não impede `run` ou `preflight`, mas o snapshot congelado não reproduz sozinho essa regressão. Correção mínima: usar fixture raiz congelada, ou conservar a prova histórica no relatório e tornar o teste autocontido.

## Conferências de execução

- Baseline explorador usa `read/glob/grep`; `list` não existe no catálogo observado. Papel implementador mantém apenas terminal Docker; a transformação substitui o terminal host.
- `-opencode.browser` remove o builtin no documento privado. A auditoria continua rejeitando browser ativo, permissões alteradas e qualquer ferramenta inesperada em recibos brutos, sem esconder registros tardios.
- Serena usa `disabled:false`, `codemode:false` e objeto `timeout` com `startup`, `catalog` e `execution`, cada um de 180000 ms. Correspondem ao schema `Mcp.LocalConfig` e `Mcp.TimeoutConfig` no offset 113416950; não há liberação de `execute`.
- O registro MCP propaga CodeMode ao catálogo. A validação exige nomes/IDs únicos, ID igual ao nome exposto, exposição direta e ação efetiva de permissão canônica. O guard compara o ID concreto recebido com o conjunto congelado, evitando dependência do timer de telemetria para o primeiro uso de MCP.
- `bench.py`, `cases.py`, `vendor/exploration.py`, `vendor/tasks_python.py` e `vendor/grader.py` permanecem byte a byte iguais ao snapshot anterior. Agenda de 120 trials, casos, contratos, limites e captura de requisições continuam preservados.

## Provas e comentários

Rodei independentemente **32 testes Python e sete Node**, todos aprovados, sem inferência. Testes incluem browser posterior ao filtro, MCP tardio antes do timer, CodeMode/permissões/IDs inválidos e substituição do terminal host. A integração nativa completa depende do preflight executado pelo proprietário desta correção; teste sintético e fonte embarcado não a certificam.

Comment Sicko: os cinco arquivos têm **zero comentários, zero docstrings e zero supressões** (`noqa`, `pylint`, `type:ignore`, ESLint e TypeScript). Deletados/restaurados: zero; reruns de remoção: zero; restrições sem encoding: zero. Nenhum comentário oferecido para encoding, nenhuma supressão de segurança pendente. O sketch arquitetural é o julgamento já fornecido; esta revisão não o expandiu.

Impacto documental: README e DESIGN devem registrar baseline de três ferramentas, browser desativado exclusivamente no ambiente privado, MCP direto e evidência de integração nativa ainda pendente quando aplicável. A evidência `full-1` deve continuar intacta, com execução nova em outra saída.
