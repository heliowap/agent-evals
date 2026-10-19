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
    Candidate("sol-fast-low", "openai", "gpt-6.1-sol-fast", "low", "openai",
              "https://chatgpt.com/backend-api/codex", "low", True, "gpt-6.1-sol", "responses", "oauth"),
    *(Candidate(f"glm-flash-{effort}", "opencode-go", "glm-5.3-flash", effort, "opencode-go",
                "https://opencode.ai/zen/go/v1", effort, False, "glm-5.3-flash", "chat", "key")
      for effort in ("high", "max")),
)
