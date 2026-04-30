# A2A-004: Transport Bindings

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how A2A messages are transported between agents. Transport layer is protocol-agnostic.

## 2. Supported Transport Profiles
- `A2A-HTTP` — POST to `/a2a/messages`, `Content-Type: application/a2a+json`
- `A2A-WebSocket`
- `A2A-Kafka`
- `A2A-NATS`
- `A2A-InternalBus`

## 3. Delivery Semantics
- `AT_MOST_ONCE`
- `AT_LEAST_ONCE` (recommended default)
- `EXACTLY_ONCE`

## 4. Idempotency
Receivers MUST treat `REQUEST_ID` + `PAYLOAD_HASH` as a composite idempotency key. If a duplicate is received, return the original result.

## 5. Retry Behavior
Retry attempts SHOULD follow exponential backoff. `MAX_LATENCY_MS` controls when a timeout escalation is returned.

## 6. Security
Transport implementations SHOULD use TLS 1.3 or mutual TLS (mTLS). Sensitive financial fields SHOULD be encrypted in transit.
