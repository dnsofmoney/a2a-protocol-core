# A2A-007: Schema Registry

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines registry and lifecycle rules for schemas used across the A2A family. Without a shared schema registry, every team reinvents incompatible payloads.

## 2. Schema Namespaces
```
a2a.core.message.v1
a2a.core.error.v1
a2a.core.receipt.v1
a2a.fintech.payout_batch.v1
a2a.legal.contract_review.v1
a2a.software.code_audit.v1
```

## 3. Versioning Rules
- Major version = breaking change
- Minor version = additive compatible change
- Patch version = clarifications only

## 4. Schema Lifecycle
Schema publishing, deprecation, compatibility rules, and domain extension registration are all governed through the registry. Deprecated schemas MUST be flagged before removal.
