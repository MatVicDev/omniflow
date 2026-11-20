"""Modelo de dados do OmniFlow.

Atendimento: Contact → Conversation → Message (com trace da IA em `meta`).
Operação:    Agent (time humano), Ticket (solicitações abertas pela IA ou pelo time).
IA:          KnowledgeArticle (base de conhecimento / RAG), Flow (automações), Setting.
Negócio:     Product e Order — dados do e-commerce que as ferramentas da IA consultam.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.utils import utcnow

CHANNELS = ("whatsapp", "instagram", "webchat", "email")
CONVERSATION_STATUSES = ("bot", "waiting", "human", "resolved")
PRIORITIES = ("low", "normal", "high", "urgent")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    role: Mapped[str] = mapped_column(String(40), default="agent")  # agent | supervisor
    team: Mapped[str] = mapped_column(String(60), default="Atendimento")
    status: Mapped[str] = mapped_column(String(20), default="online")  # online | away | offline
    avatar_color: Mapped[str] = mapped_column(String(20), default="#6366f1")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(160), index=True)
    instagram: Mapped[str | None] = mapped_column(String(80), index=True)
    city: Mapped[str | None] = mapped_column(String(80))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    lifetime_value: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="contact")
    orders: Mapped[list["Order"]] = relationship(back_populates="contact", order_by="Order.created_at.desc()")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="bot", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    intent: Mapped[str | None] = mapped_column(String(40))
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)  # -1 (negativo) … 1 (positivo)
    summary: Mapped[str | None] = mapped_column(Text)
    handoff_reason: Mapped[str | None] = mapped_column(String(200))
    ai_failures: Mapped[int] = mapped_column(Integer, default=0)
    resolved_by: Mapped[str | None] = mapped_column(String(10))  # ai | human
    csat: Mapped[int | None] = mapped_column(Integer)
    unread: Mapped[int] = mapped_column(Integer, default=0)
    first_response_seconds: Mapped[float | None] = mapped_column(Float)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    contact: Mapped[Contact] = relationship(back_populates="conversations")
    agent: Mapped[Agent | None] = relationship()
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.id", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender: Mapped[str] = mapped_column(String(20))  # contact | bot | agent | system
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # trace da IA, anexos, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    agent: Mapped[Agent | None] = relationship()


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    protocol: Mapped[str] = mapped_column(String(20), unique=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"))
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    kind: Mapped[str] = mapped_column(String(30))  # troca | devolucao | reclamacao | financeiro | outro
    description: Mapped[str] = mapped_column(Text)
    order_code: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="aberto")
    created_by: Mapped[str] = mapped_column(String(10), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    contact: Mapped[Contact] = relationship()
    conversation: Mapped[Conversation | None] = relationship()


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(60))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    hits: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Flow(Base):
    __tablename__ = "flows"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    trigger: Mapped[dict] = mapped_column(JSON)
    nodes: Mapped[list] = mapped_column(JSON)
    edges: Mapped[list] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    runs: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(60))
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))  # pago | separacao | enviado | entregue | cancelado
    total: Mapped[float] = mapped_column(Float)
    items: Mapped[list] = mapped_column(JSON)
    payment_method: Mapped[str] = mapped_column(String(20))
    carrier: Mapped[str | None] = mapped_column(String(40))
    tracking_code: Mapped[str | None] = mapped_column(String(40))
    eta: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    contact: Mapped[Contact] = relationship(back_populates="orders")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
