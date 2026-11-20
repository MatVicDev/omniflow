"""Entrada de mensagens: simulador de canais e webhook da WhatsApp Cloud API."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.schemas import Channel, InboundMessage
from app.services.agent import InboundIdentity, handle_inbound

log = logging.getLogger(__name__)
router = APIRouter(tags=["Canais"])


@router.post("/api/channels/{channel}/inbound", summary="Recebe uma mensagem de cliente em um canal")
async def inbound(channel: Channel, body: InboundMessage, db: Session = Depends(get_db)):
    ident = InboundIdentity(contact_id=body.contact_id, name=body.name, phone=body.phone,
                            email=body.email, instagram=body.instagram)
    return await handle_inbound(db, channel, ident, body.text)


@router.get("/webhooks/whatsapp", summary="Verificação do webhook (Meta)", response_class=PlainTextResponse)
def whatsapp_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    if mode == "subscribe" and token == get_settings().whatsapp_verify_token:
        return challenge
    raise HTTPException(403, "Token de verificação inválido")


@router.post("/webhooks/whatsapp", summary="Mensagens recebidas da WhatsApp Cloud API")
async def whatsapp_receive(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    processed = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            names = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue  # áudio/imagem: ponto de extensão (transcrição / visão)
                wa_id = msg["from"]
                ident = InboundIdentity(name=names.get(wa_id) or wa_id, phone=wa_id)
                await handle_inbound(db, "whatsapp", ident, msg["text"]["body"], tags=["whatsapp-cloud"])
                processed += 1
    return {"processed": processed}
