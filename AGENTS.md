# AGENTS.md

## Processing Pipeline Rule

All A2A-compliant implementations MUST follow this pipeline order. Do not shortcut or reorder.

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

## Key Architecture Rules

- Preserve A2A protocol family naming and concepts
- Do not invent a different architecture unless strictly necessary
- Prefer incremental refactors over full rewrites
- Keep files well-factored and typed
- All banking/payment integration uses simulation/mock layers until a confirmed live partnership exists

---

## Phase Separation

The [DNS of Money](https://github.com/dnsofmoney/dns-of-money) Financial Autonomy Stack and this `a2a-protocol-core` repo are **separate repositories**. A2A-031 is the bridge that will eventually connect them. Do not merge them prematurely.

---

## App Structure

```
app/
  main.py                    ← FastAPI app entrypoint
  api/routes.py              ← All endpoints
  services/
    registry.py              ← Agent registry
    resolver.py              ← FAS-1 style resolver with signed records
    messages.py              ← A2A message handling + canonicalization
    payments.py              ← Settlement orchestration
    receipts.py              ← Persisted receipts
    reputation.py            ← Reputation events + aggregate scores
  adapters/
    xrpl.py                  ← XRPL rail adapter
    fednow.py                ← FedNow rail adapter
    internal_ledger.py       ← Internal ledger adapter
  core/
    signing.py               ← Signing (upgrade path: asymmetric)
    a2a.py                   ← Canonical A2A hashing (A2A-008)
    semantic_normalizer.py   ← A2A-009 implementation
    db/database.py           ← DB schema and init
```

---

## Codex / Claude Code Priorities

1. Refactor FastAPI app into production-style modules with clean service boundaries
2. Add typed Pydantic request/response schemas for all A2A envelopes
3. Replace HMAC placeholder signing with asymmetric signatures and verification
4. Add SQLAlchemy models and Alembic migrations
5. Add pluggable rail adapter registry
6. Add integration tests proving identical inputs collapse to same `semantic_hash`
7. Dockerize local dev stack
