# Seleção do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses (3.180.000 centavos)**. Gama e Épsilon empatam no menor custo entre os elegíveis; Gama vence pelo menor prazo de implantação: 18 dias, contra 19 dias de Épsilon. Não é necessário aplicar o segundo desempate, por ordem alfabética.

A decisão cruza exclusivamente `requisitos.md` e `propostas.md`. Duas análises independentes, uma de elegibilidade e outra de custos, chegaram ao mesmo resultado. Os arquivos de entrada foram preservados.

## Requisitos e elegibilidade

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, operação iniciada em até 20 dias corridos da assinatura. Os limites exatos são aceitos. Condições específicas assinadas prevalecem sobre anúncios comerciais, e funcionalidades futuras não comprovam atendimento atual.

| Fornecedor | R1: armazenamento | R2: exportação | R3: implantação | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil; backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Condição assinada entrega somente PDF; JSON previsto para versão futura, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

Beta viola R1 porque seus backups ficam no Chile, sem previsão de mudança na proposta. Seus prazos de exportação e implantação atendem R2 e R3.

Delta não comprova atendimento a R2: a condição assinada oferece somente PDF, sem garantir exportação integral incluída em até 48 horas. A expressão comercial “exportação fácil” não substitui essa garantia, e a promessa de JSON futuro não atende ao requisito atual. A exclusão não depende de afirmar que PDF seja um formato fechado: PDF pode ser aberto, mas isso, isoladamente, não comprova todas as condições exigidas por R2. Delta atende R1 e R3.

Alfa atende exatamente os limites de 48 horas e 20 dias. O orçamento desejável de R$ 32.000,00 não é eliminatório, portanto seu custo superior a esse valor não a exclui. Os elegíveis em ordem alfabética são **Alfa, Gama e Épsilon**.

## Cálculos de custo

Para cada fornecedor:

`excedentes mensais = máximo(80.000 − franquia mensal, 0)`

`custo em 12 meses = implantação + 12 × (mensalidade + excedentes mensais × preço por evento)`

A implantação é cobrada uma única vez. O volume é de 80.000 eventos em cada mês, sem acumular franquias. Todos os valores já incluem impostos; não há atualização monetária nem desconto por antecipação. Cada evento excedente é cobrado individualmente.

| Fornecedor | Mensalidade | Franquia mensal | Excedentes por mês | Custo mensal dos excedentes | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

- Alfa: R$ 4.000,00 + 12 × (R$ 2.000,00 + 20.000 × R$ 0,02) = **R$ 32.800,00**.
- Beta: R$ 2.000,00 + 12 × R$ 1.600,00 = **R$ 21.200,00**.
- Gama: R$ 3.000,00 + 12 × R$ 2.400,00 = **R$ 31.800,00**.
- Delta: R$ 1.000,00 + 12 × R$ 1.800,00 = **R$ 22.600,00**.
- Épsilon: R$ 3.000,00 + 12 × R$ 2.400,00 = **R$ 31.800,00**.

Beta, Delta e Épsilon não informam preços de excedentes. Isso não impede esta comparação, pois suas franquias cobrem os 80.000 eventos mensais. Gama informa R$ 0,04 por excedente, mas também não ultrapassa sua franquia. Os custos menores de Beta e Delta não permitem sua escolha porque ambos são inelegíveis.

## Contrato de saída

`answer.json` contém exatamente as chaves `escolhido`, `elegiveis`, `custo_12_meses_centavos` e `excluidos`. O custo é o total do fornecedor escolhido, expresso como inteiro em centavos. A lista de elegíveis está em ordem alfabética; cada fornecedor excluído tem uma lista ordenada dos códigos violados: Beta, `["R1"]`; Delta, `["R2"]`.
