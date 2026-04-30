# A2A-008: Canonicalization & Cache Optimization

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines canonicalization rules required to maximize prompt cache reuse and minimize compute cost. This is the cost-efficiency layer of the protocol family.

## 2. Two Hash Types

**payload_hash** — Hash of the full normalized message including all variable fields. Used for deduplication, replay detection, exact result caching.

**canonical_hash** — Hash of the stable semantic structure with volatile fields removed. Used for prompt prefix cache grouping, routing similar work to the same template, analytics.

## 3. Canonical Hash Exclusions
The following fields MUST be excluded from `canonical_hash` computation:
- `SESSION_ID`, `REQUEST_ID`, `TRACE_ID`, `TIMESTAMP`
- `PAYLOAD_HASH`, `CANONICAL_HASH`, `END_MESSAGE`

## 4. Canonicalization Rules
- Uppercase all enum values
- Trim whitespace and collapse repeated spaces
- ISO-8601 UTC timestamps
- `NONE` for explicit null-like line protocol values
- Fixed block order per A2A-001

## 5. Synonym Normalization
```
CHECK → VERIFY
REVIEW → VERIFY
SHORT → CONCISE
BRIEF → CONCISE
USA → US
```

## 6. Cache Scopes
- `PROTOCOL_PREFIX_CACHE` — Static protocol instructions
- `DOMAIN_PREFIX_CACHE` — Domain-specific instructions
- `TASK_PREFIX_CACHE` — Task pattern level
- `RESULT_CACHE` — Exact result reuse
- `NO_CACHE`

## 7. Why This Matters
Natural language prompts are unique. Canonical A2A messages are repeatable. The difference means: millions of unique prompts become hundreds of cacheable templates. Every cache hit = zero additional inference cost.
