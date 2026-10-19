# Histórico e hipóteses
Às 13:40 houve uma alteração visual no painel, sem mudança de agregação.
Às 14:05 o consumidor recibos passou da versão 7 para a 8. A versão 8 passou
a exigir customer_id, enquanto o contrato vigente do produtor publica cliente_id.
Não houve migração coordenada do produtor. Às 14:16 uma instância de recibos
foi revertida para a versão 7: dez mensagens de teste com o formato vigente
foram aceitas, usando o mesmo banco e a mesma rede. As outras instâncias ainda
estão na versão 8. O consumidor notificacoes não foi atualizado.

O catálogo de hipóteses é: C1 = esgotamento de conexões do banco; C2 = quebra
de compatibilidade no consumidor recibos; C3 = indisponibilidade de DNS em produção.
Uma reversão do produtor exigiria coordenar clientes que continuam operando
normalmente. O procedimento operacional permite reverter recibos para 7 e
validar uma amostra antes de reprocessar as filas efetivamente afetadas.
Não classifique retenção temporária como perda definitiva. Ausência de
evidência de perda não é garantia de recuperação integral sem validação.
