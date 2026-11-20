from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.services.nlu import NLUResult
from app.services.tools import ToolCall, ToolContext


@dataclass
class AgentInput:
    ctx: ToolContext
    message: str
    history: list[dict]  # [{"role": "user"|"assistant", "content": str}], sem a mensagem atual
    nlu: NLUResult
    settings: dict
    system_prompt: str
    previous_intent: str | None = None


@dataclass
class AgentOutput:
    text: str
    provider: str
    model: str
    confidence: float = 0.9
    tool_calls: list[ToolCall] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    resolved_hint: bool = False  # IA entende que o assunto foi encerrado

    @property
    def handoff(self) -> dict | None:
        for call in self.tool_calls:
            if call.name == "transferir_para_humano" and call.result:
                return call.result
        return None


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def respond(self, data: AgentInput) -> AgentOutput:
        """Gera a resposta do agente, podendo chamar ferramentas."""

    @abstractmethod
    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Completação simples (resumos, sugestões do copiloto)."""
