# Piloto de idioma entre subagentes

Veredito de adoção: inconclusivo. Revisão humana de qualidade e idioma pendente.

Medianas [mínimo; máximo]. Tokens incluem todos os agentes; cache e raciocínio são parcelas, não acréscimos.

| Condição | Planejadas | Concluídas e mensuráveis | Passes factuais | Protocolo correto | Erros/timeouts | Não iniciadas |
|---|---:|---:|---:|---:|---:|---:|
| default | 20 | 20 | 15 | 20 | 0 | 0 |
| pt | 20 | 20 | 16 | 20 | 0 | 0 |
| en | 20 | 20 | 15 | 20 | 0 | 0 |

## Diferenças pareadas por tarefa

Valores negativos favorecem en. Cada par usa a mesma tarefa e repetição.
Todas as execuções completas e mensuráveis entram na primeira linha, inclusive erros factuais e desvios do protocolo.
A segunda linha é análise condicionada a acerto factual e protocolo em ambos os lados; pode ter viés de seleção.

| Caso | Comparação | Amostra | Pares | Δ tokens % | Δ tempo % |
|---|---|---|---:|---|---|
| incidente | en / default | completas | 5 | 4.6 [-9.8; 23.9] | 1.8 [-8.0; 4.2] |
| incidente | en / default | acerto+protocolo | 5 | 4.6 [-9.8; 23.9] | 1.8 [-8.0; 4.2] |
| incidente | en / pt | completas | 5 | -0.2 [-4.0; 12.5] | 4.0 [-8.1; 8.3] |
| incidente | en / pt | acerto+protocolo | 5 | -0.2 [-4.0; 12.5] | 4.0 [-8.1; 8.3] |
| fornecedor | en / default | completas | 5 | 4.8 [-2.5; 22.5] | -2.3 [-13.5; 17.9] |
| fornecedor | en / default | acerto+protocolo | 0 | sem dados | sem dados |
| fornecedor | en / pt | completas | 5 | 10.6 [-19.6; 52.9] | 5.0 [-9.1; 8.1] |
| fornecedor | en / pt | acerto+protocolo | 0 | sem dados | sem dados |
| conciliacao | en / default | completas | 5 | 0.2 [-18.6; 41.6] | -2.5 [-23.1; 3.2] |
| conciliacao | en / default | acerto+protocolo | 5 | 0.2 [-18.6; 41.6] | -2.5 [-23.1; 3.2] |
| conciliacao | en / pt | completas | 5 | 0.3 [-16.9; 15.1] | -10.7 [-16.8; -4.3] |
| conciliacao | en / pt | acerto+protocolo | 5 | 0.3 [-16.9; 15.1] | -10.7 [-16.8; -4.3] |
| acessos | en / default | completas | 5 | -6.3 [-10.1; 19.4] | -4.4 [-14.9; -0.3] |
| acessos | en / default | acerto+protocolo | 5 | -6.3 [-10.1; 19.4] | -4.4 [-14.9; -0.3] |
| acessos | en / pt | completas | 5 | -2.3 [-20.9; 0.1] | -1.9 [-15.5; 3.9] |
| acessos | en / pt | acerto+protocolo | 5 | -2.3 [-20.9; 0.1] | -1.9 [-15.5; 3.9] |

## Medidas absolutas por condição

Somente execuções completas e mensuráveis. Não interpretar falhas rápidas como economia.

| Condição | Tokens de entrada | Tokens de saída | Entrada em cache | Raciocínio | Tempo total s |
|---|---|---|---|---|---|
| default | 253268.0 [195247.0; 329910.0] | 4930.0 [3706.0; 6834.0] | 220736.0 [165632.0; 302464.0] | 260.5 [33.0; 677.0] | 102.7 [86.1; 130.5] |
| pt | 246826.5 [183077.0; 321849.0] | 4690.5 [3558.0; 6114.0] | 216384.0 [165376.0; 276992.0] | 269.5 [87.0; 356.0] | 101.4 [84.5; 130.2] |
| en | 248793.5 [221319.0; 362942.0] | 4489.0 [3402.0; 5842.0] | 214656.0 [192384.0; 316928.0] | 285.5 [23.0; 628.0] | 98.2 [87.0; 111.9] |

Rodadas interrompidas preservam registros brutos, mas o consumo de chamadas que falharam pode não ser informado pelo provedor.
O CLI pode cifrar delegações e mensagens intermediárias nos registros. protocol_pass verifica a estrutura de delegação, não adesão ao idioma.
Consulte communication_observability em cada resultado. Mensagens cifradas ficam unobservable na revisão; respostas finais legíveis não provam adesão integral.
Quatro tarefas sintéticas não sustentam generalização. Não há conversão de tokens em custo monetário nem estimativa de idioma do raciocínio interno.
Use REVIEW.md e os pacotes de revisão antes de interpretar eficiência com qualidade preservada.
