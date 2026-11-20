import re
import unicodedata
from datetime import UTC, datetime


def utcnow() -> datetime:
    """UTC 'naive' — o SQLite não guarda fuso, então padronizamos tudo em UTC."""
    return datetime.now(UTC).replace(tzinfo=None)


def normalize(text: str) -> str:
    """Minúsculas e sem acentos — base para NLU e busca."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def brl(value: float) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def first_name(name: str) -> str:
    return name.split()[0] if name else ""


ORDER_CODE_RE = re.compile(r"\b(?:AUR[-\s]?)?(\d{5})\b", re.IGNORECASE)
