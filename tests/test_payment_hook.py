"""Tests for A2A-041 Payment Hook — A2A compute marketplace to settlement."""


def test_payment_hook_success(client):
    resp = client.post("/v1/a2a/payment-hook", json={
        "task_id": "task-001",
        "agent_id": "agent-compute-001",
        "payee_alias": "pay:agent.compute",
        "amount": "0.69",
        "currency": "USD",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SETTLED"
    assert data["payee_alias"] == "pay:agent.compute"
    assert data["rail"] == "XRPL"
    assert data["hook_id"].startswith("a2a-041-")
    assert data["iso_ref"] == "pacs.008.001.08"


def test_payment_hook_deterministic_id(client):
    """Same inputs produce same hook_id (idempotency)."""
    body = {
        "task_id": "task-002",
        "agent_id": "agent-001",
        "payee_alias": "pay:vendor.alpha",
        "amount": "10.00",
    }
    r1 = client.post("/v1/a2a/payment-hook", json=body)
    r2 = client.post("/v1/a2a/payment-hook", json=body)
    assert r1.json()["hook_id"] == r2.json()["hook_id"]


def test_payment_hook_invalid_alias(client):
    resp = client.post("/v1/a2a/payment-hook", json={
        "task_id": "task-003",
        "agent_id": "agent-001",
        "payee_alias": "not-a-pay-uri",
        "amount": "5.00",
    })
    assert resp.status_code == 422


def test_payment_hook_unknown_alias(client):
    resp = client.post("/v1/a2a/payment-hook", json={
        "task_id": "task-004",
        "agent_id": "agent-001",
        "payee_alias": "pay:nonexistent.alias",
        "amount": "1.00",
    })
    assert resp.status_code == 404


def test_payment_hook_vendor_rail(client):
    """Vendor aliases resolve to FEDNOW (preferred rail)."""
    resp = client.post("/v1/a2a/payment-hook", json={
        "task_id": "task-005",
        "agent_id": "agent-001",
        "payee_alias": "pay:vendor.alpha",
        "amount": "100.00",
    })
    assert resp.status_code == 200
    assert resp.json()["rail"] == "FEDNOW"
