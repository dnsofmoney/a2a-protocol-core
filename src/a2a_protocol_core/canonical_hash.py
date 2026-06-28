"""
A2A-008 Canonical Hash computation.

Produces a SHA256 hash of the semantically significant fields of a payment
request. Two semantically equivalent payments (same amount, currency, rail,
alias, category) produce the same ``canonical_hash`` regardless of
session/trace/idempotency metadata.

Excluded fields: session_id, request_id, trace_id, timestamp,
idempotency_key, memo, payload_hash, canonical_hash, created_at, updated_at.
"""

from __future__ import annotations

import hashlib
import json

from a2a_protocol_core.semantic_normalizer import normalize_action

# Fields that carry no semantic payment meaning — excluded from the hash.
_EXCLUDED_KEYS = frozenset(
    {
        "session_id",
        "request_id",
        "trace_id",
        "timestamp",
        "idempotency_key",
        "memo",
        "payload_hash",
        "canonical_hash",
        "created_at",
        "updated_at",
    }
)

# Fields that carry semantic payment meaning — included if present.
_INCLUDED_KEYS = (
    "amount",
    "currency",
    "rail",
    "preferred_rail",
    "alias",
    "alias_uri",
    "alias_name",
    "payment_category",
    "payment_type",
    "action",
)


def compute_canonical_hash(payment_request: dict) -> str:
    """
    Compute the SHA256 canonical hash of semantically significant payment fields.

    Rules:
    - Include: amount, currency, rail/preferred_rail, alias/alias_uri,
      payment_category/payment_type, action.
    - Exclude: session_id, request_id, trace_id, timestamp,
      idempotency_key, memo, payload_hash, canonical_hash.
    - Normalize ``action`` via the A2A-009 semantic normalizer.
    - Sort keys, JSON serialize, SHA256.
    """
    canonical: dict = {}
    for key in _INCLUDED_KEYS:
        if key in payment_request and payment_request[key] is not None:
            val = payment_request[key]
            # Normalize numeric types to string for consistency.
            if isinstance(val, (int, float)):
                val = str(val)
            # Normalize action via the semantic normalizer (best-effort).
            if key == "action" and isinstance(val, str):
                try:
                    val = normalize_action(val)
                except ValueError:
                    pass  # keep raw if not a recognized action
            canonical[key] = val

    serialized = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()
