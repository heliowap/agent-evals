# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses (3.180.000 centavos)**. Atende aos três requisitos obrigatórios e empata em custo com Épsilon, vencendo pelo menor prazo de implantação: 18 dias contra 19 dias.

## Fontes e critérios

A análise usa exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md), preservados sem alterações. Dois subagentes diretos, sem descendentes, analisaram elegibilidade e custos, respectivamente. Ambos retornaram suas conclusões por mensagem; o agente principal conferiu os resultados e escreveu os arquivos finais.

Os requisitos são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos. Condições assinadas prevalecem sobre publicidade genérica, e funcionalidades futuras não contam como atendimento atual.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: início | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil; backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído: R1 |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON apenas em versão futura, sem data | 15 dias | Excluído: R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |

**Beta viola R1:** o requisito abrange também os backups, que estão no Chile. A proposta não prevê sua mudança para o Brasil.

**Delta viola R2:** a condição assinada oferece somente PDF e não assegura a exportação completa de dados em formato aberto, incluída e disponível em até 48 horas. A previsão de JSON futuro, sem data contratual, não atende ao requisito atual; o anúncio de “exportação fácil” não substitui a condição assinada. A exclusão não depende de afirmar que todo PDF seja um formato fechado.

Alfa atende exatamente os limites de 48 horas e 20 dias, portanto permanece elegível. A lista de elegíveis em `answer.json` segue a ordem alfabética portuguesa, considerando “É” como “E”: Alfa, Épsilon, Gama. Os códigos de violação de cada excluído estão ordenados.

## Cálculo do custo

Para cada proposta:

`excedentes por mês = máximo(0, 80.000 − franquia mensal)`

`custo em 12 meses = implantação + 12 × (mensalidade + excedentes por mês × preço por evento)`

São 960.000 eventos ao longo de 12 meses, com a franquia aplicada separadamente em cada mês. A implantação é cobrada uma única vez. Todos os valores já incluem impostos; não há atualização monetária, desconto antecipado ou acumulação de franquia. Excedentes são cobrados por evento, sem arredondamento para lotes.

| Fornecedor | Mensalidade | Excedentes/mês | Custo dos excedentes/mês | Implantação | Cálculo total em reais | Total em centavos |
|---|---:|---:|---:|---:|---|---:|
| Alfa | R$ 2.000,00 | 20.000 | R$ 400,00 | R$ 4.000,00 | 4.000 + 12 × (2.000 + 400) = **32.800** | 3.280.000 |
| Beta | R$ 1.600,00 | 0 | R$ 0,00 | R$ 2.000,00 | 2.000 + 12 × 1.600 = **21.200** | 2.120.000 |
| Delta | R$ 1.800,00 | 0 | R$ 0,00 | R$ 1.000,00 | 1.000 + 12 × 1.800 = **22.600** | 2.260.000 |
| Épsilon | R$ 2.400,00 | 0 | R$ 0,00 | R$ 3.000,00 | 3.000 + 12 × 2.400 = **31.800** | 3.180.000 |
| Gama | R$ 2.400,00 | 0 | R$ 0,00 | R$ 3.000,00 | 3.000 + 12 × 2.400 = **31.800** | 3.180.000 |

Alfa excede a franquia de 60.000 em 20.000 eventos por mês: 20.000 × R$ 0,02 = R$ 400,00. Gama e Épsilon usam exatamente sua franquia de 80.000; Beta utiliza menos que os 100.000 incluídos; Delta também usa exatamente sua franquia. Logo, apenas Alfa paga excedentes. A tarifa de R$ 0,04 de Gama não é acionada neste volume. As demais tarifas não informadas são irrelevantes para o cenário, pois não há excedentes nessas propostas.

## Decisão, desempate e ressalvas

Entre os elegíveis, o menor custo é R$ 31.800,00, compartilhado por Gama e Épsilon. O primeiro critério de desempate é o menor prazo de implantação: **Gama, com 18 dias**, vence Épsilon, com 19 dias. Não é necessário aplicar o segundo critério, a ordem alfabética. Beta e Delta têm custos menores, mas não podem ser escolhidos por violarem requisitos obrigatórios.

O orçamento desejável de R$ 32.000,00 não é eliminatório. Alfa permanece elegível mesmo custando R$ 800,00 acima dele; Gama fica R$ 200,00 abaixo. O campo `custo_12_meses_centavos` contém o custo total da proposta escolhida.

A conclusão considera as condições documentadas e o volume fixo de 80.000 eventos mensais. Não presume migração futura dos backups, entrega futura de funcionalidades ou condições comerciais não descritas nos arquivos.
