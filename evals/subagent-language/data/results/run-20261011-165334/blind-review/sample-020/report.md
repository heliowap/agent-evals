# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses (3.180.000 centavos)**. Gama e Épsilon empatam no menor custo entre os elegíveis; Gama vence pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon. O segundo critério de desempate, ordem alfabética, não precisa ser aplicado.

## Fontes e critérios

A análise usa exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md), preservados sem alterações. Foram consultados exatamente dois subagentes diretos, sem descendentes: um analisou a elegibilidade e o outro calculou custos e desempate. Ambos concluíram suas análises por mensagem; somente o agente principal escreveu os arquivos finais e conferiu os resultados.

Os requisitos obrigatórios são: R1, dados primários e backups armazenados no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos. Condições específicas assinadas prevalecem sobre texto comercial, e funcionalidades futuras não contam como atendimento atual.

## Elegibilidade e exclusões

| Fornecedor | R1 | R2 | R3 | Resultado e evidência da proposta |
|---|---|---|---|---|
| Alfa | Atende | Atende | Atende | Dados e backups no Brasil; JSON integral incluído em 48 horas; implantação em 20 dias. Os dois limites exatos atendem. |
| Beta | Viola | Atende | Atende | Dados primários no Brasil, mas backups no Chile, sem previsão de mudança. CSV integral incluído em 24 horas e implantação em 10 dias. Excluído por R1. |
| Delta | Atende | Viola | Atende | Dados e backups no Brasil; implantação em 15 dias. A condição assinada entrega somente PDF e promete JSON em versão futura, sem data contratual. Excluído por R2. |
| Épsilon | Atende | Atende | Atende | Dados e backups no Brasil; CSV integral incluído em 24 horas; implantação em 19 dias. |
| Gama | Atende | Atende | Atende | Dados e backups no Brasil; JSON integral incluído em 36 horas; implantação em 18 dias. |

Para Delta, a entrega somente em PDF não comprova a exportação integral em formato aberto exigida por R2. O anúncio genérico de “exportação fácil” não supera a condição assinada, e o JSON futuro não atende atualmente.

Os elegíveis são **Alfa, Épsilon e Gama**, em ordem alfabética portuguesa, considerando É como E. Os códigos de requisitos violados em `excluidos` estão ordenados; cada fornecedor excluído viola apenas um requisito.

## Cálculos de custo

Para cada mês, o excedente é `máximo(80.000 − franquia, 0)`. O custo total é:

`implantação + 12 × (mensalidade + eventos excedentes mensais × tarifa por evento)`.

| Fornecedor | Excedentes por mês | Custo mensal de excedentes | Mensalidade com excedentes | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|
| Alfa | 20.000 | R$ 400,00 | R$ 2.400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | 0 | R$ 0,00 | R$ 1.600,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Delta | 0 | R$ 0,00 | R$ 1.800,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Gama | 0 | R$ 0,00 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

- Alfa: `4.000 + 12 × (2.000 + 20.000 × 0,02) = R$ 32.800,00`.
- Beta: `2.000 + 12 × 1.600 = R$ 21.200,00`.
- Delta: `1.000 + 12 × 1.800 = R$ 22.600,00`.
- Épsilon: `3.000 + 12 × 2.400 = R$ 31.800,00`.
- Gama: `3.000 + 12 × (2.400 + 0 × 0,04) = R$ 31.800,00`.

Beta e Delta têm custos inferiores aos de Gama, mas são inelegíveis. Entre os elegíveis, Alfa custa R$ 1.000,00 a mais que Gama e Épsilon. O desempate pelo menor prazo de implantação seleciona Gama.

## Ressalvas

O volume considerado é fixo: 80.000 eventos por mês durante 12 meses, totalizando 960.000 eventos. A franquia é apurada mensalmente e não acumula; os 20.000 eventos mensais não utilizados de Beta não geram crédito. Excedentes são cobrados por evento, sem arredondamento por lotes. A implantação entra uma única vez, os impostos já estão incluídos, e não há atualização monetária nem desconto por antecipação.

Beta, Delta e Épsilon não informam tarifa de excedentes; isso não afeta o cenário solicitado, pois suas franquias cobrem o volume mensal. O orçamento desejável de R$ 32.000,00 não é eliminatório: Alfa continua elegível apesar de ultrapassá-lo, e Gama fica R$ 200,00 abaixo dele. A avaliação se limita às condições fornecidas nos dois arquivos.
