def _send(client, channel, text, **ident):
    r = client.post(f"/api/channels/{channel}/inbound", json={"text": text, **ident})
    assert r.status_code == 200, r.text
    return r.json()


def _conv(client, conv_id):
    return client.get(f"/api/conversations/{conv_id}").json()


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "offline"


def test_seed_has_live_queue_and_history(client):
    data = client.get("/api/conversations", params={"status": "open"}).json()
    assert data["counts"]["waiting"] >= 2
    assert data["counts"]["human"] >= 1
    assert data["counts"]["resolved"] > 100


def test_order_tracking_uses_tool_and_detects_delay(client, personas):
    res = _send(client, "webchat", "onde está meu pedido AUR-10482?", contact_id=personas["juliana"]["id"])
    meta = res["reply"]["meta"]
    assert meta["nlu"]["intent"] == "rastreio"
    assert meta["tool_calls"][0]["name"] == "consultar_pedido"
    assert "passou do prazo" in res["reply"]["content"]


def test_orders_from_other_customers_are_not_exposed(client, personas):
    res = _send(client, "webchat", "status do pedido AUR-10533", contact_id=personas["rafael"]["id"])
    result = res["reply"]["meta"]["tool_calls"][0]["result"]
    assert result["encontrado"] is False


def test_knowledge_answer_cites_sources(client):
    res = _send(client, "webchat", "Vocês parcelam no cartão?", name="Visitante Teste", email="visit@teste.com")
    meta = res["reply"]["meta"]
    assert meta["sources"][0]["title"] == "Formas de pagamento e parcelamento"
    assert "6x" in res["reply"]["content"]


def test_exchange_flow_opens_ticket_with_protocol(client, personas):
    fid = personas["fernanda"]["id"]
    _send(client, "whatsapp", "O sérum chegou vazando, quero trocar", contact_id=fid)
    res = _send(client, "whatsapp", "é o pedido AUR-10511", contact_id=fid)
    calls = {c["name"]: c for c in res["reply"]["meta"]["tool_calls"]}
    assert "abrir_solicitacao" in calls
    assert calls["abrir_solicitacao"]["result"]["protocolo"].startswith("OF-")
    tickets = client.get("/api/tickets").json()
    assert any(t["order_code"] == "AUR-10511" for t in tickets)


def test_cancel_paid_order(client, personas):
    res = _send(client, "email", "Quero cancelar o pedido AUR-10533", contact_id=personas["marcos"]["id"])
    assert "cancelamento" in res["reply"]["content"].lower()
    assert res["reply"]["content"].startswith("Olá, Marcos!")  # formato de e-mail


def test_human_request_hands_off_with_summary(client):
    res = _send(client, "webchat", "quero falar com um atendente", name="Cliente Handoff", email="h@teste.com")
    assert res["reply"]["meta"]["guardrail"] == "pedido_atendente"
    conv = _conv(client, res["conversation_id"])["conversation"]
    assert conv["status"] == "waiting"
    assert conv["summary"]


def test_critical_terms_escalate_as_urgent(client):
    res = _send(client, "whatsapp", "vou abrir reclamação no Reclame Aqui", name="Cliente Bravo", phone="5511900000001")
    conv = _conv(client, res["conversation_id"])["conversation"]
    assert conv["priority"] == "urgent"
    assert "risco-reputacao" in conv["tags"]


def test_thanks_resolves_and_csat_is_recorded(client):
    ident = {"name": "Cliente CSAT", "phone": "5511900000002"}
    _send(client, "whatsapp", "qual o valor mínimo para frete grátis?", **ident)
    res = _send(client, "whatsapp", "obrigada!", **ident)
    conv_id = res["conversation_id"]
    assert _conv(client, conv_id)["conversation"]["status"] == "resolved"
    _send(client, "whatsapp", "5", **ident)
    conv = _conv(client, conv_id)["conversation"]
    assert conv["csat"] == 5
    assert conv["resolved_by"] == "ai"


def test_agent_takeover_reply_and_resolve(client):
    res = _send(client, "webchat", "quero falar com um humano", name="Cliente Takeover", email="t@teste.com")
    cid = res["conversation_id"]
    r = client.post(f"/api/conversations/{cid}/messages", json={"agent_id": 2, "content": "Oi! Posso ajudar?"})
    assert r.status_code == 200
    assert _conv(client, cid)["conversation"]["status"] == "human"

    # com humano no caso, a IA não responde
    assert _send(client, "webchat", "tudo bem", email="t@teste.com")["reply"] is None

    suggestion = client.post(f"/api/conversations/{cid}/copilot/suggest").json()
    assert suggestion["text"]

    assert client.post(f"/api/conversations/{cid}/resolve").status_code == 200
    conv = _conv(client, cid)["conversation"]
    assert conv["status"] == "resolved" and conv["resolved_by"] == "human"


def test_knowledge_crud_updates_search(client):
    art = client.post("/api/knowledge", json={
        "title": "Programa de revendedoras", "category": "Institucional",
        "content": "Revendedoras cadastradas têm 35% de desconto no atacado a partir de 12 unidades.",
        "tags": ["revenda", "atacado"],
    }).json()
    found = client.post("/api/knowledge/search", json={"query": "desconto para revendedora no atacado"}).json()
    assert found["results"][0]["article_id"] == art["id"]
    assert client.delete(f"/api/knowledge/{art['id']}").status_code == 204


def test_analytics_overview_shape(client):
    ov = client.get("/api/analytics/overview").json()
    assert ov["kpis"]["conversations"] > 0
    assert 0 <= ov["kpis"]["ai_resolution_rate"] <= 100
    assert len(ov["daily"]) == 30
    assert len(ov["heatmap"]) == 7 * 24


def test_flow_toggle_disables_behavior(client):
    flows = {f["key"]: f for f in client.get("/api/flows").json()}
    fid = flows["escalonamento_critico"]["id"]
    client.patch(f"/api/flows/{fid}", json={"active": False})
    try:
        res = _send(client, "webchat", "vou no procon", name="Sem Fluxo", email="sf@teste.com")
        assert res["reply"]["meta"]["guardrail"] != "termo_critico"
    finally:
        client.patch(f"/api/flows/{fid}", json={"active": True})


def test_whatsapp_webhook(client):
    verify = client.get("/webhooks/whatsapp", params={
        "hub.mode": "subscribe", "hub.verify_token": "omniflow-verify", "hub.challenge": "42"})
    assert verify.text == "42"
    payload = {"entry": [{"changes": [{"value": {
        "contacts": [{"wa_id": "5511955554444", "profile": {"name": "Maria WhatsApp"}}],
        "messages": [{"from": "5511955554444", "type": "text", "text": {"body": "vocês entregam em Manaus?"}}],
    }}]}]}
    assert client.post("/webhooks/whatsapp", json=payload).json() == {"processed": 1}
