"""Tests for client-side attestation verification (eddsa-jcs-2022 + did:web).

Real cryptography: fixtures are signed with a locally generated Ed25519 key
using the exact server recipe (JCS canonicalization, sha256(cfg)||sha256(doc),
multibase base58btc), then verified through the public API.
"""

from __future__ import annotations

import copy

import pytest

cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from a2a_protocol_core.attestation_verify import (  # noqa: E402
    _B58_ALPHABET,
    _ED25519_PUB_MULTICODEC,
    AttestationVerificationError,
    did_web_document_url,
    fetch_did_document,
    jcs_canonicalize,
    verify_attestation,
)
from a2a_protocol_core.attestation_verify import _canonical_hash  # noqa: E402

ISSUER = "did:web:dnsofmoney.com"
VM_ID = f"{ISSUER}#key-1"


def _b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = ""
    while n > 0:
        n, rem = divmod(n, 58)
        out = _B58_ALPHABET[rem] + out
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + out


@pytest.fixture(scope="module")
def issuer_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture(scope="module")
def did_document(issuer_key):
    raw = issuer_key.public_key().public_bytes_raw()
    return {
        "id": ISSUER,
        "verificationMethod": [
            {
                "id": VM_ID,
                "type": "Multikey",
                "controller": ISSUER,
                "publicKeyMultibase": "z" + _b58encode(_ED25519_PUB_MULTICODEC + raw),
            }
        ],
        "assertionMethod": [VM_ID],
        "authentication": [VM_ID],
    }


def _sign(credential: dict, key: Ed25519PrivateKey, vm_id: str = VM_ID) -> dict:
    """The server's signing recipe (app/trust/credentials.py), reproduced for fixtures."""
    document = {k: v for k, v in credential.items() if k != "proof"}
    proof = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": "2026-07-20T00:00:00Z",
        "verificationMethod": vm_id,
        "proofPurpose": "assertionMethod",
    }
    cfg = {k: v for k, v in proof.items() if k != "proofValue"}
    cfg["@context"] = document.get("@context")
    signature = key.sign(_canonical_hash(cfg) + _canonical_hash(document))
    proof["proofValue"] = "z" + _b58encode(signature)
    return {**document, "proof": proof}


@pytest.fixture(scope="module")
def attestation(issuer_key):
    return _sign(
        {
            "@context": ["https://www.w3.org/ns/credentials/v2", "https://dnsofmoney.com/contexts/fas1-v1"],
            "type": ["VerifiableCredential", "CounterpartyScreenCredential"],
            "issuer": ISSUER,
            "validFrom": "2026-07-20T00:00:00Z",
            "credentialSubject": {
                "target": {"input": "pay:vendor.alpha", "kind": "alias"},
                "screen": {"verdict": "CLEAR", "addresses_screened": 1},
                "fee_settlement": {"txid": "ALGOTX", "invoiceId": "inv-1", "amount": "0.01"},
            },
        },
        issuer_key,
    )


# ── Happy path ────────────────────────────────────────────────────────────────


def test_verify_ok(attestation, did_document):
    v = verify_attestation(attestation, did_document=did_document)
    assert v.verified is True
    assert v.issuer == ISSUER
    assert v.verification_method == VM_ID
    assert "CounterpartyScreenCredential" in v.credential_types


def test_verify_with_expected_issuer(attestation, did_document):
    v = verify_attestation(attestation, did_document=did_document, expected_issuer=ISSUER)
    assert v.verified


# ── Failure modes ─────────────────────────────────────────────────────────────


def test_tampered_subject_fails(attestation, did_document):
    tampered = copy.deepcopy(attestation)
    tampered["credentialSubject"]["screen"]["verdict"] = "BLOCKED"  # flip the verdict
    with pytest.raises(AttestationVerificationError, match="signature does not verify"):
        verify_attestation(tampered, did_document=did_document)


def test_tampered_proof_created_fails(attestation, did_document):
    tampered = copy.deepcopy(attestation)
    tampered["proof"]["created"] = "2030-01-01T00:00:00Z"
    with pytest.raises(AttestationVerificationError, match="signature does not verify"):
        verify_attestation(tampered, did_document=did_document)


def test_unsigned_fails(did_document):
    with pytest.raises(AttestationVerificationError, match="unsigned"):
        verify_attestation({"issuer": ISSUER, "screen": {"verdict": "CLEAR"}}, did_document=did_document)


def test_wrong_cryptosuite_fails(attestation, did_document):
    bad = copy.deepcopy(attestation)
    bad["proof"]["cryptosuite"] = "ecdsa-rdfc-2019"
    with pytest.raises(AttestationVerificationError, match="cryptosuite"):
        verify_attestation(bad, did_document=did_document)


def test_wrong_proof_purpose_fails(attestation, did_document):
    bad = copy.deepcopy(attestation)
    bad["proof"]["proofPurpose"] = "authentication"
    with pytest.raises(AttestationVerificationError, match="proofPurpose"):
        verify_attestation(bad, did_document=did_document)


def test_expected_issuer_mismatch_fails(attestation, did_document):
    with pytest.raises(AttestationVerificationError, match="does not match expected"):
        verify_attestation(attestation, did_document=did_document, expected_issuer="did:web:evil.example")


def test_foreign_verification_method_fails(attestation, did_document):
    bad = copy.deepcopy(attestation)
    bad["proof"]["verificationMethod"] = "did:web:evil.example#key-1"
    with pytest.raises(AttestationVerificationError, match="does not belong to issuer"):
        verify_attestation(bad, did_document=did_document)


def test_unauthorized_key_fails(attestation, did_document):
    # Key present in the document but NOT under assertionMethod must not verify.
    doc = copy.deepcopy(did_document)
    doc["assertionMethod"] = []
    with pytest.raises(AttestationVerificationError, match="not authorized under assertionMethod"):
        verify_attestation(attestation, did_document=doc)


def test_signed_by_different_key_fails(attestation, did_document):
    other = Ed25519PrivateKey.generate()
    forged = _sign({k: v for k, v in attestation.items() if k != "proof"}, other)
    with pytest.raises(AttestationVerificationError, match="signature does not verify"):
        verify_attestation(forged, did_document=did_document)


def test_floats_rejected():
    with pytest.raises(AttestationVerificationError, match="floats"):
        jcs_canonicalize({"amount": 0.01})


# ── did:web resolution ────────────────────────────────────────────────────────


def test_did_web_url_wellknown():
    assert did_web_document_url("did:web:dnsofmoney.com") == "https://dnsofmoney.com/.well-known/did.json"


def test_did_web_url_with_path():
    assert did_web_document_url("did:web:example.com:user:alice") == "https://example.com/user/alice/did.json"


def test_did_web_url_percent_port():
    assert did_web_document_url("did:web:localhost%3A8443") == "https://localhost:8443/.well-known/did.json"


def test_did_web_rejects_other_methods():
    with pytest.raises(AttestationVerificationError, match="did:web"):
        did_web_document_url("did:key:z6Mk...")


class _Resp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(url)
        return self._responses.pop(0)


def test_fetch_did_document_ok(did_document):
    http = _Session([_Resp(200, did_document)])
    doc = fetch_did_document(ISSUER, session=http)
    assert doc["id"] == ISSUER
    assert http.calls == ["https://dnsofmoney.com/.well-known/did.json"]


def test_fetch_did_document_id_mismatch():
    http = _Session([_Resp(200, {"id": "did:web:other.example"})])
    with pytest.raises(AttestationVerificationError, match="does not match"):
        fetch_did_document(ISSUER, session=http)


def test_verify_fetches_document_over_http(attestation, did_document):
    http = _Session([_Resp(200, did_document)])
    v = verify_attestation(attestation, session=http)
    assert v.verified and http.calls == ["https://dnsofmoney.com/.well-known/did.json"]
