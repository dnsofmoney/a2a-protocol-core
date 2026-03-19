# A2A Protocol Core

> Agent-to-Agent protocol reference implementation — specs A2A-001 through A2A-061.

---

## What This Is

A simulation-only reference implementation of the A2A (Agent-to-Agent) protocol family. Covers agent registration, semantic normalization, FAS-1 alias resolution, multi-rail payment orchestration, receipt tracking, and reputation scoring.

**A2A-041** — the Payment Hook — bridges Google's A2A compute marketplace to real settlement via [DNS of Money](https://github.com/dnsofmoney/dns-of-money).

---

## Spec Coverage

| Spec Range | Domain | Status |
|------------|--------|--------|
| A2A-001 – A2A-010 | Core message canonicalization | ✅ Implemented |
| A2A-009 | Semantic normalization | ✅ Implemented |
| A2A-011 – A2A-020 | Agent registry & discovery | ✅ Implemented |
| A2A-021 – A2A-030 | Payment orchestration | ✅ Implemented |
| A2A-031 | FAS-1 Financial Address Resolution | ✅ Implemented |
| A2A-041 | Payment Hook (marketplace → settlement) | ✅ Implemented |
| A2A-042 – A2A-050 | Receipt tracking & verification | ✅ Implemented |
| A2A-051 – A2A-060 | Reputation scoring | ✅ Implemented |
| A2A-061 | DNS of Money SDK bridge | ✅ New |

---

## Architecture

```
Agent A                    Agent B
   │                          │
   ├─ POST /agents/register   │
   │                          ├─ POST /agents/register
   │                          │
   ├─ POST /payments ─────────┤
   │   ├─ normalize_semantics()     [A2A-009]
   │   ├─ resolve(pay:agent.b)      [A2A-031 / FAS-1]
   │   ├─ select_rail(policy)       [A2A-021]
   │   └─ adapter.execute()         [A2A-041]
   │                          │
   │   ←── receipt ───────────┤     [A2A-042]
   │                          │
   └─ POST /reputation/events       [A2A-051]
```

---

## Quick Start

```bash
git clone https://github.com/dnsofmoney/a2a-protocol-core.git
cd a2a-protocol-core
python -m venv .venv
.venv/Scripts/Activate.ps1    # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`

---

## Endpoints

| Method | Path | Spec | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Health check |
| POST | `/agents/register` | A2A-011 | Register an agent |
| GET | `/agents/{id}` | A2A-012 | Get agent by ID |
| GET | `/agents` | A2A-013 | List agents (filter by domain) |
| POST | `/resolve` | A2A-031 | Resolve a pay: alias |
| POST | `/payments` | A2A-021 | Execute a payment |
| GET | `/payments/{id}` | A2A-022 | Get payment status |
| POST | `/v1/a2a/payment-hook` | A2A-041 | Payment hook (marketplace → settlement) |
| POST | `/receipts` | A2A-042 | Create a receipt |
| GET | `/receipts/{id}` | A2A-043 | Get receipt |
| POST | `/reputation/events` | A2A-051 | Record reputation event |
| GET | `/reputation/{id}` | A2A-052 | Get reputation score |
| POST | `/normalize` | A2A-009 | Semantic normalization |
| POST | `/messages` | A2A-008 | Inbound message processing |

---

## A2A-041: Payment Hook

The missing piece in the A2A compute marketplace spec — payment settlement.

```bash
curl -X POST http://localhost:8000/v1/a2a/payment-hook \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "agent_id": "agent-compute-001",
    "payee_alias": "pay:agent.compute",
    "amount": "0.69",
    "currency": "USD"
  }'
```

**Response:**
```json
{
  "hook_id": "a2a-041-...",
  "task_id": "task-001",
  "payee_alias": "pay:agent.compute",
  "amount": "0.69",
  "currency": "USD",
  "status": "SETTLED",
  "rail": "XRPL",
  "iso_ref": "pacs.008.001.08",
  "settled_at": "2026-03-19T..."
}
```

---

## Tests

```bash
pytest tests/ -v
```

| Test File | Spec | Tests |
|-----------|------|-------|
| `test_a2a_core.py` | A2A-001–008 | Message canonicalization |
| `test_semantic_normalizer.py` | A2A-009 | Semantic normalization |
| `test_registry.py` | A2A-011–013 | Agent registration |
| `test_resolver.py` | A2A-031 | FAS-1 resolution |
| `test_payment_hook.py` | A2A-041 | Payment hook |
| `test_payments.py` | A2A-021 | Payment orchestration |

---

## Rules

- Preserve A2A-001 through A2A-061 naming
- Never merge into financial-autonomy-stack
- Typed Python throughout
- Simulation only — no real banking integrations
- Real settlement goes through [DNS of Money](https://github.com/dnsofmoney/dns-of-money)

---

## Related

- **DNS of Money:** [github.com/dnsofmoney/dns-of-money](https://github.com/dnsofmoney/dns-of-money) — the live resolution + settlement API
- **FAS-1 Spec:** [Financial Address Standard](https://github.com/dnsofmoney/dns-of-money/blob/main/docs/FAS-1.md)
- **Live API:** [api.dnsofmoney.com](https://api.dnsofmoney.com)

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

*A2A Protocol Core — Simulation reference for the Agent-to-Agent protocol family.*
*Built by JD + Claude — March 2026*
