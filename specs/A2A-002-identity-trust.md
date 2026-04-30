# A2A-002: Identity & Trust

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how agents are identified, authenticated, and trusted in the A2A network.

## 2. Required Agent Identity Fields
- `AGENT_ID` — Stable unique identifier
- `ORG_ID` — Organization identifier
- `KEY_ID` — Key reference
- `PUBLIC_KEY` — For signature verification

## 3. Trust Tiers
- `UNVERIFIED`
- `SELF_ASSERTED`
- `ORG_VERIFIED`
- `NETWORK_VERIFIED`
- `REGULATED_ENVIRONMENT_VERIFIED`

## 4. Message Signing
Messages MAY be signed using public-key cryptography. When signatures are used, `SIGNATURE` and `SIGNING_KEY_ID` MUST be present.

## 5. Replay Protection
Implementations SHOULD prevent replay attacks by validating `REQUEST_ID`, `TIMESTAMP`, and `PAYLOAD_HASH` together as a composite uniqueness check.
