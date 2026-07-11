"""
Regenerate the shared cross-language test vectors from the Python reference
implementation (the source of truth).

    python tests/vectors/generate_vectors.py

Writes ``canonical_vectors.json`` next to this file. After regenerating, copy the
identical file into the TS package
(``dns-of-money/sdk/a2a-protocol-core/test/vectors/``) so both suites assert
against the same bytes. Never hand-edit the hashes — regenerate.
"""

from __future__ import annotations

import json
from pathlib import Path

from a2a_protocol_core import (
    compute_canonical_hash,
    compute_semantic_hash,
    is_valid_pay_uri,
    normalize_action,
    normalize_message,
)

PAY_URI = [
    {"input": "pay:vendor.alpha", "valid": True},
    {"input": "pay:agent.compute", "valid": True},
    {"input": "pay:a", "valid": True},
    {"input": "pay:a.b.c.d", "valid": True},
    {"input": "pay:with-hyphen.ok", "valid": True},
    {"input": "PAY:VENDOR.ALPHA", "valid": False},
    {"input": "not-a-pay-uri", "valid": False},
    {"input": "pay:-leadinghyphen", "valid": False},
    {"input": "pay:", "valid": False},
    {"input": "pay:UPPER", "valid": False},
    {"input": "vendor.alpha", "valid": False},
]

NORM_OK = [
    {"input": "send", "output": "EXECUTE_PAYMENT"},
    {"input": "transfer", "output": "EXECUTE_PAYMENT"},
    {"input": "pay", "output": "EXECUTE_PAYMENT"},
    {"input": "payment", "output": "EXECUTE_PAYMENT"},
    {"input": "  SEND  ", "output": "EXECUTE_PAYMENT"},
    {"input": "resolve", "output": "QUERY"},
    {"input": "lookup", "output": "QUERY"},
    {"input": "verify", "output": "VERIFY"},
    {"input": "check", "output": "VERIFY"},
    {"input": "confirm", "output": "VERIFY"},
    {"input": "report", "output": "REPORT"},
    {"input": "status", "output": "REPORT"},
    {"input": "QUERY", "output": "QUERY"},
]

NORM_ERR = ["frobnicate", "", "xyz", "sendd"]

CH_CASES = {
    "base": {"action": "send", "amount": "2.50", "currency": "USD", "alias": "pay:agent.compute"},
    "synonym_transfer": {"action": "transfer", "amount": "2.50", "currency": "USD", "alias": "pay:agent.compute"},
    "synonym_pay": {"action": "pay", "amount": "2.50", "currency": "USD", "alias": "pay:agent.compute"},
    "with_noise": {
        "action": "payment",
        "amount": "2.50",
        "currency": "USD",
        "alias": "pay:agent.compute",
        "session_id": "s1",
        "request_id": "r1",
        "trace_id": "t1",
        "timestamp": "2026-06-28T00:00:00Z",
        "idempotency_key": "idem-1",
        "memo": "lunch",
        "payload_hash": "ph",
        "canonical_hash": "old",
        "created_at": "x",
        "updated_at": "y",
    },
    "unknown_action": {"action": "frobnicate", "amount": "1", "currency": "XRP"},
    "rail_included": {"action": "send", "amount": "10", "currency": "USD", "rail": "xrpl", "alias": "pay:x"},
    "preferred_rail": {"action": "send", "amount": "10", "currency": "USD", "preferred_rail": "xrpl", "alias": "pay:x"},
    "category": {
        "action": "verify",
        "amount": "5",
        "currency": "USD",
        "payment_category": "compute",
        "alias": "pay:agent.compute",
    },
    "alias_uri_variant": {"action": "send", "amount": "3", "currency": "USD", "alias_uri": "pay:agent.compute"},
    "numeric_int_amount": {"action": "send", "amount": 10, "currency": "USD", "alias": "pay:x"},
    "numeric_float_amount": {"action": "send", "amount": 2.5, "currency": "USD", "alias": "pay:x"},
    "payment_type_field": {
        "action": "report",
        "amount": "0.01",
        "currency": "XRP",
        "payment_type": "micropayment",
        "alias_name": "pay:agent.analysis",
    },
}

SEM_CASES = {
    "send_msg": {"action": "send", "intent": "pay vendor"},
    "verify_msg": {"action": "check", "ref": "abc"},
}


def build() -> dict:
    # Self-verify the static expectations before emitting.
    for v in PAY_URI:
        assert is_valid_pay_uri(v["input"]) is v["valid"], v
    for v in NORM_OK:
        assert normalize_action(v["input"]) == v["output"], v
    for bad in NORM_ERR:
        try:
            normalize_action(bad)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError(f"expected ValueError for {bad!r}")

    canonical_hash = [
        {"name": k, "request": r, "expected_hash": compute_canonical_hash(r)} for k, r in CH_CASES.items()
    ]
    by_name = {c["name"]: c["expected_hash"] for c in canonical_hash}
    for n in ("synonym_transfer", "synonym_pay", "with_noise"):
        assert by_name[n] == by_name["base"], n

    semantic_hash = [
        {
            "name": k,
            "message": m,
            "normalized": normalize_message(m),
            "expected_hash": compute_semantic_hash(normalize_message(m)),
        }
        for k, m in SEM_CASES.items()
    ]

    return {
        "_comment": (
            "SHARED cross-language test vectors for a2a-protocol-core. Generated from the "
            "Python reference impl (source of truth) by generate_vectors.py. Both the Python "
            "and the @dnsofmoney/a2a-protocol-core (TS) test suites assert against THIS file "
            "byte-for-byte. Do not hand-edit hashes — regenerate."
        ),
        "version": "0.1.0",
        "pay_uri": PAY_URI,
        "normalize_action": {"ok": NORM_OK, "error": NORM_ERR},
        "canonical_hash": canonical_hash,
        "canonical_hash_equivalence_groups": [["base", "synonym_transfer", "synonym_pay", "with_noise"]],
        "semantic_hash": semantic_hash,
    }


if __name__ == "__main__":
    out_path = Path(__file__).parent / "canonical_vectors.json"
    out_path.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
