# Seleção do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses (3.180.000 centavos)**. Gama e Épsilon empatam no menor custo entre os elegíveis; Gama vence pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon. Não é necessário aplicar o segundo critério de desempate, a ordem alfabética.

## Fontes e critérios

A análise usa exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md). Os arquivos de entrada foram preservados. Dois subagentes diretos fizeram análises independentes de elegibilidade e custos, sem criar arquivos ou outros subagentes; suas conclusões foram conferidas pelo agente principal, responsável pelos arquivos finais.

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, início de operação em até 20 dias corridos da assinatura. Os limites são inclusivos, condições específicas assinadas prevalecem sobre publicidade genérica e funcionalidades futuras não contam como atendimento atual.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: implantação | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído: R1 |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON futuro sem data contratual | 15 dias | Excluído: R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |

**Beta viola R1:** o armazenamento dos backups no Chile contraria a exigência de armazenamento no Brasil. A proposta não prevê mudança dessa condição. Beta atende R2 e R3.

**Delta viola R2:** a condição assinada entrega somente PDF, sem assegurar a exportação completa em formato aberto exigida. A promessa de JSON em versão futura, sem data contratual, não atende ao requisito atual. O anúncio de “exportação fácil” não substitui a condição assinada. Delta atende R1 e R3.

Alfa atende exatamente os limites de 48 horas e 20 dias. Todos os fornecedores atendem R3. A lista de elegíveis é Alfa, Épsilon e Gama, em ordem alfabética portuguesa, considerando É sob a letra E. As listas de códigos violados estão ordenadas.

## Cálculo dos custos

Para cada fornecedor, o custo mensal é a mensalidade acrescida de `máximo(0, 80.000 − franquia) × preço por evento excedente`. O total é `12 × custo mensal + implantação`, cobrada uma única vez.

| Fornecedor | Mensalidade | Franquia mensal | Excedentes por mês | Custo dos excedentes por mês | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 0,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 0,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 0,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

- Alfa: `12 × (2.000 + 20.000 × 0,02) + 4.000 = R$ 32.800,00`.
- Beta: `12 × 1.600 + 2.000 = R$ 21.200,00`.
- Delta: `12 × 1.800 + 1.000 = R$ 22.600,00`.
- Épsilon: `12 × 2.400 + 3.000 = R$ 31.800,00`.
- Gama: `12 × 2.400 + 3.000 = R$ 31.800,00`.

Beta e Delta têm totais menores, mas são inelegíveis. Entre os elegíveis, Gama e Épsilon custam R$ 1.000,00 menos que Alfa. O desempate por prazo determina Gama.

## Ressalvas

O resultado considera exatamente 80.000 eventos em cada um dos 12 meses. Não há atualização monetária, desconto antecipado nem acúmulo de franquia não utilizada. Os preços já incluem impostos. A cobrança de excedentes é por evento, sem arredondamento para lotes; somente Alfa tem excedentes neste cenário. Gama cobra R$ 0,04 por evento acima da franquia, mas não há excesso no volume informado. Não é necessário supor tarifas de excedentes não informadas para os demais fornecedores.

O orçamento desejável de R$ 32.000,00 não é eliminatório: Alfa permanece elegível apesar de excedê-lo em R$ 800,00. Gama fica R$ 200,00 abaixo desse orçamento. A conclusão se limita às condições documentadas nos dois arquivos de entrada.
