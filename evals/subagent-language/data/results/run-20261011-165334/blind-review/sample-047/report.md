# Escolha do fornecedor

**Gama é o fornecedor escolhido**, com custo total de **R$ 31.800,00 em 12 meses**, equivalente a **3.180.000 centavos**. Gama e Épsilon empatam no menor custo entre os elegíveis; Gama vence pelo prazo de implantação de 18 dias, contra 19 dias de Épsilon. Não é necessário aplicar o segundo critério de desempate, a ordem alfabética.

## Fontes e critérios

A análise utiliza exclusivamente [requisitos.md](requisitos.md) e [propostas.md](propostas.md). O horizonte é de 12 meses, com 80.000 eventos em cada mês. A implantação é cobrada uma única vez. Não há atualização monetária nem desconto por antecipação, e os valores das propostas já incluem impostos.

Os requisitos obrigatórios são: R1, dados primários e backups no Brasil; R2, exportação completa em formato aberto, incluída no preço e disponível em até 48 horas; R3, operação iniciada em até 20 dias corridos da assinatura. Os limites são inclusivos. Condições específicas assinadas prevalecem sobre publicidade, e funcionalidades futuras não comprovam atendimento atual.

## Elegibilidade e evidências

| Fornecedor | R1: armazenamento | R2: exportação | R3: implantação | Resultado |
|---|---|---|---|---|
| Alfa | Dados e backups no Brasil | JSON integral incluído, em 48 horas | 20 dias | Elegível |
| Beta | Dados primários no Brasil, backups no Chile | CSV integral incluído, em 24 horas | 10 dias | Excluído por R1 |
| Gama | Dados e backups no Brasil | JSON integral incluído, em 36 horas | 18 dias | Elegível |
| Delta | Dados e backups no Brasil | Somente PDF na condição assinada; JSON prometido para versão futura, sem data contratual | 15 dias | Excluído por R2 |
| Épsilon | Dados e backups no Brasil | CSV integral incluído, em 24 horas | 19 dias | Elegível |

Beta viola R1 porque seus backups ficam no Chile. A proposta não prevê mudança dessa localização.

Delta não garante atualmente a exportação completa em formato aberto, incluída e disponível em até 48 horas exigida por R2. O anúncio genérico de “exportação fácil” não supera a condição assinada, que entrega somente PDF e deixa JSON para uma versão futura sem data. A exclusão decorre da ausência de garantia de atendimento integral a R2; não pressupõe que todo PDF seja um formato fechado.

Alfa atende exatamente os limites de R2 e R3. Os elegíveis são Alfa, Épsilon e Gama, em ordem alfabética portuguesa, considerando É na posição da letra E. Cada lista de códigos de exclusão está ordenada; neste caso, cada excluído viola apenas um requisito identificado.

## Cálculo dos custos

Para cada fornecedor:

`excedentes mensais = máximo(0, 80.000 − franquia mensal)`

`custo em 12 meses = implantação + 12 × (mensalidade + excedentes mensais × preço por evento)`

Cada evento excedente é cobrado individualmente, sem arredondar para lotes. Franquia não utilizada não acumula entre meses.

| Fornecedor | Mensalidade | Franquia mensal | Excedentes mensais | Custo mensal com excedentes | Implantação única | Total em 12 meses | Total em centavos |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alfa | R$ 2.000,00 | 60.000 | 20.000 | R$ 2.400,00 | R$ 4.000,00 | R$ 32.800,00 | 3.280.000 |
| Beta | R$ 1.600,00 | 100.000 | 0 | R$ 1.600,00 | R$ 2.000,00 | R$ 21.200,00 | 2.120.000 |
| Gama | R$ 2.400,00 | 80.000 | 0 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |
| Delta | R$ 1.800,00 | 80.000 | 0 | R$ 1.800,00 | R$ 1.000,00 | R$ 22.600,00 | 2.260.000 |
| Épsilon | R$ 2.400,00 | 80.000 | 0 | R$ 2.400,00 | R$ 3.000,00 | R$ 31.800,00 | 3.180.000 |

Alfa: `R$ 4.000,00 + 12 × (R$ 2.000,00 + 20.000 × R$ 0,02) = R$ 32.800,00`.

Beta: `R$ 2.000,00 + 12 × R$ 1.600,00 = R$ 21.200,00`. Sobram 20.000 eventos de franquia por mês, sem acúmulo nem redução da mensalidade.

Gama: `R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00`. O preço de R$ 0,04 por excedente não incide, pois o volume é exatamente igual à franquia.

Delta: `R$ 1.000,00 + 12 × R$ 1.800,00 = R$ 22.600,00`.

Épsilon: `R$ 3.000,00 + 12 × R$ 2.400,00 = R$ 31.800,00`.

## Decisão e ressalvas

Beta e Delta custam menos, mas não participam da escolha por descumprirem requisitos obrigatórios. Entre os elegíveis, Gama e Épsilon custam R$ 1.000,00 menos que Alfa e empatam entre si. O menor prazo de implantação determina a escolha de Gama.

O orçamento de R$ 32.000,00 é desejável, não eliminatório. Alfa permanece elegível apesar de ultrapassá-lo em R$ 800,00. Gama fica R$ 200,00 abaixo desse orçamento.

Os cálculos usam o volume mensal fixo solicitado e valores inteiros em centavos. Não foram acrescentadas cobranças não previstas nas propostas. A elegibilidade depende das garantias atuais documentadas nos arquivos fornecidos.

Exatamente dois subagentes diretos, sem descendentes, realizaram análises de elegibilidade e custos e retornaram suas conclusões por mensagem. Ambos concluíram antes da redação final. Somente o agente principal escreveu os arquivos finais; os arquivos de entrada foram preservados.
