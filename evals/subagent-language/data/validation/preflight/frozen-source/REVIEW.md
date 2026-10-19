# Revisão humana do piloto

## Qualidade da entrega

Entregue ao revisor apenas a pasta `blind-review/`. Mantenha `blind-key.json`,
condições, métricas e traces fora dessa revisão. A pasta contém amostras em ordem
embaralhada, resposta estruturada, relatório e referência com fontes e gabarito.
As repetições do mesmo caso continuam identificáveis pelo conteúdo; o cegamento
oculta a condição, não a tarefa. Um texto que revele a condição deve ser anotado.

Preencha `ratings.json`, sem consultar custo ou tempo, usando booleanos:

- `portuguese`: a prosa dirigida ao usuário está em português, admitindo nomes,
  identificadores e citações originais.
- `factual_explanation`: a explicação concorda com as fontes e os cálculos; uma
  resposta JSON correta com justificativa errada recebe `false`.
- `complete`: atende todos os elementos da rubrica específica em `reference.json`.
- `unsupported_claims`: afirma como fato algo sem suporte nas fontes. Deve ser
  `false` para aprovação; inferências explicitamente qualificadas são aceitáveis.
- `notes`: justifique reprovações e eventual quebra do cegamento.

Uma entrega aprovada precisa passar no corretor automático, nos três critérios
positivos e não apresentar afirmações sem suporte. Não compensar perda de qualidade
com menos tokens. Não premiar concisão por si só nem exigir o mesmo número de palavras
entre condições. Dúvidas de gabarito devem ser resolvidas antes de abrir a chave.

## Idioma nas mensagens

Esta revisão é separada porque a instrução de idioma pode aparecer no próprio
texto. Em cada `trial-*/language-review.json`, preencha `language` com `pt`, `en`,
`mixed` ou `nonlinguistic`. Avalie a prosa autoral, excluindo citações, IDs, código
e nomes de ferramentas. Instruir em português "responda em inglês" dentro de uma
delegação em português não torna aquela delegação inglesa.

Registre a proporção de mensagens em cada idioma por execução, separando pedidos
e retornos. Uma execução segue integralmente a política quando todas as mensagens
com conteúdo linguístico usam o idioma solicitado. `default` não tem idioma exigido.
Mensagens não linguísticas saem do denominador. O comprimento em caracteres fica
disponível nos textos, mas não representa tokens e não deve ser apresentado como tal.

O relatório automático não incorpora estes rótulos nem altera o veredito após
edição dos JSONs. A análise humana final deve cruzar as notas com `blind-key.json`
e `summary.json`, citar discordâncias e apresentar denominadores. O executor já
mantém os dados necessários para essa revisão; não há juiz LLM nem custo oculto de avaliação.
