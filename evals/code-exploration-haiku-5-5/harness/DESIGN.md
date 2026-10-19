# Exploração Haiku 5.5

Decisão: desenho A, com captura e diagnósticos do desenho B. O runner conserva um único scheduler e loop de trials da cópia da base R2; não usa adapter paralelo, monkeypatch, loader ou plano JSON adicional. A comparação cobre somente código e arquivos da fixture anterior.

Interface: `python3 -B exploracao/haiku-5-5/haiku.py run --out exploracao/haiku-5-5/results/round-1`. O wrapper executa cinco smokes novos, exige 5/5 corretos com evidências válidas e prova dos parâmetros, então executa 150 trials. `plan`, `validate-offline`, `preflight` e `report` completam a interface. Destinos novos; sem sobrescrita ou retomada automática.

Coorte: Haiku 5.5 low, medium, high, xhigh e max, rota `cli_proxy/cpa-claude-haiku-5-5`, wire `claude-haiku-5-5`, Messages, sem Fast. Um tuple de `Candidate` é a fonte da coorte. Os seis casos, prompts, grader e 23 arquivos vêm da base congelada `exploracao/sol-fast-vs-deepseek/results/pilot-r2-xhigh-gemini/frozen-source`. `cases.py`, `test_cases.py` e `observer.js` ficam byte equivalentes.

Controles: cinco repetições, seed 20261010, 25 passos, 300 segundos por processo de tarefa, orçamento de admissão entre trials de 21600 segundos por fase, contexto 272000, saída 128000 para todos. Saída é a mudança experimental deliberada diante do cap anterior 32768. Apenas read/glob/grep/list; descoberta privada de configurações, plugins e skills. Isso não equivale a isolamento do sistema operacional.

Prova de execução: modelo, identidade, variante/esforço, rota Messages, thinking adaptive e max_tokens inteiro 128000 em todas as requisições observadas. Preflight sem inferência não prova encaminhamento; smoke prova a requisição enviada, não a execução interna do provedor. Sem retries de inferência ou alteração automática de esforço.

Exportação: função dedicada em runtime.py mantém stdout em arquivo regular 0600, stderr capturado, timeout e encerramento do grupo. Preserva bytes sanitizados antes de UTF-8/JSON, com exit, timeout, bytes/SHA brutos e preservados e offset de falha. Não reserializa, corrige ou reexporta automaticamente. Teste sintético não demonstra a causa de uma falha do OpenCode nativo.

Diagnóstico: preservar finish/rawFinish de todos os assistentes; distinguir limite intermediário recuperado de limite terminal. Limite terminal é categoria própria, fora de respostas incorretas comuns e pares aprovados. Falha de exportação/identidade continua infraestrutura, ainda que haja sinal de limite. Relatório declara planned, attempted, stop_reason e exit_code; cobertura incompleta sai não-zero.

Proveniência: fontes/protocolo/catálogo/executável e inventário antigo verificados antes e após a fase, incluindo o último trial. Cópia congelada descreve o código realmente usado. Não alterar fontes nem resultados anteriores. Os artefatos de validação locais não contam como inferência.

Arena: A 10/10, B 8/10 em cinco critérios de preservação, execução, prova nativa, integridade e interface. B acrescentava loader e três fluxos duplicados. Foram aproveitados recibos completos de exportação, fins intermediários/terminais e cobertura explícita. Os leitores e o juiz usaram modelos GPT; não houve revisão entre famílias.

Validação antes da entrega: grade anterior, agenda 150 equilibrada, configuração e provas negativas, exportação grande/invalidade/timeout/sanitização, diagnóstico terminal e recuperação, gate 5/5, cobertura incompleta e guard final. Tentativa nativa somente pela CLI privada; se o sandbox bloquear porta/rede, registrar zero chamadas e fornecer o comando para o Terminal.
