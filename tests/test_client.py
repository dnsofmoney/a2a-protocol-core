"""Tests for the A2A-041 payment-hook client — previously the only untested module."""

from __future__ import annotations

import json
import uuid

import pytest

from a2a_protocol_core import A2AClientError, A2APaymentHookClient


class _Resp:
    def __init__(self, status_code, *, body=None, text=""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self._responses = list(responses)
        self.get_calls = []
        self.post_calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.get_calls.append({"url": url, "headers": headers})
        return self._responses.pop(0)

    def post(self, url, data=None, headers=None, verify=None, timeout=None):
        self.post_calls.append({"url": url, "data": data, "headers": headers})
        return self._responses.pop(0)


HOOK_RESPONSE = {
    "hook_id": str(uuid.uuid4()),
    "job_id": "job-1",
    "resolution": {"provider_address": "rProv", "rail": "xrpl"},
    "settlement_result": {"status": "settled", "rail": "xrpl", "amount": "2.50", "currency": "USD"},
    "iso_message_ref": "pacs008-001",
    "created_at": "2026-07-20T00:00:00Z",
}

CAPABILITIES = {"binding_version": "1.0", "supported_schemes": ["A2A-041"], "protocol_versions": ["1.0"]}


def _client(session, **kw):
    return A2APaymentHookClient(base_url="https://api.x/", session=session, **kw)


def test_trigger_happy_path():
    http = _Session([_Resp(200, body=HOOK_RESPONSE)])
    out = _client(http, api_key="k1").trigger(
        job_id="job-1",
        provider_pay_address="pay:agent.compute",
        requester_pay_address="pay:vendor.alpha",
        amount="2.50",
        semantic_hash="abc123",
    )
    assert out.job_id == "job-1"
    assert out.settlement_result.status == "settled"
    call = http.post_calls[0]
    assert call["url"] == "https://api.x/v1/a2a/payment-hook"  # trailing slash stripped
    assert call["headers"]["X-API-Key"] == "k1"
    sent = json.loads(call["data"])
    assert sent["provider_pay_address"] == "pay:agent.compute"
    assert sent["amount"] == "2.50"


def test_trigger_validates_pay_uri_before_wire():
    http = _Session([])  # no response queued — the request must never hit the wire
    with pytest.raises(ValueError, match="Invalid pay: URI"):
        _client(http).trigger(
            job_id="j",
            provider_pay_address="not-a-pay-uri",
            requester_pay_address="pay:vendor.alpha",
            amount="1",
            semantic_hash="h",
        )
    assert http.post_calls == []


def test_trigger_validates_semantic_hash_before_wire():
    http = _Session([])
    with pytest.raises(ValueError, match="semantic_hash"):
        _client(http).trigger(
            job_id="j",
            provider_pay_address="pay:agent.compute",
            requester_pay_address="pay:vendor.alpha",
            amount="1",
            semantic_hash="   ",
        )
    assert http.post_calls == []


def test_trigger_http_error_carries_context():
    http = _Session([_Resp(422, text='{"detail": "duplicate job"}')])
    with pytest.raises(A2AClientError, match="payment hook failed 422") as exc:
        _client(http).trigger(
            job_id="j",
            provider_pay_address="pay:agent.compute",
            requester_pay_address="pay:vendor.alpha",
            amount="1",
            semantic_hash="h",
        )
    assert exc.value.status_code == 422
    assert "duplicate job" in exc.value.body


def test_capabilities_happy_path():
    http = _Session([_Resp(200, body=CAPABILITIES)])
    caps = _client(http, api_key="k1").capabilities()
    assert caps.binding_version == "1.0"
    assert http.get_calls[0]["url"] == "https://api.x/v1/a2a/capabilities"
    assert http.get_calls[0]["headers"]["X-API-Key"] == "k1"


def test_capabilities_retries_on_503(monkeypatch):
    monkeypatch.setattr("a2a_protocol_core._retry.time.sleep", lambda s: None)
    http = _Session([_Resp(503, text="unavailable"), _Resp(200, body=CAPABILITIES)])
    caps = _client(http).capabilities()
    assert caps.binding_version == "1.0"
    assert len(http.get_calls) == 2  # transient 503 retried once


def test_capabilities_error_carries_context(monkeypatch):
    monkeypatch.setattr("a2a_protocol_core._retry.time.sleep", lambda s: None)
    http = _Session([_Resp(401, text="key required")])
    with pytest.raises(A2AClientError) as exc:
        _client(http).capabilities()
    assert exc.value.status_code == 401  # 4xx is a real answer — not retried
    assert len(http.get_calls) == 1


def test_no_api_key_no_header():
    http = _Session([_Resp(200, body=CAPABILITIES)])
    _client(http).capabilities()
    assert "X-API-Key" not in http.get_calls[0]["headers"]
