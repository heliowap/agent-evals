# Comparar Haiku com e sem Serena no OpenCode

Execute da raiz de `evals` em um Terminal com acesso ao CLIProxy e ao Docker:

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py run \
  --phase full \
  --out ferramentas/haiku-serena-opencode/results/full-3
```

O piloto contém 120 trials. São seis casos, cinco repetições e quatro configurações: Haiku medium e high, cada um com ferramentas nativas e com ferramentas nativas mais Serena. Cada configuração recebe 30 trials, 15 de exploração e 15 de implementação. A agenda intercala as quatro configurações no mesmo caso e repetição.

Use um destino novo em cada rodada. Não há retomada, sobrescrita, troca de esforço ou retry de inferência pelo harness. O preflight testa infraestrutura antes da primeira chamada de modelo. Reprovação funcional não impede a coleta dos demais trials.

Para examinar a agenda e validar os contratos sem inferência:

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py plan --out ferramentas/haiku-serena-opencode/validation/plan-1
python3 -B ferramentas/haiku-serena-opencode/bench.py validate --out ferramentas/haiku-serena-opencode/validation/check-1
python3 -B ferramentas/haiku-serena-opencode/bench.py preflight --out ferramentas/haiku-serena-opencode/validation/native-1
```

O smoke opcional mede oito trials, separados do piloto completo:

```sh
python3 -B ferramentas/haiku-serena-opencode/bench.py run --phase smoke --out ferramentas/haiku-serena-opencode/results/smoke-1
```

O smoke usa uma tarefa por papel e uma repetição por configuração. Seus acertos não condicionam a admissão do piloto completo. O comando `report --out CAMINHO` recompõe somente os relatórios derivados de uma saída existente.

## Casos e aprovação

| Papel | Caso | Comportamento avaliado |
|---|---|---|
| Exploração | route | Reconstruir o caminho ativo da requisição até a execução no banco |
| Exploração | config | Resolver precedência entre camadas de configuração |
| Exploração | feature | Identificar a implementação concreta selecionada por feature flag |
| Implementação | py-money-contract | Validar valores monetários e totais com precisão de centavos, sem arredondar nem aceitar tipos proibidos |
| Implementação | py-document-scope | Restringir documentos por tenant, proprietário e exclusão lógica, com SQL parametrizado |
| Implementação | py-atomic-import | Validar o lote inteiro e aplicar inserções e atualizações atomicamente |

Os arquivos, enunciados, referências e testes vêm das suítes anteriores. O caso monetário usa o contrato corrigido de `money-contract-v2`. A proveniência registra as cópias e adaptações locais. Pesquisa cobre somente código e arquivos da fixture, sem web.

Exploração exige JSON estrito, tipos e valores corretos, citações válidas e todas as âncoras do contrato. Citações usam linhas de base um, embora o Serena retorne posições de base zero. O contrato informa essa exigência igualmente às duas condições. Os arquivos do projeto devem permanecer intactos.

Implementação exige entrega concluída, patch dentro do escopo, compilação, regressões públicas e aceite privado aprovados. O grader reaplica o patch em cópia limpa e conserva os testes públicos originais. Os testes privados ficam fora do projeto do agente. O caso de autorização verifica as condições descritas no enunciado, sem acrescentar requisitos ocultos.

## Controles e isolamento

OpenCode 2.0.26, CLIProxy, seleção `cli_proxy/cpa-claude-haiku-5-5#medium` ou `#high`, wire `claude-haiku-5-5`, thinking adaptive, contexto 272000 e cap de saída 128000. O observador verifica identidade, esforço, rota e cap das requisições. Isso atesta parâmetros enviados, sem comprovar o backend interno do provedor.

Exploração usa 300 segundos e 25 passos. Implementação usa 1200 segundos e 60 chamadas, com interrupção e tolerância do controlador. Os limites são iguais nas duas condições de cada papel. O orçamento global de admissão é 172800 segundos. Esse teto de 48 horas comporta os limites da agenda e não prevê sua duração.

Cada trial tem sessão, HOME, XDG, configuração OpenCode, configuração Serena, metadados e índice próprios. Plugins, instruções, skills, memórias e MCPs do operador não entram na descoberta privada. O processo Serena inicia em stdio no projeto da fixture. A lista de ferramentas é fixa por papel. Memórias, onboarding, shell do Serena, REPL e troca de projeto ficam indisponíveis.

Exploração usa as ferramentas nativas `read`, `glob` e `grep`. `read` também lê diretórios; não há uma ferramenta nativa `list` no OpenCode fixado. O builtin `opencode.browser` é desativado apenas na configuração privada do eval. Implementação conserva o terminal do harness, que executa comandos em Docker sem rede. O aceite usa outro container, com cópia limpa. O Serena roda no host e opera sobre a fixture privada por ferramentas limitadas e validação de caminhos. Essa restrição de projeto não equivale a isolamento do Serena em um namespace do sistema operacional.

O documento configura o servidor em `mcp.servers.serena`, a estrutura nativa do OpenCode fixado, com `disabled: false`, `codemode: false` e timeouts separados de startup, catálogo e execução. Isso expõe seus tools diretamente. O wrapper `execute` continua bloqueado. O gate verifica o catálogo completo, identidades, exposição direta e ações de permissão. Ferramentas inesperadas ou em Code Mode bloqueiam a execução antes de inferência.

A descoberta aguarda um catálogo MCP inicialmente vazio ou Serena pending até o prazo. Um catálogo vazio permanente nunca aprova. O tratamento exige exatamente Serena conectado e seus tools diretos na última observação; um catálogo completo antigo não basta. A mesma prontidão é exigida dentro de cada trial antes do primeiro prompt, com a espera incluída no tempo de tarefa. O preflight publica progresso e recibos sanitizados de descoberta, inclusive na falha, antes de remover os diretórios temporários. Os trials também preservam esses recibos quando a prontidão falha.

A instalação local do Serena e o servidor Python são identificados e congelados. O pacote contém uma cópia da distribuição JavaScript do Pyright 1.1.403, obtida do cache local já instalado. O LSP usa Node por caminho absoluto e não instala pacotes durante a rodada. Índices e memórias de projetos anteriores não são reutilizados. O preflight comprova operações de símbolos e referências, permissões de leitura e edição e disponibilidade das ferramentas no OpenCode. Uma conexão MCP sem servidor Python funcional não basta.

## Medição e limites

O relatório separa papel, esforço e condição. Apresenta aprovação completa e seus componentes, chamadas, tokens, falhas, timeouts e uso útil do Serena. Ler o manual não conta como uso útil. Trials sem uso útil permanecem no denominador do braço com Serena.

O tempo de tarefa inclui boot, inicialização do MCP, ferramentas e recuperações nativas. Preparação, exportação e grading são registrados separadamente, assim como o tempo total do trial. O relatório conserva falhas e tentativas não executadas. Comparações de tempo nos pares aprovados exigem que ambos os braços aprovem o mesmo caso e repetição. O custo informado pelo OpenCode não mede o preço marginal da assinatura.

São seis problemas sintéticos e cinco repetições operacionais. O piloto mede o efeito do pacote de ferramentas e instruções do Serena nesses casos. Não certifica ausência geral de bugs ou falhas de segurança, nem compara diretamente novas latências com rodadas históricas.

O desenho e as provas ficam em [DESIGN.md](DESIGN.md) e [validation/](validation/). Fontes consultadas para a integração: [MCP no OpenCode](https://opencode.ai/docs/mcp-servers/) e [Serena em clientes MCP](https://oraios.github.io/serena/02-usage/030_clients.html). O schema do binário instalado também foi conferido, pois o corpus local do OpenCode é de outra versão.

## Validação desta preparação

Na preparação inicial, os contratos, testes locais e Serena/LSP real passaram; [a prova inicial](validation/final-proof.json) conserva esse snapshot. No Terminal, `full-1` passou pelos gates Docker e parou na superfície nativa, com zero chamadas de modelos. O [primeiro diagnóstico](validation/surface-fix/grounding.md) registra catálogo, ordem do builtin browser e representação MCP. `full-2` parou na validação da linha MCP; sua resposta original não foi preservada. O [novo diagnóstico](validation/mcp-row-fix/grounding.md) comprova a incompatibilidade entre a posição legada e os campos nativos do documento e fundamenta a coleta de recibos antes da validação. As provas dessa correção ficam em [mcp-row-fix/](validation/mcp-row-fix/). A integração nativa completa ainda depende do preflight no Terminal, pois o servidor local não inicia neste sandbox e o socket Docker é bloqueado. Execute com saída nova; `full-1` e `full-2` não devem ser reutilizados.

Após a correção da linha MCP, os contratos locais, 44 testes Python e 7 Node passaram em [check-root-3](validation/mcp-row-fix/check-root-3/offline-tests.json). Serena/LSP real passou para os dois papéis; o preflight parou no acesso Docker, com zero chamadas de modelos. A [prova de fechamento](validation/mcp-row-fix/final-proof.json) distingue esses resultados da integração nativa ainda pendente e registra a preservação do protocolo e dos resultados anteriores.
