"""
One-call x402 pay-path — pay a ``pay:`` alias from YOUR own wallet.

This is the "make it actually easy" helper: an agent developer calls one function
to resolve the x402 requirement for a ``pay:`` alias, sign + submit an XRP payment
**with their own wallet seed**, and hand the proof back to DNS of Money for a
read-only verify + the signed resolve/verify/OFAC-screen attestation.

Non-custodial by construction: the seed is used to sign locally, in *your* process,
and is never sent over the wire. DNS of Money verifies an already-settled tx and
returns metadata — it never holds your keys or your funds.

    pip install "a2a-protocol-core[xrpl]"

    from a2a_protocol_core import pay_alias_xrp

    result = pay_alias_xrp(
        base_url="https://api.dnsofmoney.com",
        alias="pay:vendor.alpha",
        amount_xrp="0.10",
        seed="s...",            # YOUR XRPL wallet seed — signs locally, never sent
        api_key="fas_live_...", # attributes the settle leg
    )
    print(result.tx_hash, result.summary.verdict)

The pure helpers (``decode_payment_required``, ``build_x_payment_header``,
``summarize_attestation``) have no network/xrpl dependency and are unit-tested; the
XRPL signing lazy-imports ``xrpl-py`` so the base package stays dependency-light.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional, Union

import requests

from a2a_protocol_core._retry import get_with_retries

# Public mainnet XRPL JSON-RPC (multi-host cluster). Override for testnet/devnet.
DEFAULT_XRPL_RPC = "https://xrplcluster.com"
DEFAULT_TIMEOUT = 60


class X402PayError(RuntimeError):
    """Raised when the x402 pay-path fails (bad challenge, failed settle, or signing error)."""


# ── Pure helpers (no network, no xrpl — unit-tested) ─────────────────────────────


def decode_payment_required(header_value: str) -> dict:
    """Decode the base64(JSON) PAYMENT-REQUIRED header into the XRP requirement dict."""
    return json.loads(base64.b64decode(header_value))


def build_x_payment_header(tx_hash: str, payer: Optional[str] = None) -> str:
    """Build the X-PAYMENT header: base64(JSON) proof of the settled tx hash."""
    payload: dict = {"txHash": tx_hash}
    if payer:
        payload["payer"] = payer
    envelope = {"x402Version": 2, "payload": payload}
    return base64.b64encode(json.dumps(envelope).encode()).decode()


def invoice_id_hash(invoice_id: str) -> str:
    """The on-chain InvoiceID that binds a payment to a 402 challenge.

    Matches the server verifier: SHA-256 of the requirement's ``invoiceId``, hex,
    uppercased. Setting it on the Payment replay-binds the tx to this challenge.
    """
    return hashlib.sha256(invoice_id.encode("utf-8")).hexdigest().upper()


@dataclass
class AttestationSummary:
    """The deliverable at a glance — the resolve/verify/OFAC-screen verdicts."""

    verdict: Optional[str]  # overall: CLEAR / REVIEW / BLOCKED / UNKNOWN
    payee_verdict: Optional[str]
    payer_verdict: Optional[str]
    tx_id: Optional[str]
    signed: bool


def summarize_attestation(attestation: dict) -> AttestationSummary:
    """One-glance summary of the attestation (signed VC or unsigned flat form)."""
    subject = attestation.get("credentialSubject", attestation)
    screen = subject.get("screen") or {}
    settlement = subject.get("settlement") or {}
    return AttestationSummary(
        verdict=screen.get("verdict"),
        payee_verdict=(screen.get("payee") or {}).get("verdict"),
        payer_verdict=(screen.get("payer") or {}).get("verdict"),
        tx_id=settlement.get("txid"),
        signed=bool(attestation.get("proof")),
    )


@dataclass
class X402PaymentResult:
    """The outcome of a completed x402 pay-path."""

    tx_hash: str
    payer: Optional[str]
    settled: bool
    idempotent: bool
    attestation: dict
    proof: dict
    summary: AttestationSummary
    raw: dict


# ── HTTP legs (challenge + settle) ───────────────────────────────────────────────


def _pay_url(base_url: str, alias: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1/x402/pay/{alias}"


def fetch_requirement(
    *,
    base_url: str,
    alias: str,
    amount_xrp: Union[str, Decimal],
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """GET the 402 challenge and return the decoded XRP payment requirement.

    Raises ``X402PayError`` if the server does not answer 402 (e.g. x402 disabled,
    alias not payable, or the alias has no XRPL address).
    """
    http = session or requests.Session()
    resp = get_with_retries(
        http, _pay_url(base_url, alias), params={"amount": str(amount_xrp), "currency": "XRP"}, timeout=timeout
    )
    if resp.status_code != 402:
        raise X402PayError(f"expected a 402 challenge, got {resp.status_code}: {resp.text[:200]}")
    header = resp.headers.get("PAYMENT-REQUIRED")
    if not header:
        raise X402PayError("402 response missing the PAYMENT-REQUIRED header")
    return decode_payment_required(header)


def _settle(
    *,
    base_url: str,
    alias: str,
    amount_xrp: Union[str, Decimal],
    tx_hash: str,
    payer: Optional[str],
    api_key: str,
    session: requests.Session,
    timeout: int,
) -> dict:
    headers = {"X-PAYMENT": build_x_payment_header(tx_hash, payer), "X-API-Key": api_key}
    # Retry-safe: the server checks idempotency BEFORE verification, so re-sending
    # the same settled tx proof returns the recorded outcome, never a double-settle.
    resp = get_with_retries(
        session,
        _pay_url(base_url, alias),
        params={"amount": str(amount_xrp), "currency": "XRP"},
        headers=headers,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise X402PayError(f"settle leg failed {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def _result_from_body(body: dict) -> X402PaymentResult:
    attestation = body.get("attestation") or {}
    proof = body.get("proof") or {}
    return X402PaymentResult(
        tx_hash=proof.get("transaction") or "",
        payer=proof.get("payer"),
        settled=bool(body.get("settled")),
        idempotent=bool(body.get("idempotent")),
        attestation=attestation,
        proof=proof,
        summary=summarize_attestation(attestation),
        raw=body,
    )


# ── XRPL signing (lazy xrpl-py import — the [xrpl] extra) ─────────────────────────


def _sign_and_submit_xrp(
    *, pay_to: str, drops: str, seed: str, rpc_url: str, invoice_id: Optional[str], source_tag: Optional[int]
) -> tuple[str, str]:
    """Sign + submit an XRP Payment to ``pay_to`` for ``drops`` with the caller's seed.

    Returns ``(tx_hash, payer_address)``. The seed never leaves this process.
    """
    try:
        from xrpl.clients import JsonRpcClient
        from xrpl.models.transactions import Payment
        from xrpl.transaction import submit_and_wait
        from xrpl.wallet import Wallet
    except ImportError as exc:  # pragma: no cover - import guard
        raise X402PayError(
            "signing requires the 'xrpl' extra — install with: pip install 'a2a-protocol-core[xrpl]'"
        ) from exc

    wallet = Wallet.from_seed(seed)
    client = JsonRpcClient(rpc_url)
    fields: dict[str, Any] = {"account": wallet.address, "destination": pay_to, "amount": str(drops)}
    if invoice_id:
        fields["invoice_id"] = invoice_id
    if source_tag is not None:
        fields["source_tag"] = source_tag
    resp = submit_and_wait(Payment(**fields), client, wallet)
    result = resp.result
    tx_result = (result.get("meta") or {}).get("TransactionResult")
    if result.get("validated") and tx_result == "tesSUCCESS":
        return result["hash"], wallet.address
    raise X402PayError(f"XRPL payment did not succeed (result={tx_result})")


# ── One-call entry points ────────────────────────────────────────────────────────


def pay_alias_xrp(
    *,
    base_url: str,
    alias: str,
    amount_xrp: Union[str, Decimal],
    seed: str,
    api_key: str,
    xrpl_rpc_url: str = DEFAULT_XRPL_RPC,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> X402PaymentResult:
    """Pay a ``pay:`` alias in XRP from your own wallet, end to end.

    Resolve the x402 requirement (402 challenge) → sign + submit the XRP payment
    locally with ``seed`` → hand the proof to DNS of Money for read-only verify +
    the signed attestation. Non-custodial: the seed signs in-process and is never
    transmitted. Requires the ``[xrpl]`` extra. Raises ``X402PayError`` on failure.
    """
    http = session or requests.Session()
    req = fetch_requirement(base_url=base_url, alias=alias, amount_xrp=amount_xrp, session=http, timeout=timeout)
    # The XRPL exact scheme carries scheme fields in `extra`; the top-level copies
    # are our own deprecated mirrors (removed after 2026-10-01). Prefer `extra`, fall
    # back to top-level so this client still works against not-yet-updated servers.
    extra = req.get("extra") or {}
    invoice = extra.get("invoiceId") or req.get("invoiceId")
    source_tag = extra.get("sourceTag") if extra.get("sourceTag") is not None else req.get("sourceTag")
    tx_hash, payer = _sign_and_submit_xrp(
        pay_to=req["payTo"],
        drops=req["maxAmountRequired"],
        seed=seed,
        rpc_url=xrpl_rpc_url,
        invoice_id=invoice_id_hash(invoice) if invoice else None,
        source_tag=source_tag,
    )
    body = _settle(
        base_url=base_url,
        alias=alias,
        amount_xrp=amount_xrp,
        tx_hash=tx_hash,
        payer=payer,
        api_key=api_key,
        session=http,
        timeout=timeout,
    )
    return _result_from_body(body)


# ── USDC-on-Algorand pay path (official x402 client — the [algorand] extra) ───────


def fetch_requirement_header(
    *,
    base_url: str,
    alias: str,
    amount: Optional[Union[str, Decimal]] = None,
    currency: str = "USDC",
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """GET the 402 challenge and return the RAW ``PAYMENT-REQUIRED`` header value.

    Omit ``amount`` to be quoted the alias's declared price (enforced pricing) —
    for a priced endpoint the server names the number either way. The raw header
    is what the official x402 client's decoder consumes, so callers building
    payments with it should start here rather than :func:`fetch_requirement`.
    """
    http = session or requests.Session()
    params = {"currency": currency}
    if amount is not None:
        params["amount"] = str(amount)
    resp = get_with_retries(http, _pay_url(base_url, alias), params=params, timeout=timeout)
    if resp.status_code != 402:
        raise X402PayError(f"expected a 402 challenge, got {resp.status_code}: {resp.text[:200]}")
    header = resp.headers.get("PAYMENT-REQUIRED")
    if not header:
        raise X402PayError("402 response missing the PAYMENT-REQUIRED header")
    return header


class _AlgorandSigner:
    """ClientAvmSigner over algosdk (the pattern from GoPlausible's docs).

    The x402 SDK passes raw msgpack bytes; algosdk works in base64 — convert at
    the boundary. Signs ONLY the indexes the mechanism asks for (the agent's
    USDC transfer leg); the unsigned fee-payer leg is co-signed by the
    facilitator, never by us.
    """

    def __init__(self, secret_key: bytes, address: str):
        self._secret_key = secret_key
        self._address = address

    @property
    def address(self) -> str:
        return self._address

    def sign_transactions(self, unsigned_txns, indexes_to_sign):
        import algosdk

        sk_b64 = base64.b64encode(self._secret_key).decode()
        result: list = []
        for i, txn_bytes in enumerate(unsigned_txns):
            if i in indexes_to_sign:
                txn = algosdk.encoding.msgpack_decode(base64.b64encode(txn_bytes).decode())
                result.append(base64.b64decode(algosdk.encoding.msgpack_encode(txn.sign(sk_b64))))
            else:
                result.append(None)
        return result


def _algorand_secret(mnemonic: Optional[str], secret_key: Optional[Union[bytes, str]]) -> bytes:
    """Resolve the payer's 64-byte Algorand secret from a mnemonic or raw/base64 key."""
    import algosdk

    if mnemonic:
        return base64.b64decode(algosdk.mnemonic.to_private_key(mnemonic))
    if secret_key is not None:
        sk = base64.b64decode(secret_key) if isinstance(secret_key, str) else bytes(secret_key)
        if len(sk) != 64:
            raise X402PayError("algorand secret_key must be 64 bytes (or base64 thereof)")
        return sk
    raise X402PayError("provide algorand mnemonic (25 words) or secret_key")


def _run_coro(coro):
    """Run an async coroutine from this sync API, inside or outside an event loop."""
    import asyncio
    import concurrent.futures

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Called from async code: run the coroutine on its own loop in a worker thread.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def build_avm_payment_header(
    payment_required_header: str,
    *,
    mnemonic: Optional[str] = None,
    secret_key: Optional[Union[bytes, str]] = None,
) -> str:
    """Build the payment header for a USDC-on-Algorand 402 challenge.

    Drives the OFFICIAL x402 client mechanisms (never a hand-rolled group): decode
    the v2 ``PAYMENT-REQUIRED`` envelope, sign Tx0 of the atomic group locally with
    the caller's key, and encode the payment payload header. The facilitator
    co-signs the fee leg and submits — we never custody, and the key never leaves
    this process. Requires the ``[algorand]`` extra.
    """
    try:
        import algosdk
        from x402 import x402Client
        from x402.http.utils import decode_payment_required_header, encode_payment_signature_header
        from x402.mechanisms.avm.exact.register import register_exact_avm_client
    except ImportError as exc:  # pragma: no cover - import guard
        raise X402PayError(
            "USDC-on-Algorand payment requires the 'algorand' extra — "
            "install with: pip install 'a2a-protocol-core[algorand]'"
        ) from exc

    secret = _algorand_secret(mnemonic, secret_key)
    address = algosdk.encoding.encode_address(secret[32:])
    client = x402Client()
    register_exact_avm_client(client, _AlgorandSigner(secret, address))
    required = decode_payment_required_header(payment_required_header)
    payload = _run_coro(client.create_payment_payload(required))
    return encode_payment_signature_header(payload)


def _settle_with_header(
    *,
    base_url: str,
    alias: str,
    params: dict,
    payment_header: str,
    api_key: str,
    session: requests.Session,
    timeout: int,
) -> dict:
    headers = {"X-PAYMENT": payment_header, "X-API-Key": api_key}
    # Retry-safe: server-side idempotency runs before verification (no double-settle).
    resp = get_with_retries(session, _pay_url(base_url, alias), params=params, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise X402PayError(f"settle leg failed {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def pay_alias_usdc_algorand(
    *,
    base_url: str,
    alias: str,
    api_key: str,
    amount_usdc: Optional[Union[str, Decimal]] = None,
    mnemonic: Optional[str] = None,
    secret_key: Optional[Union[bytes, str]] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> X402PaymentResult:
    """Pay a ``pay:`` alias in USDC on Algorand from your own wallet, end to end.

    Fetch the 402 → sign the USDC transfer leg locally (official x402-avm
    mechanism, ``[algorand]`` extra) → the server + facilitator verify, co-sign
    the fee leg, and submit → you get the signed attestation back. Omit
    ``amount_usdc`` to pay the alias's declared price — this is the path that
    pays DNS of Money's own priced endpoints. Non-custodial throughout.
    """
    http = session or requests.Session()
    params = {"currency": "USDC"}
    if amount_usdc is not None:
        params["amount"] = str(amount_usdc)
    raw = fetch_requirement_header(
        base_url=base_url, alias=alias, amount=amount_usdc, currency="USDC", session=http, timeout=timeout
    )
    header = build_avm_payment_header(raw, mnemonic=mnemonic, secret_key=secret_key)
    body = _settle_with_header(
        base_url=base_url,
        alias=alias,
        params=params,
        payment_header=header,
        api_key=api_key,
        session=http,
        timeout=timeout,
    )
    return _result_from_body(body)


def pay_alias(
    *,
    base_url: str,
    alias: str,
    api_key: str,
    amount: Optional[Union[str, Decimal]] = None,
    currency: str = "XRP",
    xrpl_seed: Optional[str] = None,
    algorand_mnemonic: Optional[str] = None,
    algorand_secret_key: Optional[Union[bytes, str]] = None,
    xrpl_rpc_url: str = DEFAULT_XRPL_RPC,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> X402PaymentResult:
    """Rail-dispatching one-call pay: XRP settles on XRPL, USDC on Algorand.

    A convenience front door over :func:`pay_alias_xrp` / :func:`pay_alias_usdc_algorand`
    — pass the credentials for the rail you're paying on. Dispatch is a currency
    table lookup, deterministic by construction.
    """
    cur = (currency or "").upper()
    if cur == "XRP":
        if not xrpl_seed:
            raise X402PayError("XRP payment requires xrpl_seed")
        if amount is None:
            raise X402PayError("XRP payment requires amount (XRP endpoints are not price-quoted)")
        return pay_alias_xrp(
            base_url=base_url,
            alias=alias,
            amount_xrp=amount,
            seed=xrpl_seed,
            api_key=api_key,
            xrpl_rpc_url=xrpl_rpc_url,
            session=session,
            timeout=timeout,
        )
    if cur == "USDC":
        return pay_alias_usdc_algorand(
            base_url=base_url,
            alias=alias,
            api_key=api_key,
            amount_usdc=amount,
            mnemonic=algorand_mnemonic,
            secret_key=algorand_secret_key,
            session=session,
            timeout=timeout,
        )
    raise X402PayError(f"unsupported currency {currency!r} — this client pays XRP (XRPL) or USDC (Algorand)")


def attest_settled_payment(
    *,
    base_url: str,
    alias: str,
    amount_xrp: Union[str, Decimal],
    tx_hash: str,
    api_key: str,
    payer: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> X402PaymentResult:
    """Get the attestation for a payment you ALREADY settled on XRPL (bring-your-own tx).

    Same settle leg as :func:`pay_alias_xrp`, minus the signing — for agents that pay
    through their own wallet stack (or a Coinbase Agentic Wallet) and just want the
    read-only verify + attestation. No ``[xrpl]`` extra needed.
    """
    http = session or requests.Session()
    body = _settle(
        base_url=base_url,
        alias=alias,
        amount_xrp=amount_xrp,
        tx_hash=tx_hash,
        payer=payer,
        api_key=api_key,
        session=http,
        timeout=timeout,
    )
    return _result_from_body(body)
