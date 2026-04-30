# A2A-003: Capability Discovery

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how agents advertise what they can do. Enables orchestrators to select the right agent for a task without prior configuration.

## 2. Capability Manifest Fields
- `AGENT_ID`, `PROTOCOL_VERSIONS`
- `DOMAINS` — List of supported domain values
- `MESSAGE_TYPES` — Accepted message classes
- `INPUT_SCHEMAS`, `OUTPUT_SCHEMAS`
- `TOOLS` — Declared tool access
- `MAX_LATENCY_MS`, `SUPPORTS_STREAMING`

## 3. Example Manifest
```json
{
  "agent_id": "AGT-PAYMENTS-001",
  "protocol_versions": ["1.0"],
  "domains": ["FINTECH"],
  "message_types": ["QUERY", "VERIFY", "REPORT"],
  "input_schemas": ["A2A_MESSAGE_V1", "PAYOUT_BATCH_V1"],
  "output_schemas": ["PAYOUT_VALIDATION_REPORT_V1"],
  "tools": ["ledger_lookup", "policy_engine"],
  "max_latency_ms": 1500
}
```

## 4. Discovery Mechanisms
Capability manifests MAY be retrieved through HTTP endpoint, registry service, service mesh discovery, or signed manifest documents.

## 5. Routing
Orchestrators SHOULD use capability manifests to select the most appropriate agent. Selection criteria MAY include domain support, latency, trust tier, and supported schemas.
