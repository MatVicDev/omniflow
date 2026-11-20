"""Copiloto do atendente humano: resumo do caso e sugestão da próxima resposta."""

import logging

from app.models import Conversation
from app.services.ai.factory import get_provider
from app.services.ai.prompts import SUGGEST_SYSTEM, SUMMARY_SYSTEM
from app.services.nlu import INTENT_LABELS, sentiment_label
from app.services.retrieval import knowledge_index
from app.utils import first_name

log = logging.getLogger(__name__)

_NEXT_STEP = {
    "rastreio": "Confirmar a situação com a transportadora e dar um prazo concreto ao cliente.",
    "troca_devolucao": "Validar o pedido/motivo e enviar a etiqueta de postagem reversa.",
    "cancelamento": "Verificar se o pedido já foi despachado e processar o estorno.",
    "pagamento": "Conferir o status do pagamento/estorno no gateway.",
    "reclamacao": "Acolher o cliente, assumir o caso e oferecer uma solução concreta (cupom/reenvio).",
    "produto": "Indicar o produto adequado e enviar o link.",
}


def _transcript(conv: Conversation, limit: int = 16) -> str:
    who = {"contact": "Cliente", "bot": "IA", "agent": "Atendente", "system": "Sistema"}
    return "\n".join(f"{who.get(m.sender, m.sender)}: {m.content}" for m in conv.messages[-limit:])


def offline_summary(conv: Conversation) -> str:
    customer_msgs = [m.content for m in conv.messages if m.sender == "contact"]
    tools = [c for m in conv.messages if m.sender == "bot" for c in (m.meta or {}).get("tool_calls", [])]
    protocols = [c["result"]["protocolo"] for c in tools
                 if c["name"] == "abrir_solicitacao" and c.get("result")]
    orders = {p["codigo"] for c in tools if c["name"] == "consultar_pedido" and c.get("result")
              for p in c["result"].get("pedidos", [])}
    intent = INTENT_LABELS.get(conv.intent or "outro", "Outros assuntos")
    lines = [
        f"• Assunto: {intent} — cliente {sentiment_label(conv.sentiment)}.",
        f"• Última mensagem: “{customer_msgs[-1][:120]}”" if customer_msgs else "• Sem mensagens do cliente.",
    ]
    done = []
    if orders:
        done.append("pedido(s) consultado(s): " + ", ".join(sorted(orders)))
    if protocols:
        done.append("protocolo(s): " + ", ".join(protocols))
    if done:
        lines.append("• IA já fez: " + "; ".join(done) + ".")
    lines.append("• Próximo passo: " + _NEXT_STEP.get(conv.intent or "", "Entender a necessidade e resolver."))
    return "\n".join(lines)


async def summarize(conv: Conversation) -> str:
    provider = get_provider()
    if provider.name == "offline":
        return offline_summary(conv)
    try:
        text = await provider.complete(SUMMARY_SYSTEM, _transcript(conv), max_tokens=400)
        return text or offline_summary(conv)
    except Exception:  # LLM indisponível não pode travar o transbordo
        log.exception("Falha ao resumir com LLM — usando resumo offline")
        return offline_summary(conv)


async def suggest_reply(db, conv: Conversation) -> dict:
    last_customer = next((m.content for m in reversed(conv.messages) if m.sender == "contact"), "")
    hits = knowledge_index.search(db, last_customer, k=2, min_score=0.3) if last_customer else []
    provider = get_provider()
    name = first_name(conv.contact.name)

    if provider.name != "offline":
        refs = "\n\n".join(f"[{h.title}] {h.text}" for h in hits) or "Nenhuma referência encontrada."
        prompt = f"<conversa>\n{_transcript(conv)}\n</conversa>\n\n<referencias>\n{refs}\n</referencias>"
        try:
            text = await provider.complete(SUGGEST_SYSTEM, prompt, max_tokens=500)
            if text:
                return {"text": text, "sources": [h.as_dict() for h in hits], "provider": provider.name}
        except Exception:
            log.exception("Falha na sugestão via LLM — usando sugestão offline")

    if conv.intent == "reclamacao" or conv.sentiment < -0.3:
        opening = (f"Oi, {name}! Aqui é da equipe Aurora. Sinto muito pelo transtorno — "
                   "vou cuidar pessoalmente do seu caso a partir de agora.")
    else:
        opening = f"Oi, {name}! Aqui é da equipe Aurora, vou continuar seu atendimento."
    body = f"\n\n{hits[0].text}" if hits else "\n\nPode me confirmar os detalhes para eu resolver agora mesmo?"
    return {"text": opening + body, "sources": [h.as_dict() for h in hits], "provider": "offline"}
