# Escolha do fornecedor

**Gama é a escolhida**, com custo total de **R$ 31.800,00 em 12 meses** (3.180.000 centavos). Épsilon tem o mesmo custo, mas Gama vence pelo menor prazo de implantação: 18 dias contra 19 dias. O desempate seguinte, por ordem alfabética, não precisa ser aplicado.

A análise usa exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md). Dois subagentes diretos conferiram separadamente a elegibilidade e os custos, sem escrever arquivos, e suas conclusões foram conferidas pelo agente principal.

## Elegibilidade e evidências

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início da operação em até 20 dias corridos da assinatura. Os limites exatos atendem aos requisitos.

| Fornecedor | R1 — armazenamento | R2 — exportação | R3 — prazo | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil. | JSON integral incluído, em 48 horas. | 20 dias. | Elegível. |
| Beta | Dados primários no Brasil, backups no Chile. | CSV integral incluído, em 24 horas. | 10 dias. | Excluído por R1. |
| Gama | Dados e backups no Brasil. | JSON integral incluído, em 36 horas. | 18 dias. | Elegível. |
| Delta | Dados e backups no Brasil. | A condição assinada entrega somente PDF; JSON é prometido para uma versão futura, sem data contratual. | 15 dias. | Excluído por R2. |
| Épsilon | Dados e backups no Brasil. | CSV integral incluído, em 24 horas. | 19 dias. | Elegível. |

Beta viola R1 porque o requisito abrange também os backups, que ficam no Chile. Sua proposta não prevê a mudança desse armazenamento.

Delta não atende à exportação completa em formato aberto exigida por R2 nas condições atuais. A condição específica assinada prevalece sobre o anúncio genérico de “exportação fácil”; a promessa futura de JSON, sem data contratual, não comprova atendimento atual nem entrega em até 48 horas.

Alfa atende exatamente aos limites de 48 horas e 20 dias. Os elegíveis, em ordem alfabética portuguesa, são Alfa, Épsilon e Gama; o acento de Épsilon não altera sua posição na letra E.

## Cálculos de custo

Para cada fornecedor:

**Total em 12 meses = implantação + 12 × (mensalidade + máximo(0, 80.000 − franquia mensal) × preço por evento excedente).**

Alfa excede sua franquia em 20.000 eventos por mês: 20.000 × R$ 0,02 = R$ 400,00. Seu custo mensal é R$ 2.000,00 + R$ 400,00 = R$ 2.400,00. Os demais fornecedores não têm excedentes no volume contratado.

| Fornecedor | Excedentes por mês | Custo mensal com excedentes | Implantação única | Cálculo do total | Total em centavos |
|---|---:|---:|---:|---|---:|
| Alfa | 20.000 | R$ 2.400,00 | R$ 4.000,00 | 12 × R$ 2.400,00 + R$ 4.000,00 = R$ 32.800,00 | 3.280.000 |
| Beta | 0 | R$ 1.600,00 | R$ 2.000,00 | 12 × R$ 1.600,00 + R$ 2.000,00 = R$ 21.200,00 | 2.120.000 |
| Gama | 0 | R$ 2.400,00 | R$ 3.000,00 | 12 × R$ 2.400,00 + R$ 3.000,00 = R$ 31.800,00 | 3.180.000 |
| Delta | 0 | R$ 1.800,00 | R$ 1.000,00 | 12 × R$ 1.800,00 + R$ 1.000,00 = R$ 22.600,00 | 2.260.000 |
| Épsilon | 0 | R$ 2.400,00 | R$ 3.000,00 | 12 × R$ 2.400,00 + R$ 3.000,00 = R$ 31.800,00 | 3.180.000 |

Beta e Delta custam menos, mas são inelegíveis. Entre os elegíveis, Gama e Épsilon têm o menor custo; o prazo de implantação resolve o empate a favor de Gama.

## Ressalvas e contrato de saída

O cálculo considera 80.000 eventos em cada um dos 12 meses, sem acumular franquias, uma única implantação, sem atualização monetária e sem desconto por antecipação. Os impostos já estão incluídos nas propostas. Excedentes são cobrados por evento, sem arredondamento para lotes; Gama não utiliza sua tarifa de R$ 0,04 porque o volume coincide com a franquia.

O orçamento de R$ 32.000,00 é desejável, não eliminatório. Portanto, Alfa permanece elegível, apesar de custar R$ 800,00 acima dele. Gama fica R$ 200,00 abaixo desse orçamento.

Em [answer.json](answer.json), `custo_12_meses_centavos` é o custo total do fornecedor escolhido, como inteiro. O arquivo contém exatamente as quatro chaves solicitadas; `elegiveis` está em ordem alfabética e cada lista de requisitos violados em `excluidos` está ordenada. Os arquivos de entrada foram preservados.
