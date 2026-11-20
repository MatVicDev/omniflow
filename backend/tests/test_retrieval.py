import pytest

from app.db import SessionLocal
from app.services.retrieval import knowledge_index, tokenize


def test_tokenize_normalizes_and_expands_synonyms():
    tokens = tokenize("Posso devolver os produtos?")
    assert "devolucao" in tokens
    assert "posso" not in tokens  # stopword


@pytest.mark.parametrize(
    ("query", "expected_title"),
    [
        ("como faço para trocar um produto que comprei?", "Política de trocas e devoluções"),
        ("parcelam no cartão de crédito?", "Formas de pagamento e parcelamento"),
        ("qual o valor mínimo para frete grátis", "Frete grátis"),
        ("vocês testam em animais?", "Produtos veganos e cruelty-free"),
        ("quanto tempo demora o estorno no cartão", "Estornos e reembolsos"),
    ],
)
def test_search_ranks_the_right_article_first(client, query, expected_title):
    with SessionLocal() as db:
        hits = knowledge_index.search(db, query, k=3)
    assert hits, query
    assert hits[0].title == expected_title
    assert 0 < hits[0].score <= 1


def test_search_returns_nothing_for_unrelated_query(client):
    with SessionLocal() as db:
        hits = knowledge_index.search(db, "xyzabc foobar", k=3)
    assert hits == []
