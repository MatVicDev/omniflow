"""Rotas de workspace: analytics, fluxos, configurações, time, contatos, tickets e demo."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models import Agent, Contact, Flow, Ticket
from app.realtime import hub
from app.schemas import AgentSettingsPatch, FlowToggle
from app.serializers import agent_out, contact_out, ticket_out
from app.services.ai.factory import get_provider
from app.services.analytics import overview
from app.services.settings_store import get_agent_settings, update_agent_settings
from app.utils import utcnow

router = APIRouter(prefix="/api", tags=["Workspace"])


@router.get("/analytics/overview")
def analytics_overview(days: int = Query(30, ge=7, le=90), db: Session = Depends(get_db)):
    return overview(db, days)


@router.get("/flows")
def list_flows(db: Session = Depends(get_db)):
    return [
        {"id": f.id, "key": f.key, "name": f.name, "description": f.description, "trigger": f.trigger,
         "nodes": f.nodes, "edges": f.edges, "active": f.active, "runs": f.runs, "updated_at": f.updated_at}
        for f in db.scalars(select(Flow).order_by(Flow.id)).all()
    ]


@router.patch("/flows/{flow_id}")
def toggle_flow(flow_id: int, body: FlowToggle, db: Session = Depends(get_db)):
    flow = db.get(Flow, flow_id)
    if not flow:
        raise HTTPException(404, "Fluxo não encontrado")
    flow.active = body.active
    flow.updated_at = utcnow()
    db.commit()
    return {"id": flow.id, "active": flow.active}


@router.get("/settings")
def read_settings(db: Session = Depends(get_db)):
    s = get_settings()
    provider = get_provider()
    return {
        "agent": get_agent_settings(db),
        "engine": {
            "provider": provider.name,
            "model": provider.model,
            "anthropic_configured": bool(s.anthropic_api_key),
            "openai_configured": bool(s.openai_api_key),
            "whatsapp_configured": bool(s.whatsapp_token and s.whatsapp_phone_number_id),
        },
    }


@router.patch("/settings")
def patch_settings(body: AgentSettingsPatch, db: Session = Depends(get_db)):
    return {"agent": update_agent_settings(db, body.model_dump(exclude_none=True))}


@router.get("/agents")
def list_agents(db: Session = Depends(get_db)):
    return [agent_out(a) for a in db.scalars(select(Agent).order_by(Agent.id)).all()]


@router.get("/contacts")
def list_contacts(q: str | None = None, limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    stmt = select(Contact)
    if q:
        stmt = stmt.where(Contact.name.ilike(f"%{q}%"))
    return [contact_out(c) for c in db.scalars(stmt.order_by(Contact.name).limit(limit)).all()]


@router.get("/tickets")
def list_tickets(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    return [ticket_out(t) for t in db.scalars(select(Ticket).order_by(Ticket.id.desc()).limit(limit)).all()]


@router.get("/demo/personas", summary="Personas do simulador de canais")
def demo_personas(db: Session = Depends(get_db)):
    from app.seed import PERSONAS
    from app.seed_data import DEMO_PERSONAS

    by_name = {c.name: c for c in db.scalars(select(Contact)).all()}
    out = []
    for p in DEMO_PERSONAS:
        contact = by_name.get(PERSONAS[p["key"]]["name"]) if p["key"] in PERSONAS else None
        out.append({**p, "contact": contact_out(contact) if contact else None})
    return out


@router.post("/demo/reset", summary="Restaura os dados de demonstração")
async def demo_reset():
    from app.seed import reset_database

    await reset_database()
    await hub.publish("demo.reset", {})
    return {"ok": True}
