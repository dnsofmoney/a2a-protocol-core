# A2A-020: Agent Economy

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines mechanisms for AI agents to exchange economic value for task execution across the A2A network.

## 2. Economic Roles
- `TASK_REQUESTER` — Entity requesting work
- `SERVICE_AGENT` — Agent performing tasks
- `MARKETPLACE_OPERATOR` — Registry/broker listing available agents
- `SETTLEMENT_PROVIDER` — System responsible for financial settlement

## 3. Pricing Models
- `PER_TASK` — Flat fee for execution
- `PER_TOKEN` — Fee based on tokens processed
- `PER_SECOND` — Time-based compute pricing
- `PER_COMPUTE_UNIT` — Normalized compute resource pricing
- `SUBSCRIPTION` — Recurring access
- `MARKET_BID` — Dynamic pricing via bidding

## 4. Task Bidding Protocol
```
TASK ANNOUNCEMENT → AGENT BIDS → BID EVALUATION → TASK ASSIGNMENT → EXECUTION
```

## 5. Escrow Execution Model
```
TASK POSTED → FUNDS LOCKED → AGENT EXECUTES → RESULT VERIFIED → FUNDS RELEASED
```
If execution fails: `FUNDS RETURNED`. Escrow may be implemented via payment APIs, smart contracts, or custodial services.

## 6. Service Marketplaces
Marketplace entries MUST include: `SERVICE_ID`, `AGENT_ID`, `DOMAIN`, `TASK_TYPE`, `PRICING_MODEL`, `TRUST_TIER`. Marketplaces SHOULD maintain agent reputation scores.

## 7. Economic Policy Controls
- `MAX_TASK_PRICE`, `APPROVED_SETTLEMENT_METHODS`, `ALLOWED_MARKETPLACES`, `REQUIRED_TRUST_TIER`
