# Provas das falhas de medição e catálogo

A premissa incorreta era que os caminhos de sucesso bastariam para provar medição e catálogo. A revisão mostrou perdas em duas etapas, exportação e grading, enquanto o relógio da invocação já tinha fechamento em finally. Mostrou também que igualdade por conjunto não comprova cardinalidade nem identidade das ferramentas.

O censo executável está em FailureRegressionTests de test_bench.py. Cada etapa recebe uma falha externa controlada e o teste lê result.json persistido. O relógio determinístico exige um segundo registrado para a etapa iniciada. As provas de catálogo aceitam uma superfície válida e rejeitam duplicação de nomes ou IDs. As provas de MCP distinguem pending, connected e envelope malformado. Não há chamada de modelo.

As reproduções anteriores da revisão são conservadas. A correção deve fechar todas as etapas iniciadas, e as provas red/green ficam neste diretório.
