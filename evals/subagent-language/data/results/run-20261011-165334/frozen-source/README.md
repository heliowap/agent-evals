# Idioma na comunicação entre subagentes

Piloto preparado em 11/10/2026. Checagem real concluída em
`results/run-20261011-161200/`: três execuções, todas com gabarito e protocolo
aprovados e contadores conciliados. A rodada completa ainda não foi executada.
Python 3.10+, Git e Codex CLI 0.162.1.
Usa o login existente do Codex, com `gpt-6.1-sol` e esforço `high` por padrão.
Não requer dependências Python externas nem uma chave de API adicional.

## Pergunta e alcance

Adicionar uma instrução em português para os agentes se comunicarem em inglês
reduz tokens e tempo de tarefas solicitadas e entregues em português, preservando
a qualidade? A comparação principal é `en` contra `default`; a secundária é `en`
contra `pt`. O piloto não assume que português consome uma porcentagem fixa a mais.

| Condição | Instrução global |
|---|---|
| `default` | Comunicar-se com o usuário em português; sem regra de idioma entre agentes |
| `pt` | Usuário em português e comunicação entre agentes em português |
| `en` | Usuário em português e comunicação entre agentes em inglês |

As condições `pt` e `en` usam a mesma frase, alterando apenas o idioma solicitado.
O bloco inclui delegações e respostas, com preservação de citações e identificadores.
As strings exatas estão em `run.py` e são preservadas no `freeze.json` antes da execução.
O custo da instrução faz parte da medição, inclusive quando ela reaparece no contexto.

Este primeiro piloto restringe a colaboração a dois subagentes diretos, criados
com `fork_turns="none"`. O orquestrador escolhe a divisão de trabalho e pode
trocar mensagens adicionais. Isso mede a instrução em um fluxo com delegação
obrigatória e contexto inicial limpo para cada filho. Não estima o ganho quando
o agente escolhe livremente quantos subagentes criar nem quando herda o histórico
inteiro. Um estudo posterior deve variar esses fatores e usar tarefas reais.

## Tarefas e tamanho

| Tarefa | Trabalho | Gabarito automático |
|---|---|---|
| `incidente` | Cruzar evidências operacionais e histórico de mudanças | Causa, reversão, filas afetadas e evidência de perda |
| `fornecedor` | Cruzar requisitos e propostas | Elegibilidade, exclusões, custo e desempate |
| `acessos` | Aplicar uma política a 16 solicitações | Decisões incluindo exceções e limites de horário |
| `conciliacao` | Cruzar regras de fechamento e eventos | Pedidos incluídos e receita líquida por canal |

São quatro tarefas × três condições × cinco repetições = **60 execuções**, com
120 subagentes planejados além dos 60 orquestradores. Não confundir cinco
repetições com cinco tarefas diferentes. Os documentos são sintéticos e em português.
Gabaritos não são colocados na pasta de trabalho dos agentes.

Cada bloco contém a mesma tarefa/repetição nas três condições. Os blocos são
embaralhados com semente fixa e as seis permutações das condições são distribuídas
com frequências que diferem em no máximo um bloco. Execuções de condições distintas
são sequenciais; os subagentes podem trabalhar em paralelo dentro de uma execução.
Modelo, esforço, ferramentas, arquivos e regra de criação dos filhos são iguais.

## Como rodar

No terminal com acesso normal à rede e login do Codex já disponível:

```sh
cd ~/VSCode/Lab/evals/comunicacao-subagentes/idioma-piloto
python3 run.py run
```

O comando cria uma pasta nova `results/run-AAAAMMDD-HHMMSS`, verifica o isolamento
antes da primeira inferência, mostra o progresso e atualiza `report.md` após cada
execução. Consome a cota do login. Não troca de modelo nem de provedor automaticamente.

Para verificar o acesso ao modelo em outro ambiente, use a checagem curta de três
condições, separada da amostra do piloto:

```sh
python3 run.py run --cases incidente --reps 1
```

Confira se as três execuções terminaram como `completed`, com `protocol_pass=true`,
três sessões em `telemetry.json`, contadores conciliados e dois retornos de subagentes.
Se a checagem funcionar, execute o comando completo. Não agregue a checagem à amostra.
Um desvio do protocolo fica registrado e não interrompe a rodada; erros de
infraestrutura, timeout ou telemetria interrompem. Saída incompleta retorna código 1.

Para escolher parâmetros explicitamente:

```sh
python3 run.py run --model gpt-6.1-sol --effort high --reps 5 --timeout 300
```

O limite é de 300 segundos por execução, incluindo todos os agentes, mas excluindo
preparação e correção. O orçamento de admissão da rodada é de 21.600 segundos.
Um bloco só começa se couberem três limites individuais e uma reserva de 180
segundos para preparação. Isso é um limite de admissão, não um prazo rígido da
rodada inteira. No timeout, o executor encerra o grupo de processos e preserva
os registros parciais. Ctrl-C também preserva o que estiver disponível.
Não há retry pelo harness nem retomada de uma pasta existente. Retries internos
do Codex ficam sujeitos ao timeout e podem não ter consumo reportado pelo serviço.
Uma rodada incompleta deve ser analisada como incompleta, sem preencher lacunas
com uma nova rodada silenciosamente.

Comandos sem inferência e regeneração do relatório:

```sh
python3 -m unittest -v test_eval.py
python3 run.py plan
python3 run.py preflight
python3 run.py report --out results/run-AAAAMMDD-HHMMSS
```

`--out` permite escolher uma pasta nova; para `report`, informa a pasta já existente.
`--auth-file` seleciona outro arquivo de autenticação sem imprimir seu conteúdo.

## Métricas e contagem

O consumo principal é `input_tokens + output_tokens`, somado em todas as sessões
do trial. `token_usage_record` registra consumo por resposta. O coletor deduplica
por `(thread_id, response_id)` e verifica se a soma coincide com o último contador
cumulativo da própria sessão. O contador final do CLI é conciliado como consumo
do orquestrador ou da equipe e nunca somado outra vez. Divergência interrompe a rodada.
Campos obrigatórios ausentes invalidam a medição, em vez de virar zero.

Cache é parte da entrada; raciocínio é parte da saída. Ambos aparecem separados,
sem adição ao total. Registrar também consumo do orquestrador e dos filhos,
quantidade de respostas do modelo, chamadas de ferramentas e número de subagentes.
Não há conversão automática para reais/dólares ou alegação sobre custo do plano.
Tokens de entrada repetidos são consumo observado, não texto único produzido.

O tempo é de relógio, do lançamento do processo até seu término, incluindo
coordenação, ferramentas, espera e geração. Não se somam as durações dos filhos
que rodam simultaneamente. Preparação, cópia dos arquivos e correção ficam fora
desse tempo. O piloto mede a experiência desse CLI, não apenas latência do modelo.

O relatório mostra por tarefa diferenças percentuais pareadas, medianas e extremos,
com `100 × (en / referência − 1)`. Valores negativos indicam redução. Apresenta tanto
execuções completas e mensuráveis independentemente de acerto quanto o subconjunto
em que ambos os lados passaram no gabarito e no protocolo. Essa segunda análise
pode sofrer viés de seleção. Falhas, não iniciadas e desvios ficam explícitos.
Consumo incompleto de chamadas que falharam não entra como economia.

Uma diferença em tokens pode vir de tokenização, respostas mais curtas, menos
rodadas ou estratégia diferente. Este piloto não separa essas causas. Não estime
economia de latência a partir de tokens: meça ambas. Cache remoto e carga do
serviço não são controlados; a ordem alternada reduz, mas não elimina, sua influência.

## Qualidade, idioma e decisão

`answer.json` tem correção exata com tipos, chaves e valores definidos na tarefa.
O corretor exige entradas preservadas e `report.md` presente, mas não confunde
presença de texto com qualidade. A explicação e o português exigem revisão humana
cega conforme [REVIEW.md](REVIEW.md). Os retornos e mensagens entre agentes ficam
em `language-review.json`, com rótulos de idioma inicialmente vazios.
Não se pede nem se infere o idioma do raciocínio interno.

A checagem real revelou que o CLI cifra delegações e mensagens intermediárias
nos rollouts. O coletor reconhece os blocos `encrypted_content`, marca essas
mensagens como `unobservable` e não exporta o conteúdo cifrado como prosa para
revisão. `communication_observability` mostra a cobertura; `language_audit_complete`
indica disponibilidade de texto em todas as mensagens, não aprovação do idioma.
Na checagem, são legíveis dois retornos finais por condição; quatro mensagens
em `default`/`pt` e seis em `en` não são observáveis. Isso limita a auditoria de
adesão, mas não invalida a comparação da instrução atribuída sobre tokens e tempo.
`protocol_pass` cobre a estrutura de delegação, não o idioma. Os resultados
originais foram preservados; a auditoria atualizada está em `smoke-audit.json`.

A análise principal mantém a condição atribuída mesmo quando a instrução de idioma
é desobedecida. Essa adesão faz parte da utilidade prática da instrução. Uma análise
restrita a quem obedeceu pode ser exploratória e deve ser identificada separadamente.

O relatório automático mantém o veredito de adoção inconclusivo. Mesmo cinco
repetições em quatro tarefas não demonstram não inferioridade de qualidade nem
generalizam para programação, pesquisa web ou histórico herdado. Antes de uma
confirmação, definir ganho mínimo útil, margem de regressão aceitável e novos casos.
Não escolher a melhor redação nestas tarefas e apresentar a mesma amostra como confirmação.

## Isolamento e arquivos

Cada trial recebe diretório temporário, repositório Git, estado Codex e configuração
próprios. `CODEX_HOME` é definido somente no ambiente do processo filho. O arquivo
de autenticação é copiado para o estado temporário com permissão 0600 e removido
no encerramento. O perfil e as instruções reais do usuário não são alterados.
Skills, plugins, apps, memória, hooks e web ficam desativados. Agentes ficam ativados.

O adaptador deriva do runtime em `instrucoes-agents/agentsmd-detfirst-isolated/`,
com configuração explícita de subagentes e modelo/esforço parametrizados. A cópia
local permite congelar toda a implementação deste piloto sem mudar estudos antigos.
A inspeção `codex debug prompt-input` desabilita skills descobertas e compara as
instruções efetivamente visíveis. Isso não é uma captura HTTP nem isolamento total
de leitura do sistema de arquivos; o agente poderia ler arquivos fora do trabalho.

`freeze.json` guarda tarefas, gabaritos, condições, ordem e hashes das fontes antes
da primeira inferência. `frozen-source/` guarda a versão correspondente. Cada trial
preserva o prompt, contexto inspecionado, eventos, stderr, rollouts de todas as
sessões, artefatos finais, notas e métricas. Credenciais não são copiadas para resultados.

As opções de agentes seguem a [referência oficial do Codex](https://learn.chatgpt.com/docs/config-file/config-reference).
O formato de telemetria é verificado contra o CLI instalado e fixado na versão
0.162.1. Mudança de versão exige revisar o coletor antes de gerar novos resultados.
