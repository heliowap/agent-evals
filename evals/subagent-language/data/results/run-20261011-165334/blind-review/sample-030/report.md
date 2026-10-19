# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Atende aos três requisitos obrigatórios e empata em custo com Épsilon. O desempate favorece Gama pela implantação em 18 dias, contra 19 dias de Épsilon. Não foi necessário aplicar o segundo desempate, por ordem alfabética.

## Base e critérios

A análise cruza exclusivamente `requisitos.md` e `propostas.md`. Considera 80.000 eventos por mês durante 12 meses, implantação cobrada uma única vez e valores em reais, sem atualização monetária ou desconto antecipado. Os impostos já estão incluídos nas propostas. A franquia não utilizada não acumula; cada evento excedente é cobrado individualmente, sem arredondamento para lotes.

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início da operação em até 20 dias corridos desde a assinatura. Os limites exatos são aceitos. Condições específicas assinadas prevalecem sobre anúncios genéricos, e promessas de funcionalidades futuras não atendem a requisitos atuais.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: implantação | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados no Brasil; backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON futuro sem data | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

**Beta viola apenas R1:** os backups ficam no Chile, e a proposta não prevê mudança. O requisito exige que tanto os dados primários quanto os backups estejam no Brasil.

**Delta viola apenas R2:** a condição assinada entrega somente PDF, sem garantir a exportação integral dos dados em formato aberto exigida. O JSON está previsto apenas para uma versão futura, sem data contratual, e não pode ser considerado atendimento atual. O anúncio de “exportação fácil” não substitui a condição assinada. Também não há garantia contratada de atendimento ao conjunto das exigências de R2 em até 48 horas.

Alfa atende exatamente os limites de 48 horas para exportação e 20 dias para implantação. Todos os fornecedores atendem R3. Os elegíveis, em ordem alfabética portuguesa, são **Alfa, Épsilon e Gama**; Épsilon é ordenado sob a letra E.

## Cálculo do custo

Para cada fornecedor:

`excedentes mensais = máximo(0, 80.000 − franquia mensal)`

`custo em 12 meses = 12 × (mensalidade + excedentes mensais × preço por evento excedente) + implantação`

| Fornecedor | Franquia mensal | Excedentes por mês | Custo dos excedentes por mês | Mensalidade | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | 60.000 | 20.000 | R$ 400,00 | R$ 2.000,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | 100.000 | 0 | R$ 0,00 | R$ 1.600,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Gama | 80.000 | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Delta | 80.000 | 0 | R$ 0,00 | R$ 1.800,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | 80.000 | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

- Alfa: `12 × (2.000 + 20.000 × 0,02) + 4.000 = R$ 32.800,00`.
- Beta: `12 × 1.600 + 2.000 = R$ 21.200,00`.
- Gama: `12 × 2.400 + 3.000 = R$ 31.800,00`.
- Delta: `12 × 1.800 + 1.000 = R$ 22.600,00`.
- Épsilon: `12 × 2.400 + 3.000 = R$ 31.800,00`.

## Decisão e ressalvas

Beta e Delta custam menos, mas não participam da escolha por violarem requisitos obrigatórios. Entre os elegíveis, Gama e Épsilon têm o menor custo; o prazo de implantação decide a favor de Gama.

O orçamento desejável de R$ 32.000,00 não é eliminatório. Alfa permanece elegível apesar de ultrapassá-lo em R$ 800,00. Gama fica R$ 200,00 abaixo desse orçamento.

A comparação vale para o volume fixo de 80.000 eventos mensais informado. Beta, Delta e Épsilon não especificam tarifa excedente, mas ela não é necessária neste cenário, pois o consumo está dentro das respectivas franquias. Gama prevê R$ 0,04 por evento acima da franquia, sem impacto no volume analisado. Não foram presumidas funcionalidades futuras ou alterações contratuais.

Dois subagentes diretos, sem descendentes e com contexto independente, analisaram elegibilidade e custos e retornaram suas conclusões por mensagem. O agente principal conferiu os cálculos em centavos, ajustou a ordenação alfabética portuguesa e escreveu os arquivos finais após a conclusão de ambos. Os arquivos de entrada foram preservados.
