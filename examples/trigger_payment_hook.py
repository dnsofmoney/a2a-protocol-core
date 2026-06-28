"""
Minimal example: fire an A2A-041 payment hook from a calling agent.

    pip install a2a-protocol-core
    python examples/trigger_payment_hook.py

The agent decides *what* to pay and *why*; a2a-protocol-core carries a
validated, deterministic request to the DNS of Money core and parses the
result. No rail selection or scoring happens here — that stays server-side
and deterministic.
"""

from a2a_protocol_core import (
    A2APaymentHookClient,
    compute_canonical_hash,
    normalize_message,
)


def main() -> None:
    # 1. The calling agent describes its intent however it likes...
    intent = {
        "action": "send",  # synonym of EXECUTE_PAYMENT
        "amount": "2.50",
        "currency": "USD",
        "alias": "pay:agent.compute",
    }
    # 2. ...which normalizes to a stable canonical hash regardless of vocabulary.
    semantic_hash = compute_canonical_hash(normalize_message(intent))

    # 3. Fire the hook against a running DNS of Money node.
    client = A2APaymentHookClient(base_url="https://api.dnsofmoney.com")

    print("capabilities:", client.capabilities())

    result = client.trigger(
        job_id="job-demo-001",
        provider_pay_address="pay:agent.compute",
        requester_pay_address="pay:vendor.alpha",
        amount="2.50",
        currency="USD",
        semantic_hash=semantic_hash,
    )
    print("settlement:", result.settlement_result.status, result.settlement_result.rail)
    print("iso ref:", result.iso_message_ref)


if __name__ == "__main__":
    main()
