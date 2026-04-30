# A2A-042: AP2 Mandate Bridge

**Version:** 1.0 | **Status:** Working Draft

## 1. Scope
Defines how a Google Agentic Commerce **AP2 closed Payment Mandate** is consumed by A2A-041 (Payment Hook) and routed through A2A-031 (FAS-1 resolution) and A2A-030 (payment rails) to actual settlement.

## 2. The Gap This Closes
AP2 (https://ap2-protocol.org) explicitly declares three non-goals:

1. Payment rail selection
2. Address resolution
3. Fund settlement

A2A explicitly covers all three:

| AP2 Non-Goal | A2A Spec |
|--------------|----------|
| Rail selection | A2A-030 §5 |
| Address resolution | A2A-031 (FAS-1) |
| Fund settlement | A2A-041 |

AP2 ends with a cryptographically authorized intent. A2A begins with that intent and produces a settlement receipt. Without a bridge, every implementer rewrites the join.

## 3. Bridge Flow
```
[AP2 layer]                              [A2A layer]
User intent
  → Open Checkout Mandate
  → Open Payment Mandate
  → Closed Checkout Mandate
  → Closed Payment Mandate ────────────► A2A-042 Bridge
                                          ├─ verify mandate signature
                                          ├─ extract payee_alias
                                          ├─ A2A-031 resolve(alias)
                                          ├─ A2A-030 select_rail(policy)
                                          └─ A2A-041 POST /v1/a2a/payment-hook
                                                ↓
                                          settlement_receipt
                                                ↓
                                          A2A-006 receipt linkage
                                                ↓
                                          A2A-060 reputation event
```

## 4. Mandate-to-Hook Field Mapping
A conforming bridge MUST map a closed Payment Mandate to an A2A-041 hook body as follows:

| A2A-041 Field | Source in AP2 Mandate |
|---------------|-----------------------|
| `task_id` | Mandate `transaction_id` (or merchant order ref) |
| `agent_id` | Mandate `agent_identifier` |
| `payee_alias` | `merchant_payment_alias` extension (see §5) |
| `amount` | Mandate `amount.value` |
| `currency` | Mandate `amount.currency` |

## 5. Required AP2 Extension: `merchant_payment_alias`
AP2 mandates currently carry merchant identity but not a `pay:` alias. A2A-042 requires a single optional extension field:

```json
{
  "merchant_payment_alias": "pay:merchant.acme"
}
```

When present, the bridge MUST use this alias for A2A-031 resolution. When absent, the bridge MAY fall back to a registry lookup keyed on the AP2 merchant identifier — but this fallback MUST emit a `LOW_TRUST_FALLBACK` audit event.

## 6. Mandate Verification (Pre-Settlement)
Before invoking A2A-041, the bridge MUST:
1. Verify the closed Payment Mandate's signature using AP2's published verification rules
2. Confirm mandate `expiry` is in the future
3. Confirm mandate amount matches the requested settlement amount byte-for-byte
4. Confirm mandate `currency` matches resolved rail capability

Any failure → `422` with `error_code:MANDATE_INVALID`. No settlement occurs.

## 7. Idempotency Across Both Protocols
AP2 mandates are single-use. A2A-041 hook IDs are deterministic per (task_id, agent_id, payee_alias). The bridge MUST:
- Refuse to process a mandate whose `transaction_id` was previously settled
- Return the original A2A-041 response on duplicate POST (per A2A-041 §9)

The composite uniqueness key is: `(mandate.transaction_id, mandate.signature)`.

## 8. Receipt Round-Trip
The bridge MUST attach the A2A-041 settlement receipt back to the AP2 transaction record so AP2-side dispute resolution can prove fund movement. Required linkage fields:
- `a2a_hook_id`
- `a2a_settlement_rail`
- `a2a_settled_at`
- `a2a_iso_ref`

## 9. Failure Handling
| AP2 State | A2A Outcome | Bridge Action |
|-----------|-------------|---------------|
| Mandate valid, hook `SETTLED` | Success | Emit AP2 success + A2A-060 `TIMELY_SETTLEMENT` |
| Mandate valid, hook `FAILED` | Settlement failure | Surface to AP2 dispute layer; emit `SETTLEMENT_DEFAULT` |
| Mandate invalid | No A2A call | Reject at bridge; no reputation event |
| Mandate valid, alias unknown | A2A `404` | Bridge MUST NOT auto-retry with fallback alias unless §5 fallback rules are met |

## 10. Privacy
Mandate contents MUST be classified per A2A-070:
- Mandate signature, transaction_id → `OPERATIONAL`
- Amount, currency, merchant alias → `CONFIDENTIAL`
- Buyer identity fields → `PII`

Telemetry per A2A-080 MUST NOT log mandate signatures or buyer identity.

## 11. Why This Bridge Matters
AP2 is solving authorization. A2A is solving execution. Without A2A-042, every merchant building on AP2 has to reinvent rail selection, alias resolution, and idempotent settlement — exactly the wheels A2A already standardizes. This spec lets AP2 ship faster by inheriting A2A's settlement layer, and lets A2A inherit AP2's industry-standard mandate cryptography. Both protocols win; neither has to grow into the other's territory.

## 12. Reference
- AP2 — https://ap2-protocol.org
- AP2 source — https://github.com/google-agentic-commerce/AP2
