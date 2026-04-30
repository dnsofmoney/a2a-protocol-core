# A2A-061: DNS-of-Money SDK Bridge

**Version:** 1.0 | **Status:** Working Draft

## 1. Scope
Defines the client-library surface that lets A2A agents resolve `pay:` aliases, submit settlement via the A2A-041 Payment Hook, verify receipts, and emit reputation events — without each implementer rewriting the glue between A2A protocol core and DNS-of-Money / FAS-1.

## 2. Purpose
A2A-031 specifies the resolution record. A2A-041 specifies the settlement endpoint. A2A-060 specifies reputation events. An agent author should not have to assemble these by hand. A2A-061 is the canonical SDK contract that closes the loop:

```
agent → resolve → settle → receipt → reputation
```

## 3. Required Methods

```python
class A2AClient:
    def resolve(alias: str) -> ResolutionRecord: ...
    def settle(task_id, agent_id, payee_alias, amount, currency="USD") -> HookResponse: ...
    def verify_receipt(hook_id: str) -> Receipt: ...
    def emit_reputation_event(subject_id, event_type, evidence_ref) -> None: ...
```

Each method MUST be available in every conforming SDK regardless of language binding.

## 4. Auth
SDK constructor takes:
- `api_key` — bearer credential for the resolver and hook endpoints
- `agent_key_id` + `agent_private_key` — for signing requests per A2A-002

Requests MUST be signed when the receiving endpoint requires a trust tier above `SELF_ASSERTED`.

## 5. Caching
Resolution responses MUST be cached for the duration of `ttl_seconds` from the resolution record (A2A-031 §5). Cache MUST be keyed by alias. Cache MUST be invalidated on signature verification failure.

## 6. Idempotency & Retry
`settle()` MUST be safe to retry. SDKs MUST:
- Reuse the same `task_id`/`agent_id`/`payee_alias` tuple on retry so `hook_id` is stable per A2A-041 §5
- Apply exponential backoff per A2A-004 §5
- Treat `503` as retryable; `404`/`422` as terminal

## 7. Receipt Linkage
On successful `settle()`, the SDK MUST persist the mapping `task_id → hook_id → settlement_receipt_ref` so `verify_receipt()` can reconstruct the chain.

## 8. Reputation Loop
After every `settle()` call, the SDK MUST emit a reputation event:
- `TIMELY_SETTLEMENT` on `status=SETTLED` within declared latency
- `SETTLEMENT_DEFAULT` on `status=FAILED`
- `LOW_DISPUTE_RATE` is computed by the network, not the SDK

## 9. Reference Bindings
- **Python** — reference implementation, ships in `app/sdk/`
- **TypeScript** — second binding, parity tested against Python via shared A2A-090 vectors

Additional language bindings MUST pass the A2A-090 conformance suite at L5.

## 10. Error Surface
SDKs MUST raise typed errors:
- `AliasNotFound` (404)
- `InvalidAlias` (422)
- `RailUnavailable` (503, retryable)
- `SignatureInvalid` (resolution record signature failed)
- `ConformanceError` (SDK self-test detected divergence from A2A-090 vectors)

## 11. Why This Spec Exists
Without a standardized SDK contract, every agent integrates resolver + hook + reputation differently. The resulting fragmentation defeats A2A's cache and trust guarantees. A2A-061 ensures any agent reaching for "pay an alias" gets the same loop closed the same way.
