"""Popula o banco com 60 dias de operação da Aurora Cosméticos.

- Histórico sintético (estatisticamente coerente) para o dashboard.
- Conversas "ao vivo" geradas pelo orquestrador real, com traces autênticos da IA.
"""

import random
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import (
    Agent,
    Contact,
    Conversation,
    Flow,
    KnowledgeArticle,
    Message,
    Order,
    Product,
    Ticket,
)
from app.seed_data import (
    AGENTS,
    CITIES,
    FIRST_NAMES,
    FLOWS,
    HISTORY_TEMPLATES,
    KNOWLEDGE,
    LAST_NAMES,
    LIVE_SCRIPTS,
    PRODUCTS,
)
from app.services.ai.offline import OfflineProvider
from app.services.nlu import analyze
from app.services.retrieval import knowledge_index
from app.utils import first_name, utcnow

DAYS = 60
CHANNEL_WEIGHTS = {"whatsapp": 0.52, "instagram": 0.2, "webchat": 0.18, "email": 0.1}
HOUR_WEIGHTS = [1, 0.5, 0.3, 0.2, 0.2, 0.4, 1, 2, 4, 6, 8, 8, 6, 6, 7, 7, 6, 6, 7, 9, 10, 9, 6, 3]

PERSONAS = {
    "juliana": dict(name="Juliana Martins", phone="5511987654321", email="juliana.martins@email.com",
                    city="São Paulo/SP", tags=["cliente-vip", "aurora-club"]),
    "rafael": dict(name="Rafael Costa", instagram="@rafa.costa", email="rafael.costa@email.com",
                   city="Rio de Janeiro/RJ", tags=["novo"]),
    "beatriz": dict(name="Beatriz Almeida", email="beatriz.almeida@email.com", city="Recife/PE", tags=[]),
    "patricia": dict(name="Patrícia Souza", phone="5521976543210", email="patricia.souza@email.com",
                     city="Niterói/RJ", tags=["recorrente"]),
    "lucas": dict(name="Lucas Ferreira", email="lucas.ferreira@email.com", city="Curitiba/PR", tags=[]),
    "camila": dict(name="Camila Rodrigues", phone="5531998877665", email="camila.r@email.com",
                   city="Belo Horizonte/MG", tags=["aurora-club"]),
    "thiago": dict(name="Thiago Gomes", phone="5571991234567", city="Salvador/BA", tags=["novo"]),
    "fernanda": dict(name="Fernanda Lima", email="fernanda.lima@email.com", phone="5541999001122",
                     city="Curitiba/PR", tags=["aurora-club"]),
    "marcos": dict(name="Marcos Oliveira", email="marcos.oliveira@email.com", city="Campinas/SP", tags=[]),
}


def _items(rng: random.Random, products: list[Product], n: int | None = None) -> tuple[list[dict], float]:
    chosen = rng.sample(products, n or rng.choice([1, 1, 2, 2, 3]))
    items = [{"sku": p.sku, "name": p.name, "qty": rng.choice([1, 1, 1, 2]), "price": p.price} for p in chosen]
    return items, round(sum(i["qty"] * i["price"] for i in items), 2)


def _order(code: int, contact: Contact, status: str, created_days_ago: float, rng: random.Random,
           products: list[Product], eta_days: float | None = None) -> Order:
    now = utcnow()
    items, total = _items(rng, products)
    carrier = rng.choice(["Correios", "Jadlog", "Loggi"]) if status in ("enviado", "entregue") else None
    created = now - timedelta(days=created_days_ago)
    return Order(
        code=f"AUR-{code}", contact=contact, status=status, total=total, items=items,
        payment_method=rng.choice(["pix", "pix", "cartão", "cartão", "boleto"]),
        carrier=carrier,
        tracking_code=f"{rng.choice(['QB', 'NX', 'LB'])}{rng.randint(100000000, 999999999)}BR" if carrier else None,
        eta=now + timedelta(days=eta_days) if eta_days is not None else created + timedelta(days=6),
        created_at=created,
    )


def seed_base(db: Session, rng: random.Random) -> None:
    for name, email, role, team, status, color in AGENTS:
        db.add(Agent(name=name, email=email, role=role, team=team, status=status, avatar_color=color))
    products = [Product(sku=s, name=n, category=c, price=p, stock=st, description=d)
                for s, n, c, p, st, d in PRODUCTS]
    db.add_all(products)
    for title, cat, tags, content in KNOWLEDGE:
        db.add(KnowledgeArticle(title=title, category=cat, tags=tags, content=content.strip(),
                                hits=rng.randint(20, 240), updated_at=utcnow() - timedelta(days=rng.randint(2, 40))))
    for f in FLOWS:
        db.add(Flow(**f, runs=rng.randint(80, 900)))
    db.flush()

    # personas da demo com pedidos sob medida
    p = {k: Contact(**v) for k, v in PERSONAS.items()}
    db.add_all(p.values())
    orders = [
        _order(10482, p["juliana"], "enviado", 9, rng, products, eta_days=-3),
        _order(10311, p["juliana"], "entregue", 48, rng, products),
        _order(10399, p["patricia"], "enviado", 14, rng, products, eta_days=-6),
        _order(10458, p["camila"], "entregue", 6, rng, products),
        _order(10511, p["fernanda"], "entregue", 5, rng, products),
        _order(10533, p["marcos"], "pago", 0.3, rng, products, eta_days=6),
        _order(10520, p["thiago"], "separacao", 1, rng, products, eta_days=5),
        _order(10276, p["rafael"], "entregue", 52, rng, products),
    ]
    db.add_all(orders)

    # base de clientes
    used = {v["name"] for v in PERSONAS.values()}
    contacts: list[Contact] = []
    while len(contacts) < 90:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name in used:
            continue
        used.add(name)
        slug = name.lower().replace(" ", ".").encode("ascii", "ignore").decode()
        contacts.append(Contact(
            name=name, email=f"{slug}@email.com", phone=f"55{rng.randint(11, 99)}9{rng.randint(10000000, 99999999)}",
            instagram=f"@{slug.replace('.', '_')}" if rng.random() < 0.4 else None, city=rng.choice(CITIES),
            tags=rng.sample(["aurora-club", "recorrente", "cliente-vip", "novo", "atacado"], rng.choice([0, 1, 1, 2])),
            created_at=utcnow() - timedelta(days=rng.randint(30, 400)),
        ))
    db.add_all(contacts)

    code = 10100
    for c in contacts:
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            age = rng.uniform(0.5, 58)
            status = "entregue" if age > 8 else rng.choice(["pago", "separacao", "enviado", "enviado"])
            if rng.random() < 0.04:
                status = "cancelado"
            orders.append(_order(code, c, status, age, rng, products,
                                 eta_days=None if status in ("entregue", "cancelado") else rng.uniform(1, 6)))
            code += 1
            if code in (10276, 10311, 10399, 10458, 10482, 10511, 10520, 10533):
                code += 1
    db.add_all(orders[8:])
    db.flush()
    for c in [*p.values(), *contacts]:
        c.lifetime_value = round(sum(o.total for o in c.orders if o.status != "cancelado"), 2)
    db.commit()


def seed_history(db: Session, rng: random.Random) -> None:
    agents = db.scalars(select(Agent)).all()
    contacts = [c for c in db.scalars(select(Contact)).all() if c.name not in {v["name"] for v in PERSONAS.values()}]
    now = utcnow()
    ticket_seq = 1
    channels, cw = list(CHANNEL_WEIGHTS), list(CHANNEL_WEIGHTS.values())
    ai_templates = [t for t in HISTORY_TEMPLATES if t[1] == "ai"]
    human_templates = [t for t in HISTORY_TEMPLATES if t[1] == "human"]

    for day in range(DAYS, 0, -1):
        progress = (DAYS - day) / DAYS  # 0 → 1 ao longo do período (operação crescendo)
        volume = max(2, round(rng.gauss(4 + 5 * progress, 1.4)))
        ai_rate = 0.6 + 0.16 * progress
        for _ in range(volume):
            contact = rng.choice(contacts)
            channel = rng.choices(channels, cw)[0]
            if channel == "instagram" and not contact.instagram:
                channel = "whatsapp"
            hour = rng.choices(range(24), HOUR_WEIGHTS)[0]
            start = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0) + timedelta(
                hours=hour + 3, minutes=rng.randint(0, 59))  # +3h: horário local → UTC
            if start > now - timedelta(hours=2):
                continue
            intent, outcome, turns = rng.choice(ai_templates if rng.random() < ai_rate else human_templates)
            agent = rng.choice([a for a in agents if a.role == "agent"] or agents) if outcome == "human" else None
            if intent == "reclamacao":
                agent = agents[0]
            order = rng.choice(contact.orders) if contact.orders else None
            protocol = f"OF-{start:%y%m}-{ticket_seq:04d}"

            conv = Conversation(contact=contact, channel=channel, status="resolved", intent=intent,
                                resolved_by=outcome, created_at=start, agent=agent,
                                priority="urgent" if intent == "reclamacao" else "normal",
                                tags=["risco-reputacao"] if intent == "reclamacao" else [])
            db.add(conv)
            vars_ = {"nome": first_name(contact.name), "pedido": order.code if order else "AUR-10000",
                     "rastreio": (order.tracking_code if order else None) or "QB123456789BR",
                     "eta": (start + timedelta(days=3)).strftime("%d/%m/%Y"), "protocolo": protocol,
                     "atendente": agent.name.split()[0] if agent else ""}
            t = start
            sentiments = []
            for idx, (who, text) in enumerate(turns):
                body = text.format(**vars_)
                if channel == "webchat":
                    body = body.replace("*", "")
                sender = {"c": "contact", "b": "bot", "a": "agent", "s": "system"}[who]
                meta: dict = {}
                if sender == "contact":
                    nlu = analyze(body)
                    sentiments.append(nlu.sentiment)
                    meta = {"nlu": nlu.as_dict()}
                elif sender == "bot":
                    meta = {"kind": "ai_reply", "provider": "offline", "model": "omniflow-nlu-rag-v1",
                            "latency_ms": rng.randint(180, 1400), "confidence": round(rng.uniform(0.7, 0.97), 2)}
                db.add(Message(conversation=conv, sender=sender, content=body, meta=meta,
                               agent=agent if sender == "agent" else None, created_at=t))
                if sender == "bot" and conv.first_response_seconds is None:
                    conv.first_response_seconds = round((t - start).total_seconds(), 1)
                if sender == "system" and "transferida" in body:
                    conv.handoff_reason = body.split("· ")[-1]
                nxt = turns[idx + 1][0] if idx + 1 < len(turns) else None
                if nxt in ("b", "s"):
                    delay = rng.uniform(0.8, 3.5)  # IA responde em segundos
                elif nxt == "a":
                    delay = rng.randint(45, 600)  # tempo de fila humana
                else:
                    delay = rng.randint(25, 180)  # cliente lendo e respondendo
                t += timedelta(seconds=delay)
            conv.sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else 0
            conv.updated_at = conv.resolved_at = t
            roll = rng.random()
            if roll < 0.62:
                weights = [62, 26, 7, 3, 2] if outcome == "ai" else [55, 28, 10, 4, 3]
                conv.csat = rng.choices([5, 4, 3, 2, 1], weights)[0]
            if "{protocolo}" in "".join(x[1] for x in turns):
                db.add(Ticket(protocol=protocol, conversation=conv, contact=contact,
                              kind="financeiro" if intent == "cancelamento" else "troca",
                              description=turns[0][1].format(**vars_), order_code=vars_["pedido"],
                              status=rng.choice(["resolvido", "resolvido", "em_andamento"]), created_at=start))
                ticket_seq += 1
    db.commit()


async def seed_live(db: Session) -> None:
    """Gera as conversas em andamento passando pelo orquestrador real (motor offline)."""
    from app.services.agent import InboundIdentity, agent_assign, agent_send, handle_inbound

    provider = OfflineProvider(seed=7)
    contacts = {c.name: c for c in db.scalars(select(Contact)).all()}
    now = utcnow()
    for persona, channel, texts, minutes_ago, agent_id in LIVE_SCRIPTS:
        contact = contacts[PERSONAS[persona]["name"]]
        result = None
        for text in texts:
            result = await handle_inbound(db, channel, InboundIdentity(contact_id=contact.id), text,
                                          provider=provider)
        conv = db.get(Conversation, result["conversation_id"])
        if agent_id:
            agent = db.get(Agent, agent_id)
            await agent_assign(db, conv, agent)
            await agent_send(db, conv, agent, f"Oi, {first_name(contact.name)}! Aqui é o {agent.name.split()[0]}, "
                             "da equipe Aurora. Sinto muito pela reação 😔 Já aprovei a devolução com reembolso "
                             "integral. Pode me mandar uma foto da região para registrarmos no laudo?")
        # espalha os horários para parecer uma fila real
        start = now - timedelta(minutes=minutes_ago)
        conv.created_at = start
        for i, msg in enumerate(conv.messages):
            msg.created_at = start + timedelta(seconds=20 * i + (2 if msg.sender == "bot" else 0))
        conv.updated_at = conv.messages[-1].created_at
        conv.first_response_seconds = round(rng_latency(conv), 1)
    db.commit()


def rng_latency(conv: Conversation) -> float:
    first_bot = next((m for m in conv.messages if m.sender == "bot"), None)
    return (first_bot.meta.get("latency_ms", 900) / 1000) if first_bot else 1.0


async def seed(db: Session) -> None:
    rng = random.Random(42)
    seed_base(db, rng)
    seed_history(db, rng)
    knowledge_index.invalidate()
    await seed_live(db)


async def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        await seed(db)
