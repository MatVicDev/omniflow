"""Conectores de canal (saída).

Conversas vindas da WhatsApp Cloud API (tag `whatsapp-cloud`) recebem as
respostas de volta pela Graph API. Os demais canais da demo são simulados — o
painel e o simulador recebem tudo via WebSocket. Instagram (Messenger API) e
e-mail (SMTP/SES) entram aqui com a mesma interface.
"""

import logging

import httpx

from app.core.config import get_settings
from app.models import Conversation, Message

log = logging.getLogger(__name__)
GRAPH_URL = "https://graph.facebook.com/v21.0/{phone_id}/messages"


async def send_whatsapp_text(to: str, text: str) -> bool:
    s = get_settings()
    if not (s.whatsapp_token and s.whatsapp_phone_number_id):
        return False
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            GRAPH_URL.format(phone_id=s.whatsapp_phone_number_id),
            headers={"Authorization": f"Bearer {s.whatsapp_token}"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
        )
    if resp.status_code >= 400:
        log.warning("WhatsApp Cloud API respondeu %s: %s", resp.status_code, resp.text[:300])
        return False
    return True


async def deliver_outbound(conv: Conversation, messages: list[Message]) -> None:
    if conv.channel != "whatsapp" or "whatsapp-cloud" not in (conv.tags or []) or not conv.contact.phone:
        return
    for msg in messages:
        if msg.sender in ("bot", "agent"):
            try:
                await send_whatsapp_text(conv.contact.phone, msg.content)
            except httpx.HTTPError:
                log.exception("Falha ao entregar mensagem %s no WhatsApp", msg.id)
