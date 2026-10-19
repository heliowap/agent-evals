# Escolha do fornecedor

Gama é o fornecedor elegível escolhido, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Épsilon tem o mesmo custo, mas Gama vence pelo menor prazo de implantação: 18 dias contra 19. Não foi necessário aplicar o segundo desempate, por ordem alfabética.

## Critérios e evidências

A análise usa exclusivamente `requisitos.md` e `propostas.md`. São obrigatórios: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos, funcionalidades futuras não contam e condições específicas assinadas prevalecem sobre publicidade genérica.

| Fornecedor | R1: armazenamento | R2: exportação | R3: início de operação | Decisão |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Delta | Dados e backups no Brasil | Somente PDF; JSON previsto para versão futura, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |

Beta viola R1 porque seus backups estão no Chile e a proposta não prevê mudança. Delta viola R2 porque a condição assinada não assegura atualmente a exportação completa exigida em formato aberto e em até 48 horas. A expressão comercial “exportação fácil” não substitui essa garantia, e o JSON futuro não conta como atendimento atual. Essa conclusão não depende de classificar todo PDF como formato fechado: o problema é a ausência de garantia contratual do conjunto exigido por R2.

Alfa atende exatamente os limites de 48 horas e 20 dias. Nenhum fornecedor viola R3. Os elegíveis aparecem em `answer.json` na ordem alfabética portuguesa: Alfa, Épsilon, Gama, considerando É como E.

## Cálculos

Para cada fornecedor:

**Custo em 12 meses = implantação + 12 × [mensalidade + máximo(80.000 − franquia, 0) × preço por evento excedente].**

A implantação é cobrada uma única vez. O consumo é de 80.000 eventos em cada mês; franquias não utilizadas não acumulam. O excedente é calculado por evento, sem arredondamento para lotes. Todos os valores já incluem impostos, sem atualização monetária nem desconto por antecipação.

| Fornecedor | Mensalidade | Excedentes por mês | Custo mensal de excedentes | Implantação | Cálculo do total | Total em centavos |
|---|---:|---:|---:|---:|---|---:|
| Alfa | R$ 2.000,00 | 20.000 | R$ 400,00 | R$ 4.000,00 | 12 × R$ 2.400,00 + R$ 4.000,00 = R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 0 | R$ 0,00 | R$ 2.000,00 | 12 × R$ 1.600,00 + R$ 2.000,00 = R$ 21.200,00 | 2.120.000 |
| Delta | R$ 1.800,00 | 0 | R$ 0,00 | R$ 1.000,00 | 12 × R$ 1.800,00 + R$ 1.000,00 = R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 0 | R$ 0,00 | R$ 3.000,00 | 12 × R$ 2.400,00 + R$ 3.000,00 = R$ 31.800,00 | 3.180.000 |
| Gama | R$ 2.400,00 | 0 | R$ 0,00 | R$ 3.000,00 | 12 × R$ 2.400,00 + R$ 3.000,00 = R$ 31.800,00 | 3.180.000 |

Em Alfa, 20.000 eventos excedentes × R$ 0,02 = R$ 400,00 por mês. Gama consome exatamente a franquia de 80.000; sua tarifa de R$ 0,04 por evento excedente não incide neste cenário. Beta deixa 20.000 eventos de franquia sem uso por mês, sem crédito ou acúmulo.

## Ressalvas e conferência

Beta e Delta são mais baratos, mas seus descumprimentos obrigatórios impedem a escolha. O orçamento desejável de R$ 32.000,00 não é eliminatório: Alfa continua elegível apesar de excedê-lo em R$ 800,00. Gama fica R$ 200,00 abaixo dele.

A decisão considera as condições documentadas e o consumo fixado, sem presumir mudanças contratuais ou entrega de funcionalidades futuras. Dois subagentes diretos, sem descendentes, conferiram a elegibilidade e os custos e retornaram suas análises; somente o agente principal escreveu os arquivos finais. Os arquivos de entrada foram preservados.
