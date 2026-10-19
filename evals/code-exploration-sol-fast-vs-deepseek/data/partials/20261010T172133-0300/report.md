# Resultado parcial de exploração no OpenCode

Captura de 2026-10-10T17:21:33-03:00. Piloto em execução. Smoke excluído.

Terminados 116 de 210 trials, 55.2% da agenda. Foram 90 aprovados e 26 reprovados. Um trial estava em curso e 93 ainda não haviam iniciado.

## Comparação nas mesmas tarefas

Este recorte usa 16 blocos completos, totalizando 112 trials. Cada configuração foi avaliada nas mesmas 16 tarefas e repetições. Quatro resultados já terminados do próximo bloco ficam fora desta tabela.

| Configuração | Aprovados | Resposta literal correta | Mediana da tarefa | Intervalo observado |
|---|---:|---:|---:|---:|
| Opus low | 15/16, 93.8% | 16/16 | 12.52 s | 8.38 a 18.32 s |
| Sonnet medium | 14/16, 87.5% | 16/16 | 9.51 s | 8.23 a 19.46 s |
| Sonnet low | 14/16, 87.5% | 16/16 | 11.29 s | 7.84 a 17.03 s |
| Opus medium | 14/16, 87.5% | 16/16 | 15.65 s | 9.45 a 22.77 s |
| DeepSeek max | 13/16, 81.2% | 15/16 | 33.01 s | 20.40 a 63.17 s |
| Sonnet high | 10/16, 62.5% | 13/16 | 11.32 s | 9.11 a 14.31 s |
| Sol low, Fast selecionado | 6/16, 37.5% | 16/16 | 16.36 s | 12.21 a 20.47 s |

Tempos incluem respostas reprovadas. Esta tabela descreve o tempo da tarefa inteira, incluindo boot, ferramentas e retries internos. Preparação, exportação e correção ficam fora.

Opus low tem a maior aprovação estrita neste recorte. Sonnet medium tem a menor mediana. Sonnet medium e Opus low acertaram conjuntamente 13 tarefas e repetições. Sonnet medium foi mais rápido em 11 desses 13 pares. A mediana da razão Sonnet medium/Opus low foi 0,752. Essas observações não estabelecem um vencedor geral.

Os blocos completos contêm route em 3 repetições, config em 2, retry em 4, permission em 4 e feature em 3. Ainda não contêm absence. As repetições não equivalem a tarefas independentes.

## O que causou as reprovações

Nos 116 trials terminados, 22 reprovações ocorreram apenas por evidências inválidas ou insuficientes. Três outras vieram do campo owner retornado por Sonnet high sem o prefixo service.client exigido pelo contrato. Uma resposta DeepSeek veio dentro de um bloco Markdown, impedindo o parse JSON estrito. Não alteramos a régua durante a execução.

Sol teve resposta literal correta em todos os 16 trials, mas dez falharam em citações ou cobertura das evidências exigidas. Sua taxa de aprovação não deve ser interpretada como dez erros de compreensão do código.

O benchmark exige resposta literal, JSON puro, símbolos e linhas válidos, trechos exatos e todas as âncoras obrigatórias. A aprovação mede o cumprimento desse contrato inteiro.

## Verificações do recorte

As fontes e o protocolo coincidem com o congelamento. Os 116 registros de sessão foram relidos, as 548 chamadas tiveram parâmetros verificados e as respostas foram corrigidas novamente sobre a fixture de referência. As correções e os metadados coincidiram com os registros originais. Não houve erros de transporte, chamadas incompletas, troca de modelo ou alteração de fixture nos trials concluídos.

A duração observada das chamadas ao provider domina a tarefa. A mediana da proporção entre essa duração e o tempo da tarefa varia de 78,5% no Sol a 97,7% no DeepSeek. Os registros não separam capacidade de processamento remoto de espera de rede. Cache remoto pode persistir entre repetições.

Sol usou OAuth nativo, WebSocket, esforço low e priority solicitado. Fast servido permaneceu não confirmado em todos os 16 trials, com classe terminal default. Os resultados caracterizam essa configuração observada.

Explain the Number orientou a separação entre aprovação estrita, resposta literal, tempo das mesmas tarefas e limites do recorte. O piloto continua em execução.

## Dados congelados deste parcial

[snapshot.json](snapshot.json) conserva os resultados lidos, a agenda, a configuração e os cálculos desta captura. Nenhum arquivo usado pela rodada ativa foi alterado.
