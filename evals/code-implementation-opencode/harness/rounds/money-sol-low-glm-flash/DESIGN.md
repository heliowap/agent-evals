# Sol low Fast e GLM Flash no contrato monetário corrigido

## Problema

Os três candidatos novos precisam executar o mesmo contrato de `money-contract-v2`. Os gates anteriores não contêm essas configurações. Alterar as fontes históricas invalidaria sua proveniência.

## Uso

```sh
python3 -B implementacao/opencode-implementador/rounds/money-sol-low-glm-flash/run.py run \
  --out implementacao/opencode-implementador/results/money-sol-low-glm-flash
```

Um comando executa três provas de interrupção, três smokes e nove trials monetários, sequencialmente. Cada fase escreve em seu próprio diretório. Os gates precisam passar antes da fase seguinte. A saída precisa ser nova.

## Forma

O pacote contém `run.py`, a proveniência e uma cópia das fontes congeladas. `Candidate` continua sendo o tipo que reúne identidade, variante, effort, protocolo e autenticação. A coorte fixa contém Sol 6.1 low Fast via OAuth nativo e GLM 5.3 Flash high e max via OpenCode Go.

`harness/domain.py` muda apenas a coorte. `harness/tasks.py` seleciona somente o caso monetário corrigido para screening. Uma constante do contrato em `harness/contract.py` participa do congelamento das fontes pelo executor. Os demais arquivos do núcleo mantêm os bytes da fotografia original. O novo `TaskSpec` deve ser integralmente igual ao da rodada monetária corrigida.

O runner verifica a origem e os hashes, congela sua própria fonte e coordena subprocessos do CLI existente. `bench.py` conserva a preparação, auditoria, verificação antes de cada trial, controle de OAuth, execução, aprovação e relatórios. O runner consulta o resultado da fase mesmo quando o subprocesso retorna zero. A imagem Docker é selecionada pelo SHA256 da triagem original, sem nova construção ou resolução por tag mutável.

São 20 segundos e duas chamadas na prova de interrupção; smoke e comparação conservam 1200 segundos e 60 chamadas por sessão. A tolerância continua sendo 15 segundos. Não existem flags para mudar candidatos, repetições ou limites.

## Decisão de síntese

A alternativa B, pacote independente sobre o CLI congelado, é a base. Ela evita copiar o loop de execução e os controles de sessão para outro runner. A revisão pontuou B com 9/10 e A com 8/10 nos critérios registrados em `validation/money-extra-models-work.md`.

Da alternativa A, incorporamos a coorte fixa e testes de igualdade integral da tarefa. O cache atual é idêntico ao catálogo anterior, portanto as três fases podem conservar o catálogo congelado. A composição por importação de funções do runner anterior foi rejeitada porque exigiria outro loop de fases e coordenação de módulos globais.

Model the Domain orienta o uso da tupla de `Candidate` já existente. Laziness Protocol orienta o reuso do CLI completo, sem outro controlador de trials. Prove It Works exige validar a CLI e a tarefa real antes de apresentar o comando.

## Riscos e verificação

Uma nova cópia de fontes recebe hashes novos, com as diferenças registradas. Não será descrita como núcleo integralmente idêntico: a coorte e o inventário mudam, enquanto runtime, controlador, isolamento e grader permanecem iguais.

Os testes devem verificar a agenda 3/3/9, tarefa integralmente igual, contrato e fontes adulterados bloqueados, rejeição de gates antigos, parada após gates reprovados ou fase incompleta e preservação dos artefatos históricos. A validação real de baseline e referência continua sem chamadas de modelo.

A descoberta nativa das variantes será confirmada no preflight do binário OpenCode 2.0.26. A leitura estática do checkout 2.0.22 não substitui essa confirmação. Fast enviado como priority permanece separado do metadado retornado.

Os desenhos e a revisão usaram o modelo herdado da família GPT disponível. Os modelos de outras famílias indicados nas skills não estavam disponíveis nesta sessão.
