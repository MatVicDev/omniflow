"""Motor de automações (fluxos).

Os fluxos são definidos como grafo (nós + arestas) — o mesmo JSON que o painel
desenha. Aqui ficam os gatilhos que o orquestrador consulta a cada mensagem.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Flow
from app.utils import utcnow


class FlowEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._cache: dict[str, Flow] = {f.key: f for f in db.scalars(select(Flow)).all()}
        self.triggered: list[dict] = []

    def active(self, key: str) -> bool:
        flow = self._cache.get(key)
        return bool(flow and flow.active)

    def mark(self, key: str, detail: str) -> None:
        flow = self._cache.get(key)
        if flow:
            flow.runs += 1
            self.triggered.append({"key": key, "name": flow.name, "detail": detail})

    @staticmethod
    def is_business_hours(settings: dict, now: datetime | None = None) -> bool:
        tz = ZoneInfo(settings.get("timezone", "America/Sao_Paulo"))
        local = (now or utcnow()).replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        hours = settings["business_hours"]
        if local.weekday() not in hours["days"]:
            return False
        hhmm = local.strftime("%H:%M")
        return hours["start"] <= hhmm < hours["end"]
