"""NLU local em PT-BR: intenção, sentimento e entidades.

Roda em toda mensagem (custo zero, < 1 ms). Alimenta roteamento, regras de
transbordo e analytics — mesmo quando a resposta é gerada por um LLM.
"""

import re
from dataclasses import dataclass, field

from app.utils import ORDER_CODE_RE, normalize

INTENT_LABELS = {
    "saudacao": "Saudação",
    "rastreio": "Rastreio de pedido",
    "troca_devolucao": "Troca / devolução",
    "cancelamento": "Cancelamento",
    "pagamento": "Pagamento / reembolso",
    "frete_prazo": "Frete e prazos",
    "produto": "Dúvida sobre produto",
    "promocao": "Cupons e promoções",
    "horario": "Horário de atendimento",
    "reclamacao": "Reclamação",
    "falar_humano": "Pediu atendente",
    "agradecimento": "Agradecimento",
    "outro": "Outros assuntos",
}

# (padrão normalizado, peso). Padrões são substrings — "rastre" pega rastreio/rastrear.
_INTENT_PATTERNS: dict[str, list[tuple[str, float]]] = {
    "saudacao": [("oi", 0.6), ("ola", 0.8), ("bom dia", 1), ("boa tarde", 1), ("boa noite", 1), ("e ai", 0.6)],
    "rastreio": [
        ("rastre", 2), ("onde esta meu", 2), ("cade meu", 2), ("cade o", 1.5), ("nao chegou", 2),
        ("ainda nao chegou", 2), ("status do pedido", 2), ("meu pedido", 1.2), ("atrasad", 1.5),
        ("chega quando", 1.5), ("quando chega", 1.5), ("codigo de rastreio", 2.5), ("entrega", 0.8),
    ],
    "troca_devolucao": [
        ("troca", 2), ("trocar", 2), ("devolv", 2), ("devoluc", 2), ("arrepend", 2), ("defeito", 2),
        ("veio errado", 2.5), ("produto errado", 2.5), ("quebrad", 2), ("vazad", 2), ("alergia", 2.5), ("reacao", 2),
        ("irritou", 1.5), ("nao gostei", 1.2),
    ],
    "cancelamento": [("cancelar", 2.5), ("cancelamento", 2.5), ("cancela", 2)],
    "pagamento": [
        ("pix", 1.5), ("aceita", 1.8), ("boleto", 1.8), ("cartao", 1.2), ("parcel", 1.5), ("pagamento", 1.5),
        ("estorno", 2.2), ("reembolso", 2.2), ("cobrad", 1.8), ("cobranca", 1.8), ("dinheiro de volta", 2.2),
    ],
    "frete_prazo": [
        ("frete", 2), ("prazo", 1.5), ("quanto tempo", 1.2), ("cep", 1.5), ("entregam", 1.5),
        ("frete gratis", 2.5), ("envio", 1),
    ],
    "produto": [
        ("produto", 0.8), ("estoque", 2), ("serve para", 2), ("pele", 1.5), ("cabelo", 1.5), ("vegano", 2),
        ("ingrediente", 2), ("quanto custa", 2), ("preco", 1.5), ("recomenda", 1.8), ("indica", 1.5),
        ("serum", 1.8), ("hidratante", 1.8), ("protetor", 1.8), ("shampoo", 1.8), ("kit", 1.2),
        ("oleosa", 1.8), ("seca", 0.8), ("acne", 1.8), ("tem disponivel", 1.8), ("crueldade", 1.5),
    ],
    "promocao": [("cupom", 2.5), ("desconto", 2), ("promo", 2), ("black friday", 2.5), ("primeira compra", 1.5)],
    "horario": [("horario", 2), ("que horas", 1.5), ("funciona", 1), ("aberto", 1)],
    "reclamacao": [
        ("pessimo", 2), ("absurdo", 2), ("procon", 3), ("reclame aqui", 3), ("descaso", 2.5),
        ("horrivel", 2), ("palhacada", 2.5), ("advogado", 3), ("processar", 3), ("vergonha", 2),
        ("ninguem resolve", 2.5), ("enganad", 2),
    ],
    "falar_humano": [
        ("atendente", 2.5), ("humano", 2.5), ("falar com alguem", 3), ("pessoa de verdade", 3),
        ("gerente", 2), ("supervisor", 2), ("operador", 2), ("falar com uma pessoa", 3),
    ],
    "agradecimento": [("obrigad", 2), ("valeu", 2), ("perfeito", 1.2), ("resolveu", 1.5), ("show", 0.8)],
}

CRITICAL_TERMS = ("procon", "reclame aqui", "advogado", "processar", "processo judicial", "juizado", "chargeback")

_POSITIVE = {
    "obrigado": 1, "obrigada": 1, "otimo": 1.2, "excelente": 1.5, "perfeito": 1.3, "amei": 1.5, "adorei": 1.5,
    "maravilhoso": 1.5, "bom": 0.6, "boa": 0.5, "legal": 0.7, "top": 1, "show": 0.8, "rapido": 0.6,
    "resolveu": 1, "gostei": 1, "feliz": 1.2, "lindo": 1, "incrivel": 1.4, "valeu": 0.8,
}
_NEGATIVE = {
    "pessimo": 2, "horrivel": 2, "absurdo": 1.8, "ruim": 1.2, "demora": 1, "demorando": 1.2, "atrasado": 1,
    "atrasou": 1.2, "nunca": 0.8, "raiva": 1.8, "irritado": 1.6, "irritada": 1.6, "decepcionado": 1.6,
    "decepcionada": 1.6, "descaso": 2, "vergonha": 1.8, "palhacada": 2, "lixo": 2, "quebrado": 1.2,
    "vazou": 1.2, "errado": 1, "problema": 0.8, "reclamar": 1.2, "procon": 2, "enganado": 1.8, "enganada": 1.8,
    "cansado": 1, "cansada": 1, "reclamacao": 1.2, "ninguem": 0.8, "terceira": 0.6, "frustrado": 1.6,
    "frustrada": 1.6, "chateado": 1.4, "chateada": 1.4, "pior": 1.6, "demorou": 1,
    "insatisfeito": 1.6, "insatisfeita": 1.6, "defeito": 1, "alergia": 1,
}
_NEGATORS = {"nao", "nunca", "jamais", "nem"}
_INTENSIFIERS = {"muito": 1.5, "super": 1.5, "extremamente": 2, "bem": 1.2, "totalmente": 1.6, "mega": 1.5}
_POS_EMOJI = ("😊", "😀", "😍", "🥰", "❤", "👍", "🙏", "😄", "✨")
_NEG_EMOJI = ("😡", "🤬", "😠", "😤", "👎", "😢", "😭", "💔", "😕", "🙁", "😞", "😩")

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_CEP_RE = re.compile(r"\b\d{5}-?\d{3}\b")


@dataclass
class NLUResult:
    intent: str
    intent_label: str
    confidence: float
    sentiment: float
    sentiment_label: str
    entities: dict = field(default_factory=dict)
    critical: bool = False
    matched: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "intent": self.intent,
            "intent_label": self.intent_label,
            "confidence": round(self.confidence, 2),
            "sentiment": round(self.sentiment, 2),
            "sentiment_label": self.sentiment_label,
            "entities": self.entities,
            "critical": self.critical,
            "matched": self.matched,
        }


def _word_match(text: str, pattern: str) -> bool:
    # padrões curtos ("oi", "pix") precisam casar como palavra inteira
    if len(pattern) <= 3:
        return re.search(rf"\b{re.escape(pattern)}\b", text) is not None
    return pattern in text


def classify_intent(text: str) -> tuple[str, float, list[str]]:
    norm = normalize(text)
    scores: dict[str, float] = {}
    matched: dict[str, list[str]] = {}
    for intent, patterns in _INTENT_PATTERNS.items():
        for pattern, weight in patterns:
            if _word_match(norm, pattern):
                scores[intent] = scores.get(intent, 0) + weight
                matched.setdefault(intent, []).append(pattern)

    if not scores:
        return "outro", 0.3, []

    # saudação só vence se a mensagem for basicamente uma saudação
    if len(scores) > 1 and "saudacao" in scores:
        scores.pop("saudacao")
    if len(scores) > 1 and "agradecimento" in scores and len(norm.split()) > 6:
        scores.pop("agradecimento")

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = min(0.98, 0.45 + 0.35 * (scores[best] / total) + 0.06 * scores[best])
    return best, confidence, matched.get(best, [])


def analyze_sentiment(text: str) -> float:
    norm = normalize(text)
    tokens = re.findall(r"[a-z]+", norm)
    score = 0.0
    for i, tok in enumerate(tokens):
        value = _POSITIVE.get(tok, 0) - _NEGATIVE.get(tok, 0)
        if not value:
            continue
        window = tokens[max(0, i - 3) : i]
        if any(w in _NEGATORS for w in window):
            value = -value * 0.8
        for w in window:
            value *= _INTENSIFIERS.get(w, 1)
        score += value
    score += 0.8 * sum(text.count(e) for e in _POS_EMOJI)
    score -= 1.0 * sum(text.count(e) for e in _NEG_EMOJI)
    if text.count("!") >= 3:
        score -= 0.4
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 12 and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        score -= 1.0  # CAIXA ALTA = gritando
    return max(-1.0, min(1.0, score / 3))


def sentiment_label(value: float) -> str:
    if value <= -0.25:
        return "negativo"
    if value >= 0.25:
        return "positivo"
    return "neutro"


def extract_entities(text: str) -> dict:
    entities: dict = {}
    if m := ORDER_CODE_RE.search(text):
        entities["order_code"] = f"AUR-{m.group(1)}"
    if m := _EMAIL_RE.search(text):
        entities["email"] = m.group(0)
    if m := _CEP_RE.search(text):
        entities["cep"] = m.group(0)
    return entities


def analyze(text: str) -> NLUResult:
    intent, confidence, matched = classify_intent(text)
    sentiment = analyze_sentiment(text)
    norm = normalize(text)
    return NLUResult(
        intent=intent,
        intent_label=INTENT_LABELS[intent],
        confidence=confidence,
        sentiment=sentiment,
        sentiment_label=sentiment_label(sentiment),
        entities=extract_entities(text),
        critical=any(term in norm for term in CRITICAL_TERMS),
        matched=matched,
    )
