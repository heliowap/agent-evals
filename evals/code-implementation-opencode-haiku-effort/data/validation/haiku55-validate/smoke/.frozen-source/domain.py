from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSpec:
    id: str
    phase: str
    family: str
    language: str
    request: str
    files: dict[str, str]
    reference: dict[str, str]
    acceptance: str
    allowed: tuple[str, ...]
    structural: str | None = None


@dataclass(frozen=True)
class Candidate:
    id: str
    provider: str
    model: str
    variant: str
    credential_provider: str
    upstream: str
    effort: str
    fast: bool
    wire_model: str
    protocol: str
    auth_type: str

    @property
    def selection(self):
        return f"{self.provider}/{self.model}#{self.variant}"

    @property
    def identity(self):
        return {"providerID": self.provider, "id": self.model, "variant": self.variant}


@dataclass(frozen=True)
class Budget:
    seconds: int = 1200
    calls: int = 60
    grace: int = 15


CANDIDATES = (
    *(Candidate(f"haiku-{effort}", "cli_proxy", "cpa-claude-haiku-5-5", effort, "cli_proxy",
                "http://127.0.0.1:8317/v1", effort, False, "claude-haiku-5-5", "messages", "key")
      for effort in ("low", "medium", "high", "xhigh", "max")),
)
