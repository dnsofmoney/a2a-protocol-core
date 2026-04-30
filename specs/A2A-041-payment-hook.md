# A2A-041: Payment Hook

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines the bridge between A2A compute marketplace receipts (A2A-006, A2A-040) and multi-rail settlement via FAS-1 alias resolution (A2A-031, A2A-030). The Payment Hook is the moment a completed task receipt becomes a settlement instruction.

## 2. Purpose
A2A-040 produces compute receipts. A2A-030 settles funds across rails. Without a binding layer, every implementer rewrites the same wiring. A2A-041 standardizes that wiring as a single endpoint contract.

## 3. Endpoint
```
POST /v1/a2a/payment-hook
Content-Type: application/json
```

## 4. Request Body
```json
{
  "task_id": "task-001",
  "agent_id": "agent-compute-001",
  "payee_alias": "pay:agent.compute",
  "amount": "0.69",
  "currency": "USD"
}
```

Required: `task_id`, `agent_id`, `payee_alias`, `amount`. Default for `currency` is `USD`.

`payee_alias` MUST be a valid `pay:` URI per A2A-031. Implementations MUST reject malformed aliases with `422`.

## 5. Hook ID — Deterministic
Implementations MUST compute `hook_id` as:
```
hook_id = "a2a-041-" + sha256("a2a-041:{task_id}:{agent_id}:{payee_alias}")[:16]
```

Identical input MUST yield identical `hook_id`. This makes the hook idempotent — duplicate POSTs collapse to the same settlement record.

## 6. Resolution & Rail Selection
On receipt, the hook MUST:
1. Resolve `payee_alias` via the FAS-1 resolver (A2A-031). Unknown alias → `404`.
2. Select a rail using the resolver's policy-driven `select_rail()` (A2A-030 §5).
3. Submit the settlement instruction to the selected rail adapter.

## 7. Response
```json
{
  "hook_id": "a2a-041-3f2a...",
  "task_id": "task-001",
  "agent_id": "agent-compute-001",
  "payee_alias": "pay:agent.compute",
  "amount": "0.69",
  "currency": "USD",
  "status": "SETTLED",
  "rail": "XRPL",
  "iso_ref": "pacs.008.001.08",
  "settled_at": "2026-03-19T20:01:02Z"
}
```

`status` values: `SETTLED | PENDING | FAILED`. `iso_ref` carries the ISO 20022 hint from the resolution record (A2A-031 §5).

## 8. Error Codes
- `422` — Malformed `payee_alias` (not a `pay:` URI)
- `404` — Alias resolves to no record
- `503` — Rail adapter unavailable; client SHOULD retry with backoff per A2A-004 §5

## 9. Idempotency Contract
A duplicate POST with identical body MUST return the original response, not re-execute settlement. Implementations MAY cache by `hook_id` or by `(REQUEST_ID, PAYLOAD_HASH)` per A2A-004 §4.

## 10. Receipt Linkage
The hook response SHOULD be linked back to the originating compute receipt (A2A-006) via `task_id` so audit trails reconstruct the full chain: task → execution receipt → payment hook → settlement receipt.

## 11. Reputation Linkage
Successful and failed settlements SHOULD emit reputation events per A2A-060 (`TIMELY_SETTLEMENT` / `SETTLEMENT_DEFAULT`).
