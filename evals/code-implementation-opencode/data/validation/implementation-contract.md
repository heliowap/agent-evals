# Contrato de implementação aprovado

O plano em `../README.md` foi aprovado pelo usuário. Implementar o pacote neste diretório, preservando todos os arquivos dos outros temas. Não executar candidatos até os gates de isolamento, corretores e transporte passarem. O sandbox atual recusou acesso ao socket Docker; manter o bloqueio explícito e prosseguir na construção e verificação offline.

## Checkpoint e tarefas

1. Blocking first steps. Fixar este contrato, localizar ferramentas locais, conferir APIs nativas e registrar o bloqueio Docker.
2. Independent workstreams. Um proprietário para runtime, isolamento, CLI e grading; um para os dez casos Python; um para os dez casos TypeScript. Arquivos sem compartilhamento de escrita.
3. Shared mutable state. Cada autor escreve somente seus arquivos. O proprietário do executor define `domain.py`; os autores importam seu contrato sem editá-lo. Fontes de exploração permanecem intactas. Cada trial e cada grading recebe estado privado.
4. Smallest safe decomposition. O executor tem um único proprietário porque execução, cancelamento e coleta do patch precisam concordar. Curadoria das duas linguagens é independente. A agenda de inferência continua sequencial.

Fases: grounding e design concluídos no plano; acordo concluído; implementação em andamento; revisão e execução pendentes. Não há repositório Git nesta pasta e nenhum PR é necessário.

## Contrato dos casos

`domain.TaskSpec` é uma dataclass frozen com estes campos, nesta ordem:

`id: str`, `phase: str`, `family: str`, `language: str`, `request: str`, `files: dict[str, str]`, `reference: dict[str, str]`, `acceptance: str`, `allowed: tuple[str, ...]`, `structural: str | None = None`.

As linguagens são `python` e `typescript`. As fases são `screening` e `confirmation`. `files` é o projeto original visível ao agente. `reference` é um overlay privado de arquivos para a solução de referência. `acceptance` é o script privado completo de aceitação, Python ou CommonJS conforme linguagem. `allowed` contém prefixes root-relative de paths que podem mudar, normalmente `src/` e `checks/`. Alterações em checks do candidato não substituem o original no grader. `structural`, se não nulo, é outro script da mesma linguagem, exigindo somente o requisito público de refatoração.

`tasks_python.py` e `tasks_typescript.py` exportam `TASKS: tuple[TaskSpec, ...]`. Cada arquivo contém seis casos screening e quatro confirmation inéditos. IDs usam prefixes `py-` e `ts-`; só aparecem em artefatos do operador. Os seis casos de triagem cobrem as famílias do plano. A confirmação precisa de novos comportamentos e código, não renomeação das mesmas tarefas.

Projetos usam `src/`, `checks/`, README e configurações mínimas. Comandos públicos: Python `python3 checks/public.py`; TypeScript `tsc -p tsconfig.json && node checks/public.cjs`. TS compila CommonJS ES2022 com strict; checks CJS usam bibliotecas Node, sem necessidade de @types/node ou deps de rede. Configurar `outDir` `.build`. Scripts privados de TypeScript usam `require('./.build/...')`; Python scripts importam `src` a partir da raiz, inserindo cwd em sys.path se necessário. Scripts de aceitação terminam com exit não zero em falha; usam assert literal contra comportamentos e fronteiras descritos.

O baseline passa regressões públicas e falha aceitação nova. A referência passa tudo. Refatoração pode ter aceitação comportamental verde no baseline, desde que structural falhe e passe na referência. Os comandos rodam com cwd raiz do projeto. TypeScript 5.9.3 está em `~/.bun/install/cache/typescript@5.9.3@@@1/bin/tsc`, invocável via Node para verificação offline; Docker deverá usar a mesma versão. Os validadores locais só executam baselines e referências escritas pela equipe, nunca código de candidato real sem isolamento.

Enunciados parecem delegações normais, com entradas, limites e comandos. Não expõem modelo, juiz, testes ocultos, referência, comparação ou rubrica. Não exigir JSON final. Evitar arquivos e paths com nomes do experimento dentro do projeto candidato.

## Execução e isolamento

O OpenCode e suas credenciais privadas ficam no host. Emenda da implementação: leitura e edição também usam exclusivamente o terminal do container; todas as ferramentas nativas são removidas para impedir acesso ao host através de symlinks. Comandos do agente executam exclusivamente num container de código com network none e somente o workspace montado. Um plugin nativo registra a ferramenta `terminal` através de `ctx.tool.transform(editor.add(...))` e nega execução de outra ferramenta. Não usar binário Mach-O dentro de Linux, nem montar banco global ou socket Docker dentro do container.

O package nativo `@opencode/schema/tool` aceita JSON Schema para input. O plugin pode ser self-contained JavaScript, com spawn de Docker no host. O candidato fornece somente comando e timeout, nunca nome de container, host path, env host ou mounts. O plugin recebe container ID por env privado e usa AbortSignal para interromper os processos. No cancelamento, terminar o container interrompe também seus subprocessos; o volume do código conserva a entrega.

O grader usa outra árvore limpa, dependências/config originais, somente arquivos de patch permitidos e scripts privados. O namespace do candidato nunca contém grader ou referências. Código de candidato é executado pelo grader em isolamento, nunca diretamente no host. Provar isolamento com sentinelas fora do mount, symlinks e tentativa de alterar configurações. A imagem de código precisa apenas de Node, TypeScript 5.9.3 e Python, não OpenCode ou credenciais.

O runtime reutiliza o protocolo de observação nativa do explorador, preservando os códigos originais de erro no parser e distinguindo stream_cancelled de erro fatal. Não modificar os arquivos antigos. Coorte: sonnet-medium, sonnet-high, sol-fast-medium, sol-fast-high, opus-medium e deepseek-max. Sol continua builtin OAuth, sem trocar URL/tier. Agent implementer sem limite nativo steps; controlador externo de tempo e calls via session.interrupt. Auditoria confere ausência de steps e shell host e ativação do terminal isolado.

## CLI, grading e artefatos

CLI `bench.py` com comandos plan, validate, preflight, run e report. Fases budget, smoke, screening e confirmation. Screening padrão seis configs e três repetições; confirmation exige lista explícita de finalistas e usa cinco. budget e smoke têm uma tarefa/prova por config. Plan sem inferência; freeze inclui fontes, modelos, prompts, fixtures, grader, imagem, versões, ordem e budgets. Saídas sempre novas e nunca sobrescritas. Confirmação separada da triagem.

validate prova baseline/reference sem inferência. preflight prova Docker, isolamento, versão nativa, auth privada, plugins e variantes sem modelos; budget e smoke fazem inferência e devem ser explicitamente contados. Prova budget usa tarefa que continua lendo até cancelamento, com limite reduzido, sem injetar turno assistant. Guardar patch e resultado mesmo em interrupção.

Result mantém status operacional discriminado, session_completed, patch_correct, grade por critério, accepted, requested/observed identity, calls, codes/tier/usage, tempos e scope. Aprovação não depende da narrativa final. Relatório inventário congelado, denominador de todas as tentativas, contagem de chamadas, Fast solicitado/atendido e pares aprovados; nunca promover modelo automaticamente. Diferenças próximas produzem empate, não desempate por poucos milissegundos.
