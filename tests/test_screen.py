"""Tests for the paid counterparty-screen client (no real network, no wallets)."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

import importlib

from a2a_protocol_core import x402_pay
from a2a_protocol_core.screen import (
    ScreenResult,
    fetch_screen_requirement_header,
    screen,
    screen_with_payment_header,
)
from a2a_protocol_core.x402_pay import X402PayError

# The submodule, fetched explicitly — the package attribute `screen` is the function.
screen_mod = importlib.import_module("a2a_protocol_core.screen")


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


# The v2 PaymentRequired envelope the server emits on the AVM (USDC) path.
AVM_ENVELOPE = {
    "x402Version": 2,
    "accepts": [
        {
            "scheme": "exact",
            "network": "algorand:mainnet-v1.0",
            "asset": "31566704",
            "amount": "10000",
            "payTo": "ALGOADDR",
            "maxTimeoutSeconds": 600,
            "extra": {"feePayer": "FEEPAYER", "invoiceId": "inv-screen-1", "decimals": 6},
        }
    ],
    "resource": {"url": "https://api.dnsofmoney.com/api/v1/x402/screen/pay:vendor.alpha"},
}

ATTESTATION = {
    "@context": ["https://www.w3.org/ns/credentials/v2"],
    "type": ["VerifiableCredential", "CounterpartyScreenCredential"],
    "issuer": "did:web:dnsofmoney.com",
    "credentialSubject": {
        "target": {"input": "pay:vendor.alpha", "kind": "alias", "resolved": True},
        "screen": {"verdict": "CLEAR", "addresses_screened": 2},
        "fee_settlement": {"txid": "ALGOTX1", "invoiceId": "inv-screen-1"},
    },
    "proof": {"type": "DataIntegrityProof", "cryptosuite": "eddsa-jcs-2022", "proofValue": "zSIG"},
}

SETTLED = {
    "success": True,
    "settled": True,
    "idempotent": False,
    "transaction_id": "txn-uuid",
    "attestation": ATTESTATION,
    "proof": {"success": True, "transaction": "ALGOTX1", "network": "algorand:mainnet-v1.0", "payer": "PAYER"},
}


def test_fetch_screen_requirement_header():
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr(AVM_ENVELOPE)})])
    raw = fetch_screen_requirement_header(base_url="https://api.x", target="pay:vendor.alpha", session=http)
    assert json.loads(base64.b64decode(raw)) == AVM_ENVELOPE
    call = http.calls[0]
    assert call["url"].endswith("/api/v1/x402/screen/pay:vendor.alpha")
    assert call["params"] == {"currency": "USDC"}


def test_fetch_screen_requirement_not_402():
    http = _Session([_Resp(404, text="not enabled")])
    with pytest.raises(X402PayError, match="expected a 402"):
        fetch_screen_requirement_header(base_url="https://api.x", target="t", session=http)


def test_screen_usdc_end_to_end(monkeypatch):
    http = _Session(
        [
            _Resp(402, headers={"PAYMENT-REQUIRED": _hdr(AVM_ENVELOPE)}),
            _Resp(200, body=SETTLED),
        ]
    )
    built = {}

    def fake_builder(raw_header, *, mnemonic=None, secret_key=None):
        built["raw"] = raw_header
        built["mnemonic"] = mnemonic
        return "XPAYMENT-HEADER"

    monkeypatch.setattr(x402_pay, "build_avm_payment_header", fake_builder)

    result = screen(
        base_url="https://api.x",
        target="pay:vendor.alpha",
        api_key="k1",
        algorand_mnemonic="words " * 25,
        session=http,
    )
    assert isinstance(result, ScreenResult)
    assert result.verdict == "CLEAR"
    assert result.summary.signed is True
    assert result.proof["transaction"] == "ALGOTX1"
    assert result.verification is None  # verify not requested
    # the builder saw the raw 402 header
    assert json.loads(base64.b64decode(built["raw"])) == AVM_ENVELOPE
    # the settle leg carried the payment + tenant key
    settle = http.calls[1]
    assert settle["headers"]["X-PAYMENT"] == "XPAYMENT-HEADER"
    assert settle["headers"]["X-API-Key"] == "k1"
    assert settle["params"] == {"currency": "USDC"}


def test_screen_xrp_path(monkeypatch):
    req = {
        "payTo": "rPayee",
        "maxAmountRequired": "100000",
        "network": "xrpl:0",
        "extra": {"invoiceId": "inv-x", "sourceTag": 715400001},
    }
    http = _Session(
        [
            _Resp(402, headers={"PAYMENT-REQUIRED": _hdr(req)}),
            _Resp(200, body=SETTLED),
        ]
    )
    signed = {}

    def fake_sign(*, pay_to, drops, seed, rpc_url, invoice_id, source_tag):
        signed.update(pay_to=pay_to, drops=drops, invoice_id=invoice_id, source_tag=source_tag)
        return "XRPLHASH", "rPayer"

    monkeypatch.setattr(x402_pay, "_sign_and_submit_xrp", fake_sign)

    result = screen(
        base_url="https://api.x", target="rSomeAddr", api_key="k1", currency="XRP", xrpl_seed="sSeed", session=http
    )
    assert result.verdict == "CLEAR"
    # invoice binding: hashed invoiceId from the requirement's extra block
    assert signed["invoice_id"] == hashlib.sha256(b"inv-x").hexdigest().upper()
    assert signed["source_tag"] == 715400001
    assert signed["pay_to"] == "rPayee"


def test_screen_xrp_requires_seed():
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr({"payTo": "r", "maxAmountRequired": "1"})})])
    with pytest.raises(X402PayError, match="xrpl_seed"):
        screen(base_url="https://api.x", target="t", api_key="k", currency="XRP", session=http)


def test_screen_unsupported_currency():
    http = _Session([_Resp(402, headers={"PAYMENT-REQUIRED": _hdr({})})])
    with pytest.raises(X402PayError, match="unsupported fee currency"):
        screen(base_url="https://api.x", target="t", api_key="k", currency="DOGE", session=http)


def test_screen_settle_failure():
    http = _Session([_Resp(401, text="X-API-Key required")])
    with pytest.raises(X402PayError, match="screen settle failed 401"):
        screen_with_payment_header(base_url="https://api.x", target="t", payment_header="H", api_key="", session=http)


def test_screen_verify_calls_verifier(monkeypatch):
    http = _Session([_Resp(200, body=SETTLED)])
    seen = {}

    def fake_verify(attestation, *, expected_issuer=None, session=None, timeout=None):
        seen["attestation"] = attestation
        seen["expected_issuer"] = expected_issuer
        return "VERIFIED-SENTINEL"

    monkeypatch.setattr(screen_mod, "verify_attestation", fake_verify)
    result = screen_with_payment_header(
        base_url="https://api.x",
        target="t",
        payment_header="H",
        api_key="k",
        verify=True,
        expected_issuer="did:web:dnsofmoney.com",
        session=http,
    )
    assert result.verification == "VERIFIED-SENTINEL"
    assert seen["attestation"] == ATTESTATION
    assert seen["expected_issuer"] == "did:web:dnsofmoney.com"


def test_screen_verify_real_signature():
    """Full integration: signed fixture + did:web fetch through the same session."""
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from test_attestation_verify import _b58encode, _sign
    from a2a_protocol_core.attestation_verify import _ED25519_PUB_MULTICODEC

    key = Ed25519PrivateKey.generate()
    issuer = "did:web:dnsofmoney.com"
    vm = f"{issuer}#key-1"
    signed_att = _sign(
        {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential", "CounterpartyScreenCredential"],
            "issuer": issuer,
            "credentialSubject": {"screen": {"verdict": "CLEAR"}},
        },
        key,
        vm,
    )
    did_doc = {
        "id": issuer,
        "verificationMethod": [
            {
                "id": vm,
                "type": "Multikey",
                "controller": issuer,
                "publicKeyMultibase": "z" + _b58encode(_ED25519_PUB_MULTICODEC + key.public_key().public_bytes_raw()),
            }
        ],
        "assertionMethod": [vm],
    }
    body = dict(SETTLED, attestation=signed_att)
    http = _Session([_Resp(200, body=body), _Resp(200, body=did_doc)])
    result = screen_with_payment_header(
        base_url="https://api.x", target="t", payment_header="H", api_key="k", verify=True, session=http
    )
    assert result.verification.verified is True
    assert result.verification.issuer == issuer
    assert http.calls[1]["url"] == "https://dnsofmoney.com/.well-known/did.json"
