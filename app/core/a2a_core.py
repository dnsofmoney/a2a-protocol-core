from __future__ import annotations
import hashlib, json, re
from copy import deepcopy
from typing import Any

CANONICAL_BLOCK_ORDER = [
    "header", "identity", "intent", "constraints",
    "evidence", "output_spec", "cache_control", "integrity", "termination",
]

CANONICAL_KEY_ORDER: dict[str, list[str]] = {
    "header":       ["version","message_class","message_class_label","message_type","domain"],
    "identity":     ["sender_role","receiver_role","session_id","request_id","trace_id","timestamp"],
    "intent":       ["action","subject","object","goal","priority"],
    "constraints":  ["constraint_profile","policy_profile","jurisdiction","time_scope","max_latency_ms"],
    "evidence":     ["evidence_mode","data_ref","fact_set_ref","doc_ref","ledger_ref"],
    "output_spec":  ["output_format","output_schema","detail_level","confidence_mode","citation_mode"],
    "cache_control":["cache_policy","cache_scope"],
    "integrity":    ["payload_hash","canonical_hash","schema_version","signature"],
    "termination":  ["end_message"],
}

CANONICAL_HASH_EXCLUDE: set[tuple[str,str]] = {
    ("identity","session_id"), ("identity","request_id"),
    ("identity","trace_id"),   ("identity","timestamp"),
    ("integrity","payload_hash"), ("integrity","canonical_hash"),
    ("termination","end_message"),
}

SYNONYM_NORMALIZATION: dict[str, str] = {
    "check": "VERIFY", "review": "VERIFY", "inspect": "VERIFY",
    "lookup": "QUERY",  "brief": "CONCISE", "short": "CONCISE",
    "usa": "US", "united_states": "US",
}

def _normalize_value(v: Any) -> Any:
    if isinstance(v, str):
        s = " ".join(v.strip().split())
        lower = s.lower()
        if lower in SYNONYM_NORMALIZATION:
            return SYNONYM_NORMALIZATION[lower]
        return s
    return v

def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for block in CANONICAL_BLOCK_ORDER:
        if block not in message:
            continue
        out[block] = {}
        for key in CANONICAL_KEY_ORDER.get(block, []):
            if key in message[block]:
                out[block][key] = _normalize_value(message[block][key])
    return out

def canonical_json(
    message: dict[str, Any], *, for_canonical_hash: bool = False
) -> str:
    msg = deepcopy(message)
    if for_canonical_hash:
        for block, key in CANONICAL_HASH_EXCLUDE:
            if block in msg and key in msg[block]:
                del msg[block][key]
    normalized = normalize_message(msg)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def compute_hashes(message: dict[str, Any]) -> dict[str, str]:
    return {
        "payload_hash":   sha256_hex(canonical_json(message)),
        "canonical_hash": sha256_hex(canonical_json(message, for_canonical_hash=True)),
    }
