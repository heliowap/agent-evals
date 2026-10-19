# Fechamento de 10 de outubro
Incluir pedidos BRL pagos cujo instante de pagamento esteja em [2026-10-10T00:00:00Z,
2026-10-11T00:00:00Z). Datas já estão em UTC. Não usar a criação do pedido para
decidir a janela. O arquivo contém eventos repetidos por retry: deduplicar pelo
event_id antes de calcular qualquer valor. IDs diferentes representam eventos distintos.

Subtrair de cada pedido incluído os estornos confirmados ocorridos estritamente
antes de 2026-10-11T00:00:00Z, inclusive parciais. Estornos pendentes não entram.
Estorno no limite superior fica para o próximo fechamento. Pedido integralmente
estornado permanece na lista de incluídos, com líquido zero. Um estorno de pedido
fora da janela não entra neste relatório. Não converter outras moedas. Valores
são inteiros em centavos. Use o canal do pagamento; não some o valor de criação.
O relatório é por coorte de pagamentos, não um fluxo de caixa de todos os eventos do dia.
