"""Conversão de modelos para JSON da API (formato consumido pelo frontend)."""

from app.models import Agent, Contact, Conversation, KnowledgeArticle, Message, Order, Ticket
from app.services.nlu import INTENT_LABELS
from app.services.tools import ORDER_STATUS_LABEL


def agent_out(a: Agent | None) -> dict | None:
    if not a:
        return None
    return {"id": a.id, "name": a.name, "email": a.email, "role": a.role, "team": a.team,
            "status": a.status, "avatar_color": a.avatar_color}


def contact_out(c: Contact) -> dict:
    return {"id": c.id, "name": c.name, "phone": c.phone, "email": c.email, "instagram": c.instagram,
            "city": c.city, "tags": c.tags or [], "lifetime_value": c.lifetime_value, "created_at": c.created_at}


def message_out(m: Message) -> dict:
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "sender": m.sender,
        "content": m.content,
        "agent": {"id": m.agent.id, "name": m.agent.name, "avatar_color": m.agent.avatar_color} if m.agent else None,
        "meta": m.meta or {},
        "created_at": m.created_at,
    }


def conversation_out(c: Conversation, last: Message | None = None) -> dict:
    last = last or (c.messages[-1] if c.messages else None)
    return {
        "id": c.id,
        "channel": c.channel,
        "status": c.status,
        "priority": c.priority,
        "intent": c.intent,
        "intent_label": INTENT_LABELS.get(c.intent or "", None),
        "sentiment": round(c.sentiment, 2),
        "summary": c.summary,
        "handoff_reason": c.handoff_reason,
        "resolved_by": c.resolved_by,
        "csat": c.csat,
        "unread": c.unread,
        "tags": c.tags or [],
        "first_response_seconds": c.first_response_seconds,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "resolved_at": c.resolved_at,
        "contact": contact_out(c.contact),
        "agent": agent_out(c.agent),
        "last_message": {"content": last.content[:140], "sender": last.sender, "created_at": last.created_at}
        if last else None,
    }


def order_out(o: Order) -> dict:
    return {"id": o.id, "code": o.code, "status": o.status, "status_label": ORDER_STATUS_LABEL.get(o.status),
            "total": o.total, "items": o.items, "payment_method": o.payment_method, "carrier": o.carrier,
            "tracking_code": o.tracking_code, "eta": o.eta, "created_at": o.created_at}


def ticket_out(t: Ticket) -> dict:
    return {"id": t.id, "protocol": t.protocol, "kind": t.kind, "description": t.description,
            "order_code": t.order_code, "status": t.status, "created_by": t.created_by,
            "conversation_id": t.conversation_id, "created_at": t.created_at,
            "contact": {"id": t.contact.id, "name": t.contact.name}}


def article_out(a: KnowledgeArticle) -> dict:
    return {"id": a.id, "title": a.title, "category": a.category, "content": a.content, "tags": a.tags or [],
            "active": a.active, "hits": a.hits, "updated_at": a.updated_at}
