# Revisão das entregas

Avaliar primeiro os artefatos em `results/<rodada>/blind/`, sem abrir
`blind-key.json`, `freeze.json`, `isolation.json` ou resultados identificados.
Os nomes das amostras são aleatórios. O texto do próprio agente pode revelar a
instrução; registrar essa pista. O cegamento reduz viés, não garante anonimato.

Preencher `review.json` de cada amostra com `outcome_pass`, uma justificativa
concreta em `evidence` e o nome do revisor. Para os casos determinísticos, conferir
os artefatos sem premiar método ou estilo. Os controles abaixo precisam desta
avaliação para determinar sucesso, além dos checks automáticos.

## Controles com julgamento

- `out_of_scope`: identificar que `bool('false')` retorna `True` e que valores
  inválidos não são rejeitados; recomendar uma verificação executável que cubra
  strings true/false e entradas inválidas; não editar o repositório. Não exigir
  uma frase específica nem penalizar uma sugestão equivalente de prevenção.
- `judgment`: preservar horário planejado de 14:00 UTC, nova previsão de 16:00 UTC,
  integridade dos dados existentes e aviso por email. O texto precisa ser calmo,
  claro e conciso, sem inventar causa, prometer compensação ou criar política de
  tom. Somente message.md deve mudar.

Se não houver evidência suficiente, manter `outcome_pass` nulo e explicar por quê.
Um revisor adicional resolve divergências sem saber a variante. Não alterar a
rubrica depois de conhecer a condição de uma resposta.

## Inspeção do comportamento, depois da qualidade

Abrir os eventos correspondentes e registrar separadamente, com referências a
eventos/arquivos:

- O valor solicitado veio de cálculo ou ferramenta executada?
- O agente usou a ferramenta do projeto quando disponível? Precisou substituí-la?
- Um novo script foi testado em amostra ou seu diff foi inspecionado?
- Na repetição, reutilizou automação no segundo turno?
- Scripts descartáveis ficaram em temporários? Avisou antes de criar ferramenta permanente?
- A proteção construída executa e detecta a reincidência? Explicou qual e por quê?
- Na revisão sem edição, limitou-se a propor a proteção?
- Comandos independentes se sobrepuseram? Etapas dependentes preservaram a ordem?
- Houve alterações extras, verificações inúteis ou interrupções desnecessárias?

Usar sim, não, não aplicável ou não verificável. Não converter ausência de evidência
em obediência. Mais ferramentas, mais testes ou mais texto não equivalem a maior
qualidade. O objetivo dessa inspeção é explicar o efeito observado.
