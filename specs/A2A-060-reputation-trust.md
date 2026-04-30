# A2A-060: Reputation & Trust Scoring

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how A2A-compliant systems measure, publish, exchange, and consume reputation and trust scores. The network memory layer that makes trust a first-class network property.

## 2. Reputation Dimensions
- `RELIABILITY_SCORE` — Consistency of successful task completion
- `PERFORMANCE_SCORE` — Speed and efficiency relative to declared capabilities
- `INTEGRITY_SCORE` — Truthfulness, signature validity, audit consistency
- `POLICY_COMPLIANCE_SCORE` — Adherence to network and domain policies
- `ECONOMIC_SCORE` — Fair market behavior, settlement reliability, bid fulfillment
- `SECURITY_SCORE` — Resistance to abuse, compromise, or policy violations

## 3. Example Reputation Record
```json
{
  "subject_id": "AGT-COMPUTE-001",
  "subject_type": "COMPUTE_PROVIDER",
  "evaluation_window": "ROLLING_90D",
  "reliability_score": 0.992,
  "performance_score": 0.944,
  "integrity_score": 0.998,
  "policy_compliance_score": 0.987,
  "economic_score": 0.973,
  "security_score": 0.981
}
```

## 4. Trust Threshold Classes
- `TRUST_CLASS_A` — Eligible for high-value tasks
- `TRUST_CLASS_B` — Eligible for standard tasks
- `TRUST_CLASS_C` — Limited scope
- `TRUST_CLASS_RESTRICTED` — Approval required
- `TRUST_CLASS_SUSPENDED` — Blocked

## 5. Positive & Negative Events

**Positive:**
`CONSISTENT_SUCCESSFUL_EXECUTION`, `LOW_DISPUTE_RATE`, `HIGH_VERIFICATION_MATCH_RATE`, `TIMELY_SETTLEMENT`, `STABLE_UPTIME`, `AUDIT_PASSED`

**Negative:**
`TASK_FAILURE`, `FALSE_CAPABILITY_DECLARATION`, `INVALID_SIGNATURE`, `SETTLEMENT_DEFAULT`, `DISPUTE_LOSS`, `POLICY_VIOLATION`, `REPLAY_BEHAVIOR`

## 6. Anti-Manipulation Controls
- Identity cost under A2A-002 (Sybil prevention)
- Receipt-backed scoring — scores must trace to verifiable events
- Cross-authority score comparison
- Federation-level trust root verification

## 7. Weighted Trust Profiles
Example for `REGULATED_FINANCE` domain weighting:
- `INTEGRITY_SCORE`: 35%
- `POLICY_COMPLIANCE_SCORE`: 25%
- `SECURITY_SCORE`: 20%
- `RELIABILITY_SCORE`: 10%
- `ECONOMIC_SCORE`: 10%

## 8. Governance Linkage
Reputation MAY influence: voting eligibility, proposal sponsorship eligibility, arbitration panel eligibility, marketplace ranking, settlement reserve requirements. High-power governance actions SHOULD require stronger integrity and compliance scores.
