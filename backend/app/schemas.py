"""Contratos de entrada da API (validação com Pydantic)."""

from typing import Literal

from pydantic import BaseModel, Field

Channel = Literal["whatsapp", "instagram", "webchat", "email"]


class InboundMessage(BaseModel):
    """Mensagem recebida de um canal (usado pelo simulador e por integrações)."""

    text: str = Field(min_length=1, max_length=4000)
    contact_id: int | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None


class AgentMessage(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    agent_id: int


class AssignBody(BaseModel):
    agent_id: int


class ArticleIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    category: str = Field(min_length=2, max_length=60)
    content: str = Field(min_length=10)
    tags: list[str] = []
    active: bool = True


class SearchQuery(BaseModel):
    query: str = Field(min_length=2, max_length=500)


class FlowToggle(BaseModel):
    active: bool


class AgentSettingsPatch(BaseModel):
    bot_name: str | None = Field(default=None, max_length=40)
    tone: Literal["amigavel", "profissional", "descontraido"] | None = None
    greeting: str | None = Field(default=None, max_length=400)
    custom_instructions: str | None = Field(default=None, max_length=2000)
    handoff_sentiment_threshold: float | None = Field(default=None, ge=-1, le=0)
    handoff_after_failures: int | None = Field(default=None, ge=1, le=5)
    auto_resolve_on_thanks: bool | None = None
    csat_enabled: bool | None = None
    business_hours: dict | None = None
