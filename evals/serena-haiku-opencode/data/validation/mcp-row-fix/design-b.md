# Design B: recibo tipado, persistência no bench

O bench fornece um checkpoint que grava em `out/discovery/<configuration>-<role>/receipt.json` e atualiza o progresso de `preflight.json`.

```python
try:
	receipt = runtime.audit(..., checkpoint=record)
except DiscoveryError as exc:
	receipt = exc.receipt
```

Sketch, sem implementação:

```python
@dataclass(frozen=True)
class DiscoveryReceipt:
	configuration: str
	role: str
	case: str
	phase: str
	sources: tuple[SafeSource, ...]
	configuration_mcp: SafeMCPConfig | None
	attempts: tuple[MCPObservation, ...]
	surface: tuple[SafeSurface, ...]
	model_inference_calls: int | None
	error: str | None  # código fechado

class DiscoveryError(ValueError):
	receipt: DiscoveryReceipt

def audit(..., checkpoint: Callable[[DiscoveryReceipt], None]) -> DiscoveryReceipt:
	# not implemented
```

O runtime conhece o protocolo e produz snapshots imutáveis. Cada resposta, inclusive malformada, entra no recibo antes da validação. O checkpoint persiste esses snapshots fora de temp. Falhas acrescentam fase e código seguro, fazem checkpoint e lançam `DiscoveryError(receipt)` antes do cleanup. O bench mantém descobertas anteriores desde o início do estágio.

`MCPObservation` preserva tentativa, tempo, formato do envelope, cardinalidade, nome conhecido ou classificação inesperada, tipo do status, estado reconhecido e presença de integrationID. Projeções explícitas excluem auth, environment, comandos desconhecidos, campos extras e erro bruto. Configuração efetiva conserva somente fontes e campos MCP seguros. Nenhum raw ausente é reconstruído.

O documento usa `mcp.servers.serena`, com campos nativos. Serena vazio ou pending espera até o prazo. Somente uma entrada válida connected e catálogo direto exato aprova. Formato inválido, nomes extras, duplicatas e estados terminais bloqueiam. Nativo exige catálogo nativo exato e ausência de MCP.

B evita cópia tardia e recibo perdido em temp, mas acrescenta um callback. A é menor se sua cópia em finally garantir persistência anterior ao cleanup; B é preferível para progresso durável durante a descoberta. Nenhum store ou módulo é necessário.

Verificar vazio/pending/connected, vazio até timeout, linha nomeada malformada e recibo em falha. Preservar 32 testes Python, sete Node, casos, 120 trials, medium/high, limites e freeze.
