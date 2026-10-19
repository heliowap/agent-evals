# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Gama e Épsilon têm o mesmo menor custo entre os elegíveis; Gama vence pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon. O critério seguinte, ordem alfabética, não precisa ser aplicado ao desempate.

## Fontes e critérios

A análise utiliza exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md), preservados sem alterações. Foram realizadas duas conferências por subagentes diretos: elegibilidade e custos/desempate. Ambos retornaram análises; os arquivos finais foram escritos pelo agente principal.

Os requisitos obrigatórios são R1 (dados primários e backups no Brasil), R2 (exportação completa em formato aberto, incluída no preço e disponível em até 48 horas) e R3 (início de operação em até 20 dias corridos da assinatura). Os limites são inclusivos. Condições específicas assinadas prevalecem sobre publicidade genérica, e funcionalidades futuras não comprovam atendimento atual.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: início | Decisão |
| --- | --- | --- | --- | --- |
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível: atende inclusive os limites de R2 e R3 |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Condição assinada entrega somente PDF; JSON é futuro, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

Beta viola somente R1: os backups ficam no Chile e a proposta não prevê mudança. Delta viola somente R2: a condição assinada não garante a exportação completa em formato aberto exigida; entrega somente PDF e promete JSON em versão futura sem data. O anúncio comercial de “exportação fácil” não supera a condição assinada nem comprova o atendimento atual de R2.

A lista de elegíveis em `answer.json` segue a ordem alfabética portuguesa: Alfa, Épsilon, Gama, considerando É pela letra E. Cada lista de códigos violados está ordenada.

## Cálculos em 12 meses

O volume é de 80.000 eventos em cada mês, totalizando 960.000 eventos. Para cada fornecedor:

```text
excedentes_mensais = máximo(80.000 − franquia_mensal, 0)
custo_mensal = mensalidade + excedentes_mensais × preço_por_evento
custo_12_meses = implantação + 12 × custo_mensal
```

| Fornecedor | Mensalidade | Franquia mensal | Excedentes mensais | Custo do excedente por mês | Implantação única | Cálculo do total | Total em centavos |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 4.000,00 + 12 × R$ 2.400,00 = **R$ 32.800,00** | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 2.000,00 + 12 × R$ 1.600,00 = **R$ 21.200,00** | 2.120.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 3.000,00 + 12 × R$ 2.400,00 = **R$ 31.800,00** | 3.180.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 1.000,00 + 12 × R$ 1.800,00 = **R$ 22.600,00** | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 3.000,00 + 12 × R$ 2.400,00 = **R$ 31.800,00** | 3.180.000 |

Em Alfa, 20.000 eventos excedentes × R$ 0,02 = R$ 400,00 por mês. Gama não gera excedentes, pois o consumo coincide com a franquia; sua tarifa de R$ 0,04 por evento adicional não incide neste cenário. As demais propostas também não geram excedentes. Os totais de Beta e Delta são apresentados para transparência, mas sua inelegibilidade impede a escolha, apesar dos custos menores.

## Ressalvas e validação

- A implantação é cobrada uma única vez. Os impostos já estão incluídos; não há atualização monetária nem desconto por pagamento antecipado.
- A franquia é mensal e não acumula. A sobra de Beta não gera crédito. Excedentes são cobrados por evento, sem arredondamento por lotes.
- Não é necessário presumir tarifas de excedente não informadas para Beta, Delta ou Épsilon, pois o volume contratado não excede suas franquias.
- O orçamento de R$ 32.000,00 é desejável, não eliminatório. Alfa permanece elegível mesmo ficando R$ 800,00 acima; Gama fica R$ 200,00 abaixo.
- A decisão considera as condições documentadas para o volume fixado, sem assumir futuras funcionalidades ou alterações de contrato.
- `answer.json` contém exatamente as quatro chaves solicitadas. O custo está representado como inteiro em centavos; as listas de elegíveis e de códigos seguem as ordenações exigidas.
