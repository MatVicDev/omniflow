import pytest

from app.services.nlu import analyze


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("Oi, bom dia!", "saudacao"),
        ("cadê meu pedido? já faz 10 dias", "rastreio"),
        ("O sérum chegou vazando, quero trocar", "troca_devolucao"),
        ("quero cancelar minha compra", "cancelamento"),
        ("vocês aceitam pix?", "pagamento"),
        ("qual o valor do frete para o meu CEP?", "frete_prazo"),
        ("tem hidratante para pele oleosa?", "produto"),
        ("tem cupom de desconto?", "promocao"),
        ("quero falar com um atendente", "falar_humano"),
        ("muito obrigada!", "agradecimento"),
    ],
)
def test_intents(text, intent):
    assert analyze(text).intent == intent


def test_sentiment_polarity_and_negation():
    assert analyze("Amei o produto, chegou super rápido! 😍").sentiment > 0.25
    assert analyze("Péssimo atendimento, um absurdo esse descaso").sentiment < -0.5
    assert analyze("não gostei nada").sentiment <= 0
    assert analyze("O PEDIDO NÃO CHEGOU ATÉ AGORA").sentiment < 0


def test_entities_and_critical_terms():
    r = analyze("Meu pedido AUR-10482 não chegou, vou no Procon. email: ana@x.com")
    assert r.entities["order_code"] == "AUR-10482"
    assert r.entities["email"] == "ana@x.com"
    assert r.critical is True
    assert analyze("pedido 10511").entities["order_code"] == "AUR-10511"
