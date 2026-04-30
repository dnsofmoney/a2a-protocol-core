# A2A-001: Core Messaging Specification

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines the universal message envelope and canonical field ordering for all A2A messages. All other A2A specifications depend on A2A-001.

## 2. Canonical Block Order
All A2A messages MUST conform to this canonical block order. Implementations MUST NOT reorder these blocks. This requirement ensures deterministic parsing and prompt-prefix stability.

```
HEADER
IDENTITY
INTENT
CONSTRAINTS
EVIDENCE
OUTPUT_SPEC
CACHE_CONTROL
INTEGRITY
TERMINATION
```

## 3. HEADER Block — Required Fields
- `VERSION` — Integer identifying the protocol version
- `MESSAGE_CLASS` — Valid value: `A2A`
- `MESSAGE_TYPE` — `TASK | QUERY | VERIFY | TRANSFORM | DECIDE | REPORT | ESCALATE`
- `DOMAIN` — `UNIVERSAL | FINTECH | LEGAL | HEALTHCARE | SOFTWARE | RESEARCH | OPERATIONS`

## 4. IDENTITY Block
- `SENDER_ROLE`, `RECEIVER_ROLE`, `REQUEST_ID` (required)
- `SESSION_ID`, `TRACE_ID`, `TIMESTAMP` (optional)

`REQUEST_ID` MUST uniquely identify a request within the sender's scope. `TRACE_ID` SHOULD be used when requests propagate across multiple agents.

## 5. INTENT Block
- `ACTION`, `SUBJECT`, `OBJECT` (required)
- `GOAL`, `PRIORITY` (optional) — `LOW | NORMAL | HIGH | CRITICAL`

## 6. CONSTRAINTS Block
`CONSTRAINT_PROFILE`, `POLICY_PROFILE`, `JURISDICTION`, `TIME_SCOPE`, `MAX_LATENCY_MS`

## 7. EVIDENCE Block
Large datasets SHOULD be referenced rather than embedded inline.
- `EVIDENCE_MODE` — `REFERENCE_FIRST` preferred
- `DATA_REF`, `FACT_SET_REF`, `DOC_REF`, `LEDGER_REF`

## 8. OUTPUT_SPEC Block
- `OUTPUT_FORMAT` (required) — `JSON | XML | CSV | TEXT | MARKDOWN`
- `OUTPUT_SCHEMA` (required)
- `DETAIL_LEVEL` — `MINIMAL | CONCISE | STANDARD | DETAILED`
- `CONFIDENCE_MODE` — `REQUIRED | OPTIONAL | NONE`
- `CITATION_MODE` — `REQUIRED | OPTIONAL | NONE`

## 9. CACHE_CONTROL Block
- `CACHE_POLICY` — `CANONICAL_REUSE | PREFIX_REUSE | RESULT_CACHE_OK | NO_CACHE`
- `CACHE_SCOPE`

## 10. INTEGRITY Block
- `PAYLOAD_HASH` (required)
- `CANONICAL_HASH`, `SCHEMA_VERSION`, `SIGNATURE` (optional)

## 11. TERMINATION
`END_MESSAGE:TRUE`

## 12. Example A2A Request
```
VERSION:1
MESSAGE_CLASS:A2A
MESSAGE_CLASS_LABEL:AiToAi
MESSAGE_TYPE:VERIFY
DOMAIN:FINTECH
SENDER_ROLE:ORCHESTRATOR
RECEIVER_ROLE:PAYMENTS_ANALYST
SESSION_ID:S-88421
REQUEST_ID:R-19002
TRACE_ID:T-88421-19002
TIMESTAMP:2026-03-16T13:00:00Z
ACTION:VERIFY
SUBJECT:PAYOUT_BATCH
OBJECT:BATCH_CR_20260316_001
GOAL:PRE_SUBMISSION_VALIDATION
PRIORITY:HIGH
POLICY_PROFILE:ISO20022_SAFE
JURISDICTION:US
OUTPUT_FORMAT:JSON
OUTPUT_SCHEMA:PAYOUT_VALIDATION_REPORT_V1
CACHE_POLICY:CANONICAL_REUSE
PAYLOAD_HASH:<HASH>
END_MESSAGE:TRUE
```

## 13. Error Handling
```
RESULT_STATUS:ERROR
ERROR_CODE:INVALID_FIELD
ERROR_FIELD:OUTPUT_SCHEMA
ERROR_MESSAGE:Unsupported schema identifier
```

## 14. Backward Compatibility
Future protocol versions MUST preserve compatibility with `VERSION:1` messages. Existing field names MUST NOT be renamed. New fields MAY be introduced only as optional extensions.
