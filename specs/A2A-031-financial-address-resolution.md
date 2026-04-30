# A2A-031: Financial Address Resolution Binding

**Version:** 1.0 | **Status:** Working Draft

---

## 1. Scope

The bridge between A2A agents, DNS-of-Money / FAS-1 `pay:` aliases, and the A2A-030 settlement layer. Allows agents to declare `payment_alias` values and resolve them into normalized settlement instructions.

---

## 2. The Core Problem Solved

A2A-002 provides agent identity but does not resolve to payment rails. A2A-031 adds the financial naming layer: any agent can advertise `pay:agent.compute` and the resolver returns ranked payment endpoints.

---

## 3. Binding Flow

```
A2A Identity → payment_alias → resolver lookup → resolution record
             → rail selection → settlement instruction → payment receipt
```

---

## 4. Agent with Payment Alias

```json
{
  "agent_id": "AGT-COMPUTE-001",
  "payment_alias": "pay:agent.compute"
}
```

---

## 5. Resolution Record

```json
{
  "alias": "pay:agent.compute",
  "preferred_rail": "XRPL",
  "endpoints": [
    { "rail": "XRPL",   "currency": "USD", "address": "rExample123" },
    { "rail": "FEDNOW", "currency": "USD", "address": "acct://fednow/example" }
  ],
  "iso_hint": "pacs.008.001.08",
  "signature": "<signed>",
  "ttl_seconds": 300
}
```

---

## 6. Key Binding Fields

- `PAYMENT_ALIAS` — The `pay:` URI
- `RESOLUTION_REF` — Link to the resolution record
- `RESOLVER_AUTHORITY` — Who signed the record
- `RESOLUTION_TIMESTAMP` — When resolved
- `SELECTED_RAIL` — Which rail was chosen
- `SETTLEMENT_INSTRUCTION_REF` — The normalized instruction

---

## 7. What FAS-1 Is Missing (Gaps A2A-031 Closes)

- Cryptographic verification of resolution records
- TTL and cache semantics (DNS works because of caching)
- Resolver trust model and authority hierarchy
- Payment instruction normalization
- Namespace governance and dispute resolution

---

## 8. Combined Runtime Flow

```
1. Discover agent via A2A-003 registry
2. Dispatch work via A2A-001 message
3. Receive completion via A2A-006 receipt
4. Resolve pay:agent.compute via FAS-1 resolver
5. Select rail by policy (cost / compliance / availability)
6. Settle via A2A-030 rail adapter
7. Link settlement receipt back to task receipt
```

---

## 9. Combined Architecture

```
Applications
↓ A2A Orchestrator (task routing + receipts)
↓ A2A Agent Registry + FAS-1 Resolver (pay: alias lookup)
↓ Service Agents + Payment Orchestrator (rail selection)
↓ Compute/Tool Runtimes + Settlement Providers (ACH / FedNow / XRPL)
```

---

## 10. Strategic Position

The A2A Agent Registry + Financial Naming Layer + Marketplace together become the distribution layer of AI services. If developers register agents as `pay:agent.compute` and `pay:model.llama`, the network becomes the directory of AI services — the economic entry point analogous to how DNS became the naming layer of the Internet.

---

## 11. Related

- [DNS of Money](https://github.com/dnsofmoney/dns-of-money) — the FAS-1 resolver implementation
- [A2A-002](A2A-002-identity-trust.md) — agent identity layer
- [A2A-030](A2A-030-payment-rails.md) — settlement execution layer
