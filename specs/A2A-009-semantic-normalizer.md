# A2A-009: Deterministic Language & Canonical Semantics

**Version:** 1.0 | **Status:** Stable — Core Innovation

---

## 1. Scope

Defines the deterministic semantic layer for the A2A protocol family. Standardizes how A2A-compliant systems normalize meaning, collapse synonyms into canonical forms, reduce semantic drift, enforce machine-first expression patterns, and generate stable canonical representations for shared caching.

A2A-009 exists to ensure that equivalent requests, facts, actions, and outcomes are represented in a single canonical semantic form whenever possible.

---

## 2. Purpose

Two agents may express the same meaning differently, leading to unnecessary cost, ambiguity, inconsistent execution, weak caching, broken analytics, and policy mismatch. A2A-009 addresses this by requiring that semantically equivalent requests be transformed into a canonical semantic representation.

---

## 3. Relationship to A2A-008

- **A2A-008** = canonical structure. Answers: *How should messages be serialized and hashed?*
- **A2A-009** = canonical meaning. Answers: *What should the message mean in its final machine form?*

Both are required for maximal cache efficiency.

---

## 4. Design Principles

- **Determinism** — Equivalent meanings SHOULD resolve to identical representations
- **Controlled Vocabulary** — Canonical tokens SHOULD come from registered vocabularies
- **Minimal Ambiguity** — Natural-language ambiguity SHOULD be removed before critical workflows
- **Machine-First Expression** — Normalized semantics MUST prioritize machine interpretation
- **Composability** — Structures MUST remain compatible with domain extensions
- **Cache Efficiency** — Canonical semantics SHOULD maximize shared cache reuse
- **Auditability** — Transformations SHOULD be explainable and traceable

---

## 5. Semantic Processing Model

```
RAW INPUT
↓ INTERPRETATION
↓ SEMANTIC NORMALIZATION (A2A-009)
↓ CANONICAL SEMANTIC FORM
↓ CANONICAL STRUCTURAL FORM (A2A-008)
↓ HASHING / CACHING / ROUTING / EXECUTION
```

---

## 6. Canonical Action Vocabulary

Actions MUST be drawn from this controlled vocabulary:

```
QUERY      REPORT     VERIFY     EXECUTE    SETTLE     RESOLVE
REGISTER   DISCOVER   AUTHORIZE  RESERVE    RELEASE    ESCALATE
REJECT     APPROVE    SCORE      PROPOSE    VOTE       ARBITRATE
APPEAL     ATTEST     CACHE      ROUTE      SCHEDULE   METER
```

---

## 7. Synonym Collapse Rules

```
CHECK / REVIEW / INSPECT          → VERIFY
LOOK UP / LOOKUP / FIND           → QUERY
PAY / SEND / TRANSFER / SETTLE    → SETTLE    (domain: FINTECH)
RUN / LAUNCH / EXECUTE            → EXECUTE   (domain: COMPUTE)
DISPUTE / JUDGE                   → ARBITRATE (domain: GOVERNANCE)
RATE / SCORE                      → SCORE     (domain: TRUST)
```

---

## 8. Canonical Subject Vocabulary

```
PAYMENT           PAYMENT_ALIAS      WORKLOAD          AGENT
RESOLUTION_RECORD SETTLEMENT_INSTRUCTION REPUTATION_RECORD PROPOSAL
DISPUTE_CASE      POLICY             RECEIPT           SCHEMA
CONTAINER_JOB     RESOURCE_CLASS     BID               SERVICE_OFFER
```

---

## 9. Semantic Roles

- `ACTION` — What is being requested, reported, or decided
- `SUBJECT` — The primary domain object class
- `OBJECT` — The specific target entity, resource, or identifier
- `CONTEXT` — Relevant situational conditions
- `CONSTRAINTS` — Execution, policy, time, pricing, or compliance boundaries
- `QUALIFIERS` — Additional modifiers that refine meaning
- `REFERENCES` — Links to schemas, records, tasks, receipts, aliases, or evidence

---

## 10. Semantic Equivalence Examples

These three inputs normalize to the same canonical form when `domain=FINTECH` and `object=AGT-COMPUTE-001`:

```
"Pay the compute node five dollars."
"Send USD 5 to the compute provider."
"Transfer $5 to AGT-COMPUTE-001."
```

All become:

```
ACTION:SETTLE
SUBJECT:PAYMENT
OBJECT:AGT-COMPUTE-001
AMOUNT:5
CURRENCY:USD
```

And therefore share the same `semantic_hash` — enabling cache reuse across all three.

---

## 11. Domain Context Resolution

Normalization MUST consider domain context. Example: `score this` means different things in:

- `TRUST` → `ACTION:SCORE SUBJECT:REPUTATION_RECORD`
- `MARKET` → `ACTION:SCORE SUBJECT:BID`
- `ML` → `ACTION:VERIFY SUBJECT:MODEL_OUTPUT`

---

## 12. Semantic Hash

The canonical semantic form is SHA-256 hashed after JSON serialization with sorted keys and no whitespace.

```python
semantic_hash = SHA256(canonical_json(semantic_form, sort_keys=True))
```

This `semantic_hash` enables cross-agent cache sharing independent of message-level hashing.

---

## 13. Normalization Profiles

| Profile | Min Confidence |
|---------|---------------|
| `GENERAL_PURPOSE` | 0.50 |
| `LOW_LATENCY` / `CACHE_MAXIMIZED` | 0.45 |
| `STRICT_FINANCIAL` | 0.90 |
| `STRICT_GOVERNANCE` | 0.90 |
| `HIGH_SAFETY` | 0.95 |

---

## 14. Semantic Error Codes

```
SEMANTIC_ACTION_MISSING
SEMANTIC_SUBJECT_MISSING
SEMANTIC_AMBIGUITY_UNRESOLVED
SEMANTIC_TOKEN_UNKNOWN
SEMANTIC_PROFILE_VIOLATION
SEMANTIC_CONFIDENCE_TOO_LOW
```

---

## 15. Cross-Layer Integration

- **A2A-010** (Network) — routing decisions become deterministic; discovery queries become cacheable
- **A2A-020** (Economy) — identical jobs collapse into one compute event; marketplaces become efficient
- **A2A-030** (Payments) — payment instructions are canonical; settlement logic is deterministic
- **A2A-040** (Compute) — workloads hash to identical execution plans; compute reuse becomes possible
- **A2A-050** (Governance) — proposals standardized; voting machine-verifiable
- **A2A-060** (Reputation) — scoring inputs normalized; no ambiguity in behavior tracking

---

## 16. Reference Canonical JSON Form

```json
{
  "semantic_version": "1.0",
  "normalization_profile": "STRICT_FINANCIAL",
  "domain": "FINTECH",
  "action": "SETTLE",
  "subject": "PAYMENT",
  "object": "AGT-COMPUTE-001",
  "qualifiers": { "amount": 5, "currency": "USD" },
  "constraints": { "max_fee": 0.05 },
  "references": { "resolution_ref": "resolver://..." },
  "semantic_confidence": 0.99
}
```

---

## 17. Strategic Importance

A2A-009 is a core force multiplier for the entire A2A family. It turns a network of communicating agents into a network of semantically aligned agents. Without it, agents may interoperate structurally but still drift semantically. With it, structure, meaning, cacheability, policy behavior, economic logic, and governance semantics all align.

---

## 18. Integration Point

```
raw_input
→ semantic_normalizer.normalize_semantics()
→ canonical semantic form + semantic_hash
→ A2A-008 canonicalize_message()
→ canonical_hash
→ route / execute / settle
```

### Usage Example

```python
from semantic_normalizer import normalize_semantics

result = normalize_semantics(
    "Send USD 5 to the compute provider.",
    domain="FINTECH",
    profile="CACHE_MAXIMIZED",
    explicit_object="AGT-COMPUTE-001",
)

print(result['semantic_hash'])  # Same hash for all equivalent inputs
```
