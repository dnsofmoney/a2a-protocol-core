# A2A-070: Privacy & Data Handling

**Version:** 1.0 | **Status:** Working Draft

## 1. Scope
Defines how A2A-compliant systems classify, redact, encrypt, retain, and delete sensitive data carried in messages, evidence, receipts, and telemetry. Earlier specs assume sensitive content is referenced not embedded; A2A-070 makes that assumption enforceable.

## 2. Purpose
Without standardized handling, one implementer logs raw payloads, another stores receipts unencrypted, a third propagates PII into telemetry. Any single bad actor breaks the privacy posture of the whole federation. A2A-070 sets the floor every conforming implementation MUST meet.

## 3. Data Classification
Every field in an A2A message, receipt, or telemetry record MUST be assigned a classification:

| Class | Description | Examples |
|-------|-------------|----------|
| `PUBLIC` | Safe to log and propagate freely | `MESSAGE_TYPE`, `DOMAIN`, `rail` |
| `OPERATIONAL` | Internal but not sensitive | `REQUEST_ID`, `TRACE_ID`, `AGENT_ID` |
| `CONFIDENTIAL` | Restricted by policy | `amount`, `payee_alias`, `purpose_code` |
| `PII` | Personal data subject to regulation | `debtor_name`, `creditor_name`, address fields |
| `SECRET` | Cryptographic material, never logged | `private_key`, `signing_key`, `bearer_token` |

Schemas registered under A2A-007 MUST declare classification per field.

## 4. Redaction Rules
- `SECRET` fields MUST NOT appear in logs, traces, telemetry, audit records, or error messages.
- `PII` fields MUST be hashed or tokenized before inclusion in telemetry per A2A-080 §8.
- `CONFIDENTIAL` fields MAY appear in audit records but MUST NOT appear in metrics labels.
- `payload_hash` and `canonical_hash` are always safe; raw payloads are not.

## 5. Encryption
- **In transit:** TLS 1.3 minimum per A2A-004 §6. mTLS REQUIRED for `REGULATED_ENVIRONMENT_VERIFIED` trust tier.
- **At rest:** Receipts (A2A-006) and audit logs MUST be encrypted at rest when they contain `CONFIDENTIAL` or `PII` fields. AES-256-GCM or equivalent.
- **Key management:** Encryption keys MUST rotate on a documented schedule. Compromise procedures per A2A-050 §8.

## 6. Reference-First Evidence
Per A2A-001 §7, large or sensitive datasets MUST be referenced rather than embedded. The reference (`DATA_REF`, `DOC_REF`, `LEDGER_REF`) MUST itself resolve through an access-controlled endpoint that enforces the classification of its target.

## 7. Retention
Implementations MUST declare and enforce retention windows per data class:

| Class | Default Maximum | Notes |
|-------|-----------------|-------|
| `PUBLIC` | Indefinite | |
| `OPERATIONAL` | 365 days | Trace data, audit metadata |
| `CONFIDENTIAL` | 7 years | Aligns with financial record-keeping norms |
| `PII` | Per jurisdiction | GDPR-style "minimum necessary" |
| `SECRET` | Never persisted | Held in memory or KMS only |

## 8. Deletion & Right-to-Erasure
On verified erasure request, an implementation MUST:
1. Delete or tombstone `PII` fields tied to the subject within 30 days
2. Preserve `payload_hash` and `canonical_hash` (irreversible references) for audit integrity
3. Emit a deletion receipt per A2A-006 with `RESULT_STATUS:COMPLETED` and `ACTION:ERASE`

Audit-required records MAY be retained beyond erasure with PII fields scrubbed but transaction-level metadata intact.

## 9. Jurisdiction Tagging
Messages crossing jurisdictional boundaries MUST carry the `JURISDICTION` field (A2A-001 §6). Receivers MUST refuse to process if their declared jurisdiction lacks legal basis. Federation rules (A2A-050 §9) MAY constrain cross-border data flow further.

## 10. Privacy Profile Declarations
Agent capability manifests (A2A-003) SHOULD include a `privacy_profile`:

```json
{
  "privacy_profile": {
    "encryption_at_rest": true,
    "tls_min_version": "1.3",
    "supports_erasure": true,
    "retention_policy_ref": "https://example.com/retention.json",
    "jurisdiction": "US",
    "data_classes_handled": ["OPERATIONAL", "CONFIDENTIAL", "PII"]
  }
}
```

## 11. Cross-Spec Linkage
- **A2A-006** — Receipts MUST honor classification of fields they reference
- **A2A-007** — Schema registry MUST capture per-field classification
- **A2A-050** — Privacy violations are arbitrable offenses
- **A2A-060** — Privacy compliance feeds `POLICY_COMPLIANCE_SCORE`
- **A2A-080** — Telemetry redaction rules derive from this spec
- **A2A-090** — Conformance vectors MUST include redaction and erasure cases

## 12. Why This Matters
A federated agent network is only as private as its weakest implementation. Standardizing classification, redaction, encryption, retention, and erasure prevents the failure mode where one careless deployment leaks data the rest of the network was protecting.
