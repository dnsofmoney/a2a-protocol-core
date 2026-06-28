from a2a_protocol_core.canonical_hash import compute_canonical_hash


def test_metadata_does_not_change_hash():
    base = {"amount": 10, "currency": "USD", "alias": "pay:vendor.alpha"}
    noisy = {
        **base,
        "session_id": "s-1",
        "request_id": "r-1",
        "trace_id": "t-1",
        "timestamp": "2026-06-28T00:00:00Z",
        "idempotency_key": "idem-1",
        "memo": "hello",
    }
    assert compute_canonical_hash(base) == compute_canonical_hash(noisy)


def test_numeric_and_string_amount_match():
    assert compute_canonical_hash({"amount": 10}) == compute_canonical_hash({"amount": "10"})


def test_synonym_action_collapses():
    a = compute_canonical_hash({"action": "send", "amount": "1"})
    b = compute_canonical_hash({"action": "transfer", "amount": "1"})
    assert a == b


def test_semantic_difference_changes_hash():
    a = compute_canonical_hash({"amount": "1", "currency": "USD"})
    b = compute_canonical_hash({"amount": "2", "currency": "USD"})
    assert a != b


def test_unknown_action_kept_raw():
    # Unknown actions don't raise; they fall through to the raw value.
    h = compute_canonical_hash({"action": "frobnicate", "amount": "1"})
    assert isinstance(h, str) and len(h) == 64
