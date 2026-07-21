"""
Client-side verification of DNS of Money signed attestations.

The paid deliverable (resolve / verify / OFAC-screen attestation) is a W3C
Verifiable Credential secured with a **Data Integrity proof, cryptosuite
``eddsa-jcs-2022``**: JCS canonicalization (RFC 8785) + SHA-256 + Ed25519,
issued by a ``did:web`` issuer whose DID document is served at
``https://<domain>/.well-known/did.json``.

``verify_attestation`` closes the loop the SDK's pitch promises: an agent that
paid for an attestation can check the issuer's signature itself instead of
trusting TLS alone.

    from a2a_protocol_core import verify_attestation

    result = pay_alias_xrp(...)                      # or screen(...)
    v = verify_attestation(result.attestation)
    assert v.verified and v.issuer == "did:web:dnsofmoney.com"

Only the Ed25519 check needs a dependency (``cryptography``) — install the
``[verify]`` extra. Everything else (JCS, base58btc, did:web resolution) is
pure Python.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import unquote

import requests

from a2a_protocol_core._retry import get_with_retries

DEFAULT_TIMEOUT = 30

CRYPTOSUITE = "eddsa-jcs-2022"

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_ED25519_PUB_MULTICODEC = b"\xed\x01"


class AttestationVerificationError(Exception):
    """Raised when a signed attestation fails verification (or is unverifiable)."""


# ── JCS canonicalization (RFC 8785 subset — objects/arrays/strings/ints/bools/null) ──


def _reject_floats(obj: Any) -> None:
    """Credentials carry strings/ints only; full JCS float formatting is out of scope,
    so fail loud rather than canonicalize bytes another implementation might not."""
    if isinstance(obj, float):
        raise AttestationVerificationError("floats are not allowed in canonicalized credential data")
    if isinstance(obj, dict):
        for v in obj.values():
            _reject_floats(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _reject_floats(v)


def jcs_canonicalize(obj: Any) -> bytes:
    """JCS-compatible canonical UTF-8 bytes: sorted keys, compact, non-ASCII preserved."""
    _reject_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _canonical_hash(obj: Any) -> bytes:
    return hashlib.sha256(jcs_canonicalize(obj)).digest()


# ── base58btc / multibase (pure Python — no bitcoin lib needed for 32/64 bytes) ──


def base58btc_decode(s: str) -> bytes:
    n = 0
    for ch in s:
        try:
            n = n * 58 + _B58_ALPHABET.index(ch)
        except ValueError as exc:
            raise AttestationVerificationError(f"invalid base58 character {ch!r}") from exc
    full = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + full


def _multibase_decode(value: str) -> bytes:
    if not value.startswith("z"):
        raise AttestationVerificationError("expected multibase base58btc value starting with 'z'")
    return base58btc_decode(value[1:])


def public_key_bytes_from_multibase(multibase: str) -> bytes:
    """Decode a Multikey ``publicKeyMultibase`` (z6Mk… form) to the raw 32-byte key."""
    decoded = _multibase_decode(multibase)
    if not decoded.startswith(_ED25519_PUB_MULTICODEC):
        raise AttestationVerificationError("publicKeyMultibase is not an ed25519-pub multikey")
    raw = decoded[len(_ED25519_PUB_MULTICODEC) :]
    if len(raw) != 32:
        raise AttestationVerificationError(f"ed25519 public key must be 32 bytes, got {len(raw)}")
    return raw


# ── did:web resolution ────────────────────────────────────────────────────────────


def did_web_document_url(did: str) -> str:
    """Map a ``did:web`` identifier to its DID-document URL (W3C did:web §3.2).

    ``did:web:example.com`` → ``https://example.com/.well-known/did.json``;
    ``did:web:example.com:user:alice`` → ``https://example.com/user/alice/did.json``.
    Percent-encoded ports (``%3A``) in the host segment are decoded.
    """
    if not did.startswith("did:web:"):
        raise AttestationVerificationError(f"not a did:web identifier: {did}")
    segments = did[len("did:web:") :].split(":")
    host = unquote(segments[0])
    if not host:
        raise AttestationVerificationError(f"did:web has no host: {did}")
    path = [unquote(s) for s in segments[1:]]
    if path:
        return f"https://{host}/{'/'.join(path)}/did.json"
    return f"https://{host}/.well-known/did.json"


def fetch_did_document(
    did: str,
    *,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Fetch and return the DID document for a ``did:web`` issuer."""
    http = session or requests.Session()
    url = did_web_document_url(did)
    resp = get_with_retries(http, url, timeout=timeout)
    if resp.status_code != 200:
        raise AttestationVerificationError(f"DID document fetch failed ({resp.status_code}) at {url}")
    doc = resp.json()
    if doc.get("id") != did:
        raise AttestationVerificationError(f"DID document id {doc.get('id')!r} does not match {did!r}")
    return doc


def resolve_assertion_key_bytes(did_document: dict, verification_method_id: str) -> bytes:
    """Resolve a verification-method id to its raw Ed25519 key, ENFORCING assertionMethod.

    A key that is present but not authorized under the document's ``assertionMethod``
    relationship must not verify a credential — that authorization check is the heart
    of VC verification, not an optional nicety.
    """
    if verification_method_id not in (did_document.get("assertionMethod") or []):
        raise AttestationVerificationError(f"{verification_method_id} is not authorized under assertionMethod")
    for vm in did_document.get("verificationMethod") or []:
        if vm.get("id") == verification_method_id:
            mb = vm.get("publicKeyMultibase")
            if not mb:
                raise AttestationVerificationError("verification method has no publicKeyMultibase")
            return public_key_bytes_from_multibase(mb)
    raise AttestationVerificationError(f"verification method {verification_method_id} not found in DID document")


# ── Proof verification (eddsa-jcs-2022) ───────────────────────────────────────────


@dataclass
class AttestationVerification:
    """Outcome of a successful verification (failure raises, it never returns False)."""

    verified: bool
    issuer: str
    verification_method: str
    credential_types: list


def _verify_ed25519(public_key_raw: bytes, signature: bytes, data: bytes) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:  # pragma: no cover - import guard
        raise AttestationVerificationError(
            "signature verification requires the 'verify' extra — install with: pip install 'a2a-protocol-core[verify]'"
        ) from exc
    try:
        Ed25519PublicKey.from_public_bytes(public_key_raw).verify(signature, data)
    except InvalidSignature as exc:
        raise AttestationVerificationError("signature does not verify") from exc


def verify_attestation(
    attestation: dict,
    *,
    did_document: Optional[dict] = None,
    expected_issuer: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> AttestationVerification:
    """Verify a signed attestation's eddsa-jcs-2022 Data Integrity proof.

    Resolves the issuer's ``did:web`` DID document over HTTPS (or takes one via
    ``did_document`` for offline/pinned verification), enforces that the proof's
    verification method is authorized under ``assertionMethod``, and checks the
    Ed25519 signature over ``sha256(proofConfig) || sha256(document)``.

    Raises ``AttestationVerificationError`` on ANY failure — including an unsigned
    attestation (the server ships attestations unsigned when its trust layer is
    off; callers who demand cryptographic provenance must treat that as a failure,
    not a soft pass).

    Scope: this is signature + issuer-authorization verification. Whether you
    TRUST the issuer, and whether the attestation's verdict/tx bindings match the
    payment you made, remain the calling agent's judgment.
    """
    proof = attestation.get("proof")
    if not isinstance(proof, dict):
        raise AttestationVerificationError("attestation is unsigned (no proof)")
    if proof.get("cryptosuite") != CRYPTOSUITE:
        raise AttestationVerificationError(f"unsupported cryptosuite: {proof.get('cryptosuite')!r}")
    if proof.get("proofPurpose") != "assertionMethod":
        raise AttestationVerificationError(f"proofPurpose must be assertionMethod, got {proof.get('proofPurpose')!r}")

    issuer = attestation.get("issuer")
    if not isinstance(issuer, str) or not issuer:
        raise AttestationVerificationError("attestation has no issuer")
    if expected_issuer is not None and issuer != expected_issuer:
        raise AttestationVerificationError(f"issuer {issuer!r} does not match expected {expected_issuer!r}")

    vm_id = proof.get("verificationMethod")
    if not isinstance(vm_id, str) or not vm_id:
        raise AttestationVerificationError("proof has no verificationMethod")
    # The method must belong to the ISSUER's DID — a proof pointing at someone
    # else's key would otherwise verify against the wrong document.
    if vm_id.split("#", 1)[0] != issuer:
        raise AttestationVerificationError(f"verificationMethod {vm_id!r} does not belong to issuer {issuer!r}")

    proof_value = proof.get("proofValue")
    if not isinstance(proof_value, str) or not proof_value:
        raise AttestationVerificationError("proof has no proofValue")
    signature = _multibase_decode(proof_value)

    doc = did_document if did_document is not None else fetch_did_document(issuer, session=session, timeout=timeout)
    key_raw = resolve_assertion_key_bytes(doc, vm_id)

    # eddsa-jcs-2022 signing input: sha256(proofConfig) || sha256(documentWithoutProof),
    # where proofConfig is the proof minus proofValue, bound to the document @context.
    document = {k: v for k, v in attestation.items() if k != "proof"}
    cfg = {k: v for k, v in proof.items() if k != "proofValue"}
    cfg["@context"] = document.get("@context")
    _verify_ed25519(key_raw, signature, _canonical_hash(cfg) + _canonical_hash(document))

    types = attestation.get("type")
    return AttestationVerification(
        verified=True,
        issuer=issuer,
        verification_method=vm_id,
        credential_types=list(types) if isinstance(types, list) else [types] if types else [],
    )
