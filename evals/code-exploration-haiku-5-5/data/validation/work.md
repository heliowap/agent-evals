# Haiku 5.5 em leitura, pesquisa e exploração

## Etapas

- [x] Ground. Traçar o executor e os controles da rodada anterior.
- [x] Sketch. Comparar dois desenhos antes de implementar.
- [x] Agree. Escolher o desenho pelos critérios de preservação e simplicidade.
- [x] Implement. Um proprietário escreve o novo pacote.
- [x] Scrap. Desenho preservado; não houve necessidade de recomeçar.
- [x] Verify. Conferir a CLI, os casos, os hashes e tentar a execução nativa.

## Throughput checkpoint

- Blocking first steps. A coorte privada e o smoke precisam ser provados antes dos 150 comparativos.
- Independent workstreams. Grounding e esboços escrevem em arquivos temporários próprios. O proprietário do código recebe somente o pacote novo.
- Shared mutable state. Fontes e resultados anteriores ficam somente leitura; o coordenador cuida das evidências, do índice e do ledger.
- Smallest safe decomposition. Um proprietário reúne configuração, captura e orquestração, porque o smoke e os hashes dependem dessas partes.

## Escopo confirmado

O usuário confirmou pesquisa no código e nos arquivos do projeto, como no eval anterior. São seis casos, cinco repetições e cinco esforços, total de 150 trials comparativos, mais cinco smokes. Os casos são route, config, retry, permission, feature e absence. Prompts, fixtures, corretores e contrato de citações devem permanecer iguais à rodada anterior.

A base é `exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. Seus sete hashes de fonte coincidem com o congelamento e com os arquivos de código atuais. O README histórico congelado coincide com o hash de protocolo; o README atual foi atualizado depois da rodada e não é a origem selada.

## Controles e decisões pendentes

Os cinco esforços são low, medium, high, xhigh e max, usando `cli_proxy/cpa-claude-haiku-5-5`, com modelo enviado `claude-haiku-5-5` e pensamento adaptativo. O ambiente é privado, com ferramentas read, glob, grep e list. O isolamento de permissões e descoberta não é um sandbox do sistema operacional.

A [documentação Anthropic](https://platform.claude.com/docs/en/models/haiku-5-5/overview) informa saída máxima de 128K. A rodada de implementação mostrou que max consumiu o limite de 32.768 em raciocínio em treze entregas vazias. O novo desenho deve considerar 128.000 para todos os cinco esforços, preservando os demais limites de 300 segundos, 25 passos e seis horas. Essa mudança precisa ficar explícita e impede tratar os tempos como comparação controlada com as rodadas antigas.

O helper Python de captura não possui limite de 256 KiB. Uma reprodução offline com Bun, `stdout.write` seguido de `process.exit`, produziu JSON íntegro de 1.000.014 bytes quando stdout foi um arquivo regular. Isso prova o caminho sintético, sem provar o comportamento do binário OpenCode 2.0.26. O desenho deve preservar a exportação bruta e separar esgotamento de saída de erro de pesquisa.

Nenhuma inferência desta nova rodada foi realizada ainda. Bind e loopback foram bloqueados por EPERM neste sandbox em turnos anteriores; uma tentativa real registrará o estado atual, sem contornar permissões.

## Estado final

O pacote está pronto para execução no Terminal. A CLI real de plano congelou cinco smokes e 150 trials, 30 por esforço, com 150 combinações únicas de caso, repetição e candidato. A versão final passou 38 testes Python e sete testes Node, sem inferência. Os hashes dessa validação coincidem com as fontes atuais e com o plano final.

A tentativa real `run` em `validation/native-run-root-2` terminou no preflight, antes de qualquer trial ou chamada de modelo. OpenCode não conseguiu iniciar o servidor standalone para importar a credencial privada. A prova direta de bind local registrou PermissionError, errno 1, Operation not permitted, em `root-proof.json`. Não houve tentativa de contornar o sandbox. `results/round-1` permanece disponível para a execução autorizada no Terminal.

A revisão independente encontrou um P2 no smoke, que ignorava erro observado quando HTTP era 200 e o stream encerrava. A correção adicionou o contador `observed_error_requests`, rejeitou esse estado no gate e passou a regressão. O coordenador confirmou gate válido e rejeição individual nos cinco esforços. Nenhum finding continua aberto. A revisão de comentários teve zero achados; a verificação final confirmou zero comentários lexicais nos quatro arquivos alterados.

Os 4776 arquivos da comparação anterior continuam byte equivalentes. Casos, corretores e observador herdados também continuam byte equivalentes. As evidências finais são `final-proof.json`, `check-root-3`, `plan-root-final` e `native-run-root-2`. A prova nativa dos parâmetros continua pendente do smoke no Terminal; validação sintética não é resultado do modelo.

Princípios aplicados: Model the Domain colocou a coorte em um tuple de Candidate; Laziness Protocol manteve um scheduler e loop; Separate Before Serializing Shared State limitou os escritores ao pacote novo e a arquivos próprios; Prove It Works exigiu testes comportamentais, hashes e tentativa pela CLI real. As revisões usaram a família GPT e não forneceram independência entre famílias.
