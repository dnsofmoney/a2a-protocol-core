# A2A-090: Conformance & Test Vectors

**Version:** 1.0 | **Status:** Working Draft

## 1. Scope
Defines the conformance levels, test vector format, and required vectors that any A2A implementation MUST pass to claim compliance. Without shared vectors, two implementations can both believe they are correct while producing divergent hashes — breaking interop at the cache layer where A2A's value lives.

## 2. Conformance Levels
An implementation MAY claim one or more levels. Higher levels include all lower-level requirements.

| Level | Name | Required Specs |
|-------|------|----------------|
| L1 | Core Messaging | A2A-001, A2A-007, A2A-008 |
| L2 | Semantic | L1 + A2A-009 |
| L3 | Identity & Transport | L2 + A2A-002, A2A-004 |
| L4 | Receipts & Policy | L3 + A2A-005, A2A-006 |
| L5 | Settlement | L4 + A2A-030, A2A-031 |
| L6 | Full Stack | L5 + A2A-010, A2A-020, A2A-040, A2A-050, A2A-060 |

## 3. Hashing Rules
All hash outputs are SHA-256, hex-encoded lowercase.

- `payload_hash` and `canonical_hash` per A2A-008
- `semantic_hash` per A2A-009 §12
- Inputs MUST be JSON canonicalized: UTF-8 encoded, keys sorted lexicographically, no whitespace between tokens, integer numbers preserved without `.0`, no trailing newline

## 4. Test Vector File Format
Test vectors are JSON files under `tests/vectors/<spec>/`. Each file:

```json
{
  "vector_id": "A2A-008-CANON-0001",
  "spec": "A2A-008",
  "description": "Canonical hash excludes volatile fields",
  "input": { "...": "..." },
  "expected": {
    "payload_hash": "sha256:...",
    "canonical_hash": "sha256:..."
  }
}
```

A conforming implementation MUST produce `expected` outputs byte-for-byte for every vector at its claimed level.

## 5. Required Vector Categories

### 5.1 Canonicalization (A2A-008)
- `CANON-0001` — Volatile fields excluded from canonical_hash
- `CANON-0002` — Whitespace collapse and uppercasing of enums
- `CANON-0003` — Synonym normalization (`CHECK`→`VERIFY`, `USA`→`US`)
- `CANON-0004` — Block reorder rejected
- `CANON-0005` — ISO-8601 timestamp normalization

### 5.2 Semantic Normalization (A2A-009)
- `SEM-0001` — Three FINTECH inputs collapse to identical semantic_hash (per A2A-009 §10)
- `SEM-0002` — Domain disambiguation: "score this" in TRUST vs MARKET vs ML
- `SEM-0003` — Amount + currency extraction
- `SEM-0004` — Payment alias and AGT- agent ID extraction
- `SEM-0005` — Confidence threshold rejection per profile

### 5.3 Identity & Replay (A2A-002, A2A-004)
- `ID-0001` — Replay detection via REQUEST_ID + TIMESTAMP + PAYLOAD_HASH
- `ID-0002` — Signature verification with known KEY_ID
- `ID-0003` — Idempotent receiver returns original result on duplicate

### 5.4 Receipts (A2A-006)
- `RCPT-0001` — Lifecycle transitions valid set
- `RCPT-0002` — Receipt required-field validation
- `RCPT-0003` — Audit log field set complete

### 5.5 Resolution (A2A-031 / FAS-1)
- `RES-0001` — Valid `pay:<entity>.<namespace>` parse
- `RES-0002` — Resolution record signature verification
- `RES-0003` — TTL expiry forces re-resolution
- `RES-0004` — Rail selection deterministic given identical policy

## 6. Self-Test Manifest
An implementation MUST publish a `conformance.json` declaring claimed levels and pass status:

```json
{
  "implementation": "a2a-protocol-core",
  "version": "1.0.1",
  "claimed_levels": ["L1", "L2", "L5"],
  "vectors_passed": 27,
  "vectors_failed": 0,
  "vector_set_version": "1.0"
}
```

## 7. Vector Set Versioning
The vector set is itself versioned. Adding vectors is a minor bump; changing expected outputs is a major bump and requires a deprecation window.

## 8. Why This Matters
A2A's economic value comes from cache reuse across implementations. If implementer A's `canonical_hash(msg)` differs from implementer B's for the same message, every cross-org cache hit is lost. Conformance vectors are the cheapest mechanism to detect that divergence at CI time rather than in production.
