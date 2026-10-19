# Repetir o contrato monetário com instruções explícitas

O caso original deixou duas regras incompletas. O teste privado rejeita strings como `.1` e `1.`, mas o pedido não define a gramática. A API também exige `ValueError` para entradas que não sejam listas. A revisão explicita esses requisitos e a independência da precisão decimal do chamador.

## Comparação dos desenhos

| Desenho | Mudança | Sessões com modelos |
|---|---|---:|
| Runner específico e núcleo congelado | Revisão externa do contrato e seleção de um caso pelas funções existentes | 18 |
| Alterar CLI e inventário originais | Adicionar filtro de casos e mudar as fontes cobertas pelos gates | 30, incluindo seis provas de orçamento e seis sessões de smoke |

O runner específico usa uma cópia exata das 18 fontes congeladas da triagem. `TaskSpec` continua sendo a estrutura que reúne pedido, arquivos iniciais, referência, aceitação e escopo. A revisão muda o identificador, o pedido e a cópia do pedido no README do projeto. Código inicial, testes públicos, aceitação privada, referência e escopo permanecem iguais.

O chamador usa `python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py run --out implementacao/opencode-implementador/results/money-contract-v2`. A rodada contém seis candidatos e três repetições do único caso `py-money-contract-v2`.

## Limites entre módulos

`run.py` verifica a proveniência, constrói o `TaskSpec` revisado e congela sua própria fonte e o contrato. As funções existentes de `harness/bench.py` fazem agendamento, preflight, comparação dos gates, execução e relatório. `harness/controller.py` continua responsável pela interrupção. `harness/grader.py` continua responsável pela aprovação funcional.

O runner usa as seguintes operações:

1. Verificar a cópia do núcleo contra os hashes do `freeze.json` original.
2. Construir o caso revisado e conferir os campos preservados.
3. Congelar a agenda de 18 trials, o contrato e a fonte do runner.
4. Executar preflight sem inferência e aplicar os gates existentes sem alterar seus critérios.
5. Conferir os dois congelamentos antes de cada trial e executar blocos completos.
6. Produzir um resultado separado, sem combinar as duas versões do contrato.

`require_gate` reescreve relatórios derivados ao ler uma prova. Por isso, o runner passa cópias dos gates a essa função e registra os hashes e caminhos originais. Os resultados históricos não recebem escritas.

Os gates existentes comprovam o núcleo idêntico. Eles não comprovam o contrato revisado. A validação local e o preflight da nova rodada verificam baseline, referência e seleção do caso antes de qualquer chamada de modelo.

## Verificação

O plano precisa conter apenas o caso revisado, os mesmos seis candidatos e três repetições, totalizando 18 trials. Alterações posteriores do contrato ou do runner devem bloquear a execução antes da próxima chamada de modelo. Baseline e referência devem manter os mesmos resultados de compilação, regressão e aceitação da versão anterior. Falhas de infraestrutura ou escopo encerram a rodada e conservam os trials restantes como não executados.
