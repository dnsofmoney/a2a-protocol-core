# A2A-006: Receipts & Audit

**Version:** 1.0 | **Status:** Stable

## 1. Receipt Lifecycle States
`RECEIVED → ACCEPTED → PROCESSING → COMPLETED → FAILED | ESCALATED`

## 2. Receipt Required Fields
- `REQUEST_ID`, `RECEIPT_STATUS`, `RECEIVER_AGENT_ID`, `TIMESTAMP`, `PAYLOAD_HASH`
- Optional: `EXECUTION_REF`, `ERROR_CODE`, `ERROR_MESSAGE`

## 3. Example Receipt
```json
{
  "request_id": "R-19002",
  "receipt_status": "ACCEPTED",
  "receiver_agent_id": "AGT-PAYMENTS-001",
  "timestamp": "2026-03-16T17:02:00Z",
  "payload_hash": "abc123",
  "execution_ref": "EX-99881"
}
```

## 4. Audit Logs
Implementations SHOULD maintain immutable audit logs containing: `REQUEST_ID`, `TRACE_ID`, `AGENT_ID`, `ACTION`, `TIMESTAMP`, `PAYLOAD_HASH`, `RESULT_STATUS`. Retained per organizational policy.
