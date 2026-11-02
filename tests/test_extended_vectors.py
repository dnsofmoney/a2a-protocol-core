"""
Extended cross-language conformance — the Python side.

``vectors/extended_vectors.json`` was generated from this package by
``vectors/gen_extended_vectors.py`` (shared with the Go SDK). It covers what
``canonical_vectors.json`` does not: float repr, bool-as-int, big ints,
ensure_ascii escapes (DEL included), ``str.strip()`` separators, nested values,
the X-PAYMENT header bytes and the InvoiceID hash. The TS and Go suites assert
against the same file, so this test pins Python to it.
"""

from __future__ import annotations

import json
from pathlib import Path

from a2a_protocol_core import (
    __version__,
    build_x_payment_header,
    compute_canonical_hash,
    compute_semantic_hash,
    normalize_action,
    normalize_message,
)
from a2a_protocol_core.x402_pay import invoice_id_hash

VECTORS = json.loads((Path(__file__).parent / "vectors" / "extended_vectors.json").read_text(encoding="utf-8"))


def test_vectors_match_package_version():
    assert VECTORS["a2a_protocol_core_version"] == __version__


def test_extended_canonical_hash():
    for c in VECTORS["canonical_hash"]:
        assert compute_canonical_hash(json.loads(c["request_json"])) == c["expected_hash"], c["name"]


def test_extended_semantic_hash():
    for s in VECTORS["semantic_hash"]:
        normalized = normalize_message(json.loads(s["message_json"]))
        assert normalized.get("action") == s["normalized_action"], s["name"]
        assert compute_semantic_hash(normalized) == s["expected_hash"], s["name"]


def test_extended_normalize_action():
    for v in VECTORS["normalize_action_ok"]:
        assert normalize_action(v["input"]) == v["output"], v["input"]


def test_x_payment_header():
    for v in VECTORS["x_payment_header"]:
        assert build_x_payment_header(v["tx_hash"], v["payer"] or None) == v["expected"], v["tx_hash"]


def test_invoice_id_hash():
    for v in VECTORS["invoice_id_hash"]:
        assert invoice_id_hash(v["input"]) == v["expected"], v["input"]
