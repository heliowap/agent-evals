# Repetir apenas o caso monetário corrigido

Rodada concluída com 18/18 aprovações e 105 chamadas de modelo. O [relatório de resultados](../../../../implementacao-opencode-resultado.md) compara as duas versões do contrato e registra a análise corrigida da triagem. O [resumo bruto](../../results/money-contract-v2/summary.json) conserva a série desta rodada.

Esta rodada repete `py-money-contract` com o contrato explícito de [request.txt](request.txt). O novo caso recebe o identificador `py-money-contract-v2`. São 18 trials, com seis candidatos e três repetições por candidato.

As strings precisam corresponder por inteiro à gramática ASCII `[+-]?[0-9]+(?:\.[0-9]+)?`. O pedido exige rejeitar `.1`, `1.`, espaços, expoentes e underscores com `ValueError`. O pedido também explicita `ValueError` para entradas de `make_invoice` que não sejam listas e exige cálculo exato sob baixa precisão decimal.

O README do projeto entregue ao agente contém esse mesmo pedido. Os arquivos iniciais de código, os testes públicos, a aceitação privada, a referência e o escopo permanecem iguais aos da triagem original.

## Executar a rodada

Use o Terminal com Docker disponível, como nas rodadas anteriores:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py run \
  --out implementacao/opencode-implementador/results/money-contract-v2
```

O diretório de saída precisa ser novo. O executor conserva resultados anteriores. A imagem Docker já usada na triagem é suficiente.

A saída `results/money-contract-v2` já contém a rodada concluída. Para uma nova repetição, escolha outro diretório de saída.

Os candidatos são Sonnet medium, Sonnet high, Sol medium Fast, Sol high Fast, Opus medium e DeepSeek max. Identidades, efforts, rotas OAuth e provedores vêm da rodada congelada. Cada trial mantém o limite de 20 minutos e 60 chamadas de modelo. A rodada tem teto global de seis horas e para entre blocos completos. Dezoito trials não significam dezoito chamadas de modelo.

O preflight verifica o caso revisado, baseline, referência, isolamento, ferramentas e configuração dos seis candidatos antes de qualquer inferência. Falhas de infraestrutura ou de escopo encerram a rodada. Os demais trials permanecem visíveis como não executados.

## Conferir sem usar modelos

O plano congela a agenda e não chama modelos:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py plan \
  --out implementacao/opencode-implementador/validation/money-contract-v2-plan
```

A validação executa apenas código confiável do baseline e da referência:

```bash
python3 -B implementacao/opencode-implementador/rounds/money-contract-v2/run.py validate \
  --out implementacao/opencode-implementador/validation/money-contract-v2-validate
```

## Evidência e interpretação

`harness/` é uma cópia exata das 18 fontes congeladas da triagem. `provenance.json` registra seus hashes e a origem. O runner congela separadamente seu código e o pedido revisado. Uma alteração posterior dessas fontes bloqueia a próxima execução.

Os gates `budget-r4` e `smoke` continuam obrigatórios e mantêm os critérios originais. Como o núcleo é idêntico, não há novas sessões de orçamento ou smoke. O executor aplica esses gates a cópias locais verificadas e registra sua origem, sem escrever nos resultados históricos. O desenho e as alternativas estão em [DESIGN.md](DESIGN.md).

Os resultados da nova rodada medem o contrato explícito. Preserve a série original como evidência do contrato incompleto. Não use as reprovações originais por `.1` como prova de incapacidade de seguir instruções, nem considere esses patches automaticamente corretos nos demais critérios.

O tier atendido continua separado de Fast solicitado. A rodada de triagem observou `default` nos Sol, apesar de solicitar Fast. Este executor não promete que o provedor atenderá o pedido de prioridade.
