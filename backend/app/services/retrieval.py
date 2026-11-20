"""Busca na base de conhecimento (RAG) com BM25 + normalização PT-BR.

Sem dependências externas: os artigos são quebrados em trechos (parágrafos),
tokenizados com stemming leve e expansão de sinônimos. O índice fica em memória
e é reconstruído quando a base muda (versão incrementada pela API).

Em produção este módulo é o ponto de troca para embeddings + pgvector; a
interface (`search(query) -> list[Hit]`) continua a mesma.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from threading import Lock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeArticle
from app.utils import normalize

_STOPWORDS = frozenset(
    """a o as os um uma uns umas de do da dos das no na nos nas em para pra pro por com sem que se e ou meu
    minha meus minhas seu sua seus suas eu voce voces ele ela eles elas isso esse essa este esta ao aos
    como mais mas ja tem ter ser foi sao e eh vou vai qual quais quando onde porque pq tambem muito
    pouco ate sobre entre me te lhe nao sim aqui la gostaria queria quero preciso saber posso favor oi
    ola bom dia boa tarde noite obrigado obrigada depois antes faz fazer faco""".split()
)

_SYNONYMS = {
    "devolver": "devolucao", "devolvo": "devolucao", "trocar": "troca", "troco": "troca",
    "arrependi": "arrependimento", "estornar": "estorno", "reembolsar": "reembolso",
    "entregar": "entrega", "chegar": "entrega", "chega": "entrega", "envio": "entrega",
    "enviar": "entrega", "correio": "transportadora", "correios": "transportadora",
    "pagar": "pagamento", "parcelar": "parcelamento", "parcela": "parcelamento", "vezes": "parcelamento",
    "desconto": "cupom", "promocao": "cupom", "barato": "cupom",
    "gratis": "gratuito", "cancelar": "cancelamento", "rastrear": "rastreio", "rastreamento": "rastreio",
    "vegana": "vegano", "testado": "crueldade", "animais": "crueldade",
}

# famílias de palavras → forma canônica (parcelam, parcelado, parcelas → parcelamento)
_PREFIXES = (
    ("parcel", "parcelamento"), ("devol", "devolucao"), ("estorn", "estorno"), ("reembols", "reembolso"),
    ("cancel", "cancelamento"), ("rastre", "rastreio"), ("entreg", "entrega"), ("arrepend", "arrependimento"),
    ("troc", "troca"), ("alerg", "alergia"), ("hidrat", "hidratante"),
)

_SUFFIXES = ("amente", "mente", "coes", "soes", "ais", "eis", "oes", "aes", "ns", "es", "s")


def _stem(token: str) -> str:
    if len(token) <= 4:
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 4:
            if suf in ("coes", "soes"):
                return token[: -len(suf)] + suf[0] + "ao"
            if suf in ("oes", "aes"):
                return token[: -len(suf)] + "ao"
            return token[: -len(suf)]
    return token


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in re.findall(r"[a-z0-9]+", normalize(text)):
        if raw in _STOPWORDS or len(raw) < 2:
            continue
        raw = _SYNONYMS.get(raw, raw)
        raw = next((canon for prefix, canon in _PREFIXES if raw.startswith(prefix)), raw)
        tokens.append(_stem(raw))
    return tokens


@dataclass
class Chunk:
    article_id: int
    title: str
    category: str
    text: str
    tokens: list[str]


@dataclass
class Hit:
    article_id: int
    title: str
    category: str
    text: str
    score: float  # 0..1 (normalizado)

    def as_dict(self) -> dict:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "category": self.category,
            "text": self.text,
            "score": round(self.score, 3),
        }


class KnowledgeIndex:
    K1, B = 1.4, 0.72

    def __init__(self) -> None:
        self._lock = Lock()
        self._version = -1
        self.dirty_version = 0
        self.chunks: list[Chunk] = []
        self._df: Counter = Counter()
        self._avgdl = 1.0

    def invalidate(self) -> None:
        self.dirty_version += 1

    def _build(self, db: Session) -> None:
        articles = db.scalars(select(KnowledgeArticle).where(KnowledgeArticle.active.is_(True))).all()
        chunks: list[Chunk] = []
        for art in articles:
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", art.content) if p.strip()]
            for p in paragraphs:
                # título e tags entram nos tokens: dão contexto a parágrafos curtos
                toks = tokenize(f"{art.title} {' '.join(art.tags or [])}") + tokenize(p)
                chunks.append(Chunk(art.id, art.title, art.category, p, toks))
        self.chunks = chunks
        self._df = Counter(t for c in chunks for t in set(c.tokens))
        self._avgdl = sum(len(c.tokens) for c in chunks) / max(1, len(chunks))
        self._version = self.dirty_version

    def search(self, db: Session, query: str, k: int = 3, min_score: float = 0.0) -> list[Hit]:
        with self._lock:
            if self._version != self.dirty_version or not self.chunks:
                self._build(db)
        q_tokens = tokenize(query)
        if not q_tokens or not self.chunks:
            return []

        n = len(self.chunks)
        raw: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            tf = Counter(chunk.tokens)
            dl = len(chunk.tokens)
            s = 0.0
            for t in set(q_tokens):
                if t not in tf:
                    continue
                idf = math.log(1 + (n - self._df[t] + 0.5) / (self._df[t] + 0.5))
                s += idf * tf[t] * (self.K1 + 1) / (tf[t] + self.K1 * (1 - self.B + self.B * dl / self._avgdl))
            if s > 0:
                raw.append((s, chunk))

        raw.sort(key=lambda x: x[0], reverse=True)
        hits: list[Hit] = []
        seen: set[int] = set()
        for s, chunk in raw:
            # cobertura da consulta + magnitude do BM25 → confiança 0..1
            coverage = len(set(q_tokens) & set(chunk.tokens)) / len(set(q_tokens))
            score = min(0.99, 0.55 * coverage + 0.45 * (s / (s + 6)))
            if score < min_score:
                continue
            # no máximo 2 trechos por artigo, para diversificar as fontes
            if chunk.article_id in seen and sum(h.article_id == chunk.article_id for h in hits) >= 2:
                continue
            seen.add(chunk.article_id)
            hits.append(Hit(chunk.article_id, chunk.title, chunk.category, chunk.text, score))
            if len(hits) >= k:
                break
        return hits


knowledge_index = KnowledgeIndex()
