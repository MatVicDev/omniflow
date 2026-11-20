"""Hub de tempo real: todo evento relevante é publicado para os painéis via WebSocket."""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

log = logging.getLogger(__name__)


class RealtimeHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def publish(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str, ensure_ascii=False)
        async with self._lock:
            clients = list(self._clients)
        dead = []
        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:  # cliente caiu — remove sem derrubar o broadcast
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    @property
    def size(self) -> int:
        return len(self._clients)


hub = RealtimeHub()
