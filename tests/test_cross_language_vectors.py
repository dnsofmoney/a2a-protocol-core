"""
Cross-language conformance — the Python side of the shared contract.

Both this suite and the TS `@dnsofmoney/a2a-protocol-core` suite assert against
the SAME `vectors/canonical_vectors.json` (generated from this Python reference
by `generate_vectors.py`). The canonical/semantic hashes are byte-for-byte
identical across languages; this test pins Python to the vectors so neither side
can silently drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from a2a_protocol_core import (
    compute_canonical_hash,
    compute_semantic_hash,
    is_valid_pay_uri,
    normalize_action,
)

VECTORS = json.loads((Path(__file__).parent / "vectors" / "canonical_vectors.json").read_text(encoding="utf-8"))


def test_pay_uri_vectors():
    for v in VECTORS["pay_uri"]:
        assert is_valid_pay_uri(v["input"]) is v["valid"], v["input"]


def test_normalize_action_ok_vectors():
    for v in VECTORS["normalize_action"]["ok"]:
        assert normalize_action(v["input"]) == v["output"], v["input"]


def test_normalize_action_error_vectors():
    for bad in VECTORS["normalize_action"]["error"]:
        with pytest.raises(ValueError):
            normalize_action(bad)


def test_canonical_hash_matches_vectors():
    for c in VECTORS["canonical_hash"]:
        assert compute_canonical_hash(c["request"]) == c["expected_hash"], c["name"]


def test_canonical_hash_equivalence_groups():
    by_name = {c["name"]: c["expected_hash"] for c in VECTORS["canonical_hash"]}
    for group in VECTORS["canonical_hash_equivalence_groups"]:
        first = by_name[group[0]]
        for name in group:
            assert by_name[name] == first, name


def test_semantic_hash_matches_vectors():
    for s in VECTORS["semantic_hash"]:
        assert compute_semantic_hash(s["normalized"]) == s["expected_hash"], s["name"]
