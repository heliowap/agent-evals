# Seleção do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Atende aos três requisitos obrigatórios e empata em custo com Épsilon. O desempate favorece Gama, cuja implantação leva 18 dias corridos, contra 19 dias de Épsilon. Não foi necessário aplicar o segundo desempate, por ordem alfabética.

A análise cruza exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md). Dois subagentes diretos analisaram, respectivamente, elegibilidade e custos, sem alterar arquivos ou criar descendentes. Ambas as análises foram concluídas e conferidas antes da redação destes resultados. Os arquivos de entrada foram preservados.

## Atendimento aos requisitos

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura.

| Fornecedor | R1 | R2 | R3 | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído: R1 |
| Delta | Dados e backups no Brasil | Condição assinada entrega somente PDF; JSON futuro sem data contratual | 15 dias | Excluído: R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |

Alfa atende R2 e R3 exatamente nos limites permitidos. JSON e CSV satisfazem a exigência de formato aberto nas ofertas de exportação integral.

Beta viola apenas R1: seus backups ficam no Chile, e a proposta não prevê mudança desse armazenamento. Delta viola apenas R2: a condição específica assinada não assegura a exportação completa em formato aberto exigida. O anúncio genérico de “exportação fácil” não prevalece sobre essa condição, e a promessa de JSON em versão futura não conta como atendimento atual. Ambos atendem R3.

A lista de elegíveis em `answer.json` segue a ordem alfabética em português: Alfa, Épsilon, Gama, considerando É junto à letra E. As listas de violações usam os códigos em ordem crescente.

## Cálculos de custo

Para cada fornecedor, foi usada a fórmula:

**Custo em 12 meses = implantação + 12 × [mensalidade + máximo(0, 80.000 − franquia mensal) × preço por evento excedente].**

| Fornecedor | Mensalidade | Franquia mensal | Excedentes por mês | Custo dos excedentes por mês | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

As contas individuais, em reais, são:

- Alfa: 4.000 + 12 × (2.000 + 20.000 × 0,02) = **32.800**.
- Beta: 2.000 + 12 × 1.600 = **21.200**.
- Delta: 1.000 + 12 × 1.800 = **22.600**.
- Épsilon: 3.000 + 12 × 2.400 = **31.800**.
- Gama: 3.000 + 12 × 2.400 = **31.800**.

Beta e Delta têm custos inferiores aos dos elegíveis, mas suas violações obrigatórias impedem a seleção. Entre Alfa, Épsilon e Gama, o menor total é R$ 31.800,00, compartilhado por Épsilon e Gama; o prazo de implantação resolve o empate em favor de Gama.

## Premissas e ressalvas

O volume considerado é fixo em 80.000 eventos por mês durante os 12 meses. A implantação é cobrada uma única vez. Não há atualização monetária, desconto por antecipação nem acúmulo de franquia. Os excedentes são cobrados por evento, sem arredondamento por lote. Todos os valores já incluem impostos; os cálculos foram conferidos em centavos inteiros.

O preço de excedentes não informado por algumas propostas não afeta esta comparação, pois seu consumo fica dentro da franquia. O preço de R$ 0,04 por evento excedente de Gama também não é acionado neste cenário.

O orçamento de R$ 32.000,00 é desejável, mas não eliminatório: Alfa continua elegível mesmo excedendo-o em R$ 800,00. Gama e Épsilon ficam R$ 200,00 abaixo dele. A escolha se baseia nas condições documentadas e no volume solicitado; alterações de consumo ou de condições contratuais exigem nova comparação.
