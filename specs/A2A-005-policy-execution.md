# A2A-005: Policy & Execution Controls

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how execution permissions and risk controls are enforced. Policy enforcement applies at the receiving agent before execution begins.

## 2. Policy Profiles
- `READ_ONLY`
- `ANALYSIS_ONLY`
- `RECOMMENDATION_ONLY`
- `EXECUTION_WITH_APPROVAL`
- `AUTONOMOUS_EXECUTION`

## 3. Action Authorization
```
AGENT_ROLE:PAYMENTS_ANALYST
ALLOWED_ACTIONS:QUERY,VERIFY,REPORT
DISALLOWED_ACTIONS:SETTLE_FUNDS,MODIFY_LEDGER
REQUIRES_HUMAN_APPROVAL_FOR:RELEASE_PAYMENT
```

## 4. Risk Classification
- `LOW | MEDIUM | HIGH | CRITICAL`

Agents SHOULD escalate requests exceeding their permitted risk threshold.

## 5. Escalation
If a request violates policy constraints, the agent MUST return `RESULT_STATUS:ESCALATED` with explanation. All executed actions SHOULD generate audit records per A2A-006.
