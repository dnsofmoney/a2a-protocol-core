# A2A-080: Observability & Telemetry

**Version:** 1.0 | **Status:** Working Draft

## 1. Scope
Defines the wire formats, label conventions, and propagation rules for traces, metrics, and logs across A2A-compliant systems. A2A-010 §7 names the metrics; this spec makes them interoperable.

## 2. Purpose
Without standardized telemetry, two implementations both claim to track `MESSAGE_LATENCY` while producing incomparable measurements. Cross-org dashboards, federated SLA enforcement, and reputation-from-telemetry (A2A-060) all require shared label schema and trace propagation.

## 3. Standard Metrics
Implementations MUST expose these metric names. OpenTelemetry-compatible naming.

| Metric | Type | Unit | Required Labels |
|--------|------|------|-----------------|
| `a2a.messages.received` | counter | 1 | `message_type`, `domain`, `sender_role` |
| `a2a.messages.processed` | counter | 1 | `message_type`, `domain`, `result_status` |
| `a2a.message.latency` | histogram | ms | `message_type`, `domain` |
| `a2a.cache.hits` | counter | 1 | `cache_scope` |
| `a2a.cache.misses` | counter | 1 | `cache_scope` |
| `a2a.errors` | counter | 1 | `error_code`, `domain` |
| `a2a.agent.utilization` | gauge | ratio | `agent_id` |
| `a2a.settlement.latency` | histogram | ms | `rail`, `currency` |
| `a2a.reputation.events` | counter | 1 | `event_type`, `subject_type` |

## 4. Standard Labels
Label values MUST be lowercase or canonical enum values from referenced specs. Cardinality rules:

- **Bounded** (safe): `message_type`, `domain`, `result_status`, `error_code`, `rail`, `currency`, `cache_scope`, `event_type`
- **High-cardinality** (use cautiously): `agent_id`, `sender_role`, `org_id`
- **Forbidden** as labels: `request_id`, `trace_id`, `payload_hash`, `session_id` — these belong on traces, not metrics

## 5. Trace Propagation
Implementations MUST propagate W3C Trace Context (`traceparent`, `tracestate`) headers across all A2A transport profiles (A2A-004). The A2A `TRACE_ID` field SHOULD equal the W3C trace ID hex string.

Span naming convention:
```
a2a.{action}.{subject}
```
Example: `a2a.settle.payment`, `a2a.verify.payout_batch`.

Required span attributes:
- `a2a.message_type`
- `a2a.domain`
- `a2a.request_id`
- `a2a.payload_hash`
- `a2a.canonical_hash` (when computed)

## 6. Log Schema
Structured logs MUST be JSON with these required fields:

```json
{
  "timestamp": "2026-03-19T20:01:02.123Z",
  "level": "INFO",
  "trace_id": "...",
  "span_id": "...",
  "agent_id": "AGT-PAYMENTS-001",
  "request_id": "R-19002",
  "message_type": "VERIFY",
  "result_status": "COMPLETED",
  "msg": "..."
}
```

Free-text only in `msg`. All structured data goes in named fields.

## 7. Cardinality Budget
A receiver MUST NOT emit metrics whose label combinations exceed declared cardinality. Default budget: 10,000 unique label-set combinations per metric per receiver. Violations SHOULD trigger automatic label reduction (e.g., dropping `agent_id`).

## 8. Privacy
Telemetry MUST NOT contain message bodies, evidence references that resolve to PII, or settlement amounts above declared aggregation thresholds. Hashes (`payload_hash`, `canonical_hash`) are safe to log; raw payloads are not.

## 9. SLA-Linked Reputation
A2A-060 reputation scoring MAY consume telemetry from this spec. Examples:
- `PERFORMANCE_SCORE` ← rolling p95 of `a2a.message.latency`
- `RELIABILITY_SCORE` ← `a2a.messages.processed{result_status="COMPLETED"}` / total
- `ECONOMIC_SCORE` ← `a2a.settlement.latency` distribution + failure rate

Receivers consuming telemetry as reputation input MUST require signed metric submissions per A2A-002.

## 10. Conformance
A2A-090 vectors at L4 and above MUST include:
- A trace propagation vector (incoming `traceparent` preserved across an outgoing A2A call)
- A label-schema vector (verifying required labels present, forbidden labels absent)
- A log-schema vector (verifying JSON shape)

## 11. Why This Matters
Telemetry is the substrate for SLAs, reputation, billing audits, and incident response. Standardizing it now prevents the "every team built their own dashboard" failure mode that makes federated networks ungovernable.
