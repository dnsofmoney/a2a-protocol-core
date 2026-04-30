# A2A Protocol Family

**Agent-to-Agent Communication Standard**

A modular protocol suite for trusted, interoperable, cache-efficient AI-agent communication. Not a framework. Not a tool library. Not a company product. A protocol standard — comparable to how ISO 20022 standardized banking messages, HTTP standardized web communication, and DNS standardized name resolution.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Working%20Draft-yellow)]()
[![Version](https://img.shields.io/badge/Version-1.0-green)]()

---

## What Problem A2A Solves

No existing agent framework fully solves how autonomous AI systems can:

- Communicate **deterministically** across organizations and model providers
- **Settle economic value** between agents without collapsing into proprietary silos
- **Govern themselves** with verifiable, auditable decision records
- **Build trust records** that survive across sessions and providers
- **Execute compute workloads** with proof of execution and metered settlement

A2A is designed to be the entry point: an agent registry + financial naming layer + canonical message protocol. If developers register agents as `pay:agent.compute` and `pay:model.translation`, the A2A network becomes the directory of AI services — the distribution layer of the machine economy.

---

## Specification Index

| Spec | Title | Status |
|------|-------|--------|
| [A2A-001](specs/A2A-001-core-messaging.md) | Core Messaging | Stable |
| [A2A-002](specs/A2A-002-identity-trust.md) | Identity & Trust | Stable |
| [A2A-003](specs/A2A-003-capability-discovery.md) | Capability Discovery | Stable |
| [A2A-004](specs/A2A-004-transport-bindings.md) | Transport Bindings | Stable |
| [A2A-005](specs/A2A-005-policy-execution.md) | Policy & Execution Control | Stable |
| [A2A-006](specs/A2A-006-receipts-audit.md) | Receipts & Audit Trail | Stable |
| [A2A-007](specs/A2A-007-schema-registry.md) | Schema Registry | Stable |
| [A2A-008](specs/A2A-008-canonicalization.md) | Canonicalization & Cache | Stable |
| [A2A-009](specs/A2A-009-semantic-normalizer.md) | Deterministic Language & Canonical Semantics | **Stable — Core Innovation** |
| [A2A-010](specs/A2A-010-network-architecture.md) | Agent Network Architecture | Stable |
| [A2A-020](specs/A2A-020-agent-economy.md) | Autonomous Agent Economy | Working Draft |
| [A2A-030](specs/A2A-030-payment-rails.md) | Settlement & Payment Rails | Working Draft |
| [A2A-031](specs/A2A-031-financial-address-resolution.md) | Financial Address Resolution Binding | Working Draft |
| [A2A-040](specs/A2A-040-compute-execution.md) | Distributed Compute Execution | Working Draft |
| [A2A-050](specs/A2A-050-governance.md) | Governance & Arbitration | Working Draft |
| [A2A-060](specs/A2A-060-reputation-trust.md) | Reputation & Trust Scoring | Working Draft |

---

## Stack Layer Map

| Spec | Purpose | Internet Analog | Finance Analog |
|------|---------|----------------|----------------|
| A2A-001 | Message envelope | HTTP | FIX/ISO 20022 |
| A2A-002 | Identity & trust | TLS / certs | LEI / BIC |
| A2A-003 | Capability discovery | DNS SRV records | Scheme directory |
| A2A-004 | Transport | TCP/IP | SWIFT network |
| A2A-005 | Policy control | OAuth scopes | Compliance rules |
| A2A-006 | Audit receipts | HTTP status + logs | Settlement confirmations |
| A2A-007 | Schema registry | W3C / IANA | ISO message catalog |
| A2A-008 | Cache optimization | CDN / Varnish | Netting engine |
| A2A-009 | Semantic layer | Semantic web / RDF | Structured messaging |
| A2A-010 | Network topology | BGP routing | Correspondent banking |
| A2A-020 | Agent economy | AWS Marketplace | Payment marketplace |
| A2A-030 | Payment rails | Stripe API | ACH/FedNow/SWIFT |
| A2A-031 | Financial naming | DNS | IBAN / alias |
| A2A-040 | Compute execution | Lambda / containers | Batch processing |
| A2A-050 | Governance | IETF RFC process | Basel Committee |
| A2A-060 | Reputation | PageRank / StackOverflow | Credit scoring |

---

## Relationship to Existing Standards

The Linux Foundation / Google A2A protocol covers agent messaging, tasking, and capability discovery. OpenAI MCP covers tool access. LangGraph and CrewAI cover orchestration.

None of these cover: policy enforcement, schema registry, canonical cache optimization, agent economy, payment rails, distributed compute execution, governance, reputation, or financial address resolution.

A2A extends beyond all of these, treating them as baseline layers on which the full economic and governance infrastructure is built.

---

## The Core Innovation: A2A-009

A2A-009 is the semantic normalizer. It ensures that equivalent requests — regardless of how they are phrased — collapse into identical machine representations that can be cached, routed, executed, and audited without ambiguity.

```
"Pay the compute node five dollars."
"Send USD 5 to the compute provider."
"Transfer $5 to AGT-COMPUTE-001."
```

All three normalize to:

```json
{
  "action": "SETTLE",
  "subject": "PAYMENT",
  "object": "AGT-COMPUTE-001",
  "qualifiers": { "amount": 5, "currency": "USD" }
}
```

And therefore share the same `semantic_hash` — enabling cache reuse across all three. Natural language prompts are unique. Canonical A2A messages are repeatable. Millions of unique prompts become hundreds of cacheable templates. Every cache hit = zero additional inference cost.

---

## A2A-031: The Financial Address Bridge

A2A-031 binds A2A agent identity to the [DNS of Money](https://github.com/dnsofmoney/dns-of-money) `pay:` alias system. Any agent can advertise `pay:agent.compute` and the resolver returns ranked payment endpoints.

```
A2A Identity → payment_alias → resolver lookup → resolution record
             → rail selection → settlement instruction → payment receipt
```

---

## Processing Pipeline

```
raw_input
→ normalize_semantics()   [A2A-009]
→ canonical semantic form
→ semantic_hash
→ canonicalize_message()  [A2A-008]
→ canonical_hash
→ route / execute / settle
```

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
# Docs at http://127.0.0.1:8000/docs
```

---

## Status

Working draft. Not a ratified standard. The architecture is internally consistent, specs are implementation-ready, and the reference implementation is runnable. This is serious protocol-aligned infrastructure, not a toy demo.

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

## Related

- [DNS of Money](https://github.com/dnsofmoney/dns-of-money) — the `pay:` alias resolution layer
- A2A-031 is the bridge between these two repos. Do not merge them prematurely.
