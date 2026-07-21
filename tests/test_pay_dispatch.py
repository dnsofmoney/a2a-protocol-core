"""Tests for the USDC-on-Algorand pay path and the rail-dispatching pay_alias."""

from __future__ import annotations

import base64
import json

import pytest

from a2a_protocol_core import x402_pay
from a2a_protocol_core.x402_pay import (
    X402PayError,
    fetch_requirement_header,
    pay_alias,
    pay_alias_usdc_algorand,
)


class _Resp:
    def __init__(self, status_code, *, headers=None, body=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body
        self.text = text

    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return self._responses.pop(0)


def _hdr(payload: dict) -> str:
    return base64.b64encode(json.dumps(payload).encode()).decode()


ENVELOPE = {
    "x402Version": 2,
    "accepts": [{"scheme": "exact", "network": "algorand:mainnet-v1.0", "amount": "10000", "payTo": "ALGOADDR"}],
    "resource": {"url": "https://api.x/api/v1/x402/pay/pay:dnsofmoney"},
}

SETTLED = {
    "success": True,
    "settled": True,
    "idempotent": False,
    "attestation": {"credentialSubject": {"screen": {"verdict": "CLEAR"}}, "proof": {"proofValue": "z1"}},
    "proof": {"success": True, "transaction": "ALGOTX9", "network": "algorand:mainnet-v1.0", "payer": "PAYER"},
}


# ── fetch_requirement_header ──────────────────────────────────────────────────


def test_fetch_requirement_header_quotes_declared_price():
    """Omitting amount asks the priced endpoint to quote its own (enforced) price."""
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr(ENVELOPE)})])
    raw = fetch_requirement_header(base_url="https://api.x", alias="pay:dnsofmoney", session=http)
    assert json.loads(base64.b64decode(raw)) == ENVELOPE
    assert http.calls[0]["params"] == {"currency": "USDC"}  # no amount named by the payer


def test_fetch_requirement_header_with_amount():
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr(ENVELOPE)})])
    fetch_requirement_header(base_url="https://api.x", alias="pay:a", amount="1.5", session=http)
    assert http.calls[0]["params"] == {"currency": "USDC", "amount": "1.5"}


def test_fetch_requirement_header_not_402():
    http = _Session([_Resp(200, body={})])
    with pytest.raises(X402PayError, match="expected a 402"):
        fetch_requirement_header(base_url="https://api.x", alias="pay:a", session=http)


def test_fetch_requirement_header_missing_header():
    http = _Session([_Resp(402, headers={})])
    with pytest.raises(X402PayError, match="missing the PAYMENT-REQUIRED"):
        fetch_requirement_header(base_url="https://api.x", alias="pay:a", session=http)


# ── pay_alias_usdc_algorand ───────────────────────────────────────────────────


def test_pay_usdc_end_to_end(monkeypatch):
    http = _Session(
        [
            _Resp(402, headers={"PAYMENT-REQUIRED": _hdr(ENVELOPE)}),
            _Resp(200, body=SETTLED),
        ]
    )
    monkeypatch.setattr(x402_pay, "build_avm_payment_header", lambda raw, **kw: "AVM-HEADER")

    result = pay_alias_usdc_algorand(
        base_url="https://api.x", alias="pay:dnsofmoney", api_key="k1", mnemonic="m " * 25, session=http
    )
    assert result.settled is True
    assert result.tx_hash == "ALGOTX9"
    assert result.payer == "PAYER"
    assert result.summary.verdict == "CLEAR"
    settle = http.calls[1]
    assert settle["headers"] == {"X-PAYMENT": "AVM-HEADER", "X-API-Key": "k1"}
    assert settle["params"] == {"currency": "USDC"}  # declared price — payer names no amount


def test_pay_usdc_settle_failure(monkeypatch):
    http = _Session(
        [
            _Resp(402, headers={"PAYMENT-REQUIRED": _hdr(ENVELOPE)}),
            _Resp(402, text="verification failed"),
        ]
    )
    monkeypatch.setattr(x402_pay, "build_avm_payment_header", lambda raw, **kw: "AVM-HEADER")
    with pytest.raises(X402PayError, match="settle leg failed 402"):
        pay_alias_usdc_algorand(base_url="https://api.x", alias="pay:a", api_key="k", mnemonic="m", session=http)


def test_pay_usdc_without_extra_installed_or_creds():
    """Without the [algorand] extra (or creds) the builder raises X402PayError, not ImportError."""
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr(ENVELOPE)})])
    with pytest.raises(X402PayError):
        pay_alias_usdc_algorand(base_url="https://api.x", alias="pay:a", api_key="k", session=http)


# ── pay_alias dispatcher ──────────────────────────────────────────────────────


def test_pay_alias_dispatches_usdc(monkeypatch):
    seen = {}

    def fake_usdc(**kwargs):
        seen.update(kwargs)
        return "USDC-RESULT"

    monkeypatch.setattr(x402_pay, "pay_alias_usdc_algorand", fake_usdc)
    out = pay_alias(base_url="https://api.x", alias="pay:a", api_key="k", currency="USDC", algorand_mnemonic="m")
    assert out == "USDC-RESULT"
    assert seen["mnemonic"] == "m"
    assert seen["amount_usdc"] is None


def test_pay_alias_dispatches_xrp(monkeypatch):
    seen = {}

    def fake_xrp(**kwargs):
        seen.update(kwargs)
        return "XRP-RESULT"

    monkeypatch.setattr(x402_pay, "pay_alias_xrp", fake_xrp)
    out = pay_alias(
        base_url="https://api.x", alias="pay:a", api_key="k", currency="XRP", amount="0.5", xrpl_seed="sSeed"
    )
    assert out == "XRP-RESULT"
    assert seen["amount_xrp"] == "0.5"
    assert seen["seed"] == "sSeed"


def test_pay_alias_xrp_requires_seed_and_amount():
    with pytest.raises(X402PayError, match="xrpl_seed"):
        pay_alias(base_url="https://api.x", alias="pay:a", api_key="k", currency="XRP", amount="1")
    with pytest.raises(X402PayError, match="amount"):
        pay_alias(base_url="https://api.x", alias="pay:a", api_key="k", currency="XRP", xrpl_seed="s")


def test_pay_alias_unsupported_currency():
    with pytest.raises(X402PayError, match="unsupported currency"):
        pay_alias(base_url="https://api.x", alias="pay:a", api_key="k", currency="RLUSD")
