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
    *(Candidate(f"sonnet-{effort}", "cli_proxy", "cpa-claude-sonnet-5-5", effort, "cli_proxy",
                "http://127.0.0.1:8317/v1", effort, False, "claude-sonnet-5-5", "messages", "key")
      for effort in ("medium", "high")),
    *(Candidate(f"sol-fast-{effort}", "openai", "gpt-6.1-sol-fast", effort, "openai",
                "https://chatgpt.com/backend-api/codex", effort, True, "gpt-6.1-sol", "responses", "oauth")
      for effort in ("medium", "high")),
    Candidate("opus-medium", "cli_proxy", "cpa-claude-opus-5-5", "medium", "cli_proxy",
              "http://127.0.0.1:8317/v1", "medium", False, "claude-opus-5-5", "messages", "key"),
    Candidate("deepseek-max", "opencode-go", "deepseek-v4.1-flash", "max", "opencode-go",
              "https://opencode.ai/zen/go/v1", "max", False, "deepseek-v4.1-flash", "chat", "key"),
)
