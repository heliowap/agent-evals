# Verificação da comparação

A afirmação pretendida é comparar tempo observado e aprovação completa do Haiku 5.5 em cinco esforços nestes seis casos de exploração. Não declarar vencedor antes das entregas e das requisições verificadas.

O tempo principal cobre o processo `opencode run`, incluindo ferramentas e recuperações internas. Preparação, auditoria, exportação e grade ficam fora. O total do trial é separado e inclui essas etapas. O orçamento global admite trials entre tarefas; não constitui deadline rígido.

A configuração compara cinco esforços do mesmo modelo e rota. Cada esforço recebe cinco repetições dos seis casos, distribuídas em blocos com posições equilibradas. Repetições não são tarefas novas. Sessões locais são frias; cache remoto pode persistir e precisa constar nos dados de uso.

Erros, limites terminais de saída, respostas incorretas e trials ausentes devem ficar visíveis. Pares de velocidade exigem aprovação dos dois esforços no mesmo caso e repetição. A mediana geral de respostas concluídas inclui incorretas e precisa dizer isso.

A prova de trabalho exige sessão da tarefa, identidade do assistente, ferramentas permitidas, resposta e citações corretas, fixture intacta e requisições com parâmetros esperados. Exit zero isolado não prova aprovação. O serviço a montante não é atestado pela identidade enviada.

O estado da máquina deve ser registrado pela fase comparativa. Um limite de rede ou serviço não é identificável com preflight sem inferência. Se não houver rodada nativa, nenhum tempo ou ranking novo poderá ser reportado. Os testes sintéticos da captura não medem desempenho do Haiku ou do OpenCode em produção.

O cap comum de 128000 é parte desta configuração experimental. Comparações históricas com 32768 permanecem descritivas, pois o controle mudou.
