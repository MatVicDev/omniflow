from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Agent, Contact, Conversation, Message, Ticket
from app.realtime import hub
from app.schemas import AgentMessage, AssignBody
from app.serializers import contact_out, conversation_out, message_out, order_out, ticket_out
from app.services import agent as orchestrator
from app.services import copilot

router = APIRouter(prefix="/api/conversations", tags=["Conversas"])

_PRIORITY_ORDER = {"urgent": 0, "high": 1, "normal": 2, "low": 3}


def _get(db: Session, conv_id: int) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Conversa não encontrada")
    return conv


def _agent(db: Session, agent_id: int) -> Agent:
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Atendente não encontrado")
    return agent


@router.get("")
def list_conversations(
    status: str | None = Query(None, description="bot | waiting | human | resolved | open"),
    channel: str | None = None,
    q: str | None = None,
    assigned_to: int | None = None,
    limit: int = Query(60, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Conversation).join(Contact).options(
        selectinload(Conversation.contact), selectinload(Conversation.agent)
    )
    if status == "open":
        stmt = stmt.where(Conversation.status != "resolved")
    elif status:
        stmt = stmt.where(Conversation.status == status)
    if channel:
        stmt = stmt.where(Conversation.channel == channel)
    if assigned_to:
        stmt = stmt.where(Conversation.assigned_agent_id == assigned_to)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Contact.name).like(like), func.lower(Contact.email).like(like),
                              Contact.phone.like(like)))
    convs = db.scalars(stmt.order_by(Conversation.updated_at.desc()).limit(limit)).all()

    # última mensagem de cada conversa numa única consulta
    ids = [c.id for c in convs]
    last_ids = db.execute(
        select(func.max(Message.id)).where(Message.conversation_id.in_(ids)).group_by(Message.conversation_id)
    ).scalars().all() if ids else []
    last = {m.conversation_id: m for m in db.scalars(select(Message).where(Message.id.in_(last_ids)))}

    counts = dict(db.execute(select(Conversation.status, func.count()).group_by(Conversation.status)).all())
    return {
        "items": [conversation_out(c, last.get(c.id)) for c in convs],
        "counts": {
            "bot": counts.get("bot", 0), "waiting": counts.get("waiting", 0), "human": counts.get("human", 0),
            "resolved": counts.get("resolved", 0),
        },
    }


@router.get("/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    contact = conv.contact
    history = db.scalars(
        select(Conversation).where(Conversation.contact_id == contact.id, Conversation.id != conv.id)
        .order_by(Conversation.created_at.desc()).limit(5)
    ).all()
    tickets = db.scalars(select(Ticket).where(Ticket.contact_id == contact.id).order_by(Ticket.id.desc())).all()
    return {
        "conversation": conversation_out(conv),
        "messages": [message_out(m) for m in conv.messages],
        "contact": contact_out(contact),
        "orders": [order_out(o) for o in contact.orders[:5]],
        "tickets": [ticket_out(t) for t in tickets[:5]],
        "previous_conversations": [
            {"id": c.id, "channel": c.channel, "status": c.status, "intent": c.intent,
             "created_at": c.created_at, "csat": c.csat} for c in history
        ],
    }


@router.post("/{conv_id}/messages")
async def send_agent_message(conv_id: int, body: AgentMessage, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    if conv.status == "resolved":
        raise HTTPException(409, "Conversa encerrada")
    msg = await orchestrator.agent_send(db, conv, _agent(db, body.agent_id), body.content)
    return message_out(msg)


@router.post("/{conv_id}/assign")
async def assign(conv_id: int, body: AssignBody, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    await orchestrator.agent_assign(db, conv, _agent(db, body.agent_id))
    return conversation_out(conv)


@router.post("/{conv_id}/resolve")
async def resolve(conv_id: int, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    if conv.status == "resolved":
        raise HTTPException(409, "Conversa já encerrada")
    await orchestrator.agent_resolve(db, conv)
    return conversation_out(conv)


@router.post("/{conv_id}/return-to-bot")
async def return_to_bot(conv_id: int, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    await orchestrator.return_to_bot(db, conv)
    return conversation_out(conv)


@router.post("/{conv_id}/read")
async def mark_read(conv_id: int, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    if conv.unread:
        conv.unread = 0
        db.commit()
        await hub.publish("conversation.updated", conversation_out(conv))
    return {"ok": True}


@router.post("/{conv_id}/copilot/suggest")
async def copilot_suggest(conv_id: int, db: Session = Depends(get_db)):
    return await copilot.suggest_reply(db, _get(db, conv_id))


@router.post("/{conv_id}/copilot/summarize")
async def copilot_summarize(conv_id: int, db: Session = Depends(get_db)):
    conv = _get(db, conv_id)
    conv.summary = await copilot.summarize(conv)
    db.commit()
    await hub.publish("conversation.updated", conversation_out(conv))
    return {"summary": conv.summary}
