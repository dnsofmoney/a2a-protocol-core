from __future__ import annotations
from typing import Any

from app.core.a2a_core import normalize_message, compute_hashes

REQUIRED_FIELDS: dict[str, list[str]] = {
    "header": ["version", "message_class", "message_type", "domain"],
    "identity": ["sender_role", "receiver_role", "request_id"],
    "intent": ["action", "subject", "object"],
    "output_spec": ["output_format", "output_schema"],
    "integrity": ["payload_hash"],
    "termination": ["end_message"],
}


def validate_message(message: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for block, keys in REQUIRED_FIELDS.items():
        if block not in message:
            for key in keys:
                missing.append(f"{block}.{key}")
        else:
            for key in keys:
                if key not in message[block]:
                    missing.append(f"{block}.{key}")
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    return message


def process_inbound(message: dict[str, Any]) -> dict[str, Any]:
    validate_message(message)
    normalized = normalize_message(message)
    hashes = compute_hashes(message)
    if "integrity" not in normalized:
        normalized["integrity"] = {}
    normalized["integrity"]["payload_hash"] = hashes["payload_hash"]
    normalized["integrity"]["canonical_hash"] = hashes["canonical_hash"]
    return normalized
