# O que os evals mostram sobre “Deterministic first”

Relatório consolidado em 10 de outubro de 2026.

## A conclusão para o AGENTS global

Os três pilotos isolados não mostraram ganho de acerto com o trecho. Em cada configuração, o agente entregou corretamente as 36 tarefas sem a instrução e as 36 com ela. O texto mudou alguns métodos de trabalho e aumentou o volume de saída, mas essa mudança não melhorou a entrega medida.

Manter o trecho removido do `AGENTS.md` global continua sendo a decisão mais apoiada por estes resultados. Essa é uma decisão provisória sobre o bloco completo. O estudo não demonstra que usar ferramentas, criar testes ou executar comandos em paralelo seja inútil.

O achado mais repetido foi um custo adicional no caso de processamento repetido. O agente já calculava os resultados com Python sem o bloco. Com ele, passou a criar um arquivo de script e fazer verificações adicionais. Nas três configurações, a entrega final continuou correta, mas demorou mais nesse caso.

## A pergunta que foi testada

O trecho contém duas orientações principais. A primeira pede que regras verificáveis sejam implementadas como proteções executáveis, como testes e linters. A segunda pede que saídas calculáveis sejam produzidas por ferramentas ou scripts, com preferência pelas ferramentas existentes no projeto.

O texto também inclui obrigações específicas: criar um script quando um passo se repete pela segunda vez, verificar scripts novos, guardar scripts descartáveis em uma pasta temporária e paralelizar comandos independentes.

O [trecho exato avaliado](instrucoes-agents/agentsmd-detfirst-opencode/results/opus-5-5-medium/frozen-source/variants/deterministic/AGENTS.md) está preservado com as evidências.

Essas recomendações poderiam trazer ganhos diferentes:

| Ganho esperado | Como ele apareceria no trabalho |
|---|---|
| Mais exatidão | Menos erros de contagem, cálculo, transformação e edição em lote |
| Menos reincidência | Um teste ou uma checagem rejeita a volta de um defeito |
| Mais eficiência | Menor duração ou menor consumo para uma entrega igualmente correta |
| Melhor reutilização | A automação reduz trabalho nas próximas solicitações |
| Melhor controle de escopo | O agente propõe uma proteção quando a tarefa autoriza apenas revisar |

O custo possível é preparar automações e verificações que não se pagam durante a tarefa. Por isso o eval avaliou o resultado, além de observar o método. Criar mais scripts ou chamar mais ferramentas não vale pontos por si só.

## Como a comparação foi feita

Cada configuração foi executada em duas condições. O controle recebeu um `AGENTS.md` de zero bytes. O tratamento recebeu somente o trecho original, com 992 bytes. O restante das instruções globais do usuário não entrou nessa comparação.

Foram usados 12 casos, três repetições de cada caso e duas condições. Isso produz 72 execuções por configuração, agrupadas em 36 pares. A primeira condição de cada par foi balanceada: 18 pares começaram pelo controle e 18 pelo tratamento.

| Configuração | Provider ou rota | Execuções concluídas |
|---|---|---:|
| Codex CLI com Sol 6.1 `xhigh` | Integração do Codex | 72/72 |
| OpenCode 2.0.25 com Sol 6.1 `xhigh` | `openai/gpt-6.1-sol#xhigh` | 72/72 |
| OpenCode 2.0.25 com Opus 5.5 `medium` | `cli_proxy/cpa-claude-opus-5-5#medium`, via CPA | 72/72 |

As três rodadas isoladas somam 216 execuções. Elas repetem os mesmos 12 casos sintéticos, portanto não representam 216 problemas independentes.

As instruções internas de cada produto permaneceram presentes nas duas condições. A auditoria verificou o isolamento disponível, as seleções de modelo e esforço e a descoberta de configuração. Ela não capturou nem demonstrou igualdade integral dos requests HTTP aos provedores. No CPA, a identidade registrada no cliente também não atesta, por si só, qual modelo o serviço a montante entregou.

O pacote preliminar `agentsmd-detfirst` está preservado como histórico. Seus testes de funcionamento e tentativas não entram nos números consolidados deste relatório.

## O que os 12 casos medem

| Caso | Tarefa | Critério principal |
|---|---|---|
| `count` | Contar registros de log com filtros de status e horário | Inteiro exato |
| `money` | Somar valores em centavos com filtros | Total exato |
| `convert` | Converter CSV em JSON | Preservar conteúdo, ordem e tipos |
| `rename` | Renomear um identificador em vários arquivos | Alterar os usos corretos e preservar o comportamento |
| `project_tool` | Produzir um relatório do projeto | Respeitar o contrato da ferramenta disponível |
| `repeat` | Processar três lotes em duas solicitações da mesma sessão | Três resumos corretos e observação da reutilização |
| `guardrail` | Impedir usos futuros de `eval` | Checagem rejeita chamadas proibidas e aceita usos permitidos |
| `regression` | Corrigir limites invertidos em `clamp` | Testes detectam a reintrodução do defeito |
| `out_of_scope` | Revisar um parser sem editar arquivos | Identificar o defeito e recomendar prevenção executável |
| `judgment` | Reescrever uma mensagem de atraso | Texto claro, fatos preservados e alteração restrita ao arquivo pedido |
| `independent` | Executar três verificações independentes | Resultados reais corretos e observação de sobreposição temporal |
| `dependent` | Alterar configuração, gerar e verificar um arquivo | Resultado coerente com a nova configuração e a ordem necessária |

Os dois casos de julgamento receberam revisão do assistente pela rubrica definida antes das respostas. Os rótulos foram ocultados na revisão, mas o assistente conhecia o desenho e métricas agregadas. Algumas respostas também sugerem qual instrução receberam. Não houve revisão humana independente nem garantia de cegamento completo.

## Acerto igual nas três configurações

| Configuração | Sem o trecho | Com o trecho | Ganho observado |
|---|---:|---:|---:|
| Codex com Sol | 36/36 | 36/36 | 0 ponto percentual |
| OpenCode com Sol | 36/36 | 36/36 | 0 ponto percentual |
| OpenCode com Opus via CPA | 36/36 | 36/36 | 0 ponto percentual |

Isso significa que a régua não encontrou uma entrega melhor causada pelo bloco. Não significa que as duas condições sejam equivalentes em qualquer situação. O controle já chegou ao teto de acertos, de modo que a suíte oferece pouca oportunidade para demonstrar melhoria de qualidade.

Há também uma distinção entre entregar corretamente e seguir cada preferência do texto. Em `independent`, o resultado correto conta como acerto; a sobreposição dos comandos é registrada separadamente. No Opus, houve sobreposição dos três checks em uma das três execuções sem o bloco e em nenhuma das três com ele. Portanto, 100% de acertos não comprova obediência perfeita à instrução de paralelizar.

Nos casos `guardrail` e `regression`, ambas as condições construíram proteções que passaram nos testes de reincidência: seis entregas por condição, em cada configuração. Esses prompts já pedem prevenção de forma explícita. O resultado não mede se o bloco faria o agente propor espontaneamente uma proteção em uma tarefa que não a solicita.

## A duração aumentou no agregado, com efeitos diferentes por caso

O tempo abaixo é a duração média das invocações do agente. Inclui inicialização e ferramentas, mas exclui preparação, auditoria, exportação e correção do eval. Não é o tempo total do processo nem uma medida isolada da velocidade do modelo.

| Configuração | Sem o trecho | Com o trecho | Diferença observada |
|---|---:|---:|---:|
| Codex com Sol | 40,46 s | 47,37 s | +17,1% |
| OpenCode com Sol | 34,14 s | 42,17 s | +23,5% |
| OpenCode com Opus via CPA | 12,70 s | 13,43 s | +5,8% |

O sinal agregado foi desfavorável ao trecho nas três rodadas. Ainda assim, duração varia por tarefa, chamada e serviço remoto. Não houve perfil para separar inferência, proxy, rede, inicialização e ferramentas como causas dessa diferença.

No Opus, a diferença global é inconclusiva. O tratamento foi mais rápido em 18 dos 36 pares. Um intervalo exploratório de 95%, calculado após a rodada por reamostragem dos 12 casos, foi de aproximadamente −7,0% a +24,1%. Como inclui zero, os dados são compatíveis tanto com redução quanto com aumento de duração nesse recorte.

### O exemplo mais claro: repetir o processamento

Em `repeat`, o usuário primeiro pede o resumo do lote A e depois pede o mesmo para B e C.

Sem o bloco, o agente já usa Python e um laço para processar B e C. Com o bloco, cria um script temporário reutilizável e o verifica. A diferença está no trabalho de preparar a automação, sem mudança no resultado entregue.

| Mediana do caso `repeat` | Sem o trecho | Com o trecho |
|---|---:|---:|
| Codex com Sol | 48,49 s | 84,79 s |
| OpenCode com Sol | 42,44 s | 82,79 s |
| OpenCode com Opus via CPA | 12,53 s | 24,42 s |

Em cada configuração, as três execuções com o trecho foram mais lentas que todas as três sem ele. Excluindo apenas esse caso como análise de sensibilidade, a diferença agregada do Opus muda de +5,8% para −1,6%.

O mesmo padrão de custo apareceu no Codex e no OpenCode com Sol. Isso enfraquece a regra universal de criar um arquivo de script na segunda repetição. O eval não mediu se esse investimento se pagaria depois de dezenas de reutilizações ou em tarefas maiores.

## Os tokens exigem atenção à forma de contagem

Os produtos e providers não separam entrada, cache, saída e raciocínio da mesma maneira. Comparar dois campos chamados `output_tokens` sem verificar o significado pode produzir uma conclusão errada.

| Configuração | Contador usado nesta linha | Sem o trecho | Com o trecho | Diferença |
|---|---|---:|---:|---:|
| Codex com Sol | Saída, incluindo raciocínio | 35.800 | 43.232 | +20,8% |
| OpenCode com Sol | Saída mais raciocínio, parcelas somadas | 31.298 | 40.328 | +28,9% |
| OpenCode com Opus via CPA | Saída reportada pelo provider | 28.740 | 33.034 | +14,9% |

Cada linha compara as duas condições dentro da mesma configuração. A linha do CPA não fornece uma medida auditada de raciocínio separado ou de custo total.

Na rodada Codex, o contador de tokens era cumulativo entre os dois turnos de `repeat`. O executor original somava os acumulados e duplicava o primeiro turno. A análise corrigiu a agregação para usar somente o último contador, confrontado com os registros de uso. Os resultados brutos foram preservados.

No CPA, foram reportados apenas dois ou quatro tokens de entrada nativa por mensagem, grandes volumes de cache e raciocínio zero. Isso não prova ausência de raciocínio interno. Mantemos essas parcelas separadas e não inferimos economia financeira a partir delas. Nenhuma comparação deste relatório equivale a uma fatura conciliada.

## Comparar produtos é uma pergunta diferente

O experimento foi desenhado para comparar vazio versus trecho dentro de cada configuração. Usar seus resultados para comparar produtos ou modelos exige mais cautela.

Com Sol `xhigh`, o OpenCode teve 13,1% menos duração acumulada e 55,3% menos tokens normalizados que o Codex, nas mesmas 72 combinações de caso, repetição e condição. A normalização incluiu cache e raciocínio conforme a contabilidade de cada produto.

Na rodada posterior, o Opus via CPA teve duração média 62,8% menor que o Sol no OpenCode sem o trecho e 68,1% menor com o trecho. As entregas passaram na mesma régua.

Essas são comparações exploratórias. Produtos têm instruções internas e ferramentas diferentes. Na comparação com Opus também mudaram modelo, esforço e provider. As rodadas não foram intercaladas entre essas configurações. Os números descrevem o que aconteceu, mas não identificam qual componente causou a diferença nem estabelecem um vencedor geral.

## O que fazer com o resultado

A decisão atual é manter o bloco completo fora do `AGENTS.md` global. Ele não apresentou ganho mensurável de acerto nestes pilotos, e a obrigação de criar scripts acrescentou trabalho em um caso repetido nas três configurações.

Para reconsiderar a decisão, o próximo teste deve usar tarefas reais em que o controle ainda comete erros. Também precisa medir retrabalho, reincidência e reutilização posterior, além da primeira entrega. O ganho mínimo de qualidade e o custo adicional tolerável devem ser definidos antes de observar as respostas.

Testar separadamente `Rules`, `Actions` e a regra da segunda repetição ajudaria a localizar benefícios. Uma versão curta não foi avaliada aqui e não pode ser tratada como solução já validada.

## Relatórios e evidências

Os relatórios de leitura ficam na raiz de `evals/`. Os pacotes executáveis, dados brutos, revisões e fontes congelados ficam agrupados por tema. Os originais dos relatórios permanecem junto das evidências para preservar auditorias e hashes.

| Material | Local |
|---|---|
| Resultado detalhado do Codex com Sol | [Análise do Codex](agentsmd-codex-pilot-analise.md) |
| Resultado detalhado do OpenCode com Sol | [Análise do OpenCode com Sol](agentsmd-opencode-pilot-r2-analise.md) |
| Resultado detalhado do OpenCode com Opus | [Análise do OpenCode com Opus via CPA](agentsmd-opencode-opus-5-5-medium-analise.md) |
| Pacotes e instruções de execução | [Tema: instruções para agentes](instrucoes-agents/README.md) |
| Demais temas e relatórios do acervo | [Índice dos evals](README.md) |

Este relatório reúne as análises existentes. Sua elaboração e a reorganização dos arquivos não executaram novas inferências.
