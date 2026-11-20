import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import KnowledgeArticle
from app.schemas import ArticleIn, SearchQuery
from app.serializers import article_out
from app.services.retrieval import knowledge_index
from app.utils import utcnow

router = APIRouter(prefix="/api/knowledge", tags=["Base de conhecimento"])


@router.get("")
def list_articles(db: Session = Depends(get_db)):
    arts = db.scalars(select(KnowledgeArticle).order_by(KnowledgeArticle.category, KnowledgeArticle.title)).all()
    return [article_out(a) for a in arts]


@router.post("", status_code=201)
def create_article(body: ArticleIn, db: Session = Depends(get_db)):
    art = KnowledgeArticle(**body.model_dump())
    db.add(art)
    db.commit()
    knowledge_index.invalidate()
    return article_out(art)


@router.put("/{art_id}")
def update_article(art_id: int, body: ArticleIn, db: Session = Depends(get_db)):
    art = db.get(KnowledgeArticle, art_id)
    if not art:
        raise HTTPException(404, "Artigo não encontrado")
    for k, v in body.model_dump().items():
        setattr(art, k, v)
    art.updated_at = utcnow()
    db.commit()
    knowledge_index.invalidate()
    return article_out(art)


@router.delete("/{art_id}", status_code=204)
def delete_article(art_id: int, db: Session = Depends(get_db)):
    art = db.get(KnowledgeArticle, art_id)
    if not art:
        raise HTTPException(404, "Artigo não encontrado")
    db.delete(art)
    db.commit()
    knowledge_index.invalidate()


@router.post("/search", summary="Playground: testa a busca semântica usada pela IA")
def search(body: SearchQuery, db: Session = Depends(get_db)):
    start = time.perf_counter()
    hits = knowledge_index.search(db, body.query, k=5)
    return {
        "query": body.query,
        "took_ms": round((time.perf_counter() - start) * 1000, 2),
        "chunks_indexed": len(knowledge_index.chunks),
        "results": [h.as_dict() for h in hits],
    }
