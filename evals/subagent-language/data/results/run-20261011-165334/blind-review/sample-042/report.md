# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Gama e Épsilon têm o mesmo custo e atendem a todos os requisitos obrigatórios. O desempate favorece Gama pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon. Não é necessário aplicar o segundo desempate, por ordem alfabética.

## Fontes e critérios

A análise cruza exclusivamente `requisitos.md` e `propostas.md`. Foram consideradas as propostas assinadas e a demanda fixa de 80.000 eventos por mês durante 12 meses, totalizando 960.000 eventos. A implantação é cobrada uma única vez, todos os preços já incluem impostos e não há atualização monetária nem desconto por pagamento antecipado.

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos. Condições específicas assinadas prevalecem sobre publicidade genérica, e funcionalidades futuras não demonstram atendimento atual.

## Cálculo dos custos

Para cada fornecedor:

`custo total = implantação + 12 × [mensalidade + máximo(0, 80.000 − franquia mensal) × preço por evento excedente]`

A franquia é aplicada mês a mês e não acumula. Cada evento excedente é cobrado individualmente, sem arredondamento para lotes.

| Fornecedor | Mensalidade | Franquia mensal | Excedentes por mês | Custo excedente mensal | Implantação | Total em 12 meses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 |

- Alfa: `4.000 + 12 × [2.000 + (20.000 × 0,02)] = R$ 32.800,00`.
- Beta: `2.000 + 12 × 1.600 = R$ 21.200,00`.
- Gama: `3.000 + 12 × 2.400 = R$ 31.800,00`.
- Delta: `1.000 + 12 × 1.800 = R$ 22.600,00`.
- Épsilon: `3.000 + 12 × 2.400 = R$ 31.800,00`.

Gama prevê R$ 0,04 por evento acima da franquia, mas a demanda coincide exatamente com sua franquia, portanto essa cobrança é zero. As propostas de Beta, Delta e Épsilon não informam uma tarifa excedente; isso não interfere neste horizonte, pois a demanda não excede suas franquias.

## Elegibilidade e evidências

| Fornecedor | R1 | R2 | R3 | Resultado |
| --- | --- | --- | --- | --- |
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Somente PDF atualmente; JSON futuro, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

**Beta viola R1** porque os backups estão no Chile. Armazenar somente os dados primários no Brasil não atende à exigência conjunta, e a proposta não prevê mudança dos backups. Beta atende a R2 e R3.

**Delta viola R2** porque a condição específica assinada entrega somente PDF, sem comprovar a exportação completa em formato aberto exigida. A publicidade de “exportação fácil” não substitui essa condição. A promessa de JSON em versão futura, sem data contratual, não atende ao requisito atual. Delta atende a R1 e R3.

Alfa atende exatamente aos limites de 48 horas de exportação e 20 dias de implantação; ambos são aceitos expressamente pelos requisitos. Gama e Épsilon também atendem aos três requisitos. A lista de elegíveis em `answer.json` segue a ordem alfabética em português: Alfa, Épsilon, Gama, considerando É na posição da letra E.

## Decisão e ressalvas

Entre os elegíveis, Alfa custa R$ 32.800,00 e Gama e Épsilon custam R$ 31.800,00 cada. Gama vence o empate pelo menor prazo de implantação. Embora Beta e Delta sejam mais baratos, suas violações obrigatórias impedem a seleção.

O orçamento desejável de R$ 32.000,00 não é eliminatório: Alfa permanece elegível apesar de ultrapassá-lo em R$ 800,00. Gama fica R$ 200,00 abaixo desse orçamento.

A conclusão vale para a demanda e as condições documentadas nos arquivos de entrada. Não foram presumidas melhorias futuras, mudanças de localização ou descontos. Dois subagentes diretos, sem descendentes, analisaram separadamente a elegibilidade e os custos; ambos concluíram suas análises e concordaram com o resultado. A conferência e a escrita dos arquivos finais foram realizadas pelo agente principal, preservando os arquivos de entrada.
