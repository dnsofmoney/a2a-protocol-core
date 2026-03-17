import pytest
from app.core.semantic_normalizer import (
    normalize_semantics,
    SemanticValidationError,
    SemanticConfidenceError,
)

def test_cache_collapse_fintech():
    """Core A2A-009 property: equivalent inputs → same semantic_hash."""
    inputs = [
        "Pay the compute node five dollars.",
        "Send USD 5 to the compute provider.",
        "Transfer $5 to AGT-COMPUTE-001.",
    ]
    hashes = [
        normalize_semantics(t, domain="FINTECH",
                            explicit_object="AGT-COMPUTE-001",
                            profile="CACHE_MAXIMIZED")["semantic_hash"]
        for t in inputs
    ]
    assert len(set(hashes)) == 1, f"Hashes diverged: {hashes}"

def test_compute_normalization():
    r = normalize_semantics("Run this inference job on a GPU.", domain="COMPUTE")
    assert r["action"] == "EXECUTE"
    assert r["subject"] == "WORKLOAD"

def test_governance_normalization():
    r = normalize_semantics("Open a dispute about failed settlement.",
                            domain="GOVERNANCE", explicit_object="CASE-991")
    assert r["action"] == "ARBITRATE"
    assert r["subject"] == "DISPUTE_CASE"
    assert r["object"] == "CASE-991"

def test_trust_normalization():
    r = normalize_semantics("Score this agent.", domain="TRUST",
                            explicit_object="AGT-ANALYSIS-001")
    assert r["action"] == "SCORE"
    assert r["subject"] == "REPUTATION_RECORD"

def test_payment_alias_extracted():
    r = normalize_semantics("Resolve pay:agent.compute for payment.",
                            domain="FINTECH")
    assert r["action"] == "RESOLVE"
    assert "pay:agent.compute" in str(r)

def test_different_domains_different_hashes():
    h1 = normalize_semantics("send payment", domain="FINTECH",
                             explicit_object="AGT-001")["semantic_hash"]
    h2 = normalize_semantics("send workload", domain="COMPUTE",
                             explicit_object="WL-001")["semantic_hash"]
    assert h1 != h2

def test_strict_financial_profile_rejects_governance():
    with pytest.raises((SemanticValidationError, SemanticConfidenceError)):
        normalize_semantics("propose a new governance rule.",
                            domain="GOVERNANCE",
                            profile="STRICT_FINANCIAL")

def test_missing_action_raises():
    with pytest.raises((SemanticValidationError, SemanticConfidenceError)):
        normalize_semantics("the five dollars compute node xyz",
                            domain="FINTECH",
                            require_min_confidence=True)
