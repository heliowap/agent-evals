Gama é o fornecedor escolhido: seu custo total em 12 meses é **R$ 31.800,00 (3.180.000 centavos)**. Épsilon tem o mesmo custo, mas Gama vence pelo prazo de implantação: 18 dias corridos contra 19 dias. Não é necessário aplicar o segundo critério de desempate, a ordem alfabética.

A decisão usa exclusivamente `requisitos.md` e `propostas.md`. Dois subagentes diretos fizeram análises independentes de elegibilidade e custos, sem escrever arquivos nem criar descendentes; ambos chegaram à mesma conclusão. Os arquivos de entrada foram preservados.

Os requisitos obrigatórios são R1 (dados primários e backups no Brasil), R2 (exportação completa em formato aberto, incluída e disponível em até 48 horas) e R3 (início da operação em até 20 dias corridos da assinatura). Limites exatos são aceitos; condições específicas assinadas prevalecem sobre anúncios genéricos, e funcionalidades futuras não comprovam atendimento atual.

| Fornecedor | R1: armazenamento | R2: exportação | R3: início | Resultado |
| --- | --- | --- | --- | --- |
| Alfa | Dados e backups no Brasil | JSON integral, incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados no Brasil; backups no Chile | CSV integral, incluído, em 24 horas | 10 dias | Excluído: R1 |
| Gama | Dados e backups no Brasil | JSON integral, incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Condição assinada entrega somente PDF; JSON futuro sem data contratual | 15 dias | Excluído: R2 |
| Épsilon | Dados e backups no Brasil | CSV integral, incluído, em 24 horas | 19 dias | Elegível |

Beta viola apenas R1: a localização dos backups no Chile contraria a obrigação de armazenamento no Brasil, e a proposta não prevê mudança. Delta viola apenas R2: a entrega somente em PDF não atende à exportação completa em formato aberto exigida. O anúncio de “exportação fácil” não supera a condição assinada, e a promessa de JSON em versão futura não vale como atendimento atual. Todos atendem a R3. Alfa atende exatamente os limites de 48 horas e 20 dias.

O cálculo considera 80.000 eventos em cada um dos 12 meses e uma única implantação:

`total = 12 × [mensalidade + máximo(0, 80.000 − franquia mensal) × preço por evento excedente] + implantação`.

| Fornecedor | Excedentes por mês | Custo mensal com excedentes | Implantação única | Cálculo de 12 meses | Total em centavos |
| --- | ---: | ---: | ---: | --- | ---: |
| Alfa | 20.000 | R$ 2.400,00 | R$ 4.000,00 | 12 × (2.000 + 20.000 × 0,02) + 4.000 = R$ 32.800,00 | 3.280.000 |
| Beta | 0 | R$ 1.600,00 | R$ 2.000,00 | 12 × 1.600 + 2.000 = R$ 21.200,00 | 2.120.000 |
| Gama | 0 | R$ 2.400,00 | R$ 3.000,00 | 12 × 2.400 + 3.000 = R$ 31.800,00 | 3.180.000 |
| Delta | 0 | R$ 1.800,00 | R$ 1.000,00 | 12 × 1.800 + 1.000 = R$ 22.600,00 | 2.260.000 |
| Épsilon | 0 | R$ 2.400,00 | R$ 3.000,00 | 12 × 2.400 + 3.000 = R$ 31.800,00 | 3.180.000 |

Alfa é o único fornecedor com excedentes nesse volume: 20.000 × R$ 0,02 = R$ 400,00 por mês. Gama e Épsilon usam exatamente suas franquias; Beta tem 20.000 eventos mensais não utilizados, que não acumulam. Os custos de Beta e Delta estão apresentados para comparação, mas sua inelegibilidade impede a seleção.

Todos os valores já incluem impostos. Não há atualização monetária, desconto por antecipação nem cobrança por lotes arredondados. O orçamento de R$ 32.000,00 é desejável, não eliminatório: Alfa permanece elegível mesmo custando R$ 32.800,00. Gama fica R$ 200,00 abaixo desse orçamento.

Em `answer.json`, a lista de elegíveis segue a ordem alfabética em português: Alfa, Épsilon, Gama, tratando É como E. As listas de códigos de exclusão estão ordenadas. O campo `custo_12_meses_centavos` contém o total do fornecedor escolhido como inteiro. A conclusão se limita às condições documentadas e ao volume fixo solicitado; variações de consumo ou mudanças contratuais exigiriam novo cálculo.
