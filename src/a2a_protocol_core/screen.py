"""
Paid counterparty screen client — "screen before you pay".

``GET /api/v1/x402/screen/{target}`` is DNS of Money's distributable paid
endpoint: pay the screening fee (an x402 payment at the service's declared
price) and receive an OFAC + resolution attestation about a CALLER-NAMED
target — a ``pay:`` alias or a raw any-chain address. The screened party is
decoupled from the paid party, which is exactly what an agent needs before it
pays a third party.

    from a2a_protocol_core import screen

    result = screen(
        base_url="https://api.dnsofmoney.com",
        target="pay:vendor.alpha",            # or a raw address on any chain
        api_key="...",                        # settle leg requires a tenant key
        algorand_mnemonic="...25 words...",   # fee is USDC on Algorand by default
        verify=True,                          # check the attestation signature
    )
    if result.verdict == "CLEAR":
        ...proceed to pay the vendor...

The fee leg reuses the same non-custodial machinery as the pay path: USDC on
Algorand via the official x402 client (``[algorand]`` extra) or XRP via a local
XRPL signature (``[xrpl]`` extra). ``verify=True`` additionally checks the
attestation's eddsa-jcs-2022 proof against the issuer's did:web document
(``[verify]`` extra).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import requests

from a2a_protocol_core import x402_pay
from a2a_protocol_core._retry import get_with_retries
from a2a_protocol_core.attestation_verify import AttestationVerification, verify_attestation
from a2a_protocol_core.x402_pay import (
    DEFAULT_TIMEOUT,
    DEFAULT_XRPL_RPC,
    AttestationSummary,
    X402PayError,
    decode_payment_required,
    invoice_id_hash,
    summarize_attestation,
)


def screen_url(base_url: str, target: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1/x402/screen/{target}"


@dataclass
class ScreenResult:
    """The screen deliverable: the target's verdict + the signed attestation."""

    target: str
    verdict: Optional[str]  # overall: CLEAR / REVIEW / BLOCKED / UNKNOWN
    attestation: dict
    proof: dict
    summary: AttestationSummary
    verification: Optional[AttestationVerification]  # set when verify=True
    idempotent: bool
    raw: dict


def fetch_screen_requirement_header(
    *,
    base_url: str,
    target: str,
    currency: str = "USDC",
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """GET the screen 402 challenge; return the raw ``PAYMENT-REQUIRED`` header.

    The fee amount is server-set (the screening service's declared price) — the
    caller never names it.
    """
    http = session or requests.Session()
    resp = get_with_retries(http, screen_url(base_url, target), params={"currency": currency}, timeout=timeout)
    if resp.status_code != 402:
        raise X402PayError(f"expected a 402 challenge, got {resp.status_code}: {resp.text[:200]}")
    header = resp.headers.get("PAYMENT-REQUIRED")
    if not header:
        raise X402PayError("402 response missing the PAYMENT-REQUIRED header")
    return header


def screen_with_payment_header(
    *,
    base_url: str,
    target: str,
    payment_header: str,
    api_key: str,
    currency: str = "USDC",
    verify: bool = False,
    expected_issuer: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScreenResult:
    """Settle the screen fee with a caller-built payment header; return the result.

    The lower-level leg — use this when your own wallet stack built the x402
    payment. :func:`screen` wires the whole flow for you.
    """
    http = session or requests.Session()
    # Retry-safe: the settle leg is idempotent server-side (checked before verification).
    resp = get_with_retries(
        http,
        screen_url(base_url, target),
        params={"currency": currency},
        headers={"X-PAYMENT": payment_header, "X-API-Key": api_key},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise X402PayError(f"screen settle failed {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    attestation = body.get("attestation") or {}
    verification = None
    if verify:
        verification = verify_attestation(attestation, expected_issuer=expected_issuer, session=http, timeout=timeout)
    # CounterpartyScreenCredential: overall verdict lives at subject.screen.verdict
    # (signed VC wraps the body under credentialSubject; unsigned form is flat).
    subject = attestation.get("credentialSubject", attestation)
    verdict = (subject.get("screen") or {}).get("verdict")
    return ScreenResult(
        target=target,
        verdict=verdict,
        attestation=attestation,
        proof=body.get("proof") or {},
        summary=summarize_attestation(attestation),
        verification=verification,
        idempotent=bool(body.get("idempotent")),
        raw=body,
    )


def screen(
    *,
    base_url: str,
    target: str,
    api_key: str,
    currency: str = "USDC",
    algorand_mnemonic: Optional[str] = None,
    algorand_secret_key: Optional[Union[bytes, str]] = None,
    xrpl_seed: Optional[str] = None,
    xrpl_rpc_url: str = DEFAULT_XRPL_RPC,
    verify: bool = False,
    expected_issuer: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ScreenResult:
    """Screen a counterparty end to end: pay the fee, get the attested verdict.

    402 → pay the server-priced fee from your own wallet (USDC-on-Algorand by
    default; XRP with ``currency="XRP"`` + ``xrpl_seed``) → the paid deliverable
    is the OFAC + resolution attestation about ``target``. Non-custodial: keys
    sign locally and never leave the process. ``verify=True`` also checks the
    attestation signature against the issuer's did:web key.
    """
    http = session or requests.Session()
    cur = (currency or "").upper()
    raw = fetch_screen_requirement_header(base_url=base_url, target=target, currency=cur, session=http, timeout=timeout)
    if cur == "USDC":
        header = x402_pay.build_avm_payment_header(raw, mnemonic=algorand_mnemonic, secret_key=algorand_secret_key)
    elif cur == "XRP":
        if not xrpl_seed:
            raise X402PayError("XRP fee payment requires xrpl_seed")
        req = decode_payment_required(raw)
        extra = req.get("extra") or {}
        invoice = extra.get("invoiceId") or req.get("invoiceId")
        source_tag = extra.get("sourceTag") if extra.get("sourceTag") is not None else req.get("sourceTag")
        tx_hash, payer = x402_pay._sign_and_submit_xrp(
            pay_to=req["payTo"],
            drops=req["maxAmountRequired"],
            seed=xrpl_seed,
            rpc_url=xrpl_rpc_url,
            invoice_id=invoice_id_hash(invoice) if invoice else None,
            source_tag=source_tag,
        )
        header = x402_pay.build_x_payment_header(tx_hash, payer)
    else:
        raise X402PayError(f"unsupported fee currency {currency!r} — USDC (Algorand) or XRP (XRPL)")

    return screen_with_payment_header(
        base_url=base_url,
        target=target,
        payment_header=header,
        api_key=api_key,
        currency=cur,
        verify=verify,
        expected_issuer=expected_issuer,
        session=http,
        timeout=timeout,
    )
