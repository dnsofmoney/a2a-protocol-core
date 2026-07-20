"""
a2a-protocol-core — the open, deterministic core of the DNS of Money A2A surface.

What lives here is the dependency-light, verifiable protocol layer that external
AI agents adopt: the ``pay:`` address grammar, the canonical/semantic hashing
used to make payment intent stable across vocabularies, the A2A-041 wire schemas,
and a thin payment-hook client.

The intelligence lives in the calling agent. This package serves deterministic,
inspectable primitives — no rail selection, no scoring, no model in the path.
"""

from __future__ import annotations

from a2a_protocol_core.addressing import (
    MAX_PAY_URI_LENGTH,
    PAY_URI_PATTERN,
    assert_valid_pay_uri,
    is_valid_pay_uri,
)
from a2a_protocol_core.canonical_hash import compute_canonical_hash
from a2a_protocol_core.client import A2APaymentHookClient
from a2a_protocol_core.schemas import (
    A2ACapabilities,
    A2APaymentHookRequest,
    A2APaymentHookResponse,
    ResolutionDetail,
    SettlementDetail,
)
from a2a_protocol_core.semantic_normalizer import (
    CANONICAL_ACTIONS,
    SYNONYM_MAP,
    compute_semantic_hash,
    normalize_action,
    normalize_message,
)
from a2a_protocol_core.x402_pay import (
    AttestationSummary,
    X402PaymentResult,
    X402PayError,
    attest_settled_payment,
    build_x_payment_header,
    decode_payment_required,
    fetch_requirement,
    pay_alias_xrp,
    summarize_attestation,
)

__version__ = "0.2.1"

__all__ = [
    "__version__",
    # addressing
    "PAY_URI_PATTERN",
    "MAX_PAY_URI_LENGTH",
    "is_valid_pay_uri",
    "assert_valid_pay_uri",
    # hashing
    "compute_canonical_hash",
    "compute_semantic_hash",
    "normalize_action",
    "normalize_message",
    "CANONICAL_ACTIONS",
    "SYNONYM_MAP",
    # schemas
    "A2APaymentHookRequest",
    "A2APaymentHookResponse",
    "ResolutionDetail",
    "SettlementDetail",
    "A2ACapabilities",
    # client
    "A2APaymentHookClient",
    # x402 pay-path (one-call; signing needs the [xrpl] extra)
    "pay_alias_xrp",
    "attest_settled_payment",
    "fetch_requirement",
    "decode_payment_required",
    "build_x_payment_header",
    "summarize_attestation",
    "AttestationSummary",
    "X402PaymentResult",
    "X402PayError",
]
