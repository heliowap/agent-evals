# Piloto de idioma entre subagentes

Veredito de adoção: inconclusivo. Revisão humana de qualidade e idioma pendente.

Medianas [mínimo; máximo]. Tokens incluem todos os agentes; cache e raciocínio são parcelas, não acréscimos.

| Condição | Planejadas | Concluídas e mensuráveis | Passes factuais | Protocolo correto | Erros/timeouts | Não iniciadas |
|---|---:|---:|---:|---:|---:|---:|
| default | 1 | 1 | 1 | 1 | 0 | 0 |
| pt | 1 | 1 | 1 | 1 | 0 | 0 |
| en | 1 | 1 | 1 | 1 | 0 | 0 |

## Diferenças pareadas por tarefa

Valores negativos favorecem en. Cada par usa a mesma tarefa e repetição.
Todas as execuções completas e mensuráveis entram na primeira linha, inclusive erros factuais e desvios do protocolo.
A segunda linha é análise condicionada a acerto factual e protocolo em ambos os lados; pode ter viés de seleção.

| Caso | Comparação | Amostra | Pares | Δ tokens % | Δ tempo % |
|---|---|---|---:|---|---|
| incidente | en / default | completas | 1 | 9.1 [9.1; 9.1] | -12.6 [-12.6; -12.6] |
| incidente | en / default | acerto+protocolo | 1 | 9.1 [9.1; 9.1] | -12.6 [-12.6; -12.6] |
| incidente | en / pt | completas | 1 | 35.9 [35.9; 35.9] | 3.1 [3.1; 3.1] |
| incidente | en / pt | acerto+protocolo | 1 | 35.9 [35.9; 35.9] | 3.1 [3.1; 3.1] |

## Medidas absolutas por condição

Somente execuções completas e mensuráveis. Não interpretar falhas rápidas como economia.

| Condição | Tokens de entrada | Tokens de saída | Entrada em cache | Raciocínio | Tempo total s |
|---|---|---|---|---|---|
| default | 249118.0 [249118.0; 249118.0] | 4853.0 [4853.0; 4853.0] | 221952.0 [221952.0; 221952.0] | 225.0 [225.0; 225.0] | 117.4 [117.4; 117.4] |
| pt | 199764.0 [199764.0; 199764.0] | 4011.0 [4011.0; 4011.0] | 170752.0 [170752.0; 170752.0] | 32.0 [32.0; 32.0] | 99.4 [99.4; 99.4] |
| en | 272480.0 [272480.0; 272480.0] | 4492.0 [4492.0; 4492.0] | 219392.0 [219392.0; 219392.0] | 94.0 [94.0; 94.0] | 102.5 [102.5; 102.5] |

Rodadas interrompidas preservam registros brutos, mas o consumo de chamadas que falharam pode não ser informado pelo provedor.
Quatro tarefas sintéticas não sustentam generalização. Não há conversão de tokens em custo monetário nem estimativa de idioma do raciocínio interno.
Use REVIEW.md e os pacotes de revisão antes de interpretar eficiência com qualidade preservada.
