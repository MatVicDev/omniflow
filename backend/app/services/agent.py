"""Orquestrador do atendimento.

Pipeline de cada mensagem recebida (qualquer canal):

  1. Identifica contato e conversa (abre nova se necessário)
  2. NLU local → intenção, sentimento, entidades
  3. Guardrails determinísticos (pedido de atendente, termos críticos, sentimento)
  4. Agente de IA (LLM ou offline) com ferramentas e RAG
  5. Pós-processamento: fluxos, transbordo por baixa confiança, encerramento
  6. Persiste a resposta com o trace completo e publica em tempo real
"""

import logging
import re
import time
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Agent, Contact, Conversation, KnowledgeArticle, Message
from app.realtime import hub
from app.serializers import conversation_out, message_out
from app.services import copilot
from app.services.ai.base import AgentInput, AgentOutput, LLMProvider
from app.services.ai.factory import get_offline_provider, get_provider
from app.services.ai.prompts import build_system_prompt
from app.services.channels import deliver_outbound
from app.services.flows import FlowEngine
from app.services.nlu import NLUResult, analyze
from app.services.settings_store import get_agent_settings
from app.services.tools import ToolContext, run_tool
from app.utils import first_name, utcnow

log = logging.getLogger(__name__)

CONTEXT_INTENTS = {"saudacao", "agradecimento", "outro"}
HISTORY_LIMIT = 14


@dataclass
class InboundIdentity:
    contact_id: int | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None


# ─── Contato e conversa ──────────────────────────────────────────────────────


def resolve_contact(db: Session, ident: InboundIdentity) -> Contact:
    if ident.contact_id and (c := db.get(Contact, ident.contact_id)):
        return c
    conds = []
    if ident.phone:
        conds.append(Contact.phone == ident.phone)
    if ident.email:
        conds.append(Contact.email == ident.email)
    if ident.instagram:
        conds.append(Contact.instagram == ident.instagram)
    if conds and (c := db.scalars(select(Contact).where(or_(*conds))).first()):
        return c
    contact = Contact(name=ident.name or "Visitante", phone=ident.phone, email=ident.email,
                      instagram=ident.instagram, tags=["novo"])
    db.add(contact)
    db.flush()
    return contact


def open_conversation(db: Session, contact: Contact, channel: str) -> Conversation:
    conv = db.scalars(
        select(Conversation)
        .where(Conversation.contact_id == contact.id, Conversation.channel == channel,
               Conversation.status != "resolved")
        .order_by(Conversation.updated_at.desc())
    ).first()
    if conv:
        return conv
    conv = Conversation(contact_id=contact.id, channel=channel, status="bot")
    db.add(conv)
    db.flush()
    return conv


def _pending_csat(db: Session, contact: Contact, channel: str, text: str) -> Conversation | None:
    """Cliente respondeu a pesquisa de satisfação (1 a 5) de uma conversa recém-encerrada."""
    if not re.fullmatch(r"\s*[1-5]\s*(estrelas?)?\s*[!.]*\s*", text, re.IGNORECASE):
        return None
    conv = db.scalars(
        select(Conversation)
        .where(Conversation.contact_id == contact.id, Conversation.channel == channel,
               Conversation.status == "resolved", Conversation.csat.is_(None))
        .order_by(Conversation.resolved_at.desc())
    ).first()
    if conv and conv.resolved_at and (utcnow() - conv.resolved_at).total_seconds() < 86400:
        return conv
    return None


def _history(conv: Conversation, exclude_id: int) -> list[dict]:
    turns = []
    for m in conv.messages[-HISTORY_LIMIT - 1 :]:
        if m.id == exclude_id or m.sender == "system":
            continue
        role = "user" if m.sender == "contact" else "assistant"
        turns.append({"role": role, "content": m.content})
    return turns


async def _publish(conv: Conversation, msg: Message | None = None) -> None:
    if msg:
        await hub.publish("message.created", message_out(msg))
    await hub.publish("conversation.updated", conversation_out(conv))


def add_message(db: Session, conv: Conversation, sender: str, content: str, meta: dict | None = None,
                agent_id: int | None = None) -> Message:
    msg = Message(conversation_id=conv.id, sender=sender, content=content, meta=meta or {}, agent_id=agent_id)
    db.add(msg)
    conv.updated_at = utcnow()
    db.flush()
    db.refresh(conv)
    return msg


# ─── Transbordo e encerramento ───────────────────────────────────────────────


async def handoff(db: Session, conv: Conversation, reason: str, priority: str = "normal") -> None:
    conv.status = "waiting"
    conv.handoff_reason = reason
    order = ["low", "normal", "high", "urgent"]
    if order.index(priority) > order.index(conv.priority):
        conv.priority = priority
    db.flush()
    db.refresh(conv)
    conv.summary = await copilot.summarize(conv)


async def resolve_conversation(db: Session, conv: Conversation, by: str, settings: dict,
                               flows: FlowEngine | None = None) -> Message | None:
    conv.status = "resolved"
    conv.resolved_by = by
    conv.resolved_at = utcnow()
    conv.unread = 0
    flows = flows or FlowEngine(db)
    if settings.get("csat_enabled") and flows.active("pesquisa_csat"):
        flows.mark("pesquisa_csat", "Atendimento encerrado")
        text = (f"Antes de ir, {first_name(conv.contact.name)}: de 1 a 5, como você avalia este atendimento? "
                "Sua opinião ajuda muito a gente 💜")
        if conv.channel == "email":
            text = text.replace(" 💜", "")
        return add_message(db, conv, "bot", text, meta={"kind": "csat_request"})
    return None


# ─── Pipeline principal ──────────────────────────────────────────────────────


def _guardrail(nlu: NLUResult, conv: Conversation, settings: dict, flows: FlowEngine) -> dict | None:
    if nlu.critical and flows.active("escalonamento_critico"):
        flows.mark("escalonamento_critico", "Menção a órgão de defesa do consumidor / jurídico")
        conv.tags = sorted(set(conv.tags or []) | {"risco-reputacao"})
        return {"rule": "termo_critico", "reason": "Risco de reputação (Procon/Reclame Aqui/jurídico)",
                "priority": "urgent",
                "text": "Entendo a seriedade da situação e peço desculpas pelo transtorno. Estou encaminhando "
                        "seu caso com prioridade máxima para um especialista, que vai te responder em instantes."}
    if nlu.intent == "falar_humano":
        return {"rule": "pedido_atendente", "reason": "Cliente pediu atendente", "priority": "normal",
                "text": "Claro! Já estou chamando um especialista da equipe. Em instantes alguém continua com você 🙂"}
    if conv.sentiment <= settings["handoff_sentiment_threshold"] and flows.active("transbordo_inteligente"):
        flows.mark("transbordo_inteligente", "Sentimento abaixo do limite")
        return {"rule": "sentimento_negativo", "reason": "Sentimento muito negativo", "priority": "high",
                "text": "Sinto muito pela experiência, de verdade. 😔 Vou chamar agora um especialista da nossa "
                        "equipe para cuidar pessoalmente do seu caso."}
    return None


async def handle_inbound(db: Session, channel: str, ident: InboundIdentity, text: str,
                         tags: list[str] | None = None, provider: LLMProvider | None = None) -> dict:
    started = time.perf_counter()
    text = text.strip()
    contact = resolve_contact(db, ident)
    settings = get_agent_settings(db)

    if csat_conv := _pending_csat(db, contact, channel, text):
        csat_conv.csat = int(re.search(r"[1-5]", text).group(0))
        msg = add_message(db, csat_conv, "contact", text)
        reply = add_message(db, csat_conv, "bot", "Obrigada pela avaliação! Até a próxima ✨"
                            if channel != "email" else "Obrigada pela avaliação!", meta={"kind": "csat_thanks"})
        db.commit()
        await _publish(csat_conv, msg)
        await _publish(csat_conv, reply)
        return {"conversation_id": csat_conv.id, "reply": message_out(reply)}

    conv = open_conversation(db, contact, channel)
    if tags:
        conv.tags = sorted(set(conv.tags or []) | set(tags))
    is_first = db.scalar(select(func.count(Message.id)).where(Message.conversation_id == conv.id)) == 0

    nlu = analyze(text)
    incoming = add_message(db, conv, "contact", text, meta={"nlu": nlu.as_dict()})
    conv.unread += 1
    conv.sentiment = nlu.sentiment if is_first else round(0.6 * nlu.sentiment + 0.4 * conv.sentiment, 3)
    previous_intent = conv.intent
    if nlu.intent not in CONTEXT_INTENTS or conv.intent is None and nlu.intent != "saudacao":
        conv.intent = nlu.intent
    db.commit()
    await _publish(conv, incoming)

    if conv.status in ("waiting", "human"):
        return {"conversation_id": conv.id, "reply": None}  # um humano está (ou vai estar) com o caso

    await hub.publish("typing", {"conversation_id": conv.id, "sender": "bot"})

    flows = FlowEngine(db)
    ctx = ToolContext(db=db, contact=contact, conversation=conv)
    guard = _guardrail(nlu, conv, settings, flows)
    fallback_error = None

    if guard:
        out = AgentOutput(text=guard["text"], provider="guardrail", model="omniflow-rules", confidence=1.0)
        out.tool_calls.append(run_tool(ctx, "transferir_para_humano",
                                       {"motivo": guard["reason"], "prioridade": guard["priority"]}))
    else:
        data = AgentInput(ctx=ctx, message=text, history=_history(conv, incoming.id), nlu=nlu,
                          settings=settings, system_prompt=build_system_prompt(settings),
                          previous_intent=previous_intent)
        provider = provider or get_provider()
        try:
            out = await provider.respond(data)
            if not out.text:
                raise ValueError("Resposta vazia do provedor")
        except Exception as exc:  # LLM fora do ar → offline assume, o cliente nunca fica sem resposta
            log.exception("Provedor %s falhou — usando motor offline", provider.name)
            fallback_error = f"{type(exc).__name__}: {exc}"[:200]
            out = await get_offline_provider().respond(data)

    # ── pós-processamento ────────────────────────────────────────────────────
    handoff_info = out.handoff
    if not handoff_info and out.confidence < 0.35:
        conv.ai_failures += 1
        if conv.ai_failures >= settings["handoff_after_failures"] and flows.active("transbordo_inteligente"):
            flows.mark("transbordo_inteligente", "Falhas consecutivas da IA")
            handoff_info = {"motivo": "IA não encontrou resposta confiável", "prioridade": "normal"}
            out.text += "\n\nPara não te deixar sem resposta, já chamei um especialista da equipe 🙋‍♀️"
    elif not handoff_info:
        conv.ai_failures = 0

    if is_first and not guard and nlu.intent != "saudacao" and flows.active("boas_vindas"):
        flows.mark("boas_vindas", "Primeira mensagem do contato")
        if channel != "email":
            out.text = f"Oi, {first_name(contact.name)}! Aqui é a {settings['bot_name']} 👋\n\n{out.text}"

    off_hours = False
    if handoff_info and flows.active("fora_horario") and not FlowEngine.is_business_hours(settings):
        off_hours = True
        flows.mark("fora_horario", "Transbordo fora do horário comercial")
        h = settings["business_hours"]
        out.text += (f"\n\nObs.: nossa equipe atende das {h['start']} às {h['end']}. Seu caso já está na fila "
                     "com prioridade e será o primeiro a ser respondido.")

    if any(c.name == "consultar_pedido" for c in out.tool_calls) and flows.active("rastreio_inteligente"):
        flows.mark("rastreio_inteligente", "Consulta automática de pedido")

    for src in out.sources:
        if art := db.get(KnowledgeArticle, src["article_id"]):
            art.hits += 1

    latency_ms = round((time.perf_counter() - started) * 1000)
    trace = {
        "kind": "ai_reply",
        "provider": out.provider,
        "model": out.model,
        "latency_ms": latency_ms,
        "confidence": round(out.confidence, 2),
        "nlu": nlu.as_dict(),
        "tool_calls": [c.as_dict() for c in out.tool_calls],
        "sources": out.sources[:4],
        "flows": flows.triggered,
        "guardrail": guard["rule"] if guard else None,
        "handoff": handoff_info,
        "usage": out.usage,
        "fallback_error": fallback_error,
        "off_hours": off_hours,
    }
    reply = add_message(db, conv, "bot", out.text, meta=trace)
    if conv.first_response_seconds is None:
        conv.first_response_seconds = round((utcnow() - incoming.created_at).total_seconds() + latency_ms / 1000, 1)

    extra_msgs: list[Message] = []
    if handoff_info:
        await handoff(db, conv, handoff_info.get("motivo", "Transbordo"), handoff_info.get("prioridade", "normal"))
        extra_msgs.append(add_message(db, conv, "system", f"Conversa transferida para a fila humana · "
                                                          f"{handoff_info.get('motivo', '')}"))
    elif out.resolved_hint and settings.get("auto_resolve_on_thanks") and len(conv.messages) > 3:
        csat = await resolve_conversation(db, conv, "ai", settings, flows)
        if csat:
            extra_msgs.append(csat)

    db.commit()
    await _publish(conv, reply)
    for m in extra_msgs:
        await _publish(conv, m)
    await deliver_outbound(conv, [reply, *[m for m in extra_msgs if m.sender == "bot"]])
    return {"conversation_id": conv.id, "reply": message_out(reply)}


# ─── Ações do atendente humano ───────────────────────────────────────────────


async def agent_send(db: Session, conv: Conversation, agent: Agent, content: str) -> Message:
    if conv.status != "human" or conv.assigned_agent_id != agent.id:
        conv.status = "human"
        conv.assigned_agent_id = agent.id
    conv.unread = 0
    msg = add_message(db, conv, "agent", content.strip(), agent_id=agent.id)
    db.commit()
    await _publish(conv, msg)
    await deliver_outbound(conv, [msg])
    return msg


async def agent_assign(db: Session, conv: Conversation, agent: Agent) -> Message:
    conv.status = "human"
    conv.assigned_agent_id = agent.id
    conv.unread = 0
    msg = add_message(db, conv, "system", f"{agent.name} assumiu o atendimento")
    db.commit()
    await _publish(conv, msg)
    return msg


async def agent_resolve(db: Session, conv: Conversation) -> None:
    settings = get_agent_settings(db)
    by = "human" if any(m.sender == "agent" for m in conv.messages) else "ai"
    sys_msg = add_message(db, conv, "system", "Atendimento encerrado")
    csat = await resolve_conversation(db, conv, by, settings)
    db.commit()
    await _publish(conv, sys_msg)
    if csat:
        await _publish(conv, csat)
        await deliver_outbound(conv, [csat])


async def return_to_bot(db: Session, conv: Conversation) -> None:
    conv.status = "bot"
    conv.assigned_agent_id = None
    conv.ai_failures = 0
    msg = add_message(db, conv, "system", "Conversa devolvida para a IA")
    db.commit()
    await _publish(conv, msg)
