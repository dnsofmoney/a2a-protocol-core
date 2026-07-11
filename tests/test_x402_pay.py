"""Tests for the one-call x402 pay-path (no real network, no xrpl-py needed)."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from a2a_protocol_core import x402_pay
from a2a_protocol_core.x402_pay import (
    X402PayError,
    attest_settled_payment,
    build_x_payment_header,
    decode_payment_required,
    fetch_requirement,
    pay_alias_xrp,
    summarize_attestation,
)


# ── Fakes ────────────────────────────────────────────────────────────────────


class _Resp:
    def __init__(self, status_code, *, headers=None, body=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body
        self.text = text

    def json(self):
        return self._body


class _Session:
    """Queue of responses; records each .get(...) call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return self._responses.pop(0)


def _pr_header(req: dict) -> str:
    return base64.b64encode(json.dumps(req).encode()).decode()


REQ = {"payTo": "rPayeeDest", "maxAmountRequired": "100000", "network": "xrpl:0", "invoiceId": "inv-1"}

SETTLED_BODY = {
    "success": True,
    "settled": True,
    "idempotent": False,
    "transaction_id": "txn-uuid",
    "attestation": {
        "type": "fas1.resolve-verify-screen",
        "settlement": {"txid": "TXHASH", "amount": "0.10"},
        "screen": {"verdict": "CLEAR", "payee": {"verdict": "CLEAR"}, "payer": {"verdict": "CLEAR"}},
    },
    "proof": {"transaction": "TXHASH", "payer": "rPayer", "network": "xrpl:0"},
}


# ── Pure helpers ─────────────────────────────────────────────────────────────


def test_decode_payment_required_roundtrip():
    assert decode_payment_required(_pr_header(REQ)) == REQ


def test_build_x_payment_header_shape():
    decoded = json.loads(base64.b64decode(build_x_payment_header("TX", "rPayer")))
    assert decoded == {"x402Version": 2, "payload": {"txHash": "TX", "payer": "rPayer"}}
    # payer omitted when absent
    decoded2 = json.loads(base64.b64decode(build_x_payment_header("TX")))
    assert decoded2["payload"] == {"txHash": "TX"}


def test_invoice_id_hash_matches_server_rule():
    assert x402_pay.invoice_id_hash("inv-1") == hashlib.sha256(b"inv-1").hexdigest().upper()


def test_summarize_attestation_flat_and_signed():
    flat = summarize_attestation(SETTLED_BODY["attestation"])
    assert (flat.verdict, flat.payee_verdict, flat.tx_id, flat.signed) == ("CLEAR", "CLEAR", "TXHASH", False)
    signed = summarize_attestation({"proof": {"x": 1}, "credentialSubject": SETTLED_BODY["attestation"]})
    assert signed.signed is True and signed.verdict == "CLEAR"


# ── fetch_requirement ────────────────────────────────────────────────────────


def test_fetch_requirement_ok():
    sess = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _pr_header(REQ)})])
    req = fetch_requirement(base_url="https://x.test", alias="pay:v.alpha", amount_xrp="0.10", session=sess)
    assert req == REQ
    assert sess.calls[0]["params"] == {"amount": "0.10", "currency": "XRP"}


def test_fetch_requirement_non_402_raises():
    sess = _Session([_Resp(400, text="not payable")])
    with pytest.raises(X402PayError, match="expected a 402"):
        fetch_requirement(base_url="https://x.test", alias="pay:v.alpha", amount_xrp="1", session=sess)


def test_fetch_requirement_missing_header_raises():
    sess = _Session([_Resp(402, headers={})])
    with pytest.raises(X402PayError, match="missing the PAYMENT-REQUIRED"):
        fetch_requirement(base_url="https://x.test", alias="pay:v.alpha", amount_xrp="1", session=sess)


# ── pay_alias_xrp (signing monkeypatched — no xrpl) ──────────────────────────


def test_pay_alias_xrp_full_flow(monkeypatch):
    captured = {}

    def fake_sign(*, pay_to, drops, seed, rpc_url, invoice_id, source_tag):
        captured.update(pay_to=pay_to, drops=drops, seed=seed, invoice_id=invoice_id, source_tag=source_tag)
        return "TXHASH", "rPayer"

    monkeypatch.setattr(x402_pay, "_sign_and_submit_xrp", fake_sign)
    sess = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _pr_header(REQ)}), _Resp(200, body=SETTLED_BODY)])

    result = pay_alias_xrp(
        base_url="https://x.test", alias="pay:v.alpha", amount_xrp="0.10", seed="sSEED", api_key="k", session=sess
    )

    # signed the right thing: payTo, drops, and the invoice-bound InvoiceID
    assert captured["pay_to"] == "rPayeeDest"
    assert captured["drops"] == "100000"
    assert captured["invoice_id"] == hashlib.sha256(b"inv-1").hexdigest().upper()
    # settle leg carried the proof header + api key
    settle_headers = sess.calls[1]["headers"]
    assert settle_headers["X-API-Key"] == "k"
    assert "X-PAYMENT" in settle_headers
    # parsed result
    assert result.tx_hash == "TXHASH"
    assert result.payer == "rPayer"
    assert result.settled is True and result.idempotent is False
    assert result.summary.verdict == "CLEAR"


def test_pay_alias_xrp_settle_failure_raises(monkeypatch):
    monkeypatch.setattr(x402_pay, "_sign_and_submit_xrp", lambda **_: ("TX", "rPayer"))
    sess = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _pr_header(REQ)}), _Resp(402, text="bad proof")])
    with pytest.raises(X402PayError, match="settle leg failed 402"):
        pay_alias_xrp(
            base_url="https://x.test", alias="pay:v.alpha", amount_xrp="0.10", seed="s", api_key="k", session=sess
        )


def test_pay_alias_xrp_no_invoice_no_binding(monkeypatch):
    captured = {}
    monkeypatch.setattr(x402_pay, "_sign_and_submit_xrp", lambda **kw: captured.update(kw) or ("TX", "rP"))
    req_no_inv = {"payTo": "rD", "maxAmountRequired": "5", "network": "xrpl:0"}
    sess = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _pr_header(req_no_inv)}), _Resp(200, body=SETTLED_BODY)])
    pay_alias_xrp(base_url="https://x.test", alias="pay:v", amount_xrp="1", seed="s", api_key="k", session=sess)
    assert captured["invoice_id"] is None and captured["source_tag"] is None


# ── attest_settled_payment (bring-your-own tx) ───────────────────────────────


def test_attest_settled_payment_ok():
    sess = _Session([_Resp(200, body=SETTLED_BODY)])
    result = attest_settled_payment(
        base_url="https://x.test", alias="pay:v.alpha", amount_xrp="0.10", tx_hash="TXHASH", api_key="k", session=sess
    )
    assert result.tx_hash == "TXHASH" and result.summary.verdict == "CLEAR"
    # single call = settle only (no challenge)
    assert len(sess.calls) == 1
    assert "X-PAYMENT" in sess.calls[0]["headers"]
