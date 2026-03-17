from app.core.a2a_core import normalize_message, compute_hashes

def _msg(session_id="S-001", request_id="R-001"):
    return {
        "header":   {"version": 1, "message_class": "A2A",
                     "message_type": "VERIFY", "domain": "FINTECH"},
        "identity": {"sender_role": "ORCHESTRATOR",
                     "receiver_role": "PAYMENTS_ANALYST",
                     "session_id": session_id,
                     "request_id": request_id,
                     "timestamp": "2026-03-17T00:00:00Z"},
        "intent":   {"action": "VERIFY", "subject": "PAYOUT_BATCH",
                     "object": "BATCH-001"},
        "output_spec": {"output_format": "JSON",
                        "output_schema": "PAYOUT_VALIDATION_V1"},
        "integrity":   {"payload_hash": "placeholder"},
        "termination": {"end_message": True},
    }

def test_payload_hash_deterministic():
    h1 = compute_hashes(_msg())["payload_hash"]
    h2 = compute_hashes(_msg())["payload_hash"]
    assert h1 == h2

def test_canonical_hash_ignores_volatile_fields():
    ha = compute_hashes(_msg(session_id="S-001", request_id="R-001"))
    hb = compute_hashes(_msg(session_id="S-999", request_id="R-999"))
    assert ha["payload_hash"] != hb["payload_hash"]
    assert ha["canonical_hash"] == hb["canonical_hash"]

def test_synonym_normalization():
    msg = {"header": {"version": 1, "message_class": "A2A",
                      "message_type": "check", "domain": "FINTECH"},
           "identity": {"sender_role": "X", "receiver_role": "Y",
                        "request_id": "R-1"}}
    n = normalize_message(msg)
    assert n["header"]["message_type"] == "VERIFY"
