"""Métricas operacionais e de IA para o dashboard."""

from collections import Counter, defaultdict
from datetime import timedelta
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import CHANNELS, Agent, Conversation, Message
from app.services.nlu import INTENT_LABELS, sentiment_label
from app.utils import utcnow

MINUTES_SAVED_PER_AI_RESOLUTION = 7.5   # tempo médio de um atendimento humano equivalente
COST_PER_HUMAN_CONVERSATION = 4.80      # R$ — custo operacional médio por atendimento humano


def _pct(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def _delta(curr: float, prev: float) -> float | None:
    if not prev:
        return None
    return round(100 * (curr - prev) / prev, 1)


def overview(db: Session, days: int = 30) -> dict:
    now = utcnow()
    start = now - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    convs = db.scalars(
        select(Conversation).where(Conversation.created_at >= prev_start).options(selectinload(Conversation.agent))
    ).all()
    current = [c for c in convs if c.created_at >= start]
    previous = [c for c in convs if c.created_at < start]

    def kpis(items: list[Conversation]) -> dict:
        resolved = [c for c in items if c.status == "resolved"]
        by_ai = [c for c in resolved if c.resolved_by == "ai"]
        frt = [c.first_response_seconds for c in items if c.first_response_seconds is not None]
        csat = [c.csat for c in items if c.csat]
        handled = [(c.resolved_at - c.created_at).total_seconds() / 60 for c in resolved if c.resolved_at]
        return {
            "conversations": len(items),
            "resolved": len(resolved),
            "ai_resolved": len(by_ai),
            "ai_resolution_rate": _pct(len(by_ai), len(resolved)),
            "avg_first_response_s": round(mean(frt), 1) if frt else 0,
            "avg_resolution_min": round(mean(handled), 1) if handled else 0,
            "csat": round(mean(csat), 2) if csat else 0,
            "csat_responses": len(csat),
            "hours_saved": round(len(by_ai) * MINUTES_SAVED_PER_AI_RESOLUTION / 60, 1),
            "cost_saved": round(len(by_ai) * COST_PER_HUMAN_CONVERSATION, 2),
        }

    cur, prev = kpis(current), kpis(previous)
    deltas = {k: _delta(cur[k], prev[k]) for k in cur if isinstance(cur[k], int | float)}

    # volume diário por canal
    daily: dict[str, dict] = {}
    for i in range(days):
        d = (start + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        daily[d] = {"date": d, **{ch: 0 for ch in CHANNELS}, "ai": 0, "human": 0}
    for c in current:
        d = c.created_at.strftime("%Y-%m-%d")
        if d in daily:
            daily[d][c.channel] += 1
            if c.resolved_by in ("ai", "human"):
                daily[d][c.resolved_by] += 1

    channels = Counter(c.channel for c in current)
    intents = Counter(c.intent or "outro" for c in current)
    sentiments = Counter(sentiment_label(c.sentiment) for c in current)
    handoffs = Counter(c.handoff_reason for c in current if c.handoff_reason)

    # mapa de calor (dia da semana × hora) em horário de Brasília (UTC-3)
    heat = defaultdict(int)
    for c in current:
        local = c.created_at - timedelta(hours=3)
        heat[(local.weekday(), local.hour)] += 1

    # performance do time humano
    team = []
    for agent in db.scalars(select(Agent)).all():
        mine = [c for c in current if c.assigned_agent_id == agent.id]
        done = [c for c in mine if c.status == "resolved"]
        scores = [c.csat for c in mine if c.csat]
        team.append({
            "id": agent.id, "name": agent.name, "status": agent.status, "avatar_color": agent.avatar_color,
            "conversations": len(mine), "resolved": len(done),
            "open": sum(c.status == "human" for c in convs if c.assigned_agent_id == agent.id),
            "csat": round(mean(scores), 2) if scores else None,
        })
    team.sort(key=lambda a: a["conversations"], reverse=True)

    live = Counter(c.status for c in db.scalars(select(Conversation).where(Conversation.status != "resolved")))
    ai_msgs = db.scalars(
        select(Message.meta).where(Message.sender == "bot", Message.created_at >= now - timedelta(days=7))
    ).all()
    latencies = [m.get("latency_ms") for m in ai_msgs if m and m.get("latency_ms")]

    return {
        "period_days": days,
        "kpis": cur,
        "deltas": deltas,
        "daily": list(daily.values()),
        "channels": [{"channel": ch, "count": channels.get(ch, 0)} for ch in CHANNELS],
        "intents": [{"intent": k, "label": INTENT_LABELS.get(k, k), "count": v}
                    for k, v in intents.most_common(8)],
        "sentiment": [{"label": k, "count": sentiments.get(k, 0)} for k in ("positivo", "neutro", "negativo")],
        "handoff_reasons": [{"reason": k, "count": v} for k, v in handoffs.most_common(6)],
        "heatmap": [{"weekday": d, "hour": h, "count": heat.get((d, h), 0)} for d in range(7) for h in range(24)],
        "team": team,
        "live": {"bot": live.get("bot", 0), "waiting": live.get("waiting", 0), "human": live.get("human", 0)},
        "ai_latency_ms": round(mean(latencies)) if latencies else None,
    }
