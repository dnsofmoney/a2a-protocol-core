"""
Example: an AI agent pays a DNS of Money ``pay:`` alias and screens the counterparty.

The scenario the agent-payment world actually needs solved: your agent knows *who*
it wants to pay (a human-readable ``pay:`` name, not a raw r-address), needs to pay
in one step, and wants proof it screened the counterparty before releasing funds.

This is the whole loop in ~10 lines using ``a2a-protocol-core``:

    quote  → resolve the x402 price for the alias           (no wallet needed)
    pay    → sign + submit XRP from the agent's OWN wallet   (self-custody; seed never sent)
    verify → get back a signed resolve/verify/OFAC-screen attestation
    act    → the agent decides based on the screen verdict

Works today for any XRPL-holding agent — e.g. one built on Ripple's XRPL AI Starter
Kit, Crossmint agent wallets, or a Xaman/xApp wallet. DNS of Money is non-custodial:
it verifies an already-settled tx and returns metadata; it never holds your keys or
funds.

Run (quote only — safe, no spend):
    X402_BASE=https://api.dnsofmoney.com X402_ALIAS=pay:dnsofmoney \
    python examples/agent_pay_alias.py

Run (real payment — needs the [xrpl] extra + your funded XRPL wallet + an API key):
    pip install "a2a-protocol-core[xrpl]"
    X402_BASE=https://api.dnsofmoney.com X402_ALIAS=pay:vendor.alpha X402_AMOUNT=0.10 \
    FAS_API_KEY=fas_live_... XRPL_AGENT_SEED=s... \
    python examples/agent_pay_alias.py
"""

from __future__ import annotations

import os
import sys

from a2a_protocol_core import (
    X402PayError,
    fetch_requirement,
    pay_alias_xrp,
)


def main() -> int:
    base_url = os.getenv("X402_BASE", "https://api.dnsofmoney.com")
    alias = os.getenv("X402_ALIAS", "pay:dnsofmoney")
    amount = os.getenv("X402_AMOUNT", "0.01")
    seed = os.getenv("XRPL_AGENT_SEED", "").strip()
    api_key = os.getenv("FAS_API_KEY", "").strip()
    rpc = os.getenv("XRPL_RPC_URL", "https://xrplcluster.com")

    # 1) QUOTE — resolve what this alias costs, on which rail. No wallet, no spend.
    try:
        req = fetch_requirement(base_url=base_url, alias=alias, amount_xrp=amount)
    except X402PayError as exc:
        print(f"[quote] could not get a price for {alias}: {exc}")
        return 1
    print(f"[quote] {alias} -> pay {req['maxAmountRequired']} drops to {req['payTo']} on {req['network']}")

    # Quote-only mode: stop here unless the agent is configured to actually pay.
    if not (seed and api_key):
        print("[dry-run] set XRPL_AGENT_SEED (your wallet) + FAS_API_KEY to pay for real.")
        return 0

    # 2-3) PAY + VERIFY — one call: the agent signs from its own wallet, DNS of Money
    #      verifies read-only and returns the signed attestation.
    try:
        result = pay_alias_xrp(
            base_url=base_url, alias=alias, amount_xrp=amount, seed=seed, api_key=api_key, xrpl_rpc_url=rpc
        )
    except X402PayError as exc:
        print(f"[pay] failed: {exc}")
        return 1

    s = result.summary
    print(f"[paid] tx={result.tx_hash} settled={result.settled} ({'signed' if s.signed else 'unsigned'} attestation)")
    print(f"[screen] overall={s.verdict}  payee={s.payee_verdict}  payer={s.payer_verdict}")

    # 4) ACT — the agent does its own thing based on the compliance verdict.
    if s.verdict == "BLOCKED":
        print("[decide] counterparty screened BLOCKED — the agent would halt / escalate here.")
        return 2
    print("[decide] counterparty clear — the agent proceeds with the delivered service.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
