"""Tests for A2A-021 Payment Orchestration."""


def test_payment_execution(client):
    resp = client.post("/payments", json={
        "payer_agent_id": "agent-001",
        "payee_alias": "pay:agent.compute",
        "amount": 0.69,
        "currency": "USD",
        "request_id": "REQ-001",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SETTLED"
    assert data["selected_rail"] == "XRPL"


def test_payment_unknown_alias(client):
    resp = client.post("/payments", json={
        "payer_agent_id": "agent-001",
        "payee_alias": "pay:unknown.alias",
        "amount": 1.00,
        "currency": "USD",
        "request_id": "REQ-002",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "FAILED"


def test_payment_lookup(client):
    resp = client.post("/payments", json={
        "payer_agent_id": "agent-001",
        "payee_alias": "pay:vendor.alpha",
        "amount": 50.00,
        "currency": "USD",
        "request_id": "REQ-003",
    })
    pid = resp.json()["payment_id"]
    lookup = client.get(f"/payments/{pid}")
    assert lookup.status_code == 200
    assert lookup.json()["payee_alias"] == "pay:vendor.alpha"
