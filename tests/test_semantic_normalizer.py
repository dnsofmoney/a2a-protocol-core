import pytest

from a2a_protocol_core.semantic_normalizer import (
    compute_semantic_hash,
    normalize_action,
    normalize_message,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("send", "EXECUTE_PAYMENT"),
        ("pay", "EXECUTE_PAYMENT"),
        ("transfer", "EXECUTE_PAYMENT"),
        ("  Transfer ", "EXECUTE_PAYMENT"),
        ("resolve", "QUERY"),
        ("lookup", "QUERY"),
        ("verify", "VERIFY"),
        ("status", "REPORT"),
        ("EXECUTE_PAYMENT", "EXECUTE_PAYMENT"),
    ],
)
def test_normalize_action(raw, expected):
    assert normalize_action(raw) == expected


def test_normalize_action_unknown_raises():
    with pytest.raises(ValueError):
        normalize_action("frobnicate")


def test_normalize_message_does_not_mutate():
    msg = {"action": "send", "amount": "5"}
    out = normalize_message(msg)
    assert out["action"] == "EXECUTE_PAYMENT"
    assert msg["action"] == "send"  # original untouched


def test_synonyms_produce_same_semantic_hash():
    a = compute_semantic_hash(normalize_message({"action": "send", "amount": "5"}))
    b = compute_semantic_hash(normalize_message({"action": "transfer", "amount": "5"}))
    assert a == b
