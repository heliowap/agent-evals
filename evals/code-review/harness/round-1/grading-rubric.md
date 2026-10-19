# Gabarito pré-definido para o teste de revisão

Os quatro achados abaixo foram fixados antes de ler as respostas. Cada caso tem um achado de **Spec** e um de **Standards**; a pontuação não mistura os eixos. A pesquisa e as fontes primárias estão em `fixture-research.md`; os prompts cegos estão em `fixtures.json` e nos arquivos de `results/`.

| Caso | Eixo | Achado verificável (1 ponto) |
| --- | --- | --- |
| [Click #3773](https://github.com/pallets/click/pull/3773) | Spec | `break_on_hyphens = False` foi adicionado como atributo da classe, mas `textwrap.TextWrapper.__init__` cria o atributo **da instância** com o padrão `True`; o exemplo do [issue #3362](https://github.com/pallets/click/issues/3362) continua quebrando `--max-retry-count` e `--config-file-location`. |
| Click #3773 | Standards | O diff não acrescenta teste de regressão que falhe sem a mudança, contrariando a [.github/pull_request_template.md](https://github.com/pallets/click/blob/20fff386596bc1a3d92e3b5c47c81e3f17083da6/.github/pull_request_template.md#L18-L21). |
| [Click #3868](https://github.com/pallets/click/pull/3868) | Spec | A promessa da PR de respeitar aspas na linha de comando do editor não se cumpre para aspas **internas** a um argumento: com `WIN=True`, `C:\tools\vim.exe --arg="a b"` produz três tokens, `['C:\\tools\\vim.exe', '--arg="a', 'b"']`, e não dois. Não inferir daqui que a falha original de `notepad` continua nem que o lançamento real foi testado no Windows. |
| Click #3868 | Standards | O `t[1:-1] if ... else t` adicionado a `_termui_impl.py` contraria a proibição expressa de expressões ternárias em [docs/contributing.md](https://github.com/pallets/click/blob/425104296015c9ffb63fbbe4d9db12d3ae0ef12a/docs/contributing.md#L33-L38). |

## Pontuação e cautelas

- Contar um acerto somente se a resposta identificar a **causa concreta**, no eixo certo, com a localização afetada; comentário genérico sobre testes, aspas ou `textwrap` não basta. Cada eixo/caso vale 0 ou 1.
- Contar separadamente alegações verificavelmente incorretas como falsos positivos: por exemplo, dizer que #3773 alterou todo o wrap de textos (a configuração adicionada não tem efeito) ou que #3868 comprovou uma falha do `CreateProcess` no Windows (a reprodução cobre apenas parsing). Não marcar automaticamente outros achados plausíveis como falsos positivos: primeiro adjudicar a evidência.
- Registrar omissões, achados fora do eixo, falhas de chamada, custo em USD informado pelo provedor e duração observada. `high` e `max` medem duas configurações de cada modelo, não duas repetições independentes. Dois diffs de um único projeto não justificam generalização estatística.
- Sem variante de esforço anunciada para `opencode/mimo-v2.6-flash-free`; ele entra apenas na configuração padrão. `opencode/space-bunny-free` entra em `xhigh` e `max`, sem atribuir identidade definitiva ao modelo stealth.
