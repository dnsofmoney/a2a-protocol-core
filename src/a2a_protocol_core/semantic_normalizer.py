"""
A2A-009 Semantic Normalizer.

Collapses synonym verbs ("send", "pay", "transfer") into canonical
action codes ("EXECUTE_PAYMENT", "QUERY", "VERIFY", "REPORT").

Used by A2A-008 ``canonical_hash`` for action field normalization. Two agents
that describe the same intent with different words produce the same canonical
action, so the canonical hash is stable across vocabularies.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy

SYNONYM_MAP: dict[str, str] = {
    "transfer": "EXECUTE_PAYMENT",
    "send": "EXECUTE_PAYMENT",
    "pay": "EXECUTE_PAYMENT",
    "payment": "EXECUTE_PAYMENT",
    "resolve": "QUERY",
    "lookup": "QUERY",
    "verify": "VERIFY",
    "check": "VERIFY",
    "confirm": "VERIFY",
    "report": "REPORT",
    "status": "REPORT",
}

CANONICAL_ACTIONS: frozenset[str] = frozenset(
    {
        "EXECUTE_PAYMENT",
        "QUERY",
        "VERIFY",
        "REPORT",
    }
)


def normalize_action(raw_action: str) -> str:
    """
    Normalize a raw action string to its canonical form.

    Lowercases, strips whitespace, collapses synonyms.
    Raises ValueError if the result is not in CANONICAL_ACTIONS.
    """
    cleaned = raw_action.strip().lower()
    canonical = SYNONYM_MAP.get(cleaned, cleaned.upper())
    if canonical not in CANONICAL_ACTIONS:
        raise ValueError(f"Unknown action '{raw_action}' — not in {sorted(CANONICAL_ACTIONS)}")
    return canonical


def normalize_message(message: dict) -> dict:
    """
    Normalize the 'action' field of an A2A message.

    Returns a normalized copy — does NOT mutate the input.
    """
    normalized = deepcopy(message)
    if "action" in normalized:
        normalized["action"] = normalize_action(normalized["action"])
    return normalized


def compute_semantic_hash(normalized_message: dict) -> str:
    """
    SHA256 of the canonical representation of a normalized message.

    Deterministic: same normalized content -> same hash.
    """
    serialized = json.dumps(normalized_message, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()
