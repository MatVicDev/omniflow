import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import channels, conversations, knowledge, workspace
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import Base, SessionLocal, engine
from app.models import Contact
from app.realtime import hub
from app.services.ai.factory import get_provider

setup_logging()
log = logging.getLogger("omniflow")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if settings.seed_on_startup:
        from app.seed import seed

        with SessionLocal() as db:
            if not db.query(Contact.id).first():
                await seed(db)
                log.info("Banco populado com dados de demonstração")
    provider = get_provider()
    log.info("OmniFlow pronto · IA: %s (%s)", provider.name, provider.model)
    yield


app = FastAPI(
    title="OmniFlow API",
    version=settings.version,
    description="Plataforma omnichannel de atendimento com agentes de IA: inbox unificado, "
    "RAG, function calling, transbordo inteligente para humanos e analytics.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router)
app.include_router(channels.router)
app.include_router(knowledge.router)
app.include_router(workspace.router)


@app.get("/api/health", tags=["Sistema"])
def health():
    provider = get_provider()
    return {"status": "ok", "version": settings.version, "ai_provider": provider.name,
            "ai_model": provider.model, "realtime_clients": hub.size}


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # mantém a conexão (ping do cliente)
    except WebSocketDisconnect:
        await hub.disconnect(ws)
