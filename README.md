# a2a-protocol-core

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

The open, **deterministic** protocol core of the [DNS of Money](https://dnsofmoney.com)
agent-to-agent (A2A) payment surface — the dependency-light layer external AI
agents adopt to resolve, hash, and initiate `pay:` payments.

> The intelligence lives in the **calling agent**. This package serves
> deterministic, inspectable primitives — no rail selection, no scoring, no
> model anywhere in the money path.

## Install

```bash
pip install a2a-protocol-core
```

Runtime deps are intentionally minimal: `pydantic` and `requests`.

## What's in here

| Module | A2A ref | Purpose |
|---|---|---|
| `addressing` | FAS-1 | `pay:` URI grammar + validation (`is_valid_pay_uri`) |
| `semantic_normalizer` | A2A-009 | collapse synonym verbs → canonical action codes |
| `canonical_hash` | A2A-008 | metadata- & vocabulary-stable payment-intent hash |
| `schemas` | A2A-041 | payment-hook request/response wire models |
| `client` | A2A-041 | `A2APaymentHookClient` over `/v1/a2a/*` |

## Quick start

```python
from a2a_protocol_core import (
    A2APaymentHookClient,
    compute_canonical_hash,
    normalize_message,
)

# Your agent describes intent however it likes...
intent = {"action": "send", "amount": "2.50", "currency": "USD", "alias": "pay:agent.compute"}

# ...which collapses to a stable hash regardless of wording ("send" == "transfer" == "pay").
semantic_hash = compute_canonical_hash(normalize_message(intent))

client = A2APaymentHookClient(base_url="https://api.dnsofmoney.com")
result = client.trigger(
    job_id="job-001",
    provider_pay_address="pay:agent.compute",
    requester_pay_address="pay:vendor.alpha",
    amount="2.50",
    currency="USD",
    semantic_hash=semantic_hash,
)
print(result.settlement_result.status, result.iso_message_ref)
```

See [`examples/trigger_payment_hook.py`](examples/trigger_payment_hook.py).

## Pay a `pay:` alias in one call (non-custodial)

Resolve the price, pay from **your own wallet**, and get back a signed
resolve/verify/OFAC-screen attestation — one function, and your seed never leaves
your process:

```bash
pip install "a2a-protocol-core[xrpl]"
```

```python
from a2a_protocol_core import pay_alias_xrp

result = pay_alias_xrp(
    base_url="https://api.dnsofmoney.com",
    alias="pay:vendor.alpha",
    amount_xrp="0.10",
    seed="s...",             # YOUR XRPL wallet seed — signs locally, never transmitted
    api_key="fas_live_...",  # attributes the settle leg
)
print(result.tx_hash, result.summary.verdict)   # e.g. "A1B2…", "CLEAR"
```

Already settled the payment through your own wallet stack (or a Coinbase Agentic
Wallet)? Skip the signing and just fetch the attestation — no `[xrpl]` extra:

```python
from a2a_protocol_core import attest_settled_payment

result = attest_settled_payment(
    base_url="https://api.dnsofmoney.com",
    alias="pay:vendor.alpha",
    amount_xrp="0.10",
    tx_hash="A1B2C3...",     # your already-validated XRPL tx
    api_key="fas_live_...",
)
```

DNS of Money **verifies an already-settled transaction and returns metadata** — it
never holds your keys or your funds.

## Why canonical hashing?

Two agents describing the same payment with different words ("send" vs
"transfer") or different session/trace metadata must produce the **same**
intent fingerprint. `compute_canonical_hash` excludes non-semantic noise
(session/request/trace ids, timestamps, idempotency keys, memos) and
normalizes the action verb, so the hash captures *what* is being paid — not
*how it was phrased*. That fingerprint binds an agent's intent to a settlement
without trusting free text.

## Design constraints

- **Deterministic only.** Nothing here selects or scores a rail.
- **Off the money path.** The hash and client describe and carry intent; the
  deterministic core (server-side) resolves, generates ISO 20022, and settles.
- **Dependency-light.** Safe to embed in an agent runtime.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## License

Apache-2.0 — permissive with an explicit patent grant. See [LICENSE](LICENSE).
