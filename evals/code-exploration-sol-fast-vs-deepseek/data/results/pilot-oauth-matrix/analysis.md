# Resultado de exploração no OpenCode

Sonnet medium é a escolha inicial sugerida para este contrato de exploração delimitada com JSON e citações. Empatou com Opus low e Opus medium em 27 de 30 aprovações completas e teve a menor mediana de tempo. Opus low é a alternativa mais próxima: acertou as 30 respostas literais e atingiu a mesma aprovação completa. A diferença de tempo entre esses dois varia por tarefa.

O piloto concluiu 210 trials em 10 de outubro de 2026. Foram seis casos, cinco repetições e sete configurações no OpenCode 2.0.26. Não houve erros de transporte, timeouts ou trials ausentes. O smoke anterior fica fora dos cálculos.

## Aprovação e tempo

| Configuração | Aprovação completa | Resposta literal correta | Mediana da tarefa | Intervalo observado |
|---|---:|---:|---:|---:|
| Sonnet medium | 27/30, 90.0% | 29/30 | 9.84 s | 8.19 a 19.46 s |
| Opus low | 27/30, 90.0% | 30/30 | 11.89 s | 6.73 a 18.32 s |
| Opus medium | 27/30, 90.0% | 30/30 | 14.02 s | 9.02 a 22.77 s |
| Sonnet low | 25/30, 83.3% | 28/30 | 10.69 s | 6.53 a 17.03 s |
| DeepSeek max | 25/30, 83.3% | 29/30 | 31.93 s | 16.86 a 67.98 s |
| Sonnet high | 22/30, 73.3% | 27/30 | 11.08 s | 9.11 a 15.47 s |
| Sol low, Fast selecionado | 14/30, 46.7% | 30/30 | 15.42 s | 6.16 a 25.80 s |

As medianas e intervalos incluem todas as respostas concluídas, inclusive as reprovadas. Medem a invocação OpenCode com boot, ferramentas e recuperações internas. Preparação, exportação e correção ficam fora. Os tempos somados de tarefa foram 55,5 minutos. Incluindo a preparação e o fechamento de cada trial, foram 63,1 minutos, além do preflight e processamento global.

Aprovação completa exige simultaneamente resposta literal correta, JSON válido com a estrutura pedida, citações válidas, todos os trechos obrigatórios e preservação dos arquivos. Resposta literal correta verifica o objeto answer conforme o gabarito, mas não valida suas evidências. Uma resposta envolvida em Markdown ou seguida de texto adicional pode falhar já no parse. Esses resultados medem o contrato inteiro, não apenas compreensão do código.

## Comparações pareadas

Comparações de tempo abaixo incluem somente o mesmo caso e repetição em que ambos receberam aprovação completa. A razão A/B é a mediana das razões de cada par, não uma divisão das medianas gerais.

| Configuração A | Configuração B | Pares aprovados | Mediana A/B | A mais rápido | B mais rápido |
|---|---|---:|---:|---:|---:|
| Sol low, Fast selecionado | Sonnet medium | 13 | 1.427 | 3 | 10 |
| DeepSeek max | Sonnet medium | 24 | 3.015 | 0 | 24 |
| Sonnet low | Sonnet medium | 22 | 1.042 | 10 | 12 |
| Sonnet medium | Opus low | 24 | 0.838 | 14 | 10 |
| Sonnet medium | Opus medium | 25 | 0.758 | 23 | 2 |

Sonnet medium e Opus low tiveram 24 pares aprovados conjuntamente. Sonnet medium foi mais rápido em 14 e Opus low em 10. A mediana A/B de 0,838 favorece Sonnet medium neste conjunto, mas a vantagem não aparece em todas as tarefas. As faixas de tempo se sobrepõem. Sonnet medium e Sonnet low dividiram os pares em 12 contra 10, com razão mediana próxima de 1.

A elevação de esforço do Opus de low para medium não aumentou a aprovação observada. O Sonnet high teve menos aprovações que medium. Este piloto não permite generalizar que esforço alto prejudica o modelo.

## Aprovação por caso

| Configuração | route | config | retry | permission | feature | absence |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet medium | 5/5 | 4/5 | 5/5 | 5/5 | 3/5 | 5/5 |
| Opus low | 5/5 | 2/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Opus medium | 5/5 | 2/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Sonnet low | 3/5 | 5/5 | 5/5 | 5/5 | 2/5 | 5/5 |
| DeepSeek max | 5/5 | 5/5 | 5/5 | 4/5 | 1/5 | 5/5 |
| Sonnet high | 5/5 | 4/5 | 2/5 | 5/5 | 1/5 | 5/5 |
| Sol low, Fast selecionado | 3/5 | 2/5 | 2/5 | 1/5 | 1/5 | 5/5 |

Os dois Opus passaram nas cinco repetições de route, retry, permission, feature e absence. Suas três reprovações ocorreram nas evidências de config. Sonnet medium passou em route, retry, permission e absence. Teve duas falhas de evidência em feature e uma resposta que não cumpriu JSON puro em config. Os candidatos têm perfis de falha diferentes, embora compartilhem 27 aprovações.

## Tipos de reprovação

Houve 43 reprovações: 36 apenas por evidências inválidas ou incompletas, três pelo nome incompleto de um símbolo na resposta do Sonnet high, três por JSON não aceito pelo parser estrito e uma por uma cadeia de chamadas incompleta, acompanhada de evidência incompleta, do Sonnet low.

Sol acertou as 30 respostas literais. Suas 16 reprovações foram exclusivamente nas citações ou cobertura dos trechos exigidos. Sua aprovação de 14/30 não representa 16 respostas substantivamente erradas. Sonnet high retornou DatabaseClient.execute sem o prefixo service.client em três respostas do caso retry. A regra exigia o nome completo.

Uma resposta DeepSeek em feature veio num bloco Markdown. Sonnet low produziu JSON inválido em feature. Sonnet medium acrescentou texto após seu objeto JSON em config. Os registros permanecem reprovados conforme o contrato congelado. Não houve flexibilização da correção durante ou após a rodada.

O detalhamento de cada reprovação, com campos e verificações que falharam, está em [analysis.json](analysis.json).

## Rotas e Fast

Sol usou openai/gpt-6.1-sol-fast#low com credencial OAuth nativa e WebSocket para o endpoint ChatGPT. Todas as chamadas verificadas enviaram esforço low e priority. Nenhum dos 30 trials confirmou Fast servido, pois as respostas terminais informaram default. Os dados permitem comparar essa configuração executada, mas não quantificar o benefício de Fast.

DeepSeek usou a assinatura OpenCode Go e esforço max. Sonnet e Opus usaram CLIProxy no protocolo Anthropic, com pensamento adaptativo e o esforço escolhido em output_config.effort. Não foi medida delegação nativa: cada explorador rodou como uma sessão principal isolada com uma mensagem do usuário.

## Evidência e limites

As fontes coincidiram com o congelamento. Os 210 exports de sessão foram relidos e corrigidos novamente sobre a fixture de referência. Os parâmetros das 949 chamadas foram verificados. As correções, identidades e contadores coincidiram com os registros originais. Não houve chamadas incompletas, trocas de modelo ou alterações da fixture.

A duração observada das chamadas ao provider foi o componente predominante do tempo da tarefa. A mediana da proporção variou de 74,7% no Sol a 97,7% no DeepSeek. Os registros não distinguem execução remota de espera da rede. A máquina registrou 14 CPUs e carga média de 4,36 no início. Não houve monitoramento contínuo de carga.

A ordem foi balanceada por rotações. Cada sessão era nova, mas o cache remoto podia persistir. A suíte utiliza uma aplicação sintética com 23 arquivos. As cinco repetições de cada caso são medidas repetidas; continuam existindo apenas seis casos distintos. Os números não estabelecem qualidade geral de programação, segurança, revisão ou pesquisa.

Os custos informados nas sessões não equivalem a cobrança real nem permitem comparar consumo de assinaturas. O zero informado pelo Sol OAuth não implica consumo nulo de limite.

O relatório automático conserva o veredito inconclusivo por desenho. A indicação de Sonnet medium e Opus low é uma escolha operacional inicial para este papel e este contrato, com base nos resultados observados. Explain the Number orientou a separação entre aprovação completa, resposta literal e tempos pareados.

## Reproduzir a verificação

As fontes originais da rodada foram preservadas em [frozen-source](frozen-source). Para verificar os registros sem chamar modelos:

```sh
python3 -B exploracao/sol-fast-vs-deepseek/results/pilot-oauth-matrix/verify_analysis.py
```

O comando confere as fontes congeladas, a fixture, os exports, a correção e as capturas de transporte. [analysis.json](analysis.json) contém as tabelas calculadas, falhas individuais, comparações pareadas e resultados originais. [report.md](report.md) conserva o relatório automático da rodada.
