"""
Screen a counterparty before paying it — and verify the attestation yourself.

The end-to-end 0.3.0 flow: pay the screening fee in USDC on Algorand from your
own wallet (server-priced; you never name the amount), receive the OFAC +
resolution attestation about the TARGET you named, and check the issuer's
Ed25519 signature against its did:web document locally.

    pip install "a2a-protocol-core[algorand,verify]"

Env:
  FAS_API_KEY            tenant API key (the settle leg requires X-API-Key)
  ALGORAND_MNEMONIC      your 25-word payer mnemonic — signs locally, never sent
  SCREEN_TARGET          pay: alias or raw address to screen (default below)
  FAS_BASE_URL           default https://api.dnsofmoney.com
"""

from __future__ import annotations

import os
import sys

from a2a_protocol_core import screen


def main() -> int:
    api_key = os.getenv("FAS_API_KEY", "").strip()
    mnemonic = os.getenv("ALGORAND_MNEMONIC", "").strip()
    if not api_key or not mnemonic:
        print("set FAS_API_KEY and ALGORAND_MNEMONIC")
        return 2

    result = screen(
        base_url=os.getenv("FAS_BASE_URL", "https://api.dnsofmoney.com"),
        target=os.getenv("SCREEN_TARGET", "pay:vendor.alpha"),
        api_key=api_key,
        algorand_mnemonic=mnemonic,
        verify=True,  # don't just trust TLS — check the issuer's signature
        expected_issuer="did:web:dnsofmoney.com",
    )

    print(f"target   : {result.target}")
    print(f"verdict  : {result.verdict}")
    print(f"fee txid : {result.proof.get('transaction')}")
    print(f"signed   : {result.summary.signed}")
    if result.verification:
        print(f"verified : {result.verification.verified} by {result.verification.issuer}")
    return 0 if result.verdict == "CLEAR" else 1


if __name__ == "__main__":
    sys.exit(main())
