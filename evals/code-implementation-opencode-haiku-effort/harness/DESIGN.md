# Haiku 5.5 em todos os níveis de esforço

Execute da pasta `evals` depois da validação do pacote:

```sh
python3 -B implementacao/opencode-implementador/rounds/haiku-5-5/run.py run \
  --out implementacao/opencode-implementador/results/haiku-5-5
```

O comando realiza novos gates de budget e smoke antes da triagem completa. São cinco configurações, `low`, `medium`, `high`, `xhigh` e `max`, na rota `cli_proxy/cpa-claude-haiku-5-5`, com modelo enviado `claude-haiku-5-5`. Cada esforço recebe os 12 casos e três repetições. O total é 180 trials comparativos e dez sessões de gates, 190 sessões.

## Fontes e controles

O pacote deriva dos 18 arquivos congelados na triagem original. Copia o wrapper de fases já verificado, sem criar outro loop de execução. Somente os candidatos em `domain.py`, a seleção de tarefas em `tasks.py` e a declaração privada de variantes em `runtime.configuration()` mudam. `contract.py` conserva o contrato monetário explícito da rodada concluída. Onze TaskSpecs são integralmente iguais à triagem original; o Python monetário é integralmente igual ao TaskSpec corrigido.

Controller, grader, observer, terminal, isolamento, dependências, imagem por SHA, catálogo, seed e demais fontes ficam equivalentes ao baseline. Cada trial mantém 1.200 segundos, 60 chamadas e 15 segundos de graça. O limite global continua em seis horas por fase. A cópia recebe seus próprios hashes e gates; não reutiliza provas de outras configurações.

O catálogo congelado ainda não contém Haiku 5.5. A configuração global do usuário já declara o alias e cinco variantes, e o registro local do CLIProxy contém o modelo com os mesmos cinco esforços. A nova configuração privada declara essas variantes explicitamente, sem importar configurações, plugins, MCPs ou skills globais. Mantém os limites do experimento de 272.000 tokens de contexto e 32.768 de saída.

O audit nativo confere provider, alias, modelo enviado e esforço selecionado. O verificador existente de chamadas já exige modelo, esforço, rota, sessão e `thinking_type == adaptive`. Essas funções ficam intactas. Gates com qualquer variante indisponível ou sem prova de interrupção/aprovação bloqueiam a triagem.

## Desenhos comparados

O desenho A copia o CLI congelado e adapta os dados da coorte e da seleção. O desenho B passa candidatos e TaskSpecs diretamente às funções do core, acrescentando um loop explícito. A recebeu 10/10 e B recebeu 8/10 nos critérios de preservação de tarefas, controles, prova nativa, proveniência e simplicidade. A mantém um único loop já verificado. Incorporamos de B a exigência de congelar wrapper e proveniência externamente e de corrigir os rótulos dos relatórios derivados para cinco configurações.

Esboços: `/private/tmp/haiku55-design-a.md` e `/private/tmp/haiku55-design-b.md`. O cross-judge foi GPT-5.6 Sol, da mesma família disponível nesta sessão.

## Verificação

Plano real com agendas 5/5/180, validação dos 12 projetos e referências, declaração das cinco variantes, igualdade dos TaskSpecs, hashes das fontes e orçamento, interrupção após gates reprovados, agendas e relatórios finais em falhas. O código de `runtime.py` fora de `configuration()` precisa continuar equivalente ao baseline, e a mudança dentro dela precisa ser somente o registro das variantes. A origem permanece somente leitura.

As ressalvas já identificadas nos contratos de perfil e envelope de importação permanecem documentadas. Não alteramos esses enunciados nesta rodada. O resultado funcional conserva a aceitação nominal e distingue falha operacional, tempo excedido e reprovação do patch. Não inferimos ausência geral de bugs ou brechas de segurança a partir desse conjunto pequeno.
