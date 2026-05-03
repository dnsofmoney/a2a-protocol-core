"""Tests for A2A-042 AP2 Mandate Bridge."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.bridges.ap2.bridge import reset_settled_mandates_for_test


def _future(seconds: int = 600) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _past(seconds: int = 60) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _mandate(**overrides) -> dict:
    """Build a valid PaymentMandate JSON body with a bound cart."""
    base = {
        "payment_mandate_contents": {
            "payment_mandate_id": "pm-001",
            "cart_mandate_hash": "sha256:cart",
            "transaction_id": "txn-001",
            "agent_identifier": "agent-shopper-001",
            "amount": "12.50",
            "currency": "USD",
            "expiry": _future(),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "user_authorization": "stub-vc",
        "bound_cart": {
            "contents": {
                "id": "cart-001",
                "merchant_name": "Acme",
                "cart_expiry": _future(),
                "amount": "12.50",
                "currency": "USD",
                "merchant_payment_alias": "pay:agent.compute",
            },
            "merchant_authorization": "stub-jwt",
        },
    }
    if "contents" in overrides:
        base["payment_mandate_contents"].update(overrides.pop("contents"))
    if "cart_contents" in overrides:
        base["bound_cart"]["contents"].update(overrides.pop("cart_contents"))
    if "bound_cart" in overrides:
        base["bound_cart"] = overrides.pop("bound_cart")
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _clean_idempotency():
    reset_settled_mandates_for_test()
    yield
    reset_settled_mandates_for_test()


def test_bridge_happy_path(client):
    resp = client.post("/v1/a2a/ap2-bridge", json=_mandate())
    assert resp.status_code == 200
    body = resp.json()
    assert body["bridge_status"] == "BRIDGED"
    assert body["mandate_id"] == "pm-001"
    assert body["transaction_id"] == "txn-001"
    hook = body["hook_response"]
    assert hook["status"] == "SETTLED"
    assert hook["payee_alias"] == "pay:agent.compute"
    assert hook["rail"] == "XRPL"
    assert hook["iso_ref"] == "pacs.008.001.08"


def test_bridge_rejects_expired_mandate(client):
    resp = client.post("/v1/a2a/ap2-bridge", json=_mandate(contents={"expiry": _past()}))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "MANDATE_EXPIRED"


def test_bridge_rejects_missing_alias(client):
    resp = client.post(
        "/v1/a2a/ap2-bridge",
        json=_mandate(cart_contents={"merchant_payment_alias": None}),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "MANDATE_NO_PAYMENT_ALIAS"


def test_bridge_rejects_no_bound_cart(client):
    resp = client.post("/v1/a2a/ap2-bridge", json=_mandate(bound_cart=None))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "MANDATE_NO_PAYMENT_ALIAS"


def test_bridge_rejects_zero_amount(client):
    resp = client.post("/v1/a2a/ap2-bridge", json=_mandate(contents={"amount": "0.00"}))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "MANDATE_AMOUNT_NON_POSITIVE"


def test_bridge_idempotent_replay_returns_409(client):
    body = _mandate()
    r1 = client.post("/v1/a2a/ap2-bridge", json=body)
    assert r1.status_code == 200
    r2 = client.post("/v1/a2a/ap2-bridge", json=body)
    assert r2.status_code == 409
    assert r2.json()["detail"] == "MANDATE_ALREADY_SETTLED"


def test_bridge_routes_vendor_alias_to_fednow(client):
    """Vendor aliases resolve to FEDNOW per A2A-031 / resolver policy."""
    resp = client.post(
        "/v1/a2a/ap2-bridge",
        json=_mandate(cart_contents={"merchant_payment_alias": "pay:vendor.alpha"}),
    )
    assert resp.status_code == 200
    assert resp.json()["hook_response"]["rail"] == "FEDNOW"
