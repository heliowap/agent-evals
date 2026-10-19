# Desenho do piloto pareado

O problema é decidir se acrescentar Serena melhora a qualidade ou o tempo do Haiku para explorar e implementar código no OpenCode. O tratamento inclui ferramentas MCP e suas instruções. O modelo, esforço, enunciado, fixture, corretor, execução de código e limites permanecem iguais dentro de cada par.

A arquitetura selecionada é o [desenho B](validation/design-b.md), um runner misto com um único loop e cópias das primitivas já verificadas. O loop antigo de exploração pressupõe um projeto imutável e ausência de MCP. Alterá-lo para dois papéis espalharia condições por essas invariantes. Um wrapper de dois executores completos também duplicaria agenda e decisões de parada.

Configuration contém esforço e condição de ferramentas, e deriva a identidade do modelo. Case é a união de ExplorationCase e ImplementationCase. O papel decorre do próprio caso. A tabela de ferramentas permitidas gera configuração, permissões e validação de captura. O runner possui agenda e ciclo de vida; runtime possui configuração, descoberta, captura e identidade; cases possui contratos e seleção dos graders. Snapshots de referência ficam em vendor, sem imports mutáveis de outras rodadas.

Do [desenho A](validation/design-a.md), conservamos a CLI direta e o piloto sem gate de qualidade do smoke. O preflight comprova somente infraestrutura e validade do instrumento. Uma resposta funcionalmente errada é um resultado do experimento. O smoke opcional tem oito sessões e não entra no denominador principal.

A agenda tem 30 blocos de caso e repetição, com quatro configurações por bloco. Os esforços são medium e high; as condições são nativa e nativa com Serena. A execução sequencial e a rotação das posições reduzem contenção e favorecimento por ordem. O relatório calcula pares do mesmo esforço, caso e repetição, separados por papel.

Os contratos são route, config e feature da suíte exploratória; py-money-contract corrigido, py-document-scope e py-atomic-import da suíte implementadora. Cada papel tem três problemas distintos. Cinco repetições medem variação de execução, não cinco problemas novos.

O Serena inicia como MCP stdio do OpenCode, com projeto e metadados separados por trial. O projeto Python usa LSP explicitamente. A instalação do chat e suas memórias não participam. A configuração é de projeto único, com ferramentas fixas, sem shell, REPL ou memória. Metadados ficam fora da fixture para que o corretor de escopo não os confunda com alterações do agente.

A instalação local já possui a distribuição completa do Pyright 1.1.403 no cache de pacotes. A implementação copia somente essa distribuição para o pacote e invoca seu servidor JavaScript com Node por caminho absoluto. Essa escolha substitui o lançamento uvx proposto no desenho B e dispensa downloads ou cópia ampla do cache do operador. A distribuição e o executável entram na identidade congelada; o índice de cada projeto continua privado e frio.

O terminal de implementação continua no container Docker sem rede. O plugin precisa permitir a lista exata de ferramentas Serena além do terminal, pois a versão original remove e rejeita todos os outros tools. Os testes privados executam o patch em outro container. Os caminhos do MCP são conferidos na fronteira; restrição por projeto no host é declarada como tal.

O preflight precisa provar MCP e LSP operantes, catálogo final de ferramentas e ausência de fontes externas na descoberta do OpenCode antes de inferência. Fonte, contrato, catálogo, executáveis e identidade da instalação são congelados. Alteração de fonte, escopo ou infraestrutura impede continuar a campanha. Falhas funcionais permanecem visíveis e permitem a coleta seguinte.

No binário fixado, o catálogo nativo de leitura é `read/glob/grep`; `read` cobre diretórios. A configuração privada remove o builtin `opencode.browser`, que registra ferramentas depois dos plugins locais. O documento usa `mcp.servers.serena` com os campos nativos do servidor, inclusive `codemode:false`; suas ferramentas e instruções ficam diretas, com `execute` proibido. O recibo do catálogo inclui identidade, opção Code Mode e ação efetiva de permissão. O gate exige essas propriedades além do conjunto exato de nomes. O [julgamento da primeira correção](validation/surface-fix/design-judgment.md) conserva a prova primária e as alternativas rejeitadas.

Runtime possui a espera de prontidão e os recibos sanitizados; bench possui sua publicação durável e o progresso por configuração/papel. Respostas MCP entram na observação antes de serem validadas. Ausência inicial ou pending permite aguardar até o prazo, sem aprovar; conexão Serena e superfície exatas continuam obrigatórias. Somente a última observação completa pode aprovar, enquanto ferramentas inesperadas ou metadados inválidos em qualquer observação reprovam. A espera é compartilhada entre preflight e instância temporizada, antes de sessão/prompt, e consome o limite existente. Recibos sobrevivem às falhas de ambos. A [revisão desse contrato](validation/mcp-row-fix/design-judgment.md) registra a decisão sem acrescentar API pública.

O efeito de desempenho é avaliado pelo tempo observado, incluindo inicialização e ferramentas. Medidas auxiliares de boot e uso do MCP não justificam subtrair custos do tratamento. Se a indexação não puder ser separada com marcador confiável, o relatório informa essa limitação. Não se escolhe um vencedor quando o ganho cabe na variação ou quando a integração não está comprovada.

As revisões de desenho utilizam os agentes GPT disponíveis nesta sessão. A [revisão dos desenhos](validation/design-judgment.md) registra a régua, notas e recomendação independente. As provas da implementação são a autoridade para o estado de execução.
