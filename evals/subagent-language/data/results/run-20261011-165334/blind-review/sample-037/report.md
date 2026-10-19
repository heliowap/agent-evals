# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Gama e Épsilon apresentam o mesmo custo; Gama vence pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon, conforme o desempate previsto em [requisitos.md](requisitos.md).

## Fontes e critérios

A análise cruza exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md). O horizonte é de 12 meses, com 80.000 eventos por mês e implantação cobrada uma única vez. Os impostos já estão incluídos. Não há atualização monetária, desconto por antecipação nem acumulação de franquia. O excedente é cobrado por evento, mesmo sem completar um lote.

Os requisitos obrigatórios são R1 (dados primários e backups no Brasil), R2 (exportação completa em formato aberto, incluída no preço e disponível em até 48 horas) e R3 (início da operação em até 20 dias corridos da assinatura). Atender exatamente um limite é suficiente. Condições específicas assinadas prevalecem sobre publicidade genérica, e promessas de funcionalidades futuras não atendem aos requisitos atuais.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: prazo | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil; backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON em versão futura, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |

Alfa atende exatamente os limites de 48 horas e 20 dias, admitidos expressamente pelos requisitos. Beta viola R1 porque os backups permanecem no Chile e a proposta não prevê mudança. Delta viola R2 porque a entrega assinada somente em PDF não comprova a exportação integral em formato aberto exigida; a promessa futura de JSON não vale como atendimento atual, e a expressão comercial “exportação fácil” não substitui a condição assinada. Beta e Delta atendem aos demais requisitos.

## Cálculo dos custos

O cálculo usa centavos inteiros, sem arredondamento:

`custo total = implantação + 12 × (mensalidade + excedentes mensais × tarifa por evento)`

`excedentes mensais = máximo(0, 80.000 − franquia mensal)`

| Fornecedor | Mensalidade | Franquia mensal | Excedentes mensais | Custo mensal de excedentes | Implantação | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

As contas completas em reais são:

- Alfa: R$ 4.000,00 + 12 × (R$ 2.000,00 + 20.000 × R$ 0,02) = R$ 32.800,00.
- Beta: R$ 2.000,00 + 12 × R$ 1.600,00 = R$ 21.200,00.
- Delta: R$ 1.000,00 + 12 × R$ 1.800,00 = R$ 22.600,00.
- Épsilon: R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00.
- Gama: R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00.

A tarifa de R$ 0,04 de Gama não gera cobrança, pois o consumo coincide com a franquia. Os demais fornecedores, exceto Alfa, também não têm excedentes no volume especificado; portanto, não é necessário presumir tarifas que não constam das propostas.

## Decisão, desempate e ressalvas

Entre os elegíveis, Gama e Épsilon custam R$ 31.800,00, e Alfa custa R$ 32.800,00. O primeiro critério de desempate é o menor prazo de implantação: Gama vence com 18 dias, ante 19 dias de Épsilon. O segundo critério, ordem alfabética, não precisa ser aplicado à escolha.

O orçamento desejável de R$ 32.000,00 não é eliminatório; por isso, Alfa permanece elegível apesar de excedê-lo em R$ 800,00. Os custos inferiores de Beta e Delta não permitem sua escolha porque ambas violam requisitos obrigatórios.

Em `answer.json`, `custo_12_meses_centavos` representa o total do fornecedor escolhido. A lista de elegíveis segue a ordem alfabética portuguesa, considerando É como E: Alfa, Épsilon, Gama. As listas de códigos violados estão ordenadas e contêm somente as violações identificadas.

A decisão se limita às condições documentadas e ao consumo fixo informado. Foram usados exatamente dois subagentes diretos, sem descendentes, para auditar elegibilidade e custos separadamente. Ambos retornaram suas análises por mensagem e concluíram antes da criação dos arquivos finais pelo agente principal. Os arquivos de entrada foram preservados.
