# Decisão de contratação

O fornecedor escolhido é **Gama**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Gama e Épsilon têm o mesmo custo; Gama vence pelo menor prazo de implantação: 18 dias contra 19 dias. Não é necessário aplicar o segundo desempate, por ordem alfabética.

## Fontes e critérios

A análise cruza exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md), preservados sem alterações. Foram obtidas duas análises independentes, uma de elegibilidade e outra de custos, e conferidos seus resultados antes da elaboração dos arquivos finais.

Os requisitos obrigatórios são R1 (dados primários e backups no Brasil), R2 (exportação completa em formato aberto, incluída no preço e disponível em até 48 horas) e R3 (início de operação em até 20 dias corridos da assinatura). Os limites são inclusivos. Condições específicas assinadas prevalecem sobre anúncios comerciais; funcionalidades futuras não comprovam atendimento atual.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: prazo | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível; atende exatamente aos limites de R2 e R3 |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Condição assinada entrega somente PDF; JSON é futuro, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

**Beta viola somente R1:** os backups ficam no Chile, e a proposta não prevê mudança. Atende R2 e R3.

**Delta viola somente R2:** a condição assinada oferece somente PDF, sem assegurar a exportação integral dos dados em formato aberto requerida. O anúncio de “exportação fácil” não substitui essa condição, e a promessa de JSON em versão futura, sem data contratual, não atende ao requisito atual. Atende R1 e R3.

Os elegíveis são **Alfa, Épsilon e Gama**, nessa ordem alfabética em português, considerando É como E para ordenação e preservando a grafia original dos nomes.

## Cálculos

Para cada fornecedor:

```text
excedentes mensais = máximo(0, 80.000 − franquia mensal)
custo mensal = mensalidade + excedentes mensais × tarifa por evento
custo em 12 meses = implantação + 12 × custo mensal
```

| Fornecedor | Mensalidade | Franquia mensal | Excedentes mensais | Custo dos excedentes/mês | Custo mensal total | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 2.400,00 | R$ 4.000,00 | R$ 32.800,00 | 3280000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 1.600,00 | R$ 2.000,00 | R$ 21.200,00 | 2120000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3180000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.800,00 | R$ 1.000,00 | R$ 22.600,00 | 2260000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3180000 |

Alfa excede a franquia em 20.000 eventos por mês: 20.000 × R$ 0,02 = R$ 400,00. Seu total é R$ 4.000,00 + 12 × (R$ 2.000,00 + R$ 400,00) = R$ 32.800,00.

Beta custa R$ 2.000,00 + 12 × R$ 1.600,00 = R$ 21.200,00. Delta custa R$ 1.000,00 + 12 × R$ 1.800,00 = R$ 22.600,00. Seus custos menores não permitem escolhê-los, pois ambos violam requisitos obrigatórios.

Gama e Épsilon custam, cada um, R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00. A tarifa excedente de Gama, R$ 0,04 por evento, não gera cobrança neste cenário, pois o consumo coincide com sua franquia.

## Ressalvas e validação

O cenário usa 80.000 eventos em cada um dos 12 meses, sem acumular franquias, descontar pagamentos antecipados ou aplicar atualização monetária. A implantação é cobrada uma única vez. Os impostos já estão incluídos nos valores das propostas. Não há excedentes em Beta, Delta ou Épsilon; portanto, não é necessário presumir tarifas excedentes ausentes nesses documentos.

O orçamento de R$ 32.000,00 é desejável, não eliminatório. Alfa permanece elegível mesmo custando R$ 800,00 acima dele. Gama fica R$ 200,00 abaixo desse orçamento.

A conclusão se limita às condições documentadas nos dois arquivos. O contrato de `answer.json` contém exatamente `escolhido`, `elegiveis`, `custo_12_meses_centavos` e `excluidos`; o custo corresponde ao fornecedor escolhido e está expresso como inteiro em centavos. As listas de códigos violados estão ordenadas. A integridade dos arquivos de entrada foi conferida por SHA-256 antes e depois da criação das entregas.
