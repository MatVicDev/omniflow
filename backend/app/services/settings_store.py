from copy import deepcopy

from sqlalchemy.orm import Session

from app.models import Setting

DEFAULT_AGENT_SETTINGS: dict = {
    "bot_name": "Aurora",
    "tone": "amigavel",
    "greeting": "",
    "custom_instructions": "",
    "handoff_sentiment_threshold": -0.55,
    "handoff_after_failures": 2,
    "auto_resolve_on_thanks": True,
    "csat_enabled": True,
    "business_hours": {"start": "08:00", "end": "20:00", "days": [0, 1, 2, 3, 4, 5]},
    "timezone": "America/Sao_Paulo",
}

KEY = "agent"


def get_agent_settings(db: Session) -> dict:
    row = db.get(Setting, KEY)
    merged = deepcopy(DEFAULT_AGENT_SETTINGS)
    if row:
        merged.update(row.value)
    return merged


def update_agent_settings(db: Session, patch: dict) -> dict:
    current = get_agent_settings(db)
    current.update({k: v for k, v in patch.items() if k in DEFAULT_AGENT_SETTINGS})
    row = db.get(Setting, KEY)
    if row:
        row.value = current
    else:
        db.add(Setting(key=KEY, value=current))
    db.commit()
    return current
