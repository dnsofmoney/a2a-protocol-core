import pytest
from pydantic import ValidationError

from a2a_protocol_core.schemas import A2APaymentHookRequest


def test_valid_request():
    req = A2APaymentHookRequest(
        job_id="job-1",
        provider_pay_address="pay:agent.compute",
        requester_pay_address="pay:vendor.alpha",
        amount="2.50",
        semantic_hash="abc123",
    )
    assert req.currency == "USD"
    assert str(req.amount) == "2.50"


def test_invalid_pay_uri_rejected():
    with pytest.raises(ValidationError):
        A2APaymentHookRequest(
            job_id="job-1",
            provider_pay_address="not-a-pay-uri",
            requester_pay_address="pay:vendor.alpha",
            amount="1",
            semantic_hash="abc",
        )


def test_empty_semantic_hash_rejected():
    with pytest.raises(ValidationError):
        A2APaymentHookRequest(
            job_id="job-1",
            provider_pay_address="pay:agent.compute",
            requester_pay_address="pay:vendor.alpha",
            amount="1",
            semantic_hash="   ",
        )


def test_json_roundtrip_serializes_decimal():
    req = A2APaymentHookRequest(
        job_id="job-1",
        provider_pay_address="pay:agent.compute",
        requester_pay_address="pay:vendor.alpha",
        amount="2.50",
        semantic_hash="abc",
    )
    payload = req.model_dump_json()
    assert "2.50" in payload
