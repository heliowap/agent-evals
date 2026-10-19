# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total em 12 meses de **R$ 31.800,00 (3.180.000 centavos)**. Gama e Épsilon têm o mesmo custo, mas Gama vence pelo menor prazo de implantação: 18 dias, contra 19 dias de Épsilon. Não foi necessário recorrer ao desempate por ordem alfabética.

A análise usa somente `requisitos.md` e `propostas.md`. Dois subagentes diretos analisaram, respectivamente, a elegibilidade e os custos; suas conclusões foram conferidas antes da elaboração dos arquivos finais. Os arquivos de entrada foram preservados.

## Requisitos e elegibilidade

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos. Condições específicas assinadas prevalecem sobre publicidade genérica, e funcionalidades futuras não atendem ao requisito atual.

| Fornecedor | R1: armazenamento | R2: exportação | R3: início de operação | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil; backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON futuro, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

**Beta viola R1:** a proposta informa backups no Chile e não prevê sua mudança. Atender à localização dos dados primários não basta: o requisito também abrange os backups. Beta atende a R2 e R3.

**Delta viola R2:** a condição assinada entrega somente PDF e prevê JSON apenas em uma versão futura, sem data contratual. O anúncio de “exportação fácil” não substitui a condição assinada. A proposta não assegura atualmente a exportação completa em formato aberto, incluída no preço e em até 48 horas. A exclusão não depende de afirmar que todo PDF seja um formato fechado, mas da ausência dessa garantia contratual. Delta atende a R1 e R3.

Alfa atende exatamente aos limites de 48 horas e 20 dias. O orçamento desejável de R$ 32.000,00 não é eliminatório, portanto seu custo superior a esse valor não altera sua elegibilidade.

A lista `elegiveis` em `answer.json` segue a ordem alfabética em português, considerando É na posição de E: Alfa, Épsilon, Gama. Os códigos de violações estão ordenados; cada excluído tem apenas um código.

## Cálculos em 12 meses

Para cada fornecedor:

`excedentes mensais = máximo(80.000 − franquia mensal, 0)`

`custo total = implantação + 12 × (mensalidade + excedentes mensais × preço por evento)`

| Fornecedor | Mensalidade | Franquia mensal | Excedentes mensais | Custo mensal dos excedentes | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

- Alfa: 20.000 × R$ 0,02 = R$ 400,00 de excedentes por mês; R$ 4.000,00 + 12 × R$ 2.400,00 = R$ 32.800,00.
- Beta: R$ 2.000,00 + 12 × R$ 1.600,00 = R$ 21.200,00.
- Gama: R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00.
- Delta: R$ 1.000,00 + 12 × R$ 1.800,00 = R$ 22.600,00.
- Épsilon: R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00.

Beta e Delta custam menos, mas são inelegíveis. Entre os elegíveis, Gama e Épsilon compartilham o menor custo e o prazo de implantação decide a escolha por Gama.

## Ressalvas e verificação

Os cálculos consideram 80.000 eventos em cada um dos 12 meses, uma única implantação, valores sem atualização monetária e impostos já incluídos. Não há desconto antecipado, acumulação de franquia nem arredondamento dos excedentes por lote. A tarifa de R$ 0,04 de Gama não gera cobrança porque o consumo é exatamente igual à franquia. Beta, Delta e Épsilon não informam tarifa de excedentes, mas ela não é necessária neste cenário, em que não excedem suas franquias.

A seleção depende das condições descritas nos arquivos, sem confirmação externa de sua execução. Os valores foram conferidos com aritmética inteira em centavos, e o JSON foi validado quanto às quatro chaves exigidas, aos tipos, à ordenação e à coerência com a decisão.
