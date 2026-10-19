A rodada Haiku 5.5 está interrompida após 100/180 trials comparativos, com 86 aprovações completas. Os cinco gates de budget e os cinco smokes passaram. Restam 80 trials, 16 por esforço.

| Esforço | Realizados | Aprovação completa | Patch aprovado / avaliado | Mediana dos aprovados | Faixa dos aprovados | Chamadas comparativas |
|---|---:|---:|---:|---:|---:|---:|
| low | 20/36 | 20/20 | 20/20 | 22,04 s | 11,49 a 42,44 s | 98 |
| medium | 20/36 | 20/20 | 20/20 | 36,13 s | 12,51 a 78,35 s | 125 |
| high | 20/36 | 20/20 | 20/20 | 64,65 s | 20,99 a 143,08 s | 167 |
| xhigh | 20/36 | 20/20 | 20/20 | 136,22 s | 66,82 a 296,67 s | 229 |
| max | 20/36 | 6/20 | 6/19 | 325,47 s | 256,92 a 421,25 s | 144 |

As medianas contam apenas os trials aprovados. Max usa seis observações; os outros esforços usam vinte. Os mesmos vinte pares de caso e repetição foram iniciados para cada configuração, cobrindo onze dos doze problemas. O fluxo de eventos TypeScript ainda não foi executado. Há alternância por bloco, mas a carga dos providers não foi controlada nem perfilada. Os números são descritivos.

As 13 reprovações de patch de max têm alterações vazias. Todas terminaram com `finish=length`, `rawFinish=max_tokens`, 32.768 tokens de raciocínio e zero tokens de saída na última chamada. Não houve interrupção pelo controlador: três chamadas HTTP 200 completas, código de saída zero e 149,10 a 180,67 segundos. O limite de saída enviado foi 32.768 por resposta. Isso mede esta configuração sob esse limite; não demonstra desempenho com um orçamento de saída maior.

O rótulo bruto `completed` decorre de `idle.outcome=succeeded`; o parser não distingue `finish=length`. O grader privado reprovou os patches vazios, doze na aceitação e um na verificação estrutural. Não é evidência de entrega bem-sucedida nem de dificuldade em seguir instruções. Exemplo em [trial-0008](../../results/haiku-5-5/screening/trials/trial-0008/result.json).

O [trial-0100](../../results/haiku-5-5/screening/trials/trial-0100/result.json), max no arquivamento TypeScript, provocou a parada por `infra_error`. A leitura JSON da exportação da sessão falhou. O agente saiu com código zero após 335,03 segundos e quinze chamadas. Há alterações em `checks/public.cjs` e `src/service.ts`, com escopo correto, mas `grade.not_executed=true`: a implementação não foi testada. Seu `patch_correct=false` é um valor imposto pelo caminho de erro. A correção do patch permanece desconhecida.

O stdout bruto do export não foi preservado. O helper congelado captura stdout integralmente; a [verificação sem rede](stdout-capture-check.json) recebeu JSON de 1.000.016 bytes. O checkout auxiliar da CLI escreve em stdout e chama `process.exit` sem aguardar a drenagem. Uma reprodução sintética com Bun demonstrou truncamento nesse padrão e saída integral com callback. Isso sustenta uma hipótese, sem provar a causa no binário 2.0.26. Não há evidência de um limite de captura de 256 KiB no executor.

Foram conferidas 805 solicitações nativas, 763 comparativas e 42 nos gates, e 109 sessões exportadas. Modelo, esforço, pensamento adaptativo, rota e identidade permaneceram corretos nas solicitações observadas. Fontes, catálogo, imagem, agendas e grades coincidem com os registros congelados. A leitura preservou 1.109 arquivos desta rodada e os 1.250 arquivos anteriores conferidos.

Explain the Number distinguiu o esgotamento de saída das falhas de teste e da infraestrutura. Prove It Works levou à conferência dos registros reais. Nenhuma fonte, resultado ou orçamento foi alterado, e nenhum trial foi reiniciado. Para prosseguir, a exportação precisa ser corrigida em uma nova execução com evidências preservadas. Alterar o limite de saída de max seria outro experimento, que precisa ser identificado separadamente.

[Snapshot, contagens e hashes](snapshot.json). A revisão independente, pela mesma família GPT, reproduziu contagens, tempos e causas. Corrigimos a distinção entre doze reprovações de aceitação e uma estrutural; nenhum outro finding alterou a conclusão.
