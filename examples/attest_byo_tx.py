"""
Bring-your-own-wallet attestation — no signing extras needed.

For agents that already settled the payment through their own wallet stack
(their own xrpl-py flow, a Coinbase Agentic Wallet, anything that produced a
validated XRPL tx hash): skip the SDK's signing path entirely and just buy the
read-only verify + signed attestation for the tx you already made. Base
install only — no [xrpl], no [algorand].

    pip install a2a-protocol-core          # + [verify] to check the signature

Env:
  FAS_API_KEY    tenant API key
  SETTLED_TX     the already-validated XRPL payment hash
  PAY_ALIAS      alias that was paid (default pay:vendor.alpha)
  AMOUNT_XRP     the amount that tx paid (default 0.10)
"""

from __future__ import annotations

import os
import sys

from a2a_protocol_core import attest_settled_payment, verify_attestation
from a2a_protocol_core.attestation_verify import AttestationVerificationError


def main() -> int:
    api_key = os.getenv("FAS_API_KEY", "").strip()
    tx_hash = os.getenv("SETTLED_TX", "").strip()
    if not api_key or not tx_hash:
        print("set FAS_API_KEY and SETTLED_TX")
        return 2

    result = attest_settled_payment(
        base_url=os.getenv("FAS_BASE_URL", "https://api.dnsofmoney.com"),
        alias=os.getenv("PAY_ALIAS", "pay:vendor.alpha"),
        amount_xrp=os.getenv("AMOUNT_XRP", "0.10"),
        tx_hash=tx_hash,
        api_key=api_key,
    )
    print(f"settled    : {result.settled} (idempotent={result.idempotent})")
    print(f"verdict    : {result.summary.verdict}")
    print(f"signed     : {result.summary.signed}")

    try:
        v = verify_attestation(result.attestation, expected_issuer="did:web:dnsofmoney.com")
        print(f"verified   : {v.verified} by {v.issuer}")
    except AttestationVerificationError as exc:
        print(f"verify     : FAILED — {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
